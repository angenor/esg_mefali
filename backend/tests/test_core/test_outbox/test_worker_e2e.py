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


async def test_worker_marks_failed_after_max_retries(postgres_engine, monkeypatch):
    """4 passes worker avec handler qui raise toujours → status='failed'.

    §D11 architecture : 3 retries (BACKOFF [30,120,600]s) + la tentative
    initiale = 4 tentatives totales. Bascule en failed quand retry_count
    dépasse MAX_RETRIES (4ᵉ échec).

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

    # 4 passes : attempt 1 (initiale) + retries 1/2/3 → failed sur attempt 4.
    for _ in range(4):
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
    assert event.retry_count == 4  # 4 échecs enregistrés
    assert event.processed_at is not None
    assert event.error_message is not None

    # Une 5ᵉ passe ne repêche pas l'event (sort du filtre processed_at IS NULL).
    await process_outbox_batch(postgres_engine)
    event_after = await _fetch_event(postgres_engine, event_id)
    assert event_after.status == "failed"
    assert event_after.retry_count == 4  # pas ré-incrémenté


async def test_worker_uses_full_backoff_schedule_30_120_600(postgres_engine, monkeypatch):
    """Les 3 entrées BACKOFF_SCHEDULE sont utilisées successivement.

    MEDIUM-10.10-1 correctif : BACKOFF_SCHEDULE[0]=30s (retry 1),
    BACKOFF_SCHEDULE[1]=120s (retry 2), BACKOFF_SCHEDULE[2]=600s (retry 3).
    """
    async def _boom(event, db):
        raise RuntimeError("transient")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="boom"),),
    )

    event_id = await _insert_event(postgres_engine, event_type="noop.test")

    expected_delays_s = [30, 120, 600]
    for expected_delay in expected_delays_s:
        async with AsyncSession(postgres_engine) as db:
            await db.execute(
                text("UPDATE domain_events SET next_retry_at = NULL WHERE id = :id"),
                {"id": event_id},
            )
            await db.commit()

        before = datetime.now(timezone.utc)
        await process_outbox_batch(postgres_engine)
        after = datetime.now(timezone.utc)

        event = await _fetch_event(postgres_engine, event_id)
        assert event.status == "pending"  # toujours en retry
        assert event.next_retry_at is not None

        lower_bound = before + timedelta(seconds=expected_delay - 10)
        upper_bound = after + timedelta(seconds=expected_delay + 10)
        assert lower_bound <= event.next_retry_at <= upper_bound, (
            f"retry {event.retry_count} : next_retry_at {event.next_retry_at} "
            f"hors fenêtre [{lower_bound}, {upper_bound}] pour delay={expected_delay}s"
        )


async def test_worker_savepoint_isolates_handler_sql_failure(postgres_engine, monkeypatch):
    """HIGH-10.10-1 : handler qui écrit du SQL puis raise → autres events du
    batch traités normalement (pas de PendingRollbackError).

    Scénario :
        - 2 events A, B dans le batch (même event_type).
        - Handler A : INSERT users puis raise RuntimeError.
        - Handler B : succès.
    Attendu :
        - Event A : status='pending', retry_count=1, next_retry_at fixé.
        - Event B : status='processed', processed_at fixé.
        - Table users : 0 ligne (savepoint A rollback).
    """
    calls: list[str] = []

    async def _handler(event, db):
        calls.append(str(event.aggregate_id))
        if event.payload.get("fail"):
            # SQL partiel qui devrait être rollback par le savepoint.
            await db.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password) "
                    "VALUES (:id, :email, :pwd)"
                ),
                {"id": uuid.uuid4(), "email": f"leaked-{uuid.uuid4()}@test", "pwd": "x"},
            )
            raise RuntimeError("handler failed after partial SQL")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_handler, description="savepoint test"),),
    )

    # Insert 2 events : A (fail) + B (ok). Ordre créé_at → A avant B.
    async with AsyncSession(postgres_engine, expire_on_commit=False) as db:
        event_a = await write_domain_event(
            db,
            event_type="noop.test",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={"fail": True},
        )
        event_b = await write_domain_event(
            db,
            event_type="noop.test",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={"fail": False},
        )
        event_a_id = event_a.id
        event_b_id = event_b.id
        await db.commit()

    await process_outbox_batch(postgres_engine)

    # Les 2 handlers ont tourné (pas de PendingRollback qui couperait la boucle).
    assert len(calls) == 2

    # Event A : retry scheduled.
    event_a_after = await _fetch_event(postgres_engine, event_a_id)
    assert event_a_after.status == "pending"
    assert event_a_after.retry_count == 1
    assert event_a_after.next_retry_at is not None
    assert event_a_after.error_message is not None
    assert "RuntimeError" in event_a_after.error_message

    # Event B : processed.
    event_b_after = await _fetch_event(postgres_engine, event_b_id)
    assert event_b_after.status == "processed"
    assert event_b_after.processed_at is not None

    # INSERT du handler A rollback par le savepoint : 0 user "leaked-" en BDD.
    async with AsyncSession(postgres_engine) as db:
        leaked = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE email LIKE 'leaked-%@test'")
        )
        assert leaked.scalar_one() == 0


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
