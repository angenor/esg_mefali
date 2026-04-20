"""Dépendances communes pour les routers FastAPI."""

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rls import apply_rls_context
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extraire et valider l'utilisateur courant depuis le token JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
        )

    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou inactif",
        )

    # Story 10.5 — injecter le contexte RLS (app.current_user_id + app.user_role)
    # sur la session courante pour que les policies tenant_isolation (migration 024)
    # filtrent automatiquement les 4 tables sensibles. Appelé uniquement après
    # authentification réussie : un 401 ne positionne jamais le contexte, la
    # session reste à l'état reset (fail-safe).
    await apply_rls_context(db, user)

    # Exposer l'utilisateur dans request.state pour le rate limiter SlowAPI (FR-013)
    request.state.user = user

    return user
