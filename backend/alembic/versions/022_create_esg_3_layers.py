"""create ESG 3 layers schema + mv_fund_matching_cube (D3 + D4)

Revision ID: 022_esg_3layers
Revises: 021_maturity
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 022/8.
Support Décision 3 (ESG 3 couches + DSL borné anti-RCE) + Décision 4
(cube 4D PostgreSQL + GIN).

Couche 1 Faits : facts, fact_versions (audit trail FR19).
Couche 2 Critères & DSL borné : criteria, criterion_derivation_rules
(JSONB validé Pydantic côté app, PAS d'eval), criterion_referential_map.
Couche 3 Verdicts matérialisés : referentials, referential_versions,
referential_migrations, packs, pack_criteria, referential_verdicts.
Vue matérialisée mv_fund_matching_cube (PostgreSQL-only) + GIN indexes
sur sectors_eligible/countries_eligible (D4 p95 ≤ 2 s).

FR covered: [] (infra FR17-FR26)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "022_esg_3layers"
down_revision: Union[str, None] = "021_maturity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    # ===== Couche 1 : Faits =====
    op.create_table(
        "facts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=True),
        sa.Column("fact_type", sa.String(length=64), nullable=False),
        sa.Column("value_json", _jsonb_variant(), nullable=False),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("collected_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_facts_company_criterion",
        "facts",
        ["company_id", "criterion_id"],
    )

    op.create_table(
        "fact_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fact_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("value_json", _jsonb_variant(), nullable=False),
        sa.Column("changed_by_user_id", sa.UUID(), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["fact_id"], ["facts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fact_id", "version_number", name="uq_fact_version"
        ),
    )
    op.create_index(
        "ix_fact_versions_fact_version",
        "fact_versions",
        ["fact_id", "version_number"],
    )

    # ===== Couche 2 : Critères & DSL borné =====
    op.create_table(
        "criteria",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label_fr", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dimension", sa.String(length=32), nullable=False),
        sa.Column(
            "workflow_state",
            sa.String(length=16),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_version", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_criteria_code"),
    )

    # FK différée : facts est créé avant criteria (Couche 1 avant Couche 2),
    # on ajoute la FK maintenant que les deux tables existent. SET NULL car
    # un fact historique reste pertinent même si son critère est retiré (audit FR19).
    op.create_foreign_key(
        "fk_facts_criterion_id",
        "facts",
        "criteria",
        ["criterion_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "criterion_derivation_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False),
        sa.Column("rule_json", _jsonb_variant(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rule_type IN ('threshold','boolean_expression','aggregate','qualitative_check')",
            name="ck_rule_type_enum",
        ),
        sa.ForeignKeyConstraint(
            ["criterion_id"], ["criteria.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ===== Couche 3 : Référentiels =====
    op.create_table(
        "referentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label_fr", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "workflow_state",
            sa.String(length=16),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_version", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_referentials_code"),
    )

    op.create_table(
        "referential_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("referential_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", _jsonb_variant(), nullable=False),
        sa.ForeignKeyConstraint(
            ["referential_id"], ["referentials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "referential_id", "version", name="uq_referential_version"
        ),
    )

    op.create_table(
        "referential_migrations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("from_version_id", sa.UUID(), nullable=False),
        sa.Column("to_version_id", sa.UUID(), nullable=False),
        sa.Column("mapping_json", _jsonb_variant(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["from_version_id"],
            ["referential_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_version_id"],
            ["referential_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "criterion_referential_map",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column("referential_id", sa.UUID(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["criterion_id"], ["criteria.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["referential_id"], ["referentials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "criterion_id",
            "referential_id",
            name="uq_criterion_referential",
        ),
    )

    op.create_table(
        "packs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label_fr", sa.String(length=255), nullable=False),
        sa.Column(
            "workflow_state",
            sa.String(length=16),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_version", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_packs_code"),
    )

    op.create_table(
        "pack_criteria",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("pack_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column("fund_specific_overlay_rule", _jsonb_variant(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pack_id"], ["packs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["criterion_id"], ["criteria.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pack_id", "criterion_id", name="uq_pack_criterion"
        ),
    )

    op.create_table(
        "referential_verdicts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fund_application_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column("referential_id", sa.UUID(), nullable=False),
        sa.Column(
            "verdict",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("details_json", _jsonb_variant(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["fund_application_id"],
            ["fund_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["criterion_id"], ["criteria.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["referential_id"], ["referentials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_referential_verdicts_composite",
        "referential_verdicts",
        ["fund_application_id", "criterion_id", "referential_id"],
    )

    # ===== D4 mv_fund_matching_cube (PostgreSQL only) =====
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                CREATE MATERIALIZED VIEW mv_fund_matching_cube AS
                SELECT
                    f.id AS fund_id,
                    f.name AS fund_name,
                    f.sectors_eligible,
                    COALESCE(
                        (SELECT jsonb_agg(DISTINCT i.country)
                         FROM fund_intermediaries fi
                         JOIN intermediaries i ON i.id = fi.intermediary_id
                         WHERE fi.fund_id = f.id),
                        '[]'::jsonb
                    ) AS countries_eligible,
                    f.min_amount_xof,
                    f.max_amount_xof,
                    f.status
                FROM funds f
                """
            )
        )
        op.execute(
            sa.text(
                "CREATE INDEX idx_mv_cube_sectors ON mv_fund_matching_cube "
                "USING GIN ((sectors_eligible::jsonb))"
            )
        )
        op.execute(
            sa.text(
                "CREATE INDEX idx_mv_cube_countries ON mv_fund_matching_cube "
                "USING GIN (countries_eligible)"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP INDEX IF EXISTS idx_mv_cube_countries"))
        op.execute(sa.text("DROP INDEX IF EXISTS idx_mv_cube_sectors"))
        op.execute(
            sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_fund_matching_cube")
        )

    op.drop_index(
        "ix_referential_verdicts_composite", table_name="referential_verdicts"
    )
    op.drop_table("referential_verdicts")
    op.drop_table("pack_criteria")
    op.drop_table("packs")
    op.drop_table("criterion_referential_map")
    op.drop_table("referential_migrations")
    op.drop_table("referential_versions")
    op.drop_table("referentials")
    op.drop_table("criterion_derivation_rules")
    op.drop_constraint("fk_facts_criterion_id", "facts", type_="foreignkey")
    op.drop_table("criteria")
    op.drop_index("ix_fact_versions_fact_version", table_name="fact_versions")
    op.drop_table("fact_versions")
    op.drop_index("ix_facts_company_criterion", table_name="facts")
    op.drop_table("facts")
