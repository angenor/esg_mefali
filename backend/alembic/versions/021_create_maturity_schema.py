"""create maturity schema (Cluster A' FR11-FR16)

Revision ID: 021_maturity
Revises: 020_projects
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 021/8.
Support Cluster A' (maturité graduée + formalisation).

Tables créées : admin_maturity_levels (catalogue N1, 5 niveaux gradués),
formalization_plans (plan par company), admin_maturity_requirements
(exigences par pays × niveau).

Colonnes source_url/source_accessed_at/source_version ajoutées ici
(contraintes CHECK activées par migration 025).

FR covered: [] (infra FR11-FR16)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "021_maturity"
down_revision: Union[str, None] = "020_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "admin_maturity_levels",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
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
        sa.CheckConstraint("level BETWEEN 1 AND 5", name="ck_maturity_level_1_5"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("level", name="uq_maturity_level"),
        sa.UniqueConstraint("code", name="uq_maturity_code"),
    )

    op.create_table(
        "formalization_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("current_level_id", sa.UUID(), nullable=True),
        sa.Column("target_level_id", sa.UUID(), nullable=True),
        sa.Column("actions_json", _jsonb_variant(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="draft",
        ),
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
            ["current_level_id"],
            ["admin_maturity_levels.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_level_id"],
            ["admin_maturity_levels.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_formalization_plans_company_id",
        "formalization_plans",
        ["company_id"],
    )

    op.create_table(
        "admin_maturity_requirements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("level_id", sa.UUID(), nullable=False),
        sa.Column("requirements_json", _jsonb_variant(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["level_id"],
            ["admin_maturity_levels.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "country", "level_id", name="uq_maturity_country_level"
        ),
    )


def downgrade() -> None:
    op.drop_table("admin_maturity_requirements")
    op.drop_index(
        "ix_formalization_plans_company_id",
        table_name="formalization_plans",
    )
    op.drop_table("formalization_plans")
    op.drop_table("admin_maturity_levels")
