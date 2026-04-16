# Arbre des sources annoté — ESG Mefali

Vue d'ensemble des dossiers critiques du monorepo `esg_mefali`. Les dossiers non essentiels (`node_modules/`, `venv/`, `.nuxt/`, `dist/`, `build/`, `__pycache__/`, `coverage/`, `playwright-report/`, `test-results/`) sont omis.

## Racine du monorepo

```
esg_mefali/
├── README.md                       # Quickstart Docker + commandes make
├── CLAUDE.md                       # Instructions Claude Code (conventions projet, conventions dark mode, réutilisation, contexte métier)
├── Makefile                        # make dev / build / migrate / test / down / logs / clean
├── docker-compose.yml              # Dev : 3 services (postgres pgvector, backend, frontend)
├── docker-compose.prod.yml         # Prod : services liés à 127.0.0.1, intégration nginx UAfricas
├── deploy.sh                       # Script d'orchestration VPS (setup / deploy / ssl / backup / restore)
├── .env.example                    # Variables d'environnement de référence
├── note.md                         # Notes libres (non canoniques)
├── frontend/                       # 🟢 Partie 1 — Nuxt 4 (voir arborescence détaillée plus bas)
├── backend/                        # 🟣 Partie 2 — FastAPI (voir arborescence détaillée plus bas)
├── nginx/                          # Template vhost pour nginx UAfricas (esg-mefali-vhost.conf.example)
├── scripts/                        # Scripts utilitaires ponctuels
├── specs/                          # 19 spec-kits (001 → 018 + 019 piloté via _bmad-output)
│   ├── 001-technical-foundation/
│   ├── 002-chat-rich-visuals/
│   ├── …
│   └── 018-interactive-chat-widgets/
├── _bmad/                          # Configuration BMM (BMad Method) : config.yaml + sous-dossiers phases
│   └── bmm/
│       ├── 1-analysis/
│       ├── 2-plan-workflows/
│       ├── 3-solutioning/
│       └── 4-implementation/
├── _bmad-output/                   # Artefacts générés : planning-artifacts/ + implementation-artifacts/
├── docs/                           # 📘 Sortie de cette documentation (index.md + fichiers spécialisés)
└── documents_et_brouillons/        # Brouillons métier (non versionnés au code)
```

**Points d'entrée principaux** :
- Frontend : [frontend/nuxt.config.ts](../frontend/nuxt.config.ts), [frontend/app/app.vue](../frontend/app/app.vue)
- Backend : [backend/app/main.py](../backend/app/main.py)
- Orchestration : [Makefile](../Makefile), [docker-compose.yml](../docker-compose.yml)

---

## Partie 1 — Frontend Nuxt 4 (`frontend/`)

```
frontend/
├── nuxt.config.ts                  # Config Nuxt : modules Pinia, runtimeConfig (apiBase), assets CSS
├── package.json                    # Nuxt ^4.4.2 + Vue 3 + Pinia 3 + TailwindCSS 4 + driver.js 1.4 + Chart.js + Mermaid + GSAP
├── tsconfig.json                   # strict: true, alias ~ → app/
├── vitest.config.ts                # Tests unitaires (happy-dom, setupFiles tests/setup.ts)
├── playwright.config.ts            # E2E (chromium, workers=1, port 4321, reducedMotion=reduce)
├── Dockerfile + Dockerfile.prod
│
├── app/                            # 🔹 Tous les fichiers sources Nuxt 4 sous app/
│   ├── app.vue                     # Racine
│   ├── layouts/
│   │   └── default.vue             # Header + sidebar + main + widget chat flottant (spec 019)
│   ├── pages/                      # 17 pages (routing automatique)
│   │   ├── index.vue               # Accueil/dashboard
│   │   ├── login.vue, register.vue # Auth (publique)
│   │   ├── dashboard.vue           # Tableau de bord agrégé (ESG/carbon/crédit/financements)
│   │   ├── profile.vue             # Profil entreprise
│   │   ├── documents.vue           # Liste + upload documents
│   │   ├── esg/
│   │   │   ├── index.vue           # Questionnaire ESG conversationnel
│   │   │   └── results.vue         # Résultats + recommandations (tour guidé : show_esg_results)
│   │   ├── carbon/
│   │   │   ├── index.vue           # Bilan carbone
│   │   │   └── results.vue         # Dashboard émissions + plan de réduction
│   │   ├── financing/
│   │   │   ├── index.vue           # Catalogue fonds (GCF, FEM, BOAD…)
│   │   │   └── [id].vue            # Fiche fonds + matching + intermédiaires
│   │   ├── credit-score/
│   │   │   └── index.vue           # Score crédit vert alternatif
│   │   ├── applications/
│   │   │   ├── index.vue           # Dossiers de financement
│   │   │   └── [id].vue            # Rédaction dossier
│   │   ├── action-plan/
│   │   │   └── index.vue           # Feuille de route 6/12/24 mois + rappels + badges
│   │   └── reports/
│   │       └── index.vue           # Rapports ESG PDF
│   ├── components/                 # 60 composants (groupement par domaine)
│   │   ├── copilot/                # Widget chat flottant (spec 019)
│   │   │   ├── FloatingChatWidget.vue
│   │   │   ├── FloatingChatButton.vue
│   │   │   ├── ChatWidgetHeader.vue
│   │   │   ├── ConnectionStatusBadge.vue
│   │   │   └── GuidedTourPopover.vue     # Popover custom driver.js (spec 5-4)
│   │   ├── chat/                   # Messages + widgets interactifs (spec 018)
│   │   │   ├── ChatMessage.vue
│   │   │   ├── ChatInput.vue
│   │   │   ├── ConversationList.vue
│   │   │   ├── WelcomeMessage.vue
│   │   │   ├── MessageParser.vue
│   │   │   ├── ToolCallIndicator.vue
│   │   │   ├── InteractiveQuestionHost.vue
│   │   │   ├── SingleChoiceWidget.vue
│   │   │   ├── MultipleChoiceWidget.vue
│   │   │   ├── JustificationField.vue
│   │   │   └── AnswerElsewhereButton.vue
│   │   ├── richblocks/             # Visualisations SSE inline (8)
│   │   │   ├── ChartBlock.vue
│   │   │   ├── MermaidBlock.vue
│   │   │   ├── GaugeBlock.vue
│   │   │   ├── ProgressBlock.vue
│   │   │   ├── TableBlock.vue
│   │   │   ├── TimelineBlock.vue
│   │   │   ├── BlockError.vue
│   │   │   └── BlockPlaceholder.vue
│   │   ├── esg/                    # Score ESG, critères, historique, recommandations
│   │   ├── carbon/                 # Dashboard carbon (indirectement sous credit/)
│   │   ├── credit/                 # ScoreGauge, FactorsRadar, DataCoverage, CertificateButton
│   │   ├── financing/              # Cartes fonds, matching
│   │   ├── applications/           # Éditeur dossier
│   │   ├── action-plan/            # Timeline, ActionCard, ReminderForm, BadgeGrid
│   │   ├── dashboard/              # ScoreCard, FinancingCard, ActivityFeed, NextActions
│   │   ├── documents/              # List, Upload, Preview, Detail
│   │   ├── profile/                # ProfileForm, ProfileField, ProfileProgress
│   │   ├── layout/                 # AppHeader, AppSidebar
│   │   └── ui/                     # ToastNotification, FullscreenModal
│   ├── composables/                # 18 composables (dont 3 à state module-level)
│   │   ├── useAuth.ts              # Login/refresh/401 + single-flight refreshPromise (spec 7-2)
│   │   ├── useChat.ts              # SSE streaming + widgets interactifs (module-level state, spec 019)
│   │   ├── useGuidedTour.ts        # Machine à états tours guidés driver.js (spec 5-6)
│   │   ├── useDeviceDetection.ts   # Détection mobile/desktop
│   │   ├── useDriverLoader.ts      # Lazy-load driver.js (ADR7)
│   │   ├── useMessageParser.ts     # Parse markdown + richblocks
│   │   ├── useFocusTrap.ts         # Accessibilité clavier
│   │   ├── useToast.ts             # Notifications in-app
│   │   ├── useCompanyProfile.ts, useDocuments.ts, useReports.ts, useApplications.ts,
│   │   │   useCreditScore.ts, useActionPlan.ts, useCarbon.ts, useDashboard.ts,
│   │   │   useEsg.ts, useFinancing.ts  # API wrappers par domaine
│   ├── stores/                     # 11 stores Pinia
│   │   ├── auth.ts                 # user, accessToken, refreshToken + persistance localStorage
│   │   ├── ui.ts                   # theme, sidebarOpen, chatWidgetOpen/Minimized, currentPage, guidedTourActive, prefersReducedMotion
│   │   ├── company.ts, documents.ts, esg.ts, carbon.ts, financing.ts, creditScore.ts,
│   │   │   actionPlan.ts, applications.ts, dashboard.ts
│   ├── types/                      # 12 fichiers (.ts)
│   │   ├── guided-tour.ts          # GuidedTourDefinition, GuidedTourStep, TourState, TourContext
│   │   ├── interactive-question.ts # InteractiveQuestion*, InteractiveQuestionAnswer, 4 variantes qcu/qcm/*justification
│   │   ├── richblocks.ts           # Types des blocs streamés (chart/gauge/timeline/…)
│   │   └── company.ts, documents.ts, esg.ts, carbon.ts, financing.ts, actionPlan.ts, dashboard.ts, report.ts, index.ts
│   ├── middleware/                 # 2 middlewares globaux
│   │   ├── auth.global.ts          # Redirection si non connecté (sauf /login, /register)
│   │   └── chat-redirect.global.ts # Ancien /chat → / avec ?openChat=1 (spec 019)
│   ├── plugins/                    # 3 plugins côté client
│   │   ├── gsap.client.ts          # Animations (rétraction widget chat)
│   │   ├── mermaid.client.ts       # Rendu diagrammes
│   │   └── chartjs.client.ts       # Chart.js register
│   ├── lib/
│   │   └── guided-tours/
│   │       ├── registry.ts         # 6 tours (show_esg_results, show_carbon_results, …)
│   │       └── definitions/        # Définitions par tour
│   └── assets/
│       └── css/
│           └── main.css            # @import tailwindcss + driver.js + @theme (variables dark mode)
│
└── tests/
    ├── setup.ts                    # Setup Vitest global
    ├── components/                 # Tests composants (Vue Test Utils)
    ├── composables/                # Tests composables (useChat, useGuidedTour, useAuth…)
    ├── stores/                     # Tests stores Pinia
    ├── pages/                      # Tests pages
    ├── middleware/                 # Tests middlewares (auth, chat-redirect)
    ├── lib/                        # Tests guided-tours registry
    ├── layouts/                    # Tests default.vue
    ├── e2e/                        # Playwright specs
    │   ├── 8-1-parcours-fatou.spec.ts        # Parcours utilisateur ESG complet
    │   ├── 8-2-parcours-moussa.spec.ts       # Parcours carbone + financement
    │   └── fixtures/                         # mock-backend.ts, sse-stream.ts, users.ts, auth.ts
    └── e2e-live/                   # Tests E2E live (shell scripts)
        ├── 8-3-parcours-aminata.sh           # Parcours Aminata sur stack live (pas de mock)
        ├── lib/                              # assertions.sh, env.sh, login.sh
        └── screenshots/
```

**Points d'entrée & composants critiques** :
- Racine Vue : [frontend/app/app.vue](../frontend/app/app.vue)
- Layout principal : [frontend/app/layouts/default.vue](../frontend/app/layouts/default.vue)
- Widget chat flottant : [frontend/app/components/copilot/FloatingChatWidget.vue](../frontend/app/components/copilot/FloatingChatWidget.vue)
- Machine à états chat + SSE : [frontend/app/composables/useChat.ts](../frontend/app/composables/useChat.ts)
- Machine à états tours guidés : [frontend/app/composables/useGuidedTour.ts](../frontend/app/composables/useGuidedTour.ts)
- Gestion auth + refresh single-flight : [frontend/app/composables/useAuth.ts](../frontend/app/composables/useAuth.ts)

---

## Partie 2 — Backend FastAPI (`backend/`)

```
backend/
├── requirements.txt                # FastAPI 0.115 + SQLAlchemy 2 async + asyncpg + LangGraph 0.2 + LangChain 0.3
│                                   # + pgvector + python-jose + bcrypt + WeasyPrint + PyMuPDF + pytesseract + docx2txt
├── requirements-dev.txt            # pytest 8 + pytest-asyncio + pytest-cov + ruff
├── pytest.ini                      # asyncio_mode=auto, testpaths=tests
├── alembic.ini                     # Config migrations
├── Dockerfile + Dockerfile.prod
│
├── alembic/
│   ├── env.py                      # Hooks Alembic (async engine)
│   ├── script.py.mako
│   └── versions/                   # 13 migrations
│       ├── 001_create_users.py
│       ├── f9b659a2b8e6_créer_les_tables_conversations_et_…
│       ├── 163318558259_add_documents_tables.py
│       ├── 2b24b1676e59_add_company_profiles_table_…
│       ├── 005_add_esg_assessments.py
│       ├── 006_add_reports_table.py
│       ├── 007_add_carbon_tables.py
│       ├── 008_add_financing_tables.py
│       ├── 73d72f6ebd8f_add_fund_applications_table.py
│       ├── 68cd43ef0091_add_credit_score_tables.py
│       ├── 5b7f090f1dcc_add_action_plan_dashboard_tables.py
│       ├── 54432e29b7f3_add_tool_call_logs_table.py       # Spec 012 (tool calling)
│       └── 018_create_interactive_questions.py            # Spec 018 (widgets interactifs)
│
├── app/
│   ├── main.py                     # App FastAPI, lifespan (compile graph), CORS, inclusion 13 routers
│   ├── core/
│   │   ├── config.py               # Settings Pydantic (SECRET_KEY, DATABASE_URL, OPENROUTER_*)
│   │   ├── security.py             # hash_password, create_access_token, create_refresh_token, decode_token
│   │   ├── database.py             # AsyncSession + engine asyncpg
│   │   ├── deps.py                 # get_current_user (JWT dep)
│   │   └── geolocation.py          # Détection pays via IP (50+ pays supportés)
│   ├── api/                        # Routers transversaux (auth, chat, health)
│   │   ├── auth.py                 # /api/auth : register, login, refresh, me, detect-country
│   │   ├── chat.py                 # /api/chat : conversations CRUD + messages + SSE + interactive-questions
│   │   └── health.py               # /api/health
│   ├── modules/                    # 10 modules métier (routeur + logique + templates)
│   │   ├── company/router.py       # /api/company : profile, completion
│   │   ├── documents/router.py     # /api/documents : upload, list, detail, reanalyze, preview
│   │   ├── esg/router.py           # /api/esg : assessments, score, benchmarks
│   │   ├── carbon/router.py        # /api/carbon : assessments, entries, summary, benchmarks
│   │   ├── financing/router.py     # /api/financing : funds, intermediaries, matches
│   │   ├── applications/router.py  # /api/applications : CRUD + generate-section + export
│   │   ├── credit/router.py        # /api/credit : score, breakdown, history, certificate
│   │   ├── reports/router.py       # /api/reports : generate (ESG PDF), status, download
│   │   ├── action_plan/router.py   # /api/action-plan : generate, items, reminders
│   │   └── dashboard/router.py     # /api/dashboard : summary agrégé
│   ├── schemas/                    # Schemas Pydantic v2
│   │   ├── auth.py                 # RegisterRequest, LoginRequest, TokenResponse, UserResponse
│   │   ├── chat.py                 # ConversationCreate/Response, MessageCreate/Response
│   │   └── interactive_question.py # InteractiveQuestion* (spec 018)
│   ├── models/                     # ORM SQLAlchemy (22 classes, 9 fichiers)
│   │   ├── user.py                 # User
│   │   ├── company.py              # CompanyProfile
│   │   ├── conversation.py         # Conversation (thread_id LangGraph)
│   │   ├── message.py              # Message (role, content, metadata)
│   │   ├── document.py             # Document, DocumentAnalysis, DocumentChunk (embedding pgvector)
│   │   ├── esg.py                  # ESGAssessment (criteria/scores JSONB)
│   │   ├── carbon.py               # CarbonAssessment, CarbonEmissionEntry
│   │   ├── credit.py               # CreditScore, CreditDataPoint
│   │   ├── financing.py            # Fund, Intermediary, FundMatch, FundIntermediary, FinancingChunk
│   │   ├── application.py          # FundApplication (sections JSONB)
│   │   ├── action_plan.py          # ActionPlan, ActionItem, Reminder, Badge
│   │   ├── report.py               # Report
│   │   ├── interactive_question.py # InteractiveQuestion (spec 018)
│   │   └── tool_call_log.py        # ToolCallLog (observability spec 012)
│   ├── graph/                      # 🧠 Orchestration LangGraph
│   │   ├── state.py                # ConversationState (TypedDict) : messages, active_module, active_module_data (spec 013), guidance_stats (spec 019)
│   │   ├── graph.py                # Assemble StateGraph + compile
│   │   ├── nodes.py                # 9 nœuds : router, chat, esg_scoring, carbon, financing, application, credit, action_plan, document
│   │   └── tools/                  # 12 fichiers, ~36 tools LangChain
│   │       ├── common.py           # log_tool_call, get_db_and_user helpers
│   │       ├── profiling_tools.py  # 2 tools (update_user_profile, extract_profiling_data)
│   │       ├── chat_tools.py       # 4 tools (mémoire, recherche docs, conversations passées)
│   │       ├── document_tools.py   # 3 tools (analyze, fetch_chunks, search_chunks)
│   │       ├── esg_tools.py        # 5 tools (dont batch_save_esg_criteria — spec 015)
│   │       ├── carbon_tools.py     # 4 tools
│   │       ├── financing_tools.py  # 4 tools
│   │       ├── application_tools.py# 6 tools (dont create_fund_application — spec 015)
│   │       ├── credit_tools.py     # 3 tools
│   │       ├── action_plan_tools.py# 3 tools
│   │       ├── interactive_tools.py# 1 tool (ask_interactive_question — spec 018)
│   │       └── guided_tour_tools.py# 1 tool (trigger_guided_tour — spec 019)
│   ├── prompts/                    # 11 modules
│   │   ├── system.py               # BASE_PROMPT + STYLE_INSTRUCTION (spec 014) + WIDGET_INSTRUCTION (spec 018) + GUIDED_TOUR_INSTRUCTION (spec 019)
│   │   ├── esg_scoring.py, carbon.py, financing.py, application.py, credit.py,
│   │   │   action_plan.py, esg_report.py, guided_tour.py, widget.py
│   ├── chains/                     # Chaînes LangChain dédiées (hors graphe principal)
│   │   ├── analysis.py, extraction.py, summarization.py
│   └── services/                   # (à compléter — certaines logiques inline dans routers ou nodes)
│
├── tests/                          # ~50 fichiers de tests
│   ├── conftest.py                 # Fixtures : in-memory SQLite, AsyncClient, db_session
│   ├── test_api/                   # auth, chat
│   ├── test_applications/, test_action_plan/, test_credit/, test_dashboard/
│   ├── test_graph/                 # nodes, routing
│   ├── test_tools/                 # chaque tool, persistance
│   ├── test_prompts/               # rendu prompts
│   ├── test_interactive_question_*.py  # Spec 018
│   ├── test_router_coverage.py     # Audit couverture endpoints
│   └── …
│
├── scripts/                        # Seeds, utilitaires CLI
└── uploads/                        # Stockage local fichiers (dev) — volume Docker en prod
```

**Points d'entrée & composants critiques** :
- App FastAPI : [backend/app/main.py](../backend/app/main.py)
- Graph LangGraph : [backend/app/graph/graph.py](../backend/app/graph/graph.py), [backend/app/graph/nodes.py](../backend/app/graph/nodes.py)
- État conversationnel : [backend/app/graph/state.py](../backend/app/graph/state.py)
- Auth + security : [backend/app/core/security.py](../backend/app/core/security.py), [backend/app/api/auth.py](../backend/app/api/auth.py)
- Streaming SSE : [backend/app/api/chat.py](../backend/app/api/chat.py)

---

## Intersection des deux parties

Le frontend et le backend communiquent exclusivement via HTTP (REST + SSE) + multipart upload :

| Flux | Source | Cible | Protocole |
|---|---|---|---|
| CRUD + fetch | `frontend/app/composables/use*.ts` | `backend/app/api/*` + `backend/app/modules/*/router.py` | REST JSON |
| Streaming LLM | `frontend/app/composables/useChat.ts` | `backend/app/api/chat.py` → `backend/app/graph/` | SSE `text/event-stream` |
| Tours guidés (trigger) | SSE `guided_tour` event consommé par `useGuidedTour.ts` | Émis par tool `trigger_guided_tour` | Marker SSE `<!--SSE:…-->` |
| Widgets interactifs | SSE `interactive_question` event consommé par `InteractiveQuestionHost.vue` | Émis par tool `ask_interactive_question` | Marker SSE + persistance `interactive_questions` |
| Contexte page courante | `formData.append('current_page', uiStore.currentPage)` | `backend/app/graph/state.py#current_page` | Champ form injecté dans prompts (spec 3) |
| Upload | `frontend/app/composables/useDocuments.ts` | `backend/app/modules/documents/router.py` | multipart/form-data |

Voir [integration-architecture.md](./integration-architecture.md) pour le détail des formats et événements SSE.

## Dossiers volumineux omis (pour référence)

- `frontend/node_modules/`, `frontend/.nuxt/`, `frontend/coverage/`, `frontend/playwright-report/`, `frontend/test-results/`
- `backend/venv/`, `backend/uploads/`, `backend/**/__pycache__/`
- `_bmad-output/` (artefacts générés, régénérés par les workflows BMM)
- `documents_et_brouillons/` (brouillons métier hors code)
