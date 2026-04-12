# Index de documentation — ESG Mefali

> **Point d'entrée principal** pour toute assistance IA (Claude Code, BMad Method, speckit) travaillant sur ce projet.
> **Date de génération** : 2026-04-12
> **Mode de scan** : `initial_scan` / niveau `deep`
> **Générée par** : workflow BMad `bmad-document-project` (v1.2.0)

## Project Documentation Index

### Project Overview

- **Type** : monorepo multi-parts avec 2 parties indépendantes
- **Primary Language** : TypeScript (frontend) + Python 3.12 (backend)
- **Architecture** : SPA Nuxt 4 + API FastAPI asynchrone orchestrée par LangGraph
- **Base de données** : PostgreSQL 16 + pgvector
- **LLM** : Claude Sonnet 4 via OpenRouter
- **Infrastructure** : Docker Compose (postgres + backend + frontend) + Nginx en production

### Quick Reference

#### Partie `frontend` (Nuxt 4)

- **Type** : `web`
- **Tech stack** : Nuxt 4.4, Vue 3 Composition API, TypeScript strict, Pinia 3, TailwindCSS 4, Chart.js, GSAP, Mermaid
- **Root** : `frontend/`
- **Entry point** : `frontend/nuxt.config.ts` + `frontend/app/app.vue`
- **Tests** : Vitest (unit) + Playwright (E2E)
- **Métriques** : 18 pages, 56 composants, 14 composables, 11 stores Pinia, 11 fichiers de types

#### Partie `backend` (FastAPI)

- **Type** : `backend`
- **Tech stack** : Python 3.12, FastAPI, SQLAlchemy async 2, asyncpg, LangGraph, LangChain, Alembic, Pydantic v2, WeasyPrint, PyMuPDF
- **Root** : `backend/`
- **Entry point** : `backend/app/main.py`
- **Tests** : pytest + pytest-asyncio (~935 tests)
- **Métriques** : ~73 endpoints REST, 16 modèles SQLAlchemy, 13 migrations Alembic, 10 nœuds LangGraph, ~100 tools LangChain, 9 modules de prompts

### Generated Documentation

Tous les fichiers sont dans `docs/` :

| Document | Description |
|---|---|
| [Project Overview](./project-overview.md) | Vue d'ensemble métier + architecture globale + stack + modules fonctionnels |
| [Architecture Frontend](./architecture-frontend.md) | Configuration Nuxt, structure app/, pages, composants, composables, stores, dark mode, intégration API |
| [Architecture Backend](./architecture-backend.md) | Couches, point d'entrée main.py, LangGraph, config, sécurité, tests, tools LangChain |
| [Architecture d'intégration](./integration-architecture.md) | Points d'intégration frontend ↔ backend, REST JSON, SSE, upload, auth JWT, invariants |
| [Arbre des sources annoté](./source-tree-analysis.md) | Arborescence complète annotée du monorepo |
| [Inventaire des composants frontend](./component-inventory-frontend.md) | 56 composants Vue détaillés par sous-dossier |
| [Modèles de données backend](./data-models-backend.md) | 16 modèles SQLAlchemy + relations + migrations Alembic |
| [Contrats d'API REST](./api-contracts-backend.md) | 13 routers / ~73 endpoints + events SSE |
| [Guide de développement](./development-guide.md) | Setup local, Docker, tests, linting, conventions, workflow feature |
| [Guide de déploiement](./deployment-guide.md) | Prod Docker Compose + Nginx, sécurité, migrations, backup, scaling |
| [Project parts metadata](./project-parts.json) | Métadonnées structurées du monorepo (machine-readable) |

### Existing Documentation

- [README.md](../README.md) — Quickstart Docker + commandes `make`
- [CLAUDE.md](../CLAUDE.md) — Instructions projet pour Claude Code (conventions, modules, historique features)
- [.env.example](../.env.example) — Variables d'environnement documentées
- [Makefile](../Makefile) — `make dev`, `make test`, `make migrate`, ...
- [note.md](../note.md) — Notes internes
- `specs/` — 18 spécifications speckit (features 001 à 018)
- `documents_et_brouillons/` — Brouillons, brainstorming, documents sources

### Getting Started

Pour démarrer le projet en local :

```bash
# 1. Cloner et configurer
git clone <repo-url>
cd esg_mefali
cp .env.example .env
# → Éditer .env : ajouter OPENROUTER_API_KEY, changer SECRET_KEY

# 2. Lancer les 3 services (postgres + backend + frontend)
make dev

# 3. Appliquer les migrations (une fois les containers up)
make migrate

# 4. Ouvrir
# Frontend :   http://localhost:3000
# Backend API : http://localhost:8000
# Swagger :    http://localhost:8000/docs
```

Pour le **développement local sans Docker**, voir la section dédiée du [Guide de développement](./development-guide.md#5-développement-local-sans-docker).

### Pour les workflows BMad / Claude Code

- **Brownfield PRD** : pointer le workflow PRD sur `docs/index.md` (ce fichier)
- **Feature UI seule** : référencer `docs/architecture-frontend.md`
- **Feature backend / API seule** : référencer `docs/architecture-backend.md`
- **Feature full-stack** : combiner les deux + `docs/integration-architecture.md`
- **Modèle de données** : `docs/data-models-backend.md`
- **Contrat d'API** : `docs/api-contracts-backend.md`

### Conventions projet clés (extraits de `CLAUDE.md`)

- **Langue code** : anglais (variables, fonctions, classes)
- **Langue commentaires** : français
- **Langue UI/docs** : français avec accents obligatoires
- **Dark mode** : OBLIGATOIRE sur tous les composants via variantes Tailwind `dark:`
- **Réutilisabilité** : extraire tout pattern répété 2+ fois dans `components/ui/`
- **Python venv** : toujours activer `backend/venv` avant toute commande Python
- **Nommage BDD** : tables `snake_case` pluriel
- **Tests** : cible 80 % de couverture (rule `common/testing.md`)

### Historique des features majeures (18)

Voir `specs/` pour le détail de chaque feature (spec-kit structure) :

1. `001-technical-foundation` — Fondation technique
2. `002-chat-rich-visuals` — Rich blocks visuels chat
3. `003-company-profiling-memory` — Profilage entreprise + mémoire
4. `004-document-upload-analysis` — Upload + analyse documents
5. `005-esg-scoring-assessment` — Évaluation et scoring ESG
6. `006-esg-pdf-reports` — Rapports ESG PDF
7. `007-carbon-footprint-calculator` — Calculateur empreinte carbone
8. `008-green-financing-matching` — Matchmaking financement vert
9. `009-fund-application-generator` — Générateur dossiers de candidature
10. `010-green-credit-scoring` — Scoring crédit vert
11. `011-dashboard-action-plan` — Dashboard + plan d'action
12. `012-langgraph-tool-calling` — Tool calling LangGraph
13. `013-fix-multiturn-routing-timeline` — Routing multi-tour + timeline
14. `014-concise-chat-style` — Style concis du chat
15. `015-fix-toolcall-esg-timeout` — Fix timeout tool ESG
16. `016-fix-tool-persistence-bugs` — Fix persistance tools
17. `017-fix-failing-tests` — Correction tests
18. `018-interactive-chat-widgets` — Widgets questions interactives (en cours)
