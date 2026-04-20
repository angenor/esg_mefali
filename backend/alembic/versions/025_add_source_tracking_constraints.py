"""add source tracking constraints (NFR-SOURCE-TRACKING CCC-6)

Revision ID: 025_source_tracking
Revises: 024_rls_audit
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 025/8.
Support CCC-6 NFR-SOURCE-TRACKING.

Ajoute les colonnes source_url, source_accessed_at, source_version aux
tables catalogue legacy qui ne les ont pas déjà (funds, intermediaries).
Les nouvelles tables 021–023 (admin_maturity_*, criteria, referentials,
packs, document_templates, reusable_sections) les possèdent déjà.

CHECK constraint NOT VALID initialement puis VALIDATE CONSTRAINT pour
éviter de bloquer l'upgrade sur données legacy (backfill doux).

Table sources créée pour tracking centralisé (Story 10.11 CI nightly
HTTP 200).

FR covered: [] (infra NFR-SOURCE-TRACKING)
NFR covered: [NFR12, NFR27, NFR62, CCC-6]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "025_source_tracking"
down_revision: Union[str, None] = "024_rls_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables legacy recevant les 3 colonnes source (funds, intermediaries).
LEGACY_SOURCE_TABLES = ("funds", "intermediaries")

# Tables catalogue soumises au CHECK constraint (si is_published=true
# OU workflow_state='published' → source_* NOT NULL).
CHECK_TABLES = (
    ("funds", "status = 'active'"),  # legacy funds utilise status enum
    ("intermediaries", "is_active = true"),
    ("criteria", "is_published = true"),
    ("referentials", "is_published = true"),
    ("packs", "is_published = true"),
    ("document_templates", "is_published = true"),
    ("reusable_sections", "is_published = true"),
    ("admin_maturity_requirements", "is_published = true"),
    ("admin_maturity_levels", "is_published = true"),
)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # ---------- Ajout colonnes source aux tables legacy ----------
    for table in LEGACY_SOURCE_TABLES:
        op.add_column(
            table, sa.Column("source_url", sa.Text(), nullable=True)
        )
        op.add_column(
            table,
            sa.Column(
                "source_accessed_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.add_column(
            table,
            sa.Column("source_version", sa.String(length=64), nullable=True),
        )

    # ---------- Backfill doux tables legacy publiées ----------
    if dialect == "postgresql":
        op.execute(
            sa.text(
                "UPDATE funds SET "
                "source_version = 'pre-sourcing-2026-04', "
                "source_url = 'legacy://non-sourced', "
                "source_accessed_at = now() "
                "WHERE status = 'active' AND source_version IS NULL"
            )
        )
        op.execute(
            sa.text(
                "UPDATE intermediaries SET "
                "source_version = 'pre-sourcing-2026-04', "
                "source_url = 'legacy://non-sourced', "
                "source_accessed_at = now() "
                "WHERE is_active = true AND source_version IS NULL"
            )
        )

    # ---------- Table sources (tracking centralisé) ----------
    op.create_table(
        "sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                "pdf",
                "web",
                "regulation",
                "peer_reviewed",
                name="source_type_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "last_verified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("verified_by_admin_id", sa.UUID(), nullable=True),
        sa.Column(
            "http_status_last_check", sa.Integer(), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_admin_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_sources_url"),
    )

    # ---------- CHECK constraints (NOT VALID puis VALIDATE) ----------
    if dialect == "postgresql":
        for table, published_clause in CHECK_TABLES:
            check_name = f"ck_{table}_source_if_published"
            op.execute(
                sa.text(
                    f"ALTER TABLE {table} ADD CONSTRAINT {check_name} "
                    f"CHECK (NOT ({published_clause}) OR ("
                    f"source_url IS NOT NULL AND source_accessed_at IS NOT NULL "
                    f"AND source_version IS NOT NULL)) NOT VALID"
                )
            )
            op.execute(
                sa.text(
                    f"ALTER TABLE {table} VALIDATE CONSTRAINT {check_name}"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for table, _ in CHECK_TABLES:
            check_name = f"ck_{table}_source_if_published"
            op.execute(
                sa.text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {check_name}")
            )

    op.drop_table("sources")
    if dialect == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS source_type_enum"))

    for table in LEGACY_SOURCE_TABLES:
        op.drop_column(table, "source_version")
        op.drop_column(table, "source_accessed_at")
        op.drop_column(table, "source_url")
