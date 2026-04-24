---
title: 'BUG-V4-001 + BUG-V4-002 — Régressions bloquantes Vague 4 (widget cycle + spinbutton saisie)'
type: 'bugfix'
created: '2026-04-24'
status: 'done'
baseline_commit: 'db2454de38372b67eb20239248209d900e2ecddc'
context:
  - '{project-root}/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-4-2026-04-24.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Deux régressions N2 détectées en Vague 4 cassent le parcours ESG et le profil, bloquant en cascade ESG/rapports/matching/crédit/plan d'action. (1) BUG-V4-001 : après soumission du 1er widget ESG, l'IA produit le batch E1-E10 puis bascule en texte libre sur le pilier Social sans émettre de nouveau widget ; le state frontend reste perçu comme « pending » et l'input texte apparaît verrouillé (parité manquante avec `sendMessage`). (2) BUG-V4-002 : `ProfileField` type `number` envoie en PATCH l'ancienne valeur (25) alors que l'utilisateur a saisi 42 — le v-model sur `<input type="number">` ne capture pas toujours la saisie (reproductible via agent-browser).

**Approach :** (1) Renforcer le prompt `esg_scoring.py` pour imposer un `ask_interactive_question` à chaque transition de pilier, + ajouter parité defensive dans `submitInteractiveAnswer` (handle `interactive_question_resolved` + nettoyage de fin de stream). (2) Remplacer dans `ProfileField.vue` la lecture via `editValue` ref par une lecture DOM via template ref `inputEl.value` au moment de `confirmEdit()`, avec fallback vers `editValue`.

## Boundaries & Constraints

**Always :**
- Français avec accents dans tout texte UI nouveau.
- Dark mode respecté sur toute modification de composant (OBLIGATOIRE CLAUDE.md).
- Fix minimal, pas de refactor architectural (spec bugfix).
- Tests backend : `pytest` verts ; les 2 nouveaux tests (prompt ESG + useChat parité resolved) doivent passer.
- Frontend : `nuxt typecheck` vert.
- Parité cliente : si `submitInteractiveAnswer` ne traite pas `interactive_question_resolved`, la parité avec `sendMessage` doit être restaurée.

**Ask First :**
- Si le fix prompt ESG casse un snapshot golden existant → signaler et régénérer (comme db2454d).
- Si la correction widget doit s'étendre aux 5 autres spécialistes (carbon/financing/application/credit/action_plan), demander l'accord avant d'élargir le périmètre.

**Never :**
- Modifier le contrat SSE (`interactive_question` / `interactive_question_resolved`).
- Toucher au validator Pydantic `employee_count` (déjà correct en Vague 3).
- Modifier `WIDGET_INSTRUCTION` partagé (risque de régression multi-modules).
- Introduire un `watch(props.value)` dans `ProfileField` qui écraserait `editValue` pendant l'édition.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| BUG-V4-001 happy : fin pilier E, transition S | User soumet widget QCM pilier E → LLM batch_save_esg_criteria(E1-E10) → prompt oriente nouveau tour | LLM appelle `ask_interactive_question` pour pilier S ; widget S rendu ; input-bar widget active | N/A |
| BUG-V4-001 fallback : LLM n'appelle pas le widget | Stream submit termine sans event `interactive_question` | À la fin du stream, `currentInteractiveQuestion.value === null` ; ChatInput (texte) est rendu (non verrouillé) | Log dev seulement |
| BUG-V4-001 parité : event `interactive_question_resolved` arrive sur submit | Backend yield event au début du tour | Handler `submitInteractiveAnswer` met à jour `interactiveQuestionsByMessage` (state='answered') même si optimiste déjà fait | Ignore si id inconnu |
| BUG-V4-002 happy | `employee_count=25`, user ✎ → tape 42 → ✓ | PATCH body `{"employee_count":42}` ; store store/profil = 42 | N/A |
| BUG-V4-002 edge : champ vidé | User ✎ → efface → ✓ | PATCH body `{"employee_count":null}` | N/A |
| BUG-V4-002 edge : saisie non numérique | User ✎ → tape "abc" (type=number rejette à la saisie) → ✓ | `editValue` vide → emit null (comportement existant) | N/A |
| BUG-V4-002 edge : annulation | User ✎ → tape 42 → ✕ | Aucun emit, valeur origine préservée | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/prompts/esg_scoring.py` -- prompt système ESG : la section TRANSITION ENTRE PILIERS est déclarative mais ne force pas l'appel `ask_interactive_question`. Ajouter une règle explicite.
- `backend/app/api/chat.py:185-196` -- émission `interactive_question_resolved` en tête de tour sur widget_response. Contrat inchangé (référence).
- `frontend/app/composables/useChat.ts:497-530` -- handler `sendMessage` pour `interactive_question_resolved` (source de parité).
- `frontend/app/composables/useChat.ts:605-854` -- `submitInteractiveAnswer` : ne traite PAS `interactive_question_resolved`, absence de nettoyage fin de stream.
- `frontend/app/components/copilot/FloatingChatWidget.vue:623-637` -- v-if sur `currentInteractiveQuestion?.state === 'pending'` ; aucune modification (référence).
- `frontend/app/components/profile/ProfileField.vue:40-64, 121-129` -- init `editValue` + `<input v-model>` + `confirmEdit`. Lecture DOM via template ref manquante.
- `backend/tests/test_prompts/` -- emplacement pour test unitaire prompt ESG.
- `frontend/tests/composables/` (ou équivalent) -- emplacement pour test de parité useChat si infra présente ; sinon test doc.

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/prompts/esg_scoring.py` -- Ajouter une section **TRANSITION PILIER — TOOL CALL OBLIGATOIRE** : après `batch_save_esg_criteria` d'un pilier, le tour suivant DOIT invoquer `ask_interactive_question` pour présenter les questions du pilier suivant (Environnement → Social → Gouvernance). Interdire l'émission d'un message texte seul sans widget tant que les 30 critères ne sont pas évalués. -- Rationale : Hypothèse B du rapport V4, LLM laisse passer transition textuelle.
- [x] `frontend/app/composables/useChat.ts` -- Dans `submitInteractiveAnswer` stream loop (~line 738-820), ajouter une branche `else if (evt.type === 'interactive_question_resolved' && evt.id)` qui met à jour `interactiveQuestionsByMessage` (state, response_values, response_justification, answered_at) par parité avec `sendMessage`. Rationale : parité contrat SSE, éviter entrées stale dans la map. **Pas** de nouveau reset de `currentInteractiveQuestion` (optimistic reset ligne 651 suffit).
- [x] `frontend/app/composables/useChat.ts` -- Dans le `finally` de `submitInteractiveAnswer` (après le `while (true) read`), ajouter un garde-fou : si `currentInteractiveQuestion.value?.state !== 'pending'` mais non-null, forcer `currentInteractiveQuestion.value = null`. Rationale : si aucun `interactive_question` n'a été émis, s'assurer que l'input texte est débloqué (ceinture + bretelles).
- [x] `frontend/app/components/profile/ProfileField.vue` -- Ajouter `const inputEl = ref<HTMLInputElement | null>(null)` et `ref="inputEl"` sur l'`<input v-else>`. Dans `confirmEdit()`, lire la valeur effective via `const trimmed = (inputEl.value?.value ?? editValue.value).trim()` AVANT parse/emit. Rationale : BUG-V4-002, garantit que la saisie réelle dans le DOM est capturée même si un événement `input` a été manqué.
- [x] `backend/tests/test_prompts/test_esg_scoring_transition.py` -- Test unitaire vérifiant que `ESG_SCORING_PROMPT` contient la nouvelle règle de transition (mot-clé « TRANSITION PILIER » ou invariant équivalent) et cite `ask_interactive_question`. Rationale : défense en profondeur contre dérive prompt. **4 tests verts.**
- [x] `backend/tests/test_prompts/golden/esg_scoring.txt` -- Régénéré via `python -m tests.test_prompts._capture_golden --force` (drift sémantique attendu sur esg_scoring uniquement). `test_golden_snapshot_matches_post_refactor[esg_scoring]` vert.

**Acceptance Criteria :**
- Given un utilisateur évalue son ESG, when il soumet le widget du pilier E, then un nouveau widget (`ask_interactive_question`) pour le pilier Social apparaît au tour suivant et la progression continue jusqu'au pilier Gouvernance puis finalisation.
- Given le LLM échoue à appeler `ask_interactive_question` pour la transition, when le stream submit se termine, then `currentInteractiveQuestion.value` est null et `ChatInput` (texte) est rendu (l'utilisateur n'est pas piégé).
- Given le backend émet `interactive_question_resolved` en tête de tour, when le frontend est en flux `submitInteractiveAnswer`, then la question correspondante dans `interactiveQuestionsByMessage` passe bien à `state='answered'` avec les champs peuplés.
- Given un champ `ProfileField` type=number avec valeur 25, when l'utilisateur clique ✎, saisit 42, clique ✓, then le PATCH envoie `{"employee_count":42}` et la valeur persistée est 42 après F5.
- Given l'utilisateur vide un champ number et confirme, when ✓ est cliqué, then le PATCH envoie `{"employee_count":null}`.
- Given `pytest backend/tests/`, when exécuté, then 100% vert incluant le nouveau test prompt.

## Spec Change Log

### 2026-04-24 — Step 4 review patches (no loopback)
- **Finding** (Blind hunter MEDIUM) : la logique `domValue !== '' ? domValue : editValue.value` dans `ProfileField.confirmEdit` aurait écrasé un effacement volontaire si `editValue` était stale (domValue='', fallback sur editValue résiduel) — réel edge case.
- **Patch** : remplacement par `inputEl.value !== null ? (inputEl.value.value ?? '') : editValue.value`. Le DOM est source de vérité chaque fois que le `<input>` est monté ; fallback editValue réservé aux `<select>` (pas de ref).
- **Known-bad avoided** : utilisateur vide le champ → PATCH envoie l'ancienne valeur au lieu de null.
- **KEEP** : la décision de ne PAS ajouter de `watch(props.value)` (règle Never) reste valide — elle garantit l'immutabilité de l'état d'édition.
- **Defers** : DEF-BUG-V4-1 (fenêtre 1200 chars fragile), DEF-BUG-V4-2 (couverture frontend manquante) consignés dans deferred-work.md.
- **Note** : l'agent `review-edge-case-hunter` n'a pas pu être lancé (agent non enregistré dans le harness). Review effectuée avec 2/3 reviewers (Blind + Acceptance auditor).

## Design Notes

**Prompt ESG — ajout ciblé** (~10 lignes) :

```
## TRANSITION PILIER — TOOL CALL OBLIGATOIRE
Après avoir sauvegardé les 10 critères d'un pilier via `batch_save_esg_criteria`,
tu DOIS, au tour suivant, appeler `ask_interactive_question` (QCU ou QCM) pour
poser les questions du pilier suivant. Ne jamais envoyer un message texte seul
avec des questions listées — l'utilisateur doit pouvoir cliquer.
Séquence : E (10 critères) → widget S → S (10 critères) → widget G → G (10) →
confirmation finalisation → finalize_esg_assessment.
```

**Frontend ProfileField — template ref** :

```vue
<input
  v-else
  ref="inputEl"
  v-model="editValue"
  :type="type === 'number' ? 'number' : 'text'"
  ...
/>
```
```ts
const inputEl = ref<HTMLInputElement | null>(null)
function confirmEdit() {
  isEditing.value = false
  const domValue = inputEl.value?.value ?? ''
  const trimmed = (domValue || editValue.value).trim()
  // ... suite inchangée
}
```

**useChat parité** :

```ts
} else if (evt.type === 'interactive_question_resolved' && evt.id) {
  const newState = (evt.state || 'answered') as InteractiveQuestionState
  const updated: Record<string, InteractiveQuestion> = {}
  for (const [msgId, q] of Object.entries(interactiveQuestionsByMessage.value)) {
    updated[msgId] = q.id === evt.id
      ? { ...q, state: newState, response_values: evt.response_values ?? null,
          response_justification: evt.response_justification ?? null,
          answered_at: evt.answered_at ?? null }
      : q
  }
  interactiveQuestionsByMessage.value = updated
}
```

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest backend/tests/test_prompts/ -xvs` -- expected : nouveau test TRANSITION PILIER vert, pas de régression.
- `cd backend && source venv/bin/activate && pytest` -- expected : 1708+ tests verts (ligne de base db2454d).
- `cd frontend && npx nuxt typecheck` -- expected : aucune erreur TS.

**Manual checks :**
- Reproduire T-V4-W-07 + T-V4-ESG-02/03 : démarrer évaluation ESG via chat, soumettre widget pilier E, vérifier apparition widget pilier Social puis Gouvernance puis finalisation.
- Reproduire T-V4-PROFILE-01 : /profile → ✎ employés → saisir 42 → ✓ → F5 → valeur persistée = 42.
- DevTools Network EventStream : après submit widget E, confirmer events `interactive_question_resolved` (state='answered') + `interactive_question` (pilier S, state='pending') dans le stream.

## Suggested Review Order

**Intent du fix BUG-V4-001 — backend**

- Section prompt qui force le LLM à appeler `ask_interactive_question` à chaque transition de pilier (cœur du fix backend).
  [`esg_scoring.py:71`](../../backend/app/prompts/esg_scoring.py#L71)

**Intent du fix BUG-V4-001 — frontend**

- Handler `interactive_question_resolved` dans `submitInteractiveAnswer` : parité avec `sendMessage` pour éviter état stale.
  [`useChat.ts:818`](../../frontend/app/composables/useChat.ts#L818)

- Garde-fou `finally` : débloque l'input texte quand le LLM n'a émis aucun widget de rechange.
  [`useChat.ts:876`](../../frontend/app/composables/useChat.ts#L876)

- Extension du type inline pour tolérer les nouveaux champs émis par l'event resolved.
  [`useChat.ts:755`](../../frontend/app/composables/useChat.ts#L755)

**Intent du fix BUG-V4-002**

- Lecture DOM prioritaire dans `confirmEdit` — DOM source de vérité quand l'input est monté.
  [`ProfileField.vue:50`](../../frontend/app/components/profile/ProfileField.vue#L50)

- Template ref `inputEl` branché sur l'`<input>`.
  [`ProfileField.vue:24`](../../frontend/app/components/profile/ProfileField.vue#L24)

- Bind HTML du ref sur l'élément.
  [`ProfileField.vue:133`](../../frontend/app/components/profile/ProfileField.vue#L133)

**Tests & garde-fous**

- 4 tests unitaires sur la nouvelle règle prompt.
  [`test_esg_scoring_transition.py:1`](../../backend/tests/test_prompts/test_esg_scoring_transition.py#L1)

- Golden snapshot régénéré (drift sémantique attendu, prompt enrichi).
  [`golden/esg_scoring.txt:1`](../../backend/tests/test_prompts/golden/esg_scoring.txt#L1)
