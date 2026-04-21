"""Tests unit — registry handlers (Story 10.10 AC3)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox.handlers import (
    EVENT_HANDLERS,
    HandlerEntry,
    HandlerResult,
    _validate_unique_event_types,
    dispatch_event,
)
from app.models.domain_event import DomainEvent

pytestmark = pytest.mark.unit


def _make_event(event_type: str) -> DomainEvent:
    return DomainEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        aggregate_type="project",
        aggregate_id=uuid.uuid4(),
        payload={},
        status="pending",
        retry_count=0,
    )


def test_event_handlers_registry_is_frozen_tuple():
    """EVENT_HANDLERS est un tuple immutable (pattern CCC-9 Story 10.8)."""
    assert isinstance(EVENT_HANDLERS, tuple)
    assert type(EVENT_HANDLERS) is tuple  # pas une sous-classe exotique

    # Les tuples n'ont pas .append (AttributeError levée à l'évaluation).
    with pytest.raises(AttributeError):
        EVENT_HANDLERS.append(  # type: ignore[attr-defined]
            HandlerEntry(event_type="foo.bar", handler=lambda e, d: None, description="")
        )

    # Toutes les entrées sont frozen.
    for entry in EVENT_HANDLERS:
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError hérite
            entry.event_type = "mutated"  # type: ignore[misc]


def test_event_handlers_have_unique_event_types():
    """Pas de doublon dans le registre — validation passe à l'import."""
    event_types = [entry.event_type for entry in EVENT_HANDLERS]
    assert len(event_types) == len(set(event_types))

    # Re-appel explicite du validator : ne raise pas.
    _validate_unique_event_types()


def test_validate_unique_event_types_detects_duplicates(monkeypatch):
    """Un tuple patché avec doublon → RuntimeError fail-fast."""
    from app.core.outbox import handlers as handlers_mod

    duplicated = (
        HandlerEntry(event_type="noop.test", handler=lambda e, d: None, description="a"),
        HandlerEntry(event_type="noop.test", handler=lambda e, d: None, description="b"),
    )
    monkeypatch.setattr(handlers_mod, "EVENT_HANDLERS", duplicated)
    with pytest.raises(RuntimeError, match="Duplicate event_type"):
        handlers_mod._validate_unique_event_types()


async def test_dispatch_event_returns_unknown_handler_for_unregistered_type():
    """event_type absent du registry → status='unknown_handler' fail-fast sans retry."""
    event = _make_event("unregistered.foo")
    result = await dispatch_event(event, db=None)  # type: ignore[arg-type]
    assert isinstance(result, HandlerResult)
    assert result.status == "unknown_handler"
    assert result.error_message is not None
    assert "unregistered.foo" in result.error_message


async def test_dispatch_event_handler_exception_returns_retry(monkeypatch):
    """Un handler qui raise Exception → status='retry' avec error_message typé."""
    from app.core.outbox import handlers as handlers_mod

    async def _boom(event: DomainEvent, db: AsyncSession) -> None:  # type: ignore[arg-type]
        raise RuntimeError("boom connection lost")

    patched = (
        HandlerEntry(event_type="noop.test", handler=_boom, description="test"),
    )
    monkeypatch.setattr(handlers_mod, "EVENT_HANDLERS", patched)

    event = _make_event("noop.test")
    result = await handlers_mod.dispatch_event(event, db=None)  # type: ignore[arg-type]
    assert result.status == "retry"
    assert result.error_message is not None
    assert "RuntimeError" in result.error_message
    assert "boom" in result.error_message


async def test_dispatch_event_noop_handler_returns_processed():
    """Handler noop (livré dummy) → status='processed'."""
    event = _make_event("noop.test")
    result = await dispatch_event(event, db=None)  # type: ignore[arg-type]
    assert result.status == "processed"
    assert result.error_message is None
