"""Router REST pour le module admin_catalogue (endpoints stubs 401 -> 403 -> 501).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].

Comportement (AC3) — ordre des statuts : 401 -> 403 -> 501 :
- Sans JWT valide -> 401 (get_current_user prime).
- JWT valide + email non-whiteliste -> 403 (require_admin_mefali).
- Admin authentifie -> 200 pour GET /fact-types, 501 pour les 4 POST stubs.

**Contrairement a modules/projects/ et modules/maturity/**, la dependance
principale n'est PAS `Depends(get_current_user)` mais
`Depends(require_admin_mefali)` — le module admin_catalogue est UI-only et
reserve aux admins Mefali (FR61 livre Epic 18).

**Endpoints de workflow N2/N3** (`POST /criteria/{id}/request-review`,
`POST /criteria/{id}/approve`, `POST /criteria/{id}/publish`) **deferes** a
Epic 13 Story 13.8b/c — pas exposes dans Story 10.4.

**AUCUN feature flag** `ENABLE_ADMIN_CATALOGUE_MODEL` (parsimonie env var,
arbitrage Q1 Story 10.1).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.modules.admin_catalogue.dependencies import require_admin_mefali
from app.modules.admin_catalogue.schemas import (
    CriterionCreate,
    CriterionDerivationRuleCreate,
    FactTypeListResponse,
    PackCreate,
    ReferentialCreate,
)
from app.modules.admin_catalogue.service import list_fact_types

router = APIRouter()

_SKELETON_501 = (
    "Admin Catalogue skeleton — implementation delivered in Epic 13"
)

_RESPONSES_STUB = {
    501: {
        "description": (
            "Admin Catalogue skeleton — Epic 13 not yet delivered"
        )
    },
    403: {"description": "Acces reserve au role admin_mefali"},
}

_RESPONSES_GET = {
    403: {"description": "Acces reserve au role admin_mefali"},
}


@router.get(
    "/fact-types",
    response_model=FactTypeListResponse,
    responses=_RESPONSES_GET,
)
async def list_fact_types_endpoint(  # AC3 + AC7 — endpoint effectif 200
    admin: User = Depends(require_admin_mefali),
) -> FactTypeListResponse:
    """Lister les fact_type autorises (FR17 — seul endpoint effectif MVP)."""
    fact_types = await list_fact_types()
    return FactTypeListResponse(fact_types=fact_types)


@router.post(
    "/criteria",
    status_code=201,
    responses=_RESPONSES_STUB,
)
async def create_criterion_endpoint(  # AC3 — Epic 13.1
    body: CriterionCreate,
    admin: User = Depends(require_admin_mefali),
) -> dict:
    """Creer un Criterion draft (stub Epic 13.1 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.post(
    "/referentials",
    status_code=201,
    responses=_RESPONSES_STUB,
)
async def create_referential_endpoint(  # AC3 — Epic 13.2
    body: ReferentialCreate,
    admin: User = Depends(require_admin_mefali),
) -> dict:
    """Creer un Referential draft (stub Epic 13.2 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.post(
    "/packs",
    status_code=201,
    responses=_RESPONSES_STUB,
)
async def create_pack_endpoint(  # AC3 — Epic 13.3
    body: PackCreate,
    admin: User = Depends(require_admin_mefali),
) -> dict:
    """Creer un Pack draft (stub Epic 13.3 - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)


@router.post(
    "/rules",
    status_code=201,
    responses=_RESPONSES_STUB,
)
async def create_rule_endpoint(  # AC3 — Epic 13.1bis
    body: CriterionDerivationRuleCreate,
    admin: User = Depends(require_admin_mefali),
) -> dict:
    """Creer une regle de derivation (stub Epic 13.1bis - 501)."""
    raise HTTPException(status_code=501, detail=_SKELETON_501)
