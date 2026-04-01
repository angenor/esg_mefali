"""Schemas Pydantic pour le module Dashboard."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.action_plan.schemas import BadgeResponse


# --- Sous-sections du dashboard ---


class EsgSummary(BaseModel):
    """Resume ESG pour le dashboard."""

    score: float
    grade: str
    trend: str | None = None
    last_assessment_date: str | None = None
    pillar_scores: dict[str, float] = Field(default_factory=dict)


class CarbonSummary(BaseModel):
    """Resume carbone pour le dashboard."""

    total_tco2e: float
    year: int
    variation_percent: float | None = None
    top_category: str | None = None
    categories: dict[str, float] = Field(default_factory=dict)


class CreditSummary(BaseModel):
    """Resume credit vert pour le dashboard."""

    score: float
    grade: str
    last_calculated: str | None = None


class FinancingSummary(BaseModel):
    """Resume financements pour le dashboard."""

    recommended_funds_count: int = 0
    active_applications_count: int = 0
    application_statuses: dict[str, int] = Field(default_factory=dict)
    next_intermediary_action: dict | None = None
    has_intermediary_paths: bool = False


class NextAction(BaseModel):
    """Prochaine action pour le dashboard."""

    id: uuid.UUID
    title: str
    category: str
    due_date: str | None = None
    status: str
    intermediary_name: str | None = None
    intermediary_address: str | None = None


class ActivityEvent(BaseModel):
    """Evenement d'activite recente."""

    type: str
    title: str
    description: str | None = None
    timestamp: datetime
    related_entity_type: str | None = None
    related_entity_id: uuid.UUID | None = None


# --- Dashboard complet ---


class DashboardSummary(BaseModel):
    """Vue synthetique du dashboard."""

    esg: EsgSummary | None = None
    carbon: CarbonSummary | None = None
    credit: CreditSummary | None = None
    financing: FinancingSummary = Field(default_factory=FinancingSummary)
    next_actions: list[NextAction] = Field(default_factory=list)
    recent_activity: list[ActivityEvent] = Field(default_factory=list)
    badges: list[BadgeResponse] = Field(default_factory=list)
