"""Tests de l'endpoint `GET /api/admin/catalogue/audit-trail` (Story 10.12 AC1+AC4).

3 tests unit (401/403/422 + rate limit) + 2 tests `@pytest.mark.postgres`
pour la pagination keyset + filtres combines (round-trip PG reel).
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock

import pytest

_SKIP_IF_NOT_POSTGRES = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"),
    reason="Requires PostgreSQL (keyset pagination micro-precision)",
)
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.modules.admin_catalogue import audit_constants
from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail
from app.modules.admin_catalogue.router import _decode_cursor, _encode_cursor
from app.modules.admin_catalogue.service import record_audit_event

from tests.test_admin_catalogue.conftest import ADMIN_EMAIL


pytestmark = pytest.mark.asyncio


# -----------------------------------------------------------------------------
# 3 tests unit (SQLite-friendly).
# -----------------------------------------------------------------------------


async def test_audit_trail_endpoint_401_no_jwt():
    """Sans JWT -> 401 (get_current_user prime sur require_admin_mefali)."""
    from app.main import app

    # Pas d'override auth -> get_current_user leve 401
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/admin/catalogue/audit-trail")
    assert resp.status_code == 401


async def test_audit_trail_endpoint_403_non_admin_email(
    authenticated_client, monkeypatch
):
    """JWT valide + email NON-whiteliste -> 403."""
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "other-admin@mefali.test")
    resp = await authenticated_client.get("/api/admin/catalogue/audit-trail")
    assert resp.status_code == 403


async def test_audit_trail_endpoint_422_invalid_action_filter(
    admin_authenticated_client,
):
    """Filtre `?action=hacked` hors registre -> 422 (registre, pas signature)."""
    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail?action=hacked"
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    # Confirmer que c'est bien notre validator registry qui a leve, pas un
    # manquement de signature FastAPI (ex. Request param).
    assert "hors registre" in str(body["detail"])


async def test_audit_trail_endpoint_422_invalid_entity_type_filter(
    admin_authenticated_client,
):
    """Filtre `?entity_type=unknown` hors registre -> 422."""
    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail?entity_type=unknown"
    )
    assert resp.status_code == 422


async def test_audit_trail_endpoint_400_malformed_cursor(
    admin_authenticated_client,
):
    """Cursor base64 corrompu -> 400 (pas 422 : c'est une erreur de pagination)."""
    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail?cursor=not%20valid%20base64"
    )
    assert resp.status_code == 400


async def test_cursor_encode_decode_roundtrip():
    """`_encode_cursor` + `_decode_cursor` round-trip stable."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    row_id = uuid.uuid4()
    cursor = _encode_cursor(now, row_id)
    decoded_ts, decoded_id = _decode_cursor(cursor)
    assert decoded_ts == now
    assert decoded_id == row_id


# -----------------------------------------------------------------------------
# 3 tests keyset pagination (SQLite-compatible — tuple_ < supporte).
# -----------------------------------------------------------------------------


@pytest.fixture
async def seeded_audit_rows(db_session, seed_admin_user):
    """Insere 3 rows audit pour les tests de pagination keyset."""
    rows = []
    for idx in range(3):
        row = await record_audit_event(
            db_session,
            actor_user_id=seed_admin_user.id,
            entity_type="fund",
            entity_id=uuid.uuid4(),
            action="create",  # type: ignore[arg-type]
            workflow_level="N1",  # type: ignore[arg-type]
            workflow_state_before=None,
            workflow_state_after="draft",
            changes_before=None,
            changes_after={"seq": idx},
            correlation_id=None,
        )
        rows.append(row)
    await db_session.commit()
    yield rows
    # Cleanup — delete direct autorise (SQLite test, pas de trigger 42501)
    for row in rows:
        await db_session.execute(
            delete(AdminCatalogueAuditTrail).where(
                AdminCatalogueAuditTrail.id == row.id
            )
        )
    await db_session.commit()


@pytest.mark.postgres
@_SKIP_IF_NOT_POSTGRES
async def test_audit_trail_keyset_pagination_page_size_2(
    admin_authenticated_client, seeded_audit_rows
):
    """page_size=2 -> page 1 retourne 2 items + next_cursor, page 2 retourne 1 + None.

    Marker `@pytest.mark.postgres` (skip sur SQLite) — SQLite resout `func.now()`
    a la seconde (pas au micro), donc les 3 rows seedees partagent le meme
    `ts` et la comparaison `tuple_(ts, id) < (cursor_ts, cursor_id)` ne
    filtre pas fiablement sans microseconde. PG garantit micro-precision.
    """
    resp1 = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail?page_size=2&entity_type=fund"
    )
    assert resp1.status_code == 200, resp1.text
    body1 = resp1.json()
    assert body1["page_size"] == 2
    assert len(body1["items"]) == 2
    assert body1["next_cursor"] is not None

    resp2 = await admin_authenticated_client.get(
        f"/api/admin/catalogue/audit-trail?page_size=2&entity_type=fund&cursor={body1['next_cursor']}"
    )
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert len(body2["items"]) >= 1

    page1_ids = {item["id"] for item in body1["items"]}
    page2_ids = {item["id"] for item in body2["items"]}
    all_seed_ids = {str(row.id) for row in seeded_audit_rows}
    # Union totale = tous les seeds.
    assert (page1_ids | page2_ids) == all_seed_ids, (
        f"page1={page1_ids} page2={page2_ids} seeds={all_seed_ids}"
    )
    # Disjonction stricte : aucun doublon cross-page (protege contre bug
    # cursor `<=` au lieu de `<` strict qui renverrait la row de bordure).
    assert page1_ids.isdisjoint(page2_ids), (
        f"Doublons cross-page detectes : {page1_ids & page2_ids}"
    )


async def test_audit_trail_filter_by_entity_id(
    admin_authenticated_client, seeded_audit_rows
):
    """Filtre `?entity_id=<uuid>` retourne exactement la row correspondante."""
    target = seeded_audit_rows[1]
    resp = await admin_authenticated_client.get(
        f"/api/admin/catalogue/audit-trail?entity_id={target.entity_id}"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(target.id)
    assert body["items"][0]["entity_id"] == str(target.entity_id)


async def test_audit_trail_rate_limit_429_enforced(monkeypatch):
    """Rate limit : la N+1ᵉ requete retourne 429 avec header Retry-After.

    HIGH-10.12-1 fix : le router expose `_resolve_rate_limit_audit_trail`
    (callable passe a `@limiter.limit`), reevalue a chaque requete. Un
    `monkeypatch.setattr(audit_constants, 'RATE_LIMIT_AUDIT_TRAIL', ...)`
    est desormais effectif sans redemarrer l'app.

    Prouve AC4 « la 61ᵉ retourne 429 » de maniere fonctionnelle.

    N'utilise PAS la fixture `admin_authenticated_client` car elle
    desactive le limiter (override sans `Request` ne peuple pas
    `request.state.user`). On override ici avec une fonction qui peuple
    explicitement `request.state.user` — prerequis SlowAPI FR-013.
    """
    from app.api.deps import get_current_user
    from app.core.rate_limit import limiter
    from app.main import app

    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", ADMIN_EMAIL)
    monkeypatch.setattr(audit_constants, "RATE_LIMIT_AUDIT_TRAIL", "2/minute")

    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = ADMIN_EMAIL
    mock_user.is_active = True

    async def _override_get_current_user(request: Request):
        request.state.user = mock_user
        return mock_user

    app.dependency_overrides[get_current_user] = _override_get_current_user

    # Reactivation + reset du store SlowAPI in-memory pour eviter la
    # pollution croisee (la fixture admin_authenticated_client a mis
    # enabled=False dans les tests precedents).
    limiter.enabled = True
    limiter.reset()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp1 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")
            resp2 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")
            resp3 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")

        assert resp1.status_code == 200, resp1.text
        assert resp2.status_code == 200, resp2.text
        assert resp3.status_code == 429, resp3.text
        # SlowAPI pose `Retry-After` quand headers_enabled=True
        assert "retry-after" in {k.lower() for k in resp3.headers.keys()}
    finally:
        del app.dependency_overrides[get_current_user]
        limiter.reset()


async def test_audit_trail_rate_limit_scopes_by_admin_user_id(monkeypatch):
    """User A quota atteint ne doit PAS affecter user B (clef = admin_user_id).

    Prouve AC4 « un 2ᵉ admin authentifie n'est pas affecte par les quotas
    du 1ᵉʳ » (pattern FR-013 clef admin_user_id pas IP).
    """
    from app.api.deps import get_current_user
    from app.core.rate_limit import limiter
    from app.main import app

    monkeypatch.setenv(
        "ADMIN_MEFALI_EMAILS", f"{ADMIN_EMAIL},admin2@mefali.test"
    )
    monkeypatch.setattr(audit_constants, "RATE_LIMIT_AUDIT_TRAIL", "1/minute")

    user_a = MagicMock()
    user_a.id = uuid.uuid4()
    user_a.email = ADMIN_EMAIL
    user_a.is_active = True

    user_b = MagicMock()
    user_b.id = uuid.uuid4()
    user_b.email = "admin2@mefali.test"
    user_b.is_active = True

    current_user = {"value": user_a}

    async def _override_get_current_user(request: Request):
        u = current_user["value"]
        request.state.user = u
        return u

    app.dependency_overrides[get_current_user] = _override_get_current_user

    limiter.enabled = True
    limiter.reset()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # User A consomme son unique slot
            resp_a1 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")
            # User A 2eme requete -> 429
            resp_a2 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")
            # Bascule vers user B : son compteur est independant
            current_user["value"] = user_b
            resp_b1 = await ac.get("/api/admin/catalogue/audit-trail?page_size=1")

        assert resp_a1.status_code == 200, resp_a1.text
        assert resp_a2.status_code == 429, resp_a2.text
        assert resp_b1.status_code == 200, resp_b1.text
    finally:
        del app.dependency_overrides[get_current_user]
        limiter.reset()


async def test_audit_trail_rate_limit_is_sane_60_per_minute():
    """Smoke : verifie la valeur canonique enregistree (par defaut)."""
    assert audit_constants.RATE_LIMIT_AUDIT_TRAIL == "60/minute"
    assert audit_constants.RATE_LIMIT_AUDIT_EXPORT == "10/hour"
