"""Modèle ORM `domain_events` — table micro-Outbox D11 (Story 10.10).

Le schéma est livré par migration `027_outbox_prefill` (Story 10.1) + ajout
`next_retry_at` par migration `029_outbox_next_retry_at` (Story 10.10).

Contrat :
- `event_type` : format `^[a-z_]+\\.[a-z_]+$` (ex. `project.created`).
- `status` : 4 valeurs finales `pending` / `processed` / `failed` / `unknown_handler`
  (voir `app.core.outbox.handlers.HandlerResult`).
- `retry_count` : contrainte DB `<= 5` (garde-fou), cap applicatif `< 3`
  (voir `app.core.outbox.worker.MAX_RETRIES`).
- `next_retry_at` : NULL tant que pas encore retenté ; sinon timestamptz +
  `BACKOFF_SCHEDULE[retry_count - 1]` (architecture.md §D11).

Voir `docs/CODEMAPS/outbox.md` pour le contrat complet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base


class DomainEvent(Base):
    """Événement métier transactionnel (Outbox pattern D11)."""

    __tablename__ = "domain_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", server_default="pending"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Story 10.10 — colonne ajoutée par migration 029 (MEDIUM-10.1-14).
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint("retry_count <= 5", name="ck_domain_events_retry_cap"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"DomainEvent(id={self.id}, event_type={self.event_type!r}, "
            f"status={self.status!r}, retry_count={self.retry_count})"
        )
