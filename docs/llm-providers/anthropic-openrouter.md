# Provider — Anthropic via OpenRouter

Story 10.13 Livrable B — annexe `docs/bench-llm-providers-phase0.md §3`.

## Configuration

- **Auth** : header `Authorization: Bearer sk-or-...` (OpenRouter Bearer).
- **Base URL** : `https://openrouter.ai/api/v1` (`Settings.openrouter_base_url`).
- **Modèle bench** : `anthropic/claude-sonnet-4-20250514`.
- **Pricing** (2026-04-21) : ~2.90 € / 14.50 € per 1M tokens input/output
  (surcharge OpenRouter ~5 % vs direct).

## Qualité observée (à compléter post-bench)

- Score total mean : _tbd_
- Latence p95 : _tbd_ ms (comporte le hop OpenRouter → Anthropic, +20-50 ms typiques)
- Coût par appel : _tbd_ EUR

## Tics / régressions observés (à compléter)

- Latence marginale vs direct Anthropic (hop OpenRouter).

## Avantage fallback

OpenRouter route automatiquement vers d'autres providers si Anthropic
est indisponible. Candidate fallback primaire (cf.
`docs/bench-llm-providers-phase0.md §5`).
