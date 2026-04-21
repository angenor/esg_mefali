"""Implémentation Voyage API — SDK officiel ``voyageai``.

Story 10.13 — provider MVP default. Dim 1024 (voyage-3 et voyage-3-large).
Fallback automatique vers ``OpenAIEmbeddingProvider`` quand le circuit
breaker est ouvert (AC2). Le breaker ``_breaker`` (graph/tools/common.py)
est réutilisé avec la clé ``("embedding", provider_id)`` — Q6 tranchée.

SDK officiel ``voyageai>=0.2.4`` (disponible PyPI). Le SDK gère nativement
les headers ``Retry-After`` 429 via son token bucket interne — Q4.
"""

from __future__ import annotations

import asyncio
import logging

from .base import (
    EmbeddingDimensionMismatchError,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingRateLimitError,
)

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "voyage-3"
_DEFAULT_DIMENSION = 1024

#: Modèles Voyage autorisés — whitelist défensive (Q1). Toute valeur hors
#: ``VOYAGE_MODEL`` env est rejetée en amont par ``field_validator`` Pydantic.
ALLOWED_VOYAGE_MODELS: frozenset[str] = frozenset({
    "voyage-3",
    "voyage-3-large",
    "voyage-code-3",
    "voyage-3-lite",
})


class VoyageEmbeddingProvider(EmbeddingProvider):
    """Provider Voyage — MVP default. voyage-3 1024 dim.

    Fallback automatique OpenAI si le circuit breaker
    ``("embedding", "voyage")`` est ouvert (10 échecs 5xx/429 consécutifs
    sur 60 s). Voir ``graph/tools/common.py::_CircuitBreakerState``.
    """

    name = "voyage"
    dimension = _DEFAULT_DIMENSION

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        fallback: EmbeddingProvider | None = None,
    ) -> None:
        from app.core.config import settings

        if model not in ALLOWED_VOYAGE_MODELS:
            # Défense en profondeur (Pydantic field_validator rejette déjà).
            raise EmbeddingError(
                f"Unknown voyage model: {model!r}. "
                f"Allowed: {sorted(ALLOWED_VOYAGE_MODELS)}"
            )
        self.model = model
        self._api_key = api_key or settings.voyage_api_key
        self._fallback = fallback
        self._client = None
        self._async_client = None

    # ------------------------------------------------------------------
    # Circuit breaker partagé — Q6 tranchée
    # ------------------------------------------------------------------
    def _breaker_key(self) -> tuple[str, str]:
        """Clé ``(tool_name, node_name)`` pour ``_CircuitBreakerState``.

        ``embedding`` est utilisé comme "tool_name" symbolique ; le
        ``node_name`` reçoit l'identifiant du provider (``voyage``). Cela
        garantit l'absence de collision avec les breakers métier tools
        LangGraph Story 9.7.
        """
        return ("embedding", self.name)

    def _get_async_client(self):
        if self._async_client is None:
            import voyageai

            # Le SDK voyageai expose AsyncClient 0.2.x — utilise le si dispo,
            # sinon fallback synchrone via asyncio.to_thread.
            if hasattr(voyageai, "AsyncClient"):
                self._async_client = voyageai.AsyncClient(api_key=self._api_key)
            else:
                self._async_client = voyageai.Client(api_key=self._api_key)
        return self._async_client

    async def _embed_direct(
        self,
        texts: list[str],
        *,
        model: str,
    ) -> list[list[float]]:
        """Appel brut du SDK Voyage, sans circuit breaker ni fallback."""
        import voyageai

        client = self._get_async_client()

        try:
            if isinstance(client, voyageai.Client):
                # SDK sync — offload via asyncio.to_thread (Piège #9).
                result = await asyncio.to_thread(
                    client.embed,
                    texts,
                    model=model,
                )
            else:
                # AsyncClient natif si exposé par le SDK.
                result = await client.embed(texts, model=model)
        except voyageai.error.RateLimitError as exc:  # type: ignore[attr-defined]
            raise EmbeddingRateLimitError(str(exc)) from exc
        except voyageai.error.APIError as exc:  # type: ignore[attr-defined]
            raise EmbeddingError(f"Voyage API error: {exc}") from exc

        # L'objet voyageai.EmbeddingsObject expose .embeddings (list[list[float]]).
        vectors = getattr(result, "embeddings", None)
        if vectors is None and isinstance(result, dict):
            vectors = result.get("embeddings")
        if vectors is None:
            raise EmbeddingError(f"Voyage response missing embeddings: {result!r}")

        if vectors and len(vectors[0]) != self.dimension:
            raise EmbeddingDimensionMismatchError(
                f"Voyage returned dim={len(vectors[0])} expected {self.dimension}"
            )
        return vectors

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        if not texts:
            return []

        from app.graph.tools.common import _breaker

        effective_model = model or self.model
        tool_name, node_name = self._breaker_key()

        # Breaker ouvert → fallback direct OpenAI sans appel Voyage.
        if await _breaker.should_block(tool_name, node_name):
            if self._fallback is not None:
                logger.warning(
                    "Voyage circuit breaker open, falling back to %s",
                    self._fallback.name,
                    extra={
                        "metric": "embedding_fallback_openai",
                        "reason": "voyage_circuit_open",
                        "provider": self.name,
                    },
                )
                return await self._fallback.embed(texts, model=None)
            raise EmbeddingError("Voyage breaker open and no fallback configured")

        try:
            vectors = await self._embed_direct(texts, model=effective_model)
        except EmbeddingRateLimitError:
            await _breaker.record_failure(tool_name, node_name, is_llm_5xx=True)
            if self._fallback is not None:
                logger.warning(
                    "Voyage rate-limit, falling back to %s",
                    self._fallback.name,
                    extra={
                        "metric": "embedding_fallback_openai",
                        "reason": "voyage_rate_limit",
                    },
                )
                return await self._fallback.embed(texts, model=None)
            raise
        except EmbeddingError:
            await _breaker.record_failure(tool_name, node_name, is_llm_5xx=True)
            raise

        await _breaker.record_success(tool_name, node_name)
        return vectors
