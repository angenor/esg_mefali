"""Tools LangChain pour le noeud plan d'action.

Trois tools exposes au LLM :
- generate_action_plan : generer un plan d'action ESG
- update_action_item : mettre a jour le statut d'une action
- get_action_plan : consulter le plan d'action actif
"""

import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry

logger = logging.getLogger(__name__)


# Cible metier d'un plan complet (BUG-V6-005). Le tool accepte des plans
# partiels en mode batch incremental tant que `_ACTION_PLAN_ACCEPT_MIN`
# est respecte. En cas d'echec total du LLM (LLMGuardError), le fallback
# template deterministe garantit toujours `_ACTION_PLAN_TARGET_ITEMS`.
_ACTION_PLAN_TARGET_ITEMS = 10
_ACTION_PLAN_ACCEPT_MIN = 5


@tool
async def generate_action_plan(timeframe: int, config: RunnableConfig) -> str:
    """Generer un plan d'action ESG personnalise pour l'entreprise.

    Utilise cet outil quand l'utilisateur demande a creer ou generer un plan
    d'action, une feuille de route, ou un programme d'amelioration ESG.
    Le plan est sauvegarde en base et visible sur /action-plan.

    Args:
        timeframe: Horizon du plan en mois (6, 12 ou 24).
    """
    from fastapi import HTTPException

    from app.core.llm_guards import LLMGuardError
    from app.modules.action_plan.service import generate_action_plan as gen_plan
    from app.services.action_plan_fallback import (
        FallbackTemplateError,
        persist_fallback_plan,
    )

    db, user_id = get_db_and_user(config)

    fallback_used = False
    plan = None

    async def _trigger_fallback(reason: str) -> "ActionPlan":  # type: ignore[name-defined]
        """Wrapper qui convertit FallbackTemplateError en exception remontee
        au with_retry (genere "Erreur : ..." au LLM)."""
        try:
            return await persist_fallback_plan(
                db=db, user_id=user_id, timeframe=timeframe, reason=reason
            )
        except FallbackTemplateError as exc:
            # Pas de re-fallback possible : on remonte une RuntimeError que
            # with_retry transformera en str retournable au LLM.
            raise RuntimeError(
                f"Plan d'action impossible : template fallback indisponible ({exc})."
            ) from exc

    # 1. Tenter la voie LLM (le service applique deja ses retries internes
    # via run_guarded_llm_call). En cas d'echec total -> fallback template.
    try:
        plan = await gen_plan(db=db, user_id=user_id, timeframe=timeframe)
    except HTTPException:
        # Profil manquant (428) ou erreur metier remontee : pas de fallback.
        raise
    except LLMGuardError as exc:
        logger.warning(
            "action_plan LLMGuardError -> fallback user_id=%s reason=%s",
            user_id,
            getattr(exc, "code", "unknown"),
            extra={
                "metric": "action_plan_fallback",
                "user_id": str(user_id),
                "reason": "llm_guard_error",
            },
        )
        plan = await _trigger_fallback(reason="llm_guard_error")
        fallback_used = True

    items = list(plan.items or [])
    item_count = len(items)

    # 2. Validation des champs (defense en profondeur post-persistance).
    invalid: list[str] = []
    for idx, item in enumerate(items, start=1):
        missing = []
        if not getattr(item, "title", None) or not str(item.title).strip():
            missing.append("title")
        if not getattr(item, "category", None):
            missing.append("category")
        if missing:
            invalid.append(f"action #{idx} (champs manquants : {', '.join(missing)})")
    if invalid:
        return f"ERREUR : actions invalides — {'; '.join(invalid)}."

    # 3. Plan inferieur au minimum acceptable -> fallback de derniere chance.
    if item_count < _ACTION_PLAN_ACCEPT_MIN and not fallback_used:
        logger.warning(
            "action_plan count=%d < %d -> fallback user_id=%s",
            item_count,
            _ACTION_PLAN_ACCEPT_MIN,
            user_id,
            extra={
                "metric": "action_plan_fallback",
                "user_id": str(user_id),
                "reason": "count_below_min",
                "final_count": item_count,
            },
        )
        plan = await _trigger_fallback(reason="count_below_min")
        items = list(plan.items or [])
        item_count = len(items)
        fallback_used = True

    items_preview = []
    for item in items[:5]:
        status = item.status.value if hasattr(item.status, "value") else item.status
        items_preview.append(f"  - {item.title} ({item.category}, {status})")
    items_text = "\n".join(items_preview) if items_preview else "  Aucune action generee."

    # 4. Construire le message retourne au LLM.
    header = (
        "Plan d'action genere via fallback template (LLM indisponible) !"
        if fallback_used
        else "Plan d'action genere avec succes !"
    )

    incremental_note = ""
    if not fallback_used and item_count < _ACTION_PLAN_TARGET_ITEMS:
        missing = _ACTION_PLAN_TARGET_ITEMS - item_count
        incremental_note = (
            f"\n\nMode batch incremental : {item_count}/{_ACTION_PLAN_TARGET_ITEMS} "
            f"actions sauvegardees, manque {missing} pour atteindre la cible. "
            f"Continue avec le batch suivant via un nouvel appel a generate_action_plan."
        )

    return (
        f"{header}\n"
        f"- Titre : {plan.title}\n"
        f"- Horizon : {plan.timeframe} mois\n"
        f"- Nombre d'actions : {plan.total_actions}\n"
        f"- Premieres actions :\n{items_text}\n\n"
        f"Le plan complet est visible sur la page /action-plan."
        f"{incremental_note}"
    )


@tool
async def update_action_item(
    action_id: str,
    config: RunnableConfig,
    status: str | None = None,
    completion_percentage: int | None = None,
) -> str:
    """Mettre a jour le statut ou la progression d'une action du plan.

    Utilise cet outil quand l'utilisateur indique avoir progresse sur une action,
    l'avoir completee, ou souhaite changer son statut.

    Args:
        action_id: Identifiant UUID de l'action a mettre a jour.
        status: Nouveau statut (pending, in_progress, completed, cancelled).
        completion_percentage: Pourcentage de completion (0-100).
    """
    from app.modules.action_plan.service import update_action_item as update_item

    db, user_id = get_db_and_user(config)

    updates: dict = {}
    if status is not None:
        updates["status"] = status
    if completion_percentage is not None:
        updates["completion_percentage"] = completion_percentage

    if not updates:
        return "Aucune modification fournie. Precisez le statut ou le pourcentage de completion."

    item = await update_item(
        db=db,
        item_id=uuid.UUID(action_id),
        user_id=user_id,
        updates=updates,
    )

    item_status = item.status.value if hasattr(item.status, "value") else item.status

    return (
        f"Action mise a jour avec succes :\n"
        f"- Titre : {item.title}\n"
        f"- Statut : {item_status}\n"
        f"- Completion : {item.completion_percentage}%"
    )


@tool
async def get_action_plan(config: RunnableConfig) -> str:
    """Consulter le plan d'action actif de l'utilisateur et sa progression.

    Utilise cet outil quand l'utilisateur demande a voir son plan d'action,
    sa progression, ou les prochaines actions a realiser.
    Ne necessite aucun parametre.
    """
    from app.modules.action_plan.service import get_active_plan

    db, user_id = get_db_and_user(config)

    plan = await get_active_plan(db=db, user_id=user_id)

    if plan is None:
        return (
            "Aucun plan d'action actif trouve. "
            "Proposez a l'utilisateur de generer un plan d'action "
            "en precisant l'horizon souhaite (6, 12 ou 24 mois)."
        )

    completed = plan.completed_actions
    total = plan.total_actions
    pct = int((completed / total) * 100) if total > 0 else 0

    # Lister les actions non completees
    pending_items = []
    for item in (plan.items or []):
        item_status = item.status.value if hasattr(item.status, "value") else item.status
        if item_status != "completed":
            pending_items.append(
                f"  - {item.title} ({item.category}, {item_status}, {item.completion_percentage}%)"
            )

    pending_text = "\n".join(pending_items[:5]) if pending_items else "  Toutes les actions sont completees !"

    return (
        f"Plan d'action actif :\n"
        f"- Titre : {plan.title}\n"
        f"- Horizon : {plan.timeframe} mois\n"
        f"- Progression : {completed}/{total} actions ({pct}%)\n"
        f"- Prochaines actions :\n{pending_text}"
    )


ACTION_PLAN_TOOLS = [
    with_retry(generate_action_plan, max_retries=2, node_name="action_plan"),
    with_retry(update_action_item, max_retries=2, node_name="action_plan"),
    with_retry(get_action_plan, max_retries=2, node_name="action_plan"),
]
