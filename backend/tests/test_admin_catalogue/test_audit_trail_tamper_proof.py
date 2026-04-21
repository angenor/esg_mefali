"""Tests tamper-proof `admin_catalogue_audit_trail` E2E PostgreSQL (Story 10.12 AC5).

Verifient que le trigger PL/pgSQL `trg_admin_catalogue_audit_trail_immutable`
(migration 028) rejette UPDATE et DELETE avec ERRCODE 42501
(`insufficient_privilege`), independamment de tout bug applicatif (defense
en profondeur NFR12).

Tous ces tests requierent PostgreSQL — SQLite ne gere ni `REVOKE ... FROM
PUBLIC` ni les triggers PL/pgSQL (migration 028 skip sur SQLite lignes
38-41). Skip automatique via `@pytest.mark.postgres` + skipif si
`TEST_DATABASE_URL` ne pointe pas vers postgres.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail


pytestmark = [
    pytest.mark.postgres,
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"),
        reason="Requires PostgreSQL (triggers PL/pgSQL immutables)",
    ),
]


async def _seed_row(db_session, seed_admin_user) -> uuid.UUID:
    """Insert direct via ORM (INSERT reste autorise par migration 028)."""
    row = AdminCatalogueAuditTrail(
        id=uuid.uuid4(),
        actor_user_id=seed_admin_user.id,
        entity_type="fund",
        entity_id=uuid.uuid4(),
        action="create",
        workflow_level="N1",
        workflow_state_before=None,
        workflow_state_after="draft",
        changes_before=None,
        changes_after={"init": True},
        ts=datetime.now(timezone.utc),
        correlation_id=None,
    )
    db_session.add(row)
    await db_session.commit()
    return row.id


async def test_update_audit_row_raises_42501(db_session, seed_admin_user):
    """Un UPDATE direct sur `admin_catalogue_audit_trail` leve 42501."""
    row_id = await _seed_row(db_session, seed_admin_user)
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(
                "UPDATE admin_catalogue_audit_trail "
                "SET action = 'delete' WHERE id = :id"
            ),
            {"id": row_id},
        )
        await db_session.commit()
    # SQLSTATE 42501 = insufficient_privilege
    assert getattr(exc_info.value.orig, "sqlstate", None) == "42501"


async def test_delete_audit_row_raises_42501(db_session, seed_admin_user):
    """Un DELETE direct sur `admin_catalogue_audit_trail` leve 42501."""
    row_id = await _seed_row(db_session, seed_admin_user)
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(
                "DELETE FROM admin_catalogue_audit_trail WHERE id = :id"
            ),
            {"id": row_id},
        )
        await db_session.commit()
    assert getattr(exc_info.value.orig, "sqlstate", None) == "42501"


async def test_insert_via_orm_still_works(db_session, seed_admin_user):
    """Sanity check — INSERT via ORM reste autorise (trigger BEFORE UPDATE|DELETE)."""
    row_id = await _seed_row(db_session, seed_admin_user)
    result = await db_session.execute(
        text("SELECT id FROM admin_catalogue_audit_trail WHERE id = :id"),
        {"id": row_id},
    )
    assert result.scalar_one() == row_id


async def test_trigger_exists_in_pg_trigger(db_session):
    """Trigger `trg_admin_catalogue_audit_trail_immutable` present dans `pg_trigger`."""
    result = await db_session.execute(
        text(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgname = 'trg_admin_catalogue_audit_trail_immutable'"
        )
    )
    assert result.scalar_one_or_none() == "trg_admin_catalogue_audit_trail_immutable"
