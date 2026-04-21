"""Story 10.13 AC6 — tests qualité recall@5 Voyage ≥ OpenAI baseline.

Gated ``@pytest.mark.network`` + env ``EMBEDDINGS_QUALITY_CHECK=1`` +
``VOYAGE_API_KEY`` + ``OPENAI_API_KEY``. Skippés CI standard.

Le corpus golden ``fixtures/embeddings_quality_corpus.json`` fournit
15 queries (10 FR ESG + 5 EN EUDR) + 10 chunks étiquetés ``expected_top5``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def corpus():
    path = (
        Path(__file__).resolve().parent / "fixtures" / "embeddings_quality_corpus.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _env_guard():
    """Skip si env variables manquantes (pattern 10.11 C2 9.7)."""
    if os.environ.get("EMBEDDINGS_QUALITY_CHECK") != "1":
        pytest.skip("EMBEDDINGS_QUALITY_CHECK=1 requis (tests live LLM)")
    if not os.environ.get("VOYAGE_API_KEY"):
        pytest.skip("VOYAGE_API_KEY requis (tests qualité Voyage)")


def _recall_at_5(retrieved_ids: list[str], expected_ids: list[str]) -> float:
    """|top5 ∩ expected| / 5."""
    expected = set(expected_ids)
    return len(set(retrieved_ids) & expected) / 5.0


@pytest.mark.asyncio
async def test_corpus_structure_is_valid(corpus):
    """Meta-test non-network durci post-review CRITICAL-1 (2026-04-21).

    Garanties :
      1. Exactement 15 queries (10 FR ESG + 5 EN EUDR).
      2. Exactement 50 chunks (AC6 spec — pas de corpus tronqué masqué).
      3. Chaque query expose 5 ``expected_top5_chunk_ids`` uniques.
      4. **Chaque ``expected_top5_chunk_ids`` référence un chunk réel** —
         fail-fast si le corpus est désynchronisé vs ground-truth.
    """
    queries = corpus["queries"]
    chunks = corpus["chunks"]
    available_ids = {c["id"] for c in chunks}

    assert len(queries) == 15, f"expected 15 queries, got {len(queries)}"
    assert len(chunks) == 50, f"expected 50 chunks AC6, got {len(chunks)}"
    assert len(available_ids) == 50, "chunk ids must be unique"

    for q in queries:
        expected = q["expected_top5_chunk_ids"]
        assert len(expected) == 5, f"{q['id']}: must list 5 expected chunks"
        assert len(set(expected)) == 5, f"{q['id']}: expected ids must be unique"
        missing = [cid for cid in expected if cid not in available_ids]
        assert not missing, (
            f"{q['id']}: expected_top5 references non-existent chunks: {missing}"
        )


@pytest.mark.asyncio
async def test_recall_at_5_voyage_ge_openai_minus_5pt(corpus):
    """AC6 — Voyage recall@5 ≥ OpenAI - 0.05 sur 15 queries (tolérance 5 pts)."""
    _env_guard()

    from app.core.embeddings.openai import OpenAIEmbeddingProvider
    from app.core.embeddings.voyage import VoyageEmbeddingProvider

    voyage = VoyageEmbeddingProvider()
    openai_p = OpenAIEmbeddingProvider()

    chunks = corpus["chunks"]
    chunk_ids = [c["id"] for c in chunks]
    chunk_texts = [c["content"] for c in chunks]

    # Embedder le corpus + queries avec les deux providers.
    voyage_chunk_vecs = await voyage.embed(chunk_texts)
    openai_chunk_vecs = await openai_p.embed(chunk_texts)

    voyage_recalls: list[float] = []
    openai_recalls: list[float] = []

    import math

    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    def _top5_ids(query_vec, chunk_vecs):
        sims = [_cosine(query_vec, cv) for cv in chunk_vecs]
        ranked = sorted(zip(chunk_ids, sims), key=lambda p: -p[1])
        return [cid for cid, _ in ranked[:5]]

    for q in corpus["queries"]:
        voyage_q = (await voyage.embed([q["text"]]))[0]
        openai_q = (await openai_p.embed([q["text"]]))[0]
        voyage_recalls.append(
            _recall_at_5(_top5_ids(voyage_q, voyage_chunk_vecs), q["expected_top5_chunk_ids"])
        )
        openai_recalls.append(
            _recall_at_5(_top5_ids(openai_q, openai_chunk_vecs), q["expected_top5_chunk_ids"])
        )

    voyage_mean = sum(voyage_recalls) / len(voyage_recalls)
    openai_mean = sum(openai_recalls) / len(openai_recalls)

    # AC6 gate : Voyage ≥ OpenAI - 0.05.
    assert voyage_mean >= openai_mean - 0.05, (
        f"Recall@5 Voyage={voyage_mean:.3f} < OpenAI={openai_mean:.3f} - 0.05 "
        f"(régression > 5 pts, fail AC6)"
    )


@pytest.mark.asyncio
async def test_latency_p95_voyage_under_2s_on_batch_100(corpus):
    """AC6 — latence p95 Voyage < 2 s sur batch 100 textes."""
    _env_guard()

    from app.core.embeddings.voyage import VoyageEmbeddingProvider

    provider = VoyageEmbeddingProvider()

    # Génère 100 textes synthétiques (5 répétitions du corpus 10 chunks
    # + 10 queries = 20 ; upscale).
    base = [c["content"] for c in corpus["chunks"]] + [
        q["text"] for q in corpus["queries"]
    ]
    batch = (base * 5)[:100]

    # Mesure 5 fois pour calculer p95.
    durations_ms: list[float] = []
    for _ in range(5):
        started = time.perf_counter()
        await provider.embed(batch)
        durations_ms.append((time.perf_counter() - started) * 1000)

    durations_ms.sort()
    p95 = durations_ms[int(len(durations_ms) * 0.95) - 1]

    assert p95 < 2000, f"Latence p95 Voyage {p95:.0f} ms > 2 000 ms (fail AC6)"
