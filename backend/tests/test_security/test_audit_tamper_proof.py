"""AC6 — migration 028 rend ``admin_access_audit`` et
``admin_catalogue_audit_trail`` immutables au niveau SQL.

Scénarios par table (× 2 tables) :
1. INSERT : succès (audit writes doivent rester permis).
2. UPDATE : échec avec message contenant ``audit table is immutable``.
3. DELETE : échec avec message contenant ``audit table is immutable``.

PostgreSQL-only — marker ``@pytest.mark.postgres``. Résout HIGH-10.1-11.
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, InternalError


pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


def _seed_user(conn) -> uuid.UUID:
    user_id = uuid.uuid4()
    conn.execute(
        text(
            "INSERT INTO users (id, email, hashed_password, full_name, "
            "company_name, is_active) VALUES (:id, :em, 'h', 'U', 'C', true)"
        ),
        {"id": user_id, "em": f"u-{user_id.hex[:6]}@x.com"},
    )
    return user_id


def _seed_admin_access_audit(conn, admin_user_id: uuid.UUID) -> uuid.UUID:
    log_id = uuid.uuid4()
    conn.execute(
        text(
            "INSERT INTO admin_access_audit "
            "(id, admin_user_id, admin_role, table_accessed, operation) "
            "VALUES (:id, :u, 'admin_super', 'companies', 'UPDATE')"
        ),
        {"id": log_id, "u": admin_user_id},
    )
    return log_id


def _seed_catalogue_audit(conn, admin_user_id: uuid.UUID) -> uuid.UUID:
    """Crée une ligne admin_catalogue_audit_trail pour tester sa protection."""
    insp_row = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'admin_catalogue_audit_trail' "
            "ORDER BY ordinal_position"
        )
    ).fetchall()
    cols = [r[0] for r in insp_row]
    assert cols, "admin_catalogue_audit_trail devrait exister (migration 026)"

    # Valeurs minimales pour satisfaire NOT NULL contraintes.
    log_id = uuid.uuid4()
    values_sql = {
        "id": log_id,
        "admin_user_id": admin_user_id,
    }
    # Construire dynamiquement l'INSERT selon colonnes présentes
    # (schema défensif : la migration 026 peut évoluer).
    insert_fields = ["id", "admin_user_id"]
    insert_placeholders = [":id", ":admin_user_id"]
    if "action" in cols:
        insert_fields.append("action")
        insert_placeholders.append("'create'")
    if "entity_type" in cols:
        insert_fields.append("entity_type")
        insert_placeholders.append("'fund'")
    if "entity_id" in cols:
        insert_fields.append("entity_id")
        insert_placeholders.append(":entity_id")
        values_sql["entity_id"] = uuid.uuid4()
    if "changes" in cols:
        insert_fields.append("changes")
        insert_placeholders.append("CAST('{}' AS JSONB)")

    sql = (
        f"INSERT INTO admin_catalogue_audit_trail ({', '.join(insert_fields)}) "
        f"VALUES ({', '.join(insert_placeholders)})"
    )
    conn.execute(text(sql), values_sql)
    return log_id


def test_insert_admin_access_audit_succeeds(sync_engine):
    """AC6 — INSERT reste autorisé (trigger BEFORE UPDATE OR DELETE seulement)."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_admin_access_audit(conn, admin_id)
        row = conn.execute(
            text("SELECT id FROM admin_access_audit WHERE id = :id"),
            {"id": log_id},
        ).fetchone()
        assert row is not None


def test_update_admin_access_audit_raises_immutable(sync_engine):
    """AC6 — UPDATE → RAISE EXCEPTION 'audit table is immutable'."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_admin_access_audit(conn, admin_id)

    with pytest.raises((ProgrammingError, InternalError)) as exc_info:
        with sync_engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE admin_access_audit SET reason = 'tampered' "
                    "WHERE id = :id"
                ),
                {"id": log_id},
            )
    assert "audit table is immutable" in str(exc_info.value).lower()


def test_delete_admin_access_audit_raises_immutable(sync_engine):
    """AC6 — DELETE → RAISE EXCEPTION 'audit table is immutable'."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_admin_access_audit(conn, admin_id)

    with pytest.raises((ProgrammingError, InternalError)) as exc_info:
        with sync_engine.begin() as conn:
            conn.execute(
                text("DELETE FROM admin_access_audit WHERE id = :id"),
                {"id": log_id},
            )
    assert "audit table is immutable" in str(exc_info.value).lower()


def test_insert_catalogue_audit_trail_succeeds(sync_engine):
    """AC6 — INSERT catalogue trail reste autorisé."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_catalogue_audit(conn, admin_id)
        row = conn.execute(
            text(
                "SELECT id FROM admin_catalogue_audit_trail WHERE id = :id"
            ),
            {"id": log_id},
        ).fetchone()
        assert row is not None


def test_update_catalogue_audit_trail_raises_immutable(sync_engine):
    """AC6 — UPDATE catalogue trail → immutable."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_catalogue_audit(conn, admin_id)

    with pytest.raises((ProgrammingError, InternalError)) as exc_info:
        with sync_engine.begin() as conn:
            # Tente un UPDATE inoffensif (update same id).
            conn.execute(
                text(
                    "UPDATE admin_catalogue_audit_trail "
                    "SET admin_user_id = admin_user_id WHERE id = :id"
                ),
                {"id": log_id},
            )
    assert "audit table is immutable" in str(exc_info.value).lower()


def test_delete_catalogue_audit_trail_raises_immutable(sync_engine):
    """AC6 — DELETE catalogue trail → immutable."""
    with sync_engine.begin() as conn:
        admin_id = _seed_user(conn)
        log_id = _seed_catalogue_audit(conn, admin_id)

    with pytest.raises((ProgrammingError, InternalError)) as exc_info:
        with sync_engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM admin_catalogue_audit_trail WHERE id = :id"
                ),
                {"id": log_id},
            )
    assert "audit table is immutable" in str(exc_info.value).lower()
