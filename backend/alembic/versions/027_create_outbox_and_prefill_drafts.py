"""create domain_events (micro-Outbox D11) + prefill_drafts (Story 16.5)

Revision ID: 027_outbox_prefill
Revises: 026_catalogue_audit
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 027/8.
Support Décision 11 (micro-Outbox MVP) + Story 16.5 fallback UUID
prefill deep-link copilot.

domain_events : table événements outbox consommée par worker APScheduler
30s (Story 10.10) via FOR UPDATE SKIP LOCKED + index partiel PostgreSQL
(processed_at IS NULL AND retry_count < 5).

prefill_drafts : fallback deep-link copilot avec expires_at + nettoyage
worker (Story 10.10).

NOTE (arbitrage 2026-04-20, Q1) : le cleanup feature flag
ENABLE_PROJECT_MODEL est déplacé vers Story 20.1 (retrait code applicatif
uniquement, pas de nouvelle migration).

FR covered: [] (infra D11 + Story 16.5)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "027_outbox_prefill"
down_revision: Union[str, None] = "026_catalogue_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    # ---------- domain_events (D11 micro-Outbox MVP) ----------
    op.create_table(
        "domain_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.UUID(), nullable=False),
        sa.Column("payload", _jsonb_variant(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.CheckConstraint(
            "retry_count <= 5", name="ck_domain_events_retry_cap"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index partiel PostgreSQL (worker batch 30s SKIP LOCKED)
    op.create_index(
        "idx_domain_events_pending",
        "domain_events",
        ["created_at"],
        postgresql_where=sa.text(
            "processed_at IS NULL AND retry_count < 5"
        ),
    )
    op.create_index(
        "idx_domain_events_aggregate",
        "domain_events",
        ["aggregate_type", "aggregate_id"],
    )

    # ---------- prefill_drafts (Story 16.5 fallback deep-link copilot) ----------
    op.create_table(
        "prefill_drafts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("payload", _jsonb_variant(), nullable=False),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prefill_drafts_user_expires",
        "prefill_drafts",
        ["user_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prefill_drafts_user_expires", table_name="prefill_drafts"
    )
    op.drop_table("prefill_drafts")

    op.drop_index(
        "idx_domain_events_aggregate", table_name="domain_events"
    )
    op.drop_index(
        "idx_domain_events_pending",
        table_name="domain_events",
        postgresql_where=sa.text("processed_at IS NULL AND retry_count < 5"),
    )
    op.drop_table("domain_events")
