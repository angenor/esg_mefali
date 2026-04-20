"""AC5 — table admin_access_audit : structure + insert/select basique.

L'event listener SQLAlchemy qui écrit effectivement dans cette table est
livré Story 10.5. Ici on vérifie uniquement la création de schéma et la
capacité à insérer/sélectionner.
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import inspect, text


pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


def test_admin_access_audit_columns(sync_engine):
    """AC5 — colonnes D7 exactes."""
    insp = inspect(sync_engine)
    cols = {c["name"] for c in insp.get_columns("admin_access_audit")}
    required = {
        "id", "admin_user_id", "admin_role", "table_accessed",
        "operation", "record_ids", "request_id", "query_excerpt",
        "accessed_at", "reason",
    }
    missing = required - cols
    assert not missing, f"colonnes manquantes : {missing}"


def test_admin_access_audit_insert_select(sync_engine):
    """AC5 — insert + select basique fonctionne."""
    user_id = uuid.uuid4()
    log_id = uuid.uuid4()
    try:
        with sync_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, full_name, "
                    "company_name, is_active) VALUES (:id, :em, 'h', 'U', 'C', true)"
                ),
                {"id": user_id, "em": f"u-{user_id.hex[:6]}@x.com"},
            )
            conn.execute(
                text(
                    "INSERT INTO admin_access_audit "
                    "(id, admin_user_id, admin_role, table_accessed, operation) "
                    "VALUES (:id, :u, 'admin_mefali', 'companies', 'SELECT')"
                ),
                {"id": log_id, "u": user_id},
            )

        with sync_engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT admin_role, table_accessed, operation "
                    "FROM admin_access_audit WHERE id = :id"
                ),
                {"id": log_id},
            ).fetchone()
        assert row == ("admin_mefali", "companies", "SELECT")
    finally:
        with sync_engine.begin() as conn:
            conn.execute(text("DELETE FROM admin_access_audit WHERE admin_user_id = :u"), {"u": user_id})
            conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
