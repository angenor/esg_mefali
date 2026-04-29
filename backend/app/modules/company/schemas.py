"""Schemas Pydantic pour le profilage d'entreprise."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SectorEnum(str, Enum):
    """Secteurs d'activité adaptés au contexte africain."""

    agriculture = "agriculture"
    energie = "energie"
    recyclage = "recyclage"
    transport = "transport"
    construction = "construction"
    textile = "textile"
    agroalimentaire = "agroalimentaire"
    services = "services"
    commerce = "commerce"
    artisanat = "artisanat"
    autre = "autre"


class CompanyProfileResponse(BaseModel):
    """Profil d'entreprise retourné par l'API."""

    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str | None = None
    sector: SectorEnum | None = None
    sub_sector: str | None = None
    employee_count: int | None = None
    annual_revenue_xof: int | None = None
    city: str | None = None
    country: str | None = None
    year_founded: int | None = None
    has_waste_management: bool | None = None
    has_energy_policy: bool | None = None
    has_gender_policy: bool | None = None
    has_training_program: bool | None = None
    has_financial_transparency: bool | None = None
    governance_structure: str | None = None
    environmental_practices: str | None = None
    social_practices: str | None = None
    notes: str | None = None
    # Story 9.5 : champs edites manuellement, proteges contre l'ecrasement LLM.
    manually_edited_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Champs edites manuellement via PATCH /profile, proteges contre "
            "les ecrasements automatiques par le tool LLM."
        ),
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyProfileUpdate(BaseModel):
    """Mise à jour partielle du profil entreprise.

    `extra="forbid"` : rejette tout champ inconnu (422). Durcissement
    anti-tampering contre une tentative client de manipuler directement
    `manually_edited_fields` ou autres champs backend-only (review 9.5 P5).
    """

    model_config = ConfigDict(extra="forbid")

    company_name: str | None = Field(None, max_length=255)
    sector: SectorEnum | None = None
    sub_sector: str | None = Field(None, max_length=255)
    employee_count: int | None = Field(None, ge=0, le=100_000)
    annual_revenue_xof: int | None = Field(None, ge=0, le=10_000_000_000_000)
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    year_founded: int | None = Field(None, ge=1900, le=2100)

    @field_validator(
        "company_name",
        "sub_sector",
        "city",
        "country",
        "governance_structure",
        "environmental_practices",
        "social_practices",
        "notes",
        mode="before",
    )
    @classmethod
    def _strip_or_reject_blank(cls, value: object) -> object:
        # BUG-V7.1-002 / V7-002 : defense en profondeur cote REST contre
        # whitespace-only ou empty string qui ecrasaient les valeurs en BDD
        # (le tool LLM update_company_profile etait deja durci par BUG-V6-011).
        # V8-AXE5 review : strip etend aux caracteres invisibles (zero-width
        # space, BOM, word joiner) que str.strip() ignore par defaut et qui
        # rendraient un payload "​" visuellement vide mais accepte.
        if value is None:
            return None
        if isinstance(value, str):
            # V8-AXE5 review : zero-width / BOM / word joiner / NBSP
            invisible_chars = "​‌‍⁠﻿ "
            stripped = value.strip().strip(invisible_chars).strip()
            if not stripped:
                raise ValueError(
                    "Le champ ne peut pas etre vide ou contenir uniquement des espaces"
                )
            return stripped
        return value

    @field_validator(
        "employee_count", "annual_revenue_xof", "year_founded",
        mode="before",
    )
    @classmethod
    def _coerce_int_strings(cls, value: object) -> object:
        """BUG-V3-002 : coerce string numerique en int (defense en profondeur).

        Le frontend `ProfileField.vue` envoie deja un Number, mais un client
        tiers (extension, test manuel, curl) pourrait envoyer `"15"` (string).
        Pydantic v2 coerce par defaut mais on blinde ici pour garantir que
        l'entree string numerique ("15", " 15 ") soit stockee en int, et que
        les strings non-numeriques levent une erreur claire (422).
        """
        if value is None:
            return value
        # Rejeter explicitement les bools : True/False sont des int en Python,
        # mais un profil ne doit pas accepter `{"employee_count": true}` silencieusement.
        if isinstance(value, bool):
            raise ValueError(f"Valeur numerique invalide : {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"Valeur numerique invalide : {value!r}"
                ) from exc
        return value
    has_waste_management: bool | None = None
    has_energy_policy: bool | None = None
    has_gender_policy: bool | None = None
    has_training_program: bool | None = None
    has_financial_transparency: bool | None = None
    governance_structure: str | None = Field(None, max_length=2000)
    environmental_practices: str | None = Field(None, max_length=2000)
    social_practices: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=5000)


class FieldStatus(BaseModel):
    """Champs remplis et manquants d'une catégorie."""

    filled: list[str]
    missing: list[str]


class CompletionResponse(BaseModel):
    """Pourcentage de complétion par catégorie."""

    identity_completion: float
    esg_completion: float
    overall_completion: float
    identity_fields: FieldStatus
    esg_fields: FieldStatus


class IdentityExtraction(BaseModel):
    """Extraction des champs d'identité et localisation."""

    company_name: str | None = None
    sector: SectorEnum | None = None
    sub_sector: str | None = None
    employee_count: int | None = None
    annual_revenue_xof: int | None = None
    city: str | None = None
    country: str | None = None
    year_founded: int | None = None


class ESGExtraction(BaseModel):
    """Extraction des champs ESG."""

    has_waste_management: bool | None = None
    has_energy_policy: bool | None = None
    has_gender_policy: bool | None = None
    has_training_program: bool | None = None
    has_financial_transparency: bool | None = None
    governance_structure: str | None = None
    environmental_practices: str | None = None
    social_practices: str | None = None


class ProfileExtraction(BaseModel):
    """Résultat de l'extraction structurée depuis un message utilisateur.

    Structuré en sous-objets pour limiter le nombre de champs nullable
    au niveau racine (compatibilité multi-providers LLM).
    """

    identity: IdentityExtraction = Field(default_factory=IdentityExtraction)
    esg: ESGExtraction = Field(default_factory=ESGExtraction)

    def flat_dict(self) -> dict:
        """Retourner un dictionnaire plat avec tous les champs non-null."""
        result: dict = {}
        for field, value in self.identity.model_dump().items():
            if value is not None:
                result[field] = value
        for field, value in self.esg.model_dump().items():
            if value is not None:
                result[field] = value
        return result
