"""Tool LangChain ask_interactive_question (feature 018).

Permet au LLM de poser une question interactive sous forme de widget cliquable
(QCU, QCM, avec ou sans justification). La question est persistee en BDD et un
marker SSE est embarque dans le retour du tool, intercepte par stream_graph_events.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import ValidationError
from sqlalchemy import select, update

from app.graph.tools.common import get_db_and_user, log_tool_call
from app.models.interactive_question import (
    InteractiveQuestion,
    InteractiveQuestionState,
)
from app.schemas.interactive_question import InteractiveQuestionCreate

logger = logging.getLogger(__name__)


def _serialize_for_sse(question: InteractiveQuestion) -> dict:
    """Serializer une question pour le payload SSE interactive_question."""
    return {
        "type": "interactive_question",
        "id": str(question.id),
        "conversation_id": str(question.conversation_id),
        "question_type": question.question_type,
        "prompt": question.prompt,
        "options": question.options,
        "min_selections": question.min_selections,
        "max_selections": question.max_selections,
        "requires_justification": question.requires_justification,
        "justification_prompt": question.justification_prompt,
        "module": question.module,
        "created_at": (
            question.created_at.isoformat()
            if question.created_at
            else datetime.now(timezone.utc).isoformat()
        ),
    }


@tool
async def ask_interactive_question(
    question_type: str,
    prompt: str,
    options: list[dict],
    min_selections: int = 1,
    max_selections: int = 1,
    requires_justification: bool = False,
    justification_prompt: str | None = None,
    config: RunnableConfig = None,  # type: ignore[assignment]
) -> str:
    """Pose une question interactive a l'utilisateur sous forme de widget cliquable.

    A utiliser quand la question attend :
    - un choix unique (question_type='qcu')
    - plusieurs choix (question_type='qcm')
    - un choix + justification texte libre amusante ('qcu_justification' ou 'qcm_justification')

    Args:
        question_type: 'qcu' | 'qcm' | 'qcu_justification' | 'qcm_justification'.
        prompt: Enonce de la question (1-500 caracteres, francais avec accents).
        options: Liste de 2 a 8 dicts {id, label, emoji?, description?}.
        min_selections: Pour QCM uniquement, minimum d'options a cocher (defaut 1).
        max_selections: Pour QCM uniquement, maximum d'options a cocher (defaut 1).
        requires_justification: True uniquement pour les variantes _justification.
        justification_prompt: Libelle fun du champ justification (200 car max).

    Returns:
        Texte court avec marker SSE embarque. Le frontend affiche le widget,
        l'utilisateur repond, et un nouveau tour LLM demarre.
    """
    try:
        db, _user_id = get_db_and_user(config)
    except ValueError as exc:
        logger.warning("ask_interactive_question: config manquante (%s)", exc)
        return "Erreur : contexte technique indisponible, retente."

    configurable = (config or {}).get("configurable", {})
    conversation_id_raw = configurable.get("conversation_id")
    if conversation_id_raw is None:
        logger.warning("ask_interactive_question: conversation_id absent")
        return "Erreur : conversation_id manquant dans le contexte."

    conversation_id = (
        uuid.UUID(conversation_id_raw)
        if isinstance(conversation_id_raw, str)
        else conversation_id_raw
    )

    active_module_data = configurable.get("active_module_data") or {}
    module_name = (
        configurable.get("active_module")
        or active_module_data.get("module")
        or "chat"
    )

    # Validation Pydantic stricte
    try:
        payload = InteractiveQuestionCreate(
            question_type=question_type,  # type: ignore[arg-type]
            prompt=prompt,
            options=options,  # type: ignore[arg-type]
            min_selections=min_selections,
            max_selections=max_selections,
            requires_justification=requires_justification,
            justification_prompt=justification_prompt,
            module=module_name,
        )
    except ValidationError as exc:
        logger.info("ask_interactive_question validation: %s", exc)
        return f"Erreur : parametres invalides ({exc.errors()[0].get('msg', exc)})."
    except ValueError as exc:
        logger.info("ask_interactive_question validation: %s", exc)
        return f"Erreur : {exc}."

    try:
        # Invariant : marquer toute question pending de la conversation comme expired
        now = datetime.now(timezone.utc)
        await db.execute(
            update(InteractiveQuestion)
            .where(
                InteractiveQuestion.conversation_id == conversation_id,
                InteractiveQuestion.state == InteractiveQuestionState.PENDING.value,
            )
            .values(
                state=InteractiveQuestionState.EXPIRED.value,
                answered_at=now,
            )
        )

        question = InteractiveQuestion(
            conversation_id=conversation_id,
            module=payload.module,
            question_type=payload.question_type.value,
            prompt=payload.prompt,
            options=[opt.model_dump(exclude_none=True) for opt in payload.options],
            min_selections=payload.min_selections,
            max_selections=payload.max_selections,
            requires_justification=payload.requires_justification,
            justification_prompt=payload.justification_prompt,
            state=InteractiveQuestionState.PENDING.value,
        )
        db.add(question)
        await db.flush()
        await db.refresh(question)

        sse_payload = _serialize_for_sse(question)
        sse_marker = json.dumps({"__sse_interactive_question__": True, **sse_payload})

        try:
            await log_tool_call(
                db,
                user_id=_user_id,
                conversation_id=conversation_id,
                node_name=module_name,
                tool_name="ask_interactive_question",
                tool_args={
                    "question_type": question_type,
                    "prompt": prompt[:200],
                    "options_count": len(options),
                },
                tool_result={"question_id": str(question.id), "state": "pending"},
                status="success",
            )
        except Exception:  # pragma: no cover - journalisation defensive
            logger.debug("Echec journalisation tool ask_interactive_question", exc_info=True)

        return (
            "Question posee a l'utilisateur."
            f"\n\n<!--SSE:{sse_marker}-->"
        )

    except Exception as exc:
        logger.exception("Erreur dans ask_interactive_question")
        return f"Erreur lors de la creation de la question interactive : {exc}"


INTERACTIVE_TOOLS = [ask_interactive_question]
