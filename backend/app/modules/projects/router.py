"""Router REST pour le module projects (endpoints stubs 404/501).

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].

Comportement (AC3) — ordre des statuts : 401 -> 404 -> 501 :
- Sans JWT valide -> 401 (Depends(get_current_user) prime).
- Avec JWT mais `ENABLE_PROJECT_MODEL=false` -> 404 (feature masquee).
- Avec JWT et flag `true` -> 501 (squelette, Epic 11 livrera la logique).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.core.feature_flags import check_project_model_enabled
from app.models.user import User
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectList,
    ProjectMembershipCreate,
    ProjectMembershipResponse,
    ProjectResponse,
)

router = APIRouter()

_SKELETON_501 = "Projects module skeleton — implementation delivered in Epic 11"

_RESPONSES = {
    404: {"description": "Feature flag ENABLE_PROJECT_MODEL disabled"},
    501: {"description": "Projects module skeleton — Epic 11 not yet delivered"},
}


@router.post(
    "",
    status_code=201,
    responses=_RESPONSES,  # AC3 : documentation OpenAPI 404 + 501
)
async def create_project_endpoint(  # AC3
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_project_model_enabled),
) -> ProjectResponse:
    """Creer un projet (stub Epic 11 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.get(
    "/{project_id}",
    responses=_RESPONSES,
)
async def get_project_endpoint(  # AC3
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_project_model_enabled),
) -> ProjectResponse:
    """Detail d'un projet (stub Epic 11 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.get(
    "",
    responses=_RESPONSES,
)
async def list_projects_endpoint(  # AC3
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_project_model_enabled),
) -> ProjectList:
    """Liste paginee des projets de l'owner (stub Epic 11 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.post(
    "/{project_id}/memberships",
    status_code=201,
    responses=_RESPONSES,
)
async def add_project_membership_endpoint(  # AC3
    project_id: uuid.UUID,
    body: ProjectMembershipCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_project_model_enabled),
) -> ProjectMembershipResponse:
    """Ajouter un membership a un projet (stub Epic 11 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)
