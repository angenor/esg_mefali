"""Tests unitaires des primitives étendues dans common.py (Story 9.7).

Couvre :
- `is_transient_error` (≥ 8 cas, AC2/AC3)
- `with_retry` backoff exponentiel (≥ 5 cas, AC2)
- `_CircuitBreakerState` (≥ 6 cas, AC5)

Monkeypatch systématique de `asyncio.sleep` pour garder les tests < 1 s.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.graph.tools import common as common_mod
from app.graph.tools.common import (
    _CircuitBreakerState,
    _breaker,
    _reset_breaker_state_for_tests,
    is_transient_error,
    with_retry,
)


# ---------------------------------------------------------------------------
# TestIsTransientError — ≥ 8 cas (5 transients acceptés + 3 non-transients)
# ---------------------------------------------------------------------------


class TestIsTransientError:
    """Couvre la classification transient / non-transient (AC2, AC3)."""

    def test_asyncio_timeout_is_transient(self):
        assert is_transient_error(asyncio.TimeoutError()) is True

    def test_builtin_timeout_is_transient(self):
        assert is_transient_error(TimeoutError("read timeout")) is True

    def test_connection_error_is_transient(self):
        assert is_transient_error(ConnectionError("broken pipe")) is True

    def test_status_code_503_is_transient(self):
        class FakeAPIError(Exception):
            status_code = 503

        assert is_transient_error(FakeAPIError("service unavailable")) is True

    def test_status_code_429_is_transient(self):
        class RateLimit(Exception):
            status_code = 429

        assert is_transient_error(RateLimit("too many")) is True

    def test_response_nested_status_is_transient(self):
        class Resp:
            status_code = 502

        class HTTPErr(Exception):
            response = Resp()

        assert is_transient_error(HTTPErr("bad gateway")) is True

    def test_value_error_is_not_transient(self):
        assert is_transient_error(ValueError("bad input")) is False

    def test_key_error_is_not_transient(self):
        assert is_transient_error(KeyError("missing")) is False

    def test_permission_error_is_not_transient(self):
        assert is_transient_error(PermissionError("RLS deny")) is False

    def test_status_code_400_not_transient(self):
        class BadRequest(Exception):
            status_code = 400

        assert is_transient_error(BadRequest("validation failed")) is False


# ---------------------------------------------------------------------------
# TestWithRetryBackoff — ≥ 5 cas (monkeypatch asyncio.sleep)
# ---------------------------------------------------------------------------


class TestWithRetryBackoff:
    """Couvre les intervalles de backoff exponentiel (AC2)."""

    @pytest.fixture(autouse=True)
    def _reset_breaker(self):
        _reset_breaker_state_for_tests()
        yield
        _reset_breaker_state_for_tests()

    @pytest.fixture
    def mock_sleep(self, monkeypatch):
        sleep_mock = AsyncMock()
        monkeypatch.setattr(common_mod.asyncio, "sleep", sleep_mock)
        return sleep_mock

    @pytest.mark.asyncio
    async def test_success_first_attempt_no_sleep(self, mock_sleep):
        async def tool():
            return "ok"

        wrapped = with_retry(tool, node_name="t")
        result = await wrapped()

        assert result == "ok"
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_after_one_retry_sleeps_1s(self, mock_sleep):
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise asyncio.TimeoutError("first")
            return "recovered"

        wrapped = with_retry(flaky, max_retries=2, node_name="t")
        result = await wrapped()

        assert result == "recovered"
        assert calls["n"] == 2
        mock_sleep.assert_awaited_once_with(1.0)

    @pytest.mark.asyncio
    async def test_success_after_two_retries_sleeps_1_and_3(self, mock_sleep):
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise asyncio.TimeoutError("retry me")
            return "recovered"

        wrapped = with_retry(flaky, max_retries=2, node_name="t")
        result = await wrapped()

        assert result == "recovered"
        assert calls["n"] == 3
        assert [c.args[0] for c in mock_sleep.await_args_list] == [1.0, 3.0]

    @pytest.mark.asyncio
    async def test_all_retries_fail_on_transient_final_error(self, mock_sleep):
        async def always_timeout():
            raise asyncio.TimeoutError("timeout")

        wrapped = with_retry(always_timeout, max_retries=2, node_name="t")
        result = await wrapped()

        assert "Erreur" in result
        assert [c.args[0] for c in mock_sleep.await_args_list] == [1.0, 3.0]

    @pytest.mark.asyncio
    async def test_non_transient_no_sleep_immediate_return(self, mock_sleep):
        async def bad_value():
            raise ValueError("invalid")

        wrapped = with_retry(bad_value, max_retries=2, node_name="t")
        result = await wrapped()

        assert result.startswith("Erreur")
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_backoff_used(self, mock_sleep):
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise asyncio.TimeoutError("retry")
            return "ok"

        wrapped = with_retry(flaky, max_retries=2, node_name="t", backoff=[0.5, 1.5, 4.5])
        result = await wrapped()

        assert result == "ok"
        assert [c.args[0] for c in mock_sleep.await_args_list] == [0.5, 1.5]

    @pytest.mark.asyncio
    async def test_sentinel_attribute_posed(self):
        async def tool():
            return "ok"

        wrapped = with_retry(tool, node_name="t")
        assert getattr(wrapped, "_is_wrapped_by_with_retry", False) is True

    def test_backoff_too_short_raises(self):
        async def tool():
            return "ok"

        with pytest.raises(ValueError, match="backoff doit contenir"):
            with_retry(tool, max_retries=3, backoff=[1.0, 2.0])


# ---------------------------------------------------------------------------
# TestCircuitBreakerState — ≥ 6 cas
# ---------------------------------------------------------------------------


class TestCircuitBreakerState:
    """Couvre le circuit breaker (AC5)."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        _reset_breaker_state_for_tests()
        yield
        _reset_breaker_state_for_tests()

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        breaker = _CircuitBreakerState()
        assert await breaker.should_block("t", "n") is False

        for _ in range(breaker.THRESHOLD):
            await breaker.record_failure("t", "n", is_llm_5xx=True)

        assert await breaker.should_block("t", "n") is True

    @pytest.mark.asyncio
    async def test_window_60s_closes_half_open(self, monkeypatch):
        breaker = _CircuitBreakerState()

        fake_time = [0.0]

        def _now() -> float:
            return fake_time[0]

        monkeypatch.setattr(breaker, "_now", _now)

        for _ in range(breaker.THRESHOLD):
            await breaker.record_failure("t", "n", is_llm_5xx=True)

        assert await breaker.should_block("t", "n") is True

        fake_time[0] = breaker.WINDOW_S + 1.0
        assert await breaker.should_block("t", "n") is False

    @pytest.mark.asyncio
    async def test_counter_per_key(self):
        breaker = _CircuitBreakerState()

        for _ in range(5):
            await breaker.record_failure("tool_a", "node_x", is_llm_5xx=True)
        for _ in range(5):
            await breaker.record_failure("tool_b", "node_x", is_llm_5xx=True)

        assert await breaker.should_block("tool_a", "node_x") is False
        assert await breaker.should_block("tool_b", "node_x") is False

        for _ in range(breaker.THRESHOLD):
            await breaker.record_failure("tool_a", "node_x", is_llm_5xx=True)

        assert await breaker.should_block("tool_a", "node_x") is True
        assert await breaker.should_block("tool_b", "node_x") is False

    @pytest.mark.asyncio
    async def test_success_resets_counter(self):
        breaker = _CircuitBreakerState()

        for _ in range(5):
            await breaker.record_failure("t", "n", is_llm_5xx=True)
        await breaker.record_success("t", "n")

        for _ in range(breaker.THRESHOLD - 1):
            await breaker.record_failure("t", "n", is_llm_5xx=True)

        assert await breaker.should_block("t", "n") is False

    @pytest.mark.asyncio
    async def test_ignores_non_5xx_failures(self):
        breaker = _CircuitBreakerState()

        for _ in range(breaker.THRESHOLD * 2):
            await breaker.record_failure("t", "n", is_llm_5xx=False)

        assert await breaker.should_block("t", "n") is False

    @pytest.mark.asyncio
    async def test_singleton_breaker_shared(self):
        assert isinstance(_breaker, _CircuitBreakerState)
        _reset_breaker_state_for_tests()
        assert await _breaker.should_block("anything", "anywhere") is False
