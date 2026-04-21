# Provider — MiniMax M2.7 via OpenRouter

Story 10.13 Livrable B — annexe `docs/bench-llm-providers-phase0.md §3`.

## Configuration

- **Auth** : header `Authorization: Bearer sk-or-...` (OpenRouter Bearer).
- **Base URL** : `https://openrouter.ai/api/v1`.
- **Modèle bench** : `minimax/minimax-m2.7`.
- **Pricing** (2026-04-21) : ~0.46 € / 1.38 € per 1M tokens input/output
  — **6× moins cher** qu'Anthropic direct.

## Qualité observée (à compléter post-bench)

- Score total mean : _tbd_
- Latence p95 : _tbd_ ms (typiquement plus lent qu'Anthropic — hop Asie).
- Coût par appel : _tbd_ EUR (mais volume > compensation coût).

## Tics / régressions observés (piège #5)

- **Répétitions sur long contexte > 8k tokens** : observation dev lead
  baseline `.env` actuel `LLM_MODEL=minimax/minimax-m2.7`. Le modèle
  tend à répéter les phrases précédentes ou à boucler sur un concept.
  Mitigation : `max_tokens=1024` strict + timeout 60 s.
- **Cohérence FR accents variable** selon température. Privilégier
  `temperature=0.2` pour outputs structurés.
- **Conformité JSON** : moins fiable qu'Anthropic sur prompts avec
  schémas Pydantic complexes (impact axe 1 `format_valid`).

## Candidature MVP

**Non recommandé** comme provider primaire pour les tools structurés
(action_plan, executive_summary, derive_verdicts_multi_ref) malgré son
avantage coût. Candidat potentiel pour tools à faible criticité
(chat conversationnel simple) Phase Growth si coût devient contraignant.
