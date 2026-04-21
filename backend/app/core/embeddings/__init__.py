"""Couche d'abstraction embeddings — Story 10.13.

Façade publique étroite (pattern byte-identique Story 10.6 storage/).
Providers disponibles :
  - ``VoyageEmbeddingProvider`` : MVP default, voyage-3 1024 dim.
  - ``OpenAIEmbeddingProvider`` : legacy / fallback, text-embedding-3-small 1536 dim.

Sélection via ``Settings.embedding_provider`` ∈ {"voyage", "openai"}.
"""

from __future__ import annotations

from functools import lru_cache

from .base import (
    EmbeddingDimensionMismatchError,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingQuotaError,
    EmbeddingRateLimitError,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingError",
    "EmbeddingRateLimitError",
    "EmbeddingQuotaError",
    "EmbeddingDimensionMismatchError",
    "get_embedding_provider",
]


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Factory cachée (singleton process-level).

    Retourne l'instance configurée via ``Settings.embedding_provider`` :
      - ``"voyage"`` → ``VoyageEmbeddingProvider`` avec fallback OpenAI.
      - ``"openai"`` → ``OpenAIEmbeddingProvider`` (pas de fallback Voyage).

    Utilisable comme dépendance FastAPI : ``Depends(get_embedding_provider)``.
    """
    from app.core.config import settings

    from .openai import OpenAIEmbeddingProvider
    from .voyage import VoyageEmbeddingProvider

    provider = settings.embedding_provider.lower()

    if provider == "openai":
        return OpenAIEmbeddingProvider()

    if provider == "voyage":
        fallback = OpenAIEmbeddingProvider()
        return VoyageEmbeddingProvider(
            model=settings.voyage_model or "voyage-3",
            fallback=fallback,
        )

    # Safety net — la regex Pydantic bloque normalement.
    raise EmbeddingError(f"unknown embedding_provider: {provider!r}")


def _reset_embedding_provider_cache() -> None:
    """Helper de test — invalide le singleton ``lru_cache``.

    **Ne pas** exporter dans ``__all__`` (API publique étroite).
    """
    get_embedding_provider.cache_clear()
