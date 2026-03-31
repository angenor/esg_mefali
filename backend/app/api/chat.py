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
from app.modules.company.schemas import CompanyProfileUpdate
from app.modules.company.service import (
    compute_completion,
    get_or_create_profile,
    update_profile,
)
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


async def stream_llm_tokens(
    content: str,
    conversation_id: str,
    user_profile: dict | None = None,
    context_memory: list[str] | None = None,
    document_analysis_summary: str | None = None,
) -> AsyncGenerator[str, None]:
    """Streamer les tokens du LLM un par un.

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


async def extract_and_update_profile(
    user_message: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[list[dict], dict | None]:
    """Extraire les infos de profil et mettre à jour en base.

    Retourne (changed_fields, completion_data) ou ([], None) si rien extrait.
    """
    from app.chains.extraction import extract_profile_from_message

    profile = await get_or_create_profile(db, user_id)

    # Sérialiser le profil actuel pour le contexte
    current_profile = {
        field: getattr(profile, field)
        for field in [
            "company_name", "sector", "sub_sector", "employee_count",
            "annual_revenue_xof", "city", "country", "year_founded",
            "has_waste_management", "has_energy_policy", "has_gender_policy",
            "has_training_program", "has_financial_transparency",
            "governance_structure", "environmental_practices",
            "social_practices", "notes",
        ]
        if getattr(profile, field) is not None
    }
    # Convertir les enums
    for k, v in current_profile.items():
        if hasattr(v, "value"):
            current_profile[k] = v.value

    extraction = await extract_profile_from_message(user_message, current_profile)

    # Récupérer les champs extraits (dictionnaire plat, non-null uniquement)
    extraction_data = extraction.flat_dict()

    if not extraction_data:
        return [], None

    updates = CompanyProfileUpdate(**extraction_data)
    _, changed_fields = await update_profile(db, profile, updates)

    if not changed_fields:
        return [], None

    completion = compute_completion(profile)
    completion_data = {
        "identity_completion": completion.identity_completion,
        "esg_completion": completion.esg_completion,
        "overall_completion": completion.overall_completion,
    }

    return changed_fields, completion_data


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

    # Détecter si le message contient des infos de profil
    from app.graph.nodes import _detect_profile_info
    should_extract = _detect_profile_info(user_content)

    # Charger le profil et la mémoire contextuelle pour le prompt
    user_profile = await _load_profile_for_state(db, user_id)
    context_memory = await _load_context_memory(db, user_id)

    async def generate_sse() -> AsyncGenerator[str, None]:
        """Générer les événements SSE avec streaming token par token."""
        async with async_session_factory() as sse_db:
            try:
                # Émettre les événements SSE de progression document
                if doc_upload_info:
                    yield f"data: {json.dumps({'type': 'document_upload', 'document_id': doc_upload_info['document_id'], 'filename': doc_upload_info['filename'], 'status': 'uploaded'})}\n\n"
                    yield f"data: {json.dumps({'type': 'document_status', 'document_id': doc_upload_info['document_id'], 'status': 'extracting'})}\n\n"

                    # Lancer l'analyse du document
                    from app.modules.documents.service import analyze_document, get_document as get_doc
                    doc = await get_doc(sse_db, uuid.UUID(doc_upload_info["document_id"]))
                    doc_analysis_summary = None

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
                else:
                    doc_analysis_summary = None

                # Streamer les tokens du LLM avec profil + mémoire + contexte document
                full_response = ""
                async for token in stream_llm_tokens(
                    user_content, str(conv_id), user_profile, context_memory,
                    document_analysis_summary=doc_analysis_summary,
                ):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

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

                # Extraction de profil en parallèle (après le streaming)
                if should_extract:
                    try:
                        changed_fields, completion_data = await extract_and_update_profile(
                            user_content, user_id, sse_db,
                        )

                        for field_update in changed_fields:
                            yield f"data: {json.dumps({'type': 'profile_update', **field_update})}\n\n"

                        if completion_data:
                            yield f"data: {json.dumps({'type': 'profile_completion', **completion_data})}\n\n"
                    except Exception:
                        logger.exception("Erreur extraction profil")

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
