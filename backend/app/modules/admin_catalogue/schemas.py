"""Schemas Pydantic v2 pour le module admin_catalogue.

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.admin_catalogue.enums import (
    CatalogueActionEnum,
    NodeStateEnum,
    WorkflowLevelEnum,
)

__all__ = [
    "AdminCatalogueAuditTrailResponse",
    "CatalogueActionEnum",
    "CriterionCreate",
    "CriterionDerivationRuleCreate",
    "CriterionDerivationRuleResponse",
    "CriterionResponse",
    "FactTypeListResponse",
    "NodeStateEnum",
    "PackCreate",
    "PackResponse",
    "ReferentialCreate",
    "ReferentialResponse",
    "WorkflowLevelEnum",
]


# ----- Create schemas (body POST /api/admin/catalogue/*) -----


class CriterionCreate(BaseModel):
    """Body du POST /api/admin/catalogue/criteria (Epic 13.1)."""

    code: str = Field(min_length=1, max_length=64)
    label_fr: str = Field(min_length=1, max_length=255)
    dimension: str = Field(min_length=1, max_length=32)
    description: str | None = None


class ReferentialCreate(BaseModel):
    """Body du POST /api/admin/catalogue/referentials (Epic 13.2)."""

    code: str = Field(min_length=1, max_length=64)
    label_fr: str = Field(min_length=1, max_length=255)
    description: str | None = None


class PackCreate(BaseModel):
    """Body du POST /api/admin/catalogue/packs (Epic 13.3)."""

    code: str = Field(min_length=1, max_length=64)
    label_fr: str = Field(min_length=1, max_length=255)


class CriterionDerivationRuleCreate(BaseModel):
    """Body du POST /api/admin/catalogue/rules (Epic 13.1bis)."""

    criterion_id: uuid.UUID
    rule_type: Literal[
        "threshold", "boolean_expression", "aggregate", "qualitative_check"
    ]
    rule_json: dict
    version: int = 1


# ----- Response schemas -----


class CriterionResponse(BaseModel):
    """Representation complete d'un Criterion (Epic 13)."""

    id: uuid.UUID
    code: str
    label_fr: str
    description: str | None = None
    dimension: str
    workflow_state: str
    is_published: bool
    source_url: str | None = None
    source_accessed_at: datetime | None = None
    source_version: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReferentialResponse(BaseModel):
    """Representation complete d'un Referential (Epic 13)."""

    id: uuid.UUID
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


class PackResponse(BaseModel):
    """Representation complete d'un Pack (Epic 13)."""

    id: uuid.UUID
    code: str
    label_fr: str
    workflow_state: str
    is_published: bool
    source_url: str | None = None
    source_accessed_at: datetime | None = None
    source_version: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CriterionDerivationRuleResponse(BaseModel):
    """Representation complete d'une CriterionDerivationRule (Epic 13)."""

    id: uuid.UUID
    criterion_id: uuid.UUID
    rule_type: str
    rule_json: dict
    version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminCatalogueAuditTrailResponse(BaseModel):
    """Representation d'un evenement audit trail (Story 10.12)."""

    id: uuid.UUID
    actor_user_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    workflow_level: str
    workflow_state_before: str | None = None
    workflow_state_after: str | None = None
    changes_before: dict | None = None
    changes_after: dict | None = None
    ts: datetime
    correlation_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class FactTypeListResponse(BaseModel):
    """Reponse du GET /api/admin/catalogue/fact-types (FR17)."""

    fact_types: list[str]
