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
