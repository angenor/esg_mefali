"""Schemas Pydantic pour le module Dossiers de Candidature."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.application import STATUS_LABELS


# --- Enumerations (paralleles aux modeles SQLAlchemy) ---


class TargetTypeEnum(str, Enum):
    fund_direct = "fund_direct"
    intermediary_bank = "intermediary_bank"
    intermediary_agency = "intermediary_agency"
    intermediary_developer = "intermediary_developer"


class ApplicationStatusEnum(str, Enum):
    draft = "draft"
    preparing_documents = "preparing_documents"
    in_progress = "in_progress"
    review = "review"
    ready_for_intermediary = "ready_for_intermediary"
    ready_for_fund = "ready_for_fund"
    submitted_to_intermediary = "submitted_to_intermediary"
    submitted_to_fund = "submitted_to_fund"
    under_review = "under_review"
    accepted = "accepted"
    rejected = "rejected"


class SectionStatusEnum(str, Enum):
    not_generated = "not_generated"
    generated = "generated"
    validated = "validated"


# --- Schemas de creation ---


class ApplicationCreate(BaseModel):
    """Creation d'un dossier de candidature."""

    fund_id: uuid.UUID
    match_id: uuid.UUID | None = None
    intermediary_id: uuid.UUID | None = None


# --- Schemas de mise a jour ---


class ApplicationStatusUpdate(BaseModel):
    """Mise a jour du statut d'un dossier."""

    status: ApplicationStatusEnum


class SectionGenerateRequest(BaseModel):
    """Demande de generation d'une section."""

    section_key: str = Field(min_length=1)


class SectionUpdateRequest(BaseModel):
    """Mise a jour manuelle d'une section."""

    content: str | None = None
    status: SectionStatusEnum | None = None


class ExportRequest(BaseModel):
    """Demande d'export."""

    format: str = Field(pattern="^(pdf|docx)$")


# --- Schemas de reponse ---


class SectionResponse(BaseModel):
    """Reponse section generee/modifiee."""

    section_key: str
    title: str
    content: str | None = None
    status: str
    updated_at: datetime | None = None


class FundInfo(BaseModel):
    """Info fonds dans un dossier."""

    id: uuid.UUID
    name: str
    organization: str

    model_config = {"from_attributes": True}


class IntermediaryInfo(BaseModel):
    """Info intermediaire dans un dossier."""

    id: uuid.UUID
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    physical_address: str | None = None

    model_config = {"from_attributes": True}


class MatchInfo(BaseModel):
    """Info match dans un dossier."""

    id: uuid.UUID
    compatibility_score: int

    model_config = {"from_attributes": True}


class SectionsProgress(BaseModel):
    """Progression des sections."""

    total: int
    generated: int
    validated: int


class ChecklistItem(BaseModel):
    """Element de checklist."""

    key: str
    name: str
    status: str
    document_id: uuid.UUID | None = None
    required_by: str


class ApplicationSummary(BaseModel):
    """Resume d'un dossier pour les listes."""

    id: uuid.UUID
    fund_name: str
    intermediary_name: str | None = None
    target_type: TargetTypeEnum
    status: ApplicationStatusEnum
    status_label: str
    sections_progress: SectionsProgress
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    """Detail complet d'un dossier."""

    id: uuid.UUID
    fund: FundInfo
    intermediary: IntermediaryInfo | None = None
    match: MatchInfo | None = None
    target_type: TargetTypeEnum
    status: ApplicationStatusEnum
    status_label: str
    sections: dict
    checklist: list[ChecklistItem]
    intermediary_prep: dict | None = None
    simulation: dict | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    """Liste paginee de dossiers."""

    items: list[ApplicationSummary]
    total: int


class ApplicationStatusResponse(BaseModel):
    """Reponse apres mise a jour du statut."""

    id: uuid.UUID
    status: ApplicationStatusEnum
    status_label: str
    updated_at: datetime


# --- Helpers ---


def get_status_label(status: str) -> str:
    """Retourner le libelle francais d'un statut."""
    return STATUS_LABELS.get(status, status)


def compute_sections_progress(sections: dict) -> SectionsProgress:
    """Calculer la progression des sections."""
    total = len(sections)
    generated = sum(
        1 for s in sections.values()
        if s.get("status") in ("generated", "validated")
    )
    validated = sum(
        1 for s in sections.values()
        if s.get("status") == "validated"
    )
    return SectionsProgress(total=total, generated=generated, validated=validated)
