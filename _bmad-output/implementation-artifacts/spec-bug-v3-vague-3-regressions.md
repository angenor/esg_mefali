---
title: 'BUG-V3 Vague 3 — Widget JSON brut, profil employee_count, consumo, seed funds'
type: 'bugfix'
created: '2026-04-24'
status: 'done'
baseline_commit: '54559d77ee2a65cc56a8bdb7d6dbde4fff71eacb'
context:
  - 'backend/app/api/chat.py'
  - 'backend/app/graph/tools/interactive_tools.py'
  - 'backend/app/prompts/widget.py'
  - 'backend/app/prompts/carbon.py'
  - 'backend/app/modules/company/schemas.py'
  - 'backend/app/modules/company/service.py'
  - 'frontend/app/composables/useChat.ts'
  - 'frontend/app/components/chat/MessageParser.vue'
  - 'frontend/app/components/profile/ProfileField.vue'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** La Vague 3 de tests manuels a détecté 4 régressions bloquantes. (1) BUG-V3-001 N1 : lorsque l'IA appelle `ask_interactive_question`, le JSON des arguments (`{"question_type":"qcu","options":[...]}`) apparaît en texte brut dans la bulle assistant en plus du widget, et l'input reste désactivé par la pending question. (2) BUG-V3-002 N1 : éditer `employee_count` via le spinbutton de `/profile` renvoie PATCH 200 mais après F5 la valeur est re-null — régression BUG-V2-007. (3) BUG-V3-003 N3 : le mot portugais/espagnol « consumo » apparaît dans les réponses de `carbon_node`. (4) DATA-V3-001 env : les tables `funds` et `intermediaries` sont vides sur l'env de test, la migration 033 n'a pas été appliquée.

**Approach:** (1) Filtrer côté frontend les tokens JSON widget qui s'échappent du LLM + durcir `WIDGET_INSTRUCTION` pour interdire explicitement tout texte après `ask_interactive_question` ; (2) Durcir le schéma Pydantic `CompanyProfileUpdate.employee_count` avec un validator qui coerce string→int en défense en profondeur, + ajouter un cast explicite `Number()` dans `ProfileField.vue` avant emit ; (3) Ajouter une règle explicite dans `carbon.py` interdisant le vocabulaire portugais/espagnol (« consumo », « consumo de energia ») au profit exclusif de « consommation » ; (4) Exécuter `alembic upgrade head` sur l'env de test pour appliquer la migration 033 idempotente.

## Boundaries & Constraints

**Always:**
- Les 4 correctifs restent indépendants et testables isolément.
- Le filtre frontend JSON widget n'affecte JAMAIS les blocs visuels (chart/mermaid/table/gauge/progress/timeline) ni le markdown légitime.
- Le validator `employee_count` préserve `ge=0, le=100_000`.
- La règle anti-« consumo » est ajoutée en français uniquement (pas de traduction pt/es dans le prompt).

**Ask First:** Aucune décision humaine requise — root causes identifiées, patchs additifs.

**Never:**
- Toucher aux composants Interactive* (SingleChoice, MultipleChoice, Host, InputBar) — ils sont OK.
- Refactorer `stream_graph_events` ou la logique SSE backend — l'émission marker fonctionne, c'est le LLM qui double-émet.
- Modifier la migration 033 (idempotente, déjà en place).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| BUG-V3-001 happy | LLM appelle tool + émet aussi `{"question_type":"qcu","options":[...]}` en texte | Widget affiché, JSON filtré de la bulle, input désactivé tant que pending | Si filtre rate, JSON affiché mais widget OK (dégradation graceful) |
| BUG-V3-001 édge | LLM émet JSON malformé ou tronqué en streaming | Token passe au rendu, aucune exception côté parser | Ne pas planter le stream |
| BUG-V3-002 happy | Spinbutton 15 → PATCH `{"employee_count":15}` | DB stocke 15, F5 renvoie 15 | N/A |
| BUG-V3-002 edge | Spinbutton envoie `"15"` (string) | Validator coerce → DB 15 | string non numérique → 422 explicite |
| BUG-V3-003 | User pose question carbone | Réponse contient exclusivement « consommation », jamais « consumo » | N/A |
| DATA-V3-001 | Env test, `funds` vide | `alembic upgrade head` applique 033 → 12 fonds + 14 intermédiaires seedés | Idempotence : re-run no-op |

</frozen-after-approval>

## Code Map

- `backend/app/graph/tools/interactive_tools.py` — tool `ask_interactive_question` (marker SSE OK, ne pas toucher)
- `backend/app/api/chat.py:206-283` — `stream_graph_events`, émission SSE widget (OK, ne pas toucher)
- `backend/app/prompts/widget.py:8-50` — `WIDGET_INSTRUCTION` partagé 7 modules (à durcir)
- `backend/app/prompts/carbon.py` — prompt carbone (ajouter règle anti-« consumo »)
- `backend/app/modules/company/schemas.py:62-89` — `CompanyProfileUpdate` (ajouter validator employee_count)
- `frontend/app/composables/useChat.ts:206-214` — handler `on_chat_model_stream` → tokens (site de filtre possible)
- `frontend/app/components/chat/MessageParser.vue:14-19` — segments parsing (site de filtre préféré)
- `frontend/app/composables/useMessageParser.ts` — parse logic (à vérifier)
- `frontend/app/components/profile/ProfileField.vue:44-57` — `confirmEdit` (cast déjà présent, renforcer)

## Tasks & Acceptance

**Execution:**

- [x] `frontend/app/composables/useMessageParser.ts` -- Filtre regex `WIDGET_JSON_LEAK_REGEX` + helper `pushText` appliqué à chaque site d'ajout de segment texte
- [x] `backend/app/prompts/widget.py` -- Section « INTERDIT ABSOLU — Ne jamais ecrire le JSON en texte » ajoutée après les 3 règles existantes
- [x] `backend/app/prompts/carbon.py` -- Section « VOCABULAIRE OBLIGATOIRE » ajoutée sous `## ROLE` bannissant « consumo »/« consumo de energia »/« consumo electrico »
- [x] `backend/app/modules/company/schemas.py` -- `@field_validator` mode="before" sur employee_count/annual_revenue_xof/year_founded coerce string→int ou lève ValueError
- [x] `frontend/app/components/profile/ProfileField.vue` -- `confirmEdit` explicite avec `Number.isNaN` + `Number(parsed)` pour garantir sérialisation JSON int
- [x] `backend/tests/test_company_api.py` -- `test_update_profile_employee_count_string_coerced` + `test_update_profile_employee_count_string_invalid` ajoutés
- [x] `backend/tests/test_prompts/test_carbon_node_tools.py` -- `test_carbon_prompt_bans_consumo_vocabulary` + `test_build_carbon_prompt_contains_vocabulary_rule` ajoutés
- [x] `backend/tests/test_prompts/golden/*.txt` -- Regen golden snapshots (drift sémantique attendu : ajouts WIDGET_INSTRUCTION + carbon vocab)
- [ ] DATA-V3-001 (ops, à exécuter manuellement sur env test) -- `cd backend && source venv/bin/activate && alembic upgrade head` ; vérifier `SELECT COUNT(*) FROM funds` >= 12

**Acceptance Criteria:**
- Given un tour LLM où MiniMax émet à la fois tool call `ask_interactive_question` ET texte JSON des args, when le stream arrive au frontend, then la bulle assistant affiche uniquement le texte non-JSON et le widget cliquable, sans duplication visuelle.
- Given un user édite `employee_count` via spinbutton avec valeur 15, when il valide et reload F5, then la valeur 15 est toujours affichée.
- Given un user pose une question carbone à l'IA, when l'IA répond, then aucun mot « consumo » n'apparaît — uniquement « consommation ».
- Given env de test avec `alembic upgrade head` appliqué, when on liste les fonds via `/api/financing/funds`, then on voit au moins 12 fonds et 14 intermédiaires.
- Tous les tests existants passent (935+ backend verts, frontend tsc propre).

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_modules/test_company_service.py tests/test_prompts/test_carbon_prompt.py -x` — expected: pass
- `cd backend && source venv/bin/activate && pytest -q` — expected: ≥ 935 passed, 0 failed
- `cd frontend && npx tsc --noEmit` — expected: no errors
- `cd backend && source venv/bin/activate && alembic upgrade head` — expected: "Target database is up to date" ou application de 033

**Manual checks:**
- Chat → déclencher widget QCU → bulle assistant sans JSON visible, widget cliquable affiché, input désactivé tant que question pending.
- /profile → éditer employee_count à 15 via spinbutton → valider → F5 → valeur 15 persistée.
- Chat → /carbon → poser question « Quelle est ma consommation d'énergie ? » → aucune occurrence de « consumo » dans les réponses suivantes.

## Spec Change Log

**2026-04-24 — Blind hunter review (specLoopIteration=1)** — 2 HIGH findings patchés sans loopback :
1. `useMessageParser.ts:19` — regex renforcée avec ancres `^` `$` + flag `m` pour éviter faux positif sur contenu pédagogique inline.
2. `schemas.py:86` — validator `_coerce_int_strings` blindé : bool explicitement rejeté (évite coerce silencieuse `True → 1`).

## Suggested Review Order

**Frontend : filtre anti-fuite widget (BUG-V3-001)**

- Entrée principale : regex + helper qui nettoient le JSON widget orphelin avant rendu markdown.
  [`useMessageParser.ts:19`](../../frontend/app/composables/useMessageParser.ts#L19)

- Application du filtre à tous les sites d'ajout de segment texte.
  [`useMessageParser.ts:35`](../../frontend/app/composables/useMessageParser.ts#L35)

**Backend : prompt hardening (BUG-V3-001 + BUG-V3-003)**

- Section « INTERDIT ABSOLU » ajoutée à la doctrine partagée par les 7 modules.
  [`widget.py:33`](../../backend/app/prompts/widget.py#L33)

- Règle vocabulaire bannissant explicitement « consumo » (pt/es) dans le prompt carbone.
  [`carbon.py:10`](../../backend/app/prompts/carbon.py#L10)

**Backend : validation profil (BUG-V3-002)**

- Validator Pydantic v2 mode=before : coerce string→int, rejette bool, 422 explicite si invalide.
  [`schemas.py:86`](../../backend/app/modules/company/schemas.py#L86)

**Frontend : cast numérique profil (BUG-V3-002)**

- Belt & suspenders : `Number.isNaN` + `Number(parsed)` garantit int JSON-serialisé.
  [`ProfileField.vue:51`](../../frontend/app/components/profile/ProfileField.vue#L51)

**Tests**

- 2 tests intégration PATCH profile : string "15" coerce en 15, string "quinze" lève 422.
  [`test_company_api.py:157`](../../backend/tests/test_company_api.py#L157)

- 2 tests prompt carbon : présence VOCABULAIRE OBLIGATOIRE + mot « consumo » listé comme interdit.
  [`test_carbon_node_tools.py:23`](../../backend/tests/test_prompts/test_carbon_node_tools.py#L23)

- Golden snapshots regénérés (drift sémantique attendu sur carbon + widget).
  [`golden/carbon.txt`](../../backend/tests/test_prompts/golden/carbon.txt)
