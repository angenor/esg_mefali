# Tasks: Evaluation et Scoring ESG Contextualise

**Input**: Design documents from `/specs/005-esg-scoring-assessment/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/esg-api.md

**Tests**: Inclus (constitution exige TDD — Test-First NON-NEGOTIABLE, couverture 80%+).

**Organization**: Taches groupees par user story pour permettre l'implementation et le test independant de chaque story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1, US2, US3, US4, US5)
- Chemins exacts depuis la racine du projet

---

## Phase 1: Setup (Infrastructure partagee)

**Purpose**: Initialisation du module ESG et infrastructure de base

- [X] T001 Creer la structure du module backend dans backend/app/modules/esg/__init__.py
- [X] T002 [P] Definir les 30 criteres ESG (E1-E10, S1-S10, G1-G10) avec codes, libelles et descriptions dans backend/app/modules/esg/criteria.py
- [X] T003 [P] Definir les ponderations sectorielles et benchmarks par secteur dans backend/app/modules/esg/weights.py
- [X] T004 [P] Creer les types TypeScript ESG (ESGAssessment, CriteriaScore, PillarScore, Benchmark) dans frontend/app/types/esg.ts

---

## Phase 2: Foundational (Prerequis bloquants)

**Purpose**: Modele de donnees, schemas Pydantic et migration — DOIT etre complete avant toute user story

**CRITICAL**: Pas de travail sur les user stories avant cette phase

- [X] T005 Creer le modele SQLAlchemy ESGAssessment (avec champs JSONB) dans backend/app/models/esg.py
- [X] T006 Generer la migration Alembic pour la table esg_assessments dans backend/alembic/versions/
- [X] T007 Creer les schemas Pydantic (ESGAssessmentCreate, ESGAssessmentResponse, ESGAssessmentList, CriteriaScoreDetail, PillarScoreDetail, ScoreResponse, BenchmarkResponse) dans backend/app/modules/esg/schemas.py
- [X] T008 Ajouter le champ esg_assessment (dict | None) au ConversationState dans backend/app/graph/state.py
- [X] T009 Executer la migration Alembic et verifier la table esg_assessments en base

**Checkpoint**: Fondation prete — les user stories peuvent commencer

---

## Phase 3: User Story 1 — Evaluation ESG conversationnelle (Priority: P1) MVP

**Goal**: Un utilisateur peut demarrer une evaluation ESG conversationnelle via le chat, repondre aux questions pilier par pilier, voir des visuels intermediaires et obtenir un score final avec recommandations.

**Independent Test**: Demarrer une evaluation dans le chat, repondre aux questions E1-E10, S1-S10, G1-G10, verifier les blocs progress/chart/gauge/table dans le chat.

### Tests pour User Story 1

> **Ecrire ces tests EN PREMIER, verifier qu'ils ECHOUENT avant implementation**

- [X] T010 [P] [US1] Tests unitaires du service de scoring (calcul scores, ponderation, recommandations) dans backend/tests/test_esg_service.py
- [X] T011 [P] [US1] Tests unitaires des criteres et ponderations (validite des 30 criteres, coherence poids) dans backend/tests/test_esg_criteria.py
- [X] T012 [P] [US1] Tests du esg_scoring_node (flux evaluation, gestion etat, redirection profiling) dans backend/tests/test_esg_scoring_node.py

### Implementation pour User Story 1

- [X] T013 [US1] Implementer ESGScoringService : create_assessment, get_assessment, evaluate_criteria, compute_pillar_score, compute_overall_score, generate_recommendations, generate_strengths_gaps dans backend/app/modules/esg/service.py
- [X] T014 [US1] Creer le prompt systeme du noeud ESG avec instructions visuelles (progress apres chaque pilier, radar/gauge/table en fin d'evaluation) dans backend/app/prompts/esg_scoring.py
- [X] T015 [US1] Implementer esg_scoring_node dans backend/app/graph/nodes.py : gestion etat evaluation, appel LLM avec prompt ESG, mise a jour assessment_data, transition entre piliers
- [X] T016 [US1] Modifier router_node dans backend/app/graph/nodes.py : detection des intentions ESG (mots-cles evaluation/scoring/ESG), routage conditionnel vers esg_scoring_node
- [X] T017 [US1] Modifier le graph LangGraph dans backend/app/graph/graph.py : ajouter esg_scoring_node comme noeud, ajouter le routage conditionnel depuis router_node
- [X] T018 [US1] Creer le router REST ESG (POST /assessments, GET /assessments, GET /assessments/{id}, POST /assessments/{id}/evaluate, GET /assessments/{id}/score) dans backend/app/modules/esg/router.py
- [X] T019 [US1] Enregistrer le router ESG dans backend/app/main.py (prefix /api/esg)
- [X] T020 [P] [US1] Tests du router REST ESG (creation, liste, detail, score) dans backend/tests/test_esg_router.py

**Checkpoint**: L'evaluation ESG conversationnelle est fonctionnelle de bout en bout via le chat et l'API REST

---

## Phase 4: User Story 2 — Page de resultats ESG persistante (Priority: P2)

**Goal**: L'utilisateur peut consulter ses resultats ESG sur une page dediee avec score global, radar chart, barres de progression, points forts, recommandations.

**Independent Test**: Acceder a /esg et /esg/results, verifier tous les elements visuels avec des donnees d'evaluation.

### Implementation pour User Story 2

- [X] T021 [P] [US2] Creer le store Pinia ESG (assessments, currentAssessment, loading, fetchAssessments, fetchScore) dans frontend/app/stores/esg.ts
- [X] T022 [P] [US2] Creer le composable useEsg (appels API : createAssessment, listAssessments, getAssessment, getScore) dans frontend/app/composables/useEsg.ts
- [X] T023 [P] [US2] Creer le composant ScoreCircle.vue (cercle SVG avec score, couleur vert/orange/rouge) dans frontend/app/components/esg/ScoreCircle.vue
- [X] T024 [P] [US2] Creer le composant CriteriaProgress.vue (barres de progression groupees par pilier, 30 criteres) dans frontend/app/components/esg/CriteriaProgress.vue
- [X] T025 [P] [US2] Creer le composant StrengthsBadges.vue (badges verts pour points forts) dans frontend/app/components/esg/StrengthsBadges.vue
- [X] T026 [P] [US2] Creer le composant Recommendations.vue (tableau recommandations priorisees avec impact/effort/timeline) dans frontend/app/components/esg/Recommendations.vue
- [X] T027 [US2] Creer la page /esg (ecran invitation si aucune evaluation, liste des evaluations sinon) dans frontend/app/pages/esg.vue
- [X] T028 [US2] Creer la page /esg/results (score global, radar chart, criteres, points forts, recommandations) dans frontend/app/pages/esg/results.vue
- [X] T029 [US2] Ajouter l'entree "Evaluation ESG" dans la sidebar dans frontend/app/components/layout/AppSidebar.vue

**Checkpoint**: La page de resultats ESG est fonctionnelle et affiche toutes les donnees depuis l'API

---

## Phase 5: User Story 3 — Evaluation documentaire via RAG (Priority: P2)

**Goal**: L'evaluation ESG exploite les documents uploades pour enrichir les scores et citer les sources.

**Independent Test**: Uploader un document, lancer une evaluation, verifier que le systeme cite des elements du document.

### Tests pour User Story 3

- [X] T030 [P] [US3] Tests de la recherche vectorielle par critere ESG (retrieval pertinent, format des resultats) dans backend/tests/test_esg_rag.py

### Implementation pour User Story 3

- [X] T031 [US3] Ajouter la fonction de recherche RAG par critere dans backend/app/modules/esg/service.py : search_relevant_chunks(criteria_code, user_id) utilisant pgvector et DocumentChunk
- [X] T032 [US3] Integrer le contexte RAG dans esg_scoring_node : pour chaque critere evalue, rechercher les chunks pertinents et les injecter dans le prompt dans backend/app/graph/nodes.py
- [X] T033 [US3] Mettre a jour le prompt ESG pour inclure les instructions de citation des sources documentaires dans backend/app/prompts/esg_scoring.py

**Checkpoint**: L'evaluation ESG enrichit les scores avec les documents et cite les sources

---

## Phase 6: User Story 4 — Benchmarking sectoriel (Priority: P3)

**Goal**: L'utilisateur voit sa position relative par rapport aux moyennes de son secteur, dans le chat et sur la page.

**Independent Test**: Consulter le benchmark apres une evaluation, verifier le graphique comparatif.

### Implementation pour User Story 4

- [X] T034 [US4] Implementer la fonction get_sector_benchmark(sector) dans backend/app/modules/esg/service.py utilisant les donnees de weights.py
- [X] T035 [US4] Ajouter l'endpoint GET /api/esg/benchmarks/{sector} dans backend/app/modules/esg/router.py
- [X] T036 [US4] Integrer le calcul de benchmark dans la finalisation de l'evaluation (remplir sector_benchmark dans ESGAssessment) dans backend/app/modules/esg/service.py
- [X] T037 [US4] Mettre a jour le prompt ESG pour generer un bloc chart (bar) de benchmark a la fin de l'evaluation dans backend/app/prompts/esg_scoring.py
- [X] T038 [US4] Ajouter la section benchmark sur la page de resultats (graphique en barres via Chart.js) dans frontend/app/pages/esg/results.vue

**Checkpoint**: Le benchmark sectoriel est visible dans le chat et sur la page de resultats

---

## Phase 7: User Story 5 — Historique des evaluations (Priority: P3)

**Goal**: L'utilisateur voit l'evolution de son score ESG dans le temps via un graphique.

**Independent Test**: Avoir 2+ evaluations, verifier le graphique d'evolution temporelle.

### Implementation pour User Story 5

- [X] T039 [P] [US5] Creer le composant ScoreHistory.vue (graphique line Chart.js avec scores dans le temps) dans frontend/app/components/esg/ScoreHistory.vue
- [X] T040 [US5] Integrer le composant ScoreHistory dans la page de resultats avec gestion du cas mono-evaluation dans frontend/app/pages/esg/results.vue

**Checkpoint**: L'historique des evaluations est visible avec un graphique d'evolution

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Qualite, dark mode, edge cases, couverture de tests

- [X] T041 [P] Verifier la compatibilite dark mode de tous les composants ESG dans frontend/app/components/esg/
- [X] T042 [P] Gerer les edge cases : reprise d'evaluation interrompue (status draft/in_progress) dans backend/app/modules/esg/service.py et backend/app/graph/nodes.py
- [X] T043 [P] Gerer le cas secteur sans benchmark (moyenne generale + message) dans backend/app/modules/esg/service.py
- [X] T044 Tests E2E du parcours complet : demarrer evaluation → repondre aux questions → voir resultats dans backend/tests/test_esg_e2e.py
- [X] T045 Verifier la couverture de tests >= 80% et completer si necessaire
- [X] T046 Mettre a jour CLAUDE.md avec les technologies et changements de la feature 005

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependance — demarrage immediat
- **Foundational (Phase 2)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Phase 2 — MVP, priorite absolue
- **US2 (Phase 4)**: Depend de Phase 2 + US1 (necessite des donnees d'evaluation)
- **US3 (Phase 5)**: Depend de Phase 2 + US1 (enrichit le noeud ESG existant)
- **US4 (Phase 6)**: Depend de Phase 2 + US1 (ajoute benchmark au scoring)
- **US5 (Phase 7)**: Depend de Phase 2 + US2 (ajoute historique a la page resultats)
- **Polish (Phase 8)**: Depend de toutes les phases precedentes

### User Story Dependencies

- **US1 (P1)**: Autonome apres Phase 2 — aucune dependance sur d'autres stories
- **US2 (P2)**: Utilise les endpoints et donnees de US1 (lecture seule)
- **US3 (P2)**: Modifie le noeud ESG de US1 (ajout RAG) — peut commencer en parallele de US2
- **US4 (P3)**: Modifie le service et le prompt de US1 (ajout benchmark) — peut commencer en parallele de US2/US3
- **US5 (P3)**: Depend de US2 (composant sur la page resultats)

### Within Each User Story

- Tests ecrits EN PREMIER (RED) → doivent echouer
- Modeles/schemas avant services
- Services avant noeuds/endpoints
- Implementation backend avant frontend
- Verification que les tests passent (GREEN) apres implementation

### Parallel Opportunities

- T002, T003, T004 en parallele (Phase 1)
- T005, T007, T008 en parallele apres T001 (Phase 2)
- T010, T011, T012 en parallele (tests US1)
- T021-T026 en parallele (composants frontend US2)
- US2 et US3 peuvent demarrer en parallele apres US1
- US4 peut demarrer en parallele de US2/US3

---

## Parallel Example: User Story 1

```bash
# Lancer tous les tests US1 en parallele :
Task: "Tests unitaires du service de scoring dans backend/tests/test_esg_service.py"
Task: "Tests unitaires des criteres dans backend/tests/test_esg_criteria.py"
Task: "Tests du esg_scoring_node dans backend/tests/test_esg_scoring_node.py"

# Apres les tests, T018/T019 en parallele de T020 :
Task: "Router REST ESG dans backend/app/modules/esg/router.py"
Task: "Tests du router REST dans backend/tests/test_esg_router.py"
```

## Parallel Example: User Story 2

```bash
# Lancer tous les composants frontend en parallele :
Task: "Store Pinia ESG dans frontend/app/stores/esg.ts"
Task: "Composable useEsg dans frontend/app/composables/useEsg.ts"
Task: "ScoreCircle.vue dans frontend/app/components/esg/ScoreCircle.vue"
Task: "CriteriaProgress.vue dans frontend/app/components/esg/CriteriaProgress.vue"
Task: "StrengthsBadges.vue dans frontend/app/components/esg/StrengthsBadges.vue"
Task: "Recommendations.vue dans frontend/app/components/esg/Recommendations.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completer Phase 1: Setup (T001-T004)
2. Completer Phase 2: Foundational (T005-T009)
3. Completer Phase 3: User Story 1 (T010-T020)
4. **STOP et VALIDER** : Tester l'evaluation ESG conversationnelle de bout en bout via le chat
5. Deployer/demo si pret

### Incremental Delivery

1. Setup + Foundational → Infrastructure prete
2. Ajouter US1 → Evaluation conversationnelle → **MVP**
3. Ajouter US2 → Page resultats persistante → Demo
4. Ajouter US3 → Enrichissement RAG → Qualite amelioree
5. Ajouter US4 → Benchmark sectoriel → Contexte ajoute
6. Ajouter US5 → Historique → Suivi progression
7. Polish → Qualite finale

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = traçabilite vers la user story
- Constitution exige TDD : tests EN PREMIER pour chaque story
- Commit apres chaque tache ou groupe logique
- Arreter a n'importe quel checkpoint pour valider la story independamment
- Les blocs visuels (progress, chart, gauge, table, mermaid) sont deja implementes (feature 002) — pas besoin de les recreer
