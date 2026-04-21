"""Tests Story 10.13 AC8 — grep Python natif sur docs CODEMAPS / bench report / .env.example."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_codemap_rag_has_5_sections():
    """rag.md contient les 5 sections H2 requises (AC8)."""
    rag = _REPO_ROOT / "docs" / "CODEMAPS" / "rag.md"
    content = rag.read_text(encoding="utf-8")
    required_sections = [
        "## 1. Contexte & Architecture",
        "## 2. Abstraction EmbeddingProvider",
        "## 3. Migration dim 1536 → 1024",
        "## 4. Batch re-embedding corpus",
        "## 5. Pièges",
    ]
    for section in required_sections:
        assert section in content, f"Section manquante dans rag.md : {section}"


def test_codemap_rag_has_mermaid_sequence_diagram():
    """AC8 — Mermaid sequenceDiagram présent dans rag.md."""
    rag = (_REPO_ROOT / "docs" / "CODEMAPS" / "rag.md").read_text(encoding="utf-8")
    assert "```mermaid" in rag
    assert "sequenceDiagram" in rag
    assert "get_embedding_provider" in rag


def test_codemap_index_lists_rag():
    """AC8 — docs/CODEMAPS/index.md contient la ligne rag.md."""
    index = (_REPO_ROOT / "docs" / "CODEMAPS" / "index.md").read_text(encoding="utf-8")
    assert "rag.md" in index
    assert "EmbeddingProvider" in index


def test_env_example_has_voyage_and_anthropic_vars():
    """AC8 — .env.example expose EMBEDDING_PROVIDER + VOYAGE_API_KEY + VOYAGE_MODEL + ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL."""
    env = (_REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for var in [
        "EMBEDDING_PROVIDER",
        "VOYAGE_API_KEY",
        "VOYAGE_MODEL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "LLM_PROVIDER",
    ]:
        assert var in env, f".env.example manque {var}"


def test_bench_report_has_8_sections():
    """AC8 — docs/bench-llm-providers-phase0.md contient 8 sections H2."""
    report = (_REPO_ROOT / "docs" / "bench-llm-providers-phase0.md").read_text(
        encoding="utf-8"
    )
    required = [
        "## 1. Contexte R-04-1",
        "## 2. Méthodologie",
        "## 3. Résultats par provider",
        "## 4. Résultats par tool",
        "## 5. Recommandation provider primaire MVP",
        "## 6. Configuration finale",
        "## 7. Risques & limites",
        "## 8. Re-bench policy",
    ]
    for section in required:
        assert section in report, f"Section manquante : {section}"


def test_bench_report_contains_recommendation():
    """AC8 — le report mentionne explicitement un winner primaire + fallback."""
    report = (_REPO_ROOT / "docs" / "bench-llm-providers-phase0.md").read_text(
        encoding="utf-8"
    )
    assert "Recommandation" in report
    assert "anthropic" in report.lower()


@pytest.mark.parametrize(
    "annex",
    ["anthropic-openrouter.md", "anthropic-direct.md", "minimax-openrouter.md"],
)
def test_llm_providers_annexes_exist(annex: str):
    """AC8 — 3 annexes providers dans docs/llm-providers/."""
    path = _REPO_ROOT / "docs" / "llm-providers" / annex
    assert path.exists(), f"Annexe manquante : {annex}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 200, f"Annexe {annex} trop courte"
