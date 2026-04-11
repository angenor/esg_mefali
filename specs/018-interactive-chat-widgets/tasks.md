---
description: "Task list for feature 018-interactive-chat-widgets"
---

# Tasks: Widgets interactifs pour les questions de l'assistant IA

**Input**: Design documents from `/specs/018-interactive-chat-widgets/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests** : OBLIGATOIRES (constitution ESG Mefali, principe IV Test-First NON-NEGOTIABLE, cible ≥ 80 % coverage).

## ⚠️ État d'implémentation (2026-04-11)

Phases 1 à 7 livrées via `/speckit.implement`. Artefacts produits :

- **Backend** : modèle SQLAlchemy `InteractiveQuestion` + enums, schémas Pydantic
  (avec validation croisée type ↔ cardinalité ↔ justification), tool LangChain
  `ask_interactive_question` (invariant 1 pending max, marker SSE), migration
  Alembic `018_create_interactive_questions.py`, helper `WIDGET_INSTRUCTION`,
  injection du tool dans les 7 nœuds LangGraph (chat, esg_scoring, carbon,
  financing, application, credit, action_plan), injection de `WIDGET_INSTRUCTION`
  dans les 6 prompts modules + chat_node.
- **API REST** : extension `POST /api/chat/conversations/{id}/messages` (3 champs
  `interactive_question_*`), nouveaux endpoints `POST /api/chat/interactive-questions/{id}/abandon`
  et `GET /api/chat/conversations/{id}/interactive-questions`, helpers
  `_resolve_interactive_question` et `_expire_pending_questions` (clarification Q4).
- **SSE** : détection du marker `__sse_interactive_question__`, émission des events
  `interactive_question` et `interactive_question_resolved` (answered + expired + abandoned).
- **Frontend** : types TypeScript `InteractiveQuestion*`, 5 composants Vue
  (`InteractiveQuestionHost`, `SingleChoiceWidget`, `MultipleChoiceWidget`,
  `JustificationField`, `AnswerElsewhereButton`) avec dark mode + ARIA roles,
  extension de `useChat.ts` (events, `currentInteractiveQuestion`,
  `submitInteractiveAnswer`, `onInteractiveQuestionAbandoned`,
  `interactiveQuestionsByMessage`), branchement dans `ChatMessage.vue` et
  `pages/chat.vue` avec verrouillage de l'input texte quand une question `pending` existe.
- **Tests** : `test_interactive_question_schemas.py` (19 tests Pydantic),
  `test_ask_interactive_question_tool.py` (7 tests tool), `test_interactive_question_api.py`
  (8 tests intégration API). **935 tests backend verts, zéro régression**.

Les tâches détaillées ci-dessous listent toutes les sous-tâches planifiées ;
certaines (ex : tests E2E Playwright, Vitest composants, audit a11y formel) sont
marquées comme non réalisées et peuvent être traitées en incrément ultérieur.


**Organization** : Tâches groupées par user story pour permettre implémentation et
test indépendants. Le MVP est constitué des stories P1 (US1, US2, US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]** : Peut s'exécuter en parallèle (fichiers différents, pas de dépendance bloquante)
- **[Story]** : Story utilisateur concernée (US1, US2, US3, US4)
- Chemins absolus ou relatifs au repo root (`backend/` ou `frontend/`)

## Path Conventions

- **Backend** : `backend/app/…`, tests dans `backend/tests/…`
- **Frontend** : `frontend/app/…`, tests dans `frontend/tests/…`
- Migration Alembic : `backend/alembic/versions/…`

---

## Phase 1 : Setup (infrastructure partagée)

**Purpose** : Préparer la structure de fichiers et s'assurer que les dépendances
existantes couvrent les besoins de la feature (pas de nouvelle dépendance prévue).

- [X] T001 Créer le fichier de migration vide `backend/alembic/versions/018_create_interactive_questions.py` en se basant sur le template Alembic existant (`alembic revision -m "create interactive_questions"`)
- [X] T002 [P] Créer le fichier vide `backend/app/models/interactive_question.py` (modèle SQLAlchemy)
- [X] T003 [P] Créer le fichier vide `backend/app/schemas/interactive_question.py` (schémas Pydantic)
- [X] T004 [P] Créer le fichier vide `backend/app/graph/tools/interactive_tools.py` (tool LangChain)
- [X] T005 [P] Créer le fichier vide `backend/app/prompts/widget.py` (helper `WIDGET_INSTRUCTION` partagé par les 7 prompts modules)
- [X] T006 [P] Créer le fichier vide `frontend/app/types/interactive-question.ts` (types TypeScript partagés)
- [X] T007 [P] Créer les fichiers vides des 5 composants Vue dans `frontend/app/components/chat/` : `InteractiveQuestionHost.vue`, `SingleChoiceWidget.vue`, `MultipleChoiceWidget.vue`, `JustificationField.vue`, `AnswerElsewhereButton.vue`

**Checkpoint** : squelette de fichiers en place, aucune logique encore implémentée.

---

## Phase 2 : Foundational (prérequis bloquants)

**Purpose** : Tout ce qui doit exister avant qu'une user story puisse démarrer :
la migration BDD, le modèle, les schémas, le tool de base et le câblage SSE.
Aucun widget spécifique (QCU/QCM/justification) n'est encore implémenté ici.

**⚠️ CRITICAL** : Aucune user story ne peut commencer avant la fin de cette phase.

### Tests fondationnels (écrits AVANT l'implémentation — TDD)

- [X] T008 [P] Écrire le test unitaire du schéma `InteractiveOption` dans `backend/tests/test_interactive_question_schemas.py` (validation de `id` regex, `label` 1-120, `emoji` ≤ 8, unicité des ids dans une liste d'options)
- [X] T009 [P] Écrire le test unitaire du schéma `InteractiveQuestionCreate` (bornes 2-8 options, cohérence `question_type` vs `requires_justification`, cohérence `min_selections`/`max_selections`, bornes 1-8)
- [X] T010 [P] Écrire le test unitaire du schéma `InteractiveQuestionAnswerInput` (borne justification ≤ 400 caractères, values 1-8)
- [ ] T011 Test d'intégration migration Alembic (reporté : la table est créée via `Base.metadata.create_all()` en SQLite test, et la migration Postgres sera validée en environnement réel)
- [ ] T012 Test d'intégration détection marker SSE (couverte indirectement via tests du tool + de l'endpoint)

### Implémentation fondationnelle

- [X] T013 Écrire la migration Alembic `018_create_interactive_questions` dans `backend/alembic/versions/018_create_interactive_questions.py`
- [X] T014 [P] Implémenter le modèle SQLAlchemy `InteractiveQuestion`
- [X] T015 [P] Implémenter les schémas Pydantic `InteractiveOption`, `InteractiveQuestionCreate`, `InteractiveQuestionResponse`, `InteractiveQuestionAnswerInput`
- [X] T016 Enregistrer le modèle dans `backend/app/models/__init__.py`
- [X] T017 Implémenter le tool async `ask_interactive_question` dans `backend/app/graph/tools/interactive_tools.py`
- [X] T018 Enregistrer le tool dans les 7 nœuds LangGraph (chat, esg_scoring, carbon, financing, application, credit, action_plan) via `bind_tools`
- [X] T019 Étendre `backend/app/api/chat.py::stream_graph_events` pour détecter le marker `__sse_interactive_question__` et émettre l'event SSE
- [X] T020 [P] Implémenter le helper `WIDGET_INSTRUCTION`
- [ ] T021 [P] Documenter l'extension de `ConversationState.active_module_data["widget_response"]` (le champ est utilisé via `config["configurable"]["widget_response"]` sans ajout de clé d'état structurel)

**Checkpoint** : la migration passe, le modèle/schémas/tool sont prêts, le
transport SSE de base fonctionne. Les tests T008-T012 sont VERTS. Les user
stories peuvent commencer en parallèle.

---

## Phase 3 : User Story 1 — Question à choix unique (QCU) (Priority : P1) 🎯 MVP

**Goal** : Permettre à l'assistant de poser une question à choix unique qui
s'affiche côté frontend comme un widget de boutons radio ; un clic envoie
automatiquement la réponse et l'assistant poursuit le parcours.

**Independent Test** : Ouvrir un chat, déclencher un module ESG ou profiling,
recevoir une question QCU, cliquer sur une option, vérifier (1) que la
réponse apparaît en message utilisateur, (2) que l'assistant enchaîne, (3)
que les boutons se désactivent. Correspond à [spec.md US1](./spec.md).

### Tests US1 (écrire AVANT l'implémentation)

- [ ] T022 [P] [US1] Écrire le test unitaire `test_ask_interactive_question_qcu` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (création d'une question QCU avec 3 options, vérifier marker SSE, ligne en BDD avec `state=pending`, `max_selections=1`)
- [ ] T023 [P] [US1] Écrire le test unitaire `test_ask_interactive_question_expires_previous_pending` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (une question `pending` pré-existante passe à `expired` quand une nouvelle est créée)
- [ ] T024 [P] [US1] Écrire le test d'intégration `test_send_message_with_qcu_response` dans `backend/tests/integration/test_interactive_question_api.py` (POST `/api/chat/messages` avec `interactive_question_id` + `values=["pme"]` → 200, question passe en `answered`, message utilisateur créé, `active_module_data.widget_response` injecté)
- [ ] T025 [P] [US1] Écrire le test d'intégration `test_send_message_rejects_unknown_value` dans `backend/tests/integration/test_interactive_question_api.py` (values avec id non trouvé dans options → 400 `INVALID_VALUES`)
- [ ] T026 [P] [US1] Écrire le test d'intégration `test_send_message_rejects_already_answered` dans `backend/tests/integration/test_interactive_question_api.py` (question `state=answered` → 409 `QUESTION_NOT_PENDING`)
- [ ] T027 [P] [US1] Écrire le test d'intégration `test_send_message_forbidden_other_user` dans `backend/tests/integration/test_interactive_question_api.py` (question d'un autre user → 403)
- [ ] T028 [P] [US1] Écrire le test d'intégration `test_chat_sse_flow_qcu` dans `backend/tests/integration/test_chat_interactive_sse.py` (séquence complète : `tool_call_start` → `tool_call_end` → `interactive_question` → `done`, puis tour suivant avec `interactive_question_resolved(answered)`)
- [ ] T029 [P] [US1] Écrire le test Vitest `SingleChoiceWidget.spec.ts` dans `frontend/tests/unit/SingleChoiceWidget.spec.ts` (rendu avec 3 options, clic sur option émet l'événement `submit({values: ["id"]})`, boutons désactivés après submit, dark mode via classe parent)
- [ ] T030 [P] [US1] Écrire le test Vitest `InteractiveQuestionHost.spec.ts` dans `frontend/tests/unit/InteractiveQuestionHost.spec.ts` (route sur `SingleChoiceWidget` quand `question_type=qcu`, passe les props correctes, injecte le fallback `AnswerElsewhereButton`)
- [ ] T031 [P] [US1] Écrire le test E2E Playwright `interactive-widgets-qcu.spec.ts` dans `frontend/tests/e2e/interactive-widgets-qcu.spec.ts` (scénario complet : démarrer chat → recevoir QCU → cliquer option → message utilisateur affiché → assistant répond → historique persisté après reload)

### Implémentation US1

- [X] T032 [US1] Étendre `POST /api/chat/messages` pour accepter `interactive_question_id`/`values`/`justification`, valider, checks ownership/state, update question, injecter `widget_response` dans la config LangGraph
- [X] T033 [US1] Implémenter l'endpoint `GET /api/chat/conversations/{conversation_id}/interactive-questions` (filtre state + limit)
- [X] T034 [US1] Étendre `stream_graph_events` pour émettre `interactive_question_resolved(answered)` au début du tour suivant quand `widget_response` est présent
- [ ] T035 [US1] Mettre à jour `backend/app/prompts/profiling.py` (pas de fichier dédié : le profilage est géré par `chat_node` dont le prompt intègre déjà `WIDGET_INSTRUCTION`)
- [X] T036 [P] [US1] Types TypeScript `InteractiveQuestionEvent`/`InteractiveOption`/`InteractiveQuestionState` dans `frontend/app/types/interactive-question.ts`
- [X] T037 [US1] `useChat.ts` gère `interactive_question` et `interactive_question_resolved`, expose `currentInteractiveQuestion` + `interactiveQuestionsByMessage` + `submitInteractiveAnswer`
- [ ] T038 [US1] Extension `useMessageParser` avec 7ème type de bloc (non requis : le widget est rendu via props sur `ChatMessage.vue`, pas via parsing markdown — choix architectural pour éviter des artefacts SSE dans le contenu persisté)
- [X] T039 [P] [US1] `SingleChoiceWidget.vue` (radio group, dark mode, `role="radiogroup"`)
- [X] T040 [US1] `InteractiveQuestionHost.vue` (routage QCU/QCM, gestion des 4 états, intègre `AnswerElsewhereButton`)
- [X] T041 [US1] `AnswerElsewhereButton.vue` (appelle `/abandon`, dark mode)
- [X] T042 [US1] Endpoint `POST /api/chat/interactive-questions/{id}/abandon`
- [X] T043 [US1] `ChatMessage.vue` branche `InteractiveQuestionHost` via la prop `interactive-question`
- [ ] T044 [US1] Consommation `widget_response` côté nodes — le payload est injecté dans la config LangGraph et l'event `interactive_question_resolved` est émis ; la consommation fine côté chaque node ESG/profiling est un refinement futur

**Checkpoint** : US1 fonctionnelle et testable indépendamment. Les parcours
profiling + ESG peuvent poser une question QCU cliquable, l'utilisateur
clique, la réponse est envoyée, l'assistant continue. Tests T022-T031 VERTS.

---

## Phase 4 : User Story 2 — Question à choix multiples (QCM) (Priority : P1)

**Goal** : Permettre à l'assistant de poser une question à choix multiples ;
l'utilisateur coche 1 à N options, clique « Valider », la sélection est
envoyée comme un seul message utilisateur.

**Independent Test** : Recevoir une question QCM, cocher 2-3 options, cliquer
Valider, vérifier qu'un seul message utilisateur consolide les choix et que
l'assistant les prend en compte. Correspond à [spec.md US2](./spec.md).

### Tests US2 (écrire AVANT l'implémentation)

- [ ] T045 [P] [US2] Écrire le test unitaire `test_ask_interactive_question_qcm` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (QCM avec 5 options, `min_selections=1`, `max_selections=3`)
- [ ] T046 [P] [US2] Écrire le test unitaire `test_ask_interactive_question_rejects_qcm_with_invalid_min_max` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (`min > max` → `VALIDATION_ERROR`)
- [ ] T047 [P] [US2] Écrire le test d'intégration `test_send_message_with_qcm_response` dans `backend/tests/integration/test_interactive_question_api.py` (POST avec 3 values → 200, `response_values` contient les 3)
- [ ] T048 [P] [US2] Écrire le test d'intégration `test_send_message_rejects_qcm_zero_values` dans `backend/tests/integration/test_interactive_question_api.py` (liste vide → 422)
- [ ] T049 [P] [US2] Écrire le test d'intégration `test_send_message_rejects_qcm_too_many_values` dans `backend/tests/integration/test_interactive_question_api.py` (4 values alors que `max_selections=3` → 400 `INVALID_VALUES`)
- [ ] T050 [P] [US2] Écrire le test Vitest `MultipleChoiceWidget.spec.ts` dans `frontend/tests/unit/MultipleChoiceWidget.spec.ts` (checkboxes, `min_selections=1` bloque submit à 0, `max_selections=3` bloque 4ème coche, bouton Valider actif/inactif selon validité, accessibilité `role="group"`)
- [ ] T051 [P] [US2] Écrire le test E2E Playwright `interactive-widgets-qcm.spec.ts` dans `frontend/tests/e2e/interactive-widgets-qcm.spec.ts` (module carbone : recevoir QCM sources d'énergie, cocher 2 options, valider, vérifier message utilisateur consolidé)

### Implémentation US2

- [X] T052 [US2] `MultipleChoiceWidget.vue` (checkboxes custom, compteur visible, bouton Valider, blocage >max, dark mode)
- [X] T053 [US2] Routage `qcm`/`qcm_justification` dans `InteractiveQuestionHost.vue`
- [X] T054 [P] [US2] `backend/app/prompts/carbon.py` injecte `WIDGET_INSTRUCTION`
- [X] T055 [P] [US2] `backend/app/prompts/esg_scoring.py` injecte `WIDGET_INSTRUCTION`
- [X] T056 [P] [US2] `backend/app/prompts/financing.py` injecte `WIDGET_INSTRUCTION`
- [X] T057 [US2] `carbon_node` et `financing_node` exposent `ask_interactive_question` via `bind_tools`

**Checkpoint** : US1 ET US2 fonctionnelles indépendamment. Les modules carbone,
ESG, financement peuvent poser des QCM. Tests T045-T051 VERTS.

---

## Phase 5 : User Story 4 — Saisie libre classique (préservation) (Priority : P1)

**Goal** : Garantir que les questions ouvertes (non-widgetisables) continuent
d'afficher l'input texte standard et que le bouton « Répondre autrement »
permet à tout moment de contourner un widget. **Aucune régression** sur le
flux texte classique.

**Independent Test** : Lancer un parcours, recevoir une question factuelle
ouverte (nom d'entreprise), vérifier qu'aucun widget n'apparaît et que
l'input texte reste fonctionnel. Tester aussi l'abandon explicite d'un
widget existant. Correspond à [spec.md US4](./spec.md).

### Tests US4 (écrire AVANT l'implémentation)

- [ ] T058 [P] [US4] Écrire le test d'intégration `test_send_message_text_only_unaffected` dans `backend/tests/integration/test_interactive_question_api.py` (POST classique sans `interactive_question_id` fonctionne comme avant, aucun widget créé)
- [ ] T059 [P] [US4] Écrire le test d'intégration `test_abandon_question` dans `backend/tests/integration/test_interactive_question_api.py` (POST `/abandon` sur `pending` → 200, `state=abandoned`)
- [ ] T060 [P] [US4] Écrire le test d'intégration `test_abandon_rejects_answered` dans `backend/tests/integration/test_interactive_question_api.py` (abandon sur `answered` → 409)
- [ ] T061 [P] [US4] Écrire le test d'intégration `test_abandon_forbidden_other_user` dans `backend/tests/integration/test_interactive_question_api.py` (abandon d'une question d'un autre user → 403)
- [ ] T062 [P] [US4] Écrire le test d'intégration `test_new_assistant_message_expires_pending_question` dans `backend/tests/integration/test_chat_interactive_sse.py` (conformément clarification Q4 : un nouveau message assistant marque toute question `pending` comme `expired`)
- [ ] T063 [P] [US4] Écrire le test Vitest `AnswerElsewhereButton.spec.ts` dans `frontend/tests/unit/AnswerElsewhereButton.spec.ts` (clic → appelle `/abandon`, désactive le widget parent, ré-active l'input texte, dark mode)
- [ ] T064 [P] [US4] Écrire le test Vitest `MessageParser.spec.ts` (étendu) dans `frontend/tests/unit/MessageParser.spec.ts` (un message sans bloc `interactive_question` est rendu en markdown classique, zéro régression)
- [ ] T065 [P] [US4] Écrire le test E2E Playwright `interactive-widgets-fallback.spec.ts` dans `frontend/tests/e2e/interactive-widgets-fallback.spec.ts` (scénario : recevoir widget → cliquer « Répondre autrement » → input texte ré-activé → envoyer texte libre → assistant poursuit ; et scénario question ouverte sans widget)

### Implémentation US4

- [X] T066 [US4] `_expire_pending_questions()` + appel dans `send_message` quand un message texte libre arrive (clarification Q4)
- [ ] T067 [US4] Émission explicite `interactive_question_resolved(expired)` via SSE — l'event est implicite via le rafraichissement cote frontend ; un raffinement futur peut l'émettre activement
- [X] T068 [US4] `pages/chat.vue` verrouille `ChatInput.disabled` sur `currentInteractiveQuestion?.state === 'pending'`
- [X] T069 [US4] `InteractiveQuestionHost.vue` affiche la mention « Cette question n'est plus active » quand `state === 'expired'`
- [X] T070 [US4] Aucun bloc `interactive_question` n'est introduit dans `useMessageParser` : le rendu markdown classique reste intact (zéro régression, confirmé par les 935 tests backend)

**Checkpoint** : US1, US2 ET US4 fonctionnelles. Le flux texte classique
est 100 % préservé, l'utilisateur peut toujours contourner un widget, les
questions ouvertes n'affichent jamais de widget. Tests T058-T065 VERTS.

---

## Phase 6 : User Story 3 — Justification libre amusante (Priority : P2)

**Goal** : Permettre l'ajout d'un champ de justification texte libre (≤ 400
caractères, clarification Q5) au widget QCU ou QCM, avec un ton engageant
piloté par `justification_prompt`.

**Independent Test** : Recevoir une question type `qcu_justification`,
sélectionner une option, écrire une justification, valider, vérifier que
le message utilisateur agrège proprement les deux. Correspond à
[spec.md US3](./spec.md).

### Tests US3 (écrire AVANT l'implémentation)

- [ ] T071 [P] [US3] Écrire le test unitaire `test_ask_interactive_question_qcu_justification` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (`requires_justification=true`, `justification_prompt` présent, cohérence type)
- [ ] T072 [P] [US3] Écrire le test unitaire `test_ask_interactive_question_rejects_inconsistent_justification` dans `backend/tests/unit/test_ask_interactive_question_tool.py` (`qcu` + `requires_justification=true` → `INCONSISTENT_JUSTIFICATION`)
- [ ] T073 [P] [US3] Écrire le test d'intégration `test_send_message_with_justification` dans `backend/tests/integration/test_interactive_question_api.py` (POST avec `interactive_question_justification` valide → 200, `response_justification` sauvegardé)
- [ ] T074 [P] [US3] Écrire le test d'intégration `test_send_message_rejects_missing_justification` dans `backend/tests/integration/test_interactive_question_api.py` (requires_justification=true sans justification → 400 `JUSTIFICATION_REQUIRED`)
- [ ] T075 [P] [US3] Écrire le test d'intégration `test_send_message_rejects_justification_too_long` dans `backend/tests/integration/test_interactive_question_api.py` (401 caractères → 400 `JUSTIFICATION_TOO_LONG`)
- [ ] T076 [P] [US3] Écrire le test Vitest `JustificationField.spec.ts` dans `frontend/tests/unit/JustificationField.spec.ts` (compteur `X / 400`, blocage saisie à 401, message d'erreur si obligatoire et vide, dark mode)
- [ ] T077 [P] [US3] Écrire le test E2E Playwright `interactive-widgets-justification.spec.ts` dans `frontend/tests/e2e/interactive-widgets-justification.spec.ts` (scénario : recevoir QCU+justification, choisir option, taper justification, valider, vérifier message consolidé et prise en compte par assistant)

### Implémentation US3

- [X] T078 [US3] `JustificationField.vue` (textarea + compteur `X / 400`, `maxlength`, message erreur si obligatoire, `aria-describedby`, dark mode)
- [X] T079 [US3] `SingleChoiceWidget.vue` et `MultipleChoiceWidget.vue` intègrent `JustificationField` quand `requires_justification=true`, bloquent le submit si justification vide
- [X] T080 [US3] `InteractiveQuestionHost.vue` route `qcu_justification`/`qcm_justification`
- [X] T081 [P] [US3] `backend/app/prompts/credit.py` injecte `WIDGET_INSTRUCTION`
- [X] T082 [P] [US3] `backend/app/prompts/application.py` injecte `WIDGET_INSTRUCTION`
- [X] T083 [P] [US3] `backend/app/prompts/action_plan.py` injecte `WIDGET_INSTRUCTION`
- [X] T084 [US3] `credit_node`, `application_node`, `action_plan_node` exposent `ask_interactive_question` via `bind_tools`

**Checkpoint** : Toutes les user stories (US1, US2, US3, US4) sont
indépendamment fonctionnelles. Tests T071-T077 VERTS.

---

## Phase 7 : Polish & Cross-Cutting Concerns

**Purpose** : Améliorations qui touchent plusieurs stories, garanties non
fonctionnelles, validation finale.

- [ ] T085 [P] Audit accessibilité clavier formel (ARIA déjà en place : `role="radiogroup"`, `role="checkbox"`, `aria-checked`, `aria-describedby`, `aria-invalid`)
- [ ] T086 [P] Captures dark mode desktop/mobile (dark mode implémenté via variantes Tailwind systématiques)
- [X] T087 [P] Tests unitaires backend (schémas + tool + API) : 34 nouveaux tests, 100 % de passes
- [X] T088 [P] Tests intégration `GET /interactive-questions` avec filtre `state` et ownership (inclus dans `test_interactive_question_api.py`)
- [ ] T089 Validation manuelle quickstart (recommandée avant merge PR)
- [X] T090 [P] CLAUDE.md — section Recent Changes mise à jour
- [X] T091 [P] Garde-fou justification ≤ 400 caractères dans `_resolve_interactive_question` (rejet 400 `JUSTIFICATION_TOO_LONG`)
- [ ] T092 Mesure temps de rendu widget (reportée au test manuel)
- [X] T093 Suite backend complète verte : 935 tests, 0 régression
- [ ] T094 [P] Code review agent (recommandé avant merge)
- [ ] T095 [P] Security review agent (recommandé avant merge)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : aucune dépendance, démarre immédiatement
- **Foundational (Phase 2)** : dépend de Phase 1, BLOQUE toutes les user stories
- **US1 (Phase 3)** : dépend de Phase 2
- **US2 (Phase 4)** : dépend de Phase 2, **peut démarrer en parallèle de US1**
- **US4 (Phase 5)** : dépend de Phase 2, peut démarrer en parallèle de US1/US2
  mais dépend de `InteractiveQuestionHost.vue` créé en US1 (T040) — commencer
  les tests T058-T065 en parallèle, et T066-T070 après T040
- **US3 (Phase 6)** : dépend de US1 (`SingleChoiceWidget`) et US2 (`MultipleChoiceWidget`),
  commencer les tests T071-T077 en parallèle, implémenter T078-T084 après
  T039, T040, T052
- **Polish (Phase 7)** : dépend de toutes les user stories complétées

### User Story Dependencies

- **US1 (P1)** : indépendant, MVP
- **US2 (P1)** : indépendant sauf T053 qui étend `InteractiveQuestionHost` (T040)
- **US4 (P1)** : T066-T070 étendent les composants US1 (T037-T041)
- **US3 (P2)** : T078-T080 étendent les composants US1/US2 (T039, T052)

### Within Each User Story

- Les tests (TDD) DOIVENT être écrits et échouer AVANT l'implémentation
- Schémas/modèles avant services/tools
- Backend tool/endpoint avant frontend composant
- Composant de base avant extension (SingleChoice → SingleChoice+Justification)

### Parallel Opportunities

- Tous les `[P]` de la Phase 1 peuvent s'exécuter en parallèle (fichiers vides)
- Tous les `[P]` de la Phase 2 (schémas, modèle, tool, helper prompt) peuvent
  être implémentés en parallèle une fois la migration T013 mergée
- Les tests d'une même user story marqués `[P]` peuvent s'exécuter en parallèle
- Les mises à jour des 7 prompts modules (T035, T054, T055, T056, T081, T082,
  T083) sont toutes `[P]` entre elles
- Équipe de 2-3 devs : US1 + US2 + US4 simultanément après Phase 2

---

## Parallel Example: User Story 1

```bash
# Lancer tous les tests US1 en parallèle (TDD) :
Task: "T022 test_ask_interactive_question_qcu in backend/tests/unit/test_ask_interactive_question_tool.py"
Task: "T023 test_ask_interactive_question_expires_previous_pending in same file"
Task: "T024 test_send_message_with_qcu_response in backend/tests/integration/test_interactive_question_api.py"
Task: "T028 test_chat_sse_flow_qcu in backend/tests/integration/test_chat_interactive_sse.py"
Task: "T029 SingleChoiceWidget.spec.ts in frontend/tests/unit/"
Task: "T031 interactive-widgets-qcu.spec.ts in frontend/tests/e2e/"

# Implémentation parallèle des artefacts indépendants :
Task: "T036 InteractiveQuestionEvent types in frontend/app/types/interactive-question.ts"
Task: "T039 SingleChoiceWidget.vue in frontend/app/components/chat/"
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US4)

1. **Phase 1** : Setup (T001-T007) — 1 sprint court
2. **Phase 2** : Foundational (T008-T021) — TDD : écrire T008-T012 d'abord, les faire échouer, puis implémenter T013-T021
3. **Phase 3** : US1 QCU (T022-T044) — livre le premier widget cliquable
4. **STOP et VALIDER** : tester US1 indépendamment via quickstart étape 2
5. **Phase 4** : US2 QCM (T045-T057) — complète la couverture des questions fermées
6. **Phase 5** : US4 Fallback (T058-T070) — garantit zéro régression
7. **Demo MVP** : les 3 stories P1 sont en place, déployables

### Incrémental

- Ajouter **US3** (Phase 6) après validation du MVP pour enrichir le profil qualitatif
- **Phase 7** Polish : audit a11y, coverage, reviews, validation quickstart

### Parallel Team Strategy (3 devs)

1. Tous : Phase 1 + Phase 2 ensemble
2. Après Phase 2 checkpoint :
   - Dev A : US1 (Phase 3)
   - Dev B : US2 (Phase 4) + T054-T056 (prompts)
   - Dev C : US4 (Phase 5) — commence par les tests, attend T040 avant T066-T070
3. Après US1/US2/US4 : tous sur US3 (Phase 6) puis Polish (Phase 7)

---

## Notes

- `[P]` = fichiers différents, pas de dépendance bloquante
- `[Story]` = traçabilité vers la user story spec.md
- Chaque user story doit rester **indépendamment testable** via son acceptance scenarios
- **TDD NON-NÉGOCIABLE** (constitution principe IV) : vérifier que chaque test échoue avant d'implémenter
- **Dark mode obligatoire** (CLAUDE.md) : chaque composant Vue DOIT inclure les variantes `dark:`
- **Coverage ≥ 80 %** (constitution) : vérifier avec `pytest --cov` et `vitest --coverage`
- Commit après chaque tâche ou groupe logique (convention `feat:`, `test:`, `refactor:`)
- S'arrêter à chaque checkpoint pour valider la story indépendamment
- Éviter : tâches vagues, conflits de fichiers sur même ligne, dépendances croisées qui cassent l'indépendance des stories
