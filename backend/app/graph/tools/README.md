# Tools LangChain — Guide d'utilisation

Ce package expose les **34 tools LangChain** consommés par les noeuds LangGraph
du conseiller ESG. Tous les tools sont **instrumentés** via `with_retry` +
`log_tool_call` (Story 9.7, FR-021 + FR-022 + NFR75).

## 1. Inventaire des 34 tools par module

| Module | `node_name` | Tools exposés |
|--------|-------------|---------------|
| `profiling_tools.py` | `profiling` | `update_company_profile`, `get_company_profile` |
| `esg_tools.py` | `esg_scoring` | `create_esg_assessment`, `save_esg_criterion_score`, `finalize_esg_assessment`, `get_esg_assessment`, `batch_save_esg_criteria` |
| `carbon_tools.py` | `carbon` | `create_carbon_assessment`, `save_emission_entry`, `finalize_carbon_assessment`, `get_carbon_summary` |
| `financing_tools.py` | `financing` | `search_compatible_funds`, `save_fund_interest`, `get_fund_details`, `create_fund_application` |
| `credit_tools.py` | `credit` | `generate_credit_score`, `get_credit_score`, `generate_credit_certificate` |
| `application_tools.py` | `application` | `submit_fund_application_draft`, `generate_application_section`, `update_application_section`, `get_application_checklist`, `simulate_financing`, `export_application` |
| `document_tools.py` | `document` | `analyze_uploaded_document`, `get_document_analysis`, `list_user_documents` |
| `action_plan_tools.py` | `action_plan` | `generate_action_plan`, `update_action_item`, `get_action_plan` |
| `chat_tools.py` | `chat` | `get_user_dashboard_summary`, `get_company_profile_chat`, `get_esg_assessment_chat`, `get_carbon_summary_chat` |
| `interactive_tools.py` | *dynamique* (actif module) | `ask_interactive_question` |
| `guided_tour_tools.py` | *dynamique* (actif module) | `trigger_guided_tour` |

Le registre agrégé est exposé par `app.graph.tools.INSTRUMENTED_TOOLS` —
liste consommée par `graph.py` pour brancher chaque `ToolNode`.

## 2. Pattern d'ajout d'un nouveau tool (4 étapes)

1. **Déclarer la fonction `@tool`** dans le module métier approprié
   (ou créer un nouveau module `xxx_tools.py` si le domaine est nouveau).
   Signature standard : `async def my_tool(arg1, arg2, config: RunnableConfig) -> str`.

2. **Wrapper avec `with_retry`** dans la liste du module :

   ```python
   from app.graph.tools.common import with_retry

   MY_MODULE_TOOLS = [
       with_retry(my_tool, max_retries=2, node_name="my_node"),
   ]
   ```

3. **Enregistrer dans `__init__.py`** :

   ```python
   from app.graph.tools.my_module_tools import MY_MODULE_TOOLS

   INSTRUMENTED_TOOLS: list = [
       # ... tools existants ...
       *MY_MODULE_TOOLS,
   ]
   ```

4. **Vérifier l'instrumentation** : le test `test_tools_instrumentation.py::test_no_tool_escapes_wrapping`
   détecte automatiquement les oublis. Lancer :
   ```bash
   pytest tests/test_graph/test_tools_instrumentation.py -v
   ```

## 3. Configuration par défaut + surcharge par module

`with_retry` applique les défauts suivants (alignés sur NFR75) :

| Paramètre | Défaut | Signification |
|-----------|--------|---------------|
| `max_retries` | `2` | 3 tentatives totales (1 essai + 2 retries) |
| `backoff` | `[1.0, 3.0, 9.0]` | Délais en secondes avant chaque retry |
| `node_name` | `""` | Nom du nœud LangGraph (fallback dynamique via `configurable.active_module`) |

### Surcharger pour un module spécifique

```python
# Backoff plus rapide pour un tool critique (ex. profiling lors de l'onboarding)
PROFILING_TOOLS = [
    with_retry(update_company_profile, max_retries=2, node_name="profiling",
               backoff=[0.5, 1.0, 2.0]),
]

# Désactiver le retry pour un tool déterministe (pas de réseau)
PURE_TOOLS = [
    with_retry(compute_score, max_retries=0, backoff=[], node_name="scoring"),
]
```

### Circuit breaker (NFR75)

Géré automatiquement par la classe `_CircuitBreakerState` :
- Seuil : **10 erreurs 5xx consécutives** sur la clé `(tool_name, node_name)`.
- Fenêtre : **60 secondes** avant la bascule half-open.
- Métriques : `logger.error(..., extra={"metric": "circuit_breaker_open", ...})`.

Pour reset l'état du breaker dans un test :
```python
from app.graph.tools.common import _reset_breaker_state_for_tests
_reset_breaker_state_for_tests()
```

## 4. Classification des exceptions

`is_transient_error(exc)` détermine si un retry est justifié :

| Transient (retry OK) | Non transient (pas de retry) |
|----------------------|------------------------------|
| `asyncio.TimeoutError`, `TimeoutError` | `ValueError`, `pydantic.ValidationError` |
| `ConnectionError` | `sqlalchemy.exc.IntegrityError` |
| `httpx.ConnectError`, `httpx.ReadTimeout` | `PermissionError`, `KeyError` |
| `asyncpg.PostgresConnectionError` | Tout reste non explicitement transient |
| `status_code ∈ {429, 500, 502, 503, 504}` | `status_code ∈ {400, 401, 403, 404, …}` |

Les **erreurs LLM 5xx** (`{500, 502, 503, 504}` + classes OpenAI/Anthropic
`APIError`, `InternalServerError`, `APIStatusError`) incrémentent en plus le
compteur du circuit breaker.

## 5. Journalisation : table `tool_call_logs`

Chaque invocation crée 1 à N lignes (1 succès ; 2 retry success ; 1 error ;
1 circuit_open) avec les 12 colonnes suivantes :

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Clé primaire |
| `user_id` | UUID | FK users.id |
| `conversation_id` | UUID | FK conversations.id (nullable) |
| `node_name` | str(100) | `"chat"`, `"esg_scoring"`, `"carbon"`, etc. |
| `tool_name` | str(100) | Nom `@tool` LangChain |
| `tool_args` | JSON | Args métier filtrés + `_input_size_bytes` |
| `tool_result` | JSON | `{"summary": str(result)[:500], "_output_size_bytes": N}` |
| `duration_ms` | int | Durée de la tentative |
| `status` | str(20) | `"success"`, `"retry_success"`, `"error"`, `"circuit_open"` |
| `error_message` | text | Message d'erreur tronqué à 500 chars (nullable) |
| `retry_count` | int | 0 pour la 1ère tentative, 1 pour le 1er retry, etc. |
| `created_at` | DateTime(tz) | ISO-8601 UTC |

### Limitation connue — transactions avortées (H2 post-review 9.7)

`log_tool_call` écrit dans la **même session SQLAlchemy** que le tool métier
(CCC-14, transaction boundaries). Si un tool lève en cours de transaction
(ex. un `INSERT` a déjà été flushé avant le crash), la session passe en
`PendingRollbackError` et la ligne de log ne peut plus être persistée. Dans
ce cas, `_safe_log` rattrape l'erreur et émet un `logger.warning` avec
`extra={"metric": "tool_log_persistence_failure", ...}` pour être
observable côté dashboard FR55. **Le log n'est pas garanti** sur ces cas
limites ; agréger `tool_log_persistence_failure` pour les détecter.

Contrainte additionnelle (CCC-14) : tout champ texte libre > 200 chars dans
`tool_args` est automatiquement tronqué. Ne jamais logger de secrets ou
PII non filtrés (blacklist actuelle : `config`, `db`, `self`).

## 6. Références

- `_bmad-output/planning-artifacts/architecture.md` §NFR75 — policy retry + circuit breaker.
- `_bmad-output/planning-artifacts/epics/epic-09.md` — Story 9.7 (source de vérité).
- `backend/app/graph/tools/common.py` — implémentation.
- `backend/app/models/tool_call_log.py` — schéma persistance.
- `specs/012-langgraph-tool-calling/spec.md` FR-021 / FR-022 — spécifications d'origine.
