"""Schemas Pydantic v2 pour le module maturity.

Story 10.3 - module `maturity/` squelette.
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.maturity.enums import (
    MaturityChangeDirectionEnum,
    MaturityWorkflowStateEnum,
)

__all__ = [
    "AdminMaturityRequirementResponse",
    "FormalizationPlanResponse",
    "FormalizationPlanStep",
    "MaturityChangeDirectionEnum",
    "MaturityLevelDeclaration",
    "MaturityLevelResponse",
    "MaturityWorkflowStateEnum",
]


class MaturityLevelDeclaration(BaseModel):
    """Body du POST /api/maturity/declare (self-declaration Epic 12.1)."""

    level: str = Field(min_length=1, max_length=32)


class MaturityLevelResponse(BaseModel):
    """Representation complete d'un AdminMaturityLevel (Epic 12)."""

    id: uuid.UUID
    level: int
    code: str
    label_fr: str
    description: str | None = None
    workflow_state: str
    is_published: bool
    source_url: str | None = None
    source_accessed_at: datetime | None = None
    source_version: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FormalizationPlanStep(BaseModel):
    """Structure d'une etape d'un plan de formalisation (Epic 12.3 AC1)."""

    step: str
    cost_xof: int | None = None
    duration_days: int | None = None
    coordinates: dict | None = None


class FormalizationPlanResponse(BaseModel):
    """Representation d'un FormalizationPlan (Epic 12.3)."""

    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    current_level_id: uuid.UUID | None = None
    target_level_id: uuid.UUID | None = None
    steps: list[FormalizationPlanStep] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminMaturityRequirementResponse(BaseModel):
    """Representation d'une AdminMaturityRequirement (Epic 12.3 data-driven)."""

    id: uuid.UUID
    country: str
    level_id: uuid.UUID
    requirements_json: dict
    is_published: bool

    model_config = ConfigDict(from_attributes=True)
