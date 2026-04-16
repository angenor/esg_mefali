# Backlog de dette technique

> **Source canonique** : [_bmad-output/implementation-artifacts/deferred-work.md](../_bmad-output/implementation-artifacts/deferred-work.md)
> **Dernière synchronisation** : 2026-04-16
> **Nature** : extraits et regroupements des « deferred from code review » + bugs partiellement traités + bugs résolus récents. Se référer au fichier source pour la formulation intégrale et les références de code précises.

## 1. Résumé exécutif

- **En cours / partiellement résolu** : 1 item (BUG-1 placeholders vides dans les popovers de tour carbone).
- **Dettes différées ouvertes** : ~40 items issus des reviews des stories 3-1, 3-2, 4-1, 4-2, 4-3, 5-1, 6-1, 6-2, 6-3, 6-4, 7-1, 7-2, 7-3, 8-1 et 8-3.
- **Bugs résolus récents** (2026-04-14 / 15) : 3 (SSE whitelist `guided_tour`, LLM hallucine outil indisponible, lecture de bilan carbone `completed`).

---

## 2. En cours — non résolu

### BUG-1 (feature 019) — placeholders vides dans le popover carbone

- **Symptôme** : après le fix du 2026-04-15 (commit 8c71101), le LLM appelle bien `trigger_guided_tour(tour_id, context={sector, total_tco2, top_category, top_category_pct})`, mais **les valeurs numériques restent `None`** (seul `sector` est résolu depuis le profil entreprise). Conséquence : les popovers affichent *« Votre empreinte est de  tCO2e. […] représente % du total. »* (placeholders vides).
- **Cause** : `chat_node` ne reçoit ni les stats carbone ni le résumé du bilan dans son prompt, et `router_node` garde le message « Montre-moi mes résultats carbone » dans `chat_node` au lieu de transitionner vers `carbon_node` (qui aurait accès à `get_carbon_summary`).
- **Fix à venir (2 options)** :
  1. Router vers `carbon_node` sur l'intent « résultats / bilan / empreinte + `current_page == /carbon/results` ».
  2. Injecter un résumé carbone dans le system prompt de `chat_node` lorsque `current_page == /carbon/results`.
- **Statut** : déterministe, hors scope du fix surface du 2026-04-15.

---

## 3. Dettes différées — par domaine

### 3.1 Auth & Frontend API plumbing

**Story 7-2** (JWT renouvellement transparent) :
- `refreshPromise` module-level dans [useAuth.ts](../frontend/app/composables/useAuth.ts#L49) — risque théorique de partage SSR ; composable client-only en pratique mais pas de guard `import.meta.client` explicite.
- `useCarbon.fetchBenchmark` / `useEsg.fetchBenchmark` avalent toutes les erreurs non-session-expirée et retournent `null` → UI ne peut pas distinguer 404 vs 500. ([useCarbon.ts:93-98](../frontend/app/composables/useCarbon.ts#L93), [useEsg.ts:90-96](../frontend/app/composables/useEsg.ts#L90)).
- Tests manquants : cycle 401 sur `apiFetchBlob` (fiche de préparation PDF), `/auth/me`, échec d'import dynamique dans `handleAuthFailure`.
- **Dette majeure** : composables non migrés vers `apiFetch` — `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat` — ne bénéficient pas de l'intercepteur 401. À traiter dans une story dédiée `X-Y-migration-composables-vers-apifetch`.

### 3.2 Contexte page courante (current_page)

**Story 3-1** :
- Pas d'annotation reducer pour `current_page` dans `ConversationState` ([state.py:36](../backend/app/graph/state.py#L36)) — le champ pourrait ne pas se propager si un nœud LangGraph retourne un state partiel.
- `invoke_graph` n'accepte pas `current_page` → incohérence latente avec `stream_graph_events`. Vérifier l'utilisation ou supprimer. ([chat.py:56](../backend/app/api/chat.py#L56))

**Story 3-2** :
- Aucun nœud ne retourne `current_page` dans son `return {}` → risque théorique d'écrasement par le checkpoint (impact quasi-nul car re-injecté dans `initial_state`).
- `send_message_json` passe toujours `current_page=None` ([chat.py:938](../backend/app/api/chat.py#L938)) — endpoint de compatibilité non utilisé par le frontend actuel.
- Routes dynamiques (`/financing/123`) tombent sur la branche générique du prompt ([system.py:138](../backend/app/prompts/system.py#L138)) — nécessite un design de prefix matching.
- Valeur initiale `"/"` dans [`uiStore.currentPage`](../frontend/app/stores/ui.ts#L17) envoyée au backend comme page inconnue — initialiser à `null` ou ajouter `"/"` à `PAGE_DESCRIPTIONS`.
- Tests ne couvrent pas le chemin complet nœud → prompt pour 5 des 6 spécialistes (carbon, financing, application, credit, action_plan).

### 3.3 Tours guidés (driver.js + useGuidedTour)

**Story 4-1** :
- Pas de `timeout` sur `requestIdleCallback` dans [`prefetchDriverJs()`](../frontend/app/composables/useDriverLoader.ts#L25) — sous charge CPU le prefetch peut ne jamais se déclencher ; fallback `loadDriver()` OK mais avec latence.
- Couleurs hexadécimales hardcodées en mode clair dans les overrides Driver.js CSS ([main.css](../frontend/app/assets/css/main.css)) — incohérence avec le dark mode qui utilise des variables CSS.

**Story 4-2** :
- `countdown` sans borne min/max — accepte 0, négatif, NaN. Validation à ajouter dans `useGuidedTour`.
- `lib/` pas dans les dirs auto-import Nuxt — import manuel requis (choix d'architecture).
- `tsconfig.json` étend `.nuxt/tsconfig.json` → tests TypeScript cassent avant `nuxt prepare` en clone frais.
- `route` field non contraint dans `GuidedTourStep` — typo silencieux au runtime.
- `TourContext = Record<string, unknown>` sans contrat entre placeholders attendus et contexte fourni → risque d'afficher `{{variable}}` brut.

**Story 4-3** :
- Route mismatch dans [`registry.ts:22`](../frontend/app/lib/guided-tours/registry.ts#L22) : `show_esg_results` déclare `route: '/esg'` mais `esg-score-circle` est sur `/esg/results`.
- 8 éléments `data-guide-target` dans des blocs `v-if` (strengths-badges, recommendations, donut-chart, benchmark, reduction-plan, action-plan-timeline, credit-score-gauge, dashboard cards pendant loading) — le moteur doit gérer les éléments absents via skip / attente / fallback.

**Story 5-1** :
- Délai transition `complete → idle` hardcodé à 1000 ms ([useGuidedTour.ts:162-166](../frontend/app/composables/useGuidedTour.ts#L162)) — AC5 mentionne un délai configurable.
- Élément DOM peut être supprimé entre `waitForElement` et `highlight` ([useGuidedTour.ts:112-124](../frontend/app/composables/useGuidedTour.ts#L112)) — fenêtre très courte, limitation architecturale.

**Story 6-1** :
- Pas d'allowlist serveur pour `tour_id` — validation déléguée au registre frontend (par conception). Hardening défense-en-profondeur possible plus tard.
- `context` dict sans limite de taille/profondeur — un LLM pourrait envoyer un context énorme.
- Marker SSE split entre chunks de streaming ([chat.py:212-239](../backend/app/api/chat.py#L212)) — parser suppose un `on_tool_end` avec output complet.
- Plusieurs markers SSE dans un seul output non tous parsés — `index()` ne trouve que le premier `-->`.

**Story 6-2** :
- Couplage `STYLE_INSTRUCTION` / `GUIDED_TOUR_INSTRUCTION` via la même branche conditionnelle `_has_minimum_profile` dans `build_system_prompt` ([system.py:211-217](../backend/app/prompts/system.py#L211)) — un changement de seuil du style concis déplacera silencieusement le guidage.
- Pas d'assertion positionnelle sur l'ordre `WIDGET_INSTRUCTION` → `GUIDED_TOUR_INSTRUCTION` dans les 5 prompts spécialisés.
- Chemins frontend listés dans la docstring `GUIDED_TOUR_INSTRUCTION` non épinglés contre le registre Nuxt réel → divergence silencieuse possible.

**Story 6-3** :
- T-AC2 / T-AC6 court-circuitent `useGuidedTour` via mock statique — pas de validation du code path runtime réel.
- Plancher `count("GUIDED_TOUR_TOOLS") >= 12` dans T11 conflate shape et correctness.
- T-AC3 (refus consent) ne prouve pas le respect du refus (test passe car backend n'émet pas `guided_tour`, pas parce que `no` est honoré). Pas de guard `yes`-only côté frontend.
- `GUIDED_TOUR_INSTRUCTION` injecté inconditionnellement (y compris sessions anonymes / sans profil) — bloat tokens par requête.
- Aucun test cross-file alignant les 6 `tour_id` entre `guided_tour.py` (prompt), `registry.ts` (frontend), `guided_tour_tools.py` (backend tool enum).

**Story 6-4** (fréquence adaptative) :
- Décroissance / cap global sur `acceptance_count` et `refusal_count` — saturation indéfinie après ~5 acceptations (plancher 3 s permanent). Décision produit à arbitrer : cap dur vs decay temporel.
- `send_message_json` ne transmet pas `guidance_stats` au graphe ([chat.py:~976](../backend/app/api/chat.py#L976)) — volontaire par spec.
- Perte de précision au-delà de `Number.MAX_SAFE_INTEGER` dans `loadGuidanceStats`.
- Race théorique entre `currentInteractiveQuestion` lu avant `await import(...)` et event SSE `interactive_question_resolved` concurrent.
- SSE `guided_tour` arrivant pendant une question interactive `pending` → état orphelin (refus déjà comptabilisé, acceptance non comptabilisée).
- `test_guided_tour_instruction_unchanged` vérifie seulement une plage de longueur (3500-6000 chars) — pas un vrai verrou anti-régression sémantique. Passer à un snapshot.
- `try { ... } catch {}` silencieux autour de l'import dynamique dans [useChat.ts:464-466](../frontend/app/composables/useChat.ts#L464) — swallow sans observabilité.
- **Dette multi-utilisateur** : clé localStorage `esg_mefali_guidance_stats` doit migrer vers un scope par user (prefixe `user_id:` ou backend `user_guidance_stats`). À revisiter au démarrage du module 7 (admin/collaborateur/lecteur).

**Story 7-1** (DOM absent + timeout) :
- [`Date.now()`](../frontend/app/composables/useGuidedTour.ts#L179) non-monotone dans `waitForElementExtended` — bascule NTP/DST peut fausser `elapsedMs`. Préférer `performance.now()`.
- `setTimeout(..., 500)` dans `interruptTour` / `cancelTour` jamais annulé ([useGuidedTour.ts:250-252,662-666](../frontend/app/composables/useGuidedTour.ts#L250)) — leak mineur de timers.
- `cancelled` non réinitialisé sur le chemin de succès de `startTour` ([useGuidedTour.ts:278](../frontend/app/composables/useGuidedTour.ts#L278)) — état résiduel entre deux parcours consécutifs sans cancel.
- `cancelTour` ré-entrant pendant la transition `interrupted → idle` → timeouts dupliqués. Ajouter `'interrupted'` à la garde.
- Cleanup du catch global à placer dans un `finally` ([useGuidedTour.ts:~590-627](../frontend/app/composables/useGuidedTour.ts#L590)).
- `addSystemMessage` silencieusement dropped si pas de conversation active ([useChat.ts:739-744](../frontend/app/composables/useChat.ts#L739)) — fallback toast à prévoir.
- Strings FR hardcodées non extraites en MAP de constantes — nuit à une future i18n.

### 3.4 SSE, chat & résilience

**Story 7-3** (résilience SSE) :
- Classification HTTP par substring français `'erreur lors de'` ([useChat.ts:70](../frontend/app/composables/useChat.ts#L70)) — tout nouveau message en anglais ou reformulé tombe dans `'other'`. Refactor en `class HttpError extends Error` ou flag typed recommandé.
- `throw new Error('Réponse sans body...')` classifie en `'other'` et pollue `error.value` même pendant un parcours guidé ([useChat.ts:264, 659](../frontend/app/composables/useChat.ts#L264)).
- `DOMException` non-Abort mid-stream (`NetworkError`, `InvalidStateError`) classifié en `'other'` ([useChat.ts:62-72](../frontend/app/composables/useChat.ts#L62)) — readers modernes throw `TypeError`, impact <1% (Safari legacy).
- `useUiStore()` appelé dans le catch block ([useChat.ts:504, 776](../frontend/app/composables/useChat.ts#L504)) — risque Pinia-not-ready dans contextes edge.
- Test invariant AC8 fragile au cwd : `path.resolve(process.cwd(), 'app/composables/useGuidedTour.ts')` — robustesse via `new URL(..., import.meta.url)`.
- bfcache : listeners survivent mais `isConnected` stale au `pageshow` ([useChat.ts:77-85](../frontend/app/composables/useChat.ts#L77)) — handler `pageshow` à ajouter.
- Fetches concurrents (`sendMessage` + `submitInteractiveAnswer`) : si l'un succeed (flip true) puis l'autre fail en network (flip false), le signal de reprise est écrasé.

### 3.5 Tests E2E

**Story 8-1** (parcours Fatou) :
- Imports `../../../app/types/carbon` sans path alias dans [mock-backend.ts:666](../frontend/tests/e2e/fixtures/mock-backend.ts#L666) — refactoring alias Vitest/Playwright à faire globalement.
- `testMatch` : un `.test.ts` sous `tests/e2e/` serait skip par Vitest ET ignoré par Playwright. Documenter la convention dans `tests/e2e/README.md`.
- Pas de header `X-Accel-Buffering: no` sur la réponse SSE fabriquée ([sse-stream.ts:581](../frontend/tests/e2e/fixtures/sse-stream.ts#L581)) — inutile tant que la réponse est single-shot, à ajouter si streaming chunked.
- `route.continue()` sur méthodes non-POST dans plusieurs endpoints mockés ([mock-backend.ts:772, 1007, 1028, 1065](../frontend/tests/e2e/fixtures/mock-backend.ts#L772)) — laisse passer vers un backend inexistant, catch-all 404 couvre. À harmoniser.

**Story 8-3** (parcours Aminata — E2E live shell) :
- Sémantique exacte de `agent-browser close` (sans `--session`) : dépend de la doc upstream CLI 0.8.5 ; `cleanup()` actuel swallow la sortie ([8-3-parcours-aminata.sh:1175, 1264](../frontend/tests/e2e-live/8-3-parcours-aminata.sh#L1175)).
- Driver.js popover i18n : textes FR + fallback EN hardcoded (Suivant/Next, Terminer/Done/Fermer). Pas de couverture pour ES/DE.
- Flag `--session aminata-e2e` absent des invocations `agent-browser` (var d'env `AGENT_BROWSER_SESSION` utilisée à la place). Décision du 2026-04-16 : « la simulation marche, on laisse comme ça pour le moment ». À reprendre si collisions de session en 8.4/8.5/8.6.

---

## 4. Résolu récemment (2026-04-14 / 15)

Trois bugs majeurs ont été résolus et sont documentés en détail dans la source canonique :

1. **[2026-04-15] SSE event `guided_tour` silencieusement droppé par la whitelist de `send_message`** — fix 1 ligne dans [chat.py:865-868](../backend/app/api/chat.py#L865) ajoutant `"guided_tour"` à la whitelist. Test anti-régression statique : `backend/tests/test_api/test_sse_event_whitelist.py`.
   - **Dette résiduelle** : `profile_update` et `profile_completion` également émis par `stream_graph_events` mais absents de la même whitelist ; non investigué — vérifier si cassé depuis la migration tool-calling (feature 012) ou si fonctionne via une autre voie.
2. **[2026-04-15] LLM hallucine « trigger_guided_tour temporairement inaccessible »** — `GUIDED_TOUR_TOOLS` était binde côté LLM dans 6 nœuds mais absent de la liste `tools=` passée à `create_tool_loop` dans [graph.py:132-138](../backend/app/graph/graph.py#L132). Fix 3-volets : ajout aux `create_tool_loop`, durcissement du `SUMMARY_PROMPT` (interdiction de « outil indisponible »), neutralisation des summaries legacy dans `_format_memory_section`. 9 `conversations.summary` contaminés nettoyés en base.
3. **[2026-04-14] `carbon_node` retourne « Aucun bilan » alors qu'un bilan existe** — le `get_carbon_summary` n'interrogeait que les bilans `in_progress`. Ajout de `get_latest_assessment()` + fallback sur `completed`. 4 tests ajoutés.
   - **Dette d'observabilité associée** : les tools métier (carbon, esg, etc.) n'instrumentent pas `log_tool_call` ; seuls `interactive_tools` et `guided_tour_tools` le font. À traiter séparément.

---

## 5. Prochaines étapes suggérées

1. **Traiter BUG-1** (placeholders vides) en priorité : décision routing vs injection de résumé dans le prompt.
2. **Story dédiée : migration composables → `apiFetch`** pour unifier la gestion 401 (7 composables concernés).
3. **Story dédiée : observabilité tool calling** — instrumenter tous les tools métier avec `log_tool_call`, et prévoir un dashboard minimal sur `tool_call_logs`.
4. **Story dédiée : multi-user guidance stats** — migrer `esg_mefali_guidance_stats` vers un scope par user (à coupler avec l'introduction des rôles admin/collaborateur/lecteur du module 7).
5. **Clean-up défensif** : ajouter `profile_update` et `profile_completion` à la whitelist SSE, normaliser `Date.now()` → `performance.now()` dans `useGuidedTour`, déplacer les strings FR en MAP module-level.
6. **Test de contrat cross-stack** : aligner les 6 `tour_id` entre `guided_tour.py` (prompt), `registry.ts` (frontend), `guided_tour_tools.py` (enum backend).

> Pour chaque item, se référer à [deferred-work.md](../_bmad-output/implementation-artifacts/deferred-work.md) pour la formulation d'origine et le contexte de review complet.
