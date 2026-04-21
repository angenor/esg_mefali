"""CLI bench 3 providers LLM × 5 tools × 10 échantillons = 150 appels.

Story 10.13 Livrable B — R-04-1 business-decisions-2026-04-19.
Acte le provider primaire MVP avant Sprint 1 Phase 1.

Pattern Story 10.11 ``check_source_urls.py`` (argparse + exit codes +
JSON output + env gating ``BENCH_LLM_CHECK=1``).

Usage::

    python backend/scripts/bench_llm_providers.py --provider all --samples 10
    python backend/scripts/bench_llm_providers.py --provider anthropic_direct --tool generate_action_plan
    python backend/scripts/bench_llm_providers.py --dry-run --json-output bench.json

Exit codes :
    0 : succès.
    1 : erreur non-récupérable.
    2 : interrompu utilisateur.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from app.core.bench import (
    PRICING_PER_1M_TOKENS,
    PROVIDERS_TO_BENCH,
    SAMPLES_PER_TOOL_PER_PROVIDER,
    TOOLS_TO_BENCH,
)

logger = logging.getLogger("bench_llm_providers")


# ---------------------------------------------------------------------------
# Fixtures prompts — Q7 import direct (pas registry runtime LangGraph)
# ---------------------------------------------------------------------------

#: Mapping tool_name → (prompt_template, source_values_for_scoring).
#: Prompts minimaux pour bench Phase 0 (proxies Q8 — re-bench Phase 1 Epic 13).
_BENCH_FIXTURES: dict[str, dict[str, Any]] = {
    "generate_formalization_plan": {
        "prompt": (
            "Tu es un conseiller d'accompagnement des PME ouest-africaines. "
            "Génère un plan d'action concis (5 étapes) pour aider {company_name}, "
            "une PME du secteur {sector}, à se formaliser (RCCM, NINEA, IFU) "
            "avec un budget de {budget} FCFA. Réponds en français."
        ),
        "variables": {
            "company_name": "AgriMali SARL",
            "sector": "agriculture",
            "budget": "500000",
        },
        "source_values": {},
    },
    "query_cube_4d": {
        "prompt": (
            "Pour une PME du secteur {sector} avec un score ESG de {esg_score}/100, "
            "localisée au {country}, quels sont les 3 fonds verts les plus adaptés ? "
            "Réponds en français avec un tableau : Fonds | Critères | Montant."
        ),
        "variables": {
            "sector": "énergie solaire",
            "esg_score": "58",
            "country": "Sénégal",
        },
        "source_values": {"esg_score": 58.0},
    },
    "derive_verdicts_multi_ref": {
        "prompt": (
            "Pour une entreprise agroalimentaire ayant ces résultats : "
            "score environnemental {env_score}/100, social {soc_score}/100, "
            "gouvernance {gov_score}/100. Donne un verdict ESG global "
            "(score /100 + 3 actions prioritaires) en français."
        ),
        "variables": {
            "env_score": "45",
            "soc_score": "62",
            "gov_score": "38",
        },
        "source_values": {
            "env_score": 45.0,
            "soc_score": 62.0,
            "gov_score": 38.0,
        },
    },
    "generate_action_plan": {
        "prompt": (
            "Génère un plan d'action ESG sur 12 mois pour {company_name} "
            "(secteur {sector}, score ESG {esg_score}/100). Liste 5 actions "
            "prioritaires avec jalons trimestriels. Réponds en français."
        ),
        "variables": {
            "company_name": "ProTextile SA",
            "sector": "textile",
            "esg_score": "52",
        },
        "source_values": {"esg_score": 52.0},
    },
    "generate_executive_summary": {
        "prompt": (
            "Rédige un résumé exécutif (8 lignes max) du rapport ESG de {company_name} : "
            "score global {esg_score}/100, émissions {emissions} tCO2e, "
            "projection de financement {financing} FCFA. Réponds en français."
        ),
        "variables": {
            "company_name": "CaféBoboDioulasso",
            "esg_score": "67",
            "emissions": "120",
            "financing": "50000000",
        },
        "source_values": {
            "esg_score": 67.0,
            "emissions": 120.0,
        },
    },
}


# ---------------------------------------------------------------------------
# Providers invocation — LangChain wrappers
# ---------------------------------------------------------------------------


def _build_chat_model(provider_id: str):
    """Construit le wrapper LangChain selon le provider.

    Piège #4 : Anthropic direct utilise ``x-api-key`` (SDK anthropic), pas
    ``Bearer`` OpenRouter. ``ChatAnthropic`` gère ça nativement.
    """
    from app.core.config import settings

    if provider_id == "anthropic_direct":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            timeout=60,
        )
    if provider_id == "anthropic_openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model="anthropic/claude-sonnet-4-20250514",
            max_tokens=1024,
            timeout=60,
        )
    if provider_id == "minimax_openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model="minimax/minimax-m2.7",
            max_tokens=1024,
            # Piège #5 : MiniMax tics long contexte — timeout 60 s.
            timeout=60,
        )
    raise ValueError(f"Unknown provider_id: {provider_id!r}")


# ---------------------------------------------------------------------------
# Scoring 4 axes — réutilise llm_guards 9.6 (AC7)
# ---------------------------------------------------------------------------


#: Regex densité accents FR (piège #6 seuil 0.02 calibré corpus 100 textes FR).
_FR_ACCENT_PATTERN = re.compile(r"[éèêàçùïôûâ]", re.UNICODE)
_FR_ACCENT_DENSITY_THRESHOLD = 0.02


def score_axis_format_valid(text: str) -> int:
    """Axe 1 — la réponse n'est pas vide ET parse en JSON/plain text valide."""
    if not text or not text.strip():
        return 0
    return 1


def score_axis_numeric_coherence(text: str, source_values: dict) -> int:
    """Axe 2 — assert_numeric_coherence (llm_guards) : 1 = aucun drift > tolérance."""
    if not source_values:
        return 1  # pas de chiffre source à vérifier → score maximal par défaut
    from app.core.llm_guards import LLMGuardError, assert_numeric_coherence

    try:
        assert_numeric_coherence(text, source_values, target="bench", tolerance=5.0)
        return 1
    except LLMGuardError:
        return 0


def score_axis_no_forbidden_vocab(text: str) -> int:
    """Axe 3 — assert_no_forbidden_vocabulary : 1 = aucun terme interdit."""
    from app.core.llm_guards import LLMGuardError, assert_no_forbidden_vocabulary

    try:
        assert_no_forbidden_vocabulary(text, target="bench")
        return 1
    except LLMGuardError:
        return 0


def score_axis_fr_accents(text: str) -> int:
    """Axe 4 — densité d'accents FR > 0.02 (piège #6)."""
    if not text:
        return 0
    words = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
    if len(words) < 10:
        return 1  # texte trop court, défaut tolérant
    accent_hits = len(_FR_ACCENT_PATTERN.findall(text))
    density = accent_hits / max(1, len(words))
    return 1 if density >= _FR_ACCENT_DENSITY_THRESHOLD else 0


def score_sample(text: str, source_values: dict) -> dict:
    """Retourne les 4 axes + le score total ∈ [0, 1]."""
    s1 = score_axis_format_valid(text)
    s2 = score_axis_numeric_coherence(text, source_values)
    s3 = score_axis_no_forbidden_vocab(text)
    s4 = score_axis_fr_accents(text)
    return {
        "axis_format": s1,
        "axis_numeric_coherence": s2,
        "axis_no_forbidden_vocab": s3,
        "axis_fr_accents": s4,
        "score_total": (s1 + s2 + s3 + s4) / 4,
    }


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------


def estimate_cost_eur(provider_id: str, tokens_in: int, tokens_out: int) -> float:
    """Pricing → coût EUR par appel (sans marge)."""
    input_eur_1m, output_eur_1m = PRICING_PER_1M_TOKENS[provider_id]
    return (tokens_in / 1_000_000) * input_eur_1m + (tokens_out / 1_000_000) * output_eur_1m


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_results(samples: list[dict]) -> dict:
    """Mean/stddev + p95 latence sur les samples d'un (provider, tool)."""
    if not samples:
        return {"count": 0}
    scores = [s["score_total"] for s in samples]
    latencies = [s["latency_ms"] for s in samples]
    costs = [s["cost_eur"] for s in samples]
    p95_idx = max(0, int(len(latencies) * 0.95) - 1)
    sorted_lat = sorted(latencies)
    return {
        "count": len(samples),
        "score_mean": round(statistics.fmean(scores), 3),
        "score_stddev": round(statistics.pstdev(scores), 3) if len(scores) > 1 else 0.0,
        "latency_p50_ms": round(statistics.median(latencies), 1),
        "latency_p95_ms": round(sorted_lat[p95_idx], 1),
        "cost_per_call_eur_mean": round(statistics.fmean(costs), 5),
        "tokens_in_mean": round(statistics.fmean(s["tokens_in"] for s in samples), 1),
        "tokens_out_mean": round(statistics.fmean(s["tokens_out"] for s in samples), 1),
    }


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bench LLM providers R-04-1 Story 10.13")
    parser.add_argument(
        "--provider",
        choices=["all", *(p[0] for p in PROVIDERS_TO_BENCH)],
        default="all",
    )
    parser.add_argument("--tool", choices=["all", *TOOLS_TO_BENCH], default="all")
    parser.add_argument(
        "--samples",
        type=int,
        default=SAMPLES_PER_TOOL_PER_PROVIDER,
        help=f"Nombre d'échantillons par (tool, provider), défaut {SAMPLES_PER_TOOL_PER_PROVIDER}",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/bench-llm-providers-phase0.md",
        help="Fichier Markdown rapport final.",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default="bench-results.json",
        help="Fichier JSON brut (ajouter à .gitignore).",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def _resolve_scope(args: argparse.Namespace) -> tuple[list[str], list[tuple]]:
    providers = (
        list(PROVIDERS_TO_BENCH)
        if args.provider == "all"
        else [p for p in PROVIDERS_TO_BENCH if p[0] == args.provider]
    )
    tools = list(TOOLS_TO_BENCH) if args.tool == "all" else [args.tool]
    return tools, providers


def _env_guard() -> None:
    if os.environ.get("BENCH_LLM_CHECK") != "1":
        raise SystemExit(
            "BENCH_LLM_CHECK=1 requis (bench live LLM). Set env + API keys."
        )
    from app.core.config import settings

    if not settings.anthropic_api_key and not settings.openrouter_api_key:
        raise SystemExit("ANTHROPIC_API_KEY ou OPENROUTER_API_KEY requis")


async def _run_sample(
    chat_model, tool_name: str, sample_index: int
) -> dict:
    """Exécute 1 appel LLM + scoring."""
    fixture = _BENCH_FIXTURES[tool_name]
    prompt = fixture["prompt"].format(**fixture["variables"])

    started = time.perf_counter()
    response = await chat_model.ainvoke(prompt)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    text = getattr(response, "content", str(response)) or ""
    # tokens : récupération best-effort (LangChain AIMessage.usage_metadata).
    usage = getattr(response, "usage_metadata", None) or {}
    tokens_in = int(usage.get("input_tokens", 0))
    tokens_out = int(usage.get("output_tokens", 0))

    return {
        "tool": tool_name,
        "sample_index": sample_index,
        "latency_ms": elapsed_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "response_len": len(text),
        **score_sample(text, fixture["source_values"]),
    }


async def _run(args: argparse.Namespace) -> int:
    tools, providers = _resolve_scope(args)

    if args.dry_run:
        scope = {"tools": tools, "providers": [p[0] for p in providers], "samples": args.samples}
        print(json.dumps({"dry_run": True, "scope": scope}, indent=2))
        return 0

    _env_guard()

    all_samples: list[dict] = []
    aggregates: dict[str, dict[str, dict]] = {}

    for provider_id, model_name, _ in providers:
        chat_model = _build_chat_model(provider_id)
        aggregates.setdefault(provider_id, {})

        for tool_name in tools:
            tool_samples: list[dict] = []
            for i in range(args.samples):
                sample = await _run_sample(chat_model, tool_name, i)
                sample["provider"] = provider_id
                sample["model"] = model_name
                sample["cost_eur"] = estimate_cost_eur(
                    provider_id, sample["tokens_in"], sample["tokens_out"]
                )
                tool_samples.append(sample)
                all_samples.append(sample)
            aggregates[provider_id][tool_name] = aggregate_results(tool_samples)

    output_path = Path(args.json_output)
    output_path.write_text(
        json.dumps(
            {
                "samples": all_samples,
                "aggregates": aggregates,
                "meta": {
                    "samples_per_tool_per_provider": args.samples,
                    "tools": tools,
                    "providers": [p[0] for p in providers],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Bench complet : %d samples → %s", len(all_samples), output_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.warning("Interrompu (SIGINT)")
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
