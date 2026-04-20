---
title: "ESG Mefali Extension — Epics (Index)"
type: index
status: active
total_epics: 12
total_stories: 109
source_document: ../epics-consolidated.md
last_updated: 2026-04-19
---

# ESG Mefali Extension — Epic Breakdown (Index)

Document sharded depuis `epics-consolidated.md` (3 181 lignes, 12 epics, 109 stories) pour permettre le chargement d'un seul epic lors d'une `dev-story` sans trimbaler les 11 autres en contexte.

## Table des matières

| Epic | Fichier | Titre | Stories | Statut | Deps amont | Bloque |
|---|---|---|---|---|---|---|
| 9  | [epic-09.md](./epic-09.md) | Dette audit 18-specs (PURE) | 15 (6 done + 9 à livrer) | `in-progress` | — | Epic 10 (via 9.7) |
| 10 | [epic-10.md](./epic-10.md) | Fondations Extension Phase 0 (BLOQUANT) | 21 | `planned` | Story 9.7 | Epics 11–19 |
| 11 | [epic-11.md](./epic-11.md) | Cluster A — PME porteuse de projets multi-canal | 8 | `planned` | Epic 10 | Epics 12–15 |
| 12 | [epic-12.md](./epic-12.md) | Cluster A' — Maturité administrative graduée | 6 | `planned` | Epics 10, 11 | Epic 14 |
| 13 | [epic-13.md](./epic-13.md) | Cluster B — ESG multi-contextuel 3 couches | 14 | `planned` | Epic 10 | Epics 14, 15 |
| 14 | [epic-14.md](./epic-14.md) | Cube 4D — Matching projet-financement | 10 | `planned` | Epics 10, 11, 12, 13 | Epics 15–19 |
| 15 | [epic-15.md](./epic-15.md) | Moteur livrables bailleurs + SGES BETA | 10 | `planned` | Epics 10, 11, 12, 13 ; Stories 9.6, 9.10 | Epics 16–20 |
| 16 | [epic-16.md](./epic-16.md) | Copilot conversationnel — extension tool-calling | 6 | `planned` | Epics 10, 11–15 | Epic 20 |
| 17 | [epic-17.md](./epic-17.md) | Dashboard & Monitoring | 6 | `planned` | Epics 10, 11–15 ; Story 9.7 | Epic 20 |
| 18 | [epic-18.md](./epic-18.md) | Compliance & Security renforcés | 7 | `planned` | Epics 10, 11–15 | Epic 20 |
| 19 | [epic-19.md](./epic-19.md) | Socle RAG refactor + intégration ≥ 5 modules | 2 | `planned` | Epic 10 ; Story 9.13 | Epic 20 |
| 20 | [epic-20.md](./epic-20.md) | Cleanup & Release Engineering | 4 | `planned` | Epics 11–19 | — (fin Phase 1) |

**Cumul : 109 stories**.

---

## Dépendance bloquante critique

> **Story 9.7 (observabilité `with_retry` + `log_tool_call`) BLOQUE Epic 10.**
> Raison — instrumenter les nouveaux modules Extension (`projects/`, `maturity/`, `admin_catalogue/`) **DÈS leur création**, sinon réintroduction de la dette P1 #14. Arbitrage CQ-11 (voir `business-decisions-2026-04-19.md`).

Voir `epic-09.md` → Story 9.7 metadata `blocks: Epic 10 — DÉPENDANCE BLOQUANTE (CQ-11)`.

---

## Changelog global de renumérotation / refactor

Chaque ligne liste un changement structurant à préserver lors de la navigation entre versions.

- **Story 11.8 → 14.1** (Lot 4) : `CompanyProjection curée par Fund` déplacée pour respecter le DAG Epic 11 → 14 (la projection est sémantiquement liée au matching, pas à la création Company). Epic 11 passe à 8 stories. Dans `epic-11.md`, la story 11.8 actuelle = `Auditor time-bounded scoping sur la Company`.
- **Story 9.10** (Lot 2) : « Queue async Celery+Redis » → « `BackgroundTask` FastAPI + micro-Outbox `domain_events` » — alignement architecture Décision 7 (pas de Redis MVP) + Décision 11 (micro-Outbox). Estimate L → XL.
- **Story 13.4 → 13.4a + 13.4b** (Lot 4) : découpage moteur DSL borné (L) + matérialisation `ReferentialVerdict` + invalidation via Outbox (M).
- **Story 13.8 → 13.8a + 13.8b + 13.8c** (Lot 4) : découpage par workflow N1 / N2 / N3 avec UI commune.
- **Story 10.13 AJOUTÉE MVP** (post-Lot 4) : migration embeddings OpenAI → Voyage API activée dès Phase 0 (plus différée Phase Growth). Epic 10 passe de 12 → 13 stories. Story 9.13 `depends_on` étendu avec 10.13.
- **Story 10.13 AC9 benchmark** (post-Lot 4) : ajout AC9 critère bench précision/rappel Voyage vs OpenAI sur corpus pilote avant cut-over production.
- **Story 15.1 → 15.1a + 15.1b** (Lot 4) : découpage moteur PDF (template engine) + intégration guards LLM + BackgroundTask + validation perf NFR3/NFR4.
- **Stories 10.14-10.21 AJOUTÉES** (2026-04-19) : socle UI fondation. Réconciliation avec `ux-design-specification.md` Step 11 Component Strategy section 4 + 5.1. 8 stories UI fondation dans Epic 10 (Storybook + 6 composants `ui/` génériques + Lucide + `EsgIcon.vue` wrapper) pour débloquer Phase 1 Sprint 1+. Epic 10 passe de 13 → 21 stories. **Cumul total : 101 → 109 stories.** Conflit numérotation UX Step 11 vs epics.md tranché : 10.13 reste Voyage (priorité epics.md finalisé), stories UI fondation décalées de 10.13-10.20 (numérotation UX initiale) vers 10.14-10.21.

---

## Consolidated Decisions Log (QO tranchées MVP)

- **QO-A1** → Tranchée 11.1 AC5 : pas de Project sans Company (FK NOT NULL).
- **QO-A'1** → Partiellement tranchée 12.2 AC2 : seuil OCR 0,8 + fallback `pending_human_review` (pilote affinera).
- **QO-A'3 + QO-A'4** → Tranchées 12.3 AC3 : `default_steps: JSONB` data-driven (4 étapes MVP, admin Phase Growth modifie sans migration).
- **QO-A'5** → Tranchée 12.5 AC2 : pas de régression auto ; soft-block user + self-service + audit trail (pas d'escalade admin obligatoire).
- **QO-B3** → Tranchée 13.4a AC2 : **`N/A` explicite** sur fact manquant ou expiré (pas NULL, pas PASS par défaut) + rationale `fact_missing|fact_expired`.
- **QO-B4** → Tranchée 13.6 AC2 : **STRICTEST WINS** (min appliqué, pas moyenne pondérée) + `overridden_by_pack` dans `verdict.metadata`.
- **Prompt versioning — 18 specs legacy** (post-Lot 5) : dette acceptée MVP. Les 18 prompts legacy conservés non-versionnés. **Nouveaux prompts Epic 10+ obligatoirement versionnés** via framework CCC-9 (Story 10.8). Migration legacy **opportuniste**. Pas de story de migration globale.

---

## DAG de dépendances Phase 0 → Phase 1

```
Story 9.7 (observabilité) ───BLOQUE───→ Epic 10 (Fondations)
                                           │
                                           ├─ stories 9.8–9.15 (dettes P1) — parallèle à Epics 11+ (cibles indépendantes)
                                           │
                                           ├─→ Epic 19 Phase 0 (socle RAG refactor)
                                           │
                                           └─→ Epic 11 (Cluster A)
                                                 └─→ Epic 12 (Cluster A')
                                                       └─→ Epic 13 (Cluster B)
                                                             ├─→ Epic 14 (Cube 4D)
                                                             └─→ Epic 15 (Moteur livrables)
                                                                   ├─→ Epic 16 (Copilot tools)
                                                                   ├─→ Epic 17 (Dashboard)
                                                                   ├─→ Epic 18 (Compliance enforcement)
                                                                   ├─→ Epic 19 Phase 1 (RAG ≥ 5 modules)
                                                                   └─→ Epic 20 (Cleanup & Release, fin Phase 1)
```

---

## Utilisation lors d'une `dev-story`

Pour charger un seul epic :

```
# Exemple : travailler sur une story d'Epic 13
Read _bmad-output/planning-artifacts/epics/epic-13.md
```

Les dépendances cross-epic sont déclarées dans le frontmatter YAML de chaque fichier epic (`dependencies:`). Consulter `0-index.md` (ce fichier) pour la vue d'ensemble du DAG avant de démarrer.

---

## Archive

Le document consolidé original est préservé sous :

```
_bmad-output/planning-artifacts/epics-consolidated.md
```

Il contient les sections additionnelles **Overview**, **Requirements Inventory** (FR / NFR / Additional Requirements / UX Design Requirements / FR Coverage Map) et **Epic List** synthétique, qui ne sont pas répliquées dans les shards (elles restent accessibles via l'archive).

Les 12 fichiers de ce dossier (`epic-09.md` → `epic-20.md`) ne couvrent que la section **« Stories détaillées »** de chaque epic.
