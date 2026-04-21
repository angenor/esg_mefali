"""ABC EmbeddingProvider + hiérarchie d'exceptions canoniques.

Story 10.13 — découple les consommateurs (documents.service) des détails
d'implémentation du fournisseur d'embeddings. NFR42 provider abstraction +
NFR68 budget LLM + NFR74 observabilité qualité.

Pattern byte-identique au module ``app/core/storage/base.py`` (Story 10.6) :
ABC avec exceptions canoniques, jamais d'exception vendor brute remontée.

Références :
  - architecture.md §D10 LLM Provider Layer (étendu aux embeddings)
  - architecture.md §NFR75 circuit breaker 60 s
  - business-decisions-2026-04-19.md §R-04-1 bench providers
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingError(Exception):
    """Erreur de la couche embeddings (parent). Capture toute anomalie transverse."""


class EmbeddingRateLimitError(EmbeddingError):
    """429 côté fournisseur : quota par minute/jour saturé."""


class EmbeddingQuotaError(EmbeddingError):
    """Quota budgétaire dépassé (ex. crédit épuisé)."""


class EmbeddingDimensionMismatchError(EmbeddingError):
    """Le vecteur retourné n'a pas la dimension attendue par le provider."""


class EmbeddingProvider(ABC):
    """Abstraction provider d'embeddings — OpenAI (legacy) ou Voyage (MVP).

    Contrat d'invariants :
      - ``embed(texts)`` retourne une liste de vecteurs de même cardinalité
        que ``texts`` (1-to-1 alignement par indice).
      - La dimension de chaque vecteur est ``self.dimension`` (invariant
        par implémentation : 1536 OpenAI text-embedding-3-small, 1024 Voyage).
      - Les exceptions sont canoniques (hiérarchie ``EmbeddingError``),
        jamais ``voyageai.error.*`` ou ``openai.RateLimitError`` bruts.
      - ``embed`` ne bloque pas l'event loop (client async natif ou
        ``asyncio.to_thread`` fallback).
    """

    #: Identifiant court et stable du provider (ex. "voyage", "openai").
    name: str = ""

    #: Dimension produite par ``embed`` — invariante pour une instance donnée.
    dimension: int = 0

    #: Modèle concret utilisé (ex. "voyage-3", "text-embedding-3-small").
    model: str = ""

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> list[list[float]]:
        """Retourne l'embedding de chaque texte, aligné par indice.

        Args:
            texts: Liste non vide de chaînes à encoder.
            model: Surcharge ponctuelle du modèle (par défaut ``self.model``).

        Raises:
            EmbeddingRateLimitError: 429 persistant après retries.
            EmbeddingQuotaError: quota budgétaire épuisé.
            EmbeddingDimensionMismatchError: le provider a renvoyé un
                vecteur de dimension inattendue (invariant cassé).
            EmbeddingError: toute autre anomalie (réseau, parse, etc.).
        """
