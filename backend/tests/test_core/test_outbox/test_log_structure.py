"""Tests unit — structure log JSON Outbox (Story 10.10 AC5)."""

from __future__ import annotations

import logging
import uuid

import pytest

from app.core.outbox.worker import _process_single_event
from app.models.domain_event import DomainEvent

pytestmark = pytest.mark.unit


def _make_event(event_type: str = "noop.test", retry_count: int = 0) -> DomainEvent:
    return DomainEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        aggregate_type="project",
        aggregate_id=uuid.uuid4(),
        payload={"company_id": "abc-123", "name": "Mefali SARL"},
        status="pending",
        retry_count=retry_count,
    )


_REQUIRED_EXTRA_KEYS = frozenset({
    "metric",
    "event_id",
    "event_type",
    "aggregate_type",
    "aggregate_id",
    "attempt",
    "status",
    "duration_ms",
    "payload_keys",
    "error_message",
})


async def test_log_structure_contains_all_expected_keys_for_processed(caplog):
    """Log 'outbox_event_processed' porte tous les champs extra attendus (NFR37)."""
    caplog.set_level(logging.INFO, logger="app.core.outbox.worker")
    event = _make_event()
    await _process_single_event(db=None, event=event)  # type: ignore[arg-type]

    processed_records = [
        r for r in caplog.records
        if r.name == "app.core.outbox.worker"
        and getattr(r, "metric", None) == "outbox_event_processed"
    ]
    assert len(processed_records) == 1
    record = processed_records[0]
    assert record.status == "processed"
    assert record.event_type == "noop.test"
    assert record.attempt == 1
    assert isinstance(record.duration_ms, int)
    assert record.duration_ms >= 0
    assert set(record.payload_keys) == {"company_id", "name"}
    assert record.error_message is None

    for key in _REQUIRED_EXTRA_KEYS:
        assert hasattr(record, key), f"clé manquante dans log extra: {key}"


async def test_log_structure_unknown_handler(caplog):
    """Log 'outbox_event_unknown_handler' marqué ERROR + metric dédié."""
    caplog.set_level(logging.INFO, logger="app.core.outbox.worker")
    event = _make_event(event_type="unregistered.event")
    await _process_single_event(db=None, event=event)  # type: ignore[arg-type]

    records = [
        r for r in caplog.records
        if getattr(r, "metric", None) == "outbox_event_unknown_handler"
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.ERROR
    assert records[0].status == "unknown_handler"
    assert records[0].error_message is not None
    assert "unregistered.event" in records[0].error_message


async def test_log_does_not_contain_payload_values(caplog):
    """NFR18 — le payload entier n'est jamais dans le log (seulement payload_keys)."""
    caplog.set_level(logging.INFO, logger="app.core.outbox.worker")
    event = _make_event()
    await _process_single_event(db=None, event=event)  # type: ignore[arg-type]

    for record in caplog.records:
        # Aucune valeur PII dans les attributs du record.
        assert not hasattr(record, "payload")
        assert getattr(record, "payload_keys", None) is not None
        # Valeurs NON présentes : "Mefali SARL" (name), "abc-123" (id).
        assert "Mefali SARL" not in record.getMessage()
