"""Schemas Pydantic pour le profilage d'entreprise."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyProfileUpdate(BaseModel):
    """Mise à jour partielle du profil entreprise."""

    company_name: str | None = Field(None, max_length=255)
    sector: SectorEnum | None = None
    sub_sector: str | None = Field(None, max_length=255)
    employee_count: int | None = Field(None, ge=0, le=100_000)
    annual_revenue_xof: int | None = Field(None, ge=0, le=10_000_000_000_000)
    city: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    year_founded: int | None = Field(None, ge=1900, le=2100)
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
