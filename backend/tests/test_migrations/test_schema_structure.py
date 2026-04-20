"""AC3, AC4, AC6, AC7 — structure schéma après upgrade head.

Tests : en-têtes docstring, UUID PK, FK, indexes, contraintes
UNIQUE/CHECK, source tracking, retry cap, D4 cube 4D.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import inspect, text


pytestmark = pytest.mark.postgres


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"
NEW_MIGRATIONS = [
    "020_create_projects_schema.py",
    "021_create_maturity_schema.py",
    "022_create_esg_3_layers.py",
    "023_create_deliverables_engine.py",
    "024_enable_rls_on_sensitive_tables.py",
    "025_add_source_tracking_constraints.py",
    "026_create_admin_catalogue_audit_trail.py",
    "027_create_outbox_and_prefill_drafts.py",
]
NEW_TABLES = [
    "companies", "projects", "project_memberships",
    "project_role_permissions", "project_snapshots", "company_projections",
    "beneficiary_profiles",
    "admin_maturity_levels", "formalization_plans",
    "admin_maturity_requirements",
    "facts", "fact_versions", "criteria", "criterion_derivation_rules",
    "criterion_referential_map", "referentials", "referential_versions",
    "referential_migrations", "packs", "pack_criteria",
    "referential_verdicts",
    "document_templates", "template_sections", "reusable_sections",
    "reusable_section_prompt_versions", "atomic_blocks",
    "fund_application_generation_logs",
    "admin_access_audit",
    "sources",
    "admin_catalogue_audit_trail",
    "domain_events", "prefill_drafts",
]


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


# --- AC3 : metadata / docstrings -------------------------------------------

def test_migration_docstrings_present():
    """AC3 — chaque migration 020-027 a un docstring contenant Story 10.1."""
    for fname in NEW_MIGRATIONS:
        content = (MIGRATIONS_DIR / fname).read_text(encoding="utf-8")
        assert content.startswith('"""'), f"{fname} sans docstring"
        assert "Story 10.1" in content, f"{fname} ne cite pas Story 10.1"
        assert re.search(r"Revision ID:\s*\S+", content), f"{fname} sans Revision ID"
        assert re.search(r"Revises:\s*\S+", content), f"{fname} sans Revises"
        assert "Create Date:" in content, f"{fname} sans Create Date"


def test_revision_ids_verbose():
    """AC3 — Revision ID verbose convention (020_projects, ..., 027_outbox_prefill)."""
    expected = {
        "020_create_projects_schema.py": "020_projects",
        "021_create_maturity_schema.py": "021_maturity",
        "022_create_esg_3_layers.py": "022_esg_3layers",
        "023_create_deliverables_engine.py": "023_deliverables",
        "024_enable_rls_on_sensitive_tables.py": "024_rls_audit",
        "025_add_source_tracking_constraints.py": "025_source_tracking",
        "026_create_admin_catalogue_audit_trail.py": "026_catalogue_audit",
        "027_create_outbox_and_prefill_drafts.py": "027_outbox_prefill",
    }
    for fname, rev in expected.items():
        content = (MIGRATIONS_DIR / fname).read_text(encoding="utf-8")
        assert f'revision: str = "{rev}"' in content, (
            f"{fname} revision_id attendu {rev!r}"
        )


# --- AC4 : UUID PK + conventions types -------------------------------------

def test_all_new_tables_exist(sync_engine):
    insp = inspect(sync_engine)
    existing = set(insp.get_table_names())
    missing = set(NEW_TABLES) - existing
    assert not missing, f"Tables manquantes après upgrade head : {missing}"


def test_uuid_pks_everywhere(sync_engine):
    """AC4 — PK UUID sur toutes les nouvelles tables."""
    insp = inspect(sync_engine)
    for table in NEW_TABLES:
        pk = insp.get_pk_constraint(table)
        cols = {c["name"]: c for c in insp.get_columns(table)}
        for pk_col in pk["constrained_columns"]:
            col_type = str(cols[pk_col]["type"]).upper()
            assert "UUID" in col_type or pk_col != "id", (
                f"{table}.{pk_col} PK non-UUID ({col_type})"
            )


# --- AC7 : FK + UNIQUE + indexes composites --------------------------------

def test_project_memberships_unique_triplet(sync_engine):
    """AC7 — UNIQUE (project_id, company_id, role) sur project_memberships."""
    insp = inspect(sync_engine)
    uqs = insp.get_unique_constraints("project_memberships")
    triplets = [tuple(u["column_names"]) for u in uqs]
    assert ("project_id", "company_id", "role") in triplets, (
        f"UNIQUE triplet manquant, trouvé : {triplets}"
    )


def test_projects_composite_index(sync_engine):
    """AC7 — index B-tree (company_id, status) sur projects."""
    insp = inspect(sync_engine)
    idx_names = [
        i["name"] for i in insp.get_indexes("projects")
        if i["column_names"] == ["company_id", "status"]
    ]
    assert idx_names, "index (company_id, status) absent sur projects"


def test_fund_applications_project_id_not_null(sync_engine):
    """AC7 — fund_applications.project_id NOT NULL (Q2 arbitrage)."""
    insp = inspect(sync_engine)
    cols = {c["name"]: c for c in insp.get_columns("fund_applications")}
    assert "project_id" in cols, "colonne project_id absente"
    assert not cols["project_id"]["nullable"], (
        "project_id doit être NOT NULL (Q2 arbitrage 2026-04-20)"
    )


def test_referential_verdicts_composite_index(sync_engine):
    """AC7 — index (fund_application_id, criterion_id, referential_id)."""
    insp = inspect(sync_engine)
    triplets = [
        tuple(i["column_names"]) for i in insp.get_indexes("referential_verdicts")
    ]
    assert (
        "fund_application_id",
        "criterion_id",
        "referential_id",
    ) in triplets, f"index composite absent, trouvé : {triplets}"


def test_referential_verdicts_invalidated_at_column(sync_engine):
    """AC7 D3 — colonne invalidated_at TIMESTAMPTZ NULL présente."""
    insp = inspect(sync_engine)
    cols = {c["name"]: c for c in insp.get_columns("referential_verdicts")}
    assert "invalidated_at" in cols
    assert cols["invalidated_at"]["nullable"] is True


def test_domain_events_retry_cap_check(sync_engine):
    """AC7 D11 — CHECK retry_count <= 5 sur domain_events."""
    insp = inspect(sync_engine)
    checks = insp.get_check_constraints("domain_events")
    names = [c["name"] for c in checks]
    assert "ck_domain_events_retry_cap" in names, (
        f"CHECK retry_count manquant, trouvé : {names}"
    )


def test_domain_events_partial_index(sync_engine):
    """AC7 D11 — index partiel WHERE processed_at IS NULL AND retry_count < 5."""
    with sync_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'domain_events' "
                "AND indexname = 'idx_domain_events_pending'"
            )
        ).fetchall()
    assert rows, "index idx_domain_events_pending absent"
    indexdef = rows[0][0].lower()
    assert "processed_at is null" in indexdef
    assert "retry_count < 5" in indexdef


def test_prefill_drafts_user_fk_cascade(sync_engine):
    """AC7 — FK user_id ON DELETE CASCADE sur prefill_drafts."""
    insp = inspect(sync_engine)
    fks = insp.get_foreign_keys("prefill_drafts")
    user_fks = [fk for fk in fks if fk["constrained_columns"] == ["user_id"]]
    assert user_fks, "FK user_id absente"
    assert user_fks[0]["options"].get("ondelete", "").upper() == "CASCADE"


def test_catalogue_audit_trail_indexes(sync_engine):
    """AC7 D6 — indexes (entity_type, entity_id, ts), (actor_user_id, ts), (workflow_level, ts)."""
    insp = inspect(sync_engine)
    idx_triplets = [
        tuple(i["column_names"])
        for i in insp.get_indexes("admin_catalogue_audit_trail")
    ]
    assert ("entity_type", "entity_id", "ts") in idx_triplets
    assert ("actor_user_id", "ts") in idx_triplets
    assert ("workflow_level", "ts") in idx_triplets


# --- AC6 : CHECK source tracking -------------------------------------------

def test_source_tracking_columns_on_legacy_tables(sync_engine):
    """AC6 — colonnes source ajoutées sur funds et intermediaries."""
    insp = inspect(sync_engine)
    for table in ("funds", "intermediaries"):
        cols = {c["name"] for c in insp.get_columns(table)}
        assert {"source_url", "source_accessed_at", "source_version"}.issubset(cols)


def test_source_tracking_check_constraint_published(sync_engine):
    """AC6 — CHECK bloque insertion d'un criterion published sans source_*."""
    with sync_engine.begin() as conn:
        # Insertion sans source_* doit passer en draft
        conn.execute(
            text(
                "INSERT INTO criteria (id, code, label_fr, dimension, "
                "workflow_state, is_published) VALUES "
                "(gen_random_uuid(), 'test-001', 'Test 1', 'E', 'draft', false)"
            )
        )
    # Insertion published sans source_* doit échouer
    with pytest.raises(Exception) as exc_info, sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO criteria (id, code, label_fr, dimension, "
                "workflow_state, is_published) VALUES "
                "(gen_random_uuid(), 'test-002', 'Test 2', 'E', 'published', true)"
            )
        )
    err = str(exc_info.value).lower()
    assert "ck_criteria_source_if_published" in err or "check" in err


# --- AC7 GIN : mv_fund_matching_cube ---------------------------------------

def test_mv_fund_matching_cube_exists(sync_engine):
    """AC7 D4 — vue matérialisée mv_fund_matching_cube créée."""
    with sync_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT 1 FROM pg_matviews WHERE matviewname = 'mv_fund_matching_cube'"
            )
        ).fetchone()
    assert row is not None, "mv_fund_matching_cube manquante"


def test_mv_fund_matching_cube_gin_indexes(sync_engine):
    """AC7 D4 — indexes GIN sur sectors_eligible et countries_eligible."""
    with sync_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'mv_fund_matching_cube'"
            )
        ).fetchall()
    defs = " ".join(r[0].lower() for r in rows)
    assert "gin" in defs, f"aucun index GIN, trouvé : {defs}"
    assert "sectors_eligible" in defs
    assert "countries_eligible" in defs


# --- AC3 down_revision chaîne linéaire -------------------------------------

def test_down_revision_chain():
    """AC3 — chaîne 019 ← 020 ← 021 ← 022 ← 023 ← 024 ← 025 ← 026 ← 027."""
    pairs = {
        "020_create_projects_schema.py": "019_manual_edits",
        "021_create_maturity_schema.py": "020_projects",
        "022_create_esg_3_layers.py": "021_maturity",
        "023_create_deliverables_engine.py": "022_esg_3layers",
        "024_enable_rls_on_sensitive_tables.py": "023_deliverables",
        "025_add_source_tracking_constraints.py": "024_rls_audit",
        "026_create_admin_catalogue_audit_trail.py": "025_source_tracking",
        "027_create_outbox_and_prefill_drafts.py": "026_catalogue_audit",
    }
    for fname, expected_parent in pairs.items():
        content = (MIGRATIONS_DIR / fname).read_text(encoding="utf-8")
        assert f'down_revision: Union[str, None] = "{expected_parent}"' in content, (
            f"{fname} down_revision incorrect, attendu {expected_parent}"
        )
