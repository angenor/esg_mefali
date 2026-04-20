"""AC5 — RLS activé sur les 4 tables sensibles + tenant isolation réelle.

Tests PostgreSQL-only (skip SQLite). Vérifient :
- pg_class.relrowsecurity = true sur companies, fund_applications, facts, documents
- Policy tenant_isolation existe
- Un SELECT avec un autre user_id retourne 0 ligne (via set_config)
- Un bypass admin (set_config app.user_role = 'admin_mefali') voit tout
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import text


pytestmark = pytest.mark.postgres


RLS_TABLES = ("companies", "fund_applications", "facts", "documents")


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


def _set_session_context(conn, user_id: str, role: str) -> None:
    """SET LOCAL via set_config() — support des bind params."""
    conn.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": user_id},
    )
    conn.execute(
        text("SELECT set_config('app.user_role', :r, true)"),
        {"r": role},
    )


def _ensure_app_user_role(conn) -> None:
    """Crée un rôle non-superuser `app_user` si absent (RLS n'affecte pas SUPERUSER)."""
    conn.execute(
        text(
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') "
            "THEN CREATE ROLE app_user NOINHERIT; END IF; END $$;"
        )
    )
    # USAGE sur le schéma + grants sur les tables RLS
    conn.execute(text("GRANT USAGE ON SCHEMA public TO app_user"))
    for t in RLS_TABLES:
        conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO app_user"))


def test_rls_enabled_on_all_sensitive_tables(sync_engine):
    """AC5 — relrowsecurity = true sur les 4 tables."""
    with sync_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relname = ANY(:tables)"
            ),
            {"tables": list(RLS_TABLES)},
        ).fetchall()
    by_name = {r[0]: r[1] for r in rows}
    for t in RLS_TABLES:
        assert by_name.get(t) is True, f"RLS non activé sur {t}"


def test_tenant_isolation_policy_exists(sync_engine):
    """AC5 — policy tenant_isolation créée sur les 4 tables."""
    with sync_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_policies "
                "WHERE policyname = 'tenant_isolation' "
                "AND tablename = ANY(:tables)"
            ),
            {"tables": list(RLS_TABLES)},
        ).fetchall()
    names = {r[0] for r in rows}
    assert names == set(RLS_TABLES), (
        f"policies manquantes : {set(RLS_TABLES) - names}"
    )


def test_tenant_isolation_blocks_other_user(sync_engine):
    """AC5 — SELECT d'une company d'un autre user retourne 0 ligne."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    company_b_id = uuid.uuid4()

    with sync_engine.begin() as conn:
        for u in (user_a, user_b):
            conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, full_name, "
                    "company_name, is_active) VALUES (:id, :em, 'h', 'U', 'C', true)"
                ),
                {"id": u, "em": f"u-{u.hex[:6]}@x.com"},
            )
        conn.execute(
            text(
                "INSERT INTO companies (id, owner_user_id, name) "
                "VALUES (:id, :u, 'Co B')"
            ),
            {"id": company_b_id, "u": user_b},
        )

    try:
        # Simule user_a (role normal non-superuser) essayant de lire la company de user_b
        with sync_engine.connect() as conn:
            with conn.begin():
                _ensure_app_user_role(conn)
                _set_session_context(conn, str(user_a), "user")
                conn.execute(text("SET LOCAL ROLE app_user"))
                row = conn.execute(
                    text("SELECT id FROM companies WHERE id = :id"),
                    {"id": company_b_id},
                ).fetchone()
                conn.execute(text("RESET ROLE"))
        assert row is None, "RLS n'a pas filtré la company d'un autre user"
    finally:
        # Nettoyage en admin_super pour contourner RLS
        with sync_engine.connect() as conn:
            with conn.begin():
                _set_session_context(conn, str(user_a), "admin_super")
                conn.execute(
                    text("DELETE FROM companies WHERE owner_user_id = ANY(:ids)"),
                    {"ids": [user_a, user_b]},
                )
            with conn.begin():
                conn.execute(
                    text("DELETE FROM users WHERE id = ANY(:ids)"),
                    {"ids": [user_a, user_b]},
                )


def test_admin_bypass_sees_all(sync_engine):
    """AC5 — admin_mefali/admin_super voit les données de tous les tenants."""
    user_x = uuid.uuid4()
    company_x = uuid.uuid4()

    try:
        with sync_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, full_name, "
                    "company_name, is_active) VALUES (:id, :em, 'h', 'U', 'C', true)"
                ),
                {"id": user_x, "em": f"u-{user_x.hex[:6]}@x.com"},
            )
            conn.execute(
                text(
                    "INSERT INTO companies (id, owner_user_id, name) "
                    "VALUES (:id, :u, 'Co X')"
                ),
                {"id": company_x, "u": user_x},
            )

        with sync_engine.connect() as conn:
            with conn.begin():
                _set_session_context(
                    conn, str(uuid.uuid4()), "admin_mefali"
                )
                row = conn.execute(
                    text("SELECT id FROM companies WHERE id = :id"),
                    {"id": company_x},
                ).fetchone()
        assert row is not None, "admin_mefali devrait voir toutes les companies"
    finally:
        with sync_engine.connect() as conn:
            with conn.begin():
                _set_session_context(conn, str(user_x), "admin_super")
                conn.execute(
                    text("DELETE FROM companies WHERE owner_user_id = :u"),
                    {"u": user_x},
                )
            with conn.begin():
                conn.execute(
                    text("DELETE FROM users WHERE id = :id"),
                    {"id": user_x},
                )
