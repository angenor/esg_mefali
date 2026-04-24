---
title: 'BUG-V5-001 + BUG-V5-002 — Finalisation ESG persistée + scroll chat pendant streaming'
type: 'bugfix'
created: '2026-04-24'
status: 'done'
baseline_commit: '5d7dc2713981430e3faf41649e2f84d3cd9b591c'
context:
  - '{project-root}/CLAUDE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-5-2026-04-24.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Deux régressions bloquantes en vague 5. (1) À la fin d'un parcours ESG complet (9 questions groupées → 30 critères), l'IA annonce un score textuel ("moyenne 6/10") sans appeler `finalize_esg_assessment` : l'évaluation reste `in_progress`, le dashboard/`/esg/results` sont vides, plus aucun flux aval (rapport, matching, plan d'action) ne s'amorce. (2) Le scroll automatique du chat reste figé pendant le streaming : `scrollTop` n'avance pas alors que `scrollHeight` croît (777 vs 1656 observé), rendant les messages longs illisibles sans intervention manuelle.

**Approach:** (1) Renforcer le prompt `esg_scoring.py` avec une règle absolue « FINALISATION OBLIGATOIRE » qui impose l'appel tool après les 30 critères, et injecter explicitement `assessment_id` dans l'état conversationnel transmis au LLM pour qu'il puisse appeler le tool correctement. (2) Corriger l'interaction `handleScroll` / `scrollTo(behavior: 'smooth')` dans `FloatingChatWidget.vue` : le scroll programmatique fluide déclenche des évènements scroll intermédiaires qui font bascule `userScrolledUp=true`, désactivant ensuite l'auto-scroll. Guard via flag `isProgrammaticScroll`.

## Boundaries & Constraints

**Always:**
- BUG-V5-001 : conserver l'instruction existante de confirmation utilisateur avant finalize (le tool ne doit pas être appelé sans accord explicite). La règle renforcée impose le **tool call** après confirmation, pas la finalisation sans confirmation.
- BUG-V5-001 : `assessment_id` doit apparaître verbatim dans le bloc `ETAT DE L'EVALUATION EN COURS` injecté au prompt (sinon le LLM ne peut pas passer l'UUID au tool).
- BUG-V5-002 : préserver le comportement « respect du scroll manuel » — si l'utilisateur scrolle vers le haut intentionnellement, l'auto-scroll reste désactivé jusqu'à retour en bas.
- BUG-V5-002 : le fix ne doit pas casser le scroll initial à l'ouverture du widget ni le scroll lors de nouveaux messages non-streamés.
- Accents français obligatoires dans toutes les chaînes utilisateur modifiées.

**Ask First:**
- Si l'investigation révèle que `finalize_esg_assessment` a d'autres appelants qui dépendent du flow actuel (ex: bouton frontend), HALT avant modification.
- Si une solution plus radicale (passer `behavior: 'auto'` pendant le streaming) impacte l'UX, HALT.

**Never:**
- Ne pas modifier le schéma BDD ni les modèles SQLAlchemy.
- Ne pas toucher au tool `finalize_esg_assessment` lui-même (signature, logique) — seul le prompt et l'injection `assessment_id` changent côté backend.
- Ne pas ajouter de nouveau composant Vue ni refactorer la structure du widget.
- Ne pas supprimer le flag `userScrolledUp` ni le watcher `streamingContent` existants.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| ESG 30 critères saisis, utilisateur confirme finaliser | `evaluated_criteria.length === 30` + message utilisateur de confirmation | LLM appelle `finalize_esg_assessment(assessment_id=<uuid>)`, statut BDD passe à `completed`, scores persistés | Si tool échoue, message d'erreur FR à l'utilisateur + retry 1× (retry déjà configuré par `with_retry`) |
| ESG 30 critères, utilisateur pas encore de confirmation | `evaluated_criteria.length === 30` | LLM demande confirmation avant d'appeler le tool (règle préservée) | N/A |
| ESG <30 critères | évaluation en cours | Pas d'appel `finalize_esg_assessment`, le flow pilier-par-pilier continue | N/A |
| Chat streaming d'un message long | `isStreaming=true`, tokens arrivent | `messagesContainer.scrollTop` suit `scrollHeight` jusqu'à la fin | Si `userScrolledUp=true` (défilement user authentique), pas de scroll forcé |
| Utilisateur scrolle vers le haut pendant streaming | user scroll UP réel | `userScrolledUp=true`, auto-scroll pausé | N/A |
| Nouveau message après scroll manuel vers le haut | `userScrolledUp=true`, nouveau user message envoyé | `sendMessage` reset `userScrolledUp=false` (comportement existant préservé) | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/prompts/esg_scoring.py` — prompt système ESG, section `FINALISATION` à renforcer avec tool call obligatoire
- `backend/app/graph/nodes.py` — fonction `esg_scoring_node`, bloc `esg_state_context` (ligne ~684) : ajouter `assessment_id` dans les infos injectées au LLM
- `backend/app/graph/tools/esg_tools.py` — tool `finalize_esg_assessment` (ligne 128) : référence uniquement, aucune modification
- `frontend/app/components/copilot/FloatingChatWidget.vue` — fonctions `scrollToBottom` (ligne 434) et `handleScroll` (ligne 443) : ajouter flag `isProgrammaticScroll`
- `backend/tests/test_graph/test_specialists_language_reminder.py` — pattern existant pour tests prompts ESG (référence)
- `backend/tests/test_prompts/` — si existant, ajouter un test vérifiant la présence du marqueur "FINALISATION OBLIGATOIRE"

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/prompts/esg_scoring.py` — remplacer la section `## FINALISATION` par une section `## FINALISATION — TOOL CALL OBLIGATOIRE` imposant l'appel `finalize_esg_assessment(assessment_id=<uuid>)` après les 30 critères **et** la confirmation utilisateur, avec interdiction explicite de répondre textuellement avec un score
- [x] `backend/app/graph/nodes.py` — dans `esg_scoring_node`, ajouter `- Identifiant evaluation (assessment_id) : {assessment_id}` dans le bloc `ETAT DE L'EVALUATION EN COURS` afin que le LLM dispose de l'UUID à passer au tool
- [x] `frontend/app/components/copilot/FloatingChatWidget.vue` — introduire une ref `isProgrammaticScroll` (+ timer), setter à `true` dans `scrollToBottom()` avec reset via `setTimeout(~600ms)` après la fin de l'animation smooth ; dans `handleScroll()`, retourner tôt si `isProgrammaticScroll.value === true`
- [x] `backend/tests/test_graph/test_esg_finalize_prompt.py` (nouveau) — test unitaire vérifiant que `ESG_SCORING_PROMPT` contient les marqueurs "FINALISATION" et "finalize_esg_assessment" et que `esg_scoring_node` injecte `assessment_id` dans le prompt final (mock du LLM pour inspecter `chat_messages`)

**Acceptance Criteria:**
- Given une évaluation ESG avec 30 critères évalués et confirmation utilisateur de finalisation, when le tour LLM suivant s'exécute, then le LLM appelle `finalize_esg_assessment` avec l'UUID `assessment_id` et la BDD passe `status='completed'`.
- Given le prompt compilé pour `esg_scoring_node`, when on inspecte le `SystemMessage`, then il contient une sous-chaîne littérale "assessment_id" suivie de l'UUID courant (pas "pending" pour une reprise).
- Given un message IA streamé sur plus de 800px de hauteur, when le streaming complète, then `messagesContainer.scrollTop + clientHeight >= scrollHeight - 10` (bas de la liste atteint).
- Given un utilisateur qui scrolle manuellement vers le haut pendant le streaming, when de nouveaux tokens arrivent, then `userScrolledUp` reste `true` et aucun scroll forcé n'intervient.

## Design Notes

**Root cause BUG-V5-002 (non triviale).** Le watcher `streamingContent` appelle `scrollToBottom()` qui utilise `behavior: 'smooth'`. Le scroll fluide déclenche des évènements scroll intermédiaires pendant l'animation ; pendant ces évènements `scrollHeight - scrollTop - clientHeight > 100` est vrai (l'animation n'a pas fini), donc `handleScroll()` positionne `userScrolledUp=true`, ce qui désactive les scrolls suivants — boucle : plus aucun token ne fait scroller. Le flag `isProgrammaticScroll` distingue scroll programmatique du scroll utilisateur réel.

Exemple guard minimal :

```typescript
const isProgrammaticScroll = ref(false)
let _programmaticResetTimer: ReturnType<typeof setTimeout> | null = null

function scrollToBottom() {
  if (!messagesContainer.value || !isVisible.value) return
  isProgrammaticScroll.value = true
  messagesContainer.value.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: 'smooth' })
  if (_programmaticResetTimer) clearTimeout(_programmaticResetTimer)
  _programmaticResetTimer = setTimeout(() => { isProgrammaticScroll.value = false }, 600)
}

function handleScroll() {
  if (!messagesContainer.value || isProgrammaticScroll.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  userScrolledUp.value = scrollHeight - scrollTop - clientHeight > 100
}
```

**Root cause BUG-V5-001.** Le prompt oublie de lier « 30 critères atteints » → « tool call finalize ». La section `## FINALISATION` décrit ce que le LLM doit dire, pas ce qu'il doit faire via tool. De plus, le bloc d'état runtime (`nodes.py:684`) n'injecte pas `assessment_id`, donc même si le LLM voulait appeler `finalize_esg_assessment(assessment_id=...)`, il ne connaît pas l'UUID (sauf à l'avoir mémorisé d'un tour antérieur, peu fiable). Les 2 patchs sont cumulatifs : prompt renforcé + état enrichi.

## Verification

**Commands:**
- `cd backend && source venv/bin/activate && pytest tests/test_graph/test_esg_finalize_prompt.py -v` — expected: nouveaux tests passent (tool call + injection assessment_id)
- `cd backend && source venv/bin/activate && pytest tests/test_graph/ -q` — expected: aucune régression (0 échec)
- `cd frontend && npm run typecheck` — expected: aucun nouveau type error

**Manual checks:**
- Parcours ESG complet dans le chat → à la fin, vérifier en BDD (`psql` ou API `/api/esg/assessments/<id>`) que `status='completed'` et scores remplis.
- Envoyer un message long (IA streamée) → observer dans devtools que `messagesContainer.scrollTop` progresse de concert avec `scrollHeight` jusqu'à la fin du streaming.
- Scroller manuellement vers le haut pendant le streaming → vérifier que l'auto-scroll ne reprend pas tant que l'utilisateur ne redescend pas en bas.

## Spec Change Log

**2026-04-24 — Patches issus de step-04 review (3 reviewers : blind, edge-case, acceptance auditor)**

- **Trigger** : findings HIGH/MEDIUM dédupliqués sur (a) `assessment_id == "pending"` injecté tel quel dans le prompt → risque que le LLM appelle `finalize_esg_assessment(assessment_id="pending")` provoquant `uuid.UUID("pending") → ValueError` ; (b) timer reset 600 ms trop court pour scrolls smooth longue distance (700–1200 ms observé) ; (c) test em-dash fragile à un refactor de séparateur ; (d) commentaires FR ajoutés sans accents (CLAUDE.md exige é/è/ê/à/ç/ù).
- **Patches appliqués** : (a) guard conditionnel dans `nodes.py:esg_state_context` — ligne `pending` accompagnée d'une consigne explicite « appelle d'abord create_esg_assessment ; n'appelle JAMAIS finalize avec "pending" » ; (b) timer 600 → 1200 ms dans `FloatingChatWidget.vue:scrollToBottom` ; (c) regex tolérante em-dash/en-dash/hyphen dans `test_esg_finalize_prompt.py:test_esg_prompt_has_finalisation_tool_call_section` ; (d) accents ajoutés sur les 2 commentaires V5 (FloatingChatWidget + nodes.py).
- **État connu-mauvais évité** : finalize ESG appelé avec UUID invalide → erreur 500/tool retry sans guard utilisateur ; auto-scroll cassé sur reprise widget après fermeture longue ; tests bloquants au moindre refactor de séparateur ; violation soft CLAUDE.md sur les accents.
- **KEEP instructions** : conserver le flag `isProgrammaticScroll` (architecture validée par les 3 reviewers) ; conserver l'inspection statique du prompt comme test (couverture suffisante pour AC structurels — un test runtime LLM-mock est tracé dans deferred-work.md DEF-BUG-V5-2).
- **Differred (non-patch)** : `wheel`/`touchstart`/`pointerdown` listeners (DEF-BUG-V5-1), test runtime LLM-mock (DEF-BUG-V5-2), `scrollend` event listener (DEF-BUG-V5-3).
- **Rejected** : (1) "fuite de score partiel" — la REGLE ABSOLUE du prompt couvre déjà ce cas, limite inhérente LLM ; (2) "module-scoped `let` timer" — `<script setup>` scope per-instance, finding erroné ; (3) "refus utilisateur de finaliser" — comportement correct par construction.

## Suggested Review Order

**Backend — Persistance ESG**

- Renforcement du prompt avec interdiction explicite du score textuel sans tool call.
  [`esg_scoring.py:86`](../../backend/app/prompts/esg_scoring.py#L86)

- Injection conditionnelle de `assessment_id` (avec guard "pending") dans l'état runtime.
  [`nodes.py:684`](../../backend/app/graph/nodes.py#L684)

**Frontend — Auto-scroll chat**

- Flag `isProgrammaticScroll` distinguant scroll smooth interne du scroll utilisateur réel.
  [`FloatingChatWidget.vue:434`](../../frontend/app/components/copilot/FloatingChatWidget.vue#L434)

- Garde tôt dans `handleScroll` empêchant les évènements smooth de polluer `userScrolledUp`.
  [`FloatingChatWidget.vue:462`](../../frontend/app/components/copilot/FloatingChatWidget.vue#L462)

- Cleanup timer dans `onBeforeUnmount` pour éviter fuite si démontage pendant animation.
  [`FloatingChatWidget.vue:478`](../../frontend/app/components/copilot/FloatingChatWidget.vue#L478)

**Tests & traçabilité**

- 4 tests statiques garantissant les invariants prompt + injection state.
  [`test_esg_finalize_prompt.py:1`](../../backend/tests/test_graph/test_esg_finalize_prompt.py#L1)

- Travaux différés tracés (listeners scroll, test runtime LLM-mock, `scrollend`).
  [`deferred-work.md:3`](./deferred-work.md#L3)
