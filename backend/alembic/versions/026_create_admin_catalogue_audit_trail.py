"""create admin_catalogue_audit_trail (D6 FR64)

Revision ID: 026_catalogue_audit
Revises: 025_source_tracking
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 026/8.
Support Décision 6 (admin N1/N2/N3 + audit trail).

Audit trail immuable (write-only + read admin_super) avec rétention 5
ans documentée (FR64). Purge automatisée par worker Story 10.10 — hors
scope ici.

FR covered: [] (FR64)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "026_catalogue_audit"
down_revision: Union[str, None] = "025_source_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "admin_catalogue_audit_trail",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "action",
            sa.Enum(
                "create",
                "update",
                "delete",
                "publish",
                "retire",
                name="catalogue_action_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "workflow_level",
            sa.Enum(
                "N1",
                "N2",
                "N3",
                name="workflow_level_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "workflow_state_before", sa.String(length=32), nullable=True
        ),
        sa.Column(
            "workflow_state_after", sa.String(length=32), nullable=True
        ),
        sa.Column("changes_before", _jsonb_variant(), nullable=True),
        sa.Column("changes_after", _jsonb_variant(), nullable=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("correlation_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_catalogue_audit_entity_ts",
        "admin_catalogue_audit_trail",
        ["entity_type", "entity_id", "ts"],
    )
    op.create_index(
        "ix_catalogue_audit_actor_ts",
        "admin_catalogue_audit_trail",
        ["actor_user_id", "ts"],
    )
    op.create_index(
        "ix_catalogue_audit_level_ts",
        "admin_catalogue_audit_trail",
        ["workflow_level", "ts"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_catalogue_audit_level_ts",
        table_name="admin_catalogue_audit_trail",
    )
    op.drop_index(
        "ix_catalogue_audit_actor_ts",
        table_name="admin_catalogue_audit_trail",
    )
    op.drop_index(
        "ix_catalogue_audit_entity_ts",
        table_name="admin_catalogue_audit_trail",
    )
    op.drop_table("admin_catalogue_audit_trail")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS workflow_level_enum"))
        op.execute(sa.text("DROP TYPE IF EXISTS catalogue_action_enum"))
