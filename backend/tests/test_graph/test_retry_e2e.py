"""Tests E2E retry + circuit breaker (Story 9.7 T15 — AC2, AC5).

Valide le comportement bout-en-bout du wrapper ``with_retry`` :
- Retry transient + journalisation des 2 lignes (error → retry_success).
- Circuit breaker après 10 erreurs 5xx, fenêtre 60 s, recovery half-open.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool as tool_decorator
from sqlalchemy import select

from app.graph.tools import common as common_mod
from app.graph.tools.common import (
    _breaker,
    _reset_breaker_state_for_tests,
    with_retry,
)
from app.models.tool_call_log import ToolCallLog


@pytest.fixture
def reset_breaker():
    _reset_breaker_state_for_tests()
    yield
    _reset_breaker_state_for_tests()


@pytest.fixture
def mock_sleep(monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(common_mod.asyncio, "sleep", sleep_mock)
    return sleep_mock


@pytest.fixture
async def e2e_config(db_session):
    from app.models.conversation import Conversation
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"test-e2e-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="test",
        full_name="E2E User",
        company_name="E2E Co",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=user.id,
        title="E2E conv",
    )
    db_session.add(conversation)
    await db_session.flush()

    return {
        "configurable": {
            "db": db_session,
            "user_id": user.id,
            "conversation_id": conversation.id,
            "active_module": "chat",
        },
    }


# ---------------------------------------------------------------------------
# AC2 — retry transient puis succès
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_on_transient_then_success(
    e2e_config, db_session, reset_breaker, mock_sleep
):
    calls = {"n": 0}

    @tool_decorator
    async def e2e_retry_tool(config: RunnableConfig = None) -> str:
        """Échoue au 1er essai puis réussit."""
        calls["n"] += 1
        if calls["n"] == 1:
            raise asyncio.TimeoutError("read timeout")
        return "OK_AFTER_RETRY"

    wrapped = with_retry(e2e_retry_tool, max_retries=2, node_name="chat")
    result = await wrapped.ainvoke({}, config=e2e_config)
    await db_session.flush()

    assert result == "OK_AFTER_RETRY"
    assert calls["n"] == 2

    # Intervalle 1 s avant la 2e tentative
    assert [c.args[0] for c in mock_sleep.await_args_list] == [1.0]

    rows = await db_session.execute(
        select(ToolCallLog).where(ToolCallLog.tool_name == "e2e_retry_tool")
    )
    logs = list(rows.scalars().all())
    assert len(logs) == 2
    statuses = [log.status for log in logs]
    assert "error" in statuses
    assert "retry_success" in statuses

    retry_success_log = next(log for log in logs if log.status == "retry_success")
    assert retry_success_log.retry_count == 1
    error_log = next(log for log in logs if log.status == "error")
    assert error_log.retry_count == 0
    assert error_log.error_message is not None


# ---------------------------------------------------------------------------
# AC5 — circuit breaker après 10 échecs 5xx consécutifs
# ---------------------------------------------------------------------------


class _Fake503Error(Exception):
    """Simule une erreur LLM 5xx."""

    status_code = 503


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_10_failures(
    e2e_config, db_session, reset_breaker, mock_sleep, monkeypatch
):
    """10 échecs 5xx ouvrent le breaker ; 11e bloquée ; recovery après 60 s."""
    call_count = {"n": 0}

    @tool_decorator
    async def cb_tool(config: RunnableConfig = None) -> str:
        """Lève toujours 503."""
        call_count["n"] += 1
        raise _Fake503Error("service unavailable")

    # max_retries=0 → 1 appel par invocation (accélère le test)
    wrapped = with_retry(cb_tool, max_retries=0, backoff=[], node_name="chat")

    # 10 invocations qui échouent → breaker ouvert après la 10e
    for _ in range(10):
        result = await wrapped.ainvoke({}, config=e2e_config)
        assert "Erreur" in result

    assert call_count["n"] == 10
    assert await _breaker.should_block("cb_tool", "chat") is True

    # 11e invocation : circuit breaker ouvert, cb_tool NON appelé
    result = await wrapped.ainvoke({}, config=e2e_config)
    assert result == "Erreur : circuit breaker ouvert"
    assert call_count["n"] == 10  # pas d'incrément

    # Vérifier qu'une ligne status="circuit_open" a été insérée
    await db_session.flush()
    rows = await db_session.execute(
        select(ToolCallLog).where(
            ToolCallLog.tool_name == "cb_tool",
            ToolCallLog.status == "circuit_open",
        )
    )
    circuit_logs = list(rows.scalars().all())
    assert len(circuit_logs) >= 1

    # Fast-forward au-delà de la fenêtre 60 s
    real_now = _breaker._now
    base_time = real_now()
    monkeypatch.setattr(_breaker, "_now", lambda: base_time + 61.0)

    # 12e invocation après recovery : cb_tool est rappelé (et échoue à nouveau)
    call_count_before = call_count["n"]
    result = await wrapped.ainvoke({}, config=e2e_config)
    assert call_count["n"] == call_count_before + 1, (
        "Après 60 s, la fonction doit être rappelée (half-open)"
    )
