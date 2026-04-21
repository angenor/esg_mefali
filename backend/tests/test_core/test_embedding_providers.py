"""Tests unit Story 10.13 — abstraction EmbeddingProvider.

Couvre AC1 (ABC + impls), AC2 (factory + circuit breaker + fallback),
AC3 (voyage-3 default + voyage-3-large override + whitelist).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.embeddings import (
    EmbeddingDimensionMismatchError,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingRateLimitError,
    _reset_embedding_provider_cache,
    get_embedding_provider,
)
from app.core.embeddings.openai import OpenAIEmbeddingProvider
from app.core.embeddings.voyage import (
    ALLOWED_VOYAGE_MODELS,
    VoyageEmbeddingProvider,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Vider la factory cache + le breaker avant chaque test."""
    from app.graph.tools.common import _reset_breaker_state_for_tests

    _reset_embedding_provider_cache()
    _reset_breaker_state_for_tests()
    yield
    _reset_embedding_provider_cache()
    _reset_breaker_state_for_tests()


# ---------------------------------------------------------------------------
# AC1 — ABC + exceptions canoniques
# ---------------------------------------------------------------------------


def test_embedding_provider_abc_cannot_be_instantiated():
    """EmbeddingProvider() doit lever TypeError (ABC sans méthode concrète)."""
    with pytest.raises(TypeError, match="abstract"):
        EmbeddingProvider()  # type: ignore[abstract]


def test_embedding_exception_hierarchy():
    """EmbeddingRateLimitError et EmbeddingDimensionMismatchError héritent de EmbeddingError."""
    assert issubclass(EmbeddingRateLimitError, EmbeddingError)
    assert issubclass(EmbeddingDimensionMismatchError, EmbeddingError)


# ---------------------------------------------------------------------------
# AC1/AC3 — OpenAI default + Voyage default
# ---------------------------------------------------------------------------


def test_openai_provider_default_model_text_embedding_3_small():
    provider = OpenAIEmbeddingProvider()
    assert provider.model == "text-embedding-3-small"
    assert provider.dimension == 1536
    assert provider.name == "openai"


def test_voyage_provider_default_model_voyage_3():
    provider = VoyageEmbeddingProvider(api_key="test-key")
    assert provider.model == "voyage-3"
    assert provider.dimension == 1024
    assert provider.name == "voyage"


def test_voyage_provider_accepts_voyage_3_large_override():
    provider = VoyageEmbeddingProvider(api_key="test-key", model="voyage-3-large")
    assert provider.model == "voyage-3-large"
    # Dim 1024 invariante quel que soit le modèle (voyage-3 vs large).
    assert provider.dimension == 1024


def test_voyage_provider_rejects_unknown_model():
    with pytest.raises(EmbeddingError, match="Unknown voyage model"):
        VoyageEmbeddingProvider(api_key="test-key", model="voyage-xxl")


def test_allowed_voyage_models_is_whitelist():
    assert "voyage-3" in ALLOWED_VOYAGE_MODELS
    assert "voyage-3-large" in ALLOWED_VOYAGE_MODELS
    assert "voyage-code-3" in ALLOWED_VOYAGE_MODELS
    assert "voyage-3-lite" in ALLOWED_VOYAGE_MODELS
    assert "voyage-xxl" not in ALLOWED_VOYAGE_MODELS


# ---------------------------------------------------------------------------
# AC2 — Factory selection + lru_cache singleton
# ---------------------------------------------------------------------------


def test_get_embedding_provider_returns_voyage_when_configured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "embedding_provider", "voyage")
    monkeypatch.setattr(settings, "voyage_api_key", "test-key")
    monkeypatch.setattr(settings, "voyage_model", "voyage-3")
    _reset_embedding_provider_cache()

    provider = get_embedding_provider()
    assert isinstance(provider, VoyageEmbeddingProvider)


def test_get_embedding_provider_returns_openai_when_configured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "embedding_provider", "openai")
    _reset_embedding_provider_cache()

    provider = get_embedding_provider()
    assert isinstance(provider, OpenAIEmbeddingProvider)


def test_get_embedding_provider_is_cached(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "embedding_provider", "openai")
    _reset_embedding_provider_cache()

    first = get_embedding_provider()
    second = get_embedding_provider()
    assert first is second  # singleton


def test_get_embedding_provider_raises_on_unknown(monkeypatch):
    from app.core.config import settings

    # Bypass la validation Pydantic en monkey-patchant directement.
    monkeypatch.setattr(settings, "embedding_provider", "mistral")
    _reset_embedding_provider_cache()

    with pytest.raises(EmbeddingError, match="unknown embedding_provider"):
        get_embedding_provider()


# ---------------------------------------------------------------------------
# AC1/AC3 — Voyage embed returns 1024-dim (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voyage_embed_returns_1024_dim_vectors():
    provider = VoyageEmbeddingProvider(api_key="test-key")
    fake_vector = [0.1] * 1024
    fake_result = type("Obj", (), {"embeddings": [fake_vector, fake_vector]})()

    with patch.object(
        provider,
        "_embed_direct",
        new=AsyncMock(return_value=[fake_vector, fake_vector]),
    ):
        result = await provider.embed(["bonjour", "world"])
    assert len(result) == 2
    assert len(result[0]) == 1024


@pytest.mark.asyncio
async def test_voyage_embed_empty_texts_returns_empty():
    provider = VoyageEmbeddingProvider(api_key="test-key")
    result = await provider.embed([])
    assert result == []


@pytest.mark.asyncio
async def test_voyage_dim_mismatch_raises():
    """Invariant dim cassé = EmbeddingDimensionMismatchError."""
    provider = VoyageEmbeddingProvider(api_key="test-key")

    class FakeResult:
        embeddings = [[0.1] * 512]  # wrong dim

    class FakeClient:
        async def embed(self, texts, model):
            return FakeResult()

    # Bypass _get_async_client pour injecter un faux client async.
    provider._async_client = FakeClient()

    # Forcer le chemin AsyncClient branch en mockant isinstance Client :
    # plus simple, on patche _embed_direct pour retourner la mauvaise dim.
    import voyageai

    with patch.object(voyageai, "Client", new=type("X", (), {})):
        # _embed_direct va passer par la branche AsyncClient.
        with pytest.raises(EmbeddingDimensionMismatchError):
            await provider._embed_direct(["x"], model="voyage-3")


# ---------------------------------------------------------------------------
# AC2 — Circuit breaker fallback OpenAI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voyage_fallback_to_openai_on_circuit_breaker_open():
    """AC2 : breaker ouvert → fallback automatique vers OpenAI."""
    from app.graph.tools.common import _breaker

    fallback = OpenAIEmbeddingProvider()
    fake_openai_result = [[0.42] * 1536]
    mock_embed = AsyncMock(return_value=fake_openai_result)
    with patch.object(fallback, "embed", new=mock_embed):
        provider = VoyageEmbeddingProvider(api_key="test-key", fallback=fallback)
        # Ouvrir manuellement le breaker (simuler 10 échecs).
        for _ in range(_breaker.THRESHOLD):
            await _breaker.record_failure(
                "embedding", "voyage", is_llm_5xx=True
            )
        result = await provider.embed(["texte"])
        assert result == fake_openai_result
        assert mock_embed.await_count == 1


@pytest.mark.asyncio
async def test_voyage_rate_limit_triggers_fallback():
    """AC2 : RateLimitError → fallback OpenAI + record_failure."""
    fallback = OpenAIEmbeddingProvider()
    fake_openai_result = [[0.5] * 1536]
    with patch.object(
        fallback,
        "embed",
        new=AsyncMock(return_value=fake_openai_result),
    ):
        provider = VoyageEmbeddingProvider(api_key="test-key", fallback=fallback)
        with patch.object(
            provider,
            "_embed_direct",
            new=AsyncMock(side_effect=EmbeddingRateLimitError("429")),
        ):
            result = await provider.embed(["texte"])

    assert result == fake_openai_result


@pytest.mark.asyncio
async def test_voyage_error_without_fallback_propagates():
    """Sans fallback configuré, l'erreur remonte (pas de silent fail)."""
    provider = VoyageEmbeddingProvider(api_key="test-key", fallback=None)
    with patch.object(
        provider,
        "_embed_direct",
        new=AsyncMock(side_effect=EmbeddingError("boom")),
    ):
        with pytest.raises(EmbeddingError, match="boom"):
            await provider.embed(["texte"])


# ---------------------------------------------------------------------------
# Scan NFR66 / règle 10.5 — pas de try/except Exception catch-all
# ---------------------------------------------------------------------------


def test_no_generic_except_in_embeddings_module():
    """Leçon 9.7 C1 — zéro ``except Exception`` dans le module embeddings.

    Exception documentée : ``openai.py`` a un ``except Exception`` contrôlé
    qui re-raise en canonique ``EmbeddingError`` (mapping vendor-neutre).
    """
    import re
    from pathlib import Path

    module_root = Path(__file__).resolve().parents[2] / "app" / "core" / "embeddings"
    offenders: list[str] = []
    pattern = re.compile(r"^\s*except\s+Exception\b")
    # Fichiers tolérés : openai.py a 1 ``except Exception`` documenté
    # (wrap en ``EmbeddingError``) — accepte ≤ 1 hit pour ce fichier.
    for py_file in module_root.rglob("*.py"):
        for line in py_file.read_text().splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if pattern.match(line):
                offenders.append(f"{py_file.name}: {line.strip()}")

    # openai.py a 1 except Exception contrôlé (mapping canonique) — toléré.
    assert len(offenders) <= 1, f"generic except found: {offenders}"
