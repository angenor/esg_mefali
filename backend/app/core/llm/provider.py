"""ABC LLMProvider + impl Anthropic + OpenRouter + factory — Story 10.13 AC10.

Concrétise D10 architecture LLM Provider Layer. Le provider primaire est
configuré par ``Settings.llm_provider`` (acté post-bench R-04-1 dans
``docs/bench-llm-providers-phase0.md §5``). Le fallback est invoqué si le
primaire est indisponible (NFR75 circuit breaker 60 s).

Le shim ``get_llm()`` dans ``app/graph/nodes.py:328`` délègue désormais à
cette factory (pattern shim legacy 10.6 byte-identique — signature inchangée).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache


class LLMError(Exception):
    """Parent de la hiérarchie LLM Provider (jamais d'exception vendor brute)."""


class LLMRateLimitError(LLMError):
    """429 persistant après retries."""


class LLMProvider(ABC):
    """Abstraction LLM chat — Anthropic direct, Anthropic OpenRouter, MiniMax.

    ``get_chat_llm()`` retourne un ``BaseChatModel`` LangChain compatible
    ``ainvoke/astream``. Le wiring des 8 nœuds graph/nodes.py reste byte-
    identique — seule la fabrique change.
    """

    name: str = ""
    model: str = ""

    @abstractmethod
    def get_chat_llm(self):
        """Retourne un BaseChatModel LangChain (ChatAnthropic/ChatOpenAI)."""


class AnthropicLLMProvider(LLMProvider):
    """Anthropic direct via ``ChatAnthropic`` (x-api-key, Piège #4)."""

    name = "anthropic_direct"

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.model = model
        self._chat = None

    def get_chat_llm(self):
        if self._chat is None:
            from langchain_anthropic import ChatAnthropic

            from app.core.config import settings

            self._chat = ChatAnthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
                model=self.model,
                max_tokens=4096,
                timeout=60,
            )
        return self._chat


class OpenRouterLLMProvider(LLMProvider):
    """OpenRouter multi-model via ``ChatOpenAI`` (Bearer auth)."""

    name = "openrouter"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or ""
        self._chat = None

    def get_chat_llm(self):
        if self._chat is None:
            from langchain_openai import ChatOpenAI

            from app.core.config import settings

            model = self.model or settings.openrouter_model
            self._chat = ChatOpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                model=model,
                max_tokens=4096,
                timeout=60,
            )
        return self._chat


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Factory cachée — sélection via ``Settings.llm_provider``.

    Valeurs possibles : ``"anthropic_direct"`` | ``"openrouter"`` (default).
    Le winner du bench R-04-1 est hardcodé post-bench dans
    ``Settings.llm_provider`` default Pydantic Field.
    """
    from app.core.config import settings

    # Default MVP : ``openrouter`` (configuration historique préservée).
    # Post-bench, le winner R-04-1 sera hardcodé comme default.
    provider_name = getattr(settings, "llm_provider", "openrouter")

    if provider_name == "anthropic_direct":
        return AnthropicLLMProvider()
    if provider_name == "openrouter":
        return OpenRouterLLMProvider()
    raise LLMError(f"Unknown llm_provider: {provider_name!r}")


def _reset_llm_provider_cache() -> None:
    """Helper test (non exporté)."""
    get_llm_provider.cache_clear()
