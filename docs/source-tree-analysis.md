# Arbre des sources annoté — ESG Mefali

Vue d'ensemble des dossiers critiques du monorepo `esg_mefali`. Les dossiers non essentiels (`node_modules/`, `venv/`, `.nuxt/`, `dist/`, `build/`, `__pycache__/`) sont omis.

```
esg_mefali/
├── README.md                       # Quickstart Docker + commandes make
├── CLAUDE.md                       # Instructions Claude Code (conventions projet)
├── Makefile                        # make dev / build / migrate / test / down / logs / clean
├── docker-compose.yml              # Dev : 3 services (postgres, backend, frontend)
├── docker-compose.prod.yml         # Production
├── deploy.sh                       # Script de déploiement (20 Ko)
├── .env.example                    # Variables d'environnement documentées
├── .env                            # Secrets locaux (git-ignored)
├── .gitignore
├── note.md                         # Notes internes
│
├── _bmad/                          # Configuration BMad Method v6.3
│   └── bmm/
│       └── config.yaml             # project_name, communication_language, docs path
├── _bmad-output/                   # Artefacts BMad (planning / implementation)
│
├── _bmad-output/                   # Alias (sortie BMad)
│
├── .specify/                       # Spec-kit (speckit) — templates et mémoire
│   ├── memory/constitution.md
│   └── templates/                  # spec / plan / tasks / checklist / constitution
│
├── .claude/                        # Config Claude Code local
│   ├── commands/                   # Commandes speckit.*
│   └── skills/                     # Skills speckit.*
│
├── specs/                          # 18 features spec-driven (001 → 018)
│   ├── 001-technical-foundation/
│   ├── 002-chat-rich-visuals/
│   ├── 003-company-profiling-memory/
│   ├── 004-document-upload-analysis/
│   ├── 005-esg-scoring-assessment/
│   ├── 006-esg-pdf-reports/
│   ├── 007-carbon-footprint-calculator/
│   ├── 008-green-financing-matching/
│   ├── 009-fund-application-generator/
│   ├── 010-green-credit-scoring/
│   ├── 011-dashboard-action-plan/
│   ├── 012-langgraph-tool-calling/
│   ├── 013-fix-multiturn-routing-timeline/
│   ├── 014-concise-chat-style/
│   ├── 015-fix-toolcall-esg-timeout/
│   ├── 016-fix-tool-persistence-bugs/
│   ├── 017-fix-failing-tests/
│   └── 018-interactive-chat-widgets/ # feature en cours
│
├── docs/                           # ◄── Documentation projet générée (ce dossier)
│
├── documents_et_brouillons/        # Brouillons, brainstorming, docs sources
│
├── nginx/                          # Configuration reverse proxy production
│
├── scripts/
│   └── init-test-db.sql            # Init SQLite/Postgres de test
│
├── backend/                        # ──────────── PART: BACKEND (FastAPI) ────────────
│   ├── Dockerfile                  # Image dev
│   ├── Dockerfile.prod             # Image prod (multistage)
│   ├── pytest.ini                  # asyncio_mode=auto, testpaths=tests
│   ├── requirements.txt            # Dépendances runtime (FastAPI, LangGraph, WeasyPrint, …)
│   ├── requirements-dev.txt        # Dépendances dev/test (pytest, ruff, black, mypy, …)
│   ├── alembic.ini                 # Config Alembic
│   ├── alembic/
│   │   ├── env.py                  # Environnement de migration async
│   │   └── versions/               # 13 migrations (001 → 018)
│   ├── uploads/                    # Fichiers utilisateurs (git-ignored)
│   ├── venv/                       # Environnement virtuel Python (git-ignored)
│   ├── app/
│   │   ├── main.py                 # Entrée FastAPI, lifespan LangGraph, CORS, routers
│   │   ├── api/                    # Routers directs (chat + auth + health + deps)
│   │   │   ├── auth.py             # POST /register, /login, /refresh, GET /me, /detect-country
│   │   │   ├── chat.py             # Chat + SSE streaming + questions interactives
│   │   │   ├── health.py           # GET /health
│   │   │   └── deps.py             # Depends(get_current_user), get_db
│   │   ├── chains/                 # Chaînes LangChain (document analysis, RAG, extraction)
│   │   ├── core/
│   │   │   ├── config.py           # Settings Pydantic (DATABASE_URL, JWT, OpenRouter)
│   │   │   ├── database.py         # Engine async + session factory
│   │   │   ├── security.py         # JWT HS256 + bcrypt
│   │   │   └── geolocation.py      # Détection pays via IP + pays supportés
│   │   ├── graph/                  # ◄── Cœur LangGraph
│   │   │   ├── graph.py            # create_compiled_graph() : assemblage des nœuds
│   │   │   ├── nodes.py            # 9 nœuds spécialisés (router + 8 modules) ~58 Ko
│   │   │   ├── state.py            # ConversationState (TypedDict)
│   │   │   ├── checkpointer.py     # MemorySaver / Postgres checkpointer LangGraph
│   │   │   └── tools/              # 12 fichiers de tools LangChain (~100 fonctions)
│   │   │       ├── common.py       # Utils (log_tool_call, get_db_and_user, with_retry)
│   │   │       ├── profiling_tools.py
│   │   │       ├── esg_tools.py
│   │   │       ├── carbon_tools.py
│   │   │       ├── financing_tools.py
│   │   │       ├── application_tools.py
│   │   │       ├── credit_tools.py
│   │   │       ├── action_plan_tools.py
│   │   │       ├── document_tools.py
│   │   │       ├── chat_tools.py
│   │   │       └── interactive_tools.py
│   │   ├── models/                 # 16 modèles SQLAlchemy async (~1717 LOC)
│   │   │   ├── base.py             # Base, UUIDMixin, TimestampMixin
│   │   │   ├── user.py
│   │   │   ├── company.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py         # Document + DocumentAnalysis + DocumentChunk (pgvector)
│   │   │   ├── esg.py
│   │   │   ├── carbon.py
│   │   │   ├── financing.py        # Fund + Intermediary + FundMatch + chunks
│   │   │   ├── credit.py
│   │   │   ├── application.py
│   │   │   ├── action_plan.py      # ActionPlan + ActionItem + Reminder + Badge
│   │   │   ├── report.py
│   │   │   ├── tool_call_log.py
│   │   │   └── interactive_question.py
│   │   ├── modules/                # 10 modules métier (router + service + schemas + logique)
│   │   │   ├── company/
│   │   │   ├── documents/
│   │   │   ├── esg/                # + criteria.py, weights.py
│   │   │   ├── carbon/             # + benchmarks.py, emission_factors.py
│   │   │   ├── financing/          # + preparation_sheet.py, seed.py
│   │   │   ├── applications/       # + export.py, prep_sheet.py, simulation.py
│   │   │   ├── credit/             # + certificate.py
│   │   │   ├── action_plan/        # + badges.py
│   │   │   ├── reports/            # + charts.py
│   │   │   └── dashboard/
│   │   ├── nodes/                  # Placeholder (vide — nœuds réels dans graph/nodes.py)
│   │   ├── prompts/                # 9 prompts système modulaires
│   │   │   ├── system.py           # Prompt racine (expert ESG/finance durable)
│   │   │   ├── esg_scoring.py
│   │   │   ├── carbon.py
│   │   │   ├── financing.py
│   │   │   ├── credit.py
│   │   │   ├── action_plan.py
│   │   │   ├── application.py
│   │   │   ├── esg_report.py
│   │   │   └── widget.py           # Schémas widgets interactifs (qcu/qcm)
│   │   └── schemas/                # 9 fichiers Pydantic DTO
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── interactive_question.py
│   │       ├── esg_scoring.py
│   │       ├── carbon.py
│   │       ├── financing.py
│   │       ├── credit.py
│   │       ├── action_plan.py
│   │       └── system.py
│   └── tests/                      # ~935 tests (pytest asyncio)
│       ├── conftest.py             # Fixtures (client, db_session, override_auth, …)
│       ├── test_auth.py
│       ├── test_chat.py
│       ├── test_graph/             # Routing + intégration LangGraph
│       ├── test_tools/             # 15 fichiers (tests par tool)
│       ├── test_prompts/           # 13 fichiers
│       ├── test_esg_*.py           # 6 fichiers
│       ├── test_carbon_*.py        # 3 fichiers
│       ├── test_financing_*.py     # 4 fichiers
│       ├── test_credit/            # 4 fichiers
│       ├── test_applications/
│       ├── test_action_plan/
│       ├── test_dashboard/
│       ├── test_documents_*.py     # 6 fichiers
│       ├── test_reports_*.py       # 3 fichiers
│       └── test_*_coverage.py      # Couverture nœuds, routers, services
│
└── frontend/                       # ──────────── PART: FRONTEND (Nuxt 4) ────────────
    ├── Dockerfile
    ├── Dockerfile.prod
    ├── nuxt.config.ts              # compat 4, Pinia, Tailwind postcss, runtimeConfig.apiBase
    ├── tsconfig.json               # strict: true (hérite de .nuxt/tsconfig.json)
    ├── vitest.config.ts            # env node, tests/**/*.test.ts
    ├── package.json                # Nuxt 4.4, Vue 3, Pinia 3, Tailwind 4, Chart.js, GSAP, Mermaid
    ├── package-lock.json
    ├── node_modules/               # git-ignored
    ├── app/                        # ◄── Structure Nuxt 4 (tout le code source)
    │   ├── app.vue                 # Root component
    │   ├── assets/
    │   │   └── css/
    │   │       └── main.css        # Tailwind 4 + @theme + dark variant
    │   ├── layouts/
    │   │   └── default.vue         # Layout app (header + sidebar + main + chat panel)
    │   ├── middleware/
    │   │   └── auth.global.ts      # Guard global (JWT + redirect login)
    │   ├── plugins/
    │   │   ├── mermaid.client.ts
    │   │   ├── chartjs.client.ts
    │   │   └── gsap.client.ts
    │   ├── pages/                  # 18 pages (routing auto Nuxt)
    │   │   ├── index.vue           # Redirect → /dashboard
    │   │   ├── login.vue
    │   │   ├── register.vue
    │   │   ├── profile.vue
    │   │   ├── dashboard.vue
    │   │   ├── chat.vue
    │   │   ├── esg/
    │   │   │   ├── index.vue
    │   │   │   └── results.vue
    │   │   ├── carbon/
    │   │   │   ├── index.vue
    │   │   │   └── results.vue
    │   │   ├── financing/
    │   │   │   ├── index.vue
    │   │   │   └── [id].vue        # Route dynamique
    │   │   ├── credit-score/
    │   │   │   └── index.vue
    │   │   ├── action-plan/
    │   │   │   └── index.vue
    │   │   ├── applications/
    │   │   │   ├── index.vue
    │   │   │   └── [id].vue
    │   │   ├── documents.vue
    │   │   └── reports/
    │   │       └── index.vue
    │   ├── components/             # 56 composants Vue 3 par feature
    │   │   ├── ui/                 # 2 génériques (FullscreenModal, ToastNotification)
    │   │   ├── layout/             # 3 (AppHeader, AppSidebar, ChatPanel)
    │   │   ├── chat/               # 13 (messages + widgets interactifs feature 018)
    │   │   ├── richblocks/         # 8 (chart, mermaid, table, gauge, progress, timeline)
    │   │   ├── esg/                # 6
    │   │   ├── credit/             # 7
    │   │   ├── dashboard/          # 4
    │   │   ├── action-plan/        # 6
    │   │   ├── documents/          # 4
    │   │   └── profile/            # 3
    │   ├── composables/            # 14 composables (useAuth, useChat SSE, useEsg, …)
    │   ├── stores/                 # 11 stores Pinia (auth, ui, company, dashboard, …)
    │   ├── types/                  # 11 fichiers de types TypeScript
    │   └── utils/
    │       └── normalizeTimeline.ts
    └── tests/
        └── components/
            ├── MessageParser.test.ts
            └── TimelineBlock.test.ts
```

## Dossiers critiques par rôle

### Pour ajouter un endpoint REST
1. Créer/éditer `backend/app/modules/<module>/router.py`
2. Ajouter logique dans `service.py`, DTO dans `schemas.py`
3. Inclure le router dans `backend/app/main.py`
4. Créer migration Alembic si schéma : `backend/alembic/versions/`
5. Tests : `backend/tests/test_<module>_*.py`

### Pour ajouter un nœud LangGraph
1. Éditer `backend/app/graph/nodes.py` (nouvelle fonction `async def xxx_node(state)`)
2. Ajouter les tools associés dans `backend/app/graph/tools/xxx_tools.py`
3. Prompt système dans `backend/app/prompts/xxx.py`
4. Router dans `backend/app/graph/graph.py` (arête conditionnelle)
5. Tests : `backend/tests/test_graph/` + `backend/tests/test_tools/`

### Pour ajouter une page frontend
1. Créer `frontend/app/pages/<feature>/index.vue` (route auto)
2. Composants dédiés dans `frontend/app/components/<feature>/`
3. Composable `frontend/app/composables/use<Feature>.ts`
4. Store Pinia `frontend/app/stores/<feature>.ts`
5. Types `frontend/app/types/<feature>.ts`
6. Tests : `frontend/tests/components/<Feature>.test.ts`

### Points d'intégration frontend ↔ backend
- `frontend/app/composables/useAuth.ts` (wrapper `fetch` avec JWT)
- `frontend/app/composables/useChat.ts` (SSE, events typés)
- `backend/app/api/chat.py` + `backend/app/graph/` (émission SSE)
- Base URL configurable : `NUXT_PUBLIC_API_BASE` (défaut `http://localhost:8000/api`)
