# Research: Intégration Tool Calling LangGraph

**Branch**: `012-langgraph-tool-calling` | **Date**: 2026-04-01

## R1: Architecture SSE actuelle vs Tool Calling

### Constat
Le chemin SSE (`generate_sse()` dans `api/chat.py`) **bypasse complètement** le graphe LangGraph compilé. Il appelle `llm.astream(messages)` directement via `stream_llm_tokens()`. Le `compiled_graph` existe mais n'est utilisé que par le fallback JSON (`invoke_graph()`).

### Décision
Réécrire le chemin SSE pour utiliser le graphe LangGraph avec `astream_events()` au lieu d'appeler le LLM directement. Cela permet de bénéficier nativement du tool calling via le graphe.

### Justification
- `astream_events()` de LangGraph émet des événements granulaires : `on_chat_model_stream` (tokens), `on_tool_start`, `on_tool_end`, ce qui mappe directement sur les événements SSE nécessaires.
- L'approche alternative (ajouter le tool calling en dehors du graphe dans `stream_llm_tokens()`) dupliquerait la logique de routing et les tools dans le code SSE, violant le principe DRY.
- Le graphe compilé est déjà créé au démarrage mais inutilisé — cette refonte le met en production.

### Alternatives rejetées
- **Ajouter une boucle tool call manuelle dans `stream_llm_tokens()`** : Duplication de la logique, maintenance double, pas de bénéfice du routing LangGraph.
- **Garder le SSE séparé et ajouter un webhook post-tool** : Trop complexe, latence supplémentaire.

---

## R2: Injection du user_id et de la session DB dans les tools

### Constat
Les services métier nécessitent `db: AsyncSession` et `user_id: UUID` comme premiers arguments. Les tools LangChain sont appelés par le LLM — celui-ci ne doit pas avoir à passer le `user_id`. De plus, `user_id` n'est pas déclaré dans le TypedDict `ConversationState`.

### Décision
Utiliser `RunnableConfig` de LangChain pour injecter `user_id` et `db` dans les tools via les métadonnées de configuration. Chaque tool accède à ces valeurs via `config["configurable"]["user_id"]` et `config["configurable"]["db"]`.

### Justification
- `RunnableConfig` est le mécanisme standard LangChain pour passer du contexte aux tools sans que le LLM le voie.
- L'alternative (variables globales, contextvars) est moins explicite et plus difficile à tester.
- Le `user_id` sera aussi ajouté au TypedDict `ConversationState` pour que les noeuds y accèdent de manière typée.

### Pattern de code
```python
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

@tool
async def update_company_profile(
    company_name: str | None = None,
    sector: str | None = None,
    # ... autres paramètres
    config: RunnableConfig = None,
) -> str:
    """Met à jour le profil entreprise avec les champs fournis."""
    user_id = config["configurable"]["user_id"]
    db = config["configurable"]["db"]
    # appel au service métier
    profile = await company_service.get_or_create_profile(db, user_id)
    # ...
```

### Alternatives rejetées
- **Passer user_id comme paramètre visible du tool** : Le LLM devrait connaître et passer l'UUID, source d'erreurs.
- **Utiliser `contextvars`** : Moins testable, risque de fuite entre requêtes concurrentes.

---

## R3: Gestion de la session DB dans le contexte LangGraph

### Constat
Les services utilisent `db: AsyncSession` injecté par FastAPI `Depends(get_db)` au niveau du router. Mais dans le contexte LangGraph + tool calling, les tools s'exécutent en dehors du scope FastAPI classique.

### Décision
Créer la session DB en amont dans le handler SSE et la passer via `RunnableConfig["configurable"]["db"]`. La session est commitée/rollbackée dans le handler SSE après l'exécution complète du graphe.

### Justification
- La session doit vivre le temps de toute la réponse (graphe + tools), pas par tool individuellement.
- Les tools qui appellent `db.flush()` (la majorité) fonctionnent dans cette transaction unique.
- Les rares services qui font `db.commit()` (action_plan) continueront de fonctionner car ils ont la session.

### Alternative rejetée
- **Créer une session par tool call** : Perte de la transactionalité, risque d'incohérence si un tool réussit et le suivant échoue.

---

## R4: Pattern d'exécution des tool calls dans les noeuds

### Constat
LangGraph avec LangChain >= 0.3.0 supporte le pattern "tool node" : un noeud dédié (`ToolNode`) qui exécute les tool calls automatiquement. Le flow est : noeud spécialiste (LLM avec tools bindés) → si tool_calls → ToolNode → retour au LLM.

### Décision
Utiliser le pattern `ToolNode` de LangGraph pour chaque noeud spécialiste. Le graphe aura des sous-graphes conditionnels : `specialist_node → should_continue → tool_node → specialist_node` (boucle jusqu'à réponse finale sans tool calls, max 5 itérations).

### Justification
- `ToolNode` est le pattern recommandé par LangGraph — il gère automatiquement l'exécution des tools et la construction des `ToolMessage`.
- La boucle conditionnelle permet au LLM de chaîner plusieurs tools (max 5 par tour, conforme à la spec).
- Le pattern est le même pour tous les noeuds, seuls les tools déclarés diffèrent.

### Alternatives rejetées
- **Exécution manuelle des tools dans chaque noeud** : Duplication, plus de code, plus de bugs.
- **Un seul ToolNode partagé avec tous les tools** : Le LLM verrait tous les tools de tous les modules, confusion possible et prompts trop longs.

---

## R5: Compatibilité OpenRouter avec Tool Calling

### Constat
Le projet utilise `ChatOpenAI` pointant vers OpenRouter (`https://openrouter.ai/api/v1`). Le modèle est `anthropic/claude-sonnet-4-20250514`.

### Décision
OpenRouter supporte le tool calling pour les modèles Claude via l'API OpenAI-compatible. `ChatOpenAI.bind_tools()` fonctionne nativement avec cette configuration. Aucune modification du client LLM nécessaire.

### Vérification requise
- Tester que `llm.bind_tools([tool1, tool2]).ainvoke(messages)` retourne bien des `tool_calls` via OpenRouter.
- Vérifier que `astream_events()` émet correctement les événements tool avec OpenRouter.

---

## R6: Streaming SSE avec tool calls — Nouveaux événements

### Constat actuel des événements SSE
Les événements existants sont : `token`, `done`, `document_upload`, `document_status`, `document_analysis`, `profile_update`, `profile_completion`, `report_suggestion`, `error`.

### Décision
Ajouter 3 nouveaux types d'événements SSE :

| Événement | Payload | Quand |
|-----------|---------|-------|
| `tool_call_start` | `{ tool_name, tool_args }` | Quand le LLM émet un tool call |
| `tool_call_end` | `{ tool_name, success, result_summary }` | Quand le tool a fini de s'exécuter |
| `tool_call_error` | `{ tool_name, error_message }` | Quand un tool échoue (après retry) |

### Justification
- Le frontend peut afficher un indicateur contextuel ("Sauvegarde du profil...", "Calcul du score ESG...") en utilisant `tool_name`.
- Le `result_summary` dans `tool_call_end` est une version courte du résultat (pas le résultat complet qui peut être volumineux).
- Conforme à FR-015 et FR-016 de la spec.

---

## R7: Refactoring du routing — Router hybride

### Constat
Le `router_node` actuel utilise des regex pour détecter l'intention et set des `_route_*` booleans. Avec le tool calling, le routing reste nécessaire pour diriger vers le bon noeud spécialiste (qui a les bons tools).

### Décision
Conserver le `router_node` regex existant pour le routing de premier niveau. Chaque noeud spécialiste gère ensuite ses propres tools. Le chat_node aura aussi des tools de lecture pour les questions factuelles.

### Justification
- Le routing LLM-based serait plus lent et plus coûteux (un appel LLM supplémentaire).
- Le regex actuel fonctionne bien pour les intentions principales.
- Le chat_node avec tools de lecture est le "filet de sécurité" pour les questions qui ne matchent pas les regex spécialistes.
