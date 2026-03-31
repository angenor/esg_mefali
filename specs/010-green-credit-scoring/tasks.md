# Tasks: Scoring de Credit Vert Alternatif

**Input**: Design documents from `/specs/010-green-credit-scoring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Inclus — la constitution impose TDD (Test-First NON-NEGOTIABLE, couverture 80%+).

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, US3, US4, US5)
- Chemins de fichiers exacts inclus

---

## Phase 1: Setup

**Purpose**: Structure du module credit et modeles de base

- [x] T001 Creer la structure du module backend dans backend/app/modules/credit/__init__.py
- [x] T002 [P] Creer les modeles CreditScore et CreditDataPoint avec enums dans backend/app/models/credit.py
- [x] T003 [P] Creer les schemas Pydantic request/response dans backend/app/modules/credit/schemas.py
- [x] T004 Generer la migration Alembic pour les tables credit_scores et credit_data_points
- [x] T005 Ajouter credit_data et _route_credit au state LangGraph dans backend/app/graph/state.py
- [x] T006 Enregistrer le credit_router dans backend/app/main.py avec prefix /api/credit

---

## Phase 2: Foundational (Prerequisites bloquants)

**Purpose**: Algorithme de scoring et service metier — prerequis pour toutes les user stories

**CRITICAL**: Aucune user story ne peut commencer avant la fin de cette phase

- [x] T007 [P] Ecrire les tests du service de calcul de scoring dans backend/tests/test_credit/test_service.py (tests algorithme solvabilite, impact vert, score combine, confiance, interactions intermediaires)
- [x] T008 [P] Ecrire les tests du router dans backend/tests/test_credit/test_router.py (tests 5 endpoints : generate, score, breakdown, history, certificate)
- [x] T009 Implementer le service de scoring dans backend/app/modules/credit/service.py : fonctions calculate_solvability_score, calculate_green_impact_score, calculate_combined_score, calculate_confidence, collect_data_points, generate_recommendations
- [x] T010 Implementer le router REST dans backend/app/modules/credit/router.py : POST /generate, GET /score, GET /score/breakdown, GET /score/history, GET /score/certificate
- [x] T011 Creer le prompt systeme du credit_node dans backend/app/prompts/credit.py
- [x] T012 Verifier que les tests T007 et T008 passent, corriger si necessaire

**Checkpoint**: Service scoring fonctionnel, endpoints disponibles, tests verts

---

## Phase 3: User Story 1 — Generation du score de credit vert (Priority: P1) MVP

**Goal**: Generer un score combine solvabilite + impact vert avec integration des interactions intermediaires

**Independent Test**: POST /api/credit/generate retourne un score combine avec sous-scores et confiance. Un utilisateur avec intermediaires contactes a un meilleur score engagement.

### Tests US1

- [x] T013 [P] [US1] Test d'integration : generer un score pour un utilisateur avec donnees completes dans backend/tests/test_credit/test_service.py (section integration)
- [x] T014 [P] [US1] Test d'integration : generer un score avec donnees partielles → confiance faible dans backend/tests/test_credit/test_service.py
- [x] T015 [P] [US1] Test d'integration : comparer score engagement avec/sans interactions intermediaires dans backend/tests/test_credit/test_service.py

### Implementation US1

- [x] T016 [US1] Implementer la collecte des data points depuis le state LangGraph (profil, ESG, carbone, candidatures, intermediaires) dans backend/app/modules/credit/service.py fonction collect_data_points
- [x] T017 [US1] Implementer le calcul du sous-facteur engagement_seriousness avec barème intermediaires (contacting: +15, applying: +20, submitted: +30, accepted: +20 bonus) dans backend/app/modules/credit/service.py
- [x] T018 [US1] Implementer le calcul du sous-facteur green_projects avec poids differentie par statut candidature via intermediaire dans backend/app/modules/credit/service.py
- [x] T019 [US1] Implementer le calcul de confiance (couverture sources + fraicheur) dans backend/app/modules/credit/service.py fonction calculate_confidence
- [x] T020 [US1] Implementer la generation de recommandations personnalisees incluant suggestion intermediaire dans backend/app/modules/credit/service.py fonction generate_recommendations
- [x] T021 [US1] Implementer le verrou anti-generation simultanee dans backend/app/modules/credit/service.py (retourner 409 si generation en cours)
- [x] T022 [US1] Verifier que les tests T013-T015 passent

**Checkpoint**: POST /api/credit/generate fonctionnel, score calcule correctement, intermediaires integres

---

## Phase 4: User Story 2 — Consultation du detail et des facteurs (Priority: P1)

**Goal**: Page frontend avec jauges, radar, detail des facteurs, recommandations

**Independent Test**: La page /credit-score affiche le score combine, les sous-scores, le radar des facteurs avec mention des intermediaires, et les recommandations

### Tests US2

- [x] T023 [P] [US2] Ecrire les tests du composable useCreditScore dans frontend/tests/credit-score.test.ts (fetch score, breakdown, history, generate, certificate)
- [x] T024 [P] [US2] Ecrire les tests du store creditScore dans frontend/tests/credit-score.test.ts

### Implementation US2

- [x] T025 [P] [US2] Creer le store Pinia creditScore dans frontend/app/stores/creditScore.ts (state: score, breakdown, history, loading, error)
- [x] T026 [P] [US2] Creer le composable useCreditScore dans frontend/app/composables/useCreditScore.ts (generateScore, fetchScore, fetchBreakdown, fetchHistory, downloadCertificate)
- [x] T027 [US2] Creer le composant ScoreGauge (jauge circulaire score combine) dans frontend/app/components/credit/ScoreGauge.vue
- [x] T028 [P] [US2] Creer le composant SubScoreGauges (deux jauges solvabilite/impact) dans frontend/app/components/credit/SubScoreGauges.vue
- [x] T029 [P] [US2] Creer le composant FactorsRadar (graphique radar Chart.js des facteurs) dans frontend/app/components/credit/FactorsRadar.vue
- [x] T030 [P] [US2] Creer le composant DataCoverage (barres progression couverture sources) dans frontend/app/components/credit/DataCoverage.vue
- [x] T031 [P] [US2] Creer le composant Recommendations (liste actions amelioration avec suggestion intermediaire) dans frontend/app/components/credit/Recommendations.vue
- [x] T032 [US2] Creer la page principale /credit-score dans frontend/app/pages/credit-score/index.vue (assemblage composants, dark mode, etats vide/loading/erreur)
- [x] T033 [US2] Ajouter le lien /credit-score dans la navigation sidebar dans frontend/app/components/layout/AppSidebar.vue
- [x] T034 [US2] Verifier que les tests T023-T024 passent

**Checkpoint**: Page /credit-score affiche score, jauges, radar, recommandations avec dark mode

---

## Phase 5: User Story 3 — Affichage conversationnel dans le chat (Priority: P2)

**Goal**: credit_node LangGraph affiche jauges et radar dans les messages du chat

**Independent Test**: Demander "score de credit vert" dans le chat → reponse avec blocs gauge, chart radar, progress, mermaid

### Tests US3

- [x] T035 [P] [US3] Ecrire les tests du credit_node dans backend/tests/test_credit/test_node.py (detection intent, generation blocs visuels, gestion score absent)

### Implementation US3

- [x] T036 [US3] Implementer la detection credit dans le router_node : ajouter patterns credit dans backend/app/graph/nodes.py (fonction _detect_credit_request)
- [x] T037 [US3] Implementer le credit_node dans backend/app/graph/nodes.py : collecte state → calcul score → formatage blocs visuels (gauge, chart radar, progress, mermaid, chart line)
- [x] T038 [US3] Ajouter le noeud credit au graphe LangGraph dans backend/app/graph/graph.py (add_node, conditional_edge depuis router)
- [x] T039 [US3] Verifier que les tests T035 passent

**Checkpoint**: Chat repond avec visualisations credit (jauges, radar, parcours)

---

## Phase 6: User Story 4 — Historique et evolution du score (Priority: P2)

**Goal**: Graphique d'evolution temporelle des scores sur la page et dans le chat

**Independent Test**: Utilisateur avec 3+ versions de score voit un graphique lineaire d'evolution

### Implementation US4

- [x] T040 [P] [US4] Creer le composant ScoreHistory (graphique line Chart.js evolution temporelle) dans frontend/app/components/credit/ScoreHistory.vue
- [x] T041 [US4] Integrer ScoreHistory dans la page /credit-score (section historique, gestion cas 1 seul score) dans frontend/app/pages/credit-score/index.vue
- [x] T042 [US4] Ajouter le bloc chart line historique dans le credit_node (reponse chat) dans backend/app/graph/nodes.py

**Checkpoint**: Historique affiche sur la page et dans le chat

---

## Phase 7: User Story 5 — Attestation PDF (Priority: P3)

**Goal**: Generation et telechargement d'une attestation PDF du score

**Independent Test**: GET /api/credit/score/certificate retourne un PDF avec score, sous-scores, confiance, validite

### Tests US5

- [x] T043 [P] [US5] Ecrire les tests de generation PDF dans backend/tests/test_credit/test_certificate.py (contenu PDF, score expire, score absent)

### Implementation US5

- [x] T044 [P] [US5] Creer le template Jinja2 pour l'attestation dans backend/app/modules/credit/certificate_template.html (en-tete, scores, jauges SVG, facteurs, mention legale, date validite)
- [x] T045 [US5] Implementer la generation PDF via WeasyPrint dans backend/app/modules/credit/certificate.py (render Jinja2 → HTML → PDF bytes)
- [x] T046 [US5] Implementer l'endpoint GET /score/certificate dans backend/app/modules/credit/router.py (verification score valide, retour PDF)
- [x] T047 [P] [US5] Creer le composant CertificateButton (bouton telechargement attestation) dans frontend/app/components/credit/CertificateButton.vue
- [x] T048 [US5] Integrer CertificateButton dans la page /credit-score dans frontend/app/pages/credit-score/index.vue
- [x] T049 [US5] Verifier que les tests T043 passent

**Checkpoint**: Attestation PDF telechargeale depuis la page et l'API

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Qualite, performance, securite

- [x] T050 [P] Verifier la couverture de tests >= 80% sur le module credit (backend et frontend)
- [x] T051 [P] Verifier le dark mode complet sur la page /credit-score et tous les composants
- [x] T052 [P] Verifier les etats vides/erreur/loading sur la page /credit-score
- [x] T053 Verifier la gestion du score expire (message regeneration sur page et chat)
- [x] T054 Validation quickstart.md : suivre les etapes et verifier le parcours complet

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dependances — demarrage immediat
- **Foundational (Phase 2)**: Depend de Setup — BLOQUE toutes les user stories
- **US1 (Phase 3)**: Depend de Foundational — MVP
- **US2 (Phase 4)**: Depend de US1 (besoin des endpoints score/breakdown)
- **US3 (Phase 5)**: Depend de Foundational (service scoring) — peut se faire en parallele avec US2
- **US4 (Phase 6)**: Depend de US2 (composant dans la page) et US1 (historique)
- **US5 (Phase 7)**: Depend de US1 (score genere) — peut se faire en parallele avec US2/US3
- **Polish (Phase 8)**: Depend de toutes les user stories

### User Story Dependencies

- **US1 (P1)**: Apres Foundational — aucune dependance sur d'autres stories
- **US2 (P1)**: Apres US1 (endpoints backend necessaires)
- **US3 (P2)**: Apres Foundational — independant de US2
- **US4 (P2)**: Apres US2 (integration dans la page)
- **US5 (P3)**: Apres US1 — independant de US2/US3/US4

### Within Each User Story

- Tests DOIVENT etre ecrits et ECHOUER avant implementation
- Modeles avant services
- Services avant endpoints
- Core avant integration
- Story complete avant passage a la suivante

### Parallel Opportunities

- T002 + T003 (modeles + schemas en parallele)
- T007 + T008 (tests service + tests router en parallele)
- T013 + T014 + T015 (tests integration US1 en parallele)
- T025 + T026 (store + composable en parallele)
- T027 + T028 + T029 + T030 + T031 (composants frontend US2 en parallele)
- US3 + US5 en parallele (pas de dependances mutuelles)

---

## Parallel Example: User Story 2

```bash
# Lancer store et composable en parallele :
Task: "Creer le store Pinia creditScore dans frontend/app/stores/creditScore.ts"
Task: "Creer le composable useCreditScore dans frontend/app/composables/useCreditScore.ts"

# Lancer les 5 composants en parallele :
Task: "Creer ScoreGauge dans frontend/app/components/credit/ScoreGauge.vue"
Task: "Creer SubScoreGauges dans frontend/app/components/credit/SubScoreGauges.vue"
Task: "Creer FactorsRadar dans frontend/app/components/credit/FactorsRadar.vue"
Task: "Creer DataCoverage dans frontend/app/components/credit/DataCoverage.vue"
Task: "Creer Recommendations dans frontend/app/components/credit/Recommendations.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completer Phase 1: Setup
2. Completer Phase 2: Foundational (CRITICAL)
3. Completer Phase 3: US1 — Generation du score
4. **STOP et VALIDER**: Tester POST /api/credit/generate independamment
5. Deployer/demo si pret

### Incremental Delivery

1. Setup + Foundational → Base prete
2. US1 → Score genere → Test → Deploy (MVP!)
3. US2 → Page frontend → Test → Deploy
4. US3 + US5 en parallele → Chat + PDF → Test → Deploy
5. US4 → Historique → Test → Deploy
6. Polish → Qualite finale

---

## Notes

- [P] = fichiers differents, pas de dependances
- [Story] = lie a la user story pour tracabilite
- Chaque user story est testable independamment
- Verifier que les tests echouent AVANT d'implementer
- Commit apres chaque tache ou groupe logique
- Constitution : TDD obligatoire, couverture 80%+, dark mode, francais
