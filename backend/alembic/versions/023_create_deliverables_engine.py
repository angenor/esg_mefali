"""create deliverables engine (pyramide Template → Section → Block) — D5

Revision ID: 023_deliverables
Revises: 022_esg_3layers
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 023/8.
Support Décision 5 (moteur livrables + prompt versioning FR57).

Tables créées : document_templates, template_sections, reusable_sections,
reusable_section_prompt_versions, atomic_blocks,
fund_application_generation_logs.

FR44 NO BYPASS : reusable_sections.human_review_required NOT NULL +
CHECK (human_review_required = true WHERE code IN ('sges_beta', ...)).

FR covered: [] (infra FR36-FR44, FR57)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "023_deliverables"
down_revision: Union[str, None] = "022_esg_3layers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "document_templates",
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
        sa.UniqueConstraint("code", name="uq_document_templates_code"),
    )

    op.create_table(
        "reusable_sections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label_fr", sa.String(length=255), nullable=False),
        sa.Column(
            "human_review_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        sa.CheckConstraint(
            "(code NOT IN ('sges_beta','esia','stakeholder_engagement_plan')) "
            "OR human_review_required = true",
            name="ck_no_bypass_human_review",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_reusable_sections_code"),
    )

    op.create_table(
        "template_sections",
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID(), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["template_id"], ["document_templates.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["section_id"], ["reusable_sections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("template_id", "section_id"),
    )

    op.create_table(
        "reusable_section_prompt_versions",
        sa.Column("section_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("llm_model", sa.String(length=64), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["section_id"], ["reusable_sections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("section_id", "version"),
    )

    op.create_table(
        "atomic_blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID(), nullable=False),
        sa.Column("block_type", sa.String(length=32), nullable=False),
        sa.Column("content", _jsonb_variant(), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["section_id"], ["reusable_sections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fund_application_generation_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fund_application_id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID(), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("llm_model_version", sa.String(length=64), nullable=True),
        sa.Column("prompt_anonymized", sa.Text(), nullable=True),
        sa.Column("referentials_versions", _jsonb_variant(), nullable=True),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["fund_application_id"],
            ["fund_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"], ["reusable_sections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fund_application_generation_logs_app_generated",
        "fund_application_generation_logs",
        ["fund_application_id", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fund_application_generation_logs_app_generated",
        table_name="fund_application_generation_logs",
    )
    op.drop_table("fund_application_generation_logs")
    op.drop_table("atomic_blocks")
    op.drop_table("reusable_section_prompt_versions")
    op.drop_table("template_sections")
    op.drop_table("reusable_sections")
    op.drop_table("document_templates")
