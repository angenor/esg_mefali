"""Router chat : CRUD conversations, envoi de messages avec streaming SSE."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import async_session_factory, get_db
from app.models.company import CompanyProfile
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    PaginatedResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────


async def get_user_conversation(
    conversation_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Conversation:
    """Récupérer une conversation appartenant à l'utilisateur, ou lever 404."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable",
        )
    return conversation


async def invoke_graph(content: str, conversation_id: str) -> str:
    """Invoquer le graphe LangGraph et retourner la réponse complète.

    Cette fonction est mockée dans les tests.
    """
    from app.main import compiled_graph

    if compiled_graph is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service IA indisponible",
        )

    config = {"configurable": {"thread_id": conversation_id}}
    result = await compiled_graph.ainvoke(
        {"messages": [HumanMessage(content=content)]},
        config=config,
    )
    return result["messages"][-1].content


async def _error_sse(message: str) -> AsyncGenerator[str, None]:
    """Générer un événement SSE d'erreur."""
    yield f"data: {json.dumps({'type': 'error', 'content': message})}\n\n"


async def stream_graph_events(
    content: str,
    conversation_id: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    user_profile: dict | None = None,
    context_memory: list[str] | None = None,
    document_analysis_summary: str | None = None,
    document_upload: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """Streamer les événements du graphe LangGraph via astream_events().

    Utilise le graphe compilé avec tool calling pour un flux complet :
    tokens, tool_call_start, tool_call_end, tool_call_error.

    Yields:
        dict avec type: token | tool_call_start | tool_call_end | tool_call_error
    """
    from app.main import compiled_graph

    if compiled_graph is None:
        yield {"type": "error", "content": "Service IA indisponible"}
        return

    # Construire l'état initial pour le graphe
    initial_state = {
        "messages": [HumanMessage(content=content)],
        "user_id": str(user_id),
        "user_profile": user_profile,
        "context_memory": context_memory or [],
        "profile_updates": None,
        "profiling_instructions": None,
        "document_upload": document_upload,
        "document_analysis_summary": document_analysis_summary,
        "has_document": document_upload is not None,
        "esg_assessment": None,
        "_route_esg": False,
        "carbon_data": None,
        "_route_carbon": False,
        "financing_data": None,
        "_route_financing": False,
        "application_data": None,
        "_route_application": False,
        "credit_data": None,
        "_route_credit": False,
        "action_plan_data": None,
        "_route_action_plan": False,
        "tool_call_count": 0,
    }

    config = {
        "configurable": {
            "thread_id": conversation_id,
            "user_id": user_id,
            "db": db,
            "conversation_id": uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id,
        },
    }

    try:
        async for event in compiled_graph.astream_events(
            initial_state,
            config=config,
            version="v2",
        ):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                # Token de texte streamé
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield {"type": "token", "content": chunk.content}

            elif kind == "on_tool_start":
                # Début d'exécution d'un tool
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                run_id = event.get("run_id", "")
                yield {
                    "type": "tool_call_start",
                    "tool_name": tool_name,
                    "tool_args": tool_input if isinstance(tool_input, dict) else {},
                    "tool_call_id": run_id,
                }

            elif kind == "on_tool_end":
                # Fin d'exécution d'un tool
                tool_name = event.get("name", "unknown")
                output = event.get("data", {}).get("output", "")
                run_id = event.get("run_id", "")
                result_summary = str(output)[:200] if output else ""
                yield {
                    "type": "tool_call_end",
                    "tool_name": tool_name,
                    "tool_call_id": run_id,
                    "success": True,
                    "result_summary": result_summary,
                }

                # Émettre les événements SSE profile_update/completion
                # si le tool a retourné des métadonnées de profil
                output_str = str(output) if output else ""
                sse_marker = "<!--SSE:"
                if sse_marker in output_str:
                    try:
                        start = output_str.index(sse_marker) + len(sse_marker)
                        end = output_str.index("-->", start)
                        sse_data = json.loads(output_str[start:end])
                        if sse_data.get("__sse_profile__"):
                            for field_update in sse_data.get("changed_fields", []):
                                yield {"type": "profile_update", **field_update}
                            completion = sse_data.get("completion")
                            if completion:
                                yield {"type": "profile_completion", **completion}
                    except (ValueError, json.JSONDecodeError):
                        logger.debug("Impossible de parser les métadonnées SSE du tool")

            elif kind == "on_tool_error":
                # Erreur d'un tool
                tool_name = event.get("name", "unknown")
                error_data = event.get("data", {})
                run_id = event.get("run_id", "")
                yield {
                    "type": "tool_call_error",
                    "tool_name": tool_name,
                    "tool_call_id": run_id,
                    "error_message": str(error_data.get("error", "Erreur inconnue"))[:200],
                }

    except Exception as e:
        logger.exception("Erreur stream_graph_events")
        yield {"type": "error", "content": str(e)}


async def stream_llm_tokens(
    content: str,
    conversation_id: str,
    user_profile: dict | None = None,
    context_memory: list[str] | None = None,
    document_analysis_summary: str | None = None,
) -> AsyncGenerator[str, None]:
    """Streamer les tokens du LLM un par un (fallback sans tool calling).

    Utilise le LLM directement avec streaming pour un rendu progressif.
    Le prompt système est enrichi avec le profil, la mémoire contextuelle
    et le contexte document si disponible.
    """
    from app.graph.nodes import get_llm
    from app.prompts.system import build_system_prompt
    from langchain_core.messages import SystemMessage

    llm = get_llm()
    system_prompt = build_system_prompt(
        user_profile, context_memory,
        document_analysis_summary=document_analysis_summary,
    )
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=content)]

    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


async def _load_profile_for_state(
    db: AsyncSession, user_id: uuid.UUID
) -> dict | None:
    """Charger le profil utilisateur pour le state du graphe."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return None

    profile_dict: dict = {}
    for field in [
        "company_name", "sector", "sub_sector", "employee_count",
        "annual_revenue_xof", "city", "country", "year_founded",
        "has_waste_management", "has_energy_policy", "has_gender_policy",
        "has_training_program", "has_financial_transparency",
        "governance_structure", "environmental_practices",
        "social_practices", "notes",
    ]:
        value = getattr(profile, field)
        if value is not None:
            profile_dict[field] = value.value if hasattr(value, "value") else value

    return profile_dict if profile_dict else None


async def _load_context_memory(
    db: AsyncSession, user_id: uuid.UUID
) -> list[str]:
    """Charger les 3 derniers résumés de conversation."""
    result = await db.execute(
        select(Conversation.summary)
        .where(
            Conversation.user_id == user_id,
            Conversation.summary.isnot(None),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(3)
    )
    return [row[0] for row in result.all() if row[0]]


async def _summarize_previous_conversation(
    db: AsyncSession, user_id: uuid.UUID
) -> None:
    """Générer le résumé de la dernière conversation si elle n'en a pas."""
    from app.chains.summarization import generate_summary

    # Récupérer la dernière conversation sans résumé
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.summary.is_(None),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    prev_conv = result.scalar_one_or_none()

    if prev_conv is None:
        return

    # Charger les messages de cette conversation
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == prev_conv.id)
        .order_by(Message.created_at.asc())
    )
    conv_messages = msg_result.scalars().all()

    if not conv_messages:
        return

    # Formater les messages pour le LLM
    messages_text = "\n".join(
        f"{'Utilisateur' if m.role == 'user' else 'Assistant'}: {m.content}"
        for m in conv_messages
    )

    summary = await generate_summary(messages_text)
    if summary:
        prev_conv.summary = summary
        await db.flush()


# ─── CRUD Conversations ──────────────────────────────────────────────


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate = ConversationCreate(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Créer une nouvelle conversation.

    Génère le résumé du thread précédent (s'il n'en a pas déjà un).
    """
    # Générer le résumé du thread précédent si nécessaire
    await _summarize_previous_conversation(db, current_user.id)

    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationResponse],
)
async def list_conversations(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lister les conversations de l'utilisateur connecté."""
    count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.user_id == current_user.id
        )
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Modifier le titre d'une conversation."""
    conversation = await get_user_conversation(conversation_id, current_user, db)
    conversation.title = data.title
    await db.flush()
    await db.refresh(conversation)
    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Supprimer une conversation et ses messages."""
    conversation = await get_user_conversation(conversation_id, current_user, db)
    await db.delete(conversation)


# ─── Messages ────────────────────────────────────────────────────────


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=PaginatedResponse[MessageResponse],
)
async def get_messages(
    conversation_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Récupérer les messages d'une conversation."""
    await get_user_conversation(conversation_id, current_user, db)

    count_result = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post(
    "/conversations/{conversation_id}/messages",
)
async def send_message(
    conversation_id: uuid.UUID,
    content: str = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Envoyer un message et recevoir la réponse en streaming SSE.

    Accepte un message texte (content) et/ou un fichier (file) en multipart.
    Si un fichier est joint, il est uploadé et analysé avant la réponse IA.
    """
    conversation = await get_user_conversation(conversation_id, current_user, db)

    # Gérer le contenu : multipart (Form) ou JSON fallback
    message_content = content or ""

    # Si pas de contenu et pas de fichier, tenter de lire le body JSON
    if not message_content and file is None:
        return StreamingResponse(
            _error_sse("Veuillez fournir un message ou un fichier"),
            media_type="text/event-stream",
        )

    # Si un fichier est joint, l'uploader
    uploaded_doc = None
    if file is not None:
        from app.modules.documents.service import upload_document

        file_content = await file.read()
        try:
            uploaded_doc = await upload_document(
                db=db,
                user_id=current_user.id,
                filename=file.filename or "document",
                content=file_content,
                content_type=file.content_type or "application/octet-stream",
                file_size=len(file_content),
                conversation_id=conversation.id,
            )
        except ValueError as e:
            return StreamingResponse(
                _error_sse(str(e)),
                media_type="text/event-stream",
            )

    # Si pas de contenu texte mais un fichier, générer un message par défaut
    if not message_content and uploaded_doc:
        message_content = f"Analyse ce document : {uploaded_doc.original_filename}"

    # Sauvegarder le message utilisateur
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_content,
    )
    db.add(user_message)
    await db.flush()

    # Capturer les IDs avant de quitter le scope de la session FastAPI
    conv_id = conversation.id
    conv_title = conversation.title
    user_content = message_content
    user_id = current_user.id

    # Préparer les infos document pour le state
    doc_upload_info = None
    if uploaded_doc:
        doc_upload_info = {
            "document_id": str(uploaded_doc.id),
            "filename": uploaded_doc.original_filename,
            "user_id": str(user_id),
        }

    # Charger le profil et la mémoire contextuelle pour le prompt
    user_profile = await _load_profile_for_state(db, user_id)
    context_memory = await _load_context_memory(db, user_id)

    async def generate_sse() -> AsyncGenerator[str, None]:
        """Générer les événements SSE via le graphe LangGraph avec tool calling."""
        async with async_session_factory() as sse_db:
            try:
                # Émettre les événements SSE de progression document
                doc_analysis_summary = None
                if doc_upload_info:
                    yield f"data: {json.dumps({'type': 'document_upload', 'document_id': doc_upload_info['document_id'], 'filename': doc_upload_info['filename'], 'status': 'uploaded'})}\n\n"
                    yield f"data: {json.dumps({'type': 'document_status', 'document_id': doc_upload_info['document_id'], 'status': 'extracting'})}\n\n"

                    from app.modules.documents.service import analyze_document, get_document as get_doc
                    doc = await get_doc(sse_db, uuid.UUID(doc_upload_info["document_id"]))

                    if doc:
                        yield f"data: {json.dumps({'type': 'document_status', 'document_id': doc_upload_info['document_id'], 'status': 'analyzing'})}\n\n"

                        try:
                            analysis = await analyze_document(sse_db, doc)
                            doc_analysis_summary = (
                                f"Document : {doc_upload_info['filename']}\n"
                                f"Type : {doc.document_type.value if doc.document_type else 'inconnu'}\n"
                            )
                            if analysis.summary:
                                doc_analysis_summary += f"Résumé : {analysis.summary}\n"
                            if analysis.key_findings:
                                findings = analysis.key_findings
                                if isinstance(findings, list):
                                    doc_analysis_summary += "Points clés :\n" + "\n".join(f"- {f}" for f in findings[:5])

                            yield f"data: {json.dumps({'type': 'document_analysis', 'document_id': doc_upload_info['document_id'], 'summary': analysis.summary or '', 'document_type': doc.document_type.value if doc.document_type else 'autre'})}\n\n"
                        except Exception:
                            logger.exception("Erreur analyse document dans chat")
                            doc_analysis_summary = f"Document reçu : {doc_upload_info['filename']}. Erreur lors de l'analyse."
                            yield f"data: {json.dumps({'type': 'document_status', 'document_id': doc_upload_info['document_id'], 'status': 'error'})}\n\n"

                # Streamer via le graphe LangGraph avec tool calling
                full_response = ""
                async for event in stream_graph_events(
                    content=user_content,
                    conversation_id=str(conv_id),
                    user_id=user_id,
                    db=sse_db,
                    user_profile=user_profile,
                    context_memory=context_memory,
                    document_analysis_summary=doc_analysis_summary,
                    document_upload=doc_upload_info,
                ):
                    event_type = event.get("type")

                    if event_type == "token":
                        full_response += event["content"]
                        yield f"data: {json.dumps(event)}\n\n"

                    elif event_type in ("tool_call_start", "tool_call_end", "tool_call_error"):
                        yield f"data: {json.dumps(event)}\n\n"

                    elif event_type == "error":
                        yield f"data: {json.dumps(event)}\n\n"

                # Sauvegarder la réponse complète
                assistant_message = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_response,
                )
                sse_db.add(assistant_message)
                await sse_db.flush()
                await sse_db.refresh(assistant_message)

                yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id)})}\n\n"

                # Notification rapport : si une evaluation ESG vient d'etre completee
                try:
                    from app.models.esg import ESGAssessment, ESGStatusEnum
                    latest_assessment_result = await sse_db.execute(
                        select(ESGAssessment)
                        .where(
                            ESGAssessment.user_id == user_id,
                            ESGAssessment.status == ESGStatusEnum.completed,
                        )
                        .order_by(ESGAssessment.updated_at.desc())
                        .limit(1)
                    )
                    latest_completed = latest_assessment_result.scalar_one_or_none()
                    if latest_completed:
                        from app.models.report import Report
                        existing_report = await sse_db.execute(
                            select(Report).where(
                                Report.assessment_id == latest_completed.id,
                                Report.user_id == user_id,
                            ).limit(1)
                        )
                        if existing_report.scalar_one_or_none() is None:
                            yield f"data: {json.dumps({'type': 'report_suggestion', 'assessment_id': str(latest_completed.id), 'message': 'Votre evaluation ESG est terminee ! Vous pouvez generer un rapport PDF detaille.'})}\n\n"
                except Exception:
                    logger.debug("Notification rapport : aucune evaluation completee ou erreur")

                await sse_db.commit()

                # Générer un titre automatique en arrière-plan
                if conv_title == "Nouvelle conversation":
                    import asyncio

                    async def _generate_title_bg() -> None:
                        try:
                            from app.graph.nodes import generate_title

                            title = await generate_title(user_content, full_response)
                            async with async_session_factory() as title_db:
                                result = await title_db.execute(
                                    select(Conversation).where(Conversation.id == conv_id)
                                )
                                conv = result.scalar_one_or_none()
                                if conv:
                                    conv.title = title
                                    await title_db.commit()
                        except Exception:
                            pass

                    asyncio.create_task(_generate_title_bg())

            except Exception as e:
                logger.exception("Erreur SSE generate")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ─── JSON fallback pour l'ancien format ────────────────────────────


@router.post(
    "/conversations/{conversation_id}/messages/json",
)
async def send_message_json(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Envoyer un message en JSON (sans fichier) — compatibilité."""
    return await send_message(
        conversation_id=conversation_id,
        content=data.content,
        file=None,
        current_user=current_user,
        db=db,
    )
