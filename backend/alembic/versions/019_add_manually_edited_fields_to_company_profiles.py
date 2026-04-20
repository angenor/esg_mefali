"""add manually_edited_fields to company_profiles

Revision ID: 019_manual_edits
Revises: 018_interactive
Create Date: 2026-04-18

Story 9.5 — P1 #7 : flag des champs edites manuellement pour que le tool LLM
`update_company_profile` ne les ecrase jamais silencieusement (spec 003 §3.6).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019_manual_edits"
down_revision: Union[str, None] = "018_interactive"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # JSONB en Postgres ; variant JSON pour SQLite (tests in-memory conftest.py).
    # server_default '[]' garantit une liste vide non-NULL pour les profils
    # anterieurs a la migration (AC4 : retro-compatibilite, pas de backfill).
    op.add_column(
        "company_profiles",
        sa.Column(
            "manually_edited_fields",
            sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("company_profiles", "manually_edited_fields")
