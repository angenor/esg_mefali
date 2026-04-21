"""seed Annexe F sources catalogue (Story 10.11)

Revision ID: 030_seed_sources_annexe_f
Revises: 029_outbox_next_retry_at
Create Date: 2026-04-21

Story 10.11 — sourcing documentaire Annexe F + CI nightly source_url
health-check.

Migration **données** (pas structurelle) : insère les 22 sources
officielles ESG/financement vert de l'Annexe F PRD dans la table
`sources` créée par la migration 025.

Idempotente via `INSERT ... ON CONFLICT (url) DO NOTHING`. Ré-exécution
sans effet (contrainte `uq_sources_url`).

Source unique de vérité : `backend.app.core.sources.annexe_f_seed.
ANNEXE_F_SOURCES` (pattern 10.5 « pas de duplication »).
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.core.sources.annexe_f_seed import ANNEXE_F_SOURCES

# revision identifiers, used by Alembic.
revision = "030_seed_sources_annexe_f"
down_revision = "029_outbox_next_retry_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insère les sources Annexe F (idempotent ON CONFLICT)."""

    bind = op.get_bind()
    dialect = bind.dialect.name

    now = datetime.now(timezone.utc)

    sources_table = sa.table(
        "sources",
        sa.column("id", sa.UUID()),
        sa.column("url", sa.Text()),
        sa.column("source_type", sa.Text()),
        sa.column("last_verified_at", sa.DateTime(timezone=True)),
        sa.column("http_status_last_check", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    if dialect == "postgresql":
        # ON CONFLICT DO NOTHING natif Postgres — préserve l'idempotence
        # sans perdre la contrainte UNIQUE(url).
        for seed in ANNEXE_F_SOURCES:
            op.execute(
                sa.text(
                    "INSERT INTO sources "
                    "(id, url, source_type, last_verified_at, "
                    "http_status_last_check, created_at) "
                    "VALUES (gen_random_uuid(), :url, :source_type, "
                    ":verified, NULL, :created) "
                    "ON CONFLICT (url) DO NOTHING"
                ).bindparams(
                    url=seed.url,
                    source_type=seed.source_type,
                    verified=now,
                    created=now,
                )
            )
        return

    # SQLite (tests) : INSERT OR IGNORE équivaut à ON CONFLICT DO NOTHING.
    import uuid

    for seed in ANNEXE_F_SOURCES:
        op.execute(
            sa.text(
                "INSERT OR IGNORE INTO sources "
                "(id, url, source_type, last_verified_at, "
                "http_status_last_check, created_at) "
                "VALUES (:id, :url, :source_type, :verified, NULL, :created)"
            ).bindparams(
                id=str(uuid.uuid4()),
                url=seed.url,
                source_type=seed.source_type,
                verified=now.isoformat(),
                created=now.isoformat(),
            )
        )


def downgrade() -> None:
    """Pas de downgrade destructif pour une migration données.

    Les lignes peuvent être supprimées manuellement si nécessaire via
    `DELETE FROM sources WHERE url = ANY (...)`. Un downgrade automatique
    pourrait retirer des sources ajoutées par l'admin N3 entre-temps.
    """

    pass
