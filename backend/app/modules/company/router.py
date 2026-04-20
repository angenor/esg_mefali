"""Router FastAPI pour le module company (profil entreprise)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.company.schemas import (
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompletionResponse,
)
from app.modules.company.service import (
    compute_completion,
    get_or_create_profile,
    update_profile,
)

router = APIRouter()


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyProfileResponse:
    """Récupérer le profil entreprise (le crée s'il n'existe pas)."""
    profile = await get_or_create_profile(db, current_user.id)
    await db.commit()
    return CompanyProfileResponse.model_validate(profile)


@router.patch("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    updates: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyProfileResponse:
    """Mettre à jour le profil entreprise (mise à jour partielle, source=manual).

    Story 9.5 : source="manual" marque chaque champ dans `manually_edited_fields`
    pour empecher l'ecrasement ulterieur par le tool LLM `update_company_profile`.
    """
    profile = await get_or_create_profile(db, current_user.id)
    updated_profile, _changed, _skipped = await update_profile(
        db, profile, updates, source="manual",
    )
    await db.commit()
    await db.refresh(updated_profile)
    return CompanyProfileResponse.model_validate(updated_profile)


@router.get("/profile/completion", response_model=CompletionResponse)
async def get_completion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompletionResponse:
    """Récupérer les pourcentages de complétion du profil."""
    profile = await get_or_create_profile(db, current_user.id)
    await db.commit()
    return compute_completion(profile)
