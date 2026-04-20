# Sprint Plan — ESG Mefali (2026-04-19)

**Auteur** : Solo Project Lead (Angenor) · **Base** : `prd.md` (71 FR + 76 NFR) · `architecture.md` (11 D + 14 CCC + 12 patterns + 10 règles) · `epics.md` (12 epics · 109 stories · checklist CQ-1..CQ-14) · `ux-design-specification.md` (25 arbitrages Q1-Q25 · 8 composants à gravité) · `business-decisions-2026-04-19.md` (8 valeurs quantifiées · R-04-1 tranché) · `implementation-readiness-report-2026-04-19.md` (statut READY-WITH-DOWNSTREAM-DEPENDENCIES).

---

## 1. Executive Summary

- **Vélocité retenue** : 12,5 points Fibonacci / sprint de 2 semaines (milieu de la fourchette solo 10-15 pts). Buffer 20 % appliqué sur stories XL/split.
- **Périmètre Phase 0 + Phase 1** : **374 points Fibonacci** au total (29 pts Epic 9 dette + 78 pts Epic 10 fondations + 5 pts 19.1 Phase 0 RAG refactor + 262 pts Phase 1 clusters/copilot/dashboard/compliance/release/19.2).
- **Nombre de sprints estimés** : **30 sprints** = ~60 semaines = ~14 mois hors congés. Phase 0 = **Sprints 0-8** (9 sprints, ~18 semaines / 4,5 mois). Phase 1 MVP = **Sprints 9-29** (21 sprints, ~42 semaines / 10 mois).
- **Go-live MVP cible** : **fin Sprint 29** (semaine 60, environ fin T+14 mois à partir du 2026-04-19 soit mi-2027-06). Trigger `SC-B-PILOTE` (15 k€ consultants ESG AO) déclenché en Sprint 27-28 (load test + pen test + audit WCAG pré-go-live).
- **Budget cumulé cap vs réels (MVP)** :
  - Infra : **1 000 €/mois × 14 mois = 14 k€** cap (NFR69, `business-decisions-2026-04-19.md`).
  - LLM : **500 €/mois × 14 mois = 7 k€** cap (NFR68). Seuils alerting 400 €/500 € dans Story 17.5.
  - Pilote : **15 k€** (consultants ESG + support + incentives PME pilotes) déclenché à go-live.
  - Audit WCAG : **4 k€** (Story 20.4, Sprint 28).
  - **Total MVP hors salaires : ~40 k€** sur 14 mois.
- **Trois risques majeurs** :
  1. **Story 13.4a moteur DSL borné Pydantic** : 5 pts estimate mais périmètre critique (DSL = cœur Cluster B ESG + Cube 4D + livrables). Risque sous-estimation → sprint entier probable. Mitigation = prototypage anticipé Sprint 14, pair-review externe via GitHub issue.
  2. **Story 10.13 Voyage + bench LLM XL 8 pts** : bench 150 échantillons × 3 providers ajoute ~2 jours au scope migration embeddings. Split 10.13a bench + 10.13b ingestion proposé. Mitigation = dans un seul sprint avec exit criteria strict.
  3. **Vélocité solo en contexte brownfield** : 18 specs livrées + 109 stories nouvelles = charge mentale élevée. Buffer 20 % + alternance front/back + checkpoint CQ-14 fin Phase 0 (Sprint 8) pour re-calibration.

---

## 2. Prérequis & Contexte

### 2.1 Vélocité et cadence

- **Cadence** : sprints de 2 semaines.
- **Vélocité cible** : **12,5 pts Fibonacci / sprint** (fourchette 10-15 tolérée sprint par sprint). Pas de parallélisation forte (solo). Swap contexte max 2 stories simultanées si indépendantes (front/back).
- **Mapping T-shirt → points** (epics.md CQ-13 — estimations indicatives ; Fibonacci) :
  - XS = 1 · S = 2 · M = 3 · L = 5 · XL = 8 · XXL = 13.
- **Convention Definition of Ready / Definition of Done** : voir Annexes C & D (checklist CQ-1..CQ-14 enforced à chaque story).

### 2.2 DAG bloquant (extrait)

```
              ┌─────────────────────────────────────────────────────┐
              │ Stories done 9.1-9.6 (rate limit, quota, OCR, ...) │  (gelées)
              └───────────────────────┬─────────────────────────────┘
                                      │
   ┌──────────────────────────────────▼──────────────────────────────────┐
   │ Cluster 1 bloquant Phase 0 — Sprint 0 (dette audit résiduelle)      │
   │                                                                     │
   │  9.7 observabilité (M/3) ──┐ BLOQUE Epic 10 (NFR38/NFR75)           │
   │  9.8 dead code (S/2)       ├── Sprint 0 : ~13 pts                   │
   │  9.11 batch carbon (S/2)   │                                         │
   │  9.14 SECTOR_WEIGHTS (S/2) ┘                                         │
   └──────────────────────────────────┬──────────────────────────────────┘
                                      │
   ┌──────────────────────────────────▼─────────────────────────────────┐
   │ Epic 10 Fondations BLOQUANTE (21 stories · 78 pts · 7-8 sprints)   │
   │                                                                    │
   │  10.1 migrations Alembic 020-027 (L/5) ─┐                           │
   │  10.5 RLS 4 tables (L/5)                ├── Sprints 1-2            │
   │  10.10 micro-Outbox (L/5)               ┘                           │
   │                                                                    │
   │  10.13 Voyage + bench (XL/8 split 10.13a/b) ─── Sprint 3            │
   │                                                                    │
   │  10.2-10.4 modules squelettes + 10.6 Storage + 10.7 envs ─ Sprint 4-5│
   │  10.8 framework prompts + 10.9 feature flag ──── Sprint 5-6         │
   │  10.11 sourcing + 10.12 audit trail ──── Sprint 6                   │
   │                                                                    │
   │  10.14-10.21 socle UI fondation (Storybook + 7 ui/ + Lucide) ─ Sprints 6-7│
   │                                                                    │
   │  19.1 RAG refactor cross-module (L/5) ──── Sprint 7                 │
   │                                                                    │
   │  9.10 + 9.12 + 9.13 + 9.15 dette résiduelle (consomment 10.10 + 19.1)│
   │        ──── Sprint 7-8 (fin Phase 0)                                │
   │                                                                    │
   │              ✋ CHECKPOINT CQ-14 re-validation estimations ── Sprint 8 │
   └──────────────────────────────────┬─────────────────────────────────┘
                                      │
   ┌──────────────────────────────────▼─────────────────────────────────┐
   │ Phase 1 MVP — Sprints 9-29 (262 pts · 21 sprints · ~10 mois)       │
   │                                                                    │
   │  Epic 11 Cluster A  (25 pts / ~2 sprints) ── Sprints 9-10         │
   │  Epic 12 Cluster A' (19 pts / ~2 sprints) ── Sprints 10-11 (parallèle A)│
   │  Epic 13 Cluster B ESG (56 pts / 5 sprints) ── Sprints 12-16       │
   │  Epic 14 Cube 4D (33 pts / 3 sprints) ── Sprints 17-19             │
   │  Epic 15 Cluster C livrables + SGES BETA (43 pts / 4 sprints) ── Sprints 20-23│
   │  Epic 16 Copilot extension (19 pts / 2 sprints) ── Sprints 24-25   │
   │  Epic 17 Dashboard + 19.2 RAG cross (22 + 5 = 27 pts / 2 sprints) ─ Sprints 25-26│
   │  Epic 18 Compliance (27 pts / 2-3 sprints) ── Sprints 26-27        │
   │  Epic 20 Release (13 pts / 1-2 sprints) ── Sprints 28-29           │
   │        │                                                           │
   │        ▼                                                           │
   │     🎯 GO-LIVE MVP fin Sprint 29 — trigger SC-B-PILOTE 15 k€        │
   └────────────────────────────────────────────────────────────────────┘
```

### 2.3 Checklist CQ-1..CQ-14 — enforcement par story

Chaque story **doit** respecter, avant passage en `review` :

- **CQ-1** : orientée capability user (pas d'epic purement technique sans valeur).
- **CQ-2** : pas de forward dependency inter-epic (DAG A → A' → B → Cube 4D → C → D respecté).
- **CQ-3** : complétable dans 1 sprint (≤ 8 pts, split si XL confirmé).
- **CQ-4** : appartenance claire à Epic 9 (dette) OU Epic 10+ (fondations/features), pas de doublon.
- **CQ-5** : FR44 SGES BETA NO BYPASS isolé en story dédiée (15.5).
- **CQ-6** : AC au format Given/When/Then avec métriques quantifiées (ex. NFR1 → « p95 ≤ 2 s »).
- **CQ-7** : pas de création BDD upfront — la migration arrive avec la première story qui l'utilise (exception docuumentée : 10.1 consolidation).
- **CQ-8** : metadata story : `fr_covered` + `nfr_covered` + `phase` + `cluster` + `estimate` + `qo_rattachees` + `depends_on`.
- **CQ-9** : chaque QO-Ax/B/C/T attribuée à un epic pour tranchage (QO-A1/A'1/A'3/A'4/A'5/B3/B4/C2/T4).
- **CQ-10** : feature flag `ENABLE_PROJECT_MODEL` retiré via Story 20.1 fin Phase 1.
- **CQ-11** : format story aligné sur `implementation-artifacts/9-x` + `spec-audits/`.
- **CQ-12** : table de traçabilité normalisée epic ↔ cluster ↔ FR ↔ NFR ↔ Risk ↔ QO.
- **CQ-13** : estimation indicative XS/S/M/L/XL/XXL.
- **CQ-14** : **jalon de re-validation estimations fin Phase 0 obligatoire** (Sprint 8).

### 2.4 Périmètre : Phase 0 vs Phase 1 vs Phase Growth

| Phase | Périmètre | Sprints | Points | Exit jalon |
|---|---|---|---|---|
| **Phase 0 Fondations** | Epic 9 dette (9.7-9.15) + Epic 10 fondations (10.1-10.21) + Epic 19.1 RAG refactor | 0-8 (9 sprints) | 112 | Checkpoint CQ-14, re-validation estimations, catalogue data-driven opérationnel, RLS activée, UI foundation Storybook-ready |
| **Phase 1 MVP** | Epics 11-18 + 19.2 + 20 | 9-29 (21 sprints) | 262 | **Go-live MVP** (pen test + load test + WCAG clean), pilote déclenché |
| **Phase Growth (hors sprint plan)** | SGES GA, ESG ext P1, Celery+Redis, S3 full, RAG 8/8, extension `en` | Post-MVP T+3 à T+12 | hors scope | Growth roadmap (non couvert ici) |

---

## 3. Sprint-by-Sprint Plan

> **Convention** : chaque sprint affiche (1) objectif, (2) stories avec ID + titre court + points + dépendances + CQ applicables prioritaires, (3) total points, (4) risques, (5) exit criteria. Buffer 20 % : stories XL/split entrent seules dans un sprint avec `<` 15 pts totaux.

---

### Sprint 0 (semaines 1-2) — Dette audit résiduelle non-bloquante

**Objectif** : solder les dettes audit "quick wins" parallélisables (pas de dépendance bloquante sur 10.x), libérer l'esprit avant le marathon Epic 10, et livrer 9.7 qui **débloque toute la Phase 0**.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **9.7** | Instrumentation `with_retry` + `log_tool_call` (9 modules tools) | 3 (M) | — | CQ-11, CQ-4 |
| **9.8** | Suppression dead code `profiling_node` + `chains/extraction.py` | 2 (S) | — | CQ-4, CQ-13 |
| **9.11** | `batch_save_emission_entries` module carbon | 2 (S) | — | CQ-6, CQ-4 |
| **9.14** | Complétion `SECTOR_WEIGHTS` 11 secteurs | 2 (S) | — | CQ-4 |
| **9.15** | Migration 7 composables frontend → `apiFetch` | 3 (M) | — | CQ-4, CQ-13 |

**Total points** : 12 (dans cible 10-15).

**Risques** :
- 9.7 touche 9 modules tools (profiling, esg, carbon, financing, credit, application, document, action_plan, chat). Risque de régression → couverture tests ≥ 85 % obligatoire (NFR60).
- 9.15 front a un test E2E Playwright "JWT expiré → redirect" sur ≥ 3 des 7 modules.

**Exit criteria** :
- [ ] 9.7 mergée → Epic 10 débloqué (CQ-11 enforcement `with_retry` + `log_tool_call` sur tous les nouveaux modules).
- [ ] 1172+ tests backend verts post-9.8 + 9.11.
- [ ] Couverture `weights.py` → 11/11 secteurs (9.14).
- [ ] Zero 500 sur session expirée dans les 7 modules frontend migrés.
- [ ] Doc `deferred-work.md` mise à jour.

---

### Sprint 1 (semaines 3-4) — Fondation schéma + RLS

**Objectif** : livrer le socle schéma Alembic (migrations 020-026 + tables transverses `prefill_drafts` + `domain_events`) et activer la RLS 4 tables sensibles. Ces 2 stories sont les prérequis durs de tous les modules Phase 1.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.1** | Migrations Alembic 020-027 (socle schéma Extension) | 5 (L) | 9.7 | CQ-7, CQ-6 |
| **10.5** | RLS PostgreSQL 4 tables sensibles + tests contournement | 5 (L) | 10.1, 9.7 | CQ-6, CQ-8 |
| **10.9** | Feature flag `ENABLE_PROJECT_MODEL` (var env + wrapper) | 2 (S) | 10.2 (stub acceptable) | CQ-10 |

**Total points** : 12.

**Risques** :
- 10.1 = 8 migrations séquentielles + 2 tables transverses. Test rollback 027 → 019 **exigé** avant Sprint 2 (NFR32 restoration trimestrielle).
- 10.5 RLS performance : benchmark avant/après exigé (AC6 ≤ 10 % dégradation p95).
- 10.9 nécessite un stub de 10.2 (routes `/api/projects/*` retournant 404 si flag `false`). Accepté comme exception CQ-7 (stub mini non coûteux).

**Exit criteria** :
- [ ] `alembic upgrade head` propre depuis état 019 → 027 idempotent.
- [ ] Test RLS cross-tenant isolation vert + log admin escape opérationnel.
- [ ] Feature flag en env, toggle DEV confirmé.
- [ ] Performance p95 queries 4 tables RLS ≤ 110 % baseline.

---

### Sprint 2 (semaines 5-6) — Micro-Outbox + StorageProvider

**Objectif** : livrer le pattern Outbox (Décision 11 + CCC-14) qui sera consommé par Stories 9.10/12.5/13.4b/15.4/17.4, et l'abstraction `StorageProvider` prérequise pour tous les modules manipulant des fichiers.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.10** | Micro-Outbox `domain_events` + worker batch 30 s (APScheduler + FOR UPDATE SKIP LOCKED) | 5 (L) | 10.1, 9.7 | CQ-6, CQ-8 |
| **10.6** | Abstraction `StorageProvider` (local + S3 EU-West-3) | 3 (M) | 9.7 | CQ-6 |
| **10.2** | Module `projects/` squelette (router + service + schemas + models + node LangGraph) | 3 (M) | 10.1, 9.7 | CQ-11 |

**Total points** : 11.

**Risques** :
- 10.10 `FOR UPDATE SKIP LOCKED` exige validation concurrent multi-replicas (documenté AC3). Tests de concurrence essentiels.
- 10.6 migration des 8 modules existants (documents, reports, applications, financing fiche, etc.) vers `storage.put()` → risque régression. Mitigation : golden tests avant/après.

**Exit criteria** :
- [ ] `domain_events` worker tourne 30 s propre en DEV + STAGING (toggle `DOMAIN_EVENTS_WORKER_ENABLED`).
- [ ] 8 modules migrés StorageProvider, tests moto verts.
- [ ] Module `projects/` avec stub `create_project` instrumenté (9.7 enforcement).

---

### Sprint 3 (semaines 7-8) — Voyage embeddings + bench LLM 3 providers (XL splitté)

**Objectif** : migrer les embeddings OpenAI → Voyage + conduire le bench R-04-1 (`business-decisions-2026-04-19.md`). XL 8 pts confirmé, **sprint entier dédié**.

> **Split recommandé** : **10.13a** (5 pts) migration embeddings + `EmbeddingProvider` abstraction + batch re-embedding + tests qualité AC1-AC8 ; **10.13b** (3 pts) bench 3 providers × 5 tools × 150 échantillons qualité + livrable `docs/bench-llm-providers-phase0.md` AC9.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.13a** | Migration embeddings OpenAI → Voyage (API + batch + qualité) | 5 (L) | 10.1, 9.6, 9.7 | CQ-6, CQ-13 |
| **10.13b** | Bench 3 providers LLM × 5 tools + recommandation finale | 3 (M) | 10.13a, 9.6 | CQ-9, CQ-12 |
| **10.21** | Setup Lucide + `EsgIcon.vue` wrapper + icônes ESG custom | 2 (S) | — | CQ-11 |

**Total points** : 10. Buffer 2,5 pts pour absorber imprévu bench.

**Risques** :
- **Bench 150 échantillons = charge manuelle significative** (scoring qualité 4 axes par échantillon). Risque dérapage bench → 2+ jours supplémentaires.
- Régression qualité Voyage vs OpenAI refusée (AC6) : si `recall@5` < baseline, rollback conservation OpenAI + fallback automatique.
- Crédits Voyage épuisés avant fin sprint → stress test budget NFR68.

**Exit criteria** :
- [ ] `EMBEDDING_PROVIDER=voyage` par défaut avec fallback OpenAI circuit breaker 60 s.
- [ ] Batch re-embedding terminé sur corpus DocumentChunk spec 004.
- [ ] `docs/bench-llm-providers-phase0.md` livré avec recommandation MVP primaire (Anthropic direct OU OpenRouter OU MiniMax) + tableau chiffré.
- [ ] Décision LLM primaire **actée** avant Sprint 4 (`business-decisions-2026-04-19.md` §R-04-1).
- [ ] Lucide + `EsgIcon.vue` opérationnels (prérequis Stories 10.17 et composants métier).

---

### Sprint 4 (semaines 9-10) — Modules squelettes + envs ségrégués

**Objectif** : livrer les 3 modules squelettes restants + l'infra 3 environnements (split potentiel 10.7a/10.7b). Ces stories conditionnent toute la Phase 1.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.3** | Module `maturity/` squelette | 3 (M) | 10.1, 9.7, 10.2 | CQ-11 |
| **10.4** | Module `admin_catalogue/` squelette (backend + UI admin UI-only, sans `admin_node`) | 5 (L) | 10.1 | CQ-4, CQ-11 |
| **10.7** | Environnements DEV/STAGING/PROD ségrégués + pipeline anonymisation | 5 (L) | 10.1, 10.6 | CQ-6 |

**Total points** : 13.

**Risques** :
- **10.7 estimate L avec risque XL** (noté dans epics.md). Si IAM/AWS/secrets Manager traînent, split 10.7a envs ségrégués (L) + 10.7b pipeline anonymisation (M) reporté Sprint 5.
- 10.4 = 2 sous-livrables (backend state machine N1/N2/N3 + UI admin squelette). Risque dépassement si Reka UI pas maîtrisé → priorité backend, UI minimal.

**Exit criteria** :
- [ ] 3 modules squelettes en place avec `with_retry`/`log_tool_call` enforced (CQ-11).
- [ ] DEV/STAGING/PROD isolés, secrets différenciés, approvals CI/CD enforcés.
- [ ] `copy-prod-to-staging.sh` opérationnel avec anonymisation PII déterministe.
- [ ] STAGING minimal t3.micro en ligne avec job `explain-hotpaths.yml`.

---

### Sprint 5 (semaines 11-12) — Framework prompts + audit trail + sourcing

**Objectif** : livrer les 3 stories transverses catalogue (framework prompts CCC-9 + sourcing Annexe F + audit trail). Prérequis dur à l'Epic 13 (ESG) qui publiera les premiers référentiels.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.8** | Framework d'injection unifié de prompts (CCC-9) | 5 (L) | 9.7 | CQ-6 |
| **10.11** | Sourcing documentaire Annexe F + CI nightly `source_url` HTTP 200 | 3 (M) | 10.1 | CQ-9 |
| **10.12** | Audit trail catalogue (migration 026 + endpoints admin) | 3 (M) | 10.1, 10.4 | CQ-6, CQ-14 |

**Total points** : 11.

**Risques** :
- 10.8 refactor des 9 modules `prompts/*.py` → golden tests exigés (AC6 snapshots identiques ou supérieurs). Risque régression sémantique.
- 10.11 sourcing manuel 22+ sources Annexe F = charge documentaire pure. Sprint doit inclure ~1 jour de lecture docs GCF/FEM/BOAD/IFC/etc. pour extraire URLs + dates ISO.

**Exit criteria** :
- [ ] Registry `INSTRUCTION_REGISTRY` opérationnel, 9 prompts consommant `build_prompt()`.
- [ ] Catalogue seedé avec 22+ sources (FR62 enforcé : DRAFT sans `source_url` → publication bloquée).
- [ ] CI nightly `source_url_health_check.yml` opérationnelle (NFR40 alerting).
- [ ] `admin_catalogue_audit_trail` append-only (trigger PostgreSQL) + endpoint `/api/admin/catalogue/audit-trail` testé pen-test proofing (AC5).

---

### Sprint 6 (semaines 13-14) — Socle UI fondation I (Storybook + Button + Input + Badge)

**Objectif** : démarrer le socle UI (stories 10.14-10.17) pour débloquer Phase 1 composants métier. Stories P0 UX.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.14** | Setup Storybook partiel + 6 stories à gravité | 5 (L) | 10.8 | CQ-8, CQ-12 |
| **10.15** | `ui/Button.vue` 4 variantes primary/secondary/ghost/danger | 2 (S) | — | CQ-11 |
| **10.16** | `ui/Input.vue` + `ui/Textarea.vue` + `ui/Select.vue` | 3 (M) | — | CQ-11 |
| **10.17** | `ui/Badge.vue` tokens sémantiques (lifecycle FA + verdicts ESG + admin) | 2 (S) | 10.21 | CQ-6 |

**Total points** : 12.

**Risques** :
- 10.14 Storybook + axe-core addon : configuration cross-platform (Vite + Vue 3). Risque d'installation/debug initial. Mitigation : reprendre template officiel `@storybook/vue3-vite`.
- Les 6 stories à gravité dans 10.14 ne sont que des **stubs interactifs** à cette étape (les composants métier complets seront livrés en Phase 1). AC3 = états UX Step 11 section Custom Components.

**Exit criteria** :
- [ ] `npm run storybook` démarre sur 6006, 6 stories à gravité visibles.
- [ ] `npm run storybook:test` vert (axe-core 0 violation sur chaque story).
- [ ] `ui/Button` + `ui/Input` + `ui/Textarea` + `ui/Select` + `ui/Badge` en prod, coverage ≥ 85 %.
- [ ] Dark mode rendu correct + touch targets ≥ 44 px.

---

### Sprint 7 (semaines 15-16) — Socle UI fondation II + RAG refactor (début fin Phase 0)

**Objectif** : finaliser la chaîne UI fondation (Drawer/Combobox/Tabs/DatePicker) + livrer l'abstraction RAG cross-module (19.1) prérequise à Story 9.13 + Epic 19.2.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **10.18** | `ui/Drawer.vue` wrapper Reka UI Dialog (variant side) | 3 (M) | — | CQ-11 |
| **10.19** | `ui/Combobox.vue` + `ui/Tabs.vue` wrappers Reka UI | 3 (M) | — | CQ-11 |
| **10.20** | `ui/DatePicker.vue` | 3 (M) | 10.16, 10.21 | CQ-11 |
| **19.1** | Socle RAG refactor — abstraction `RagService` réutilisable cross-module | 5 (L) | 10.13a | CQ-6, CQ-14 |

Wait, total = 14 pts, limite haute. Accepté (buffer minimal).

Actually reconsidering: 19.1 Phase 0 dépend de 10.13 Voyage. Acceptable Sprint 7.

**Total points** : 14.

**Risques** :
- 10.20 DatePicker accessibilité clavier (WAI-ARIA Date Picker Dialog pattern) est la story UI fondation la plus complexe. Risque dérapage. Si ≥ 1 j supplémentaire → reporter à Sprint 8.
- 19.1 RAG refactor est **non trivial** (factoriser `search_similar_chunks`, chunking + embedding + citation standardisé sur 2 modules démo : ex. documents + reports). Mitigation : test sur corpus existant spec 004 + Voyage (10.13) déjà en place.

**Exit criteria** :
- [ ] Drawer/Combobox/Tabs/DatePicker en prod, tests Vitest + axe-core verts.
- [ ] `RagService` abstraction prête, 2 modules pilotes consomment (preuve réutilisabilité pour 9.13 + 19.2).
- [ ] Citations source standardisées (format `nom_fichier:page/chunk`).

---

### Sprint 8 (semaines 17-18) — Fin Phase 0 : queue async + chat PDF + RAG applications + ✋ checkpoint CQ-14

**Objectif** : livrer les 3 stories dette qui dépendent de 10.10 et 19.1 (9.10, 9.12, 9.13). Fin de Phase 0. **Checkpoint CQ-14 re-validation estimations** à organiser en fin de sprint.

| Story | Titre | Points | Dépendances | CQ prioritaires |
|---|---|---|---|---|
| **9.10** | Queue async `BackgroundTask` + micro-Outbox (migration 3 endpoints longs) | 8 (XL) | 10.10, 9.7 | CQ-3, CQ-14 |
| **9.12** | FR-019 notification chat PDF + `REPORT_TOOLS` LangChain | 3 (M) | 9.10, 9.7 | CQ-4 |
| **9.13** | FR-005 RAG documentaire applications | 3 (M) | 19.1, 10.13 | CQ-4, CQ-14 |

**Total points** : 14. Pas de buffer, mais les 3 stories se chaînent logiquement (9.12 consomme 9.10 qui consomme 10.10).

**Risques** :
- **9.10 XL 8 pts** : migration de 3 endpoints synchrones (`reports/service.py` PDF ESG + `action_plan/service.py` LLM plan + `applications/service.py` dossier). **Sprint entier probable** si régression. Split envisagé à trancher en dev-story : 9.10a reports (M/3) + 9.10b action_plan (M/3) + 9.10c applications (M/3) → 3 sprints → reporter 9.12/9.13 Sprint 9. **Décision** : garder XL 8 pts en un seul sprint avec buffer 20 % si les 3 endpoints suivent le même pattern.
- **Checkpoint CQ-14** : si vélocité Phase 0 (9 sprints × 12,5 = 112,5 pts) a dérapé > 20 %, re-estimer Phase 1.

**Exit criteria Phase 0** :
- [ ] **9 stories dette Epic 9** toutes `done` (9.7→9.15).
- [ ] **21 stories Epic 10 Fondations** toutes `done`.
- [ ] **Story 19.1 RAG refactor** `done`.
- [ ] **Checkpoint CQ-14 tenu** : tableau re-estimation Phase 1 publié avec mise à jour points si drift > 20 %.
- [ ] Documentation `docs/CODEMAPS/` à jour (architecture, rag, frontend).
- [ ] Budget cumulé infra/LLM réel vs 1000 €/500 €/mois comparé (3 mois Phase 0 déjà passés).
- [ ] Runbook Phase 1 ready (ordre Epic 11 → 12 → 13 → 14 → 15 → 16 → 17/19.2 → 18 → 20).

**🎯 Milestone Phase 0 END — Sprint 8 fin, semaine 18, ~4,5 mois depuis kickoff.**

---

### Sprint 9-10 (semaines 19-22) — Epic 11 Cluster A : PME porteuse de projets multi-canal

**Objectif** : livrer le Cluster A (FR1-FR10 + FR67). Racine du data model système.

#### Sprint 9

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **11.1** | Création Company avec profil de base | 3 (M) | Epic 10 | CQ-9 (QO-A1) |
| **11.2** | Invitation collaborateurs (editor/viewer/auditor) + révocation | 3 (M) | 11.1 | CQ-6 |
| **11.3** | Création/MAJ Project avec cycle de vie | 3 (M) | 11.1, 10.9 | CQ-10 |
| **11.8** | Auditor time-bounded scoping sur Company | 2 (S) | 11.2 | CQ-6 |

**Total points** : 11. Exit : Company + Project + collaborateurs + auditor opérationnels.

#### Sprint 10

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **11.4** | Project porté solo OU consortium via `ProjectMembership` | 3 (M) | 11.3 | CQ-6 |
| **11.5** | Admin ajoute nouveau `project-membership role` via N2 | 3 (M) | 10.4, 11.4 | CQ-11 |
| **11.6** | `BeneficiaryProfile` sur membres du projet | 3 (M) | 11.4 | CQ-6 |
| **11.7** | Bulk-import CSV/Excel bénéficiaires (Moussa 152 producteurs) | 5 (L) | 11.6, 10.6 | CQ-6 |

**Total points** : 14. Buffer serré. Risque 11.7 (CSV/Excel validation per-row) — split possible 11.7a validation (M) + 11.7b import (S) si dérapage.

**Exit criteria Epic 11** :
- [ ] Journey 2 Moussa bulk import 152 producteurs testable en DEV.
- [ ] RLS vérifiée cross-tenant (11.1 AC4).
- [ ] QO-A1 tranchée (FK Project.company_id NOT NULL — 11.1 AC5).
- [ ] Test a11y manuel PME path (clarification_2 UX : tests lecteurs d'écran post-epic).

---

### Sprint 11 (semaines 23-24) — Epic 12 Cluster A' : Maturité administrative graduée

**Objectif** : livrer le Cluster A' (FR11-FR16). Parcours Aminata niveau 0 → FormalizationPlan chiffré XOF → OCR validation.

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **12.1** | Auto-déclaration niveau maturité (4 niveaux) | 2 (S) | 11.1, 10.3 | CQ-6 |
| **12.2** | Validation OCR justificatifs (RCCM, NINEA, bilans) | 3 (M) | 12.1, 10.6, 9.4 | CQ-9 (QO-A'1) |
| **12.3** | Génération `FormalizationPlan` XOF + durée + coordonnées | 5 (L) | 12.1, 10.3 | CQ-9 (QO-A'3/A'4) |
| **12.4** | Suivi `FormalizationPlan` étape par étape avec preuves | 3 (M) | 12.3, 12.2 | CQ-6 |

**Total points** : 13.

**Risques** :
- **12.3 FormalizationPlan** : LLM génère `default_steps: JSONB` 4 étapes MVP (coordonnées pays-driven via `AdminMaturityRequirement`). Risque coût LLM élevé si génération non cachée. Mitigation : cache par `(country, level_from, level_to)`.
- OCR 12.2 seuil 0,8 + fallback `pending_human_review` (QO-A'1 tranché).

**Exit criteria** :
- [ ] Aminata niveau 0 → plan chiffré 100-150 k FCFA + tribunal commerce + caisse sociale en < 3 s p95.
- [ ] OCR bilingue fra+eng (spec 9.4 consommée) confiance ≥ 0,8 auto, < 0,8 `pending_human_review`.
- [ ] Tests a11y manuel Epic 12.

---

### Sprint 12 (semaines 25-26) — Fin Epic 12 + débuts Epic 13 Cluster B ESG

**Objectif** : clôturer Epic 12 (12.5 + 12.6) et démarrer Epic 13 (13.1 + 13.2 facts + evidence).

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **12.5** | Auto-reclassification niveau après validation justificatifs | 3 (M) | 12.4, 10.10, 10.12 | CQ-9 (QO-A'5) |
| **12.6** | Admin maintien `AdminMaturityRequirement` par pays | 3 (M) | 10.4, 10.11, 10.12 | CQ-11 |
| **13.1** | Enregistrement faits atomiques quanti + quali avec evidence | 5 (L) | Epic 10, 10.6, 9.7 | CQ-6 |

**Total points** : 11.

**Exit criteria Epic 12 + transition B** :
- [ ] FR11-FR16 100 % verts (audit trail, auto-reclassif, admin maintenance country).
- [ ] UEMOA/CEDEAO francophone couvert pays cible (SN/CI prioritaires — `business-decisions-2026-04-19.md` SC-B1).
- [ ] 13.1 facts storage opérationnel (RLS enforced).

---

### Sprints 13-16 (semaines 27-34) — Epic 13 Cluster B ESG multi-contextuel 3 couches

**Objectif** : livrer le cluster B (FR17-FR26). **Bloc le plus complexe** : DSL borné Pydantic (13.4a), matérialisation verdicts (13.4b), admin catalogue 3 niveaux (13.8a/b/c), Journey 3 Akissi vue comparative (13.10), property-based tests (13.11).

#### Sprint 13 (semaines 27-28) — Evidence + versioning

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **13.2** | Evidence multi-type (doc, vidéo CLIP, déclaration honneur, signature témoin) | 5 (L) | 13.1, 10.6 | CQ-6 |
| **13.3** | Versioning temporel faits (`valid_until` + historique) | 3 (M) | 13.1 | CQ-6 |
| **13.11** | Tests property-based Hypothesis non-contradiction verdicts (SC-T6) | 3 (M) | 13.4a, 13.4b | CQ-9 |

Wait, 13.11 depends on 13.4a/b. Move to Sprint 15.

Reorganization:
- Sprint 13 : 13.2 (5) + 13.3 (3) + prepare 13.4a scaffolding = **8 pts + prep** → under-capacity, ajouter 13.6 (pack selector, 3 pts) mais dépend de 13.4a. **Accept 8 pts Sprint 13 volontairement court** pour anticiper prototypage 13.4a DSL.

#### Sprint 13 (revu) — Evidence + versioning + prototypage 13.4a DSL

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **13.2** | Evidence multi-type | 5 (L) | 13.1, 10.6 | CQ-6 |
| **13.3** | Versioning temporel faits | 3 (M) | 13.1 | CQ-6 |
| **13.4a (prep)** | **Prototypage DSL borné Pydantic** (PoC non livré, spike technique 3 jours) | hors points | — | CQ-3 mitigation risque |

**Total points livrés** : 8. Spike technique consomme ~20 % temps.

#### Sprint 14 (semaines 29-30) — Moteur DSL borné + matérialisation verdicts (risque majeur)

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **13.4a** | Moteur DSL borné Pydantic — exécution d'une rule sur un jeu de facts | 5 (L) | 13.1, 10.4 | CQ-9 (QO-B3) |
| **13.4b** | Matérialisation `ReferentialVerdict` + invalidation via Outbox | 3 (M) | 13.4a, 10.10 | CQ-6 |
| **13.5** | Traçabilité verdict → facts + rules (justification auditable) | 3 (M) | 13.4a, 13.4b | CQ-6 |

**Total points** : 11.

**Risques majeur Sprint 14** :
- **13.4a moteur DSL** : user note « risque sprint entier ». Spike prototypage Sprint 13 doit valider la faisabilité. Si bloquant → isoler en sprint 14 dédié (5 pts seul) + décaler 13.4b/13.5 Sprint 15.
- `N/A` explicite sur fact manquant/expiré (QO-B3 tranché) = cœur sémantique.

#### Sprint 15 (semaines 31-32) — Packs + scoring global + property-based tests

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **13.6** | Sélection Pack (IFC Bancable / EUDR-DDS / Artisan Minimal) | 3 (M) | 13.4a/b, 10.4 | CQ-9 (QO-B4 STRICTEST WINS) |
| **13.7** | Score ESG global pondéré + drill-down + migration SECTOR_WEIGHTS → BDD | 5 (L) | 13.4b, 9.14 | CQ-6 |
| **13.11** | Tests property-based Hypothesis non-contradiction verdicts | 3 (M) | 13.4a/b | CQ-9 |

**Total points** : 11.

**Exit criteria Sprint 15** :
- [ ] Score global calculable sur 3-5 référentiels actifs en ≤ 30 s p95 (NFR2).
- [ ] 9.14 `SECTOR_WEIGHTS` migré vers table BDD (feeds_into Epic 13 explicite).
- [ ] Hypothesis SC-T6 property-based tests verts.

#### Sprint 16 (semaines 33-34) — Admin catalogue ESG 3 workflows + vue comparative

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **13.8a** | Scaffolding admin catalogue ESG + CRUD `FactType`/`Criterion` N1 | 5 (L) | 10.4, 10.11, 10.12 | CQ-6 |
| **13.8b** | Workflow N2 peer review `Pack` + `Rule` (2e admin + threaded comments) | 5 (L) | 13.8a, 13.4a | CQ-6 |
| **13.10** | Vue comparative scoring multi-référentiels (Journey 3 Akissi) | 3 (M) | 13.4b, 13.6, 13.7 | CQ-6 |

**Total points** : 13.

> **Note** : 13.8c (workflow N3 `Referential` + `ReferentialMigration` + ImpactProjectionPanel + test rétroactif ≥ 50 snapshots + seuil 20 %) et 13.9 reportés Sprint 19 (Epic 14 en cours) pour étaler la charge admin catalogue. Cela **ne bloque pas** Cube 4D (14.x) qui consomme 13.4b + 13.6 livrés ici.

**Exit criteria Epic 13 partiel (Sprint 16)** :
- [ ] FR17-FR23 + FR24 partiel + FR26 livrés.
- [ ] Journey 3 Akissi vue comparative opérationnelle (FR26).
- [ ] 13.8c + 13.9 reportés Sprint 19 (FR24 complet + FR25).
- [ ] Test a11y manuel post-epic.

---

### Sprints 17-19 (semaines 35-40) — Epic 14 Cube 4D Matching projet-financement

**Objectif** : livrer le Cube 4D + lifecycle `FundApplication` (FR27-FR35). Intégré avec 13.8c + 13.9 Sprint 19.

#### Sprint 17 (semaines 35-36) — Projection + cube matcher + voie d'accès

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **14.1** | `CompanyProjection` — vue curée par Fund ciblé | 3 (M) | 11.1, 10.4, spec 008 Fund | CQ-6 |
| **14.2** | Query cube 4D matcher (project × company × referentials × access route) | 5 (L) | Epic 10 GIN, Epic 11, 12, 13 | CQ-6 |
| **14.3** | Affichage voie d'accès (directe OU intermédiée avec prerequisites) | 3 (M) | 14.2, 10.11 | CQ-6 |

**Total points** : 11.

**Risque** : 14.2 performance NFR1 (≤ 2 s p95 cache tiède). Indexes GIN AR-D4 livrés 10.1. EXPLAIN sur hot paths vérifié 10.7 AC7.

#### Sprint 18 (semaines 37-38) — Critères intermédiaires + FundApplication création/multi + lifecycle

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **14.4** | Critères intermédiaire superposés aux critères Fund | 3 (M) | 14.3, 13.4 | CQ-6 |
| **14.5** | Création `FundApplication` ciblant Fund + voie d'accès | 3 (M) | 14.3 | CQ-6 |
| **14.6** | Multiples `FundApplication` sur même Project sans duplication | 2 (S) | 14.5 | CQ-6 |
| **14.7** | Lifecycle `FundApplication` (draft → submitted → in_review → accepted/rejected/withdrawn) | 5 (L) | 14.5, Epic 15 pour snapshot/signed/exported | CQ-6 |

**Total points** : 13.

**Dépendance** : 14.7 a besoin d'Epic 15 partiel pour `snapshot_frozen` + `signed` + `exported`. Livraison Sprint 20+ Epic 15 livrera les pièces manquantes. 14.7 livre les 4 états `draft/submitted/in_review/accepted-rejected-withdrawn` ici, les 3 autres en Sprint 20-21 via 14.7.ext.

#### Sprint 19 (semaines 39-40) — Remédiation + notification + admin Fund + fin Epic 13 (13.8c + 13.9)

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **14.8** | Archive `FundApplication` rejeté + remédiation (Journey 4 Ibrahim) | 3 (M) | 14.7, 14.2 | CQ-6 |
| **14.9** | Notification user changement referential/pack/criterion + choix stay/migrate | 3 (M) | 13.9, 10.10 | CQ-6 |
| **14.10** | Admin met à jour Fund/Intermediary/Liaison temps réel (N1) | 3 (M) | 10.4, 10.11, 10.12 | CQ-11 |
| **13.8c** | Workflow N3 `Referential` + `ReferentialMigration` + ImpactProjectionPanel + test rétroactif ≥ 50 snapshots + seuil 20 % | 5 (L) | 13.8b | CQ-6, CQ-9 |
| **13.9** | Publication nouvelle version Referential + `ReferentialMigration` | 3 (M) | 13.8c | CQ-6 |

**Total points** : 17. **Dépassement buffer 15 pts.** Re-priorisation :

- Garder Sprint 19 à 14 pts max : 14.8 (3) + 14.9 (3) + 13.8c (5) + 13.9 (3) = 14 pts. **14.10 reporté Sprint 20**.

**Total Sprint 19 révisé** : 14 pts.

**Exit criteria Epic 14 (Sprint 20 finalisation)** :
- [ ] FR27-FR35 livrés avec 14.10 Sprint 20.
- [ ] Epic 13 complet (FR17-FR26 + FR24/FR25 via 13.8c/13.9).
- [ ] Journey 4 Ibrahim (refus + remédiation) E2E testable.
- [ ] ImpactProjectionPanel (composant à gravité UX Q11) opérationnel.

---

### Sprints 20-23 (semaines 41-48) — Epic 15 Cluster C Moteur livrables + SGES BETA

**Objectif** : livrer les livrables PDF/DOCX bailleur-compliant + **FR44 SGES BETA NO BYPASS** (CQ-5).

#### Sprint 20 (semaines 41-42) — Template engine PDF + 14.10 report

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **14.10** | Admin Fund/Intermediary/Liaison N1 (reporté Sprint 19) | 3 (M) | 10.4, 10.11, 10.12 | CQ-11 |
| **15.1a** | Template engine PDF (Jinja2 + WeasyPrint + templates relationnels DB-driven) | 5 (L) | Epic 10 migration 023 + StorageProvider | CQ-6 |
| **15.1b** | Intégration guards LLM (9.6) + BackgroundTask async (9.10) + validation perf NFR3/NFR4 | 5 (L) | 15.1a, 9.10, 9.6, 10.8 | CQ-6 |

**Total points** : 13.

#### Sprint 21 (semaines 43-44) — DOCX + evidence annexes + signature + blocage >50k

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **15.2** | Génération DOCX éditable parallèle du PDF | 3 (M) | 15.1 | CQ-6 |
| **15.3** | Annexe automatique des evidence (mode sélectif) | 3 (M) | 15.1, 13.2 | CQ-6 |
| **15.6** | Attestation électronique user obligatoire avant export (signature checkbox + modal) | 3 (M) | 15.1, step-up MFA Epic 18 stub | CQ-5 |
| **15.7** | Blocage export > 50 000 USD sans review section-par-section | 3 (M) | 15.1 | CQ-6 |

**Total points** : 12.

**Composants à gravité livrés** : `SignatureModal` (15.6), `SectionReviewCheckpoint` (15.7). Storybook `/Gravity/SignatureModal` complet (10.14 stub devenu full).

#### Sprint 22 (semaines 45-46) — Snapshot + calibration voie + **SGES BETA NO BYPASS (XL)**

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **15.4** | Snapshot cryptographique `FundApplication` au moment génération (hash immuable) | 5 (L) | 15.1, 10.10, 10.12 | CQ-6 |
| **15.8** | Calibration livrable par voie d'accès (direct vs intermédiaire Moussa) | 3 (M) | 15.1, 14.3 | CQ-6 |
| **15.5** | **SGES/ESMS BETA workflow revue humaine consultant NO BYPASS + verrou applicatif** | 8 (XL) | 15.1, 15.4, 10.12 | **CQ-5 (story dédiée)** |

**Total points** : 16. **Dépassement 1 pt.** Accept — 15.5 critique CQ-5, pas de split possible.

**Risques Sprint 22** :
- **15.5 XL** : implémentation workflow bloquant + tentatives bypass loggées incident sécurité. Pas d'admin bypass (même `admin_super`). Seul retrait BETA = Phase 2 GA. Sprint entier de facto.
- 15.4 snapshot cryptographique = hash + immutabilité + audit trail.

**Exit criteria Sprint 22** :
- [ ] SGES BETA banner `SgesBetaBanner` (composant à gravité) en prod.
- [ ] NO BYPASS enforcé applicatif + logs incident.
- [ ] Snapshot hash + domain_events atomicité vérifiée.

#### Sprint 23 (semaines 47-48) — Admin catalogue livrables + ajustements Epic 15

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **15.9** | Admin gère catalogue `DocumentTemplate` + `ReusableSection` + `AtomicBlock` (N2) | 5 (L) | 10.4, 10.11, 10.12, 13.8b | CQ-11 |
| **14.7.ext** | Extension `FundApplication` lifecycle `snapshot_frozen` + `signed` + `exported` via Epic 15 livré | 2 (S) | 15.4, 15.6 | CQ-6 |

**Total points** : 7. Sous-capacité → ajouter 2 stories Epic 16 Copilot à démarrer :

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **16.1** | Enregistrement tools nouveaux modules dans `chat_node` | 5 (L) | 9.7, Epic 10, Epic 11-15 tools | CQ-6 |

**Total révisé Sprint 23** : 12 pts.

**Exit criteria Epic 15** :
- [ ] FR36-FR44 livrés (dont FR44 SGES BETA NO BYPASS).
- [ ] Livrables GCF / IFC AIMM / EUDR DDS / Proparco AIMM / SGES BETA Phase 1 testables.
- [ ] Snapshot cryptographique immuable (rétention 10 ans SGES).
- [ ] Test a11y manuel post-epic.

---

### Sprints 24-25 (semaines 49-52) — Epic 16 Copilot extension + Epic 17 début

**Objectif** : étendre le Copilot (FR45-FR50) aux nouveaux modules + démarrer Dashboard.

#### Sprint 24 (semaines 49-50) — Copilot cross-turn + widgets + guided tours

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **16.2** | Extension `ConversationState` avec `active_project` cross-turn | 3 (M) | 16.1, spec 013 | CQ-6 |
| **16.3** | Extension widgets interactifs aux nouveaux modules | 3 (M) | 16.1, spec 018 | CQ-6 |
| **16.4** | Extension guided tours aux parcours Epic 11-15 | 3 (M) | 16.1, spec 019, Epic 11-15 UI | CQ-6 |
| **16.5** | Fallback gracieux manual input quand LLM échoue | 3 (M) | 16.1 | CQ-6 |
| **16.6** | Reprise conversation interrompue depuis checkpoint LangGraph MemorySaver | 2 (S) | 16.1 | CQ-6 |

**Total points** : 14.

**Exit Epic 16** :
- [ ] FR45-FR50 verts.
- [ ] `prefill_drafts` consommée par 16.5 (table livrée 10.1 AC7).
- [ ] Test a11y manuel post-epic.

#### Sprint 25 (semaines 51-52) — Dashboard PME étendu + Drill-down + multi-projets

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **17.1** | Dashboard PME étendu avec nouveaux blocs (projets/maturité/ESG/matching/livrables) | 5 (L) | Epic 11-15 livrés, module 011 existant | CQ-6 |
| **17.2** | Drill-down score global ESG → verdicts par référentiel | 3 (M) | 13.4b, 13.5, 13.10 | CQ-6 |
| **17.3** | Dashboard multi-projets (Journey 2 Moussa COOPRACA) | 3 (M) | 17.1, Epic 11 | CQ-6 |
| **19.2** | Intégration `RagService` aux modules cross-functional (carbon + credit + action_plan) | 5 (L) | 19.1, 9.13 | CQ-6 |

**Total points** : 16. Dépassement 1 pt → 19.2 reporté Sprint 26.

**Total révisé Sprint 25** : 11 pts.

---

### Sprint 26 (semaines 53-54) — Fin Epic 17 + RAG cross-module + début Epic 18

**Objectif** : finaliser Dashboard + monitoring admin + RAG 5 modules (FR70 promesse PRD).

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **17.4** | Reminders in-app (deadlines bailleur, renouvellement, facts, référentiel, formalisation) | 3 (M) | 10.10, 12.x, 13.x, 14.x | CQ-6 |
| **17.5** | Dashboard monitoring admin (p95 tools, guards, couverture catalogue, budget LLM) | 5 (L) | 9.7, 10.10, 10.11 | CQ-6 |
| **17.6** | Alerting anomalies (échec guards, retry anormal, source_url, budget, circuit breaker) | 3 (M) | 17.5, 10.11 | CQ-6 |
| **19.2** | Intégration RAG cross-module (reporté Sprint 25) | 5 (L) | 19.1, 9.13 | CQ-6 |

**Total points** : 16. Dépassement. Arbitrage : garder 19.2 (5 pts bloque NFR43 + FR70 ≥ 5 modules) + 17.4 (3) + 17.5 (5) = 13 pts. **17.6 reporté Sprint 27**.

**Total révisé Sprint 26** : 13 pts.

**Exit Epic 17 partiel + Epic 19 complet** :
- [ ] FR51-FR55 livrés (17.6 Sprint 27 clôt FR56).
- [ ] FR70 ≥ 5 modules (9.13 applications + 19.2 carbon + credit + action_plan + documents).
- [ ] Budget LLM observabilité opérationnelle (17.5 consomme alerting 400/500 €).

---

### Sprint 27 (semaines 55-56) — Epic 18 Compliance/Security + fin Epic 17

**Objectif** : livrer les garanties compliance + sécurité PME (anonymisation PII, MFA, chiffrement, droit effacement, export portabilité, password reset, audit trail).

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **17.6** | Alerting anomalies (reporté Sprint 26) | 3 (M) | 17.5, 10.11 | CQ-6 |
| **18.1** | Pipeline anonymisation PII systématique avant LLM + audit annuel | 5 (L) | 10.8 | CQ-6 |
| **18.2** | Chiffrement at rest KMS sur tables/buckets sensibles | 3 (M) | 10.6, 10.7 | CQ-6 |
| **18.3** | MFA `admin_mefali`/`admin_super` + step-up MFA actions à risque | 5 (L) | Epic 10 | CQ-6 |

**Total points** : 16. Dépassement 1 pt. Arbitrage : 17.6 (3) + 18.1 (5) + 18.3 (5) = 13 pts. **18.2 reporté Sprint 28**.

**Total révisé Sprint 27** : 13 pts.

---

### Sprint 28 (semaines 57-58) — Fin Epic 18 + Release engineering début

**Objectif** : finaliser compliance (18.4/18.5/18.6/18.7) + audit WCAG externe + pen test lancé en parallèle.

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **18.2** | Chiffrement at rest KMS (reporté Sprint 27) | 3 (M) | 10.6, 10.7 | CQ-6 |
| **18.4** | Droit à l'effacement — soft delete + purge différée 30-90 j + snapshots préservés | 5 (L) | Epic 10, 15.4 | CQ-6 |
| **18.5** | Export data portability JSON + CSV optionnel | 3 (M) | 10.6, 9.10 | CQ-6 |
| **20.4** | Audit accessibilité WCAG AA externe (prestataire FR/EU) | 3 (M) | Epic 11-17 UI livrées | CQ-14 |

**Total points** : 14.

**Externalisation Sprint 28** :
- **Story 20.4** : déclenchement contrat audit WCAG externe 4 k€ (`business-decisions-2026-04-19.md`). Scope = 5 journeys personas + 8 composants à gravité Storybook. Durée audit externe ~2-3 semaines, livrable rapport + re-test post-corrections en Sprint 30 (post-MVP).

---

### Sprint 29 (semaines 59-60) — Pré-release : Epic 18 fin + load test + pen test + cleanup + 🎯 GO-LIVE MVP

**Objectif** : livrer les dernières stories compliance + exécuter load test (20.2) + pen test (20.3) + cleanup feature flag (20.1). **Go-live MVP**.

| Story | Titre | Points | Dépendances | CQ |
|---|---|---|---|---|
| **18.6** | Password reset + magic link passwordless + force reset admin | 3 (M) | Epic 10 NFR45 Mailgun | CQ-6 |
| **18.7** | Audit trail accès données sensibles (rétention 5 ans) | 3 (M) | Epic 10 | CQ-6 |
| **20.1** | Cleanup feature flag `ENABLE_PROJECT_MODEL` (migration 027) | 2 (S) | Epic 11-19 livrés | CQ-10 |
| **20.2** | Load testing k6 conforme NFR71 | 5 (L) | Epic 11-19 livrés | CQ-14 |
| **20.3** | Pen test externe indépendant (findings CRITIQUES corrigés avant pilote) | 3 (M) | Epic 10-19 livrés | CQ-6 |

**Total points** : 16. Dépassement 1 pt. Arbitrage : 18.6 (3) + 20.1 (2) + 20.2 (5) + 20.3 (3) = 13 pts. **18.7 reporté +1 semaine post-go-live** (tranche tolérée, FR69 déjà couvert partiellement par 10.12 audit trail catalogue).

**Total révisé Sprint 29** : 13 pts + Audit WCAG re-test externe (hors points).

**Exit criteria Sprint 29 = 🎯 GO-LIVE MVP** :
- [ ] **109 stories** `done` (sauf 18.7 report tolérance +1 semaine).
- [ ] Load test k6 : 100 users simultanés chat+cube 4D, 10 SGES simultanés, 500 appels/min read-only, tous NFR performance respectés (NFR71).
- [ ] Pen test externe : findings CRITIQUES tous corrigés.
- [ ] Audit WCAG : findings HIGH/CRITICAL corrigés (re-test Sprint 30 hors plan).
- [ ] Feature flag `ENABLE_PROJECT_MODEL` retiré (NFR63 + CQ-10).
- [ ] **Trigger SC-B-PILOTE 15 k€** déclenché : 10 k€ consultants ESG AO seniors + 3 k€ support PME pilotes + 2 k€ incentives (voucher/airtime/goodies).
- [ ] Partenaire bailleur identifié (Proparco / BAD / BOAD / équivalent — condition d'activation `SC-B-PILOTE`).
- [ ] Pilote sur 20-50 PME pilotes + 1-2 partenaires institutionnels.
- [ ] 1159+ tests verts, coverage ≥ 80 % (≥ 85 % code critique).

---

## 4. Milestones & Jalons GTM

| Sprint | Date cible (semaines depuis 2026-04-19) | Milestone | Action GTM |
|---|---|---|---|
| **Sprint 0** | S+2 | Kickoff Phase 0 + 9.7 livrée | Post LinkedIn engagement Phase 0 |
| **Sprint 3** | S+8 | Bench LLM tranché (R-04-1) | Décision provider primaire MVP communiquée |
| **Sprint 8** | S+18 (~4,5 mois) | **End Phase 0 + Checkpoint CQ-14 re-validation** | Sprint planning Phase 1 publié, ajustements vélocité |
| **Sprint 11** | S+24 (~6 mois) | Aminata journey desktop + mobile testable (niveaux 0-1) | Démo interne / pré-pilote |
| **Sprint 16** | S+34 (~8 mois) | ESG 3 couches opérationnel + Journey 3 Akissi testable | Atelier stakeholders business (révision SC-B1/B5/B6/MO-5 selon `business-decisions-2026-04-19.md`) |
| **Sprint 19** | S+40 (~9,5 mois) | Cube 4D Matching Journey 4 Ibrahim testable | Showcase candidats partenaires bailleurs |
| **Sprint 23** | S+48 (~11 mois) | Cluster C livrables + SGES BETA NO BYPASS (FR44) en beta interne | Partenariat signé 1er bailleur (cible Proparco/BAD/BOAD) |
| **Sprint 27** | S+56 (~12,5 mois) | Dashboard admin + RAG 5 modules + Compliance socle | Audit WCAG externe + pen test lancés (contrats signés) |
| **Sprint 29** | **S+60 (~14 mois)** | **🎯 GO-LIVE MVP + trigger SC-B-PILOTE 15 k€** | **Pilote 20-50 PME (SN ou CI) + partenaire institutionnel actif** |
| **T+3 mois post-MVP** | S+72 (~17 mois) | **Révision `business-decisions-2026-04-19.md`** | Mise à jour SC-B1/B5/B6/MO-5/NFR68 avec données terrain pilote |
| **T+6 mois post-MVP** | S+86 (~20 mois) | Révision SC-B6 rétention 60 % | Décision continuation ou Phase Growth monétisation |
| **T+9 mois post-MVP** | S+98 (~23 mois) | Modèle éco SC-B5 validé (≥ 1 partenaire payant identifié) | Lancement Phase Growth |
| **T+12 mois post-MVP** | S+112 (~26 mois) | **200 MAU (SC-B1)** | Décision scaling + extension UEMOA/CEDEAO multi-pays |

---

## 5. Risques Planning & Mitigations

### 5.1 Risque technique — Story XL / sprint entier

| Risque | Story | Description | Probabilité | Mitigation |
|---|---|---|---|---|
| R-PLAN-1 | **13.4a Moteur DSL borné** (5 pts, risque 1 sprint entier) | DSL Pydantic + exécution rule + N/A explicite = cœur architectural. Sous-estimation probable. | HIGH | **Spike technique Sprint 13 non livré (PoC)** + pair-review via GitHub issue (community) + fallback split 13.4a1 Pydantic schema + 13.4a2 exécution moteur si dérapage |
| R-PLAN-2 | **9.10 Queue async + micro-Outbox** (8 pts XL) | Migration 3 endpoints synchrones → risque régression 3 modules. | HIGH | **Split 9.10a reports + 9.10b action_plan + 9.10c applications** si dérapage Sprint 8. Golden tests avant/après. |
| R-PLAN-3 | **10.13 Voyage + bench LLM** (8 pts XL, splitté 10.13a/b) | 150 échantillons qualité manuelle = 2 j sup scope bench. | MEDIUM | Split déjà planifié (5+3). Bench assisté par script `scripts/bench_llm_providers.py`. |
| R-PLAN-4 | **15.5 SGES BETA NO BYPASS** (8 pts XL) | Workflow bloquant critique juridique (CQ-5). Pas de bypass admin. | HIGH | Sprint entier Sprint 22. Pair-review externe via consultant ESG AO (budget SC-B-PILOTE 10 k€ anticipé). |
| R-PLAN-5 | **10.7 envs ségrégués** (L mais risque XL) | AWS IAM + secrets Manager + 3 envs = complexité infra. | MEDIUM | **Split 10.7a envs + 10.7b pipeline anonymisation** prêt. Buffer Sprint 4 + report Sprint 5 si besoin. |

### 5.2 Risque vélocité — Solo + contexte brownfield

| Risque | Description | Probabilité | Mitigation |
|---|---|---|---|
| R-VEL-1 | Vélocité réelle < 10 pts/sprint sur 3 sprints consécutifs | MEDIUM | Checkpoint CQ-14 Sprint 8 re-calibre Phase 1. Alternance front/back pour éviter fatigue. Buffer 20 % sur stories XL. |
| R-VEL-2 | Charge mentale 18 specs brownfield + 109 stories extension | HIGH | Documentation `docs/CODEMAPS/` systématique. TodoWrite tool pour traçabilité. Code review agents Claude après chaque merge. |
| R-VEL-3 | Dette technique cumulée 18 specs (9 stories dette) | MEDIUM | **Phase 0 Sprints 0-8** dédiée au solde dette. Checkpoint CQ-14 Sprint 8 obligatoire. |

### 5.3 Risque budgétaire — Caps NFR68/NFR69

| Risque | Description | Probabilité | Mitigation |
|---|---|---|---|
| R-BUD-1 | **Budget LLM > 500 €/mois** (NFR68) | MEDIUM | Alerting 400 €/500 € livré Story 17.5. Bench 10.13 sélectionne provider plus économe. Fallback MiniMax si Anthropic trop cher. |
| R-BUD-2 | **Budget infra > 1 000 €/mois** (NFR69) | LOW | Review trimestrielle (cf. `business-decisions-2026-04-19.md`). RDS t3.micro STAGING explicit. Upgrade déclenché ≥ 500 MAU seulement. |
| R-BUD-3 | Audit WCAG > 4 k€ | LOW | Cap validé `business-decisions-2026-04-19.md`. Scope restreint 5 journeys + 8 composants gravité. |
| R-BUD-4 | Pilote > 15 k€ | MEDIUM | Cap bas fourchette PRD (15-30 k€). Activation conditionnée partenaire signé. Révision si bailleur exige revue payante. |

### 5.4 Risque GTM — Partenaire bailleur non signé à T+12 mois

| Risque | Description | Probabilité | Mitigation |
|---|---|---|---|
| R-GTM-1 | Aucun partenaire institutionnel actif à T+3 mois post-MVP | MEDIUM | Révision SC-B1 adoption à la baisse (100 MAU, `business-decisions-2026-04-19.md`). Canal croissance organique activé (LinkedIn, conférences AO). |
| R-GTM-2 | Modèle éco SC-B5 non validé à T+9 mois | HIGH | Freemium MVP maintenu. Évaluation B2B2C intermédiaires (SIB/Ecobank). |

---

## 6. Parallélisation limitée (solo)

### 6.1 Stories indépendantes candidates au swap contexte (max 2)

- **Front + back en parallèle** (exemples de sprints mixtes) :
  - Sprint 6 : 10.14 Storybook (front) + 10.15/10.16/10.17 composants UI (front) → swap back uniquement en fin de sprint si avance.
  - Sprint 10 : 11.4/11.5 back (module) + 11.7 front (CSV/Excel import UI).
- **Stories orthogonales dans un même sprint** :
  - Sprint 2 : 10.10 (back outbox) + 10.6 (back storage) + 10.2 (back skeleton) — tout back mais modules différents.
  - Sprint 27 : 17.6 (front/back monitoring) + 18.1 (back anonymisation) + 18.3 (back MFA).

### 6.2 Alternance front/back recommandée

- **Sprints front-heavy** : 6, 7, 11 (FormalizationPlan UI), 15 (Journey 3 Akissi), 20-22 (SignatureModal + SectionReviewCheckpoint + SgesBetaBanner), 25 (dashboard 17.1-17.3).
- **Sprints back-heavy** : 0, 1, 2, 3, 4, 5, 8, 12, 13-14 (DSL), 17-19 (Cube 4D), 27-29 (compliance + release).
- Éviter 3 sprints consécutifs même côté (burnout cognitif).

---

## 7. Tableau récapitulatif

| Sprint | Stories | Points | Exit criteria clé | Milestone GTM |
|---|---|---|---|---|
| **0** | 9.7, 9.8, 9.11, 9.14, 9.15 | 12 | 9.7 mergée → Epic 10 débloqué | Post LinkedIn |
| **1** | 10.1, 10.5, 10.9 | 12 | Migrations 020-026 + RLS activée + flag | — |
| **2** | 10.10, 10.6, 10.2 | 11 | Outbox worker + StorageProvider + projects skeleton | — |
| **3** | 10.13a, 10.13b, 10.21 | 10 | **Décision LLM primaire actée** + Voyage en prod + Lucide | Provider MVP communiqué |
| **4** | 10.3, 10.4, 10.7 | 13 | 3 modules squelettes + 3 envs isolés | — |
| **5** | 10.8, 10.11, 10.12 | 11 | Framework prompts CCC-9 + sourcing Annexe F + audit trail | — |
| **6** | 10.14, 10.15, 10.16, 10.17 | 12 | Storybook + Button + Input + Badge | — |
| **7** | 10.18, 10.19, 10.20, 19.1 | 14 | Drawer + Combobox + Tabs + DatePicker + RAG refactor | — |
| **8** | 9.10, 9.12, 9.13 + **✋ CQ-14 checkpoint** | 14 | **End Phase 0 + re-validation estimations** | Sprint planning Phase 1 publié |
| **9** | 11.1, 11.2, 11.3, 11.8 | 11 | Company + Project + collaborateurs + auditor | — |
| **10** | 11.4, 11.5, 11.6, 11.7 | 14 | Consortium + bulk-import 152 producteurs Moussa | Démo interne |
| **11** | 12.1, 12.2, 12.3, 12.4 | 13 | FormalizationPlan Aminata niveau 0 → 1 | — |
| **12** | 12.5, 12.6, 13.1 | 11 | Fin Epic 12 + début Epic 13 facts | — |
| **13** | 13.2, 13.3 + spike 13.4a PoC | 8 | Evidence + versioning + prototypage DSL | — |
| **14** | 13.4a, 13.4b, 13.5 | 11 | **Moteur DSL + verdicts ESG** | Atelier stakeholders business |
| **15** | 13.6, 13.7, 13.11 | 11 | Packs + scoring global + property-based tests | — |
| **16** | 13.8a, 13.8b, 13.10 | 13 | Admin catalogue ESG N1/N2 + Journey 3 Akissi | — |
| **17** | 14.1, 14.2, 14.3 | 11 | Cube 4D matcher + voie d'accès | — |
| **18** | 14.4, 14.5, 14.6, 14.7 | 13 | Critères intermédiaire + lifecycle FundApplication | — |
| **19** | 14.8, 14.9, 13.8c, 13.9 | 14 | **Fin Epic 13 + Journey 4 Ibrahim remédiation** | Showcase bailleurs |
| **20** | 14.10, 15.1a, 15.1b | 13 | Template engine PDF + guards + async | — |
| **21** | 15.2, 15.3, 15.6, 15.7 | 12 | DOCX + evidence + SignatureModal + >50k block | — |
| **22** | 15.4, 15.8, **15.5 SGES BETA XL** | 16 | **FR44 NO BYPASS + snapshot cryptographique** | — |
| **23** | 15.9, 14.7.ext, 16.1 | 12 | Fin Epic 15 + début Copilot | Partenariat 1er bailleur signé |
| **24** | 16.2, 16.3, 16.4, 16.5, 16.6 | 14 | Fin Epic 16 Copilot étendu | — |
| **25** | 17.1, 17.2, 17.3 | 11 | Dashboard PME étendu + Moussa multi-projets | — |
| **26** | 17.4, 17.5, 19.2 | 13 | Reminders + monitoring admin + RAG 5 modules | — |
| **27** | 17.6, 18.1, 18.3 | 13 | Alerting + anonymisation PII + MFA | Audit WCAG + pen test lancés |
| **28** | 18.2, 18.4, 18.5, 20.4 | 14 | Chiffrement KMS + droit effacement + export + **audit WCAG livré** | Pilote en préparation |
| **29** | 18.6, 20.1, 20.2, 20.3 | 13 | **🎯 GO-LIVE MVP** + load test + pen test + flag cleanup | **SC-B-PILOTE 15 k€ trigger** |

**Total cumulé points** : 374 pts sur 30 sprints = moyenne 12,47 pts / sprint (cible 12,5 respectée).

---

## 8. Annexes

### Annexe A — Mapping Story → exigences CQ-1..CQ-14 prioritaires

| Story | CQ prioritaires | Note |
|---|---|---|
| 9.7 | CQ-11, CQ-4 | Dette audit pure, bloque Epic 10 |
| 9.10 | CQ-3, CQ-14 | XL, candidat split 9.10a/b/c |
| 9.13 | CQ-4, CQ-14 | RAG applications (P1 #13) consomme 19.1 + 10.13 |
| 10.1 | CQ-7, CQ-6 | Consolidation unique migrations (exception CQ-7 documentée) |
| 10.5 | CQ-6, CQ-8 | RLS 4 tables NFR12 + FR59 |
| 10.10 | CQ-6, CQ-8 | Pattern Outbox CCC-14, consommé par 9.10/12.5/13.4b/15.4/17.4 |
| 10.13 | CQ-9, CQ-12 | AC9 bench 3 providers (R-04-1 tranché `business-decisions-2026-04-19.md`) |
| 10.14 | CQ-8, CQ-12 | 6 composants à gravité UX Step 11 |
| 11.1 | CQ-9 (QO-A1) | Project sans Company = NON (FK NOT NULL) |
| 12.2 | CQ-9 (QO-A'1) | OCR seuil 0,8 + fallback human review |
| 12.3 | CQ-9 (QO-A'3/A'4) | Niveaux intermédiaires + formalisation vs conformité fiscale |
| 12.5 | CQ-9 (QO-A'5) | Pas de régression auto + soft-block |
| 13.4a | CQ-9 (QO-B3) | N/A explicite pas NULL ni PASS défaut |
| 13.6 | CQ-9 (QO-B4) | STRICTEST WINS (min appliqué) |
| 15.5 | **CQ-5** | SGES BETA NO BYPASS **story dédiée obligatoire** |
| 20.1 | **CQ-10** | Cleanup feature flag `ENABLE_PROJECT_MODEL` fin Phase 1 |
| Checkpoint Sprint 8 | **CQ-14** | Re-validation estimations fin Phase 0 obligatoire (PRD ligne 941) |
| Toutes stories Epic 10+ | CQ-11 | `with_retry` + `log_tool_call` enforced dès création module (9.7 mergée) |

### Annexe B — Stories XL identifiées et stratégie de split

| Story | Points | Split stratégie | Sprint |
|---|---|---|---|
| **9.10** | 8 (XL) | **9.10a reports (M/3) + 9.10b action_plan (M/3) + 9.10c applications (M/3)** si dérapage Sprint 8 | 8 |
| **10.7** | 5 (L, risque XL) | **10.7a envs ségrégués (L/5) + 10.7b pipeline anonymisation (M/3)** si dérapage | 4 |
| **10.13** | 8 (XL) | **10.13a Voyage migration (L/5) + 10.13b bench 3 providers (M/3)** ✅ planifié Sprint 3 | 3 |
| **13.4a** | 5 (L, risque XL) | **13.4a1 Pydantic schema + DSL types (M/3) + 13.4a2 exécution moteur + N/A (M/3)** si dérapage + **PoC Sprint 13 non livré** | 14 |
| **15.5** | 8 (XL) | **Pas de split recommandé** (workflow atomique critique juridique). Sprint entier Sprint 22. | 22 |

### Annexe C — Definition of Ready (pré-sprint)

Pour chaque story entrant dans un sprint :

- [ ] **CQ-6** : AC Given/When/Then avec métriques quantifiées (NFR référencé si applicable).
- [ ] **CQ-8** : metadata complète (`fr_covered`, `nfr_covered`, `phase`, `cluster`, `estimate`, `qo_rattachees`, `depends_on`).
- [ ] **CQ-9** : QO rattachée tranchée dans le document de spec (si applicable).
- [ ] **CQ-11** : format story aligné sur `implementation-artifacts/9-x` + `spec-audits/`.
- [ ] **CQ-13** : estimation XS/S/M/L/XL confirmée.
- [ ] Dépendances `depends_on` toutes `done` (DAG respecté — CQ-2).
- [ ] Fichiers frontend/backend identifiés (pas de découverte majeure en cours de story).
- [ ] Budget LLM + infra vérifié (pas d'impact > 10 % sur caps NFR68/NFR69).
- [ ] Spec UX disponible si composant à gravité (Storybook scope Q16 + 25 arbitrages UX).

### Annexe D — Definition of Done (fin sprint)

Pour chaque story passée en `done` :

- [ ] Code implémenté conforme AC1..ACn.
- [ ] Tests unitaires + intégration + E2E (le cas échéant) verts.
- [ ] Coverage ≥ 80 % (≥ 85 % code critique : guards LLM, anonymisation PII, RLS, rate limiting, signature, snapshot, livrables bailleur — NFR60).
- [ ] `with_retry` + `log_tool_call` enforced si story touche un tool LangChain (CQ-11 héritage 9.7).
- [ ] Dark mode rendu correct (CLAUDE.md obligatoire).
- [ ] Accessibilité WCAG 2.1 AA (axe-core sans violation pour composants UI).
- [ ] Code review agent `code-reviewer` exécuté, CRITICAL + HIGH adressés (NFR76).
- [ ] Code review agent `security-reviewer` exécuté si code critique sécurité (auth, payments, user data, docs bailleurs).
- [ ] `docs/CODEMAPS/` à jour (NFR61 + NFR62).
- [ ] Baseline tests augmentée (NFR59 zero failing tests on main).
- [ ] `sprint-status.yaml` mis à jour : statut `done` + commit SHA.
- [ ] Changelog / PR description FR avec accents obligatoires.
- [ ] Budget LLM réel vs prévision documenté dans commentaire PR.
- [ ] Pre-commit `detect-secrets` + `pip-audit` + `npm audit` verts (NFR15, NFR72).

---

**Fin du sprint plan — ESG Mefali 2026-04-19.**
