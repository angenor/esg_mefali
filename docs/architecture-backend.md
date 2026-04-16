# Architecture Backend — FastAPI + LangGraph

## 1. Résumé exécutif

API conversationnelle bâtie sur **FastAPI 0.115** entièrement asynchrone, avec **SQLAlchemy 2 async** / **asyncpg** sur **PostgreSQL 16 + pgvector**, et une couche d'orchestration LLM via **LangGraph 0.2** + **LangChain 0.3** consommant **Claude Sonnet 4** (via OpenRouter). Le cœur métier vit dans un graphe à 9 nœuds, enrichi par ~36 tools LangChain qui persistent l'état directement en BDD. 73 endpoints REST exposent les fonctions utilisateur et un endpoint SSE diffuse le stream conversationnel.

**Architecture** : modulaire par domaine métier (`app/modules/<domain>/`) avec routers dédiés, ORM centralisé (`app/models/`), schémas Pydantic v2 (`app/schemas/`), graphe LangGraph isolé dans `app/graph/`, et chaînes ponctuelles dans `app/chains/`.

## 2. Stack technique

| Catégorie | Techno | Version | Rôle |
|---|---|---|---|
| Web framework | FastAPI | `>=0.115.0` | Endpoints, DI, OpenAPI |
| ASGI server | Uvicorn | `>=0.34.0` | Exécution async |
| Langage | Python | 3.12 | Patterns async/await, type hints complets |
| ORM | SQLAlchemy | `2.0.36+` async | Modèles + requêtes |
| Driver PG | asyncpg | `>=0.30.0` | Connexion async |
| Migrations | Alembic | `>=1.14.0` | Schéma versionné |
| Vecteurs | pgvector | `>=0.3.6` | Embeddings documents + fonds |
| LLM core | LangChain | `>=0.3.0` | Messages, tools, prompts |
| LLM orchestration | LangGraph | `>=0.2.0` | StateGraph multi-nœuds |
| LLM OpenAI | langchain-openai | `>=0.3.0` | Wrapper compatible OpenRouter |
| Validation | Pydantic | `>=2.10.0` | Schémas + Pydantic Settings |
| Auth | python-jose + bcrypt | `3.3.0` / `5.0.0` | JWT HS256 + hash mot de passe |
| HTTP client | httpx | `>=0.28.0` | Appels externes async |
| PDF extraction | PyMuPDF | `>=1.24.0` | Extraction texte PDF |
| OCR | pytesseract + pdf2image | `>=0.3.10` / `>=1.17.0` | Fallback OCR |
| Docx | docx2txt + python-docx | `>=0.8` / `>=1.1.0` | Lecture + génération |
| Excel | openpyxl | `>=3.1.0` | XLSX |
| PDF output | WeasyPrint + Jinja2 | `>=62.0` / `>=3.1.0` | Rapports ESG |
| Charts | matplotlib | `>=3.9.0` | Graphiques PDF |
| Tests | pytest + pytest-asyncio + pytest-cov | `8`+ | Suite complète |
| Lint | ruff | `>=0.8.0` | Format + lint |

## 3. Architecture en couches

```
┌─────────────────────────────────────────────────────┐
│  app/main.py                                         │
│  - CORSMiddleware                                    │
│  - Lifespan : compile LangGraph graph                │
│  - include_router × 13                               │
└──────────────────────────┬──────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
┌─────────────┐   ┌────────────────┐   ┌────────────────┐
│ app/api/    │   │ app/modules/   │   │ app/api/       │
│ auth.py     │   │ <domain>/      │   │ chat.py        │
│ chat.py     │   │   router.py    │   │ (SSE endpoint) │
│ health.py   │   │   templates/   │   │                │
└──────┬──────┘   └────────┬───────┘   └────────┬───────┘
       │                   │                     │
       │                   │                     ▼
       │                   │          ┌───────────────────┐
       │                   │          │ app/graph/        │
       │                   │          │  graph.py         │
       │                   │          │  nodes.py (9)     │
       │                   │          │  state.py         │
       │                   │          │  tools/ (12, ~36) │
       │                   │          └───────────────────┘
       │                   │                     │
       ▼                   ▼                     ▼
┌──────────────────────────────────────────────────────┐
│ app/core/                                             │
│  config.py (Settings)  security.py  database.py      │
│  deps.py (get_current_user)  geolocation.py          │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│ app/models/ (22 classes, 14 fichiers)                │
│    ORM SQLAlchemy async + pgvector                   │
│    ←→ app/schemas/ (Pydantic v2)                     │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ PostgreSQL 16 +     │
                 │ pgvector (async)    │
                 └─────────────────────┘
```

## 4. Point d'entrée ([app/main.py](../backend/app/main.py))

- **FastAPI app** instanciée au module level.
- **Lifespan** asynchrone : à la startup, compile le graphe LangGraph si `OPENROUTER_API_KEY` est présente (stocké dans `compiled_graph` global) ; à l'arrêt, libère la ressource.
- **Middleware CORS** : origins `["http://localhost:3000"]` (à ouvrir). `allow_credentials=True`, méthodes/headers ouverts.
- **Includes** :

| Prefixe | Router | Endpoints |
|---|---|---|
| `/api/auth` | `api.auth` | 5 |
| `/api/chat` | `api.chat` | 9 |
| `/api/company` | `modules.company.router` | 3 |
| `/api/documents` | `modules.documents.router` | 6 |
| `/api/esg` | `modules.esg.router` | 6 |
| `/api/carbon` | `modules.carbon.router` | 6 |
| `/api/financing` | `modules.financing.router` | 10 |
| `/api/applications` | `modules.applications.router` | 9 |
| `/api/credit` | `modules.credit.router` | 5 |
| `/api/reports` | `modules.reports.router` | 3 + 1 listing |
| `/api/action-plan` | `modules.action_plan.router` | 6 |
| `/api/dashboard` | `modules.dashboard.router` | 1 |
| `/api/health` | `api.health` | 1 |

Total : **73 endpoints exposés**. Détail complet : [api-contracts-backend.md](./api-contracts-backend.md).

## 5. Organisation applicative (`app/`)

### `app/core/` — briques transverses

- [`config.py`](../backend/app/core/config.py) — `Settings(BaseSettings)` Pydantic. Variables : `DATABASE_URL`, `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`, `APP_VERSION`, `DEBUG`, `CORS_ORIGINS`, `UPLOAD_DIR`.
- [`security.py`](../backend/app/core/security.py) — `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`. Algorithme HS256, expirations via settings, request_timeout explicite sur `get_llm()` à 60 s (spec 015).
- [`database.py`](../backend/app/core/database.py) — `AsyncEngine` + `AsyncSession` factory + dépendance `get_db()`.
- [`deps.py`](../backend/app/core/deps.py) — dépendance FastAPI `get_current_user` qui décode le JWT et charge `User`.
- [`geolocation.py`](../backend/app/core/geolocation.py) — détection pays via header / GeoIP pour `POST /api/auth/register`. 50+ pays UEMOA/CEDEAO + international.

### `app/api/` — routers transverses

- [`auth.py`](../backend/app/api/auth.py) — signup, login, refresh, me, detect-country.
- [`chat.py`](../backend/app/api/chat.py) — CRUD conversations + messages + **SSE streaming** + gestion widgets interactifs (spec 018).
- [`health.py`](../backend/app/api/health.py) — `GET /api/health` : état FastAPI + test connexion BDD.

### `app/modules/<domain>/`

Chaque module métier regroupe `router.py`, souvent un `service.py` et/ou des `templates/` Jinja. 10 modules : `company`, `documents`, `esg`, `carbon`, `financing`, `applications`, `credit`, `reports`, `action_plan`, `dashboard`.

### `app/models/` — ORM (22 classes, 14 fichiers)

Détail complet : [data-models-backend.md](./data-models-backend.md). Highlights :

- Couche auth : `User`, `CompanyProfile`.
- Couche conversation : `Conversation` (avec `thread_id` LangGraph), `Message`, **`InteractiveQuestion` (spec 018)**, **`ToolCallLog` (spec 012)**.
- Couche documents : `Document`, `DocumentAnalysis`, `DocumentChunk` (embedding pgvector).
- Couche métier : `ESGAssessment`, `CarbonAssessment` + `CarbonEmissionEntry`, `CreditScore` + `CreditDataPoint`, `Fund`, `Intermediary`, `FundMatch`, `FundIntermediary`, `FinancingChunk` (embedding), `FundApplication`, `ActionPlan` + `ActionItem` + `Reminder` + `Badge`, `Report`.

### `app/schemas/` — Pydantic v2

Trois fichiers :
- [`auth.py`](../backend/app/schemas/auth.py) — `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenResponse`, `UserResponse`.
- [`chat.py`](../backend/app/schemas/chat.py) — `ConversationCreate/Response/Update`, `MessageCreate/Response`, `PaginatedResponse`.
- [`interactive_question.py`](../backend/app/schemas/interactive_question.py) — `InteractiveQuestionCreate`, `InteractiveQuestionResponse`, `InteractiveQuestionState`.

### `app/graph/` — orchestration LangGraph

Cœur du backend. Détail ci-dessous (section 6).

### `app/prompts/` — 11 modules de prompts

- [`system.py`](../backend/app/prompts/system.py) — `BASE_PROMPT` identitaire + helpers injectés conditionnellement :
  - `STYLE_INSTRUCTION` (spec 014) — consigne de concision.
  - `WIDGET_INSTRUCTION` (spec 018) — format d'émission des questions interactives.
  - `GUIDED_TOUR_INSTRUCTION` (spec 019) — critères pour déclencher un tour.
- Un fichier par module métier : `esg_scoring.py`, `carbon.py`, `financing.py`, `application.py`, `credit.py`, `action_plan.py`, `esg_report.py`, `guided_tour.py`, `widget.py`. Chaque prompt liste les outils disponibles, le rôle attendu, les règles absolues (format de réponse, tool calling obligatoire pour certains endpoints — durci spec 015).

### `app/chains/` — chaînes LangChain ponctuelles

- `analysis.py` — pipeline d'analyse de document après extraction.
- `extraction.py` — extraction structurée PDF/Docx.
- `summarization.py` — résumés de conversations précédentes (stockés dans `Conversation.previous_thread_summary`).

## 6. Orchestration LangGraph (`app/graph/`)

### `state.py` — `ConversationState` (TypedDict)

Champs :

```python
messages: Annotated[list, add_messages]        # Historique BaseMessage

# Profil utilisateur + mémoire
user_id: str | None
user_profile: dict | None
context_memory: list[str]
profile_updates: list[dict] | None
profiling_instructions: str | None

# Documents
document_upload: dict | None
document_analysis_summary: str | None
has_document: bool

# Sous-états par module + flags routage
esg_assessment: dict | None;   _route_esg: bool
carbon_data: dict | None;      _route_carbon: bool
financing_data: dict | None;   _route_financing: bool
application_data: dict | None; _route_application: bool
credit_data: dict | None;      _route_credit: bool
action_plan_data: dict | None; _route_action_plan: bool

# Routage multi-tour (spec 013)
active_module: str | None
active_module_data: dict | None

# Context adaptatif (spec 3)
current_page: str | None

# Tours guidés (spec 019)
guidance_stats: dict | None     # {refusal_count, acceptance_count}

# Boucle tools
tool_call_count: int
```

### `graph.py` — assemblage

1. Création du `StateGraph(ConversationState)`.
2. Ajout des 9 nœuds (`router`, `chat`, `document`, `esg_scoring`, `carbon`, `financing`, `application`, `credit`, `action_plan`).
3. Arêtes conditionnelles depuis `router_node` — routage vers le bon module selon `active_module` (si continuation) ou classification binaire LLM (si changement) — voir spec 013.
4. Chaque nœud spécialiste peut boucler avec un `ToolNode` jusqu'à 5 itérations.
5. `compile()` avec checkpointer optionnel (MemorySaver en dev, `langgraph-checkpoint-postgres` possible en prod).

### `nodes.py` — 9 nœuds

| Nœud | Rôle | Particularités |
|---|---|---|
| `router_node` | Classifie la requête en module actif (ou continuation) | Spec 013 : binaire continuation/changement, défaut sécuritaire = continuer dans `active_module` en cas d'erreur LLM |
| `chat_node` | Conversation générale + profilage | STYLE_INSTRUCTION conditionnelle (post-onboarding uniquement) |
| `document_node` | Analyse du document uploadé | Feed `chat_node` ensuite |
| `esg_scoring_node` | 30 critères E-S-G | Tool `batch_save_esg_criteria` pour éviter les timeouts (spec 015) |
| `carbon_node` | Bilan carbone + plan de réduction | Tools adaptés secteur Afrique |
| `financing_node` | Matching fonds + RAG pgvector | `FinancingChunk` embeddings |
| `application_node` | Rédaction dossier de financement | `create_fund_application` + `generate_section` (spec 015) |
| `credit_node` | Scoring crédit vert alternatif | Données Mobile Money + photos IA |
| `action_plan_node` | Feuille de route 6/12/24 mois | Blocs `timeline/table/mermaid/gauge/chart` |

Chaque nœud partage la même logique :

```python
1. Prompt = BASE + STYLE? + WIDGET + GUIDED_TOUR + <module>_PROMPT + contexte page
2. llm.bind_tools(TOOLS_MODULE + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS).invoke(messages)
3. Si ai_msg.tool_calls et tool_call_count < 5 :
     ToolNode(tools).invoke(state) → ré-entre le nœud (incrément compteur)
4. Sinon : émet l'AIMessage final
5. Gère activation / mise à jour / désactivation de active_module (spec 013)
```

### `tools/` — 12 fichiers, ~36 tools

| Fichier | Nombre | Tools majeurs |
|---|---|---|
| `common.py` | — | `log_tool_call()`, `get_db_and_user()` |
| `profiling_tools.py` | 2 | `update_user_profile`, `extract_profiling_data` |
| `chat_tools.py` | 4 | `save_conversation_summary`, `fetch_context_memory`, `search_documents`, `list_past_conversations` |
| `document_tools.py` | 3 | `analyze_uploaded_document`, `fetch_document_chunks`, `search_document_chunks` |
| `esg_tools.py` | 5 | `create_esg_assessment`, `save_esg_criterion_score`, `finalize_esg_assessment`, `get_esg_assessment`, **`batch_save_esg_criteria`** (spec 015) |
| `carbon_tools.py` | 4 | `create_carbon_assessment`, `save_carbon_entry`, `finalize_carbon_assessment`, `get_carbon_summary` (fix spec 019 : consulter aussi les bilans `completed`) |
| `financing_tools.py` | 4 | `search_funds`, `get_fund_details`, `list_intermediaries`, `create_fund_match` |
| `application_tools.py` | 6 | **`create_fund_application`** (spec 015), `generate_section`, `save_section`, `finalize_application`, `get_checklist`, `simulate_financing` |
| `credit_tools.py` | 3 | `compute_credit_score`, `save_credit_data_point`, `finalize_credit_score` |
| `action_plan_tools.py` | 3 | `create_action_plan`, `add_action_item`, `create_reminder` |
| `interactive_tools.py` | 1 | **`ask_interactive_question`** (spec 018) — 4 variantes |
| `guided_tour_tools.py` | 1 | **`trigger_guided_tour`** (spec 019) |

Chaque tool se termine par un `await log_tool_call(...)` pour tracer dans `tool_call_logs`.

### Streaming SSE

Endpoint : `POST /api/chat/conversations/{id}/messages` ([chat.py](../backend/app/api/chat.py)).

```python
async def _stream_chat(...):
    async for event in compiled_graph.astream_events(
        state, config={"configurable": {"thread_id": conversation.thread_id, ...}}
    ):
        # Mapping LangGraph event → SSE type (token, tool_call_start/end/error, ...)
        # Emission des markers <!--SSE:{}-->  embarqués dans les tokens pour interactive_question, guided_tour, profile_update
```

Retourne un `StreamingResponse(..., media_type="text/event-stream")`.

## 7. Authentification & sécurité

- **JWT HS256** via `python-jose`. Access token 60–480 min selon env, refresh 30 jours.
- **Hash** bcrypt. Aucun stockage en clair.
- **Middleware auth** via dépendance `get_current_user` sur chaque endpoint protégé.
- **CORS** codé en dur (à nettoyer).
- **Rate limiting** : ❌ absent. Voir [technical-debt-backlog.md](./technical-debt-backlog.md).
- **Injection SQL** : impossible grâce à SQLAlchemy ORM / prepared statements asyncpg.
- **Validation** : systématique via Pydantic v2 à l'entrée de chaque endpoint.

## 8. Accès aux données

- **pgvector** pour les embeddings (`DocumentChunk.embedding`, `FinancingChunk.embedding`).
- **Requêtes similarité** : `<->` (cosine distance) dans les services documents et financing (RAG).
- **Indices** : pas d'index HNSW déclaré — à ajouter si le volume explose.
- **Migrations** : 13 fichiers Alembic dans [backend/alembic/versions/](../backend/alembic/versions/). Voir [data-models-backend.md](./data-models-backend.md#migrations-alembic).

## 9. Intégrations externes

| Service | Rôle | Config |
|---|---|---|
| OpenRouter | Inférence LLM (Claude Sonnet 4) | `OPENROUTER_*` env |
| Filesystem local | Stockage documents + PDF générés | `UPLOAD_DIR` (`backend/uploads/` en dev, volume Docker en prod) |

## 10. Tests

- **pytest 8** + **pytest-asyncio** (autouse).
- [pytest.ini](../backend/pytest.ini) : `asyncio_mode = auto`, `testpaths = tests`.
- **Conftest** : fixtures `setup_db` (SQLite in-memory par défaut, PostgreSQL via `TEST_DATABASE_URL` optionnel), `client` (AsyncClient FastAPI), `db_session`.
- **Découpage** : `test_api/`, `test_applications/`, `test_action_plan/`, `test_credit/`, `test_dashboard/`, `test_graph/`, `test_tools/`, `test_prompts/`, test_interactive_question_*, test_router_coverage.py, test_system_prompt.py, etc.
- **Volume** : ~50 fichiers, cible ~935 assertions (CLAUDE.md).

## 11. Observabilité

- **Logs** : module `logging` Python standard, pas de structuration JSON.
- **Audit tool calls** : table `tool_call_logs` indexée (cf. [data-models-backend.md](./data-models-backend.md#toolcalllog)).
- **Métriques / traces** : absents. Voir dette technique.

## 12. Compatibilité déploiement

- **Worker** : `uvicorn app.main:app --reload` en dev. En prod : `uvicorn` direct (pas de Gunicorn), port 8000 interne, lié à 127.0.0.1:8010 via Docker Compose prod.
- **Healthcheck** : `GET /api/health` consommé par nginx et `deploy.sh`.
- **Migrations au déploiement** : déclenchées manuellement via `./deploy.sh migrate`.

## 13. Décisions notables

| Décision | Ref | Justification |
|---|---|---|
| Tout asynchrone (FastAPI + SQLAlchemy async + asyncpg) | — | Cohabitation avec LangGraph streaming sans blocage thread |
| LangGraph au lieu de chaînes LangChain linéaires | spec 012 | État partagé, tool calling natif, checkpointing |
| Active module dans l'état (continuation/changement) | spec 013 | Conserve le contexte entre tours, évite la perte de focus sur ESG/carbon long-running |
| Widget instruction + Guided tour instruction dans le prompt | specs 018, 019 | Chaque nœud a la même UX cohérente, pas de duplication |
| batch_save_esg_criteria | spec 015 | Évite timeout de 30 appels séquentiels (une transaction) |
| Marker SSE HTML-commentaire | 018, 019 | Canal unique pour tokens + payloads structurés |
| Tool `trigger_guided_tour` côté backend | spec 019 | Le LLM décide quand proposer, mais le frontend garde le contrôle final (consentement via widget) |
| Route carbon consulte bilans `completed` via `get_carbon_summary` | fix 2026-04-15 | Permettre la consultation post-finalisation sans recréer l'assessment |

## 14. Limites et dette technique

- Rate limiting absent — à ajouter via `slowapi` ou au niveau nginx avant ouverture publique.
- CORS codé en dur — à rendre configurable via env `CORS_ORIGINS`.
- Aucun scheduler de rappels (table `reminders` populée mais pas consommée par un worker).
- Pas de worker d'analyse document (traitement fait dans la requête HTTP — risque de timeout sur gros fichiers).
- Embeddings pgvector sans index ANN — OK à < 100k docs, à réviser ensuite.
- Couverture de tests mesurable mais pas imposée en CI.
- Pas de métriques / traces.
- OpenRouter single provider — à abstraire pour permettre du fallback / multi-provider.

Voir [technical-debt-backlog.md](./technical-debt-backlog.md) pour le suivi priorisé.
