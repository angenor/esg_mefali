"""Schemas Pydantic v2 pour le module projects.

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.enums import ProjectRoleEnum, ProjectStatusEnum

__all__ = [
    "ProjectCreate",
    "ProjectResponse",
    "ProjectSummary",
    "ProjectList",
    "ProjectMembershipCreate",
    "ProjectMembershipResponse",
    "ProjectStatusEnum",
    "ProjectRoleEnum",
]


class ProjectCreate(BaseModel):
    """Creation d'un projet (consomme par POST /api/projects)."""

    name: str = Field(min_length=1, max_length=255)
    company_id: uuid.UUID
    status: ProjectStatusEnum = ProjectStatusEnum.idea
    description: str | None = None


class ProjectResponse(BaseModel):
    """Representation complete d'un projet (consumed Epic 11)."""

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    status: ProjectStatusEnum
    version_number: int
    description: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """Resume d'un projet pour les listes."""

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    status: ProjectStatusEnum
    version_number: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """Liste paginee de projets (pattern ESGAssessmentList)."""

    data: list[ProjectSummary]
    total: int
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=50)


class ProjectMembershipCreate(BaseModel):
    """Creation d'un membership projet."""

    company_id: uuid.UUID
    role: ProjectRoleEnum


class ProjectMembershipResponse(BaseModel):
    """Representation d'un membership projet."""

    id: uuid.UUID
    project_id: uuid.UUID
    company_id: uuid.UUID
    role: ProjectRoleEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
