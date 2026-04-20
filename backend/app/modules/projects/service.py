"""Service du module projects (surface API consommee par Epic 11 + Epic 14).

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].

Les 5 fonctions ci-dessous sont des stubs `NotImplementedError`. Epic 11
livrera la logique metier reelle. Anti-pattern God service (NFR64) :
toute lecture/ecriture sur les tables `projects`/`project_memberships`
doit passer par ces fonctions — aucun `select(Project)` inline dans les
consommateurs externes (matching_service Epic 14, router Epic 11...).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.enums import ProjectRoleEnum, ProjectStatusEnum
from app.modules.projects.models import Project, ProjectMembership

_SKELETON_MSG = "Story 10.2 skeleton — implemented in Epic 11 story 11-X"


# AC7 — surface d'API consommee par Epic 14 + Epic 11.


async def create_project(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    name: str,
    status: ProjectStatusEnum = ProjectStatusEnum.idea,
    description: str | None = None,
) -> Project:
    """Creer un projet (stub Epic 11).

    Epic 11 implementera : INSERT Project + event `project.created` via
    domain_events (CCC-14 D11 micro-Outbox).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def get_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> Project | None:
    """Recuperer un projet avec filtre owner (stub Epic 11).

    Epic 11 implementera : SELECT Project WHERE company_id IN (SELECT id
    FROM companies WHERE owner_user_id = ?) pour l'isolation tenant en
    complement de RLS (Story 10.5).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def list_projects_by_owner(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[Project], int]:
    """Lister les projets d'un owner paginés (stub Epic 11)."""
    raise NotImplementedError(_SKELETON_MSG)


async def add_membership(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    company_id: uuid.UUID,
    role: ProjectRoleEnum,
) -> ProjectMembership:
    """Ajouter un membership `(project, company, role)` (stub Epic 11).

    Epic 11 implementera : INSERT ProjectMembership + gestion
    IntegrityError si le triplet existe deja (UNIQUE D1).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def get_memberships_for_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
) -> list[ProjectMembership]:
    """Lister les memberships d'un projet (stub Epic 11)."""
    raise NotImplementedError(_SKELETON_MSG)
