# Bench LLM providers — Phase 0 (R-04-1)

**Décision** : `business-decisions-2026-04-19.md §R-04-1` — acter le
provider LLM primaire MVP avant Sprint 1 Phase 1.

**Statut** : infrastructure livrée (Story 10.13 Tasks 6-10). Exécution
effective du bench 150 échantillons = **à conduire manuellement** par
dev lead avec `BENCH_LLM_CHECK=1 + ANTHROPIC_API_KEY + OPENROUTER_API_KEY`.
Ce document fournit la méthodologie, la recommandation provisoire basée
sur pricing + heuristiques connues, et le template de résultats.

## 1. Contexte R-04-1

Décision 2026-04-19 : « Bench 3 providers × 5 tools × 10 échantillons = 150
appels scorés 4 axes pour acter le provider primaire MVP avant Sprint 1
Phase 1 ». La D10 architecture LLM Provider Layer est désormais concrétisée
(`backend/app/core/llm/provider.py` ABC + 2 impl + factory `lru_cache`).

## 2. Méthodologie

- **Providers** (3) — cf. `backend/app/core/bench/bench_constants.py`
  `PROVIDERS_TO_BENCH` :
    - `anthropic_direct` (Anthropic x-api-key, claude-sonnet-4-20250514)
    - `anthropic_openrouter` (OpenRouter Bearer, anthropic/claude-sonnet-4-20250514)
    - `minimax_openrouter` (OpenRouter Bearer, minimax/minimax-m2.7)
- **Tools Phase 0 proxies** (5, Q8 tranchée) : `generate_formalization_plan`,
  `query_cube_4d`, `derive_verdicts_multi_ref`, `generate_action_plan`,
  `generate_executive_summary`. Les 3 premiers sont proxyfiés avec des
  fixtures minimales — les tools canoniques Epic 13 Phase 1 exigeront un
  re-bench.
- **Échantillons** : 10 par (tool, provider) = 150 appels total. Fixtures
  prompts dans `scripts/bench_llm_providers.py::_BENCH_FIXTURES` (Q7 import
  direct, pas registry 10.8 runtime).
- **Scoring 4 axes** (AC7) :
    - Axe 1 — **Format valid** : réponse non vide (binaire 0/1).
    - Axe 2 — **Cohérence numérique** : `llm_guards.assert_numeric_coherence`
      tolérance 5 points.
    - Axe 3 — **Vocabulaire interdit** : `llm_guards.assert_no_forbidden_vocabulary`.
    - Axe 4 — **FR accents** : densité `[éèêàçùïôûâ]` / mots > 0.02.
    - Agrégation : `score_total = mean(axes) ∈ [0, 1]`, `mean ± stddev`
      sur 10 samples par (provider, tool).
- **Latence** : `time.perf_counter` autour de `chat_model.ainvoke(prompt)`.
  Métriques agrégées `latency_p50_ms`, `latency_p95_ms`.
- **Coût** : pricing `bench_constants.py::PRICING_PER_1M_TOKENS` (sources
  officielles consultées 2026-04-21) × tokens `usage_metadata` LangChain.

**Exécution local-only (Q5 tranchée)** — CI coûteux prohibitif Phase 0
(~6 €/run × 365 = 2 200 €/an). Re-bench déclencheur-based Phase Growth.

```bash
# Commande de référence (dev lead local, clés provisionnées)
export BENCH_LLM_CHECK=1
export ANTHROPIC_API_KEY=sk-ant-...
export OPENROUTER_API_KEY=sk-or-...
cd backend && source venv/bin/activate
python scripts/bench_llm_providers.py \
    --provider all \
    --samples 10 \
    --json-output /tmp/bench-results.json \
    --output docs/bench-llm-providers-phase0.md
```

## 3. Résultats par provider

*Template à remplir après exécution.*

| Provider              | Score mean | Stddev | Latency p95 | Cost/call €  | Rank |
|-----------------------|-----------:|-------:|------------:|-------------:|-----:|
| anthropic_direct      |    _tbd_   | _tbd_  | _tbd_ ms    | _tbd_        |  1-3 |
| anthropic_openrouter  |    _tbd_   | _tbd_  | _tbd_ ms    | _tbd_        |  1-3 |
| minimax_openrouter    |    _tbd_   | _tbd_  | _tbd_ ms    | _tbd_        |  1-3 |

## 4. Résultats par tool × provider

*Template à remplir après exécution.*

| Tool                          | anthropic_direct | anthropic_openrouter | minimax_openrouter |
|-------------------------------|-----------------:|---------------------:|-------------------:|
| generate_formalization_plan   |           _tbd_ |               _tbd_ |             _tbd_ |
| query_cube_4d                 |           _tbd_ |               _tbd_ |             _tbd_ |
| derive_verdicts_multi_ref     |           _tbd_ |               _tbd_ |             _tbd_ |
| generate_action_plan          |           _tbd_ |               _tbd_ |             _tbd_ |
| generate_executive_summary    |           _tbd_ |               _tbd_ |             _tbd_ |

## 5. Recommandation provider primaire MVP

**Recommandation provisoire (avant bench effectif)** : `anthropic_direct`
comme provider primaire MVP, `openrouter` (modèle anthropic) comme
fallback. Rationale basé sur heuristiques pré-bench :

- **Qualité FR + cohérence numérique** : Anthropic Claude Sonnet 4
  historiquement le plus fiable sur prompts FR avec contraintes structurées
  (observations dev lead sur stories 9.x). MiniMax m2.7 présente des tics
  répétitifs >8k tokens context (piège #5).
- **Coût** : `anthropic_direct` ~2.76/13.80 EUR par 1M tokens (input/output)
  vs MiniMax ~0.46/1.38 EUR. Gap 6× mais budget NFR68 500 €/mois couvre
  usage MVP (~5M tokens/mois estimé 10 PME pilotes) = ~70 €/mois Anthropic
  vs ~11 €/mois MiniMax. Anthropic reste **sous plafond** — la qualité
  prévaut sur le coût à ce volume.
- **Fallback OpenRouter anthropic** : découple la dépendance à
  l'infrastructure Anthropic directe (mitigation panne provider — NFR75).

**Provider bench winner à hardcoder post-exécution** :

```python
# backend/app/core/config.py — Settings
llm_provider: str = Field(default="anthropic_direct", pattern="^(openrouter|anthropic_direct)$")
llm_fallback_provider: str = Field(default="openrouter", pattern="^(openrouter|anthropic_direct)$")
```

## 6. Configuration finale `.env` + `LLMProvider` abstraction

Ajouts `.env` (template `.env.example` mis à jour) :

```bash
# LLM provider primaire (winner bench R-04-1)
LLM_PROVIDER=anthropic_direct
LLM_FALLBACK_PROVIDER=openrouter

# Anthropic direct
ANTHROPIC_API_KEY=<sk-ant-...>
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1

# OpenRouter fallback (existant)
OPENROUTER_API_KEY=<sk-or-...>
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
```

Le shim `backend/app/graph/nodes.py::get_llm()` peut désormais déléguer
à `get_llm_provider().get_chat_llm()` (pattern 10.6 shim byte-identique)
— wiring déféré 10.13b ou Story 13.X Phase 1 (cf. §Hors scope).

## 7. Risques & limites

1. **Échantillon 10/tool statistiquement faible** — 150 samples total ne
   permettent pas de détecter des régressions fines < 10 pts. Phase 1
   corpus MTEB multilingual subset (~50k queries) pour robustesse.
2. **Biais prompt design fixtures** — les prompts `_BENCH_FIXTURES` sont
   courts et mono-secteur. Un LLM overfitted sur ces thèmes (agriculture,
   ESG) peut surclasser artificiellement.
3. **Proxies Phase 0 vs tools canoniques Phase 1** (Q8) — re-bench
   obligatoire quand Epic 13 livre `query_cube_4d`,
   `derive_verdicts_multi_ref`, `generate_formalization_plan`.
4. **Pricing cards drift** — snapshot pricing 2026-04-21. Re-bench si
   delta > 20 % observé via `tool_call_logs.cost_usd` dashboard.
5. **Axe FR accents regex proxy** — densité `>0.02` tolérante pour textes
   courts. Biais possible envers modèles verbeux.

## 8. Re-bench policy

Re-exécuter ce bench si :

- **Pricing change** : un provider baisse/augmente de > 20 % sur input ou
  output (détectable via `tool_call_logs.cost_eur` p95 dérive).
- **Version majeure modèle** : Claude 5 release, MiniMax m3.x.
- **Dégradation qualité observée** : `tool_call_logs` score agrégé < 0.85
  sur fenêtre 7 jours (alerting Story 17.6 Phase Growth).
- **Epic 13 tools canoniques** livrés : `query_cube_4d`,
  `derive_verdicts_multi_ref`, `generate_formalization_plan` — Phase 1.

## Annexes — Détails par provider

Voir `docs/llm-providers/`.
