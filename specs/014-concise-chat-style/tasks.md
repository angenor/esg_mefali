# Tasks: Style de communication concis

**Input**: Design documents from `/specs/014-concise-chat-style/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Inclus (constitution IV. Test-First).

**Organization**: Tasks groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story associee (US1, US2, US3)
- Chemins exacts dans les descriptions

---

## Phase 1: Setup

**Purpose**: Aucune initialisation de projet necessaire — tous les fichiers existent deja.

- [x] T001 Creer le fichier de tests `backend/tests/test_prompts/test_style_instruction.py` avec la structure de base (imports, fixtures)

---

## Phase 2: Foundational (Prerequis bloquants)

**Purpose**: Definir la constante STYLE_INSTRUCTION et le helper d'onboarding — prerequis pour toutes les user stories.

- [x] T002 Definir la constante `STYLE_INSTRUCTION` dans `backend/app/prompts/system.py` apres `DOCUMENT_VISUAL_INSTRUCTIONS` — contient les regles de concision (FR-001 a FR-006, FR-009), les exemples BON/MAUVAIS (FR-008), et la regle "chaque mot = info nouvelle ou action concrete"
- [x] T003 Ajouter la fonction `_has_minimum_profile(profile: dict) -> bool` dans `backend/app/prompts/system.py` — retourne True si le profil a >= 2 champs renseignes (condition post-onboarding pour FR-010)

**Checkpoint**: `STYLE_INSTRUCTION` et `_has_minimum_profile` disponibles pour import.

---

## Phase 3: User Story 1 - Reponses concises apres un bloc visuel (Priority: P1) MVP

**Goal**: L'assistant ne repete plus en texte les informations deja presentes dans les blocs visuels. Max 2-3 phrases d'accompagnement par bloc.

**Independent Test**: Appeler `build_esg_prompt()` / `build_carbon_prompt()` et verifier que le prompt contient l'instruction de style concis.

### Tests US1

- [x] T004 [P] [US1] Ecrire `test_style_instruction_in_esg_prompt` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie que `build_esg_prompt()` contient STYLE_INSTRUCTION
- [x] T005 [P] [US1] Ecrire `test_style_instruction_in_carbon_prompt` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie que `build_carbon_prompt()` contient STYLE_INSTRUCTION
- [x] T006 [P] [US1] Ecrire `test_style_instruction_in_all_specialized_prompts` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie les 6 modules (financing, credit, application, action_plan inclus)
- [x] T007 [P] [US1] Ecrire `test_style_instruction_contains_examples` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie que STYLE_INSTRUCTION contient au moins un exemple BON et un MAUVAIS

### Implementation US1

- [x] T008 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_esg_prompt()` dans `backend/app/prompts/esg_scoring.py`
- [x] T009 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_carbon_prompt()` dans `backend/app/prompts/carbon.py`
- [x] T010 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_financing_prompt()` dans `backend/app/prompts/financing.py`
- [x] T011 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_credit_prompt()` dans `backend/app/prompts/credit.py`
- [x] T012 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_application_prompt()` dans `backend/app/prompts/application.py`
- [x] T013 [P] [US1] Importer `STYLE_INSTRUCTION` et l'ajouter en fin de `build_action_plan_prompt()` dans `backend/app/prompts/action_plan.py`

**Checkpoint**: Tous les prompts specialises incluent STYLE_INSTRUCTION. Tests T004-T007 passent.

---

## Phase 4: User Story 2 - Pas de formules de politesse ni de recapitulatif (Priority: P1)

**Goal**: Le chat general (build_system_prompt) inclut STYLE_INSTRUCTION pour les utilisateurs profiles, et l'exclut pendant l'onboarding.

**Independent Test**: Appeler `build_system_prompt(user_profile={'sector': 'recyclage', 'city': 'Abidjan'})` et verifier la presence de STYLE_INSTRUCTION. Appeler sans profil et verifier son absence.

### Tests US2

- [x] T014 [P] [US2] Ecrire `test_style_instruction_present_with_profile` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie injection quand profil renseigne (>= 2 champs)
- [x] T015 [P] [US2] Ecrire `test_style_instruction_absent_without_profile` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie absence quand profil None
- [x] T016 [P] [US2] Ecrire `test_style_instruction_absent_minimal_profile` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie absence quand profil < 2 champs

### Implementation US2

- [x] T017 [US2] Modifier `build_system_prompt()` dans `backend/app/prompts/system.py` — ajouter injection conditionnelle de `STYLE_INSTRUCTION` quand `_has_minimum_profile(user_profile)` est True, apres les sections existantes

**Checkpoint**: Chat general injecte STYLE_INSTRUCTION post-onboarding, l'exclut pendant l'onboarding. Tests T014-T016 passent.

---

## Phase 5: User Story 3 - Chaque mot apporte une information nouvelle (Priority: P2)

**Goal**: Verifier que le contenu de STYLE_INSTRUCTION couvre bien toutes les regles de la spec (FR-001 a FR-009).

**Independent Test**: Inspecter la constante STYLE_INSTRUCTION et verifier la presence de chaque regle cle.

### Tests US3

- [x] T018 [US3] Ecrire `test_style_instruction_contains_rules` dans `backend/tests/test_prompts/test_style_instruction.py` — verifie que STYLE_INSTRUCTION contient les mots-cles de chaque regle (concis, redondance, politesse, recapitulatif, emoji, confirmation, information nouvelle)

### Implementation US3

- [x] T019 [US3] Relire et ajuster le texte de `STYLE_INSTRUCTION` dans `backend/app/prompts/system.py` si des regles manquent apres le test T018

**Checkpoint**: Toutes les regles de la spec sont couvertes dans le texte de STYLE_INSTRUCTION.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Validation finale et nettoyage.

- [x] T020 Executer la validation quickstart.md dans `backend/` — verifier que tous les imports fonctionnent et que les assertions passent
- [x] T021 Lancer `pytest backend/tests/test_prompts/test_style_instruction.py -v` et verifier 8/8 tests passent
- [x] T022 Lancer `pytest backend/tests/ -x -q` et verifier zero regression sur les tests existants

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Pas de dependance
- **Phase 2 (Foundational)**: Depend de Phase 1
- **Phase 3 (US1)**: Depend de Phase 2 — prompts specialises
- **Phase 4 (US2)**: Depend de Phase 2 — chat general (independant de US1)
- **Phase 5 (US3)**: Depend de Phase 2 — validation du contenu
- **Phase 6 (Polish)**: Depend de Phases 3, 4, 5

### User Story Dependencies

- **US1 (P1)**: Independant — modifie 6 fichiers de prompts specialises
- **US2 (P1)**: Independant — modifie uniquement `system.py` (build_system_prompt)
- **US3 (P2)**: Independant — valide/ajuste le contenu de STYLE_INSTRUCTION

### Parallel Opportunities

- T004-T007 (tests US1) en parallele
- T008-T013 (implementation US1) en parallele (6 fichiers differents)
- T014-T016 (tests US2) en parallele
- US1 et US2 en parallele (fichiers differents)

---

## Parallel Example: User Story 1

```bash
# Tests en parallele :
Task: "test_style_instruction_in_esg_prompt dans backend/tests/test_prompts/test_style_instruction.py"
Task: "test_style_instruction_in_carbon_prompt dans backend/tests/test_prompts/test_style_instruction.py"
Task: "test_style_instruction_in_all_specialized_prompts dans backend/tests/test_prompts/test_style_instruction.py"
Task: "test_style_instruction_contains_examples dans backend/tests/test_prompts/test_style_instruction.py"

# Implementation en parallele (6 fichiers differents) :
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/esg_scoring.py"
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/carbon.py"
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/financing.py"
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/credit.py"
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/application.py"
Task: "Injecter STYLE_INSTRUCTION dans backend/app/prompts/action_plan.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Phase 1 : Setup (T001)
2. Phase 2 : Foundational (T002, T003)
3. Phase 3 + 4 en parallele : US1 (prompts specialises) + US2 (chat general)
4. **STOP et VALIDER** : Tester manuellement une conversation ESG et verifier la concision
5. Deployer

### Incremental Delivery

1. Setup + Foundational → Constante prete
2. US1 → Prompts specialises concis → Tester
3. US2 → Chat general concis avec exception onboarding → Tester
4. US3 → Validation exhaustive des regles → Tester
5. Polish → Zero regression confirmee

---

## Notes

- 22 taches au total
- Pas de migration BDD, pas de nouveau endpoint, pas de nouveau composant frontend
- Modification de 7 fichiers Python existants + 1 fichier de test cree
- US1 et US2 peuvent s'executer en parallele (fichiers differents)
- Commit apres chaque phase pour faciliter le rollback
