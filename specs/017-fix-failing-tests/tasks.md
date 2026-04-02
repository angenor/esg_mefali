# Tasks: Correction des 34 tests en échec

**Input**: Design documents from `/specs/017-fix-failing-tests/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Non applicable — cette feature corrige des tests existants, pas de nouveaux tests à écrire.

**Organization**: Tasks groupées par user story pour permettre une implémentation et validation indépendante de chaque correction.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story associée (US1, US2, US3, US4, US5)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Fixtures partagés)

**Purpose**: Créer les fixtures et helpers partagés dans conftest.py qui seront utilisés par les phases suivantes

- [x] T001 Ajouter le fixture `override_auth` dans `backend/tests/conftest.py` — utilise `app.dependency_overrides[get_current_user]` avec un mock user (UUID, email, is_active=True), yield + cleanup
- [x] T002 Ajouter le helper `make_conversation_state(**overrides)` dans `backend/tests/conftest.py` — retourne un dict complet avec les 27 clés de ConversationState à leurs valeurs par défaut, accepte des overrides via kwargs

**Checkpoint**: Fixtures disponibles — les corrections par user story peuvent commencer

---

## Phase 2: User Story 1 — Correction auth 401 (15 tests) (Priority: P1) 🎯 MVP

**Goal**: Les 15 tests financing (status, intermédiaires, préparation) passent en utilisant le fixture `override_auth`

**Independent Test**: `pytest backend/tests/test_financing_status.py backend/tests/test_financing_intermediaries.py backend/tests/test_financing_preparation.py -v` → 15/15 pass

### Implementation

- [x] T003 [P] [US1] Modifier `backend/tests/test_financing_status.py` — supprimer les `@patch("app.api.deps.get_current_user")` locaux, ajouter `@pytest.mark.usefixtures("override_auth")` sur les 5 tests, supprimer le fixture `mock_user` local si devenu inutile
- [x] T004 [P] [US1] Modifier `backend/tests/test_financing_intermediaries.py` — supprimer les `@patch` auth locaux, ajouter `@pytest.mark.usefixtures("override_auth")` sur les 7 tests, supprimer le fixture `mock_user` local si devenu inutile
- [x] T005 [P] [US1] Modifier `backend/tests/test_financing_preparation.py` — supprimer les `@patch` auth locaux, ajouter `@pytest.mark.usefixtures("override_auth")` sur les 3 tests, supprimer le fixture `mock_user` local si devenu inutile

**Checkpoint**: 15 tests auth corrigés — vérifier avec pytest que tous passent

---

## Phase 3: User Story 2 — Correction state incomplet nodes (7 tests) (Priority: P1)

**Goal**: Les 7 tests financing node + credit node passent en utilisant `make_conversation_state()`

**Independent Test**: `pytest backend/tests/test_financing_node.py backend/tests/test_credit/test_node.py -v` → 7/7 pass

### Implementation

- [x] T006 [P] [US2] Modifier `backend/tests/test_financing_node.py` — remplacer les state dicts partiels par `make_conversation_state(...)` avec les overrides appropriés pour chaque test (messages, financing_data, esg_assessment selon le scénario)
- [x] T007 [P] [US2] Modifier `backend/tests/test_credit/test_node.py` — remplacer les state dicts partiels par `make_conversation_state(...)` avec les overrides appropriés (messages, credit_data selon le scénario)

**Checkpoint**: 7 tests state corrigés — vérifier avec pytest que tous passent

---

## Phase 4: User Story 3 — Correction Form vs JSON chat (3 tests) (Priority: P2)

**Goal**: Les 3 tests chat envoient des données Form au lieu de JSON

**Independent Test**: `pytest backend/tests/test_chat.py -v -k "send_message"` → 3/3 pass

### Implementation

- [x] T008 [US3] Modifier `backend/tests/test_chat.py` — remplacer `json={"content": "..."}` par `data={"content": "..."}` dans les 3 tests concernés (test_send_message_empty_content, test_send_message_persists, test_send_message_too_long)

**Checkpoint**: 3 tests chat corrigés

---

## Phase 5: User Story 4 — Correction mock type application node (1 test) (Priority: P2)

**Goal**: Le test application node utilise AIMessage + AsyncMock chain correcte

**Independent Test**: `pytest backend/tests/test_applications/test_node.py -v -k "test_application_node_returns_messages"` → 1/1 pass

### Implementation

- [x] T009 [US4] Modifier `backend/tests/test_applications/test_node.py` — remplacer `MagicMock()` par `AIMessage(content="...")` pour la réponse, utiliser `AsyncMock()` pour le LLM avec `mock_llm.bind_tools.return_value = mock_llm` et `mock_llm.ainvoke.return_value = mock_response`

**Checkpoint**: 1 test application corrigé

---

## Phase 6: User Story 5 — Correction WeasyPrint reports (6 tests) (Priority: P3)

**Goal**: Les 6 tests rapport passent sans bibliothèques système C installées

**Independent Test**: `pytest backend/tests/test_report_router.py backend/tests/test_report_service.py -v` → 6/6 pass

### Implementation

- [x] T010 [P] [US5] Modifier `backend/tests/test_report_router.py` — ajouter mock WeasyPrint via `patch.dict(sys.modules, {"weasyprint": mock_weasyprint})` avec `mock_weasyprint.HTML.return_value.write_pdf.return_value = b"%PDF-1.4..."` pour les 5 tests concernés
- [x] T011 [P] [US5] Modifier `backend/tests/test_report_service.py` — ajouter mock WeasyPrint via le même pattern `patch.dict(sys.modules)` pour le test `test_generate_report_success`

**Checkpoint**: 6 tests rapport corrigés

---

## Phase 7: Validation finale

**Purpose**: Vérifier zéro régression et 100% pass rate

- [x] T012 Lancer les 34 tests ciblés → 84/84 pass (tests existants + nouveaux tests détectés dans les fichiers)
- [x] T013 Lancer la suite complète (`pytest backend/ --tb=short -q`) → 907/907 pass, zéro régression
- [x] T014 Mettre à jour `documents_et_brouillons/failing-tests-audit.md` — marquer comme résolu

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Aucune dépendance — commence immédiatement
- **Phases 2-6 (User Stories)**: Toutes dépendent de Phase 1 (fixtures partagés)
- **Phase 7 (Validation)**: Dépend de la complétion de toutes les phases précédentes

### User Story Dependencies

- **US1 (Auth 401)**: Dépend de T001 (fixture override_auth)
- **US2 (State incomplet)**: Dépend de T002 (helper make_conversation_state)
- **US3 (Form vs JSON)**: Indépendant — ne dépend d'aucun fixture partagé
- **US4 (Mock type)**: Indépendant — ne dépend d'aucun fixture partagé
- **US5 (WeasyPrint)**: Indépendant — ne dépend d'aucun fixture partagé

### Parallel Opportunities

- T001 et T002 peuvent s'exécuter en parallèle (même fichier conftest.py mais sections indépendantes)
- T003, T004, T005 en parallèle (fichiers différents)
- T006, T007 en parallèle (fichiers différents)
- T008, T009 en parallèle (fichiers différents)
- T010, T011 en parallèle (fichiers différents)
- US3, US4, US5 en parallèle avec US1/US2 (aucune dépendance sur les fixtures)

---

## Parallel Example: Phase 2 (User Story 1)

```bash
# Après Phase 1 complétée, lancer les 3 corrections auth en parallèle :
Task T003: "Modifier test_financing_status.py — override_auth"
Task T004: "Modifier test_financing_intermediaries.py — override_auth"
Task T005: "Modifier test_financing_preparation.py — override_auth"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Compléter Phase 1: Fixtures partagés (T001, T002)
2. Compléter Phase 2: Auth 401 — 15 tests corrigés (T003-T005)
3. Compléter Phase 3: State incomplet — 7 tests corrigés (T006-T007)
4. **STOP et VALIDER**: 22/34 tests corrigés (65% du problème résolu)

### Full Delivery

5. Phase 4: Form/JSON (T008) — 3 tests supplémentaires
6. Phase 5: Mock type (T009) — 1 test supplémentaire
7. Phase 6: WeasyPrint (T010-T011) — 6 tests supplémentaires
8. Phase 7: Validation → 34/34 pass, 901/901 total

---

## Notes

- [P] = fichiers différents, pas de dépendances
- Aucun code de production modifié — uniquement des fichiers de test
- Commit recommandé après chaque phase (checkpoint)
- Les phases 4-6 sont totalement indépendantes entre elles et peuvent être traitées dans n'importe quel ordre
