"""Schemas Pydantic pour le chat et les conversations."""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ConversationCreate(BaseModel):
    """Données pour créer une conversation."""

    title: str = Field(default="Nouvelle conversation", min_length=1, max_length=255)


class ConversationUpdate(BaseModel):
    """Données pour modifier une conversation."""

    title: str = Field(min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    """Conversation retournée par l'API."""

    id: uuid.UUID
    title: str
    current_module: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Données pour envoyer un message."""

    content: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Message retourné par l'API."""

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique."""

    items: list[T]
    total: int
    page: int
    limit: int
