"""Tests unit — logique retry & savepoint worker (Story 10.10 patches post-review).

Couvre :
    - MEDIUM-10.10-1 : BACKOFF_SCHEDULE[0/1/2]=(30,120,600) tous utilisés.
    - HIGH-10.10-1 : `_SavepointRollbackSignal` capturé proprement.

Tests SQLite fast-path (pas de marqueur `postgres`) — SAVEPOINT supporté
nativement par SQLite.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox import handlers as handlers_mod
from app.core.outbox.handlers import HandlerEntry
from app.core.outbox.worker import (
    BACKOFF_SCHEDULE,
    MAX_RETRIES,
    _process_single_event,
)
from app.models.domain_event import DomainEvent

pytestmark = pytest.mark.unit


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    from tests.conftest import test_session_factory

    async with test_session_factory() as session:
        async with session.begin():
            yield session


def _make_event(retry_count: int = 0) -> DomainEvent:
    return DomainEvent(
        id=uuid.uuid4(),
        event_type="noop.test",
        aggregate_type="project",
        aggregate_id=uuid.uuid4(),
        payload={"k": "v"},
        status="pending",
        retry_count=retry_count,
    )


def test_backoff_schedule_invariant():
    """MEDIUM-10.10-1 invariant : len(BACKOFF_SCHEDULE) == MAX_RETRIES."""
    assert len(BACKOFF_SCHEDULE) == MAX_RETRIES
    assert BACKOFF_SCHEDULE == (30, 120, 600)
    assert MAX_RETRIES == 3


@pytest.mark.parametrize(
    ("retry_count_before", "expected_delay_s"),
    [
        (0, 30),   # 1er échec → BACKOFF[0]=30s
        (1, 120),  # 2ᵉ échec → BACKOFF[1]=120s
        (2, 600),  # 3ᵉ échec → BACKOFF[2]=600s (MEDIUM-10.10-1 : plus dead code)
    ],
)
async def test_process_single_event_uses_full_backoff_schedule(
    db, monkeypatch, retry_count_before: int, expected_delay_s: int
):
    """Les 3 delays (30, 120, 600) sont atteints pour retry_count 0→1, 1→2, 2→3."""
    async def _boom(event, db):
        raise RuntimeError("flaky")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="test"),),
    )

    event = _make_event(retry_count=retry_count_before)
    before = datetime.now(timezone.utc)
    await _process_single_event(db, event)
    after = datetime.now(timezone.utc)

    # Post-process : retry_count incrémenté, next_retry_at dans la fenêtre attendue.
    assert event.retry_count == retry_count_before + 1
    assert event.status == "pending"  # pas encore failed
    assert event.next_retry_at is not None
    assert event.error_message is not None

    lower = before.timestamp() + expected_delay_s - 5
    upper = after.timestamp() + expected_delay_s + 5
    assert lower <= event.next_retry_at.timestamp() <= upper


async def test_process_single_event_marks_failed_when_retry_count_exceeds_max(
    db, monkeypatch
):
    """MEDIUM-10.10-1 : retry_count passe de MAX_RETRIES à MAX_RETRIES+1 → failed."""
    async def _boom(event, db):
        raise RuntimeError("always fails")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="test"),),
    )

    # Event qui a déjà épuisé ses 3 retries (retry_count=3 = MAX_RETRIES).
    event = _make_event(retry_count=MAX_RETRIES)
    await _process_single_event(db, event)

    assert event.retry_count == MAX_RETRIES + 1  # 4
    assert event.status == "failed"
    assert event.processed_at is not None
    assert event.error_message is not None


async def test_savepoint_rollback_signal_not_propagated_outside(db, monkeypatch):
    """HIGH-10.10-1 : `_SavepointRollbackSignal` est capturé, pas propagé.

    Un handler qui raise → result.status='retry' → savepoint rollback →
    `_process_single_event` termine sans exception externe, et l'event est
    mis à jour (retry_count, next_retry_at) malgré le rollback du savepoint.
    """
    async def _boom(event, db):
        raise ValueError("handler explicit failure")

    monkeypatch.setattr(
        handlers_mod,
        "EVENT_HANDLERS",
        (HandlerEntry(event_type="noop.test", handler=_boom, description="test"),),
    )

    event = _make_event(retry_count=0)
    # Ne doit PAS lever — _SavepointRollbackSignal est capturé en interne.
    await _process_single_event(db, event)

    # Les updates sur event ont bien été appliqués (hors savepoint).
    assert event.retry_count == 1
    assert event.status == "pending"
    assert event.next_retry_at is not None
    assert event.error_message is not None
    assert "ValueError" in event.error_message
