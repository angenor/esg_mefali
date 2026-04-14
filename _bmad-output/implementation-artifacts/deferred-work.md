# Deferred Work

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
