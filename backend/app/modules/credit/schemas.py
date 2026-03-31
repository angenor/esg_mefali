"""Schemas Pydantic pour le module Scoring de Credit Vert."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --- Enums ---


class ConfidenceLabelEnum(str, Enum):
    """Label de confiance affichable."""

    very_low = "very_low"
    low = "low"
    medium = "medium"
    good = "good"
    excellent = "excellent"


class RecommendationImpact(str, Enum):
    """Impact d'une recommandation."""

    high = "high"
    medium = "medium"
    low = "low"


# --- Nested Schemas ---


class RecommendationItem(BaseModel):
    """Recommandation d'amelioration."""

    action: str
    impact: RecommendationImpact
    category: str


class DataSourceItem(BaseModel):
    """Source de donnees pour le scoring."""

    name: str
    available: bool
    completeness: float = Field(ge=0, le=1)
    last_updated: str | None = None


class DataSourcesResponse(BaseModel):
    """Ensemble des sources de donnees."""

    sources: list[DataSourceItem] = Field(default_factory=list)
    overall_coverage: float = Field(ge=0, le=1)


class IntermediaryInteractions(BaseModel):
    """Detail des interactions intermediaires dans un facteur."""

    contacted: int = 0
    appointments: int = 0
    submitted: int = 0
    intermediary_names: list[str] = Field(default_factory=list)


class ApplicationStatuses(BaseModel):
    """Detail des candidatures dans un facteur."""

    interested: int = 0
    submitted_via_intermediary: int = 0
    accepted: int = 0


class FactorDetail(BaseModel):
    """Detail d'un facteur de scoring."""

    score: float
    weight: float
    details: str
    intermediary_interactions: IntermediaryInteractions | None = None
    application_statuses: ApplicationStatuses | None = None


class AxisBreakdown(BaseModel):
    """Decomposition d'un axe (solvabilite ou impact vert)."""

    total: float
    factors: dict[str, FactorDetail]


class ScoreBreakdownData(BaseModel):
    """Decomposition complete du score."""

    solvability: AxisBreakdown
    green_impact: AxisBreakdown


# --- Response Schemas ---


class CreditScoreResponse(BaseModel):
    """Reponse pour un score de credit vert."""

    model_config = {"from_attributes": True}

    id: str
    version: int
    combined_score: float
    solvability_score: float
    green_impact_score: float
    confidence_level: float
    confidence_label: str
    generated_at: datetime
    valid_until: datetime


class CreditScoreWithExpiry(CreditScoreResponse):
    """Score avec indicateur d'expiration."""

    is_expired: bool = False


class CreditScoreBreakdownResponse(CreditScoreResponse):
    """Score avec decomposition complete."""

    score_breakdown: ScoreBreakdownData
    data_sources: DataSourcesResponse
    recommendations: list[RecommendationItem] = Field(default_factory=list)


class CreditScoreHistoryItem(BaseModel):
    """Element dans l'historique des scores."""

    model_config = {"from_attributes": True}

    id: str
    version: int
    combined_score: float
    solvability_score: float
    green_impact_score: float
    confidence_level: float
    confidence_label: str
    generated_at: datetime


class CreditScoreHistoryResponse(BaseModel):
    """Reponse paginee de l'historique des scores."""

    scores: list[CreditScoreHistoryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
