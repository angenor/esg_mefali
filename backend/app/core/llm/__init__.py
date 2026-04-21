"""Couche d'abstraction LLM — Story 10.13 AC10.

Pattern byte-identique ``app/core/embeddings/``. Factory lru_cache +
fallback provider configuré post-bench.
"""

from __future__ import annotations

from .provider import (
    LLMError,
    LLMProvider,
    LLMRateLimitError,
    get_llm_provider,
)

__all__ = [
    "LLMProvider",
    "LLMError",
    "LLMRateLimitError",
    "get_llm_provider",
]
