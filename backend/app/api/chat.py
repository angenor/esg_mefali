"""Router chat : CRUD conversations, envoi de messages avec streaming SSE."""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
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
    En production, elle utilise le graphe compilé avec streaming.
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
    """Créer une nouvelle conversation."""
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
    # Compter le total
    count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(
            Conversation.user_id == current_user.id
        )
    )
    total = count_result.scalar_one()

    # Récupérer la page
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
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Envoyer un message et recevoir la réponse en streaming SSE."""
    conversation = await get_user_conversation(conversation_id, current_user, db)

    # Sauvegarder le message utilisateur
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    await db.flush()

    async def generate_sse() -> AsyncGenerator[str, None]:
        """Générer les événements SSE."""
        try:
            # Invoquer le graphe LangGraph
            response_content = await invoke_graph(
                data.content, str(conversation.id)
            )

            # Sauvegarder la réponse de l'assistant
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_content,
            )
            db.add(assistant_message)
            await db.flush()
            await db.refresh(assistant_message)

            # Envoyer les tokens (pour la v1, on envoie la réponse complète)
            yield f"data: {json.dumps({'type': 'token', 'content': response_content})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
