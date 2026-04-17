"""Schemas Pydantic pour le module documents."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatusEnum(str, Enum):
    """Statuts de traitement d'un document."""

    uploaded = "uploaded"
    processing = "processing"
    analyzed = "analyzed"
    error = "error"


class DocumentTypeEnum(str, Enum):
    """Types de documents identifiés par l'analyse."""

    statuts_juridiques = "statuts_juridiques"
    rapport_activite = "rapport_activite"
    facture = "facture"
    contrat = "contrat"
    politique_interne = "politique_interne"
    bilan_financier = "bilan_financier"
    autre = "autre"


# --- Schemas de sortie de l'analyse IA ---


class ESGRelevantInfo(BaseModel):
    """Informations ESG extraites du document."""

    environmental: list[str] = Field(default_factory=list)
    social: list[str] = Field(default_factory=list)
    governance: list[str] = Field(default_factory=list)


class DocumentAnalysisOutput(BaseModel):
    """Sortie structurée de la chaîne d'analyse LangChain."""

    document_type: DocumentTypeEnum = Field(
        description="Type de document identifié"
    )
    summary: str = Field(
        description="Résumé du document en français (3-5 phrases)"
    )
    key_findings: list[str] = Field(
        description="Points clés extraits (5-10 éléments)"
    )
    structured_data: dict = Field(
        default_factory=dict,
        description="Données structurées extraites (chiffres clés, dates, montants)",
    )
    esg_relevant_info: ESGRelevantInfo = Field(
        default_factory=ESGRelevantInfo,
        description="Informations pertinentes ESG classées par pilier",
    )


# --- Schemas de réponse API ---


class DocumentAnalysisResponse(BaseModel):
    """Analyse d'un document retournée par l'API."""

    summary: str | None = None
    key_findings: list | None = None
    structured_data: dict | None = None
    esg_relevant_info: dict | None = None
    analyzed_at: str | None = None

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    """Document retourné dans les listes."""

    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    status: DocumentStatusEnum
    document_type: DocumentTypeEnum | None = None
    has_analysis: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(BaseModel):
    """Document avec son analyse complète."""

    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    status: DocumentStatusEnum
    document_type: DocumentTypeEnum | None = None
    created_at: datetime
    analysis: DocumentAnalysisResponse | None = None

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Réponse après upload de fichiers."""

    documents: list[DocumentResponse]


class DocumentListResponse(BaseModel):
    """Liste paginée de documents."""

    documents: list[DocumentResponse]
    total: int
    page: int
    limit: int


class ReanalyzeResponse(BaseModel):
    """Réponse après relance d'analyse."""

    id: uuid.UUID
    status: DocumentStatusEnum
    message: str


class QuotaStatus(BaseModel):
    """Statut de quota de stockage d'un utilisateur (dette spec 004 §3.2)."""

    bytes_used: int = Field(description="Octets utilisés")
    bytes_limit: int = Field(description="Limite d'octets")
    docs_count: int = Field(description="Nombre de documents")
    docs_limit: int = Field(description="Limite de documents")
    usage_percent: int = Field(
        ge=0,
        le=100,
        description="Pourcentage du quota le plus contraignant",
    )
