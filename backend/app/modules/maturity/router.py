"""Router REST pour le module maturity (endpoints stubs 401 -> 501).

Story 10.3 - module `maturity/` squelette.
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Comportement (AC3) — ordre des statuts : 401 -> 501 :
- Sans JWT valide -> 401 (Depends(get_current_user) prime).
- Avec JWT -> 501 (squelette, Epic 12 livrera la logique metier complete).

**Contrairement a modules/projects/, PAS de feature flag `ENABLE_MATURITY_MODEL`** :
les endpoints renvoient directement 501 (pas de 404 intermediaire). Arbitrage
Q1 Story 10.1 : seul `ENABLE_PROJECT_MODEL` introduit (parsimonie env var).

# TODO Epic 12 S1 : ajouter 'maturity' dans _MODULE_ROUTE_FLAGS et
# module_labels du router_node quand maturity_node devient routable
# (actuellement pattern squelette sans routing heuristique — cf. AC5
# Story 10.3 + lecon MEDIUM-10.2-2 Code Review 2026-04-20).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.user import User
from app.modules.maturity.schemas import (
    FormalizationPlanResponse,
    MaturityLevelDeclaration,
    MaturityLevelResponse,
)

router = APIRouter()

_SKELETON_501 = (
    "Maturity module skeleton — implementation delivered in Epic 12"
)

_RESPONSES = {
    501: {
        "description": "Maturity module skeleton — Epic 12 not yet delivered"
    },
}


@router.post(
    "/declare",
    status_code=201,
    responses=_RESPONSES,  # AC3 : documentation OpenAPI 501
)
async def declare_maturity_level_endpoint(  # AC3 — Epic 12.1
    body: MaturityLevelDeclaration,
    current_user: User = Depends(get_current_user),
) -> FormalizationPlanResponse:
    """Self-declaration de niveau de maturite (stub Epic 12.1 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.get(
    "/formalization-plan",
    responses=_RESPONSES,
)
async def get_formalization_plan_endpoint(  # AC3 — Epic 12.3
    current_user: User = Depends(get_current_user),
) -> FormalizationPlanResponse:
    """Recuperation du plan de formalisation de l'entreprise courante (stub Epic 12.3 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.get(
    "/levels",
    responses=_RESPONSES,
)
async def list_published_levels_endpoint(  # AC3
    current_user: User = Depends(get_current_user),
) -> list[MaturityLevelResponse]:
    """Catalogue pagine des AdminMaturityLevel publies (stub Epic 12 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)
