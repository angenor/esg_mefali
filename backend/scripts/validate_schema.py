"""Script d'audit schéma BDD vs metadata SQLAlchemy (Story 10.1 AC10).

Usage :
    TEST_ALEMBIC_URL=postgresql+psycopg2://... python scripts/validate_schema.py

Le script :
1. Applique `alembic upgrade head` sur la DB cible.
2. Compare `Base.metadata` (introspection Python) vs `sa.inspect(engine)`
   (schéma réel PostgreSQL).
3. Liste les tables présentes en base mais absentes des modèles
   (migrations sans modèle — normal en Phase 0 car les modèles 10.2-10.4
   ne sont pas encore livrés).
4. Code retour 0 = OK, 1 = divergence inattendue.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _backend_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    url = os.environ.get("TEST_ALEMBIC_URL")
    if not url:
        print("ERROR: set TEST_ALEMBIC_URL", file=sys.stderr)
        return 1

    cfg = Config(str(_backend_root() / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    sync_url = url.replace("+asyncpg", "").replace("+psycopg", "")
    if sync_url.startswith("postgresql://"):
        sync_url = "postgresql+psycopg2://" + sync_url[len("postgresql://") :]
    engine = create_engine(sync_url)
    insp = inspect(engine)
    db_tables = set(insp.get_table_names())

    # Import des modèles existants
    sys.path.insert(0, str(_backend_root()))
    from app.models.base import Base  # noqa: E402
    import app.models  # noqa: F401, E402

    model_tables = set(Base.metadata.tables.keys())

    only_db = db_tables - model_tables
    only_models = model_tables - db_tables

    # Les 30+ tables Story 10.1 n'ont pas encore de modèles (Stories 10.2-10.4)
    expected_schema_only = {
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
        "admin_access_audit", "sources", "admin_catalogue_audit_trail",
        "domain_events", "prefill_drafts",
    }
    unexpected_in_db = only_db - expected_schema_only
    print(f"DB tables         : {len(db_tables)}")
    print(f"Model tables      : {len(model_tables)}")
    print(f"Schema-only (10.1) : {len(only_db & expected_schema_only)} attendues")
    if unexpected_in_db:
        print(
            f"ERROR: tables inattendues en base : {sorted(unexpected_in_db)}",
            file=sys.stderr,
        )
        return 1
    if only_models:
        print(
            f"ERROR: modèles sans table BDD : {sorted(only_models)}",
            file=sys.stderr,
        )
        return 1
    print("OK — schéma aligné sur les modèles + extensions Story 10.1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
