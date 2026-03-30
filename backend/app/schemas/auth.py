"""Schemas Pydantic pour l'authentification."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Données requises pour l'inscription."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Données requises pour la connexion."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Données requises pour le rafraîchissement du token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Réponse contenant les jetons d'authentification."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Profil utilisateur retourné par l'API."""

    id: uuid.UUID
    email: str
    full_name: str
    company_name: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
