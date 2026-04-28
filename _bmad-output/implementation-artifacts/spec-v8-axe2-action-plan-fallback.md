---
title: 'V8-AXE2 — generate_action_plan validation relâchée + fallback template'
type: 'bugfix'
created: '2026-04-28'
status: 'done'
baseline_commit: 'bdd8c84c5d42fbb0647cddf108bdd2a49e2f9029'
context:
  - '{project-root}/docs/CODEMAPS/methodology.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-7-2026-04-28.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe3-routing-credit-carbon-finalize.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le tool `generate_action_plan` échoue systématiquement sur 3 vagues (V6-005 LLM textuel sans appel, V7-007 MiniMax `json_parse_failed` ×2, V7.1-009 Claude `LLMGuardError` 9× = 3 cycles × 3 retries). Le seuil runtime ≥10 actions imposé par §4nonies bloque même les meilleurs providers et il n'existe aucun fallback déterministe — l'utilisateur reste sans plan.

**Approach:** Mettre en place une **validation runtime adaptative + fallback déterministe** au niveau du tool : (1) accepter un plan partiel ≥5 actions (mode batch incrémental, message « X/10 sauvegardées, complète avec batch suivant »), (2) si le service lève `LLMGuardError` malgré ses retries internes, déclencher un fallback template qui charge `action_plan_default.json`, substitue les placeholders avec le profil entreprise, persiste 10 actions et logue `fallback déclenché user_id=…`. Pas de modification du graph LangGraph ni du modèle SQLAlchemy.

## Boundaries & Constraints

**Always:**
- Garder l'appel LLM en 1ère intention (qualité optimale quand il fonctionne).
- Mode batch incrémental ≥5 actions accepté et persisté tel quel — message tool indique la cible 10 et invite le LLM à compléter.
- Fallback template persiste un `ActionPlan` complet (10 items, `status=active`, archivage de l'ancien plan actif comme la voie LLM).
- Tous les retours du tool restent des `str` exploitables par le LLM (pattern §4nonies — jamais d'exception remontée).
- Logger `fallback_triggered` avec `user_id`, `reason` (`llm_guard_error` | `count_below_min`), `final_count`.

**Ask First:**
- Si le profil entreprise est absent (HTTP 428 du service) : laisser le service lever et le tool retourne le message d'erreur métier — **ne pas** déclencher fallback.
- Si la BDD échoue lors du fallback : remonter erreur explicite, ne pas tenter de re-fallback.

**Never:**
- Ne jamais modifier le graph LangGraph (`backend/app/graph/nodes.py`) ni les noeuds.
- Ne jamais modifier le modèle `ActionPlan` SQLAlchemy ni la migration.
- Ne jamais abaisser `MIN_ACTION_COUNT` dans `app/core/llm_guards.py` (déjà à 5).
- Ne jamais empiler des retries supplémentaires côté tool — le service fait déjà ses 3 tentatives via `run_guarded_llm_call`.
- Ne jamais retourner moins de 10 actions persistées en sortie de fallback.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| LLM-OK-10+ | LLM produit 10–20 actions valides | Plan persisté tel quel, message succès complet | N/A |
| LLM-PARTIAL-5-9 | LLM produit 5–9 actions valides | Plan persisté, message « X/10 actions, complète avec batch suivant » | N/A |
| LLM-FAIL-LLMGuardError | `run_guarded_llm_call` lève après ses retries | Fallback template déclenché, 10 actions persistées, log `fallback_triggered` | retour str succès fallback |
| JSON-MALFORMED | LLM produit JSON avec trailing comma / single quotes | `json_repair` répare avant rejet | si repair échoue → continue en pipeline retry du service |
| PROFILE-MISSING | Pas de `CompanyProfile` user | HTTP 428 du service → message tool explicite | pas de fallback |
| FALLBACK-DB-FAIL | DB échoue pendant insert fallback | Message erreur tool explicite | log erreur, pas de re-fallback |

</frozen-after-approval>

## Code Map

- `backend/app/graph/tools/action_plan_tools.py` -- tool `generate_action_plan` à patcher : try/except LLMGuardError, branche fallback, abaisser seuil acceptation à ≥5 (mode incrémental).
- `backend/app/modules/action_plan/service.py` -- service existant `generate_action_plan` (laissé inchangé pour LLM-OK), à exposer `_extract_json_array` qui consommera `json_repair` (modif minimale).
- `backend/app/core/llm_guards.py` -- contient `LLMGuardError`, `MIN_ACTION_COUNT=5`, `validate_action_plan_schema` (référence, **non modifié**).
- `backend/app/templates/action_plan_default.json` -- **nouveau** : 10 actions ESG/Carbone/Financement génériques avec placeholders `{{sector}}`, `{{employee_count}}`, `{{country}}`.
- `backend/app/services/__init__.py` -- **nouveau** (répertoire à créer).
- `backend/app/services/action_plan_fallback.py` -- **nouveau** : `generate_fallback_actions(profile)` charge JSON, substitue placeholders, retourne `list[dict]` (10 items) + `persist_fallback_plan(db, user_id, timeframe, profile)` qui crée `ActionPlan` + `ActionItem`s.
- `backend/app/services/json_repair.py` -- **nouveau** : `repair_json(text) -> dict | list | None` (trailing comma, single→double quotes, unquoted keys, fallback `None`).
- `docs/CODEMAPS/methodology.md` -- ajouter `### 4decies. Validation runtime adaptative + fallback (Leçon 40)` à la suite de §4nonies.
- `backend/tests/test_graph/test_action_plan_tool_fallback.py` -- **nouveau** fichier de tests (≥6 tests).

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/services/__init__.py` -- créer module vide -- **enabler** des nouveaux services.
- [x] `backend/app/services/json_repair.py` -- implémenter `repair_json` (regex trailing comma, quotes, unquoted keys ; `try json.loads` après chaque passe ; retour `None` si rien ne marche).
- [x] `backend/app/templates/action_plan_default.json` -- créer template 10 actions (3 environment, 2 social, 2 governance, 2 financing, 1 carbon) avec champs `title`, `description`, `category`, `priority`, `due_date_offset_months`, `estimated_cost_xof`, `estimated_benefit` + placeholders `{{sector}}`, `{{employee_count}}`, `{{country}}`.
- [x] `backend/app/services/action_plan_fallback.py` -- `generate_fallback_actions(profile_dict, timeframe) -> list[dict]` (charge JSON, substitue placeholders, calcule `due_date` à partir de l'offset) + `persist_fallback_plan(db, user_id, timeframe) -> ActionPlan` (charge profil, archive plan actif, insère plan + 10 items, retourne plan).
- [x] `backend/app/graph/tools/action_plan_tools.py` -- patcher tool : abaisser `_ACTION_PLAN_MIN_ITEMS` à 5, ajouter try/except `LLMGuardError`, sur exception → appeler `persist_fallback_plan` + log `fallback_triggered` ; sur succès <10 actions → message « X/10 sauvegardées, manque Y, continue avec batch suivant ».
- [x] `backend/app/modules/action_plan/service.py` -- dans `_extract_json_array`, en cas de `json.JSONDecodeError` initial, tenter `repair_json` avant de re-lever (compatibilité §4nonies préservée).
- [x] `backend/tests/test_tools/test_action_plan_tool_fallback.py` -- 9 tests (3 json_repair + 2 template + 1 persistance BDD + 3 tool integration) ; **placement final** : `test_tools/` au lieu de `test_graph/` pour réutiliser la fixture `mock_config`.
- [x] `backend/tests/test_tools/test_action_plan_tools.py` -- adapter `test_rejects_below_minimum_items` → `test_accepts_partial_batch_with_incremental_message` (nouveau contrat §4decies).
- [x] `backend/tests/test_graph/test_tools_instrumentation.py` -- `test_action_plan_prod_retries_on_transient` : passer `mock_plan.items` à 10 (au lieu de `[]`) pour ne pas déclencher fallback dans test centré retry.
- [x] `docs/CODEMAPS/methodology.md` -- ajouter `### 4decies. Leçon 40` (validation adaptative + fallback) ; mettre à jour cumul « 36 leçons » → « 37 leçons ».

**Acceptance Criteria:**
- Given un appel `generate_action_plan(timeframe=12)` quand le LLM retourne 10+ actions valides, then le plan est persisté inchangé et le tool renvoie le message succès historique.
- Given un appel quand le LLM retourne 7 actions valides, then le plan est persisté avec 7 items et le message tool indique « 7/10 actions sauvegardées, manque 3, continue avec batch suivant ».
- Given un appel quand `run_guarded_llm_call` lève `LLMGuardError` malgré ses 3 tentatives, then le fallback template est déclenché, 10 actions sont persistées en BDD, un log structuré `fallback_triggered` est émis, et le tool renvoie un message succès indiquant l'usage du fallback.
- Given un JSON LLM avec trailing comma, when `_extract_json_array` est invoqué, then `json_repair` répare le payload et le service continue sans déclencher de retry.
- Given un profil sans `company_name`, when le tool est appelé, then le service lève HTTP 428 et le tool retourne le message « Profil entreprise requis… » sans déclencher fallback.
- Tous les tests existants `pytest backend/tests/test_graph/test_action_plan*` restent verts (zéro régression).

## Spec Change Log

### 2026-04-28 — Itération 1 review (3 reviewers parallèles)

Aucun finding `intent_gap` ni `bad_spec` — implémentation conforme à la spec frozen, patches uniquement.

- **8 patches appliqués** :
  - #1 CRITICAL : `persist_fallback_plan` archive + insert dans un seul commit final (atomicité).
  - #2 HIGH : passe `_convert_single_to_double_quotes` rendue safe (no-op si double quote présent — protège l'apostrophe française).
  - #4 HIGH : ajout test `test_action_plan_count_below_min_triggers_fallback` (path step-3 sans LLMGuardError).
  - #5 HIGH : `_load_template()` lève `FallbackTemplateError` au lieu de propager `FileNotFoundError` / `JSONDecodeError` ; tool convertit en str via wrapper `_trigger_fallback`.
  - #6 MED : `persist_fallback_plan` accepte un paramètre `reason` ; tool passe `count_below_min` ou `llm_guard_error` selon la branche.
  - #9 MED : `_safe_priority` / `_safe_category` loguent un warning `Template drift` sur fallback.
  - #10 LOW : `persist_fallback_plan` recharge le plan avec `selectinload(items)` après commit (évite lazy-load detached en async).
  - #12 LOW : paths pytest dans Verification corrigés (`test_tools/` au lieu de `test_graph/`).
- **1 defer** : race concurrente partial unique index → `deferred-work.md:DEF-V8-AXE2-1`.
- **3 reject** : regex unquoted keys dans values (parse échoue → None, sain), cascading placeholder (exploitabilité nulle), patch path test (faux positif).

**KEEP** : ne pas ré-introduire la passe `_convert_single_to_double_quotes` aveugle (corrompt le français) ; ne pas re-séparer les commits dans `persist_fallback_plan` (atomicité critique) ; conserver la double branche `llm_guard_error` / `count_below_min` distincte dans les logs.

## Design Notes

**Pattern §4decies — Leçon 40 (à ajouter à methodology.md) :**

Sur les tools de **génération créative** (plan d'action, recommandations, contenus structurés ouverts), la validation runtime stricte de §4nonies (BUG-V5-003 : ≥10 critères, ≥10 actions, etc.) bloque même les meilleurs LLM quand la complexité du prompt + la longueur du JSON dépassent leur fenêtre de fiabilité. Le pattern adaptatif est :

1. **Validation stricte 1ère tentative** (≥10 actions) — qualité optimale.
2. **Acceptation incrémentale ≥5 actions** — mode batch, message LLM « complète au prochain tour ».
3. **Fallback template déterministe** — dernier recours après échec total des retries internes du service. Garantit la disponibilité du feature même quand le provider LLM est indisponible ou défaillant.

Différence vs §4nonies (idempotence/dedup/whitespace) : §4nonies protège contre le **non-respect du tool calling** (le LLM ne persiste pas) ; §4decies protège contre la **défaillance qualité** du LLM même quand il appelle bien le tool. Les deux cohabitent : la validation reste activée, le fallback est juste un filet de sécurité ultime.

**Exemple template (3 lignes pour illustration) :**
```json
{"actions": [
  {"title": "Audit consommation énergétique {{sector}}", "category": "environment", "priority": "high", "due_date_offset_months": 2, "estimated_cost_xof": 500000},
  {"title": "Formation équipe ({{employee_count}} pers.) sur sécurité", "category": "social", "priority": "medium", "due_date_offset_months": 4, "estimated_cost_xof": 300000}
]}
```

**Helper `repair_json` — passes ordonnées :**
1. trailing comma : `re.sub(r",(\s*[}\]])", r"\1", text)`
2. single → double quotes (hors strings) : approche tolérante via état machine simple, sinon `text.replace("'", '"')` avec test parse
3. unquoted keys : `re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', text)`
4. `try json.loads(text)` après chaque passe ; succès → retour, sinon `None`.

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_tools/test_action_plan_tool_fallback.py -v` -- expected: 11 tests passent (3 json_repair + 2 template + 1 persistance + 4 tool + 2 FallbackTemplateError).
- `cd backend && source venv/bin/activate && pytest tests/test_tools/test_action_plan_tools.py tests/test_action_plan/ tests/test_graph/test_tools_instrumentation.py -v` -- expected: zéro régression.
- `cd backend && source venv/bin/activate && pytest --co -q tests/ 2>&1 | tail -3` -- expected: collection sans erreur.
- `cd backend && source venv/bin/activate && python -c "from app.services.action_plan_fallback import generate_fallback_actions; print(len(generate_fallback_actions({'sector':'agriculture','employee_count':10,'country':'Sénégal'}, 12)))"` -- expected: `10`.

**Manual checks:**
- Inspecter le log applicatif après un test de fallback simulé : la ligne `fallback_triggered user_id=… reason=llm_guard_error final_count=10` doit apparaître.
- Ouvrir `/action-plan` après fallback simulé : 10 actions visibles, catégories réparties (3 env, 2 soc, 2 gov, 2 fin, 1 carbon).

## Suggested Review Order

**Orchestration adaptative (entry point)**

- Try LLM, fallback sur `LLMGuardError` ou `count<5`, mode incrémental sinon.
  [`action_plan_tools.py:38`](../../backend/app/graph/tools/action_plan_tools.py#L38)
- Wrapper `_trigger_fallback` qui convertit `FallbackTemplateError` en `RuntimeError` capturable par `with_retry`.
  [`action_plan_tools.py:55`](../../backend/app/graph/tools/action_plan_tools.py#L55)
- Branche `count_below_min` avec log structuré distinct.
  [`action_plan_tools.py:91`](../../backend/app/graph/tools/action_plan_tools.py#L91)

**Fallback déterministe (cœur du patch)**

- `persist_fallback_plan` : single commit final + reload `selectinload(items)` + reason paramétrable.
  [`action_plan_fallback.py:121`](../../backend/app/services/action_plan_fallback.py#L121)
- Chargement template avec `FallbackTemplateError` typée (review #5).
  [`action_plan_fallback.py:50`](../../backend/app/services/action_plan_fallback.py#L50)
- `_substitute_placeholders` + `_coerce_str` (gère Enum sector).
  [`action_plan_fallback.py:96`](../../backend/app/services/action_plan_fallback.py#L96)

**Réparation JSON tolérante**

- Pipeline `repair_json` 4 passes (parse → trailing comma → unquoted keys → safe single quotes).
  [`json_repair.py:82`](../../backend/app/services/json_repair.py#L82)
- `_convert_top_level_single_quotes` no-op si `"` présent (protège l'apostrophe française, review #2).
  [`json_repair.py:57`](../../backend/app/services/json_repair.py#L57)
- Intégration dans `_extract_json_array` du service existant.
  [`service.py:38`](../../backend/app/modules/action_plan/service.py#L38)

**Template & doctrine**

- 10 actions ESG/Carbone/Financement avec placeholders.
  [`action_plan_default.json:1`](../../backend/app/templates/action_plan_default.json#L1)
- Capitalisation Leçon 40 §4decies.
  [`methodology.md:1203`](../../docs/CODEMAPS/methodology.md#L1203)

**Tests**

- 11 tests fallback (json_repair, template, persistance BDD réelle, intégration tool).
  [`test_action_plan_tool_fallback.py:1`](../../backend/tests/test_tools/test_action_plan_tool_fallback.py#L1)
- Test existant adapté au nouveau contrat batch incrémental.
  [`test_action_plan_tools.py:181`](../../backend/tests/test_tools/test_action_plan_tools.py#L181)
- Test instrumentation : `mock_plan.items` à 10 pour ne pas déclencher fallback.
  [`test_tools_instrumentation.py:961`](../../backend/tests/test_graph/test_tools_instrumentation.py#L961)
