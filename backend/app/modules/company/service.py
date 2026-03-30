"""Service de gestion du profil entreprise."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile
from app.modules.company.schemas import (
    CompanyProfileUpdate,
    CompletionResponse,
    FieldStatus,
)

# Champs d'identité et localisation (seuil 70%)
IDENTITY_FIELDS = [
    "company_name",
    "sector",
    "sub_sector",
    "employee_count",
    "annual_revenue_xof",
    "year_founded",
    "city",
    "country",
]

# Champs ESG (suivi séparé)
ESG_FIELDS = [
    "has_waste_management",
    "has_energy_policy",
    "has_gender_policy",
    "has_training_program",
    "has_financial_transparency",
    "governance_structure",
    "environmental_practices",
    "social_practices",
]

# Labels en français pour les notifications
# Champs autorisés pour la mise à jour via l'API
UPDATABLE_FIELDS = {
    "company_name", "sector", "sub_sector", "employee_count",
    "annual_revenue_xof", "city", "country", "year_founded",
    "has_waste_management", "has_energy_policy", "has_gender_policy",
    "has_training_program", "has_financial_transparency",
    "governance_structure", "environmental_practices",
    "social_practices", "notes",
}

FIELD_LABELS: dict[str, str] = {
    "company_name": "Nom de l'entreprise",
    "sector": "Secteur",
    "sub_sector": "Sous-secteur",
    "employee_count": "Nombre d'employés",
    "annual_revenue_xof": "Chiffre d'affaires",
    "city": "Ville",
    "country": "Pays",
    "year_founded": "Année de création",
    "has_waste_management": "Gestion des déchets",
    "has_energy_policy": "Politique énergétique",
    "has_gender_policy": "Politique genre",
    "has_training_program": "Programme de formation",
    "has_financial_transparency": "Transparence financière",
    "governance_structure": "Gouvernance",
    "environmental_practices": "Pratiques environnementales",
    "social_practices": "Pratiques sociales",
    "notes": "Notes",
}


def _is_field_filled(value: object) -> bool:
    """Déterminer si un champ est considéré comme rempli."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def compute_completion(profile: CompanyProfile) -> CompletionResponse:
    """Calculer les pourcentages de complétion par catégorie."""
    identity_filled: list[str] = []
    identity_missing: list[str] = []

    for field in IDENTITY_FIELDS:
        value = getattr(profile, field, None)
        if _is_field_filled(value):
            identity_filled.append(field)
        else:
            identity_missing.append(field)

    esg_filled: list[str] = []
    esg_missing: list[str] = []

    for field in ESG_FIELDS:
        value = getattr(profile, field, None)
        if _is_field_filled(value):
            esg_filled.append(field)
        else:
            esg_missing.append(field)

    identity_pct = (len(identity_filled) / len(IDENTITY_FIELDS)) * 100 if IDENTITY_FIELDS else 0
    esg_pct = (len(esg_filled) / len(ESG_FIELDS)) * 100 if ESG_FIELDS else 0
    overall_pct = (identity_pct + esg_pct) / 2

    return CompletionResponse(
        identity_completion=round(identity_pct, 1),
        esg_completion=round(esg_pct, 1),
        overall_completion=round(overall_pct, 1),
        identity_fields=FieldStatus(filled=identity_filled, missing=identity_missing),
        esg_fields=FieldStatus(filled=esg_filled, missing=esg_missing),
    )


async def get_or_create_profile(
    db: AsyncSession, user_id: uuid.UUID
) -> CompanyProfile:
    """Récupérer le profil existant ou en créer un nouveau."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CompanyProfile(user_id=user_id, country="Côte d'Ivoire")
        db.add(profile)
        await db.flush()
        await db.refresh(profile)

    return profile


async def get_profile(
    db: AsyncSession, user_id: uuid.UUID
) -> CompanyProfile | None:
    """Récupérer le profil sans le créer."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_profile(
    db: AsyncSession,
    profile: CompanyProfile,
    updates: CompanyProfileUpdate,
) -> tuple[CompanyProfile, list[dict]]:
    """Mettre à jour le profil avec les champs non-null.

    Retourne le profil mis à jour et la liste des champs modifiés.
    """
    changed_fields: list[dict] = []
    update_data = updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field not in UPDATABLE_FIELDS:
            continue
        if value is not None:
            old_value = getattr(profile, field)
            if old_value != value:
                setattr(profile, field, value)
                # Convertir les enums en string pour la sérialisation
                display_value = value.value if hasattr(value, "value") else value
                changed_fields.append({
                    "field": field,
                    "value": display_value,
                    "label": FIELD_LABELS.get(field, field),
                })

    if changed_fields:
        await db.flush()
        await db.refresh(profile)

    return profile, changed_fields
