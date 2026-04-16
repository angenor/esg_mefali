# Index de documentation — ESG Mefali

> **Point d'entrée principal** pour toute assistance IA (Claude Code, BMad Method, SpecKit) travaillant sur ce projet.
> **Généré le** : 2026-04-16 (Deep Scan)
> **Type** : monorepo avec 2 parties (Frontend Nuxt 4 + Backend FastAPI)

## Vue d'ensemble

- **Type** : monorepo (`frontend/` + `backend/`) déployé conjointement via Docker Compose
- **Architecture** : client-serveur, orchestration LLM côté serveur, streaming SSE unidirectionnel
- **Pattern** : modulaire par domaine métier (ESG, carbon, financing, applications, credit, action-plan, documents, dashboard, reports, profile)
- **Dernière refonte majeure** : spec 019 — chat refactoré en widget flottant omniprésent + tours guidés driver.js + résilience SSE

## Quick reference par partie

### 🟢 Frontend Nuxt 4 (`frontend/`)

| Dimension | Valeur |
|---|---|
| Framework | Nuxt 4.4 + Vue 3 Composition API |
| Langage | TypeScript 5 strict |
| State | Pinia 3 (11 stores) |
| Styling | TailwindCSS 4 + dark mode (`@theme`) |
| Animations | GSAP (widget chat) |
| Tours guidés | driver.js 1.4 (lazy-loaded) |
| Charts / Diagrams | Chart.js + Mermaid |
| Tests | Vitest 3 (unit) + Playwright 1.49 (E2E mocké) + bash (E2E live) |
| Pages | 17 |
| Composants | 60 |
| Composables | 18 (dont 3 à state module-level) |
| Tours guidés | 6 |
| Point d'entrée | [frontend/nuxt.config.ts](../frontend/nuxt.config.ts) |

### 🟣 Backend FastAPI (`backend/`)

| Dimension | Valeur |
|---|---|
| Framework | FastAPI 0.115 (async) |
| Langage | Python 3.12 |
| ORM | SQLAlchemy 2 async + asyncpg |
| BDD | PostgreSQL 16 + pgvector |
| LLM | LangGraph 0.2 + LangChain 0.3 + OpenRouter (Claude Sonnet 4) |
| Auth | JWT HS256 (python-jose + bcrypt) + refresh single-flight |
| Tests | pytest 8 + pytest-asyncio + pytest-cov |
| Endpoints REST | 73 |
| Nœuds LangGraph | 9 |
| Tools LangChain | ~36 (12 fichiers) |
| Modèles ORM | 22 |
| Migrations Alembic | 13 |
| Point d'entrée | [backend/app/main.py](../backend/app/main.py) |

## Documentation générée

### Architecture

- [project-overview.md](./project-overview.md) — Mission, stack, chiffres-clés, journal specs 001–019
- [source-tree-analysis.md](./source-tree-analysis.md) — Arborescence annotée des 2 parties
- [architecture-frontend.md](./architecture-frontend.md) — Architecture Nuxt 4 + systèmes transverses (dark mode, tours, widgets, SSE)
- [architecture-backend.md](./architecture-backend.md) — Architecture FastAPI + orchestration LangGraph détaillée
- [integration-architecture.md](./integration-architecture.md) — Contrats frontend ↔ backend : REST, SSE, upload, tours, widgets

### Références techniques

- [api-contracts-backend.md](./api-contracts-backend.md) — Catalogue des 73 endpoints REST + format SSE
- [data-models-backend.md](./data-models-backend.md) — Schéma BDD complet (22 modèles, 13 migrations, pgvector)
- [component-inventory-frontend.md](./component-inventory-frontend.md) — Inventaire composants + composables + stores + types

### Opérationnel

- [development-guide.md](./development-guide.md) — Setup local (Docker + manuel), commandes Make, conventions
- [deployment-guide.md](./deployment-guide.md) — Procédure prod (`deploy.sh`), nginx UAfricas, SSL Let's Encrypt, rollback
- [technical-debt-backlog.md](./technical-debt-backlog.md) — Dette technique priorisée

### Métadonnées

- [project-parts.json](./project-parts.json) — Métadonnées structurées des 2 parties (pour consommation outillée)
- [project-scan-report.json](./project-scan-report.json) — État du workflow de documentation

## Intégrations frontend ↔ backend

| Flux | Source | Cible | Détail |
|---|---|---|---|
| CRUD + fetch | `frontend/app/composables/use*.ts` | `/api/*` | REST JSON + JWT Bearer |
| Chat streaming | `frontend/app/composables/useChat.ts` | `POST /api/chat/.../messages` | SSE via fetch reader (10+ types d'events) |
| Upload | `frontend/app/composables/useDocuments.ts` | `POST /api/documents/upload` | multipart/form-data, 50 Mo max |
| Tours guidés | `useGuidedTour.ts` ← event SSE `guided_tour` | Tool `trigger_guided_tour` (backend) | Marker `<!--SSE:{__sse_guided_tour__:true}-->` |
| Widgets interactifs | `InteractiveQuestionHost.vue` ← event SSE `interactive_question` | Tool `ask_interactive_question` (backend) | Marker `<!--SSE:{__sse_interactive_question__:true}-->` + table `interactive_questions` |
| Contexte page | `uiStore.currentPage` → FormData | `ConversationState.current_page` | Injecté dans les prompts (spec 3) |

Voir [integration-architecture.md](./integration-architecture.md) pour le détail des formats et événements SSE.

## Points d'entrée clés pour l'IDE

- **Layout principal** : [frontend/app/layouts/default.vue](../frontend/app/layouts/default.vue)
- **Widget chat flottant** : [frontend/app/components/copilot/FloatingChatWidget.vue](../frontend/app/components/copilot/FloatingChatWidget.vue)
- **SSE reader + state chat** : [frontend/app/composables/useChat.ts](../frontend/app/composables/useChat.ts)
- **Tours guidés** : [frontend/app/composables/useGuidedTour.ts](../frontend/app/composables/useGuidedTour.ts)
- **Registre des tours** : [frontend/app/lib/guided-tours/registry.ts](../frontend/app/lib/guided-tours/registry.ts)
- **App FastAPI** : [backend/app/main.py](../backend/app/main.py)
- **Endpoint SSE** : [backend/app/api/chat.py](../backend/app/api/chat.py)
- **Graphe LangGraph** : [backend/app/graph/graph.py](../backend/app/graph/graph.py), [backend/app/graph/nodes.py](../backend/app/graph/nodes.py)
- **État conversationnel** : [backend/app/graph/state.py](../backend/app/graph/state.py)
- **Prompts** : [backend/app/prompts/system.py](../backend/app/prompts/system.py)
- **Tools** : [backend/app/graph/tools/](../backend/app/graph/tools/)
- **Migrations** : [backend/alembic/versions/](../backend/alembic/versions/)

## Getting Started (développeur)

```bash
# 1. Clone & config
git clone <repo> && cd esg_mefali
cp .env.example .env         # Éditer OPENROUTER_API_KEY

# 2. Stack Docker
make dev                     # postgres + backend + frontend
make migrate                 # Applique les migrations Alembic

# 3. Accès
# Frontend : http://localhost:3000
# Backend  : http://localhost:8000
# Swagger  : http://localhost:8000/docs

# 4. Tests
make test                    # Complet (backend + frontend)
```

Détails et alternatives sans Docker : [development-guide.md](./development-guide.md).

## Getting Started (IA / Agent)

1. **Commencer par** [project-overview.md](./project-overview.md) pour comprendre la mission, la stack et l'historique des specs.
2. **Pour un travail ciblé** :
   - Fonctionnalité UI/frontend : [architecture-frontend.md](./architecture-frontend.md) + [component-inventory-frontend.md](./component-inventory-frontend.md).
   - Fonctionnalité backend / API / LangGraph : [architecture-backend.md](./architecture-backend.md) + [api-contracts-backend.md](./api-contracts-backend.md) + [data-models-backend.md](./data-models-backend.md).
   - Fonctionnalité transverse (chat, widgets, tours) : [integration-architecture.md](./integration-architecture.md).
3. **Conventions projet** : [CLAUDE.md](../CLAUDE.md) (langue, dark mode, réutilisation, contexte métier).
4. **Dette connue** : [technical-debt-backlog.md](./technical-debt-backlog.md).
5. **Specs passées** : [specs/001](../specs/001-technical-foundation) → [specs/018](../specs/018-interactive-chat-widgets) (spec 019 pilotée via `_bmad-output/`).

## Conventions projet (rappel)

- 🇫🇷 **UI + doc en français accentué** (é, è, ê, à, ç, ù obligatoires). Code + identifiants en anglais.
- 🌙 **Dark mode obligatoire** sur chaque composant (`dark:` variants Tailwind, variables `@theme`).
- ♻️ **Réutilisation** : pattern > 2 occurrences ⇒ extraction en `components/ui/` ou composable.
- 🐍 **Python venv** : jamais d'installation globale, `source backend/venv/bin/activate` à chaque session.
- 📐 **Nuxt 4** : toutes les sources dans `frontend/app/`.
- ✅ **Fichiers autorisés à être modifiés** : aucun fichier n'est "interdit" par convention ; la modification est toujours permise si elle sert la cohérence.

## État de la documentation

Tous les documents listés ci-dessus existent sur le disque. Aucun marqueur `_(To be generated)_` en suspens.

**Généré par** : workflow `bmad-document-project` (Deep Scan, full_rescan)
**Session** : 2026-04-16
**État précédent archivé** : `docs/.archive/project-scan-report-2026-04-12.json`
