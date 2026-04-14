# Deferred Work

## Deferred from: code review of story-7-2 (2026-04-14)

- `refreshPromise` module-level dans `useAuth.ts` risque de partage entre requetes SSR — composable client-only en pratique mais pas de guard `import.meta.client` explicite. [frontend/app/composables/useAuth.ts:49]
- `useCarbon.fetchBenchmark` et `useEsg.fetchBenchmark` avalent toutes les erreurs non-session-expirée et retournent `null` — UI ne peut pas distinguer 404 vs 500. Comportement pre-existant, a traiter globalement. [frontend/app/composables/useCarbon.ts:93-98, useEsg.ts:90-96]
- Tests manquants : cycle 401 sur `apiFetchBlob` (fiche de preparation PDF), `/auth/me` (fetchUser), echec d'import dynamique dans `handleAuthFailure`. Scenarios principaux couverts par les 19 tests existants. [frontend/tests/composables/useAuth.refresh.test.ts]
- Composables non migres vers `apiFetch` (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`) ne beneficient pas de l'intercepteur 401. Dette technique deja documentee dans la story, future story `X-Y-migration-composables-vers-apifetch` proposee.

## Deferred from: code review of story-3-1 (2026-04-13)

- Pas d'annotation reducer pour `current_page` dans ConversationState — le champ pourrait ne pas se propager si un noeud LangGraph retourne un state partiel. Risque latent pour Story 3.2 quand les noeuds liront activement cette valeur. [backend/app/graph/state.py:36]
- `invoke_graph` n'accepte pas `current_page` — inconsistance latente avec `stream_graph_events`. Verifier si cette fonction est encore utilisee et la mettre a jour ou la supprimer. [backend/app/api/chat.py:56]

## Deferred from: code review of story-3-2 (2026-04-13)

- Checkpointer LangGraph et `current_page` — aucun nœud ne retourne `current_page` dans son `return {}`, risque théorique d'écrasement par le checkpoint. Risque quasi nul car toujours re-injecté dans `initial_state` et read-only. [backend/app/graph/nodes.py]
- `send_message_json` passe toujours `current_page=None` — endpoint de compatibilité, pas utilisé par le frontend actuel. Ajouter le support ou documenter la limitation. [backend/app/api/chat.py:938]
- Routes dynamiques (`/financing/123`) tombent sur la branche générique du prompt — nécessite un design de prefix matching pour extraire les descriptions contextuelles des pages avec paramètres. [backend/app/prompts/system.py:138]
- Valeur initiale `"/"` dans `uiStore.currentPage` envoyée au backend comme page inconnue — initialiser à `null` ou ajouter `"/"` à `PAGE_DESCRIPTIONS`. [frontend/app/stores/ui.ts:17]
- Tests ne couvrent pas le chemin complet nœud → prompt pour 5 des 6 spécialistes (carbon, financing, application, credit, action_plan) — couverture indirecte via tests prompts directs. [backend/tests/test_graph/test_current_page.py]

## Deferred from: code review of story-4-1 (2026-04-13)

- Pas de `timeout` sur `requestIdleCallback` dans `prefetchDriverJs()` — sous charge CPU le prefetch peut ne jamais se declencher avant le premier guidage. Le fallback `loadDriver()` gere ce cas mais avec latence supplementaire. [frontend/app/composables/useDriverLoader.ts:25]
- Couleurs hexadecimales hardcodees en mode clair dans les overrides Driver.js CSS — incohérence avec le dark mode qui utilise des variables CSS du design system. Pattern pre-existant dans le projet. [frontend/app/assets/css/main.css]

## Deferred from: code review of story-4-2 (2026-04-13)

- `countdown` sans borne min/max — accepte 0, négatif, NaN. Ajouter validation dans le moteur `useGuidedTour` (Story 5.1). [frontend/app/types/guided-tour.ts]
- `lib/` pas dans les dirs auto-import Nuxt — import manuel requis. Choix d'architecture, documenter si nécessaire. [frontend/nuxt.config.ts]
- `tsconfig.json` étend `.nuxt/tsconfig.json` — tests TypeScript cassent avant `nuxt prepare` en clone frais. Setup pré-existant. [frontend/tsconfig.json]
- `route` field non contraint dans `GuidedTourStep` — un typo de route échoue silencieusement au runtime. Validation croisée à ajouter dans Story 5.1. [frontend/app/types/guided-tour.ts]
- `TourContext = Record<string, unknown>` sans contrat entre les placeholders attendus et le contexte fourni — risque d'affichage de `{{variable}}` brut si clé manquante. Design d'interpolation à prévoir dans Story 5.1. [frontend/app/types/guided-tour.ts]

## Deferred from: code review of story-4-3 (2026-04-13)

- Route mismatch `show_esg_results` : registre declare `route: '/esg'` mais `esg-score-circle` est sur `/esg/results`. Corriger dans `registry.ts:22` la route en `/esg/results`. [frontend/app/lib/guided-tours/registry.ts:22]
- 8 elements `data-guide-target` dans des blocs `v-if` (esg-strengths-badges, esg-recommendations, carbon-donut-chart, carbon-benchmark, carbon-reduction-plan, action-plan-timeline, credit-score-gauge, dashboard cards pendant loading). Le moteur `useGuidedTour` (Story 5.1) devra gerer les elements absents du DOM via skip, attente ou fallback. [multiple pages]

## Deferred from: code review of story-5-1 (2026-04-13)

- Delai transition `complete → idle` hardcode a 1000ms — AC5 mentionne un delai configurable. Exposer une constante ou un parametre optionnel dans `startTour`. [frontend/app/composables/useGuidedTour.ts:162-166]
- Element DOM peut etre supprime entre le retour de `waitForElement` et l'appel `highlight` — fenetre de timing tres courte. Limitation architecturale, impact negligeable en conditions normales. [frontend/app/composables/useGuidedTour.ts:112-124]

## Deferred from: code review of story-6-1 (2026-04-13)

- Pas d'allowlist serveur pour `tour_id` — AC4 delegue explicitement la validation au registre frontend (par conception du spec). Hardening defense-en-profondeur possible plus tard. [backend/app/graph/tools/guided_tour_tools.py]
- `context` dict sans limite de taille/profondeur — un LLM pourrait envoyer un context enorme. Pre-existant aux autres tools qui acceptent des dicts LLM-controlled. [backend/app/graph/tools/guided_tour_tools.py:24]
- Marker SSE split entre chunks de streaming — parser actuel dans `stream_graph_events` suppose un `on_tool_end` avec output complet. Limitation partagee avec les markers `__sse_profile__` et `__sse_interactive_question__`. [backend/app/api/chat.py:212-239]
- Plusieurs markers SSE dans un seul output ne sont pas tous parses — `index()` ne trouve que le premier `-->`, les markers suivants sont ignores. Pre-existant. [backend/app/api/chat.py:213-217]

## Deferred from: code review of story-6-2 (2026-04-13)

- Couplage STYLE_INSTRUCTION / GUIDED_TOUR_INSTRUCTION : meme branche conditionnelle `_has_minimum_profile` dans `build_system_prompt`. Un futur changement de seuil du style concis deplacera silencieusement le guidage. Extraire un helper dedie ou ajouter un test d'independance. [backend/app/prompts/system.py:211-217]
- Aucune assertion positionnelle sur l'ordre `WIDGET_INSTRUCTION` → `GUIDED_TOUR_INSTRUCTION` dans les 5 prompts specialises — les tests verifient la presence (`in`) mais pas l'ordre. Un swap futur ne declencherait aucune erreur. [backend/tests/test_prompts/test_guided_tour_instruction.py]
- Chemins frontend listes dans la docstring `GUIDED_TOUR_INSTRUCTION` (`/esg/results`, `/action-plan`, etc.) non epingles contre le registre Nuxt reel (`frontend/app/lib/guided-tours/registry.ts`). Divergence silencieuse possible (cosmetique, le tool_call utilise le `tour_id` qui lui est valide). Test cross-stack a creer. [backend/app/prompts/guided_tour.py:12-17]

## Deferred from: code review of story-6-3 (2026-04-14)

- T-AC2 / T-AC6 court-circuitent `useGuidedTour` via mock statique — le test ne valide pas que `handleGuidedTourEvent` emprunte le code path runtime reel. Couverture d'integration plus realiste a prevoir en epic 8 (e2e). [frontend/tests/composables/useChat.guided-tour-consent.test.ts]
- Plancher `count("GUIDED_TOUR_TOOLS") >= 12` dans T11 conflate shape et correctness. Un refactor legitime (liste partagee, spread) casse le test. Herite 6.2. [backend/tests/test_prompts/test_guided_tour_instruction.py]
- T-AC3 (refus consent) ne prouve pas le respect du refus — test passe car backend n'emet pas `guided_tour`, pas parce que `no` est honore. Si le backend emettait a tort un guided_tour apres refus, le frontend n'a pas de guard `yes`-only. Test d'alignement backend/frontend a ajouter (hors scope prompt-only). [frontend/tests/composables/useChat.guided-tour-consent.test.ts]
- `GUIDED_TOUR_INSTRUCTION` injecte inconditionnellement (y compris pour sessions anonymes / sans profil) — bloat tokens par requete. Decision architecturale a valider globalement ou gated. [backend/app/prompts/system.py:213-220]
- Aucun test cross-file alignant les 6 `tour_id` entre `guided_tour.py` (prompt), `registry.ts` (frontend), `guided_tour_tools.py` (backend tool enum). Renommage silencieux possible. Test de contrat pour story 7.x ou 8.x. [multi-file]
- Validation serveur `tour_id` (tool-level) et validation `context` dans `handleGuidedTourEvent` — hors scope story 6.3 (story 6.1 pour le tool, `useChat.ts` NE PAS TOUCHER pour le handler). [backend/app/graph/tools/guided_tour_tools.py, frontend/app/composables/useChat.ts:682-700]

## Deferred from: code review of story 6-4-frequence-adaptative-des-propositions-de-guidage (2026-04-14)

- Decroissance / cap global sur `acceptance_count` et `refusal_count` — actuellement saturation indefinie apres ~5 acceptations (plancher 3s permanent). Decision produit a arbitrer : cap dur vs decay temporel. [frontend/app/composables/useGuidedTour.ts]
- `send_message_json` (endpoint fallback JSON) ne transmet pas `guidance_stats` au graphe — volontaire par spec ; acceptable car le fallback est hors-parcours principal. Extension Chrome / integrations externes (story 8.x) devront explicitement opter pour la modulation. [backend/app/api/chat.py:~976]
- Perte de precision au-dela de `Number.MAX_SAFE_INTEGER` dans `loadGuidanceStats` — limite JS native ; mitigable par plafond serveur (cf. patch P8 meme review). [frontend/app/composables/useGuidedTour.ts]
- Race theorique entre `currentInteractiveQuestion` lu avant `await import(...)` et evenement SSE `interactive_question_resolved` concurrent — fenetre temporelle minime, impact pratique negligeable. [frontend/app/composables/useChat.ts]
- SSE `guided_tour` arrivant pendant une question interactive `pending` laisse un etat orphelin (refus deja comptabilise sur la question precedente, acceptance non comptabilisee sur le tour). Path early-return existant avec message systeme ; edge rare. [frontend/app/composables/useChat.ts:~730-733]
- `test_guided_tour_instruction_unchanged` verifie seulement une plage de longueur (3500-6000 chars) — ne constitue pas un vrai verrou anti-regression semantique. A renforcer avec snapshot au prochain refactor 6.2. [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:~894-903]
- `try { ... } catch {}` silencieux autour de l'import dynamique + increment dans `useChat.ts` — swallow des erreurs non-critiques mais sans observabilite. A envisager dans story tooling/observability. [frontend/app/composables/useChat.ts:464-466]
- Migration de la cle localStorage `esg_mefali_guidance_stats` vers un scope par utilisateur (prefixe `user_id:` ou deplacement backend `user_guidance_stats`). Status quo accepte pour story 6.4. A revisiter au demarrage du module 7 (multi-utilisateurs admin/collaborateur/lecteur). Ajouter un TODO inline en meme temps que les patchs 6.4. [frontend/app/composables/useGuidedTour.ts]

## Deferred from: code review of story 7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement (2026-04-14)

- `Date.now()` non-monotone dans `waitForElementExtended` — une bascule NTP/DST peut fausser le calcul d'elapsedMs. Preferer `performance.now()` pour les mesures de duree. [frontend/app/composables/useGuidedTour.ts:179,183,189]
- `setTimeout(..., 500)` dans `interruptTour`/`cancelTour` (transition `interrupted`→`idle`) jamais annule — leak mineur de timers sur cancels repetes. [frontend/app/composables/useGuidedTour.ts:250-252,662-666]
- `cancelled` non reinitialise sur le chemin de succes de `startTour` — etat residuel possible entre deux parcours consecutifs sans cancel entre les deux. [frontend/app/composables/useGuidedTour.ts:278]
- `cancelTour` re-entre pendant la transition `interrupted`→`idle` cree des timeouts dupliques — ajouter `'interrupted'` a la garde de retour anticipe. [frontend/app/composables/useGuidedTour.ts:~635]
- Cleanup du catch global a placer dans un `finally` au lieu d'apres le catch — robustesse face a un throw interne au catch (ex. import dynamique qui throw lui-meme). [frontend/app/composables/useGuidedTour.ts:~590-627]
- `addSystemMessage` peut etre silencieusement drop si aucune conversation active cote `useChat` — limitation pre-existante ; AC4 suppose que l'utilisateur voit toujours le message empathique. A renforcer avec un fallback toast si pas de conversation active. [frontend/app/composables/useGuidedTour.ts:598-600, frontend/app/composables/useChat.ts:739-744]
- Strings FR hardcodees ("Je n'ai pas pu pointer cet element...", "La page met trop de temps a charger...", "Le guidage a rencontre un probleme...") non extraites en MAP de constantes module-level — conforme aux conventions actuelles du projet mais nuit a une future i18n ou a un edit global. [frontend/app/composables/useGuidedTour.ts:424,504,~418,~509,~600]

## Deferred from: code review of story 7-3-resilience-sse-et-indicateur-de-reconnexion (2026-04-14)

- Classification HTTP par substring francais `'erreur lors de'` : tous les throws actuels matchent mais tout nouveau message en englais ou reformule tombe dans `'other'`. Refactor en sentinel `class HttpError extends Error` ou en drapeau typed recommande a terme. [frontend/app/composables/useChat.ts:70]
- `throw new Error('Réponse sans body...')` classifie en `'other'` et pollue `error.value` meme pendant un parcours guide. Scenario rare (200 OK sans body). AC3 autorise explicitement ce comportement pour non-network, mais incoherent avec l'intention de masquer les erreurs reseau pendant un tour. [frontend/app/composables/useChat.ts:264, 659]
- `DOMException` non-Abort mid-stream (`NetworkError`, `InvalidStateError`) classifie en `'other'`. Readers modernes throw `TypeError` donc impact < 1 % du trafic (Safari legacy). Documente en spec Dev Notes. [frontend/app/composables/useChat.ts:62-72]
- `useUiStore()` appele dans le catch block — risque Pinia-not-ready dans contextes edge. Impossible dans flow UI reel. Refactor optionnel : hoister en haut de `useChat()`. [frontend/app/composables/useChat.ts:504, 776]
- Test invariant AC8 fragile au cwd : `path.resolve(process.cwd(), 'app/composables/useGuidedTour.ts')` fonctionne si vitest lance depuis `frontend/`. Robustesse : `new URL(..., import.meta.url)`. [frontend/tests/composables/useChat.connection.test.ts:831-838]
- bfcache : listeners survivent mais `isConnected` stale au `pageshow`. Edge case rare (page cachee offline puis restauree online sans event). Handler `pageshow` a ajouter a terme. [frontend/app/composables/useChat.ts:77-85]
- Fetches concurrents (`sendMessage` + `submitInteractiveAnswer`) : si l'un succeed et flip a true puis l'autre fail en network, la bascule a false ecrase le signal de reprise. Peu probable dans l'UX normale (serialisation par `abortController`). [frontend/app/composables/useChat.ts:289, 683, 503, 775]
