# Tasks: Calculateur d'Empreinte Carbone Conversationnel

**Input**: Design documents from `/specs/007-carbon-footprint-calculator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus (constitution exige Test-First NON-NEGOTIABLE, couverture 80%+)

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, US3, US4, US5)
- Chemins absolus depuis la racine du repo

---

## Phase 1: Setup (Infrastructure partagee)

**Purpose**: Initialisation du module carbon et des dependances

- [X] T001 Creer la migration Alembic pour les tables carbon dans backend/alembic/versions/007_add_carbon_tables.py
- [X] T002 Creer les modeles SQLAlchemy CarbonAssessment et CarbonEmissionEntry dans backend/app/models/carbon.py
- [X] T003 Enregistrer les modeles carbon dans backend/app/models/__init__.py
- [X] T004 [P] Creer les constantes de facteurs d'emission dans backend/app/modules/carbon/emission_factors.py
- [X] T005 [P] Creer les donnees de benchmarks sectoriels dans backend/app/modules/carbon/benchmarks.py
- [X] T006 [P] Creer les types TypeScript carbon dans frontend/app/types/carbon.ts

---

## Phase 2: Foundational (Prerequisites bloquants)

**Purpose**: Infrastructure coeur que TOUTES les user stories necessitent

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

- [X] T007 Creer les schemas Pydantic (requete/reponse) dans backend/app/modules/carbon/schemas.py
- [X] T008 Creer le service CarbonService (CRUD assessments + calcul emissions) dans backend/app/modules/carbon/service.py
- [X] T009 Creer le router FastAPI avec les 6 endpoints dans backend/app/modules/carbon/router.py
- [X] T010 Enregistrer le carbon_router dans backend/app/main.py (prefix /api/carbon)
- [X] T011 Ajouter le champ carbon_data au ConversationState dans backend/app/graph/state.py
- [X] T012 Ajouter la detection d'intent carbone dans router_node dans backend/app/graph/nodes.py

**Checkpoint**: Module carbon installe, endpoints accessibles, state pret pour le carbon_node

---

## Phase 3: User Story 1 - Bilan carbone guide par conversation (Priority: P1) MVP

**Goal**: L'utilisateur complete un bilan carbone via le questionnaire conversationnel avec visualisations progressives dans le chat

**Independent Test**: Demarrer un bilan via le chat, repondre categorie par categorie, verifier les graphiques progressifs et le bilan final

### Tests for User Story 1

> **NOTE: Ecrire ces tests EN PREMIER, verifier qu'ils ECHOUENT avant l'implementation**

- [X] T013 [P] [US1] Tests unitaires du service carbon (calcul emissions, validation, CRUD) dans backend/tests/test_carbon_service.py
- [X] T014 [P] [US1] Tests integration des endpoints carbon (POST/GET assessments, POST entries, GET summary) dans backend/tests/test_carbon_router.py
- [X] T015 [P] [US1] Tests du carbon_node (progression categories, generation visualisations, reprise) dans backend/tests/test_carbon_node.py

### Implementation for User Story 1

- [X] T016 [US1] Creer le prompt systeme du carbon_node avec instructions visuelles dans backend/app/prompts/carbon.py
- [X] T017 [US1] Implementer le carbon_node dans backend/app/graph/nodes.py (machine a etats par categorie, questions contextualisees FR, generation blocs chart/gauge/table/timeline)
- [X] T018 [US1] Integrer le carbon_node dans le graphe LangGraph (routing depuis router_node, edges) dans backend/app/graph/graph.py
- [X] T019 [US1] Implementer la logique de calcul des emissions dans le service (application facteurs, conversion unites, totaux) dans backend/app/modules/carbon/service.py
- [X] T020 [US1] Implementer la sauvegarde des entrees et mise a jour du bilan dans le service dans backend/app/modules/carbon/service.py
- [X] T021 [US1] Implementer la validation des donnees (valeurs negatives, incoherentes) dans backend/app/modules/carbon/service.py
- [X] T022 [US1] Implementer la contrainte unicite bilan par annee dans backend/app/modules/carbon/service.py
- [X] T023 [US1] Implementer la reprise de bilan interrompu (detection bilan in_progress existant) dans backend/app/modules/carbon/service.py

**Checkpoint**: Le questionnaire conversationnel fonctionne de bout en bout dans le chat avec visualisations inline

---

## Phase 4: User Story 2 - Dashboard de resultats carbone (Priority: P2)

**Goal**: Page dediee /carbon/results affichant les resultats persistants du bilan avec visualisations interactives

**Independent Test**: Acceder a /carbon/results apres un bilan complete, verifier donut, equivalences, comparaison sectorielle

### Implementation for User Story 2

- [X] T024 [P] [US2] Creer le composable useCarbon.ts (API calls: list, get, summary, benchmark) dans frontend/app/composables/useCarbon.ts
- [X] T025 [P] [US2] Creer le store Pinia carbon dans frontend/app/stores/carbon.ts
- [X] T026 [US2] Creer la page resultats /carbon/results avec donut Chart.js, equivalences, comparaison sectorielle dans frontend/app/pages/carbon/results.vue
- [X] T027 [US2] Implementer le graphique d'evolution temporelle (multi-bilans) dans frontend/app/pages/carbon/results.vue
- [X] T028 [US2] Implementer l'endpoint GET /api/carbon/assessments/{id}/summary dans backend/app/modules/carbon/router.py (generation equivalences parlantes + benchmark)

**Checkpoint**: La page /carbon/results affiche les resultats de maniere coherente avec le chat

---

## Phase 5: User Story 3 - Plan de reduction personnalise (Priority: P2)

**Goal**: Plan de reduction carbone avec quick wins et actions long terme, economies FCFA, timeline

**Independent Test**: Completer un bilan et verifier que le plan contient au moins 3 quick wins et 3 actions long terme avec chiffrage

### Implementation for User Story 3

- [X] T029 [US3] Implementer la generation du plan de reduction dans le carbon_node (blocs table + timeline) dans backend/app/prompts/carbon.py
- [X] T030 [US3] Persister le plan de reduction dans CarbonAssessment.reduction_plan dans backend/app/modules/carbon/service.py
- [X] T031 [US3] Afficher la section plan de reduction sur la page resultats dans frontend/app/pages/carbon/results.vue

**Checkpoint**: Le plan de reduction s'affiche dans le chat (table + timeline) et sur la page resultats

---

## Phase 6: User Story 4 - Comparaison sectorielle (Priority: P3)

**Goal**: Comparaison de l'empreinte carbone avec la moyenne du secteur

**Independent Test**: Completer un bilan pour un secteur et verifier le graphique comparatif

### Implementation for User Story 4

- [X] T032 [US4] Implementer l'endpoint GET /api/carbon/benchmarks/{sector} avec fallback secteur similaire dans backend/app/modules/carbon/router.py
- [X] T033 [US4] Integrer la comparaison sectorielle dans le carbon_node (bloc chart bar) dans backend/app/graph/nodes.py
- [X] T034 [US4] Afficher la comparaison sectorielle sur la page resultats dans frontend/app/pages/carbon/results.vue

**Checkpoint**: Le benchmark sectoriel s'affiche dans le chat et sur la page resultats

---

## Phase 7: User Story 5 - Gestion des bilans (Priority: P3)

**Goal**: Page /carbon listant les bilans avec navigation vers les resultats, accessible depuis la sidebar

**Independent Test**: Creer plusieurs bilans, verifier la liste sur /carbon, naviguer vers les details

### Implementation for User Story 5

- [X] T035 [US5] Creer la page liste des bilans /carbon/index.vue dans frontend/app/pages/carbon/index.vue
- [X] T036 [US5] Ajouter l'entree "Empreinte Carbone" dans la sidebar dans frontend/app/components/layout/AppSidebar.vue
- [X] T037 [US5] Gerer l'etat vide (aucun bilan) avec redirection vers le chat dans frontend/app/pages/carbon/index.vue

**Checkpoint**: Navigation complete sidebar → liste bilans → resultats detailles

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Qualite, dark mode, edge cases

- [X] T038 [P] Appliquer le dark mode sur toutes les pages carbon (index.vue, results.vue) dans frontend/app/pages/carbon/
- [X] T039 [P] Verifier la couverture de tests >= 80% et completer si necessaire
- [X] T040 Mettre a jour CLAUDE.md avec les technologies et changements de la feature 007 dans CLAUDE.md
- [X] T041 Valider le quickstart.md (tester tous les scenarios manuellement)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependances — demarre immediatement
- **Foundational (Phase 2)**: Depend de Phase 1 — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Phase 2 — MVP, priorite maximale
- **US2 (Phase 4)**: Depend de Phase 2 + US1 (besoin de donnees de bilan)
- **US3 (Phase 5)**: Depend de Phase 2 + US1 (plan genere pendant le bilan)
- **US4 (Phase 6)**: Depend de Phase 2 + benchmarks.py (Phase 1)
- **US5 (Phase 7)**: Depend de Phase 2 (CRUD assessments)
- **Polish (Phase 8)**: Depend de toutes les user stories

### User Story Dependencies

- **US1 (P1)**: Apres Phase 2 — aucune dependance sur d'autres stories
- **US2 (P2)**: Apres US1 (affiche les resultats d'un bilan complete)
- **US3 (P2)**: Apres US1 (plan genere a la fin du bilan conversationnel)
- **US4 (P3)**: Peut demarrer apres Phase 2 (independant), mais s'integre avec US1/US2
- **US5 (P3)**: Peut demarrer apres Phase 2 (independant)

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant implementation
- Modeles avant services
- Services avant endpoints
- Backend avant frontend (pour les donnees)

### Parallel Opportunities

- T004/T005/T006 en parallele (Phase 1, fichiers differents)
- T013/T014/T015 en parallele (tests US1)
- T024/T025 en parallele (composable + store frontend)
- US4 et US5 en parallele (independantes)
- T038/T039 en parallele (Phase 8)

---

## Parallel Example: User Story 1

```bash
# Tests US1 en parallele :
Task: "Tests unitaires service carbon dans backend/tests/test_carbon_service.py"
Task: "Tests integration endpoints dans backend/tests/test_carbon_router.py"
Task: "Tests carbon_node dans backend/tests/test_carbon_node.py"
```

## Parallel Example: Phase 1

```bash
# Setup en parallele :
Task: "Facteurs d'emission dans backend/app/modules/carbon/emission_factors.py"
Task: "Benchmarks sectoriels dans backend/app/modules/carbon/benchmarks.py"
Task: "Types TypeScript dans frontend/app/types/carbon.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completer Phase 1: Setup
2. Completer Phase 2: Foundational (CRITIQUE — bloque tout)
3. Completer Phase 3: User Story 1 (bilan conversationnel + visualisations)
4. **STOP et VALIDER**: Tester le bilan de bout en bout dans le chat
5. Demo si pret

### Incremental Delivery

1. Setup + Foundational → Infrastructure prete
2. Ajouter US1 → Bilan conversationnel fonctionnel (MVP!)
3. Ajouter US2 + US3 → Dashboard resultats + plan de reduction
4. Ajouter US4 + US5 (en parallele) → Comparaison sectorielle + gestion bilans
5. Polish → Dark mode, couverture tests, documentation

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = traçabilite vers la user story de la spec
- Constitution Test-First : tous les tests ecrits AVANT implementation
- Commit apres chaque tache ou groupe logique
- Arret possible a chaque checkpoint pour validation independante
