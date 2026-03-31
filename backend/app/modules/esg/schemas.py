"""Schemas Pydantic pour le module ESG."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ESGStatusEnum(str, Enum):
    """Statut d'une evaluation ESG."""

    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"


class CriteriaScoreDetail(BaseModel):
    """Detail du score d'un critere."""

    score: int = Field(ge=0, le=10)
    justification: str = ""
    sources: list[str] = Field(default_factory=list)


class PillarDetail(BaseModel):
    """Detail du score d'un pilier."""

    raw_score: float
    weighted_score: float
    weights_applied: dict[str, float] = Field(default_factory=dict)


class ESGAssessmentCreate(BaseModel):
    """Creation d'une evaluation ESG."""

    conversation_id: uuid.UUID | None = None


class ESGAssessmentResponse(BaseModel):
    """Evaluation ESG retournee par l'API."""

    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    version: int = 1
    status: ESGStatusEnum = ESGStatusEnum.draft
    sector: str
    overall_score: float | None = None
    environment_score: float | None = None
    social_score: float | None = None
    governance_score: float | None = None
    assessment_data: dict | None = None
    recommendations: list | None = None
    strengths: list | None = None
    gaps: list | None = None
    sector_benchmark: dict | None = None
    current_pillar: str | None = None
    evaluated_criteria: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ESGAssessmentSummary(BaseModel):
    """Resume d'une evaluation pour les listes."""

    id: uuid.UUID
    version: int
    status: ESGStatusEnum
    sector: str
    overall_score: float | None = None
    environment_score: float | None = None
    social_score: float | None = None
    governance_score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ESGAssessmentList(BaseModel):
    """Liste paginee d'evaluations."""

    data: list[ESGAssessmentSummary]
    total: int
    page: int
    limit: int


class CriteriaScoreResponse(BaseModel):
    """Score d'un critere dans la reponse detaillee."""

    code: str
    label: str
    score: int = Field(ge=0, le=10)
    max: int = 10
    weight: float = 1.0


class PillarScoreResponse(BaseModel):
    """Score d'un pilier dans la reponse detaillee."""

    score: float
    criteria: list[CriteriaScoreResponse]


class ScoreResponse(BaseModel):
    """Reponse detaillee du score ESG."""

    assessment_id: uuid.UUID
    status: ESGStatusEnum
    overall_score: float
    color: str
    pillars: dict[str, PillarScoreResponse]
    strengths_count: int = 0
    gaps_count: int = 0
    recommendations_count: int = 0


class EvaluateRequest(BaseModel):
    """Requete d'evaluation conversationnelle."""

    message: str = Field(min_length=1, max_length=5000)


class EvaluateResponse(BaseModel):
    """Reponse de progression de l'evaluation."""

    assessment_id: uuid.UUID
    status: ESGStatusEnum
    current_pillar: str | None = None
    evaluated_criteria: list[str] = Field(default_factory=list)
    progress_percent: float = 0.0
    total_criteria: int = 30


class BenchmarkResponse(BaseModel):
    """Benchmark sectoriel."""

    sector: str
    sector_label: str
    sample_size: str = "estimation"
    averages: dict[str, float]
    top_criteria: list[str]
    weak_criteria: list[str]
