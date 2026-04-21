"""Tests E2E PostgreSQL — worker Outbox SKIP LOCKED + retry + dead-letter.

Story 10.10 AC2 / AC4 / AC7 / AC9 bonus.

**Marker @pytest.mark.postgres obligatoire** : ``SELECT FOR UPDATE SKIP
LOCKED`` est PostgreSQL-only (incompatible SQLite — leçon Story 10.1).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.outbox import handlers as handlers_mod
from app.core.outbox.handlers import HandlerEntry
from app.core.outbox.worker import process_outbox_batch, purge_expired_prefill_drafts
from app.core.outbox.writer import write_domain_event
from app.models.domain_event import DomainEvent

pytestmark = pytest.mark.postgres


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_event(
    engine: AsyncEngine,
    *,
    event_type: str = "noop.test",
    aggregate_type: str = "project",
) -> uuid.UUID:
    """Insère un event via le writer (transaction propre)."""
    async with AsyncSession(engine, expire_on_commit=False) as db:
        event = await write_domain_event(
            db,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=uuid.uuid4(),
            payload={"idx": 0},
        )
        event_id = event.id  # capturer avant commit
        await db.commit()
        return event_id


async def _fetch_event(engine: AsyncEngine, event_id: uuid.UUID) -> DomainEvent:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        result = await db.execute(
            select(DomainEvent).where(DomainEvent.id == event_id)
        )
        event = result.scalar_one()
        # Force loading de tous les attributs avant fermeture session.
        _ = (
            event.id, event.event_type, event.aggregate_type,
            event.aggregate_id, event.payload, event.status,
            event.retry_count, event.error_message, event.created_at,
            event.processed_at, event.next_retry_at,
        )
        db.expunge(event)
        return event


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_worker_processes_pending_event_and_marks_processed(postgres_engine):
    """1 event inséré → 1 passe worker → status='processed', processed_at NOT NULL."""
    event_id = await _insert_event(postgres_engine, event_type="noop.test")

    await process_outbox_batch(postgres_engine)

    event = await _fetch_event(postgres_engine, event_id)
    assert event.status == "processed"
    assert event.processed_at is not None
    assert event.retry_count == 0
    assert event.error_message is None


async def test_worker_skip_locked_allows_concurrent_processing(postgres_engine):
    """2 coroutines concurrent sur 10 events : chaque event traité exactement 1 fois.

    Le verrou row-level ``FOR UPDATE SKIP LOCKED`` garantit qu'un event
    verrouillé par coroutine A est skippé par coroutine B, pas bloqué.
    """
    # Insert 10 events pending.
    event_ids: list[uuid.UUID] = []
    async with AsyncSession(postgres_engine, expire_on_commit=False) as db:
        for _ in range(10):
            e = await write_domain_event(
                db,
                event_type="noop.test",
                aggregate_type="project",
                aggregate_id=uuid.uuid4(),
                payload={"i": 1},
            )
            event_ids.append(e.id)
        await db.commit()

    # 2 coroutines traitent le même backlog en parallèle.
    await asyncio.gather(
        process_outbox_batch(postgres_engine),
        process_outbox_batch(postgres_engine),
    )

    # Chaque event a été traité exactement 1 fois.
    async with AsyncSession(postgres_engine, expire_on_commit=False) as db:
        result = await db.execute(
            text(
                "SELECT status, processed_at, retry_count "
                "FROM domain_events WHERE id = ANY(:ids)"
            ),
            {"ids": event_ids},
        )
        rows = result.all()
    assert len(rows) == 10
    for row in rows:
        assert row.status == "processed"
        assert row.processed_at is not None
        assert row.retry_count == 0


async def test_worker_retry_schedules_next_retry_at_on_handler_exception(
    postgres_engine, monkeypatch
):
    """Handler qui raise → retry_count=1 + next_retry_at ≈ now()+30s."""
    async def _boom(event, db):
        raise RuntimeError("simulated transient DB error")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="boom"),),
    )

    event_id = await _insert_event(postgres_engine, event_type="noop.test")
    before = datetime.now(timezone.utc)
    await process_outbox_batch(postgres_engine)
    after = datetime.now(timezone.utc)

    event = await _fetch_event(postgres_engine, event_id)
    assert event.status == "pending"  # toujours pending, sera repêché
    assert event.retry_count == 1
    assert event.processed_at is None
    assert event.next_retry_at is not None
    assert event.error_message is not None
    assert "RuntimeError" in event.error_message

    # next_retry_at ≈ now() + 30s (tolérance 10s pour latence réseau/CI).
    expected_min = before + timedelta(seconds=20)
    expected_max = after + timedelta(seconds=40)
    assert expected_min <= event.next_retry_at <= expected_max


async def test_worker_marks_failed_after_3_retries(postgres_engine, monkeypatch):
    """3 passes worker avec handler qui raise toujours → status='failed'.

    On force ``next_retry_at = NULL`` entre chaque passe pour que l'event
    soit immédiatement éligible (simulation d'attente backoff écoulée).
    """
    async def _boom(event, db):
        raise RuntimeError("always fails")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="boom"),),
    )

    event_id = await _insert_event(postgres_engine, event_type="noop.test")

    for _ in range(3):
        # Reset next_retry_at pour que l'event soit immédiatement éligible.
        async with AsyncSession(postgres_engine) as db:
            await db.execute(
                text("UPDATE domain_events SET next_retry_at = NULL WHERE id = :id"),
                {"id": event_id},
            )
            await db.commit()
        await process_outbox_batch(postgres_engine)

    event = await _fetch_event(postgres_engine, event_id)
    assert event.status == "failed"
    assert event.retry_count == 3
    assert event.processed_at is not None
    assert event.error_message is not None

    # Une 4ᵉ passe ne repêche pas l'event (sort de l'index / filtre).
    await process_outbox_batch(postgres_engine)
    event_after = await _fetch_event(postgres_engine, event_id)
    assert event_after.status == "failed"
    assert event_after.retry_count == 3  # pas ré-incrémenté


async def test_worker_marks_unknown_handler_fail_fast_without_retry(postgres_engine):
    """event_type absent du registry → status='unknown_handler', retry_count=0."""
    # On insère un event avec un event_type qui n'existe pas dans EVENT_HANDLERS.
    event_id = await _insert_event(postgres_engine, event_type="unknown.foo")

    await process_outbox_batch(postgres_engine)

    event = await _fetch_event(postgres_engine, event_id)
    assert event.status == "unknown_handler"
    assert event.retry_count == 0
    assert event.processed_at is not None
    assert event.error_message is not None
    assert "unknown.foo" in event.error_message


async def test_purge_prefill_drafts_removes_expired_rows(
    postgres_engine, insert_test_user
):
    """3 drafts insérés, 2 expirés, 1 valide → purge en laisse 1."""
    now = datetime.now(timezone.utc)
    expired_1 = uuid.uuid4()
    expired_2 = uuid.uuid4()
    valid_id = uuid.uuid4()

    async with AsyncSession(postgres_engine) as db:
        for pid, expires_at in [
            (expired_1, now - timedelta(hours=2)),
            (expired_2, now - timedelta(minutes=1)),
            (valid_id, now + timedelta(hours=1)),
        ]:
            await db.execute(
                text(
                    "INSERT INTO prefill_drafts (id, user_id, payload, expires_at) "
                    "VALUES (:id, :uid, :payload, :exp)"
                ),
                {
                    "id": pid,
                    "uid": insert_test_user,
                    "payload": '{"k":"v"}',
                    "exp": expires_at,
                },
            )
        await db.commit()

    await purge_expired_prefill_drafts(postgres_engine)

    async with AsyncSession(postgres_engine) as db:
        result = await db.execute(text("SELECT COUNT(*) FROM prefill_drafts"))
        remaining = result.scalar_one()
    assert remaining == 1

    # Seul le draft valide a survécu.
    async with AsyncSession(postgres_engine) as db:
        result = await db.execute(
            text("SELECT id FROM prefill_drafts")
        )
        remaining_ids = [row[0] for row in result.all()]
    assert remaining_ids == [valid_id]
