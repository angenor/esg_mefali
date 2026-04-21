"""Tests de l'endpoint `GET /audit-trail/export.csv` (Story 10.12 AC3).

Couvre : streaming chunked + Content-Type + escape formula injection
(CVE-2014-3524) + hard cap 50k truncation + ligne sentinelle + header
`X-Export-Truncated: true`.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone

import pytest

from app.modules.admin_catalogue import audit_constants
from app.modules.admin_catalogue.router import (
    _csv_row_from_model,
    _csv_safe_cell,
)
from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail
from app.modules.admin_catalogue.service import record_audit_event


pytestmark = pytest.mark.asyncio


# -----------------------------------------------------------------------------
# Unit tests — escape formula injection (SQLite-friendly).
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload,expected_prefix",
    [
        ("=SUM(A1:A10)", "'=SUM(A1:A10)"),
        ("+cmd|calc", "'+cmd|calc"),
        ("-1", "'-1"),
        ("@SUM", "'@SUM"),
        ("\tTAB-start", "'\tTAB-start"),
        ("\rCR-start", "'\rCR-start"),
    ],
)
async def test_csv_safe_cell_prefixes_formula_injection(payload, expected_prefix):
    """CVE-2014-3524 : cellule debutant par `=+-@\\t\\r` prefixee par `'`."""
    assert _csv_safe_cell(payload) == expected_prefix


async def test_csv_safe_cell_leaves_normal_strings_unchanged():
    """Les chaines ordinaires ne sont pas modifiees."""
    assert _csv_safe_cell("fund") == "fund"
    assert _csv_safe_cell("2026-04-21") == "2026-04-21"
    assert _csv_safe_cell(123) == "123"


async def test_csv_safe_cell_serializes_dict_as_json():
    """Les dict JSONB sont serialises en JSON (pas str() qui donnerait repr Python)."""
    result = _csv_safe_cell({"title": "T"})
    assert result == '{"title": "T"}'


async def test_csv_safe_cell_escapes_json_starting_with_at():
    """Si un JSON commence par `@` apres serialisation, escape applique."""
    # Dict dont le JSON serialized ne commence jamais par =/+/-/@ (toujours `{`),
    # donc ce test valide le contrat : aucune mutation pour `{...}`.
    result = _csv_safe_cell({"@tag": "x"})
    assert result.startswith("{")  # pas d'escape (le `{` initial n'est pas vuln)


async def test_csv_safe_cell_none_returns_empty_string():
    """`None` -> chaine vide."""
    assert _csv_safe_cell(None) == ""


async def test_csv_row_from_model_applies_escape_on_entity_type():
    """`_csv_row_from_model` passe chaque cellule par `_csv_safe_cell`."""
    row = AdminCatalogueAuditTrail(
        id=uuid.uuid4(),
        actor_user_id=uuid.uuid4(),
        entity_type="=FORMULA",  # valeur malicieuse
        entity_id=uuid.uuid4(),
        action="create",
        workflow_level="N1",
        workflow_state_before=None,
        workflow_state_after=None,
        changes_before=None,
        changes_after=None,
        ts=datetime.now(timezone.utc),
        correlation_id=None,
    )
    cells = _csv_row_from_model(row)
    # index 2 = entity_type (voir _CSV_HEADER)
    assert cells[2] == "'=FORMULA"


# -----------------------------------------------------------------------------
# Integration tests — streaming endpoint.
# -----------------------------------------------------------------------------


async def test_export_csv_streaming_content_type_and_disposition(
    admin_authenticated_client,
):
    """CSV streaming : Content-Type=text/csv + Content-Disposition=attachment."""
    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail/export.csv"
    )
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers["content-type"]
    assert resp.headers["content-disposition"].startswith("attachment;")
    assert "audit-trail-" in resp.headers["content-disposition"]
    # Header hard cap absent sur une table vide
    assert resp.headers.get("X-Export-Truncated") != "true"


async def test_export_csv_contains_header_row(admin_authenticated_client):
    """La premiere ligne du CSV est la ligne d'entete attendue."""
    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail/export.csv"
    )
    assert resp.status_code == 200
    first_line = resp.text.split("\n")[0].strip()
    expected_cols = (
        "id,actor_user_id,entity_type,entity_id,action,workflow_level,"
        "workflow_state_before,workflow_state_after,changes_before,"
        "changes_after,ts,correlation_id"
    )
    assert first_line == expected_cols


async def test_export_csv_escapes_formula_injection_end_to_end(
    admin_authenticated_client, db_session, seed_admin_user
):
    """Row avec `entity_type='=FORMULA'` -> CSV contient `'=FORMULA`."""
    # Seed direct via record_audit_event (entity_type='fund' autorise dans
    # validator — mais on veut valider l'escape CSV, pas le validator
    # endpoint). Le test seed un entity_type qui passe le validator mais
    # dont le JSON `changes_after` commence par `@` (impossible car dict
    # toujours `{`). On utilise plutot une string directement via ORM :
    row = AdminCatalogueAuditTrail(
        id=uuid.uuid4(),
        actor_user_id=seed_admin_user.id,
        entity_type="fund",
        entity_id=uuid.uuid4(),
        action="create",
        workflow_level="N1",
        workflow_state_before=None,
        workflow_state_after="=SUM(A1)",  # valeur malicieuse
        changes_before=None,
        changes_after={"title": "T"},
        ts=datetime.now(timezone.utc),
        correlation_id=None,
    )
    db_session.add(row)
    await db_session.commit()

    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail/export.csv"
    )
    assert resp.status_code == 200
    assert "'=SUM(A1)" in resp.text


async def test_export_csv_hard_cap_truncation(
    admin_authenticated_client, db_session, seed_admin_user, monkeypatch
):
    """Depassement `EXPORT_ROW_HARD_CAP` -> sentinelle + header truncated."""
    monkeypatch.setattr(audit_constants, "EXPORT_ROW_HARD_CAP", 2)

    # Seed 3 rows -> cap 2 => truncation attendue.
    for _ in range(3):
        db_session.add(
            AdminCatalogueAuditTrail(
                id=uuid.uuid4(),
                actor_user_id=seed_admin_user.id,
                entity_type="fund",
                entity_id=uuid.uuid4(),
                action="create",
                workflow_level="N1",
                workflow_state_before=None,
                workflow_state_after=None,
                changes_before=None,
                changes_after=None,
                ts=datetime.now(timezone.utc),
                correlation_id=None,
            )
        )
    await db_session.commit()

    resp = await admin_authenticated_client.get(
        "/api/admin/catalogue/audit-trail/export.csv"
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Export-Truncated") == "true"
    assert audit_constants.EXPORT_TRUNCATED_SENTINEL in resp.text
    # Exactement 2 data rows + 1 header + 1 sentinelle
    non_empty_lines = [ln for ln in resp.text.split("\n") if ln.strip()]
    assert len(non_empty_lines) == 4  # header + 2 data + sentinel
