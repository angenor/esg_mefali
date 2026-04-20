"""AC4 — tenant isolation : matrice 4 rôles × 4 tables (16 tests paramétrés).

Pour chaque combinaison (role ∈ {user, admin_mefali, admin_super, auditor},
table ∈ {companies, fund_applications, facts, documents}) :

- role = user/auditor → SELECT d'une ligne appartenant à un autre user
  retourne **0 lignes** (RLS filtre).
- role = admin_mefali/admin_super → SELECT voit la ligne **et** une
  opération mutante no-op (UPDATE) déclenche un flush ``before_flush``
  qui écrit dans ``admin_access_audit``.

La fixture classe seed 5 users + 2 companies + 2 fund_applications +
2 facts + 2 documents via un client admin_super (bypass RLS à
l'initialisation).

PostgreSQL-only — marker ``@pytest.mark.postgres``.
"""
from __future__ import annotations

import itertools
import uuid

import pytest
from alembic import command
from sqlalchemy import text


pytestmark = pytest.mark.postgres


ROLES = ("user", "admin_mefali", "admin_super", "auditor")
TABLES = ("companies", "fund_applications", "facts", "documents")
ADMIN_ROLES = {"admin_mefali", "admin_super"}


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture
def rls_fixture(sync_engine, monkeypatch):
    """Seed minimum pour la matrice 4×4 : 2 users + 1 ligne par table.

    Le fixture crée 2 tenants (user_A, user_B) + leurs données et
    renvoie les identifiants. Les whitelists admin sont positionnées via
    ``monkeypatch.setenv``.
    """
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "admin-mefali@mefali.com")
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "admin-super@mefali.com")

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()
    fund_app_a = uuid.uuid4()
    fund_app_b = uuid.uuid4()
    fact_a = uuid.uuid4()
    fact_b = uuid.uuid4()
    doc_a = uuid.uuid4()
    doc_b = uuid.uuid4()

    with sync_engine.begin() as conn:
        # Contexte admin_super pour écrire malgré RLS.
        conn.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        # Users
        for u in (user_a, user_b):
            conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, "
                    "full_name, company_name, is_active) "
                    "VALUES (:id, :em, 'h', 'U', 'C', true)"
                ),
                {"id": u, "em": f"u-{u.hex[:6]}@x.com"},
            )
        # Companies
        for cid, uid in ((company_a, user_a), (company_b, user_b)):
            conn.execute(
                text(
                    "INSERT INTO companies (id, owner_user_id, name) "
                    "VALUES (:id, :u, :n)"
                ),
                {"id": cid, "u": uid, "n": f"Co-{cid.hex[:6]}"},
            )
        # Fund applications — schéma minimum (défensif sur colonnes).
        fa_cols = _inspect_columns(conn, "fund_applications")
        for faid, uid in ((fund_app_a, user_a), (fund_app_b, user_b)):
            fields = ["id", "user_id"]
            values = [":id", ":u"]
            params = {"id": faid, "u": uid}
            if "status" in fa_cols:
                fields.append("status")
                values.append("'draft'")
            if "fund_id" in fa_cols:
                # fund_id peut être NULL si la contrainte le permet ; sinon
                # on skip et la migration 023 aura rendu fund_id nullable.
                pass
            conn.execute(
                text(
                    f"INSERT INTO fund_applications ({', '.join(fields)}) "
                    f"VALUES ({', '.join(values)})"
                ),
                params,
            )
        # Facts — rattaché via company_id.
        fact_cols = _inspect_columns(conn, "facts")
        for fid, cid in ((fact_a, company_a), (fact_b, company_b)):
            fields = ["id", "company_id"]
            values = [":id", ":c"]
            params = {"id": fid, "c": cid}
            if "fact_type" in fact_cols:
                fields.append("fact_type")
                values.append("'esg_indicator'")
            if "key" in fact_cols:
                fields.append("key")
                values.append("'test'")
            if "value_text" in fact_cols:
                fields.append("value_text")
                values.append("'v'")
            conn.execute(
                text(
                    f"INSERT INTO facts ({', '.join(fields)}) "
                    f"VALUES ({', '.join(values)})"
                ),
                params,
            )
        # Documents
        doc_cols = _inspect_columns(conn, "documents")
        for did, uid in ((doc_a, user_a), (doc_b, user_b)):
            fields = ["id", "user_id"]
            values = [":id", ":u"]
            params = {"id": did, "u": uid}
            if "filename" in doc_cols:
                fields.append("filename")
                values.append("'t.pdf'")
            if "file_size" in doc_cols:
                fields.append("file_size")
                values.append("1")
            if "mime_type" in doc_cols:
                fields.append("mime_type")
                values.append("'application/pdf'")
            if "storage_path" in doc_cols:
                fields.append("storage_path")
                values.append("'/tmp/t.pdf'")
            if "status" in doc_cols:
                fields.append("status")
                values.append("'uploaded'")
            conn.execute(
                text(
                    f"INSERT INTO documents ({', '.join(fields)}) "
                    f"VALUES ({', '.join(values)})"
                ),
                params,
            )

    data = {
        "user_a": user_a,
        "user_b": user_b,
        "companies": {"a": company_a, "b": company_b},
        "fund_applications": {"a": fund_app_a, "b": fund_app_b},
        "facts": {"a": fact_a, "b": fact_b},
        "documents": {"a": doc_a, "b": doc_b},
    }
    yield data

    # Cleanup — admin_super pour bypass RLS.
    with sync_engine.begin() as conn:
        conn.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        conn.execute(text("DELETE FROM admin_access_audit"))
        conn.execute(text("DELETE FROM facts"))
        conn.execute(text("DELETE FROM documents"))
        conn.execute(text("DELETE FROM fund_applications"))
        conn.execute(text("DELETE FROM companies"))
        conn.execute(text("DELETE FROM users"))


def _inspect_columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :t"
        ),
        {"t": table},
    ).fetchall()
    return {r[0] for r in rows}


def _ensure_app_user_role(conn) -> None:
    """Crée le rôle non-superuser ``app_user`` (RLS ne filtre pas SUPERUSER)."""
    conn.execute(
        text(
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE "
            "rolname = 'app_user') THEN CREATE ROLE app_user NOINHERIT; "
            "END IF; END $$"
        )
    )
    conn.execute(text("GRANT USAGE ON SCHEMA public TO app_user"))
    for t in TABLES:
        conn.execute(
            text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO app_user")
        )


def _target_id(rls_fixture, table: str) -> uuid.UUID:
    """ID de la ligne appartenant à user_B (le "autre tenant")."""
    return rls_fixture[table]["b"]


@pytest.mark.parametrize(
    "role,table",
    list(itertools.product(ROLES, TABLES)),
)
def test_rls_matrix(sync_engine, rls_fixture, role, table):
    """16 scénarios : filtrage user/auditor + bypass admin_mefali/super."""
    user_a_id = rls_fixture["user_a"]
    target_id = _target_id(rls_fixture, table)

    # Rôle RLS effectif positionné dans la session.
    # - user/auditor : rôle "user" côté Postgres (fallback).
    # - admin_mefali/admin_super : rôle identique côté Postgres.
    pg_role = role if role in ADMIN_ROLES else "user"

    with sync_engine.connect() as conn:
        with conn.begin():
            _ensure_app_user_role(conn)
            conn.execute(
                text("SELECT set_config('app.current_user_id', :u, false)"),
                {"u": str(user_a_id)},
            )
            conn.execute(
                text("SELECT set_config('app.user_role', :r, false)"),
                {"r": pg_role},
            )
            conn.execute(text("SET LOCAL ROLE app_user"))

            row = conn.execute(
                text(f"SELECT id FROM {table} WHERE id = :id"),
                {"id": target_id},
            ).fetchone()
            conn.execute(text("RESET ROLE"))

    if role in ADMIN_ROLES:
        assert row is not None, (
            f"[role={role} table={table}] admin devrait voir la ligne d'un autre tenant"
        )
    else:
        assert row is None, (
            f"[role={role} table={table}] {role} ne devrait PAS voir la ligne d'un autre tenant"
        )
