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


def test_embedding_breaker_key_is_separate_from_tool_breakers():
    """MEDIUM-2 post-review — la clé ``('embedding', 'voyage')`` du breaker
    ne collisionne pas avec les clés ``(tool_name, node_name)`` des tools
    LangGraph (Story 9.7). Validation schéma de clés.
    """
    provider = VoyageEmbeddingProvider(api_key="test-key")
    key = provider._breaker_key()
    assert key == ("embedding", "voyage")
    # Collision théorique : un tool nommé "embedding" dans le graph n'existe
    # pas — scan du registry graph/tools/ confirme (aucun tool embed_*).
    from pathlib import Path
    tools_dir = Path(__file__).resolve().parents[2] / "app" / "graph" / "tools"
    for py_file in tools_dir.rglob("*.py"):
        content = py_file.read_text()
        # Un tool registré porterait ``name="embedding"`` — scan défensif.
        assert 'name="embedding"' not in content, (
            f"Collision risque : {py_file.name} enregistre un tool nommé "
            "'embedding' — renommer ou durcir la clé du breaker."
        )


def test_financing_service_uses_embedding_provider():
    """HIGH-3 post-review — le scan no-duplicate règle 10.5 doit passer :
    ``OpenAIEmbeddings(`` n'apparaît plus dans le **code exécutable** de
    ``modules/financing/`` (les docstrings et commentaires d'historique
    sont tolérés — cf. `get_embedding_provider()` est utilisé runtime).
    """
    import ast
    import re
    from pathlib import Path

    financing_dir = (
        Path(__file__).resolve().parents[2] / "app" / "modules" / "financing"
    )
    pattern = re.compile(r"\bOpenAIEmbeddings\(")
    offenders: list[str] = []
    for py_file in financing_dir.rglob("*.py"):
        source = py_file.read_text()
        # Strip docstrings via AST pour éviter faux positifs sur commentaires
        # historiques qui mentionnent "OpenAIEmbeddings(".
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        docstring_ranges: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    doc = node.body[0]
                    docstring_ranges.append((doc.lineno, doc.end_lineno or doc.lineno))
        for line_no, line in enumerate(source.splitlines(), 1):
            if any(lo <= line_no <= hi for lo, hi in docstring_ranges):
                continue
            if line.lstrip().startswith("#"):
                continue
            if pattern.search(line):
                offenders.append(f"{py_file.name}:{line_no}")
    assert offenders == [], f"financing/ uses OpenAIEmbeddings directly: {offenders}"


def test_financing_chunks_has_embedding_vec_v2():
    """HIGH-3 post-review — la colonne ``embedding_vec_v2 Vector(1024)``
    doit exister sur ``FinancingChunk`` (migration 032).
    """
    from app.models.financing import FinancingChunk

    assert hasattr(FinancingChunk, "embedding_vec_v2"), (
        "FinancingChunk.embedding_vec_v2 absent — migration 032 non wirée ?"
    )


def test_voyageai_sdk_surface_compat():
    """MEDIUM-3 post-review 2026-04-21 — fail-fast si le SDK voyageai
    (0.2.x compat Python 3.14, pivot vs 0.3.4 spec) change de surface.

    Le pivot ``voyageai-0.2.3`` utilise :
      - ``voyageai.Client`` (sync, toujours présent)
      - ``voyageai.AsyncClient`` (optional, détecté via ``hasattr``)
      - ``voyageai.error.RateLimitError`` + ``voyageai.error.APIError``

    Si le SDK renomme ``voyageai.error`` → ``voyageai.exceptions`` en 0.3+,
    ce test détecte la régression au prochain bump dep avant le runtime.
    """
    import voyageai

    assert hasattr(voyageai, "Client"), "voyageai.Client absent"
    assert hasattr(voyageai, "error"), "voyageai.error module absent (renommé ?)"
    assert hasattr(voyageai.error, "RateLimitError"), "RateLimitError absent"
    assert hasattr(voyageai.error, "APIError"), "APIError absent"


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

    Post-patch HIGH-4 (2026-04-21) : ``openai.py`` catche désormais des
    exceptions vendor explicites (``openai.RateLimitError``, ``APIError``,
    ``APITimeoutError``, ``APIConnectionError``) — plus de substring match
    ``"rate" in msg``. Scan strict : 0 offender.
    """
    import re
    from pathlib import Path

    module_root = Path(__file__).resolve().parents[2] / "app" / "core" / "embeddings"
    offenders: list[str] = []
    pattern = re.compile(r"^\s*except\s+Exception\b")
    for py_file in module_root.rglob("*.py"):
        for line in py_file.read_text().splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if pattern.match(line):
                offenders.append(f"{py_file.name}: {line.strip()}")

    assert offenders == [], f"generic except Exception found: {offenders}"


# ---------------------------------------------------------------------------
# HIGH-4 — Exceptions vendor OpenAI explicites (3 cas)
# ---------------------------------------------------------------------------


def _fake_httpx_request():
    """Fabrique un ``httpx.Request`` stub minimal pour les exceptions openai."""
    import httpx

    return httpx.Request("POST", "https://api.openai.com/v1/embeddings")


def _fake_httpx_response(status_code: int):
    """Fabrique un ``httpx.Response`` stub avec ``.request`` attaché."""
    import httpx

    return httpx.Response(status_code=status_code, request=_fake_httpx_request())


@pytest.mark.asyncio
async def test_openai_provider_maps_rate_limit_error():
    """``openai.RateLimitError`` → ``EmbeddingRateLimitError`` canonique."""
    from openai import RateLimitError

    provider = OpenAIEmbeddingProvider()

    class _FakeClient:
        async def aembed_documents(self, texts):
            raise RateLimitError(
                message="429 rate exceeded",
                response=_fake_httpx_response(429),
                body=None,
            )

    provider._client = _FakeClient()
    with pytest.raises(EmbeddingRateLimitError):
        await provider.embed(["x"])


@pytest.mark.asyncio
async def test_openai_provider_maps_api_timeout_error():
    """``openai.APITimeoutError`` → ``EmbeddingError`` canonique."""
    from openai import APITimeoutError

    provider = OpenAIEmbeddingProvider()

    class _FakeClient:
        async def aembed_documents(self, texts):
            raise APITimeoutError(request=_fake_httpx_request())

    provider._client = _FakeClient()
    with pytest.raises(EmbeddingError, match="connection/timeout"):
        await provider.embed(["x"])


@pytest.mark.asyncio
async def test_openai_provider_maps_api_error():
    """``openai.APIError`` générique → ``EmbeddingError`` canonique."""
    from openai import APIError

    provider = OpenAIEmbeddingProvider()

    class _FakeClient:
        async def aembed_documents(self, texts):
            raise APIError(
                message="500 server error",
                request=_fake_httpx_request(),
                body=None,
            )

    provider._client = _FakeClient()
    with pytest.raises(EmbeddingError, match="API error"):
        await provider.embed(["x"])
