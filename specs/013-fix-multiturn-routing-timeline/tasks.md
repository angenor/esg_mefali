# Tasks: Correction du Routing Multi-tour LangGraph et du Format Timeline

**Input**: Design documents from `/specs/013-fix-multiturn-routing-timeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus (constitution Test-First NON-NEGOTIABLE)

**Organization**: Tasks groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, US3, US4, US5, US6)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup

**Purpose**: Aucune initialisation necessaire — le projet existe. Cette phase est vide.

---

## Phase 2: Foundational (State + Router Core)

**Purpose**: Ajouter le mecanisme de module actif au state et la logique de base du routeur. BLOQUE toutes les user stories.

### Tests Foundational

- [X] T001 [P] Test unitaire : ConversationState accepte active_module et active_module_data dans backend/tests/test_graph/test_active_module.py
- [X] T002 [P] Test unitaire : router_node route vers active_module quand defini (sans changement de sujet) dans backend/tests/test_graph/test_active_module.py
- [X] T003 [P] Test unitaire : router_node detecte changement de sujet et reset active_module dans backend/tests/test_graph/test_active_module.py
- [X] T004 [P] Test unitaire : router_node reste dans le module actif en cas de doute (defaut securitaire) dans backend/tests/test_graph/test_active_module.py
- [X] T005 [P] Test unitaire : router_node classification normale quand active_module est null dans backend/tests/test_graph/test_active_module.py

### Implementation Foundational

- [X] T006 Ajouter les champs active_module (str | None) et active_module_data (dict | None) au ConversationState dans backend/app/graph/state.py
- [X] T007 Implementer la logique active_module dans router_node : (1) lire active_module du state, (2) si defini appel LLM classification binaire continuation/changement, (3) si continuation router via _route_* correspondant, (4) si changement reset et classifier normalement dans backend/app/graph/nodes.py
- [X] T008 Creer la fonction utilitaire _is_topic_continuation(message, active_module) qui effectue la classification LLM binaire avec defaut True en cas d'erreur dans backend/app/graph/nodes.py
- [X] T009 Verifier que les tests T001-T005 passent

**Checkpoint**: Le routeur priorise active_module sur la classification. Les tests fondamentaux sont verts.

---

## Phase 3: User Story 1 — Evaluation ESG multi-tour (Priority: P1)

**Goal**: Un echange ESG de 5 questions-reponses successives sauvegarde les 5 criteres en base.

**Independent Test**: Envoyer 5 messages successifs dans un echange ESG et verifier les 5 criteres sauvegardes.

### Tests US1

- [X] T010 [P] [US1] Test integration : esg_scoring_node active active_module="esg_scoring" au demarrage dans backend/tests/test_graph/test_active_module.py
- [X] T011 [P] [US1] Test integration : esg_scoring_node desactive active_module a la finalisation dans backend/tests/test_graph/test_active_module.py
- [X] T012 [P] [US1] Test integration : echange ESG 3 Q/R successives sauvegarde 3 criteres dans backend/tests/test_graph/test_active_module.py
- [X] T013 [P] [US1] Test unitaire : message court ("oui", "non") pendant ESG actif reste dans esg_scoring_node dans backend/tests/test_graph/test_active_module.py

### Implementation US1

- [X] T014 [US1] Modifier esg_scoring_node pour activer active_module="esg_scoring" et active_module_data={assessment_id, criteria_remaining, criteria_evaluated} au demarrage de session dans backend/app/graph/nodes.py
- [X] T015 [US1] Modifier esg_scoring_node pour mettre a jour active_module_data apres chaque critere evalue dans backend/app/graph/nodes.py
- [X] T016 [US1] Modifier esg_scoring_node pour remettre active_module=None et active_module_data=None a la finalisation dans backend/app/graph/nodes.py
- [X] T017 [US1] Verifier que les tests T010-T013 passent

**Checkpoint**: L'evaluation ESG multi-tour fonctionne. Les criteres sont sauvegardes successivement.

---

## Phase 4: User Story 2 — Bilan carbone multi-tour (Priority: P1)

**Goal**: Un echange carbone de 3 entrees successives sauvegarde les 3 entrees en base.

**Independent Test**: Envoyer 3 messages de consommation et verifier les 3 entrees en base.

### Tests US2

- [X] T018 [P] [US2] Test integration : carbon_node active active_module="carbon" au demarrage dans backend/tests/test_graph/test_active_module.py
- [X] T019 [P] [US2] Test integration : echange carbone 3 entrees successives sauvegarde 3 entrees dans backend/tests/test_graph/test_active_module.py

### Implementation US2

- [X] T020 [US2] Modifier carbon_node pour activer active_module="carbon" et active_module_data={assessment_id, entries_collected, current_category} au demarrage de session dans backend/app/graph/nodes.py
- [X] T021 [US2] Modifier carbon_node pour mettre a jour active_module_data apres chaque entree collectee dans backend/app/graph/nodes.py
- [X] T022 [US2] Modifier carbon_node pour remettre active_module=None a la finalisation dans backend/app/graph/nodes.py
- [X] T023 [US2] Verifier que les tests T018-T019 passent

**Checkpoint**: Le bilan carbone multi-tour fonctionne. Les entrees sont sauvegardees successivement.

---

## Phase 5: User Story 3 — Changement de module en cours de session (Priority: P2)

**Goal**: Un changement de sujet en milieu de module est detecte et le routing bascule correctement.

**Independent Test**: Demarrer un bilan carbone, dire "Parlons de financement", verifier le basculement.

### Tests US3

- [X] T024 [P] [US3] Test : "Parlons plutot de financement" pendant un bilan carbone → routing bascule vers financing_node dans backend/tests/test_graph/test_active_module.py
- [X] T025 [P] [US3] Test : "Stop, je veux parler d'autre chose" pendant un ESG → routing bascule vers chat_node dans backend/tests/test_graph/test_active_module.py
- [X] T026 [P] [US3] Test : transition directe carbone → financement sans passer par null dans backend/tests/test_graph/test_active_module.py
- [X] T027 [P] [US3] Test : module suspendu reste in_progress en base (pas de perte de donnees) dans backend/tests/test_graph/test_active_module.py

### Implementation US3

- [X] T028 [US3] Implementer la transition directe entre modules dans router_node : si changement de sujet detecte ET nouveau module identifie → active_module = nouveau module directement dans backend/app/graph/nodes.py
- [X] T029 [US3] S'assurer que la suspension d'un module ne modifie pas son statut en base (reste in_progress) dans backend/app/graph/nodes.py
- [X] T030 [US3] Verifier que les tests T024-T027 passent

**Checkpoint**: Le changement de module fonctionne avec suspension propre de la session en cours.

---

## Phase 6: User Story 4 — Reprise de module apres interruption (Priority: P2)

**Goal**: Apres interruption, l'utilisateur peut reprendre un module la ou il s'etait arrete.

**Independent Test**: Quitter un ESG, envoyer un message general, dire "Continuons l'ESG" → reprise.

### Tests US4

- [X] T031 [P] [US4] Test : "Continuons l'evaluation ESG" avec un ESG in_progress en base → reprend au bon critere dans backend/tests/test_graph/test_active_module.py
- [X] T032 [P] [US4] Test : "On reprend le bilan carbone" avec un carbone in_progress → reprend avec les entrees collectees dans backend/tests/test_graph/test_active_module.py

### Implementation US4

- [X] T033 [US4] Modifier esg_scoring_node pour lire l'evaluation in_progress depuis la base quand active_module est active mais active_module_data est vide dans backend/app/graph/nodes.py
- [X] T034 [US4] Modifier carbon_node pour lire le bilan in_progress depuis la base dans le meme cas dans backend/app/graph/nodes.py
- [X] T035 [US4] Modifier router_node pour detecter les intentions de reprise ("continuons", "reprenons") et router vers le bon module en requetant la base pour les sessions in_progress dans backend/app/graph/nodes.py
- [X] T036 [US4] Verifier que les tests T031-T032 passent

**Checkpoint**: La reprise de module fonctionne pour ESG et carbone.

---

## Phase 7: User Story 5 — Recherche de financement multi-tour (Priority: P2)

**Goal**: Les reponses aux questions de suivi financement restent dans le noeud financement.

**Independent Test**: Dire "Quels financements pour moi ?", verifier search_compatible_funds appele, repondre "Oui le SUNREF" → reste dans financement.

### Tests US5

- [X] T037 [P] [US5] Test : financing_node active active_module="financing" quand search_compatible_funds est appele dans backend/tests/test_graph/test_active_module.py
- [X] T038 [P] [US5] Test : "Oui le SUNREF m'interesse" pendant financement actif → reste dans financing_node dans backend/tests/test_graph/test_active_module.py

### Implementation US5

- [X] T039 [US5] Modifier financing_node pour activer active_module="financing" et active_module_data au demarrage de session dans backend/app/graph/nodes.py
- [X] T040 [US5] Modifier financing_node pour desactiver active_module a la finalisation dans backend/app/graph/nodes.py
- [X] T041 [US5] Appliquer le meme pattern active_module aux noeuds application_node, credit_node, action_plan_node dans backend/app/graph/nodes.py
- [X] T042 [US5] Verifier que les tests T037-T038 passent

**Checkpoint**: Tous les noeuds specialistes gerent active_module. BUG-1 est entierement corrige.

---

## Phase 8: User Story 6 — Affichage correct des blocs timeline (Priority: P3)

**Goal**: Les blocs timeline s'affichent correctement quel que soit le format LLM (events, phases, items).

**Independent Test**: Simuler un bloc timeline avec "phases" au lieu de "events" → s'affiche correctement.

### Tests US6

- [X] T043 [P] [US6] Test frontend : TimelineBlock parse correctement {"events": [...]} dans frontend/tests/components/TimelineBlock.test.ts
- [X] T044 [P] [US6] Test frontend : TimelineBlock parse correctement {"phases": [...]} comme alias dans frontend/tests/components/TimelineBlock.test.ts
- [X] T045 [P] [US6] Test frontend : TimelineBlock parse les variantes de champs (period, name, state) dans frontend/tests/components/TimelineBlock.test.ts
- [X] T046 [P] [US6] Test frontend : TimelineBlock affiche erreur quand ni events ni phases dans frontend/tests/components/TimelineBlock.test.ts
- [X] T047 [P] [US6] Test frontend : TimelineBlock utilise "todo" par defaut quand status absent dans frontend/tests/components/TimelineBlock.test.ts
- [X] T048 [P] [US6] Test frontend : TimelineBlock gere le JSON invalide sans crash dans frontend/tests/components/TimelineBlock.test.ts

### Implementation US6

- [X] T049 [US6] Modifier TimelineBlock.vue pour normaliser les variantes de cle (phases/items/steps → events) et les aliases de champs (period→date, name→title, state→status, details→description) avec defaut status="todo" dans frontend/app/components/richblocks/TimelineBlock.vue
- [X] T050 [P] [US6] Modifier le prompt action_plan.py : remplacer le format {"phases":[...]} par {"events":[...]} avec champs date/title/status/description dans backend/app/prompts/action_plan.py
- [X] T051 [P] [US6] Modifier le prompt carbon.py : remplacer le format {"items":[...]} par {"events":[...]} dans backend/app/prompts/carbon.py
- [X] T052 [P] [US6] Modifier le prompt financing.py : remplacer le format {"items":[...]} par {"events":[...]} dans backend/app/prompts/financing.py
- [X] T053 [US6] Verifier que les tests T043-T048 passent

**Checkpoint**: BUG-2 est corrige. Les timelines s'affichent correctement.

---

## Phase 9: Polish & Non-Regression

**Purpose**: Zero regression, validation complete

- [X] T054 Executer la suite de tests backend complete (python -m pytest tests/ -v) et verifier zero regression sur les 796 tests passants dans backend/
- [X] T055 Executer les tests frontend (npx vitest run) et verifier zero regression dans frontend/
- [ ] T056 Verification manuelle du parcours multi-tour complet selon quickstart.md
- [X] T057 Mettre a jour CLAUDE.md section Recent Changes avec le resume de la feature 013 dans CLAUDE.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Vide — pas de setup necessaire
- **Phase 2 (Foundational)**: BLOQUE toutes les user stories — state + router core
- **Phase 3 (US1 ESG)**: Depend de Phase 2
- **Phase 4 (US2 Carbon)**: Depend de Phase 2, independant de US1
- **Phase 5 (US3 Changement)**: Depend de Phase 2 + au moins un noeud modifie (US1 ou US2)
- **Phase 6 (US4 Reprise)**: Depend de Phase 2 + US1 ou US2 (pour avoir un module testable)
- **Phase 7 (US5 Financement)**: Depend de Phase 2, independant de US1/US2
- **Phase 8 (US6 Timeline)**: Independant de toutes les autres phases (BUG-2 est distinct)
- **Phase 9 (Polish)**: Depend de toutes les phases precedentes

### User Story Dependencies

- **US1 (ESG P1)**: Phase 2 uniquement
- **US2 (Carbon P1)**: Phase 2 uniquement — peut tourner en parallele avec US1
- **US3 (Changement P2)**: Phase 2 + au moins US1 ou US2 (besoin d'un module fonctionnel pour tester)
- **US4 (Reprise P2)**: Phase 2 + au moins US1 ou US2
- **US5 (Financement P2)**: Phase 2 uniquement — peut tourner en parallele avec US1/US2
- **US6 (Timeline P3)**: Aucune dependance sur les autres US — peut tourner en parallele avec tout

### Within Each User Story

- Tests ecrits AVANT implementation (TDD)
- Tests doivent ECHOUER avant implementation
- Implementation minimale pour faire passer les tests
- Verification des tests apres implementation

### Parallel Opportunities

- US1, US2, US5 peuvent tourner en parallele apres Phase 2
- US6 (timeline) peut tourner en parallele avec TOUT le reste (BUG-2 est independant)
- T043-T048 (tests frontend timeline) peuvent tous tourner en parallele
- T050-T052 (prompts) peuvent tous tourner en parallele

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Lancer tous les tests en parallele :
Task T001: "Test ConversationState active_module"
Task T002: "Test router route vers active_module"
Task T003: "Test router detecte changement sujet"
Task T004: "Test router defaut securitaire"
Task T005: "Test router classification normale"

# Puis implementation sequentielle :
Task T006: "Ajouter champs au state"
Task T007: "Logique router"
Task T008: "Fonction _is_topic_continuation"
```

## Parallel Example: US6 (Timeline)

```bash
# Tous les tests frontend en parallele :
Task T043-T048: tous dans le meme fichier mais independants

# Prompts en parallele :
Task T050: "action_plan.py"
Task T051: "carbon.py"
Task T052: "financing.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 = BUG-1 Core)

1. Complete Phase 2: State + Router (CRITIQUE)
2. Complete Phase 3: US1 (ESG multi-tour)
3. Complete Phase 4: US2 (Carbon multi-tour)
4. **STOP et VALIDER**: Les 2 workflows principaux fonctionnent
5. Les 20+ tests bloques par BUG-1 sont debloques

### Incremental Delivery

1. Phase 2 → Fondation prete
2. US1 + US2 → MVP (BUG-1 core resolu)
3. US3 + US4 → Experience complete (changement + reprise)
4. US5 → Tous les modules couverts
5. US6 → BUG-2 resolu (timeline)
6. Phase 9 → Non-regression validee

---

## Notes

- Le fichier principal modifie est backend/app/graph/nodes.py (router_node + noeuds specialistes)
- La majorite des tests sont dans un seul fichier backend/tests/test_graph/test_active_module.py
- US6 (timeline) est completement independante et peut etre faite a tout moment
- Commit apres chaque phase completee
