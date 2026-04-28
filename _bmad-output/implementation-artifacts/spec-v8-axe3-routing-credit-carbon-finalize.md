---
title: 'V8-AXE3 — Routing déterministe credit_score + finalize_carbon_assessment'
type: 'bugfix'
created: '2026-04-28'
status: 'done'
baseline_commit: '5cc1da3c12e05bc7dffb808812faa41236a59ad2'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-7-2026-04-28.md'
  - '{project-root}/CLAUDE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Sous MiniMax comme sous Claude Sonnet 4.6, `credit_node` et `carbon_node` ignorent deux tools obligatoires : `generate_credit_score` (le LLM répond « outil non disponible » ou redirige vers `/credit-score`) et `finalize_carbon_assessment` (le LLM affiche un plan de réduction puis n'appelle jamais le tool, l'assessment reste `status='in_progress'`). Régressions BUG-V7-006, BUG-V7-008, BUG-V7.1-005, BUG-V7.1-010 — switch LLM réfuté, c'est architectural.

**Approach:** Détecter l'intention utilisateur (regex FR sur dernier `HumanMessage`) + pré-conditions état, puis injecter un `AIMessage(content="", tool_calls=[...])` synthétique AVANT l'appel LLM. Le ToolNode existant exécute le tool ; le LLM est ensuite invoqué normalement pour formuler la réponse finale post-`ToolMessage`. Aucune modification topology `graph.py`.

## Boundaries & Constraints

**Always:**
- Heuristiques uniquement dans `nodes.py` (carbon_node, credit_node) ; pas dans `api/chat.py` ni `graph.py`.
- Détection sur `state.messages[-1]` UNIQUEMENT si `HumanMessage`.
- Pré-conditions strictes : carbone exige `assessment_id != "pending"` ET `len(completed_categories) >= len(applicable_categories)` ; crédit exige `state.user_id` non nul.
- Pas de re-forçage si un `ToolMessage` du même tool existe déjà dans le tour courant.
- Logging `logger.info("Forced tool invocation: <name> in <node>")` à chaque déclenchement.

**Ask First:** Si en production le ratio forçage > 30% des messages credit/carbon (logs), revoir la regex avec accord humain — ne pas désactiver l'heuristique seul.

**Never:** Modifier les tools eux-mêmes ; court-circuiter le LLM pour la réponse finale post-tool ; créer un nœud dédié au forçage ; réintroduire `_route_credit`/`_route_carbon` ; forcer si tool déjà appelé dans le tour.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output |
|----------|--------------|-----------------|
| Forçage credit | `messages[-1]="évalue ma solvabilité"`, `user_id` présent, pas de `ToolMessage` `generate_credit_score` dans le tour | Nœud retourne `AIMessage(content="", tool_calls=[{"name":"generate_credit_score","args":{},"id":<uuid>}])` SANS appel LLM |
| Forçage carbon finalize | `messages[-1]="Oui, finalise ce bilan"`, `assessment_id=<uuid>`, `completed==applicable` | Nœud retourne `AIMessage(content="", tool_calls=[{"name":"finalize_carbon_assessment","args":{"assessment_id":<uuid>},"id":<uuid>}])` SANS appel LLM |
| Pas de match / pré-condition KO | Question informationnelle ; ou catégories incomplètes ; ou `user_id` absent ; ou tool déjà appelé dans le tour | Comportement actuel préservé : appel LLM normal avec tools liés |

</frozen-after-approval>

## Code Map

- `backend/app/graph/nodes.py` — `carbon_node` (l. 751), `credit_node` (l. 1109) à modifier ; ajouter helpers `_should_force_credit_score(state) -> bool` et `_should_force_finalize_carbon(state) -> tuple[bool, str | None]` au module-level avec regex compilées.
- `backend/app/graph/tools/carbon_tools.py` — `finalize_carbon_assessment(assessment_id, config)` (l. 197) inchangé.
- `backend/app/graph/tools/credit_tools.py` — `generate_credit_score(config)` (l. 43) inchangé, aucun argument métier.
- `backend/app/graph/state.py` — lecture seule de `messages`, `carbon_data`, `user_id`.
- `backend/tests/test_carbon_node.py` + `backend/tests/test_credit/test_node.py` — étendre.
- `backend/tests/test_graph/test_force_tool_invocation.py` — NOUVEAU.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/graph/nodes.py` -- Ajouter les deux helpers (regex compilées module-level, vérif pré-conditions, vérif absence de `ToolMessage` du même nom dans le tour, logging) -- Centraliser la logique de détection.
- [x] `backend/app/graph/nodes.py` -- Dans `credit_node`, avant `llm.ainvoke(...)`, si `_should_force_credit_score(state)` : retourner directement `AIMessage(content="", tool_calls=[{"name":"generate_credit_score","args":{},"id":str(uuid.uuid4())}])` + `active_module="credit"` -- Forçage credit.
- [x] `backend/app/graph/nodes.py` -- Dans `carbon_node`, avant l'appel LLM, si `_should_force_finalize_carbon(state)` : retourner `AIMessage(content="", tool_calls=[{"name":"finalize_carbon_assessment","args":{"assessment_id":<uuid>},"id":str(uuid.uuid4())}])` -- Forçage carbon finalize.
- [x] `backend/tests/test_graph/test_force_tool_invocation.py` -- NOUVEAU. Tests unitaires des deux helpers couvrant les 3 scénarios I/O Matrix (forçage OK, pas de match, pré-conditions KO) ; mocker `state` uniquement, aucun LLM.
- [x] `backend/tests/test_carbon_node.py` -- Étendre : test runtime mockant le LLM, vérifier que `llm.ainvoke` n'est PAS appelé en cas de forçage et que la réponse contient `tool_calls[0].name == "finalize_carbon_assessment"`.
- [x] `backend/tests/test_credit/test_node.py` -- Idem pour `generate_credit_score`.

**Acceptance Criteria:**
- Given un user envoie "évalue ma solvabilité" et `user_id` présent, when `credit_node` s'exécute, then un `AIMessage` avec `tool_calls=[{"name":"generate_credit_score",...}]` est produit SANS appel LLM préalable.
- Given un user envoie "Oui, finalise ce bilan" et toutes les catégories applicables sont complétées, when `carbon_node` s'exécute, then un `AIMessage` avec `tool_calls=[{"name":"finalize_carbon_assessment","args":{"assessment_id":<uuid>}}]` est produit SANS appel LLM, et l'assessment passe en `status='completed'` après exécution du ToolNode.
- Given une question informationnelle, when le nœud s'exécute, then aucun forçage et le LLM est invoqué normalement.
- Given un `ToolMessage` du même tool existe déjà dans le tour, when le nœud est rappelé, then aucun re-forçage et le LLM formule la réponse finale.
- Given `completed_categories` incomplet OU `user_id` absent, when le nœud s'exécute, then aucun forçage.
- `pytest backend/tests/test_carbon_node.py backend/tests/test_credit/test_node.py backend/tests/test_graph/test_force_tool_invocation.py` passe à 100% ; les 935 tests existants restent verts.

## Spec Change Log

- 2026-04-28 (review V8-AXE3, iteration 1, classe `patch`) — 3 patches mineurs appliqués sans loopback :
  1. **F1 (HIGH)** : `tool_call_count: (state.get("tool_call_count") or 0) + 1` ajouté aux 2 retours forcés (cohérence avec `_should_continue_tool_loop` dans graph.py qui s'appuie sur ce compteur). Évite l'escalade silencieuse vers `MAX_TOOL_CALLS_PER_TURN=5` et le drift d'observabilité.
  2. **F3 (MEDIUM)** : `try: uuid.UUID(str(assessment_id)) except (ValueError, TypeError, AttributeError): return False, None` dans `_should_force_finalize_carbon` avant validation des catégories. Évite `ValueError` non-transient côté tool si `assessment_id` est corrompu (ex: checkpoint Memory restauré avec ID invalide).
  3. **F5 (HIGH)** : retrait de `note` du jeu de mots-clés de la regex `_FORCE_CREDIT_RE`. `note` seul est trop générique en français (« donne-moi une note de 1 à 10 ») → false positives sur le forçage `generate_credit_score`. Test négatif ajouté.
- KEEP : la stratégie « AIMessage synthétique avec `tool_calls=[...]` injecté avant `llm.ainvoke` » est validée par les 3 reviewers. La triple-garde (regex match + pré-conditions état + dedup `_tool_already_called_in_turn`) est la bonne défense en profondeur — ne pas la simplifier même si la 3e garde est `de facto` redondante (audit confirme : volontairement défensive). `applicable.issubset(completed)` est conservé tel quel (rejet de la suggestion `len >= len` car sémantiquement supérieur — détecte les écarts entre completed et applicable).
- 6 findings classés `defer` (cf. deferred-work.md DEF-V8-AXE3-1 à 6). 0 finding `intent_gap`, 0 finding `bad_spec`, pas de loopback.

## Design Notes

**Pourquoi un AIMessage synthétique injecté plutôt qu'un nouveau nœud ?** Le ToolNode itère sur `tool_calls` du dernier `AIMessage` ; produire ce message côté nœud réutilise toute l'infrastructure existante (retry, `tool_call_logs`, persistance) sans toucher la topologie. Le LLM reste responsable de la réponse finale au tour suivant.

**Regex FR :**
- Credit : `r"(évalue|calcule|génère|donne|fais)\b.*\b(solvabilité|score|crédit)"` (case-insensitive).
- Carbon finalize : `r"(finalise|finaliser|terminer|valide|valider|confirme).{0,40}(bilan|carbone)"` (case-insensitive).

**Détection « tool déjà appelé dans le tour »** : remonter `messages` en sens inverse jusqu'au `HumanMessage` précédent ; si un `ToolMessage` avec `name=<tool>` est rencontré avant, ne pas forcer.

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_graph/test_force_tool_invocation.py -v` — expected: ≥6 cas verts.
- `cd backend && source venv/bin/activate && pytest tests/test_carbon_node.py tests/test_credit/test_node.py -v` — expected: existants verts + nouveaux tests forçage verts.
- `cd backend && source venv/bin/activate && pytest -x` — expected: 935+ tests verts, zéro régression.

**Manual checks:**
- Backend lancé avec `LLM_MODEL=minimax/minimax-m2.7`. Atteindre carbone toutes catégories complétées, taper « Oui finalise ce bilan » → BDD `carbon_assessments.status='completed'` + `total_emissions_tco2e` non nul. Logs : `Forced tool invocation: finalize_carbon_assessment in carbon_node`.
- User profil complet, taper « évalue ma solvabilité » → BDD enregistrement `credit_scores` créé. Logs : `Forced tool invocation: generate_credit_score in credit_node`.

## Suggested Review Order

**Mécanisme de forçage (entrée principale)**

- Helpers + regex compilées module-level, design intent du patch
  [`nodes.py:165`](../../backend/app/graph/nodes.py#L165)

- `_should_force_credit_score` — gate credit (regex + user_id + dedup tour)
  [`nodes.py:217`](../../backend/app/graph/nodes.py#L217)

- `_should_force_finalize_carbon` — gate carbon avec validation UUID + complétude catégories (F3)
  [`nodes.py:239`](../../backend/app/graph/nodes.py#L239)

- `_tool_already_called_in_turn` — défense en profondeur dedup (algo corrigé en step-03)
  [`nodes.py:198`](../../backend/app/graph/nodes.py#L198)

**Injection dans les nœuds**

- `carbon_node` : injection AIMessage(tool_calls) + tool_call_count incrémenté (F1)
  [`nodes.py:880`](../../backend/app/graph/nodes.py#L880)

- `credit_node` : injection AIMessage(tool_calls) + tool_call_count incrémenté (F1)
  [`nodes.py:1278`](../../backend/app/graph/nodes.py#L1278)

**Tests — entrées d'épreuve**

- Tests unitaires helpers + regex + scénarios I/O Matrix (3 + 8 cas)
  [`test_force_tool_invocation.py:1`](../../backend/tests/test_graph/test_force_tool_invocation.py#L1)

- Test runtime carbon_node : LLM non appelé en cas de forçage
  [`test_carbon_node.py:96`](../../backend/tests/test_carbon_node.py#L96)

- Test runtime credit_node : LLM non appelé + cas négatifs (informational/no user_id)
  [`test_credit/test_node.py:144`](../../backend/tests/test_credit/test_node.py#L144)
