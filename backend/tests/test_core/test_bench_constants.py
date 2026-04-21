"""Tests Story 10.13 Livrable B — bench_constants CCC-9 registry."""

from __future__ import annotations

import pytest

from app.core.bench import (
    PRICING_PER_1M_TOKENS,
    PROVIDERS_TO_BENCH,
    SAMPLES_PER_TOOL_PER_PROVIDER,
    TOOLS_TO_BENCH,
)


def test_tools_to_bench_is_frozen_tuple_of_5():
    """AC9 — 5 tools canoniques Phase 0."""
    assert isinstance(TOOLS_TO_BENCH, tuple)
    assert len(TOOLS_TO_BENCH) == 5


def test_providers_to_bench_has_3_entries():
    """AC9 — 3 providers (anthropic_openrouter, anthropic_direct, minimax_openrouter)."""
    assert isinstance(PROVIDERS_TO_BENCH, tuple)
    assert len(PROVIDERS_TO_BENCH) == 3
    provider_ids = {entry[0] for entry in PROVIDERS_TO_BENCH}
    assert provider_ids == {
        "anthropic_openrouter",
        "anthropic_direct",
        "minimax_openrouter",
    }


def test_samples_per_tool_yields_150_total():
    """AC9 — 10 × 5 × 3 = 150 appels."""
    assert SAMPLES_PER_TOOL_PER_PROVIDER == 10
    assert SAMPLES_PER_TOOL_PER_PROVIDER * len(TOOLS_TO_BENCH) * len(PROVIDERS_TO_BENCH) == 150


def test_pricing_covers_all_providers():
    """Chaque provider doit avoir une entrée pricing (validator import-time)."""
    for provider_id, _, _ in PROVIDERS_TO_BENCH:
        assert provider_id in PRICING_PER_1M_TOKENS
        input_price, output_price = PRICING_PER_1M_TOKENS[provider_id]
        assert input_price > 0
        assert output_price > 0


def test_providers_registry_ids_unique():
    """Validator import-time fail-fast si duplicate."""
    from app.core.bench.bench_constants import _validate_providers_registry_unique_ids

    # Ne doit pas lever sur le registry actuel.
    _validate_providers_registry_unique_ids()


def test_pricing_minimax_cheapest():
    """Sanity check : MiniMax input < Anthropic input (constitution du bench)."""
    minimax_in, _ = PRICING_PER_1M_TOKENS["minimax_openrouter"]
    anthropic_in, _ = PRICING_PER_1M_TOKENS["anthropic_direct"]
    assert minimax_in < anthropic_in


def test_tools_to_bench_immutable():
    """CCC-9 — tuple frozen, pas de list mutable."""
    with pytest.raises((TypeError, AttributeError)):
        TOOLS_TO_BENCH.append("new_tool")  # type: ignore[attr-defined]
