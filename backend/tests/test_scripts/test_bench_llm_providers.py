"""Tests Story 10.13 Livrable B — scripts/bench_llm_providers.py (AC9)."""

from __future__ import annotations

import argparse

import pytest

from scripts import bench_llm_providers as bench


def test_parse_args_defaults():
    args = bench._parse_args([])
    assert args.provider == "all"
    assert args.tool == "all"
    assert args.samples == 10
    assert args.dry_run is False


def test_parse_args_single_provider():
    args = bench._parse_args(["--provider", "anthropic_direct"])
    assert args.provider == "anthropic_direct"


def test_parse_args_rejects_unknown_provider():
    with pytest.raises(SystemExit):
        bench._parse_args(["--provider", "openai_xxx"])


def test_resolve_scope_all_yields_3x5():
    args = argparse.Namespace(provider="all", tool="all")
    tools, providers = bench._resolve_scope(args)
    assert len(tools) == 5
    assert len(providers) == 3


def test_resolve_scope_single_tool():
    args = argparse.Namespace(provider="all", tool="generate_action_plan")
    tools, providers = bench._resolve_scope(args)
    assert tools == ["generate_action_plan"]
    assert len(providers) == 3


# ---------------------------------------------------------------------------
# Scoring 4 axes unit tests
# ---------------------------------------------------------------------------


def test_score_axis_format_empty_returns_zero():
    assert bench.score_axis_format_valid("") == 0
    assert bench.score_axis_format_valid("   ") == 0


def test_score_axis_format_non_empty_returns_one():
    assert bench.score_axis_format_valid("Bonjour le monde") == 1


def test_score_axis_fr_accents_density_above_threshold():
    """Un texte avec suffisamment d'accents → score 1."""
    text = (
        "Ceci est un résumé exécutif très détaillé avec beaucoup d'accents français. "
        "L'équipe a préparé un bilan complet après délibération approfondie. "
        "Les résultats sont présentés dans un rapport officiel."
    )
    assert bench.score_axis_fr_accents(text) == 1


def test_score_axis_fr_accents_no_accents_returns_zero():
    text = (
        "This is a long English text without any accents at all, which should fail "
        "the French accent density check because it lacks accented characters."
    )
    assert bench.score_axis_fr_accents(text) == 0


def test_score_axis_forbidden_vocab_clean_text():
    assert bench.score_axis_no_forbidden_vocab("Texte propre et sans problème") == 1


def test_score_axis_numeric_coherence_no_source():
    """Pas de source_values → score 1 par défaut."""
    assert bench.score_axis_numeric_coherence("Score de 45/100", {}) == 1


def test_score_axis_numeric_coherence_aligned():
    """Nombre dans le texte proche de la source → score 1."""
    assert bench.score_axis_numeric_coherence(
        "Le score global est de 50/100.", {"esg_score": 50.0}
    ) == 1


def test_score_axis_numeric_coherence_divergent():
    """Nombre texte >> divergence tolérance → score 0."""
    assert bench.score_axis_numeric_coherence(
        "Le score global est de 95/100.", {"esg_score": 50.0}
    ) == 0


def test_score_sample_aggregates_4_axes():
    result = bench.score_sample(
        "Résumé exécutif détaillé avec présentation approfondie des résultats officiels préparés.",
        {},
    )
    assert "axis_format" in result
    assert "axis_numeric_coherence" in result
    assert "axis_no_forbidden_vocab" in result
    assert "axis_fr_accents" in result
    assert 0 <= result["score_total"] <= 1


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------


def test_estimate_cost_anthropic_direct_input_only():
    # 1M tokens input seulement, 0 output → input_eur_1m (2.76 EUR).
    cost = bench.estimate_cost_eur("anthropic_direct", 1_000_000, 0)
    assert cost == pytest.approx(2.76, rel=1e-3)


def test_estimate_cost_minimax_cheapest():
    cost_minimax = bench.estimate_cost_eur("minimax_openrouter", 1_000_000, 1_000_000)
    cost_anthropic = bench.estimate_cost_eur("anthropic_direct", 1_000_000, 1_000_000)
    assert cost_minimax < cost_anthropic


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_aggregate_results_shape():
    samples = [
        {"score_total": 1.0, "latency_ms": 100, "cost_eur": 0.001, "tokens_in": 50, "tokens_out": 30},
        {"score_total": 0.75, "latency_ms": 200, "cost_eur": 0.002, "tokens_in": 60, "tokens_out": 40},
        {"score_total": 1.0, "latency_ms": 150, "cost_eur": 0.0015, "tokens_in": 55, "tokens_out": 35},
    ]
    agg = bench.aggregate_results(samples)
    assert agg["count"] == 3
    assert agg["score_mean"] == pytest.approx(0.917, abs=1e-2)
    assert "latency_p95_ms" in agg
    assert "cost_per_call_eur_mean" in agg


def test_aggregate_empty_samples():
    assert bench.aggregate_results([]) == {"count": 0}


# ---------------------------------------------------------------------------
# Dry-run CLI integration
# ---------------------------------------------------------------------------


def test_bench_fixtures_cover_all_tools():
    from app.core.bench import TOOLS_TO_BENCH

    for tool in TOOLS_TO_BENCH:
        assert tool in bench._BENCH_FIXTURES, f"fixture manquante pour {tool}"
        fixture = bench._BENCH_FIXTURES[tool]
        assert "prompt" in fixture
        assert "variables" in fixture
        assert "source_values" in fixture
