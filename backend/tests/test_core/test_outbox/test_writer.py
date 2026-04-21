"""Tests unit — writer Outbox (Story 10.10 AC1)."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox.writer import write_domain_event
from app.models.domain_event import DomainEvent

pytestmark = pytest.mark.unit


@pytest.fixture
async def db() -> AsyncSession:
    from tests.conftest import test_session_factory

    async with test_session_factory() as session:
        yield session


async def test_write_domain_event_inserts_row_in_current_transaction(db):
    """Le writer ajoute la ligne dans la transaction courante, sans commit interne."""
    aggregate_id = uuid.uuid4()
    event = await write_domain_event(
        db,
        event_type="project.created",
        aggregate_type="project",
        aggregate_id=aggregate_id,
        payload={"company_id": str(uuid.uuid4()), "name": "Mefali SARL"},
    )

    # Après flush, la ligne est visible dans la session mais non commitée.
    assert event.id is not None
    assert event.status == "pending"
    assert event.retry_count == 0
    assert event.processed_at is None
    assert event.next_retry_at is None

    # La ligne est récupérable via SELECT dans la même session.
    result = await db.execute(select(DomainEvent).where(DomainEvent.id == event.id))
    fetched = result.scalar_one()
    assert fetched.event_type == "project.created"
    assert fetched.aggregate_id == aggregate_id

    # Rollback propage à l'event (pas de commit interne du writer).
    await db.rollback()
    result2 = await db.execute(select(DomainEvent).where(DomainEvent.id == event.id))
    assert result2.scalar_one_or_none() is None


async def test_write_domain_event_validates_event_type_format(db):
    """event_type hors regex → ValueError fail-fast."""
    with pytest.raises(ValueError, match="Invalid event_type"):
        await write_domain_event(
            db,
            event_type="BadFormat",  # pas snake_case.snake_case
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={"foo": "bar"},
        )

    with pytest.raises(ValueError, match="Invalid event_type"):
        await write_domain_event(
            db,
            event_type="no_dot",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={},
        )

    with pytest.raises(ValueError, match="Invalid event_type"):
        await write_domain_event(
            db,
            event_type="Dots.Mixed",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={},
        )


async def test_write_domain_event_validates_payload_json_serializable(db):
    """payload non JSON-sérialisable → ValueError explicite."""
    # datetime naïve (pas d'isoformat explicite côté caller) → non sérialisable.
    with pytest.raises(ValueError, match="not JSON-serializable"):
        await write_domain_event(
            db,
            event_type="project.created",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={"dt": datetime.now()},
        )

    # set → non sérialisable.
    with pytest.raises(ValueError, match="not JSON-serializable"):
        await write_domain_event(
            db,
            event_type="project.created",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload={"items": {"a", "b"}},
        )

    # payload pas un dict (JSON object) → ValueError.
    with pytest.raises(ValueError, match="payload must be a dict"):
        await write_domain_event(
            db,
            event_type="project.created",
            aggregate_type="project",
            aggregate_id=uuid.uuid4(),
            payload=[1, 2, 3],  # type: ignore[arg-type]
        )
