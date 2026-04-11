"""Router d'authentification : register, login, refresh, me."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.geolocation import (
    SUPPORTED_COUNTRIES,
    detect_country_from_request,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.company import CompanyProfile
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


@router.get("/detect-country")
async def detect_country(request: Request) -> dict:
    """Détecter le pays de l'utilisateur via son IP publique.

    Retourne la liste des pays supportés et le pays détecté (si possible).
    Utilisé par le frontend pour pré-remplir le dropdown à l'inscription.
    """
    detected = await detect_country_from_request(request)
    return {
        "detected_country": detected,
        "supported_countries": SUPPORTED_COUNTRIES,
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Créer un nouveau compte utilisateur."""
    # Vérifier l'unicité de l'email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    # Déterminer le pays : priorité à la valeur envoyée par le frontend
    # (saisie par l'utilisateur dans le dropdown), sinon fallback sur la
    # détection IP côté serveur.
    country = data.country
    if not country:
        country = await detect_country_from_request(request)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Initialiser le profil entreprise avec le nom fourni à l'inscription
    # afin que le LLM y ait accès dès la première conversation.
    profile = CompanyProfile(
        user_id=user.id,
        company_name=data.company_name,
        country=country,
    )
    db.add(profile)
    await db.flush()

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authentifier un utilisateur et retourner les jetons."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest) -> dict:
    """Rafraîchir le jeton d'accès."""
    user_id = decode_token(data.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré",
        )

    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Récupérer le profil de l'utilisateur connecté."""
    return current_user
