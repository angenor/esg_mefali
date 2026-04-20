"""AC8 — cycles CRUD INSERT → SELECT → UPDATE → DELETE sur les nouvelles tables.

Tests via raw SQL + gen_random_uuid() (PostgreSQL). Les modèles ORM
viennent Story 10.2 / 10.3 / 10.4.
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import text


pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture
def seed_user(sync_engine):
    """Insère un user pour satisfaire les FK."""
    user_id = uuid.uuid4()
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, full_name, "
                "company_name, is_active) VALUES "
                "(:id, :email, :pwd, 'Test', 'Test Co', true)"
            ),
            {
                "id": user_id,
                "email": f"test-{user_id.hex[:8]}@example.com",
                "pwd": "hashed",
            },
        )
    yield user_id
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})


def _crud_cycle(sync_engine, table: str, insert_sql: str, params: dict,
                update_sql: str, update_params: dict, pk: uuid.UUID):
    with sync_engine.begin() as conn:
        conn.execute(text(insert_sql), params)
    with sync_engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT id FROM {table} WHERE id = :id"), {"id": pk}
        ).fetchone()
    assert row is not None, f"INSERT {table} : ligne non trouvée"
    with sync_engine.begin() as conn:
        conn.execute(text(update_sql), update_params)
    with sync_engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {table} WHERE id = :id"), {"id": pk}
        )
    with sync_engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT id FROM {table} WHERE id = :id"), {"id": pk}
        ).fetchone()
    assert row is None, f"DELETE {table} : ligne persistée"


def test_companies_crud(sync_engine, seed_user):
    pk = uuid.uuid4()
    _crud_cycle(
        sync_engine, "companies",
        "INSERT INTO companies (id, owner_user_id, name) "
        "VALUES (:id, :u, 'Acme')",
        {"id": pk, "u": seed_user},
        "UPDATE companies SET name = 'Acme 2' WHERE id = :id",
        {"id": pk},
        pk,
    )


def test_projects_crud(sync_engine, seed_user):
    company_id = uuid.uuid4()
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO companies (id, owner_user_id, name) "
                "VALUES (:id, :u, 'ProjCo')"
            ),
            {"id": company_id, "u": seed_user},
        )
    pk = uuid.uuid4()
    _crud_cycle(
        sync_engine, "projects",
        "INSERT INTO projects (id, company_id, name) "
        "VALUES (:id, :c, 'Proj 1')",
        {"id": pk, "c": company_id},
        "UPDATE projects SET name = 'Proj 2' WHERE id = :id",
        {"id": pk},
        pk,
    )
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM companies WHERE id = :id"), {"id": company_id})


def test_domain_events_crud(sync_engine):
    pk = uuid.uuid4()
    aggregate_id = uuid.uuid4()
    _crud_cycle(
        sync_engine, "domain_events",
        "INSERT INTO domain_events (id, event_type, aggregate_type, "
        "aggregate_id, payload) VALUES "
        "(:id, 'test', 'project', :agg, '{}'::jsonb)",
        {"id": pk, "agg": aggregate_id},
        "UPDATE domain_events SET retry_count = 1 WHERE id = :id",
        {"id": pk},
        pk,
    )


def test_prefill_drafts_crud(sync_engine, seed_user):
    pk = uuid.uuid4()
    _crud_cycle(
        sync_engine, "prefill_drafts",
        "INSERT INTO prefill_drafts (id, user_id, payload, expires_at) "
        "VALUES (:id, :u, '{}'::jsonb, now() + interval '1 day')",
        {"id": pk, "u": seed_user},
        "UPDATE prefill_drafts SET payload = CAST('{\"k\": 1}' AS jsonb) WHERE id = :id",
        {"id": pk},
        pk,
    )


def test_domain_events_retry_cap_rejects_6(sync_engine):
    """CHECK retry_count <= 5 rejette 6."""
    with pytest.raises(Exception), sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO domain_events (id, event_type, aggregate_type, "
                "aggregate_id, payload, retry_count) VALUES "
                "(gen_random_uuid(), 't', 't', gen_random_uuid(), '{}'::jsonb, 6)"
            )
        )


def test_project_memberships_unique_triplet_rejects_duplicate(
    sync_engine, seed_user
):
    """UNIQUE (project_id, company_id, role) rejette un doublon exact."""
    company_id = uuid.uuid4()
    project_id = uuid.uuid4()
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO companies (id, owner_user_id, name) "
                "VALUES (:id, :u, 'C')"
            ),
            {"id": company_id, "u": seed_user},
        )
        conn.execute(
            text(
                "INSERT INTO projects (id, company_id, name) "
                "VALUES (:id, :c, 'P')"
            ),
            {"id": project_id, "c": company_id},
        )
        conn.execute(
            text(
                "INSERT INTO project_memberships (id, project_id, company_id, role) "
                "VALUES (gen_random_uuid(), :p, :c, 'porteur_principal')"
            ),
            {"p": project_id, "c": company_id},
        )
    with pytest.raises(Exception), sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO project_memberships (id, project_id, company_id, role) "
                "VALUES (gen_random_uuid(), :p, :c, 'porteur_principal')"
            ),
            {"p": project_id, "c": company_id},
        )
    # Une company peut cumuler deux rôles distincts
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO project_memberships (id, project_id, company_id, role) "
                "VALUES (gen_random_uuid(), :p, :c, 'beneficiaire')"
            ),
            {"p": project_id, "c": company_id},
        )
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM companies WHERE id = :id"), {"id": company_id})
