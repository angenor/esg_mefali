# Tasks: Fix Tool Persistence & Routing Bugs

**Input**: Design documents from `/specs/016-fix-tool-persistence-bugs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Inclus (constitution IV. Test-First NON-NEGOTIABLE)

**Organization**: Tasks groupées par user story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallèle (fichiers différents, pas de dépendance)
- **[Story]**: User story concernée (US1, US2, US3, US4, US5)
- Chemins absolus depuis la racine du projet

## Path Conventions

- **Backend**: `backend/app/`
- **Frontend**: `frontend/app/`
- **Tests backend**: `backend/tests/`
- **Tests frontend**: `frontend/tests/` ou `frontend/app/__tests__/`

---

## Phase 1: Setup

**Purpose**: Vérifier l'état actuel et préparer l'environnement

- [X] T001 Activer le venv et vérifier que les tests existants passent : `source backend/venv/bin/activate && cd backend && python -m pytest tests/ -x --tb=short`
- [X] T002 Vérifier que les tests frontend passent : `cd frontend && npm run test`

---

## Phase 2: Foundational (Pattern REGLE ABSOLUE)

**Purpose**: Aucun prérequis bloquant — les fichiers existent déjà. Cette phase documente le pattern commun.

**Aucune tâche bloquante** : les 5 user stories modifient des fichiers différents et peuvent être implémentées en parallèle après Phase 1.

---

## Phase 3: User Story 1 - Sauvegarde critères ESG (Priority: P1) — MVP

**Goal**: Le LLM appelle `batch_save_esg_criteria` ou `save_esg_criterion_score` après chaque réponse ESG de l'utilisateur, avec progression affichée.

**Independent Test**: Démarrer une évaluation ESG, répondre à une question environnementale, vérifier que `evaluated_criteria` en BDD n'est plus vide.

### Tests US1

- [X] T003 [P] [US1] Écrire le test unitaire vérifiant que le prompt ESG contient "REGLE ABSOLUE" et "batch_save_esg_criteria" dans `backend/tests/test_prompts/test_esg_scoring_prompt.py`
- [X] T004 [P] [US1] Écrire le test unitaire vérifiant que les tool_instructions du esg_scoring_node incluent `batch_save_esg_criteria` — dans `backend/tests/test_prompts/test_esg_node_tools.py`

### Implementation US1

- [X] T005 [US1] Remonter la section "SAUVEGARDE PAR LOT" avant "INSTRUCTIONS VISUELLES" et ajouter "REGLE ABSOLUE" dans `backend/app/prompts/esg_scoring.py`
- [X] T006 [US1] Modifier les tool_instructions dans esg_scoring_node (`backend/app/graph/nodes.py`) : ajouter `batch_save_esg_criteria` dans la liste des tools, reformuler en "REGLE ABSOLUE" impérative
- [X] T007 [US1] Vérifier que les tests T003 et T004 passent

**Checkpoint**: Le prompt ESG et le node contiennent "REGLE ABSOLUE" + batch_save_esg_criteria documenté. Test 3.2 devrait passer.

---

## Phase 4: User Story 2 - Sauvegarde entrées carbone (Priority: P1)

**Goal**: Le LLM appelle `save_emission_entry` pour chaque source d'émission identifiée dans le message de l'utilisateur.

**Independent Test**: Démarrer un bilan carbone, fournir une donnée d'électricité, vérifier que `entries` en BDD n'est plus vide.

### Tests US2

- [X] T008 [P] [US2] Écrire le test unitaire vérifiant que les tool_instructions du carbon_node contiennent "REGLE ABSOLUE" et "save_emission_entry" — dans `backend/tests/test_prompts/test_carbon_node_tools.py`

### Implementation US2

- [X] T009 [US2] Modifier les tool_instructions dans carbon_node (`backend/app/graph/nodes.py`) : remplacer le texte consultatif par "REGLE ABSOLUE" impérative
- [X] T010 [US2] Vérifier que le test T008 passe

**Checkpoint**: Le carbon_node contient "REGLE ABSOLUE" + save_emission_entry obligatoire. Test 4.2 devrait passer.

---

## Phase 5: User Story 3 - Recherche fonds via BDD (Priority: P2)

**Goal**: Le LLM appelle `search_compatible_funds` au lieu de répondre de mémoire sur les fonds disponibles.

**Independent Test**: Demander "Quels financements verts ?", vérifier que le tool search_compatible_funds est appelé et que SUNREF/FNDE apparaissent.

### Tests US3

- [X] T011 [P] [US3] Écrire le test unitaire vérifiant que le prompt financement NE CONTIENT PLUS la liste détaillée des 12 fonds et contient "REGLE ABSOLUE" — dans `backend/tests/test_prompts/test_financing_prompt.py`

### Implementation US3

- [X] T012 [US3] Modifier `backend/app/prompts/financing.py` : remplacer la section "BASE DE DONNEES DES FONDS" par mention courte avec `search_compatible_funds`
- [X] T013 [US3] Modifier `backend/app/prompts/financing.py` : remplacer la section "INTERMEDIAIRES" par référence aux résultats tools
- [X] T014 [US3] Renforcer les tool_instructions dans financing_node avec "REGLE ABSOLUE"
- [X] T015 [US3] Vérifier que le test T011 passe

**Checkpoint**: Le prompt financement ne contient plus les détails des fonds. Le LLM est forcé d'utiliser le tool. Test 5.1 devrait passer.

---

## Phase 6: User Story 4 - Rendu bloc gauge (Priority: P3)

**Goal**: Le bloc gauge s'affiche correctement dans le chat au lieu de rester bloqué sur "Génération du graphique..."

**Independent Test**: Déclencher un bloc gauge (demander complétion profil), vérifier qu'il rend un visuel et non le placeholder.

### Tests US4

- [X] T016 [P] [US4] Écrire le test unitaire vérifiant le parsing des blocs incomplets — dans `frontend/tests/components/MessageParser.test.ts`

### Implementation US4

- [X] T017 [US4] Modifier `frontend/app/components/chat/MessageParser.vue` : remplacer la condition `!segment.isComplete` par `!segment.isComplete && isStreaming`
- [X] T018 [US4] Vérifier que le test T016 passe

**Checkpoint**: Les blocs gauge incomplets post-streaming sont rendus avec fallback. Test 1.5 devrait passer.

---

## Phase 7: User Story 5 - Correction données inexistantes (Priority: P3)

**Goal**: L'assistant corrige l'utilisateur au lieu de proposer d'ajouter un site/entité inexistant(e).

**Independent Test**: Demander "bilan carbone de mon usine de Yamoussoukro", vérifier que l'assistant dit "pas de données pour Yamoussoukro" au lieu de proposer d'ajouter.

### Tests US5

- [X] T019 [P] [US5] Écrire le test unitaire vérifiant que le prompt système contient l'instruction de correction — dans `backend/tests/test_prompts/test_system_prompt_correction.py`

### Implementation US5

- [X] T020 [US5] Modifier `backend/app/prompts/system.py` : ajouter instruction de correction des données inexistantes dans `_format_profile_section()`
- [X] T021 [US5] Vérifier que le test T019 passe

**Checkpoint**: Le prompt système inclut l'instruction de correction. Test 12.1 devrait passer.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Vérification globale, zéro régression

- [X] T022 Exécuter la suite de tests backend complète : 867 passed, 33 failed (pré-existants), +13 nouveaux tests
- [X] T023 Exécuter la suite de tests frontend complète : 24 passed, +3 nouveaux tests
- [X] T024 Vérifier zéro régression : aucune régression introduite
- [X] T025 Mettre à jour `documents_et_brouillons/esg-mefali-test-plan.md` section "BUGS PENDANT LES TESTS" avec les résultats post-fix

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Pas de dépendance — démarre immédiatement
- **Phase 2 (Foundational)**: N/A — pas de tâche bloquante
- **Phase 3-7 (User Stories)**: Dépendent de Phase 1 uniquement. Peuvent démarrer en parallèle.
- **Phase 8 (Polish)**: Dépend de toutes les user stories complétées

### User Story Dependencies

- **US1 (ESG)**: Indépendant — modifie `prompts/esg_scoring.py` + `nodes.py` (esg_scoring_node)
- **US2 (Carbon)**: Indépendant — modifie `nodes.py` (carbon_node, lignes différentes de US1)
- **US3 (Financing)**: Indépendant — modifie `prompts/financing.py` + `nodes.py` (financing_node)
- **US4 (Gauge)**: Indépendant — modifie `frontend/` uniquement
- **US5 (Chat correction)**: Indépendant — modifie `prompts/system.py` uniquement

⚠️ **US1 et US2 modifient tous deux `nodes.py`** mais dans des sections différentes (lignes 601-615 vs 758-768). Peuvent être parallélisés si les edits ne conflictent pas.

### Within Each User Story

1. Test d'abord (RED) → doit échouer
2. Implémentation (GREEN) → doit passer
3. Vérification (checkpoint)

---

## Parallel Opportunities

```bash
# Toutes les user stories en parallèle (fichiers différents) :
US1: backend/app/prompts/esg_scoring.py + backend/app/graph/nodes.py (L601-615)
US2: backend/app/graph/nodes.py (L758-768)
US3: backend/app/prompts/financing.py + backend/app/graph/nodes.py (L868-876)
US4: frontend/app/components/chat/MessageParser.vue
US5: backend/app/prompts/system.py

# Tous les tests en parallèle :
T003 + T004 + T008 + T011 + T016 + T019
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 = P1)

1. Compléter Phase 1 (Setup/vérification)
2. Compléter US1 (ESG persistence) — le bug le plus critique
3. Compléter US2 (Carbon persistence) — même pattern, même priorité
4. **STOP et VALIDER** : Tester les tests 3.2 et 4.2 du plan de test
5. Les 2 bugs P1 corrigés = MVP fonctionnel

### Incremental Delivery

1. US1 + US2 → Test indépendamment → Bug systémique corrigé (MVP)
2. US3 → Test indépendamment → Fonds via BDD
3. US4 + US5 → Test indépendamment → Polish visuel + comportemental
4. Phase 8 → Validation globale

---

## Notes

- Les modifications sont principalement du texte (prompts) — risque de régression faible
- Le pattern "REGLE ABSOLUE" est déjà validé dans la branche 015 pour application/credit
- Attention aux conflits dans `nodes.py` si US1, US2, US3 sont édités en parallèle (sections différentes mais même fichier)
- Préférer l'édition séquentielle de `nodes.py` : US1 → US2 → US3
