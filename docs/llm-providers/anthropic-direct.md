# Provider — Anthropic direct (`api.anthropic.com`)

Story 10.13 Livrable B — annexe `docs/bench-llm-providers-phase0.md §3`.

## Configuration

- **Auth** : header `x-api-key: sk-ant-...` + `anthropic-version: 2023-06-01`.
  Piège #4 de la story — différent d'OpenRouter (`Bearer`). Géré
  nativement par `langchain_anthropic.ChatAnthropic`.
- **Base URL** : `https://api.anthropic.com/v1` (`Settings.anthropic_base_url`).
- **Modèle bench** : `claude-sonnet-4-20250514`.
- **Pricing** (2026-04-21) : ~2.76 € / 13.80 € per 1M tokens input/output
  (conversion USD→EUR 0.92).

## Qualité observée (à compléter post-bench)

- Score total mean : _tbd_
- Score stddev : _tbd_
- Latence p95 : _tbd_ ms
- Coût par appel : _tbd_ EUR

## Tics / régressions observés (à compléter)

- _tbd_

## Cas de régression vs gagnant (à compléter)

- _tbd_
