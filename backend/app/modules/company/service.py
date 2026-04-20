"""Service de gestion du profil entreprise."""

import logging
import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile
from app.models.user import User
from app.modules.company.schemas import (
    CompanyProfileUpdate,
    CompletionResponse,
    FieldStatus,
)

logger = logging.getLogger(__name__)

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
    """Récupérer le profil existant ou en créer un nouveau.

    Si le profil n'existe pas ou n'a pas de nom d'entreprise, initialise
    le champ `company_name` depuis `User.company_name` (valeur fournie
    à l'inscription), pour que le LLM puisse le voir dès la première
    conversation.
    """
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        profile = CompanyProfile(
            user_id=user_id,
            company_name=user.company_name if user else None,
        )
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
    elif not profile.company_name:
        # Backfill pour les profils existants créés avant cette correction
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user and user.company_name:
            profile.company_name = user.company_name
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
    source: Literal["manual", "llm"] = "manual",
) -> tuple[CompanyProfile, list[dict], list[dict]]:
    """Mettre à jour le profil avec les champs non-null.

    Story 9.5 (P1 #7) : le parametre `source` discrimine l'origine de l'ecriture.
    - `source="manual"` : appel via PATCH /api/company/profile. Le champ est
      systematiquement ecrit et ajoute a `profile.manually_edited_fields`.
    - `source="llm"` : appel via le tool LangChain `update_company_profile`.
      Les champs deja presents dans `manually_edited_fields` sont ignores
      (log WARNING + entree dans `skipped_fields` renvoyee) pour garantir
      que « l'edition manuelle prevaut » (spec 003 §3.6).

    Retourne un 3-uplet `(profile, changed_fields, skipped_fields)` :
    - `changed_fields` : champs effectivement modifies.
    - `skipped_fields` : champs skippes car proteges manuel (toujours vide
      si `source="manual"` — le chemin manuel n'est jamais bloque).
    """
    changed_fields: list[dict] = []
    skipped_fields: list[dict] = []
    update_data = updates.model_dump(exclude_unset=True)
    # Copie defensive : jamais muter la liste de la BDD en place (immutabilite).
    existing_manual = list(profile.manually_edited_fields or [])

    for field, value in update_data.items():
        if field not in UPDATABLE_FIELDS:
            continue
        if value is None:
            continue

        old_value = getattr(profile, field)

        # Chemin LLM : skip si le champ a deja ete edite manuellement.
        if source == "llm" and field in existing_manual:
            if old_value != value:
                # Borner la valeur loggee a 200 chars : evite de polluer les logs
                # avec les contenus Text (governance_structure, social_practices,
                # notes, etc.) et reduit le risque d'exposition PII (review 9.5 P8).
                old_repr = repr(old_value)
                attempted_repr = repr(value)
                if len(old_repr) > 200:
                    old_repr = old_repr[:200] + "...(truncated)"
                if len(attempted_repr) > 200:
                    attempted_repr = attempted_repr[:200] + "...(truncated)"
                logger.warning(
                    "Tool LLM tente d'ecraser un champ edite manuellement "
                    "(skip) : field=%s old=%s attempted=%s profile_id=%s",
                    field, old_repr, attempted_repr, profile.id,
                )
                display_attempted = value.value if hasattr(value, "value") else value
                display_current = (
                    old_value.value if hasattr(old_value, "value") else old_value
                )
                skipped_fields.append({
                    "field": field,
                    "attempted_value": display_attempted,
                    "current_value": display_current,
                    "label": FIELD_LABELS.get(field, field),
                })
            # IMPORTANT : continue pour ne pas executer la branche d'ecriture.
            continue

        # Chemin manuel OU chemin LLM sur champ non-protege : ecriture normale.
        if old_value != value:
            setattr(profile, field, value)
            display_value = value.value if hasattr(value, "value") else value
            changed_fields.append({
                "field": field,
                "value": display_value,
                "label": FIELD_LABELS.get(field, field),
            })

        # Chemin manuel : marquer le champ comme protege (idempotent), meme si
        # la valeur n'a pas change. Un PATCH explicite sur /profile vaut
        # validation manuelle de l'utilisateur (cf. review 9.5 D1).
        if source == "manual" and field not in existing_manual:
            existing_manual.append(field)

    # Persister la liste manually_edited_fields si elle a evolue (AC2).
    manual_list_changed = False
    if source == "manual":
        new_manual = sorted(existing_manual)  # ordre stable pour les tests
        current_manual = sorted(profile.manually_edited_fields or [])
        if new_manual != current_manual:
            profile.manually_edited_fields = new_manual
            manual_list_changed = True

    if changed_fields or manual_list_changed:
        await db.flush()
        await db.refresh(profile)

    return profile, changed_fields, skipped_fields
