# Tasks: Intégration Tool Calling LangGraph

**Input**: Design documents from `/specs/012-langgraph-tool-calling/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Inclus (TDD obligatoire par constitution — Principe IV)

**Organization**: Tasks groupées par user story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story concernée (US1-US10)
- Chemins de fichiers exacts inclus

---

## Phase 1: Setup

**Purpose**: Création de la structure de fichiers et des utilitaires partagés

- [x] T001 Créer le répertoire `backend/app/graph/tools/` avec `__init__.py`
- [x] T002 Créer le helper commun `backend/app/graph/tools/common.py` avec les fonctions `get_db_and_user(config)` pour extraire user_id et db depuis RunnableConfig, et `log_tool_call()` pour la journalisation
- [x] T003 [P] Créer le répertoire `backend/tests/test_tools/` avec `__init__.py` et `conftest.py` (fixtures mock db, mock user_id, mock RunnableConfig)

---

## Phase 2: Foundational (Bloquant)

**Purpose**: Infrastructure qui DOIT être complète avant toute user story

**CRITICAL**: Aucun travail de user story ne peut commencer avant la fin de cette phase

- [x] T004 Étendre le TypedDict `ConversationState` dans `backend/app/graph/state.py` — ajouter `user_id: str | None` et `tool_call_count: int` (compteur de boucles max 5)
- [x] T005 [P] Créer le modèle SQLAlchemy `ToolCallLog` dans `backend/app/models/tool_call_log.py` — champs : id, user_id, conversation_id, node_name, tool_name, tool_args (JSON), tool_result (JSON), duration_ms, status, error_message, retry_count, created_at. Ajouter les index (user_id, created_at DESC) et (tool_name, status)
- [x] T006 [P] Générer et appliquer la migration Alembic pour la table `tool_call_logs` via `alembic revision --autogenerate -m "add tool_call_logs table"` puis `alembic upgrade head`
- [x] T007 Écrire les tests du helper `common.py` dans `backend/tests/test_tools/test_common.py` — tester `get_db_and_user()` avec config valide/manquant, `log_tool_call()` avec succès/erreur/retry
- [x] T008 Refactorer `backend/app/graph/graph.py` pour ajouter le pattern ToolNode conditionnel : créer une fonction factory `create_tool_loop(node_fn, tools, node_name)` qui retourne le sous-graphe (noeud LLM → should_continue → ToolNode → noeud LLM, max 5 itérations)
- [x] T009 Écrire les tests de `create_tool_loop()` dans `backend/tests/test_graph/test_tool_loop.py` — tester : réponse sans tool call (passe directement), 1 tool call + réponse finale, 5 tool calls (plafond atteint), tool call en erreur + retry
- [x] T010 Refactorer le handler SSE dans `backend/app/api/chat.py` — remplacer `llm.astream()` par `compiled_graph.astream_events()`, mapper `on_chat_model_stream` → événement SSE `token`, `on_tool_start` → événement SSE `tool_call_start`, `on_tool_end` → événement SSE `tool_call_end`, gérer les erreurs tools via `tool_call_error`. Injecter `user_id` et `db` dans le `RunnableConfig` passé au graphe
- [x] T011 Écrire les tests du handler SSE refactoré dans `backend/tests/test_graph/test_sse_tool_events.py` — tester : flux sans tool call (tokens uniquement), flux avec 1 tool call (token → tool_call_start → tool_call_end → token → done), flux avec erreur tool (tool_call_error émis)
- [x] T012 Mettre à jour `frontend/app/composables/useChat.ts` — ajouter le parsing des événements SSE `tool_call_start`, `tool_call_end`, `tool_call_error`, exposer un ref `activeToolCall: { name: string, args: object } | null` pour le composant d'affichage
- [x] T012a Implémenter la journalisation complète des tool calls dans `backend/app/graph/tools/common.py` — chaque tool call est loggé dans `tool_call_logs` via `log_tool_call()` (appel après chaque exécution, success/error/retry). Dépend de T005-T006 (modèle + migration)
- [x] T012b Ajouter la gestion du retry automatique dans `backend/app/graph/tools/common.py` — wrapper `with_retry()` qui effectue 1 retry silencieux avant de retourner l'erreur (FR-021). Utilisé par tous les tools des phases suivantes

**Checkpoint**: Infrastructure tool calling prête — le graphe supporte ToolNode, le SSE transmet les événements tool, le frontend les parse, le retry et la journalisation sont opérationnels

---

## Phase 3: User Story 1 — Profilage automatique via conversation (Priority: P1) MVP

**Goal**: Quand l'utilisateur mentionne des infos entreprise dans le chat, elles sont sauvegardées en base automatiquement et visibles sur /profile

**Independent Test**: Envoyer "je suis dans l'agriculture à Bouaké avec 30 employés" dans le chat → les données apparaissent sur /profile

### Tests US1

- [x] T013 [P] [US1] Écrire les tests unitaires des tools profiling dans `backend/tests/test_tools/test_profiling_tools.py` — tester `update_company_profile` (mise à jour partielle, retour des champs mis à jour et complétion), `get_company_profile` (profil existant, profil inexistant). Utiliser mock db et mock RunnableConfig
- [x] T014 [P] [US1] Écrire le test d'intégration du noeud profiling dans `backend/tests/test_tools/test_profiling_tools.py` — tests d'export et descriptions françaises

### Implementation US1

- [x] T015 [P] [US1] Créer les tools profiling dans `backend/app/graph/tools/profiling_tools.py` — implémenter `update_company_profile` (16 paramètres optionnels, appelle `company_service.get_or_create_profile()` puis `company_service.update_profile()`, retourne les champs mis à jour + complétion) et `get_company_profile` (appelle `company_service.get_profile()`, retourne profil + complétion + champs manquants)
- [x] T016 [US1] Refactorer `chat_node` dans `backend/app/graph/nodes.py` — bind les profiling tools via `llm.bind_tools(PROFILING_TOOLS)` dans le chat_node
- [x] T017 [US1] Intégrer les profiling tools dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py` — chat_node utilise PROFILING_TOOLS dans sa boucle ToolNode

**Checkpoint**: US1 testable indépendamment — profil sauvegardé via chat

---

## Phase 4: User Story 2 — Évaluation ESG sauvegardée critère par critère (Priority: P1)

**Goal**: L'évaluation ESG est créée, chaque critère est sauvegardé au fur et à mesure dans le chat, et le score final est visible sur /esg

**Independent Test**: Démarrer une évaluation ESG via le chat, répondre à 3 critères → les scores partiels visibles sur /esg

### Tests US2

- [x] T018 [P] [US2] Écrire les tests unitaires des tools ESG dans `backend/tests/test_tools/test_esg_tools.py` — tester `create_esg_assessment` (création avec status=draft), `save_esg_criterion_score` (sauvegarde critère, retour count + score partiel), `finalize_esg_assessment` (calcul scores E/S/G/global, confirmation requise), `get_esg_assessment` (avec et sans assessment_id)

### Implementation US2

- [x] T019 [P] [US2] Créer les tools ESG dans `backend/app/graph/tools/esg_tools.py` — implémenter `create_esg_assessment`, `save_esg_criterion_score`, `finalize_esg_assessment`, `get_esg_assessment`. FR-019 confirmation dans la docstring de finalize
- [x] T020 [US2] Refactorer `esg_scoring_node` dans `backend/app/graph/nodes.py` — bind les 4 tools ESG via `llm.bind_tools(ESG_TOOLS)`, instructions tool calling dans le prompt
- [x] T021 [US2] Intégrer esg_scoring_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US2 testable indépendamment — évaluation ESG sauvegardée progressivement

---

## Phase 5: User Story 3 — Bilan carbone conversationnel sauvegardé (Priority: P1)

**Goal**: Les données de consommation fournies par l'utilisateur sont converties et sauvegardées en base, visibles sur /carbon

**Independent Test**: Dire "je consomme 200L de gasoil par mois" → l'entrée apparaît sur /carbon avec le calcul tCO2e

### Tests US3

- [x] T022 [P] [US3] Écrire les tests unitaires des tools carbone dans `backend/tests/test_tools/test_carbon_tools.py` — tester `create_carbon_assessment`, `save_emission_entry` (calcul tCO2e vérifié), `finalize_carbon_assessment` (confirmation requise), `get_carbon_summary`

### Implementation US3

- [x] T023 [P] [US3] Créer les tools carbone dans `backend/app/graph/tools/carbon_tools.py` — implémenter les 4 tools. FR-019 confirmation dans la docstring de finalize
- [x] T024 [US3] Refactorer `carbon_node` dans `backend/app/graph/nodes.py` — bind les 4 tools carbone via `llm.bind_tools(CARBON_TOOLS)`, instructions tool calling dans le prompt
- [x] T025 [US3] Intégrer carbon_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US3 testable indépendamment — bilan carbone sauvegardé via chat

---

## Phase 6: User Story 8 — Plan d'action généré et sauvegardé (Priority: P1)

**Goal**: Le plan d'action demandé par l'utilisateur est sauvegardé en base et visible sur /action-plan

**Independent Test**: Demander "génère un plan d'action sur 12 mois" → le plan apparaît sur /action-plan

### Tests US8

- [x] T026 [P] [US8] Écrire les tests unitaires des tools action plan dans `backend/tests/test_tools/test_action_plan_tools.py` — tester `generate_action_plan` (création plan + items), `update_action_item` (mise à jour statut), `get_action_plan` (plan actif)

### Implementation US8

- [x] T027 [P] [US8] Créer les tools action plan dans `backend/app/graph/tools/action_plan_tools.py` — implémenter `generate_action_plan` (appelle `action_plan_service.generate_action_plan()`), `update_action_item`, `get_action_plan`
- [x] T028 [US8] Refactorer `action_plan_node` dans `backend/app/graph/nodes.py` — bind les 3 tools, ajouter les instructions de sauvegarde obligatoire dans le prompt système
- [x] T029 [US8] Intégrer action_plan_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US8 testable indépendamment — plan d'action sauvegardé via chat

---

## Phase 7: User Story 9 — Chat avec lecture temps réel (Priority: P1)

**Goal**: Le chat_node consulte la base en temps réel pour répondre aux questions factuelles au lieu de répondre de mémoire

**Independent Test**: Modifier un score ESG via l'interface web, puis demander "quel est mon score ESG ?" dans le chat → la réponse reflète le score actuel

### Tests US9

- [x] T030 [P] [US9] Écrire les tests unitaires des tools chat dans `backend/tests/test_tools/test_chat_tools.py` — tester `get_user_dashboard_summary`, `get_company_profile`, `get_esg_assessment`, `get_carbon_summary` (retours formatés pour le LLM)

### Implementation US9

- [x] T031 [P] [US9] Créer les tools chat (lecture seule) dans `backend/app/graph/tools/chat_tools.py` — implémenter `get_user_dashboard_summary` (appelle `dashboard_service.get_dashboard_summary()`), `get_company_profile`, `get_esg_assessment`, `get_carbon_summary`
- [x] T032 [US9] Refactorer `chat_node` dans `backend/app/graph/nodes.py` — bind les 4 tools de lecture, ajouter les instructions de consultation base temps réel dans le prompt système
- [x] T033 [US9] Intégrer chat_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US9 testable indépendamment — chat répond avec données temps réel

---

## Phase 8: User Story 4 — Recherche et suivi de financements (Priority: P2)

**Goal**: Les fonds compatibles sont recherchés en base et les intérêts de l'utilisateur sont sauvegardés

**Independent Test**: Demander "quels financements pour moi ?" → les fonds apparaissent sur /financing avec scores

### Tests US4

- [x] T034 [P] [US4] Écrire les tests unitaires des tools financement dans `backend/tests/test_tools/test_financing_tools.py` — tester `search_compatible_funds`, `save_fund_interest`, `get_fund_details`, `create_fund_application`

### Implementation US4

- [x] T035 [P] [US4] Créer les tools financement dans `backend/app/graph/tools/financing_tools.py` — implémenter les 4 tools. `search_compatible_funds` collecte profil/ESG/carbone depuis la base pour le matching. `create_fund_application` appelle `application_service.create_application()`
- [x] T036 [US4] Refactorer `financing_node` dans `backend/app/graph/nodes.py` — bind les 4 tools, ajouter instructions de recherche base au lieu de mémoire
- [x] T037 [US4] Intégrer financing_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US4 testable indépendamment — matching financement fonctionnel via chat

---

## Phase 9: User Story 5 — Génération et suivi de dossiers de candidature (Priority: P2)

**Goal**: Chaque section de dossier générée/modifiée via le chat est sauvegardée en base

**Independent Test**: Demander "génère la section présentation de l'entreprise" → la section est visible sur /applications

### Tests US5

- [x] T038 [P] [US5] Écrire les tests unitaires des tools application dans `backend/tests/test_tools/test_application_tools.py` — tester `generate_application_section`, `update_application_section`, `get_application_checklist`, `simulate_financing`, `export_application`

### Implementation US5

- [x] T039 [P] [US5] Étendre `backend/app/modules/applications/service.py` — ajouter la méthode `simulate(db, application)` qui calcule montant éligible, ROI, timeline, impact carbone, frais intermédiaire et retourne un dict
- [x] T040 [P] [US5] Étendre `backend/app/modules/applications/service.py` — ajouter la méthode `export(db, application, format)` qui génère un PDF (WeasyPrint) ou DOCX (python-docx) et retourne l'URL de téléchargement
- [x] T041 [US5] Créer les tools application dans `backend/app/graph/tools/application_tools.py` — implémenter les 5 tools
- [x] T042 [US5] Refactorer `application_node` dans `backend/app/graph/nodes.py` — bind les 5 tools, ajouter instructions de sauvegarde systématique
- [x] T043 [US5] Intégrer application_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US5 testable indépendamment — dossiers de candidature gérés via chat

---

## Phase 10: User Story 6 — Scoring crédit vert (Priority: P2)

**Goal**: Le score de crédit vert est calculé et sauvegardé en base quand l'utilisateur le demande

**Independent Test**: Demander "calcule mon score de crédit vert" → le score apparaît sur /credit-score

### Tests US6

- [x] T044 [P] [US6] Écrire les tests unitaires des tools crédit dans `backend/tests/test_tools/test_credit_tools.py` — tester `generate_credit_score`, `get_credit_score`, `generate_credit_certificate`

### Implementation US6

- [x] T045 [P] [US6] Étendre `backend/app/modules/credit/service.py` — ajouter la méthode `generate_certificate(db, user_id)` qui génère un PDF d'attestation (WeasyPrint) et retourne l'URL de téléchargement
- [x] T046 [US6] Créer les tools crédit dans `backend/app/graph/tools/credit_tools.py` — implémenter les 3 tools
- [x] T047 [US6] Refactorer `credit_node` dans `backend/app/graph/nodes.py` — bind les 3 tools, ajouter instructions d'appel obligatoire au tool (pas d'estimation texte)
- [x] T048 [US6] Intégrer credit_node dans le graphe via `create_tool_loop()` dans `backend/app/graph/graph.py`

**Checkpoint**: US6 testable indépendamment — score crédit calculé et sauvegardé via chat

---

## Phase 11: User Story 7 — Analyse de documents via tools (Priority: P2)

**Goal**: L'analyse de documents passe par les tools au lieu d'être simulée

**Independent Test**: Uploader un document → l'analyse complète apparaît sur /documents

### Tests US7

- [x] T049 [P] [US7] Écrire les tests unitaires des tools document dans `backend/tests/test_tools/test_document_tools.py` — tester `analyze_uploaded_document`, `get_document_analysis`, `list_user_documents`

### Implementation US7

- [x] T050 [P] [US7] Créer les tools document dans `backend/app/graph/tools/document_tools.py` — implémenter les 3 tools
- [x] T051 [US7] Refactorer `document_node` dans `backend/app/graph/nodes.py` — bind les 3 tools (via chat_node qui suit), ajouter instructions d'analyse obligatoire via tool
- [x] T052 [US7] Intégrer document tools dans le graphe via chat_node (document_node → chat_node avec DOCUMENT_TOOLS)

**Checkpoint**: US7 testable indépendamment — analyse documentaire réelle via tools

---

## Phase 12: User Story 10 — Indicateurs visuels pendant les tools (Priority: P3)

**Goal**: Le frontend affiche un indicateur contextuel pendant l'exécution des tool calls

**Independent Test**: Déclencher un tool call → un indicateur "Sauvegarde du profil..." apparaît puis disparaît

### Implementation US10

- [x] T053 [US10] Créer le composant `frontend/app/components/chat/ToolCallIndicator.vue` — affiche le label français du tool en cours (mapping tool_name → label depuis le contrat SSE), animation de chargement, disparaît quand `tool_call_end` ou `tool_call_error` arrive. Compatible dark mode (variantes `dark:` de Tailwind obligatoires)
- [x] T054 [US10] Intégrer `ToolCallIndicator` dans la page chat `frontend/app/pages/chat.vue` — afficher le composant quand `activeToolCall` est non-null (ref exposée par `useChat.ts`)

**Checkpoint**: US10 testable indépendamment — indicateur visuel fonctionnel

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Améliorations transversales

- [x] T055 [P] Émettre les événements SSE `profile_update` et `profile_completion` depuis le tool `update_company_profile` au lieu du code actuel dans `generate_sse()` — migrer la logique de `extract_and_update_profile()` vers le tool
- [x] T058 Vérifier que les 9 noeuds avec tools fonctionnent de bout en bout via un test d'intégration global dans `backend/tests/test_graph/test_full_tool_flow.py` — simuler un parcours utilisateur complet : profil → ESG → carbone → financement → plan d'action
- [x] T059 [P] Mettre à jour `CLAUDE.md` à la racine — documenter le tool calling LangGraph dans la section Recent Changes
- [x] T060 Exécuter le quickstart.md validation — vérifier que `llm.bind_tools()` fonctionne avec OpenRouter, que `astream_events()` émet les bons événements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dépendances — peut commencer immédiatement
- **Foundational (Phase 2)**: Dépend du Setup — BLOQUE toutes les user stories
- **US1-US9 (Phases 3-11)**: Dépendent de la Phase 2 foundational
  - Peuvent s'exécuter en parallèle entre elles
  - Ou séquentiellement par priorité (P1 d'abord, puis P2)
- **US10 (Phase 12)**: Dépend de la Phase 2 (T012 en particulier — parsing SSE frontend)
- **Polish (Phase 13)**: Dépend de la complétion de toutes les user stories souhaitées

### User Story Dependencies

- **US1 (P1)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US2 (P1)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US3 (P1)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US8 (P1)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US9 (P1)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US4 (P2)**: Après Phase 2 — fonctionne mieux avec US1 (profil pour le matching) mais testable seul
- **US5 (P2)**: Après Phase 2 — nécessite T039-T040 (nouvelles méthodes service)
- **US6 (P2)**: Après Phase 2 — nécessite T045 (nouvelle méthode service)
- **US7 (P2)**: Après Phase 2 — aucune dépendance sur d'autres stories
- **US10 (P3)**: Après T012 (parsing SSE frontend)

### Within Each User Story

1. Tests écrits en PREMIER (doivent ÉCHOUER avant implémentation)
2. Tools créés (fichier dans `graph/tools/`)
3. Noeud refactoré (dans `nodes.py`)
4. Intégration dans le graphe (dans `graph.py`)

### Parallel Opportunities

- **Phase 1** : T001 et T003 en parallèle
- **Phase 2** : T005+T006 en parallèle avec T004, T007 après T002
- **Phases 3-11** : Toutes les user stories P1 peuvent s'exécuter en parallèle (5 agents)
- **Dans chaque US** : Tests [P] et tools [P] en parallèle, puis noeud → graphe séquentiels

---

## Parallel Example: Phase 3 (US1 — Profilage)

```bash
# Lancer les tests et tools en parallèle :
Task T013: "Tests unitaires profiling_tools dans backend/tests/test_tools/test_profiling_tools.py"
Task T014: "Test intégration profiling_node dans backend/tests/test_graph/test_nodes_tool_calling.py"
Task T015: "Créer profiling_tools dans backend/app/graph/tools/profiling_tools.py"

# Puis séquentiellement :
Task T016: "Refactorer profiling_node dans backend/app/graph/nodes.py"
Task T017: "Intégrer dans le graphe via backend/app/graph/graph.py"
```

---

## Implementation Strategy

### MVP First (US1 — Profilage uniquement)

1. Compléter Phase 1: Setup (T001-T003)
2. Compléter Phase 2: Foundational (T004-T012) — CRITIQUE
3. Compléter Phase 3: US1 Profilage (T013-T017)
4. **STOP et VALIDER** : Tester "je suis dans l'agriculture à Bouaké" → profil sauvegardé
5. Déployer/démontrer si prêt

### Incremental Delivery (P1 stories)

1. Setup + Foundational → Infrastructure prête
2. US1 (Profilage) → Profil via chat (MVP!)
3. US2 (ESG) → Scoring ESG via chat
4. US3 (Carbone) → Bilan carbone via chat
5. US8 (Plan d'action) → Plan d'action via chat
6. US9 (Chat lecture) → Données temps réel dans le chat
7. Chaque story ajoute de la valeur sans casser les précédentes

### Parallel Team Strategy

Avec plusieurs développeurs après Phase 2 :
- Dev A : US1 (Profilage) + US4 (Financement)
- Dev B : US2 (ESG) + US5 (Application)
- Dev C : US3 (Carbone) + US6 (Crédit)
- Dev D : US8 (Plan d'action) + US7 (Document)
- Dev E : US9 (Chat lecture) + US10 (Frontend)

---

## Notes

- [P] = fichiers différents, pas de dépendances mutuelles
- [Story] = mappe la tâche à la user story pour traçabilité
- Chaque user story est indépendamment complétable et testable
- Les tests DOIVENT échouer avant l'implémentation (TDD — constitution Principe IV)
- Committer après chaque tâche ou groupe logique
- Arrêt possible à chaque checkpoint pour valider indépendamment
