# Tasks: Correction des 3 anomalies bloquant les tests d'intégration

**Input**: Design documents from `/specs/015-fix-toolcall-esg-timeout/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Tests unitaires inclus pour valider les corrections de prompts et les nouveaux tools.

**Organization**: Tasks groupées par user story pour permettre l'implémentation et le test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration timeout et préparation

- [X] T001 Ajouter `request_timeout=60` dans `get_llm()` dans `backend/app/graph/nodes.py`

**Checkpoint**: Le LLM a un timeout explicite de 60 secondes par appel.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pas de prérequis bloquants supplémentaires — l'architecture `create_tool_loop` dans `graph.py` est déjà correcte.

**Checkpoint**: Phase 1 suffisante. Les user stories peuvent démarrer.

---

## Phase 3: User Story 1 - Génération de dossier candidature via le chat (Priority: P1)

**Goal**: Le LLM appelle les tools application pour persister les dossiers en base au lieu de répondre en texte.

**Independent Test**: Envoyer "Crée-moi un dossier SUNREF via la SIB" dans le chat → le dossier apparait sur /applications.

### Tests pour User Story 1

- [X] T002 [P] [US1] Écrire test unitaire vérifiant que le prompt application contient les noms des tools et la REGLE ABSOLUE dans `backend/tests/test_prompts/test_application_prompt.py`
- [X] T003 [P] [US1] Écrire test unitaire vérifiant que `create_fund_application` existe dans `APPLICATION_TOOLS` dans `backend/tests/test_prompts/test_application_tools.py`

### Implementation pour User Story 1

- [X] T004 [P] [US1] Créer le tool `create_fund_application` dans `backend/app/graph/tools/application_tools.py` — arguments: `fund_id: str`, `config: RunnableConfig`, optionnel `target_type: str`. Crée un dossier en base via le service applications et retourne l'ID + infos de base. Ajouter à la liste `APPLICATION_TOOLS`.
- [X] T005 [P] [US1] Réécrire le prompt `APPLICATION_PROMPT` dans `backend/app/prompts/application.py` — changer le ROLE de passif ("Tu informes") à actif ("Tu crées et gères les dossiers"). Ajouter une section OUTILS DISPONIBLES listant les 6 tools avec leurs cas d'usage. Ajouter une REGLE ABSOLUE : "Ne génère JAMAIS le contenu d'un dossier uniquement en texte dans le chat. Appelle TOUJOURS le tool correspondant pour sauvegarder." Conserver les instructions visuelles existantes (mermaid, progress, table, timeline, gauge). Ajouter les instructions d'adaptation du ton par destinataire (direct, banque, agence, développeur carbone).
- [X] T006 [US1] Lancer les tests existants + nouveaux tests pour vérifier la non-régression : `cd backend && pytest tests/ -v`

**Checkpoint**: Le prompt application est directif, le tool `create_fund_application` existe, les tests passent.

---

## Phase 4: User Story 2 - Calcul du score de crédit vert via le chat (Priority: P1)

**Goal**: Le LLM appelle les tools crédit pour persister les scores en base au lieu de donner des estimations textuelles.

**Independent Test**: Envoyer "Calcule mon score de crédit vert" → le score apparait sur /credit-score.

### Tests pour User Story 2

- [X] T007 [P] [US2] Écrire test unitaire vérifiant que le prompt crédit contient les noms des 3 tools et la REGLE ABSOLUE dans `backend/tests/test_prompts/test_credit_prompt.py`

### Implementation pour User Story 2

- [X] T008 [US2] Réécrire le prompt `CREDIT_PROMPT` dans `backend/app/prompts/credit.py` — renforcer le ROLE avec mention explicite des 3 tools (`generate_credit_score`, `get_credit_score`, `generate_credit_certificate`). Ajouter une section OUTILS DISPONIBLES avec cas d'usage de chaque tool. Ajouter une REGLE ABSOLUE : "Ne donne JAMAIS une estimation de score en texte sans appeler `generate_credit_score`. Un score estimé dans le chat est INTERDIT — seul le score calculé par le tool est valide." Ajouter les sources de données utilisées pour le calcul (profil, ESG, carbone, documents, candidatures, intermédiaires). Conserver les instructions visuelles existantes (gauge, chart radar, progress, mermaid).
- [X] T009 [US2] Lancer les tests existants + nouveaux tests : `cd backend && pytest tests/ -v`

**Checkpoint**: Le prompt crédit est directif, les tests passent.

---

## Phase 5: User Story 3 - Évaluation ESG complète sans timeout (Priority: P2)

**Goal**: Sauvegarde par lot des critères ESG pour éviter le timeout SSE lors d'évaluations de 30 critères.

**Independent Test**: Évaluer 30 critères ESG et finaliser → se termine en moins de 15 secondes.

### Tests pour User Story 3

- [X] T010 [P] [US3] Écrire test unitaire vérifiant que `batch_save_esg_criteria` existe dans `ESG_TOOLS` et accepte une liste de critères dans `backend/tests/test_prompts/test_esg_tools.py`
- [X] T011 [P] [US3] Écrire test unitaire vérifiant que le prompt ESG contient l'instruction d'utiliser le batch dans `backend/tests/test_prompts/test_esg_prompt.py`

### Implementation pour User Story 3

- [X] T012 [US3] Créer le tool `batch_save_esg_criteria` dans `backend/app/graph/tools/esg_tools.py` — arguments: `assessment_id: str`, `criteria: list[dict]` (chaque dict: criterion_code, score, justification), `config: RunnableConfig`. Implémente la même logique que `save_esg_criterion_score` mais pour N critères en UNE SEULE transaction (update unique de `assessment_data` et `evaluated_criteria`). Retourne le nombre de critères sauvegardés + scores partiels. Ajouter à la liste `ESG_TOOLS`.
- [X] T013 [US3] Mettre à jour le prompt `ESG_SCORING_PROMPT` dans `backend/app/prompts/esg_scoring.py` — ajouter une instruction : "Quand tu as plusieurs critères à sauvegarder (évaluation par pilier ou finalisation), utilise `batch_save_esg_criteria` au lieu de faire plusieurs appels `save_esg_criterion_score`. Par exemple, après avoir évalué les 10 critères Environnement, sauvegarde-les tous en un seul appel batch."
- [X] T014 [US3] Lancer les tests existants + nouveaux tests : `cd backend && pytest tests/ -v`

**Checkpoint**: Le tool batch existe, le prompt ESG instruit son utilisation, les tests passent.

---

## Phase 6: User Story 4 - Non-régression (Priority: P1)

**Goal**: Vérifier que les 29 tests existants continuent à passer après toutes les corrections.

**Independent Test**: Suite complète des 36 tests — objectif 32+ PASS.

- [X] T015 [US4] Exécuter la suite complète des tests backend : `cd backend && pytest tests/ -v --tb=short` et vérifier zéro régression sur les tests existants
- [X] T016 [US4] Vérifier que les tests de prompts du module action_plan (déjà corrigé) passent toujours : `cd backend && pytest tests/test_prompts/test_style_instruction.py -v`

**Checkpoint**: Tous les tests existants + nouveaux passent. Zéro régression.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T017 Mettre à jour le CLAUDE.md avec les Recent Changes pour la feature 015
- [X] T018 Vérifier que les prompts des 3 modules modifiés suivent le même pattern (cohérence entre application, crédit, ESG)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Pas de dépendance — start immédiat
- **Phase 2 (Foundational)**: Rien à faire — l'architecture est déjà correcte
- **Phase 3 (US1 Application)**: Dépend de Phase 1 (timeout)
- **Phase 4 (US2 Crédit)**: Dépend de Phase 1 (timeout), INDÉPENDANT de Phase 3
- **Phase 5 (US3 ESG Batch)**: Dépend de Phase 1 (timeout), INDÉPENDANT de Phases 3-4
- **Phase 6 (US4 Non-régression)**: Dépend de Phases 3, 4, 5 (toutes corrections appliquées)
- **Phase 7 (Polish)**: Dépend de Phase 6 (validation complète)

### User Story Dependencies

- **US1 (Application)**: Indépendant des autres stories
- **US2 (Crédit)**: Indépendant des autres stories
- **US3 (ESG Batch)**: Indépendant des autres stories
- **US4 (Non-régression)**: Dépend de US1 + US2 + US3

### Within Each User Story

- Tests écrits AVANT l'implémentation (RED)
- Implémentation (GREEN)
- Vérification non-régression après chaque story

### Parallel Opportunities

- **US1, US2 et US3 sont ENTIÈREMENT parallélisables** — fichiers différents, aucune dépendance croisée
- T002 et T003 en parallèle (tests US1)
- T004 et T005 en parallèle (tool + prompt, fichiers différents)
- T007 en parallèle avec T002/T003 (test US2, fichier différent)
- T010 et T011 en parallèle (tests US3)

---

## Parallel Example: All User Stories

```bash
# Phase 1 (séquentiel, 1 seule tâche):
T001: Ajouter timeout dans get_llm()

# Phases 3+4+5 en parallèle (3 agents):
Agent 1 (US1): T002 → T003 → T004 + T005 → T006
Agent 2 (US2): T007 → T008 → T009
Agent 3 (US3): T010 → T011 → T012 → T013 → T014

# Phase 6 (séquentiel, après toutes les stories):
T015 → T016

# Phase 7 (séquentiel):
T017 → T018
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (timeout)
2. Complete Phase 3: US1 (application tool calling)
3. **STOP and VALIDATE**: Tester le module candidature indépendamment
4. Si OK → continuer avec US2 et US3

### Exécution Optimale (Parallèle)

1. Phase 1: T001 (1 tâche)
2. Phases 3+4+5 en parallèle (3 stories indépendantes, 3 agents)
3. Phase 6: Validation globale non-régression
4. Phase 7: Polish

### Estimation

- **18 tâches totales**
- **3 stories parallélisables**
- **Chemin critique**: T001 → (US1 ou US2 ou US3) → T015 → T017

---

## Notes

- [P] tasks = fichiers différents, pas de dépendances
- Les 3 corrections sont chirurgicales : prompts + tools, PAS de modification de l'architecture du graphe
- Le `create_fund_application` est le seul nouveau tool requis pour le module application
- Le `batch_save_esg_criteria` est le seul nouveau tool requis pour le module ESG
- `graph.py` et la structure des noeuds dans `nodes.py` ne sont PAS modifiés (sauf `get_llm()`)
