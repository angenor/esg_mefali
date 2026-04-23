"""Seed fonds, intermédiaires, liaisons et chunks RAG financement (BUG-009)

Revision ID: 033_seed_financing_funds_intermediaries
Revises: 032_add_financing_chunks_embedding_v2_voyage
Create Date: 2026-04-23

Migration données idempotente — insère les 12 fonds verts réels, les 14
intermédiaires, les ~30 liaisons fonds-intermédiaires et les chunks RAG
textuels (sans embeddings — la génération nécessite un appel API async,
elle se fait via `seed.py` ou la tâche de post-migration).

Idempotence : guard SELECT COUNT(*) FROM funds > 0 → skip total.
Ré-exécution sans effet si des fonds existent déjà.

PostgreSQL uniquement : les tests unitaires SQLite créent les tables via
les modèles ORM directement et n'ont pas besoin de ce seed.
"""

from __future__ import annotations

import json
import uuid

import sqlalchemy as sa
from alembic import op

# Source unique des données — pas de duplication (pattern 10.5).
from app.modules.financing.seed import (
    FUND_INTERMEDIARY_LINKS,
    FUNDS_DATA,
    INTERMEDIARIES_DATA,
    _build_chunk_text,
    _build_intermediary_chunk_text,
)

revision = "033_seed_financing_funds_intermediaries"
down_revision = "032_add_financing_chunks_embedding_v2_voyage"
branch_labels = None
depends_on = None

_SEED_VERSION = "seed-v1-2026-04-23"


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        return

    count = bind.execute(sa.text("SELECT COUNT(*) FROM funds")).scalar()
    if count and count > 0:
        return

    _insert_funds(bind)
    _insert_intermediaries(bind)
    _insert_links(bind)
    _insert_chunks(bind)


def downgrade() -> None:
    """Pas de downgrade destructif pour une migration données."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enum_val(obj) -> str | None:
    if obj is None:
        return None
    return obj.value if hasattr(obj, "value") else str(obj)


def _json(obj) -> str | None:
    if obj is None:
        return None
    return json.dumps(obj, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Insertions
# ---------------------------------------------------------------------------


def _insert_funds(bind) -> None:
    sql = sa.text(
        "INSERT INTO funds ("
        "  id, name, organization,"
        "  fund_type, description, website_url,"
        "  contact_info, eligibility_criteria, sectors_eligible,"
        "  min_amount_xof, max_amount_xof,"
        "  required_documents, esg_requirements,"
        "  status, access_type, intermediary_type,"
        "  application_process, typical_timeline_months, success_tips,"
        "  source_url, source_accessed_at, source_version,"
        "  created_at, updated_at"
        ") VALUES ("
        "  :id, :name, :organization,"
        "  CAST(:fund_type AS fund_type_enum), :description, :website_url,"
        "  CAST(:contact_info AS jsonb),"
        "  CAST(:eligibility_criteria AS jsonb),"
        "  CAST(:sectors_eligible AS jsonb),"
        "  :min_amount_xof, :max_amount_xof,"
        "  CAST(:required_documents AS jsonb),"
        "  CAST(:esg_requirements AS jsonb),"
        "  CAST(:status AS fund_status_enum),"
        "  CAST(:access_type AS access_type_enum),"
        "  CAST(:intermediary_type AS intermediary_type_enum),"
        "  CAST(:application_process AS jsonb),"
        "  :typical_timeline_months, :success_tips,"
        "  :source_url, now(), :source_version,"
        "  now(), now()"
        ") ON CONFLICT (id) DO NOTHING"
    )

    for fund in FUNDS_DATA:
        bind.execute(
            sql,
            {
                "id": str(fund["id"]),
                "name": fund["name"],
                "organization": fund["organization"],
                "fund_type": _enum_val(fund["fund_type"]),
                "description": fund["description"],
                "website_url": fund.get("website_url"),
                "contact_info": _json(fund.get("contact_info")),
                "eligibility_criteria": _json(fund.get("eligibility_criteria", {})),
                "sectors_eligible": _json(fund.get("sectors_eligible", [])),
                "min_amount_xof": fund.get("min_amount_xof"),
                "max_amount_xof": fund.get("max_amount_xof"),
                "required_documents": _json(fund.get("required_documents", [])),
                "esg_requirements": _json(fund.get("esg_requirements", {})),
                "status": _enum_val(fund["status"]),
                "access_type": _enum_val(fund["access_type"]),
                "intermediary_type": _enum_val(fund.get("intermediary_type")),
                "application_process": _json(fund.get("application_process", [])),
                "typical_timeline_months": fund.get("typical_timeline_months"),
                "success_tips": fund.get("success_tips"),
                # Requis par le CHECK constraint migration 025
                "source_url": fund.get("website_url") or "legacy://non-sourced",
                "source_version": _SEED_VERSION,
            },
        )


def _insert_intermediaries(bind) -> None:
    sql = sa.text(
        "INSERT INTO intermediaries ("
        "  id, name, intermediary_type, organization_type,"
        "  description, country, city, website_url,"
        "  contact_email, contact_phone, physical_address,"
        "  accreditations, services_offered, typical_fees,"
        "  eligibility_for_sme, is_active,"
        "  source_url, source_accessed_at, source_version,"
        "  created_at, updated_at"
        ") VALUES ("
        "  :id, :name,"
        "  CAST(:intermediary_type AS intermediary_type_enum),"
        "  CAST(:organization_type AS organization_type_enum),"
        "  :description, :country, :city, :website_url,"
        "  :contact_email, :contact_phone, :physical_address,"
        "  CAST(:accreditations AS jsonb),"
        "  CAST(:services_offered AS jsonb),"
        "  :typical_fees,"
        "  CAST(:eligibility_for_sme AS jsonb),"
        "  true,"
        "  :source_url, now(), :source_version,"
        "  now(), now()"
        ") ON CONFLICT (id) DO NOTHING"
    )

    for inter in INTERMEDIARIES_DATA:
        bind.execute(
            sql,
            {
                "id": str(inter["id"]),
                "name": inter["name"],
                "intermediary_type": _enum_val(inter["intermediary_type"]),
                "organization_type": _enum_val(inter["organization_type"]),
                "description": inter.get("description"),
                "country": inter["country"],
                "city": inter["city"],
                "website_url": inter.get("website_url"),
                "contact_email": inter.get("contact_email"),
                "contact_phone": inter.get("contact_phone"),
                "physical_address": inter.get("physical_address"),
                "accreditations": _json(inter.get("accreditations", [])),
                "services_offered": _json(inter.get("services_offered", {})),
                "typical_fees": inter.get("typical_fees"),
                "eligibility_for_sme": _json(inter.get("eligibility_for_sme", {})),
                "source_url": inter.get("website_url") or "legacy://non-sourced",
                "source_version": _SEED_VERSION,
            },
        )


def _insert_links(bind) -> None:
    sql = sa.text(
        "INSERT INTO fund_intermediaries ("
        "  id, fund_id, intermediary_id, role, is_primary, geographic_coverage"
        ") VALUES ("
        "  gen_random_uuid(), :fund_id, :intermediary_id,"
        "  :role, :is_primary,"
        "  CAST(:geographic_coverage AS jsonb)"
        ") ON CONFLICT (fund_id, intermediary_id) DO NOTHING"
    )

    for link in FUND_INTERMEDIARY_LINKS:
        bind.execute(
            sql,
            {
                "fund_id": str(link["fund_id"]),
                "intermediary_id": str(link["intermediary_id"]),
                "role": link.get("role"),
                "is_primary": link.get("is_primary", False),
                "geographic_coverage": _json(link.get("geographic_coverage", [])),
            },
        )


def _insert_chunks(bind) -> None:
    sql = sa.text(
        "INSERT INTO financing_chunks ("
        "  id, source_type, source_id, content, created_at"
        ") VALUES ("
        "  :id,"
        "  CAST(:source_type AS financing_source_type_enum),"
        "  :source_id, :content, now()"
        ") ON CONFLICT (id) DO NOTHING"
    )

    for fund in FUNDS_DATA:
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"chunk.fund.{fund['id']}"))
        bind.execute(
            sql,
            {
                "id": chunk_id,
                "source_type": "fund",
                "source_id": str(fund["id"]),
                "content": _build_chunk_text(fund),
            },
        )

    for inter in INTERMEDIARIES_DATA:
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"chunk.intermediary.{inter['id']}"))
        bind.execute(
            sql,
            {
                "id": chunk_id,
                "source_type": "intermediary",
                "source_id": str(inter["id"]),
                "content": _build_intermediary_chunk_text(inter),
            },
        )
