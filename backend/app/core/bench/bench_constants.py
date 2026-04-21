"""Story 10.13 Livrable B — registries bench LLM providers.

Pattern CCC-9 byte-identique Story 10.8+10.10+10.11+10.12 : ``Final[tuple[...]]``
immutables + ``_validate_*`` fail-at-import si incohérence.

**Q8 tranchée — proxies Phase 0** : les 5 tools canoniques R-04-1 ne sont
pas tous livrés Phase 0 (cube 4D, formalization plan Aminata niveau 0,
derive_verdicts_multi_ref). Stratégie MVP = bench avec proxies existants
(Spec 005/006/008/011) + re-bench Phase 1 Epic 13.
"""

from __future__ import annotations

from typing import Final

#: 5 tools canoniques Phase 0 (proxies R-04-1 — cf. bench report §Scope).
#: ``generate_formalization_plan`` = proxy action_plan (Aminata N0 Phase 1).
#: ``query_cube_4d`` = proxy recommend_financing (cube 4D Phase 1 Story 13.X).
#: ``derive_verdicts_multi_ref`` = proxy derive_esg_score (3 couches Phase 1).
TOOLS_TO_BENCH: Final[tuple[str, ...]] = (
    "generate_formalization_plan",
    "query_cube_4d",
    "derive_verdicts_multi_ref",
    "generate_action_plan",
    "generate_executive_summary",
)

#: 3 providers à bencher — (id, model, base_url_setting_name).
#: L'``id`` est stable pour le JSON output + le log ``tool_call_logs``.
PROVIDERS_TO_BENCH: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "anthropic_openrouter",
        "anthropic/claude-sonnet-4-5-20251022",
        "openrouter_base_url",
    ),
    (
        "anthropic_direct",
        "claude-sonnet-4-5-20251022",
        "anthropic_base_url",
    ),
    (
        "minimax_openrouter",
        "minimax/minimax-m2.7",
        "openrouter_base_url",
    ),
)

#: Nombre d'échantillons par (tool, provider). 10 × 5 × 3 = 150 appels total.
SAMPLES_PER_TOOL_PER_PROVIDER: Final[int] = 10

#: Pricing par 1M tokens — (input_eur, output_eur).
#:
#: Snapshot : **2026-04-21** — modèle Claude Sonnet 4.6 (release 2025-10-22).
#: Taux USD→EUR 0.92 (source : ECB reference rate 2026-04-21).
#: Re-bench triggered si delta observé > 20 % (cf. §Re-bench policy
#: docs/bench-llm-providers-phase0.md).
#:
#: Sources officielles consultées 2026-04-21 :
#:   - anthropic_direct  : https://www.anthropic.com/pricing (Sonnet 4.6 : $3 / $15 per 1M)
#:   - anthropic_openrouter : https://openrouter.ai/anthropic/claude-sonnet-4.6 (+~5 % surcharge)
#:   - minimax_openrouter : https://openrouter.ai/minimax/minimax-m2.7 (~$0.50 / $1.50 per 1M)
PRICING_PER_1M_TOKENS: Final[dict[str, tuple[float, float]]] = {
    # Anthropic direct Sonnet 4.6 : $3 / $15 per 1M → ~2.76 / ~13.80 EUR.
    # Source : https://www.anthropic.com/pricing (accessed 2026-04-21)
    "anthropic_direct": (2.76, 13.80),
    # OpenRouter surcharge marginale (~5 %) : 2.90 / 14.50 EUR.
    # Source : https://openrouter.ai/anthropic/claude-sonnet-4.6 (accessed 2026-04-21)
    "anthropic_openrouter": (2.90, 14.50),
    # MiniMax m2.7 via OpenRouter : ~$0.50 / $1.50 per 1M → 0.46 / 1.38 EUR.
    # Source : https://openrouter.ai/minimax/minimax-m2.7 (accessed 2026-04-21)
    "minimax_openrouter": (0.46, 1.38),
}


# ---------------------------------------------------------------------------
# Validators import-time (fail-fast si incohérence — pattern CCC-9)
# ---------------------------------------------------------------------------


def _validate_providers_registry_unique_ids() -> None:
    """Les ``provider_id`` de ``PROVIDERS_TO_BENCH`` doivent être uniques."""
    ids = [entry[0] for entry in PROVIDERS_TO_BENCH]
    if len(ids) != len(set(ids)):
        duplicates = {x for x in ids if ids.count(x) > 1}
        raise RuntimeError(
            f"PROVIDERS_TO_BENCH: provider_id dupliqués: {duplicates}"
        )


def _validate_tools_registry_unique() -> None:
    """Les tools bench doivent être uniques."""
    if len(TOOLS_TO_BENCH) != len(set(TOOLS_TO_BENCH)):
        duplicates = {x for x in TOOLS_TO_BENCH if TOOLS_TO_BENCH.count(x) > 1}
        raise RuntimeError(f"TOOLS_TO_BENCH: tools dupliqués: {duplicates}")


def _validate_pricing_covers_all_providers() -> None:
    """Chaque provider doit avoir une entrée pricing (évite KeyError runtime)."""
    for provider_id, _, _ in PROVIDERS_TO_BENCH:
        if provider_id not in PRICING_PER_1M_TOKENS:
            raise RuntimeError(
                f"PRICING_PER_1M_TOKENS manque le provider {provider_id!r}"
            )


_validate_providers_registry_unique_ids()
_validate_tools_registry_unique()
_validate_pricing_covers_all_providers()
