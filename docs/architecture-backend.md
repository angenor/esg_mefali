# Architecture Backend — FastAPI + LangGraph

## 1. Résumé exécutif

Le backend est un **monolithe FastAPI asynchrone** orchestré par un **graphe LangGraph** à 9 nœuds spécialisés. Il expose ~73 endpoints REST (sous `/api`), avec streaming SSE pour le chat IA, persiste tout dans PostgreSQL 16 + pgvector, et délègue l'intelligence au modèle Claude Sonnet 4 via OpenRouter. Chaque module métier est découpé en `router / service / schemas / logique spécifique`, avec ses propres tools LangChain et prompts système.

## 2. Stack technologique

| Catégorie | Technologie | Version | Justification |
|---|---|---|---|
| Langage | Python | 3.12 | Typage moderne, pattern matching, perf asyncio |
| Framework HTTP | FastAPI | ≥0.115.0 | Async natif, Pydantic v2, OpenAPI auto, SSE simple |
| Serveur ASGI | Uvicorn (standard) | ≥0.34.0 | Production-ready, hot-reload en dev |
| ORM | SQLAlchemy async | ≥2.0.36 | `AsyncSession`, `select()` typé, compat Alembic |
| Driver BDD | asyncpg | ≥0.30.0 | Le plus rapide pour PostgreSQL async |
| Migrations | Alembic | ≥1.14.0 | Autogen schéma, 13 migrations au 2026-04-12 |
| Vecteurs | pgvector (`pgvector` Py) | ≥0.3.6 | RAG documents + fonds de financement |
| Validation | Pydantic v2 + pydantic-settings | ≥2.10 / ≥2.7 | DTO, settings par env |
| Auth | python-jose + bcrypt | ≥3.3 / ≥5.0 | JWT HS256 |
| LLM | langchain-core / langchain-openai / langgraph | ≥0.3 / ≥0.3 / ≥0.2 | Tool calling, streaming, checkpointer |
| PDF | WeasyPrint + Jinja2 + matplotlib | ≥62 / ≥3.1 / ≥3.9 | Rapports HTML→PDF, graphiques SVG |
| Docs | PyMuPDF, pytesseract, pdf2image, docx2txt, openpyxl | — | Extraction texte + OCR |
| Word | python-docx | ≥1.1 | Export dossiers de candidature |
| HTTP client | httpx | ≥0.28 | Tests + OpenRouter |

## 3. Architecture en couches

```
┌────────────────────────────────────────────────────────────┐
│  HTTP Layer — app/api/* + app/modules/*/router.py          │
│  FastAPI routers, Dependency Injection (deps.py)           │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│  Service Layer — app/modules/*/service.py                  │
│  Logique métier, orchestration, règles de scoring          │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│  Graph Layer — app/graph/                                  │
│  LangGraph : routing, tool calling, streaming              │
│  • graph.py   — création et compilation du graphe          │
│  • nodes.py   — 9 nœuds spécialisés                        │
│  • state.py   — ConversationState typée (TypedDict)        │
│  • tools/     — 12 fichiers de tools LangChain             │
│  • checkpointer.py — MemorySaver / Postgres checkpointer   │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│  Data Layer — app/models/ + app/core/database.py           │
│  SQLAlchemy async, AsyncSession, 16 modèles                │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector                                  │
└────────────────────────────────────────────────────────────┘
```

## 4. Point d'entrée — `app/main.py`

- Titre OpenAPI : `ESG Mefali API`, version issue de `settings.app_version`
- **Lifespan async** :
  - Startup : compile le graphe LangGraph (`create_compiled_graph`) si `OPENROUTER_API_KEY` est fournie
  - Warning dégradé si clé absente (API démarre sans IA)
  - Shutdown : libère la référence globale `compiled_graph`
- **CORS** : `http://localhost:3000` uniquement, credentials + all methods + all headers
- **Routers** (prefixe `/api`) : `auth`, `chat`, `company`, `documents`, `esg`, `reports`, `carbon`, `financing`, `applications`, `credit`, `dashboard`, `action-plan`, `health`

## 5. Structure du package `app/`

| Dossier | Rôle |
|---|---|
| `api/` | Routers FastAPI directs (`auth.py`, `chat.py`, `health.py`, `deps.py`) — le chat est ici (pas dans `modules/`) à cause de son couplage avec le graphe |
| `chains/` | Chaînes LangChain dédiées (extraction document, RAG spécifique) |
| `core/` | `config.py` (Settings Pydantic), `database.py` (engine/session factory async), `security.py` (JWT + bcrypt), `geolocation.py` (détection pays via IP) |
| `graph/` | `graph.py`, `nodes.py` (~58 ko), `state.py`, `checkpointer.py`, `tools/` |
| `graph/tools/` | 12 fichiers, ~100 tools LangChain par module métier |
| `models/` | 16 fichiers SQLAlchemy (~1717 LOC) + `base.py` (Mixins UUID + timestamps) |
| `modules/` | 10 sous-dossiers par module métier (`esg/`, `carbon/`, `financing/`, `applications/`, `credit/`, `action_plan/`, `company/`, `documents/`, `reports/`, `dashboard/`) |
| `nodes/` | Placeholder (nœuds réels dans `graph/nodes.py`) |
| `prompts/` | 9 prompts système modulaires + `widget.py` (schémas widgets interactifs) |
| `schemas/` | 9 fichiers Pydantic pour I/O REST |

## 6. Graphe LangGraph (`app/graph/`)

### 6.1 Nœuds (10)

1. **router_node** — Classification d'intent LLM + heuristiques regex pour détecter le module. Gère `active_module` dans `ConversationState` (continuation vs changement) — feature 013
2. **profiling_node** — Extrait info profil (CA, secteur, effectifs) via le tool `update_company_profile`
3. **document_node** — Analyse d'un PDF uploadé (extraction + embeddings + RAG)
4. **esg_scoring_node** — Évaluation ESG guidée, 30 critères, piliers E/S/G
5. **carbon_node** — Assessment carbone (scopes 1/2/3), facteurs d'émission, objectifs
6. **financing_node** — Matchmaking fonds + intermédiaires (RAG pgvector)
7. **application_node** — Génération sections de dossier de candidature
8. **credit_node** — Scoring crédit vert alternatif, certificat PDF
9. **action_plan_node** — Génération plan d'action (10-15 items catégorisés)
10. **chat_node** — Conversation générale / fallback, visualisations Markdown enrichies

Chaque nœud spécialiste peut invoquer ses tools via un `ToolNode` conditionnel (boucle max **5 itérations**, retry automatique 1× par tool). Les erreurs sont loggées dans `tool_call_logs`.

### 6.2 État partagé — `ConversationState`

TypedDict utilisé par LangGraph (resumé) :

- `messages: list[BaseMessage]` — historique typé LangChain
- `user_id: str`, `conversation_id: str`
- `active_module: str | None` — module "collant" pour les multi-tours (feature 013)
- `active_module_data: dict | None` — données de reprise
- `profile: CompanyProfile | None`
- `dashboard_summary: dict | None`
- Flags de streaming SSE

### 6.3 Streaming SSE

Le chat utilise `astream_events()` (LangGraph) et émet les événements SSE suivants :

- `token` : chunk texte de l'assistant
- `done` : fin de la réponse (avec `message_id` persisté)
- `document_upload`, `document_status`, `document_analysis` : progression upload
- `profile_update`, `profile_completion` : extraction champs profil
- `tool_call_start`, `tool_call_end`, `tool_call_error` : visualisation des tools
- `interactive_question`, `interactive_question_resolved` : widgets interactifs (feature 018)

Les payloads interactifs transitent via un marker `<!--SSE:{"__sse_interactive_question__":true,...}-->` détecté dans `stream_graph_events`.

## 7. Configuration — `app/core/config.py`

```python
class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/esg_mefali"

    secret_key: str = "changez-cette-cle-en-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480    # 8h
    refresh_token_expire_days: int = 30

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"

    # Alias de compatibilité LLM_*
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    app_version: str = "0.1.0"
    debug: bool = False
```

Fichier `.env` chargé depuis `../.env` ou `./.env`. La méthode `model_post_init` mappe les variables `LLM_*` (héritées) vers `OPENROUTER_*` pour rétro-compat.

## 8. Sécurité

- **JWT HS256** : `access_token` 8h, `refresh_token` 30j
- **Bcrypt** via `passlib` pour les mots de passe
- **CORS** restreint à `http://localhost:3000` (à élargir en prod via une var d'env dédiée)
- **Géolocalisation IP** dans `core/geolocation.py` (détection pays à l'inscription)
- **Dépendances FastAPI** : `Depends(get_current_user)` sur toutes les routes sauf `auth`, `health`

> ⚠️ `SECRET_KEY` par défaut est un placeholder. **Obligatoire** de le remplacer en production.

## 9. Pattern modulaire type

Chaque module dans `app/modules/<module>/` suit la même structure :

```
modules/<module>/
├── __init__.py
├── router.py       # FastAPI APIRouter + endpoints
├── schemas.py      # Pydantic DTO in/out
├── service.py      # Logique métier async, dépendances BDD
├── <domain>.py     # Règles spécifiques (ex: weights.py, emission_factors.py, badges.py)
└── export.py       # (optionnel) génération PDF/DOCX
```

Les **services** sont instanciés avec une `AsyncSession` passée en paramètre. Pas de singleton applicatif, pas de DI lourde — juste `Depends()` FastAPI.

## 10. Tests

- **Framework** : pytest + pytest-asyncio (`asyncio_mode=auto`)
- **BDD de test** : SQLite in-memory (configuré dans `scripts/init-test-db.sql` pour l'environnement Docker)
- **Fixtures** : `conftest.py` fournit `client`, `db_session`, `override_auth`, `make_conversation_state`
- **Volume** : ~935 tests, répartis en :
  - `test_tools/` — 15 fichiers
  - `test_prompts/` — 13 fichiers
  - `test_graph/` — 2 fichiers (routing, intégration)
  - `test_<module>/` ou `test_<module>_*.py` — 1 à 6 fichiers par module
  - `test_*_coverage.py` — tests complémentaires de couverture
- **Couverture cible** : 80 % (rule `common/testing.md`)
- **Lancement** :
  - Via Docker : `make test-back`
  - Direct : `source backend/venv/bin/activate && pytest tests/ -v --cov=app --cov-report=term-missing`

## 11. Migrations (Alembic)

13 migrations au 2026-04-12, dans `backend/alembic/versions/` :

| Migration (extrait) | Feature |
|---|---|
| `001_create_users.py` | Users, conversations, messages |
| `2b24b1676e59_...` | `CompanyProfile` + détection pays |
| `163318558259_...` | Documents + DocumentAnalysis + DocumentChunk (pgvector) |
| `005_add_esg_assessments.py` | `ESGAssessment` + critères |
| `006_add_reports_table.py` | Rapports PDF |
| `007_add_carbon_tables.py` | `CarbonAssessment` + entries |
| `008_add_financing_tables.py` | Fonds + intermédiaires + matchs + chunks RAG |
| `68cd43ef0091_...` | `CreditScore` + data points |
| `73d72f6ebd8f_...` | `FundApplication` |
| `5b7f090f1dcc_...` | Action plan + items + reminders + badges |
| `54432e29b7f3_...` | Tool call logs |
| `018_create_interactive_questions.py` | Questions interactives (widgets chat) |

Commande standard : `alembic upgrade head` (via `make migrate` dans Docker).

## 12. Intégration LLM — OpenRouter + Claude Sonnet 4

```python
# app/graph/nodes.py
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        request_timeout=60,   # feature 015 : timeout explicite
    )
```

- Modèle par défaut : `anthropic/claude-sonnet-4-20250514`
- Clé via `OPENROUTER_API_KEY` ou alias `LLM_API_KEY`
- Timeout HTTP explicite 60 s pour éviter les blocages (feature 015)
- Tous les nœuds instancient le LLM à la volée — pas de client partagé (cheap car SDK réutilise la session httpx interne)

## 13. Tools LangChain (12 fichiers dans `graph/tools/`)

| Fichier | Tools clés |
|---|---|
| `profiling_tools.py` | `update_company_profile`, `get_company_profile` |
| `esg_tools.py` | `create_esg_assessment`, `save_esg_criterion_score`, `batch_save_esg_criteria`, `finalize_esg_assessment`, `get_esg_assessment` |
| `carbon_tools.py` | `create_carbon_assessment`, `save_emission_entry`, `finalize_carbon_assessment`, `get_carbon_summary` |
| `financing_tools.py` | `search_compatible_funds`, `save_fund_interest`, `get_fund_details`, `create_fund_application` |
| `application_tools.py` | `create_fund_application`, `generate_application_section`, `update_application_section`, `get_application_checklist`, `simulate_financing`, `export_application` |
| `credit_tools.py` | `generate_credit_score`, `get_credit_score`, `generate_credit_certificate` |
| `action_plan_tools.py` | `generate_action_plan`, `update_action_item`, `get_action_plan` |
| `document_tools.py` | `analyze_uploaded_document`, `get_document_analysis`, `list_user_documents` |
| `chat_tools.py` | `get_user_dashboard_summary`, `get_company_profile_chat`, `get_esg_assessment_chat`, `get_carbon_summary_chat` |
| `interactive_tools.py` | `ask_interactive_question` (4 variantes : qcu / qcm / qcu_justification / qcm_justification) |
| `common.py` | Utilitaires : `log_tool_call`, `get_db_and_user`, `with_retry`, `_extract_tool_args` |

## 14. Risques et points d'attention

- **SECRET_KEY par défaut** non sécurisée — à impérativement surcharger en prod
- **CORS** en dur sur `localhost:3000` — à externaliser via env `CORS_ORIGINS`
- **venv Python 3.14** présent dans le repo — les rules projet demandent 3.12 ; à harmoniser
- **Timeout LLM** fixé à 60 s, le graphe autorise 5 itérations de tools → pire cas ~5 min ; surveiller en prod
- **CompanyProfile** potentiellement volumineux — pas de pagination côté chat
- **Compte exact d'endpoints** : ~73 (à reconfirmer à chaque ajout de feature)

## 15. Références croisées

- [Modèles de données](./data-models-backend.md)
- [Contrats d'API](./api-contracts-backend.md)
- [Architecture d'intégration](./integration-architecture.md)
- [Guide de développement](./development-guide.md)
