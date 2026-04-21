"""Tests Story 10.13 AC10 — LLMProvider abstraction."""

from __future__ import annotations

import pytest

from app.core.llm import LLMError, LLMProvider, get_llm_provider
from app.core.llm.provider import (
    AnthropicLLMProvider,
    OpenRouterLLMProvider,
    _reset_llm_provider_cache,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    _reset_llm_provider_cache()
    yield
    _reset_llm_provider_cache()


def test_llm_provider_abc_cannot_be_instantiated():
    with pytest.raises(TypeError, match="abstract"):
        LLMProvider()  # type: ignore[abstract]


def test_anthropic_provider_default_model():
    provider = AnthropicLLMProvider()
    assert provider.name == "anthropic_direct"
    assert "claude" in provider.model.lower()


def test_openrouter_provider_name():
    provider = OpenRouterLLMProvider(model="minimax/minimax-m2.7")
    assert provider.name == "openrouter"
    assert provider.model == "minimax/minimax-m2.7"


def test_get_llm_provider_default_openrouter(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "openrouter")
    _reset_llm_provider_cache()
    provider = get_llm_provider()
    assert isinstance(provider, OpenRouterLLMProvider)


def test_get_llm_provider_anthropic_when_configured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "anthropic_direct")
    _reset_llm_provider_cache()
    provider = get_llm_provider()
    assert isinstance(provider, AnthropicLLMProvider)


def test_get_llm_provider_raises_on_unknown(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "aws_bedrock")
    _reset_llm_provider_cache()
    with pytest.raises(LLMError, match="Unknown llm_provider"):
        get_llm_provider()


def test_get_llm_provider_is_cached(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "openrouter")
    _reset_llm_provider_cache()
    first = get_llm_provider()
    second = get_llm_provider()
    assert first is second


# ---------------------------------------------------------------------------
# HIGH-5 patch post-review 2026-04-21 — shim get_llm() vraiment tenu
# ---------------------------------------------------------------------------


def test_get_llm_shim_delegates_to_provider(monkeypatch):
    """``graph/nodes.py::get_llm()`` doit déléguer à ``get_llm_provider()``."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-test")
    _reset_llm_provider_cache()

    from app.graph.nodes import get_llm

    llm = get_llm()
    # L'instance retournée doit provenir de get_llm_provider().get_chat_llm()
    # — pour OpenRouter : ChatOpenAI avec streaming=True.
    from langchain_openai import ChatOpenAI

    assert isinstance(llm, ChatOpenAI)
    assert getattr(llm, "streaming", False) is True


def test_get_llm_shim_anthropic_when_configured(monkeypatch):
    """AC10 — switch ``llm_provider=anthropic_direct`` propage au shim."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "anthropic_direct")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-" + "x" * 60)
    _reset_llm_provider_cache()

    from app.graph.nodes import get_llm

    llm = get_llm()
    from langchain_anthropic import ChatAnthropic

    assert isinstance(llm, ChatAnthropic)


def test_provider_streaming_toggle_isolated_instances():
    """streaming=True vs False → 2 instances séparées (pas de pollution)."""
    provider = OpenRouterLLMProvider(model="test-model")
    llm_streaming = provider.get_chat_llm(streaming=True)
    llm_batch = provider.get_chat_llm(streaming=False)
    assert llm_streaming is not llm_batch
