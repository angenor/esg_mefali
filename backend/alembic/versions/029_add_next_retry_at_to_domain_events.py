"""add next_retry_at to domain_events (MEDIUM-10.1-14)

Revision ID: 029_outbox_next_retry_at
Revises: 028_audit_tamper
Create Date: 2026-04-21

Story 10.10 — micro-Outbox worker batch 30 s + retry exponentiel.

Absorbe la dette `MEDIUM-10.1-14` (colonne `next_retry_at` manquante
dans le schéma 027). Sans ce champ, le worker serait forcé à un retry
immédiat sur toute ligne en échec (ordre `created_at` ASC) → hot-loop
CPU + pression BDD. Le worker calcule :

    next_retry_at = now() + interval BACKOFF_SCHEDULE[retry_count - 1]

avec `BACKOFF_SCHEDULE = (30, 120, 600)` secondes (architecture.md §D11).

**L'index partiel `idx_domain_events_pending` (créé par 027) n'est pas
recréé ici** : intégrer `next_retry_at <= now()` dans un `WHERE` partiel
serait refusé par PostgreSQL (`now()` est non-IMMUTABLE). Le filtre
applicatif `(next_retry_at IS NULL OR next_retry_at <= now())` vit donc
dans la query worker `process_outbox_batch` (voir
`backend/app/core/outbox/worker.py`).

FR covered: [] (infra D11)
NFR covered: [NFR37, NFR75, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "029_outbox_next_retry_at"
down_revision: Union[str, None] = "028_audit_tamper"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "domain_events",
        sa.Column(
            "next_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("domain_events", "next_retry_at")
