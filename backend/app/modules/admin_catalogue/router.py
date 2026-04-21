"""Router REST pour le module admin_catalogue (endpoints stubs + audit trail 10.12).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
Story 10.12 — endpoints `GET /audit-trail` + `GET /audit-trail/export.csv`.

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

import base64
import csv
import hashlib
import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.modules.admin_catalogue import audit_constants
from app.modules.admin_catalogue.audit_constants import (
    ACTION_TYPES,
    ENTITY_TYPES,
    EXPORT_TRUNCATED_SENTINEL,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MAX,
    RATE_LIMIT_AUDIT_EXPORT,
    RATE_LIMIT_AUDIT_TRAIL,
)
from app.modules.admin_catalogue.dependencies import require_admin_mefali
from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail
from app.modules.admin_catalogue.schemas import (
    AdminCatalogueAuditTrailResponse,
    AuditTrailPage,
    CriterionCreate,
    CriterionDerivationRuleCreate,
    FactTypeListResponse,
    PackCreate,
    ReferentialCreate,
)
from app.modules.admin_catalogue.service import list_fact_types


router = APIRouter()
logger = logging.getLogger("app.modules.admin_catalogue.audit_trail")


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

_RESPONSES_AUDIT = {
    401: {"description": "JWT absent ou invalide"},
    403: {"description": "Acces reserve au role admin_mefali"},
    422: {"description": "Filtre action/entity_type hors registre"},
    429: {"description": "Rate limit depasse par admin_user_id"},
}


# ---------------------------------------------------------------------------
# Helpers keyset cursor (opaque base64url) — pagination Story 10.12 AC1.
# ---------------------------------------------------------------------------


def _encode_cursor(ts: datetime, row_id: uuid.UUID) -> str:
    """Encoder un keyset cursor (ts, id) en base64url opaque.

    Format interne `{ts_iso_utc}|{uuid_hex}` puis base64url. Les clients
    ne doivent pas parser cette valeur — elle peut changer de format sans
    preavis (opaque par contrat).
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    raw = f"{ts.isoformat()}|{row_id.hex}"
    return base64.urlsafe_b64encode(raw.encode("ascii")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decoder un keyset cursor base64url. Leve `ValueError` si malforme.

    Le caller (handler) convertit `ValueError` en HTTP 400 pour eviter de
    confondre avec 422 (validation du body/query avant decode).
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("ascii")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("cursor base64 malforme") from exc

    if "|" not in decoded:
        raise ValueError("cursor format invalide (separator manquant)")

    ts_part, id_part = decoded.split("|", 1)
    try:
        ts = datetime.fromisoformat(ts_part)
    except ValueError as exc:
        raise ValueError(f"cursor ts invalide: {ts_part}") from exc
    try:
        row_id = uuid.UUID(id_part)
    except ValueError as exc:
        raise ValueError(f"cursor id invalide: {id_part}") from exc
    return ts, row_id


# ---------------------------------------------------------------------------
# Helpers CSV (Story 10.12 AC3) — escape formula injection + streaming.
# ---------------------------------------------------------------------------

_FORMULA_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe_cell(value: Any) -> str:
    """Escape anti-CVE-2014-3524 — prefixe `'` si cellule commence par
    `=`/`+`/`-`/`@`/`\\t`/`\\r`. Appliquee avant ecriture csv.writer.

    `None` -> chaine vide. Les dict (JSONB) sont serialises JSON via
    `json.dumps(ensure_ascii=False)` avant escape.
    """
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    if text.startswith(_FORMULA_INJECTION_PREFIXES):
        return "'" + text
    return text


_CSV_HEADER: tuple[str, ...] = (
    "id",
    "actor_user_id",
    "entity_type",
    "entity_id",
    "action",
    "workflow_level",
    "workflow_state_before",
    "workflow_state_after",
    "changes_before",
    "changes_after",
    "ts",
    "correlation_id",
)


def _csv_row_from_model(row: AdminCatalogueAuditTrail) -> list[str]:
    """Serialiser une ligne AdminCatalogueAuditTrail en cellules escapees."""
    return [
        _csv_safe_cell(row.id),
        _csv_safe_cell(row.actor_user_id),
        _csv_safe_cell(row.entity_type),
        _csv_safe_cell(row.entity_id),
        _csv_safe_cell(row.action),
        _csv_safe_cell(row.workflow_level),
        _csv_safe_cell(row.workflow_state_before),
        _csv_safe_cell(row.workflow_state_after),
        _csv_safe_cell(row.changes_before),
        _csv_safe_cell(row.changes_after),
        _csv_safe_cell(row.ts.isoformat() if row.ts else None),
        _csv_safe_cell(row.correlation_id),
    ]


# ---------------------------------------------------------------------------
# Filtres communs endpoint + export.
# ---------------------------------------------------------------------------


def _build_filter_clauses(
    *,
    actor_user_id: uuid.UUID | None,
    action: str | None,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    ts_from: datetime | None,
    ts_to: datetime | None,
) -> list:
    """Construire la liste de conditions SQLAlchemy pour les filtres de query.

    Chaque valeur None est ignoree. Les `action`/`entity_type` doivent
    avoir ete valides contre `ACTION_TYPES`/`ENTITY_TYPES` par le caller.
    """
    clauses = []
    if actor_user_id is not None:
        clauses.append(AdminCatalogueAuditTrail.actor_user_id == actor_user_id)
    if action is not None:
        clauses.append(AdminCatalogueAuditTrail.action == action)
    if entity_type is not None:
        clauses.append(AdminCatalogueAuditTrail.entity_type == entity_type)
    if entity_id is not None:
        clauses.append(AdminCatalogueAuditTrail.entity_id == entity_id)
    if ts_from is not None:
        clauses.append(AdminCatalogueAuditTrail.ts >= ts_from)
    if ts_to is not None:
        clauses.append(AdminCatalogueAuditTrail.ts <= ts_to)
    return clauses


def _validate_action_filter(action: str | None) -> None:
    """422 si `action` hors `ACTION_TYPES`."""
    if action is not None and action not in ACTION_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Filtre `action={action!r}` hors registre. "
                f"Valeurs autorisees : {list(ACTION_TYPES)}."
            ),
        )


def _validate_entity_type_filter(entity_type: str | None) -> None:
    """422 si `entity_type` hors `ENTITY_TYPES`."""
    if entity_type is not None and entity_type not in ENTITY_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Filtre `entity_type={entity_type!r}` hors registre. "
                f"Valeurs autorisees : {list(ENTITY_TYPES)}."
            ),
        )


# ---------------------------------------------------------------------------
# Endpoints existants (Story 10.4).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Endpoints audit trail (Story 10.12).
# ---------------------------------------------------------------------------


@router.get(
    "/audit-trail",
    response_model=AuditTrailPage,
    responses=_RESPONSES_AUDIT,
)
@limiter.limit(RATE_LIMIT_AUDIT_TRAIL)
async def list_audit_trail(
    request: Request,
    cursor: str | None = Query(default=None),
    page_size: int = Query(default=PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX),
    actor_user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    ts_from: datetime | None = Query(default=None),
    ts_to: datetime | None = Query(default=None),
    admin: User = Depends(require_admin_mefali),
    db: AsyncSession = Depends(get_db),
) -> AuditTrailPage:
    """Lister les evenements audit trail catalogue (AC1).

    Pagination keyset `(ts DESC, id DESC)` — stable sous concurrent inserts
    et scalable O(log N) contrairement a offset-based. Rate limit 60/min
    par `admin_user_id` (pas IP, pattern FR-013 9.1).
    """
    _validate_action_filter(action)
    _validate_entity_type_filter(entity_type)

    clauses = _build_filter_clauses(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ts_from=ts_from,
        ts_to=ts_to,
    )

    if cursor is not None:
        try:
            cursor_ts, cursor_id = _decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"cursor invalide: {exc}"
            )
        clauses.append(
            tuple_(
                AdminCatalogueAuditTrail.ts,
                AdminCatalogueAuditTrail.id,
            )
            < (cursor_ts, cursor_id)
        )

    stmt = (
        select(AdminCatalogueAuditTrail)
        .where(and_(*clauses) if clauses else True)
        .order_by(
            desc(AdminCatalogueAuditTrail.ts),
            desc(AdminCatalogueAuditTrail.id),
        )
        .limit(page_size + 1)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if len(rows) > page_size:
        page_items = rows[:page_size]
        last = page_items[-1]
        next_cursor = _encode_cursor(last.ts, last.id)
    else:
        page_items = rows
        next_cursor = None

    return AuditTrailPage(
        items=[
            AdminCatalogueAuditTrailResponse.model_validate(row)
            for row in page_items
        ],
        next_cursor=next_cursor,
        page_size=page_size,
    )


@router.get(
    "/audit-trail/export.csv",
    responses={
        **_RESPONSES_AUDIT,
        200: {
            "content": {"text/csv": {}},
            "description": (
                "Streaming CSV (Transfer-Encoding: chunked). Header "
                "`X-Export-Truncated: true` si hard cap atteint."
            ),
        },
    },
)
@limiter.limit(RATE_LIMIT_AUDIT_EXPORT)
async def export_audit_trail_csv(
    request: Request,
    actor_user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    ts_from: datetime | None = Query(None),
    ts_to: datetime | None = Query(None),
    admin: User = Depends(require_admin_mefali),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporter l'audit trail filtre au format CSV streaming (AC3).

    Streaming `yield_per=500` + hard cap `EXPORT_ROW_HARD_CAP` + escape
    anti-formula injection + meta-audit log `audit_export_issued`.
    """
    _validate_action_filter(action)
    _validate_entity_type_filter(entity_type)

    clauses = _build_filter_clauses(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ts_from=ts_from,
        ts_to=ts_to,
    )

    filters_payload = {
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "ts_from": ts_from.isoformat() if ts_from else None,
        "ts_to": ts_to.isoformat() if ts_to else None,
    }
    filters_hash = hashlib.sha256(
        json.dumps(filters_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]

    # Snapshot pour fermeture lexicale (lu via audit_constants.EXPORT_ROW_HARD_CAP
    # pour permettre monkeypatch en tests).
    stmt = (
        select(AdminCatalogueAuditTrail)
        .where(and_(*clauses) if clauses else True)
        .order_by(
            desc(AdminCatalogueAuditTrail.ts),
            desc(AdminCatalogueAuditTrail.id),
        )
        .execution_options(yield_per=500)
    )

    truncated_flag = {"value": False, "count": 0}

    async def _stream_rows():
        # En-tete
        buf = io.StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(_CSV_HEADER)
        yield buf.getvalue()

        hard_cap = audit_constants.EXPORT_ROW_HARD_CAP
        count = 0
        result = await db.stream(stmt)
        async for row in result.scalars():
            if count >= hard_cap:
                truncated_flag["value"] = True
                sentinel_buf = io.StringIO()
                sentinel_buf.write(EXPORT_TRUNCATED_SENTINEL + "\n")
                yield sentinel_buf.getvalue()
                break
            line_buf = io.StringIO()
            csv.writer(line_buf, quoting=csv.QUOTE_MINIMAL).writerow(
                _csv_row_from_model(row)
            )
            count += 1
            yield line_buf.getvalue()

        truncated_flag["count"] = count
        logger.info(
            "audit_export_issued",
            extra={
                "actor_user_id": str(admin.id),
                "filters_hash": filters_hash,
                "row_count": count,
                "truncated": truncated_flag["value"],
            },
        )

    # Headers (Transfer-Encoding chunked automatique sur StreamingResponse)
    filename = f"audit-trail-{datetime.now(timezone.utc).date().isoformat()}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    # `X-Export-Truncated` est pose apres streaming ; on le precalcule en
    # emettant une pre-query count-plus-1 seulement si necessaire. Pour le
    # MVP, on pose toujours le header base sur le comptage final via un
    # generator wrapper qui met a jour post-streaming : FastAPI/Starlette
    # ne permet pas de muter les headers apres envoi du premier chunk, on
    # pose donc le header a partir d'une pre-verification "existe-t-il >
    # hard_cap rows".
    # Pre-verification : COUNT(*) > hard_cap
    count_stmt = (
        select(AdminCatalogueAuditTrail.id)
        .where(and_(*clauses) if clauses else True)
        .limit(audit_constants.EXPORT_ROW_HARD_CAP + 1)
    )
    count_result = await db.execute(count_stmt)
    ids_sample = count_result.scalars().all()
    if len(ids_sample) > audit_constants.EXPORT_ROW_HARD_CAP:
        headers["X-Export-Truncated"] = "true"

    return StreamingResponse(
        _stream_rows(),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )
