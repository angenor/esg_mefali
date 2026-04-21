"""Implémentation OpenAI — wrapper ``langchain_openai.OpenAIEmbeddings``.

Story 10.13 — legacy (text-embedding-3-small, 1536 dim). Conservé comme
fallback automatique quand Voyage est indisponible (breaker ouvert AC2).

Scope MVP strict : consommé par le chemin document_chunks uniquement.
Les embeddings Fund (``modules/financing``) restent non migrés Phase 0
(écart scope story — cf. deferred-work HIGH-10.13-2).
"""

from __future__ import annotations

import logging

from .base import (
    EmbeddingDimensionMismatchError,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingRateLimitError,
)

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "text-embedding-3-small"
_DEFAULT_DIMENSION = 1536


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Provider OpenAI text-embedding-3-small — legacy / fallback.

    Dim 1536 fixe. La clé d'API + base_url sont lues depuis ``Settings``
    (réutilise ``openrouter_*`` existants, fallback ``llm_*`` via alias).
    """

    name = "openai"
    dimension = _DEFAULT_DIMENSION

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        from app.core.config import settings

        self.model = model
        self._api_key = api_key or settings.openrouter_api_key
        self._base_url = base_url or settings.openrouter_base_url
        # Lazy-init du client LangChain — évite le coût de boot si
        # ``voyage`` est sélectionné et OpenAI jamais invoqué.
        self._client = None

    def _get_client(self):
        if self._client is None:
            from langchain_openai import OpenAIEmbeddings

            self._client = OpenAIEmbeddings(
                model=self.model,
                openai_api_base=self._base_url,
                openai_api_key=self._api_key,
            )
        return self._client

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        if not texts:
            return []

        if model and model != self.model:
            # Modèle ponctuel : instancier un client ad-hoc (rare).
            from langchain_openai import OpenAIEmbeddings

            client = OpenAIEmbeddings(
                model=model,
                openai_api_base=self._base_url,
                openai_api_key=self._api_key,
            )
        else:
            client = self._get_client()

        try:
            vectors = await client.aembed_documents(texts)
        except Exception as exc:  # noqa: BLE001 — wrap en canoniques
            # Classification légère sans try/except Exception catch-all fantôme :
            # on mappe les exceptions connues des clients openai vers notre
            # hiérarchie canonique. Le `Exception` brut reste re-raise comme
            # ``EmbeddingError`` pour éviter de fuiter un type vendor.
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg:
                raise EmbeddingRateLimitError(str(exc)) from exc
            raise EmbeddingError(f"OpenAI embedding failed: {exc}") from exc

        # Invariant dimension (défense en profondeur).
        if vectors and len(vectors[0]) != self.dimension:
            raise EmbeddingDimensionMismatchError(
                f"OpenAI returned dim={len(vectors[0])} expected {self.dimension}"
            )
        return vectors
