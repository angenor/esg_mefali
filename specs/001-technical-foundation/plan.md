# Implementation Plan: Foundation Technique ESG Mefali

**Branch**: `001-technical-foundation` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-technical-foundation/spec.md`

## Summary

Mise en place du socle technique complet de la plateforme ESG Mefali : un backend FastAPI avec authentification JWT et graphe LangGraph minimal (chat node + checkpointer PostgreSQL), un frontend Nuxt 4 avec layout responsive (sidebar + panneau chat IA persistant), et une infrastructure Docker Compose orchestrant les 3 services. Aucune logique metier ESG — uniquement l'infrastructure technique.

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.x (strict mode)
**Primary Dependencies**:
- Backend : FastAPI, SQLAlchemy[asyncio], asyncpg, Alembic, langchain-core, langchain-openai, langgraph, langgraph-checkpoint-postgres, python-jose[cryptography], passlib[bcrypt], pydantic>=2.0
- Frontend : Nuxt 4, Pinia, TailwindCSS 4, GSAP, vue-chartjs (Chart.js), mermaid
**Storage**: PostgreSQL 16 + pgvector
**Testing**: pytest + httpx (backend), Vitest + Playwright (frontend E2E)
**Target Platform**: Web application (Linux server via Docker)
**Project Type**: Web application (frontend + backend + database)
**Performance Goals**: Premier token IA < 3s, demarrage services < 2min
**Constraints**: Mobile-first, UI entierement en francais, connexions potentiellement lentes (Afrique de l'Ouest)
**Scale/Scope**: PME africaines francophones, demarrage avec quelques dizaines d'utilisateurs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Detail |
|----------|--------|--------|
| I. Francophone-First | PASS | UI en francais, code en anglais, commentaires en francais |
| II. Architecture Modulaire | PASS | Structure en modules independants, schemas Pydantic pour les interfaces |
| III. Conversation-Driven | PASS | Panneau chat IA persistant comme element central de l'UX |
| IV. Test-First (NON-NEGOTIABLE) | PASS | pytest + Vitest + Playwright, objectif 80% couverture |
| V. Securite & Donnees | PASS | JWT, bcrypt, SQLAlchemy ORM (pas de SQL brut), .env pour les secrets |
| VI. Inclusivite | PASS (partiel) | Mobile-first, lazy loading. Speech-to-text reporte a une feature ulterieure |
| VII. Simplicite & YAGNI | PASS | Monolithe modulaire, sync, stockage local, pas d'abstraction prematuree |

**Resultat** : Tous les gates passent. Aucune violation.

## Project Structure

### Documentation (this feature)

```text
specs/001-technical-foundation/
├── plan.md              # Ce fichier
├── spec.md              # Specification fonctionnelle
├── research.md          # Phase 0 : recherche technique
├── data-model.md        # Phase 1 : modele de donnees
├── quickstart.md        # Phase 1 : guide de demarrage rapide
├── contracts/           # Phase 1 : contrats d'API
│   └── api-auth.md      # Contrat des endpoints d'authentification
│   └── api-chat.md      # Contrat des endpoints de conversation
│   └── api-health.md    # Contrat du health check
└── tasks.md             # Phase 2 : taches (genere par /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                  # Point d'entree FastAPI
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── security.py          # JWT, hashing, dependances auth
│   │   └── database.py          # Engine async SQLAlchemy, session
│   ├── models/
│   │   ├── base.py              # DeclarativeBase SQLAlchemy
│   │   └── user.py              # Modele User
│   ├── schemas/
│   │   ├── auth.py              # Schemas Pydantic auth (register, login, token)
│   │   └── chat.py              # Schemas Pydantic chat (message, conversation)
│   ├── api/
│   │   ├── deps.py              # Dependances communes (get_current_user)
│   │   ├── auth.py              # Router /auth
│   │   ├── chat.py              # Router /chat (SSE streaming)
│   │   └── health.py            # Router /health
│   ├── graph/
│   │   ├── state.py             # ConversationState (TypedDict)
│   │   ├── graph.py             # Compilation du graphe LangGraph
│   │   ├── nodes.py             # chat_node (appel Claude via OpenRouter)
│   │   └── checkpointer.py      # Configuration PostgresCheckpointer
│   ├── prompts/
│   │   └── system.py            # Prompt systeme de base
│   ├── modules/
│   │   └── company/             # Module entreprise (placeholder)
│   ├── chains/                  # Vide (futur)
│   └── nodes/                   # Vide (futur, noeuds supplementaires)
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/                # Migrations
├── tests/
│   ├── conftest.py              # Fixtures (client async, db test)
│   ├── test_auth.py             # Tests endpoints auth
│   ├── test_chat.py             # Tests endpoints chat
│   └── test_health.py           # Tests health check
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
└── .env.example

frontend/
├── nuxt.config.ts               # Config Nuxt 4 + modules
├── app.vue                      # Layout racine
├── tailwind.config.ts           # Design system couleurs marque
├── assets/
│   └── css/
│       └── main.css             # Imports Tailwind + custom
├── layouts/
│   └── default.vue              # Layout : sidebar + header + contenu + chat panel
├── pages/
│   ├── login.vue                # Page connexion
│   ├── register.vue             # Page inscription
│   └── index.vue                # Dashboard (placeholder)
├── components/
│   ├── layout/
│   │   ├── AppSidebar.vue       # Sidebar retractable
│   │   ├── AppHeader.vue        # Header avec logo + menu user
│   │   └── ChatPanel.vue        # Panneau chat IA lateral persistant
│   ├── chat/
│   │   ├── ChatMessage.vue      # Bulle de message (user/assistant)
│   │   ├── ChatInput.vue        # Zone de saisie + envoi
│   │   └── ConversationList.vue # Liste des conversations
│   └── ui/
│       └── ToastNotification.vue # Composant toast global
├── composables/
│   ├── useAuth.ts               # Logique auth (login, register, refresh)
│   ├── useChat.ts               # Logique chat (SSE, messages)
│   └── useToast.ts              # Logique notifications toast
├── stores/
│   ├── auth.ts                  # Pinia store auth (user, token)
│   └── ui.ts                    # Pinia store UI (sidebar, theme)
├── middleware/
│   └── auth.global.ts           # Middleware auth global
├── plugins/
│   ├── gsap.client.ts           # Plugin GSAP (client-only)
│   └── chartjs.client.ts        # Plugin Chart.js (client-only)
├── types/
│   └── index.ts                 # Types partages
├── Dockerfile
├── package.json
└── tsconfig.json

docker-compose.yml               # 3 services : frontend, backend, postgres
Makefile                          # Commandes : dev, build, migrate, test
.gitignore                        # Python + Node + IDE
.env.example                      # Variables d'environnement racine
README.md                         # Instructions setup local
```

**Structure Decision**: Architecture web classique frontend/backend separee, conforme au CLAUDE.md. Le backend suit la structure modulaire FastAPI definie dans la spec (app/graph/, app/nodes/, app/modules/, etc.). Le frontend suit les conventions Nuxt 4 (pages/, components/, composables/, stores/).

## Architecture Decisions

### AD-001 : Authentification JWT stateless

**Decision** : JWT stateless avec access token (1h) + refresh token (30j) stockes cote client.
**Rationale** : Simple a implementer, pas besoin de session store Redis pour la v1. Le refresh token long (30j) offre un bon confort pour les utilisateurs PME qui ne se connectent pas quotidiennement.
**Alternative rejetee** : Session-based auth (necessite Redis, plus complexe pour une v1).

### AD-002 : LangGraph avec PostgresCheckpointer

**Decision** : Utiliser LangGraph comme orchestrateur de conversation avec AsyncPostgresSaver pour persister l'etat. Le LLM est accede via `ChatOpenAI` (langchain-openai) avec base URL OpenRouter (et non ChatAnthropic qui ne supporte pas OpenRouter).
**Rationale** : LangGraph permet d'ajouter des noeuds (modules ESG) sans refactorer le systeme de conversation. Le checkpointer PostgreSQL reutilise la BDD existante, pas besoin d'un store separe. Le graph et le checkpointer sont initialises dans le lifespan FastAPI pour gerer correctement le cycle de vie des connexions.
**Alternative rejetee** : Appel direct Claude API sans orchestrateur (rendrait l'ajout de modules metier beaucoup plus complexe). ChatAnthropic rejete car bug de routing avec OpenRouter.

### AD-003 : Chat en panneau lateral persistant

**Decision** : Le chat IA est un panneau lateral droit, toujours visible (repliable sur mobile), distinct de la sidebar de navigation a gauche.
**Rationale** : Conforme au principe III (Conversation-Driven). L'utilisateur peut interagir avec l'IA depuis n'importe quelle page, ce qui est essentiel quand les modules metier seront ajoutes.
**Layout** : `[Sidebar nav | Contenu principal | Chat panel]`

### AD-004 : Streaming SSE pour les reponses IA

**Decision** : Utiliser Server-Sent Events (SSE) via FastAPI StreamingResponse pour streamer les tokens LangGraph vers le frontend.
**Rationale** : SSE est unidirectionnel (serveur → client), parfait pour le streaming de texte. Plus simple que WebSocket pour ce cas d'usage. Le frontend utilise EventSource natif ou fetch + ReadableStream.
**Alternative rejetee** : WebSocket (bidirectionnel, surdimensionne pour du streaming de texte simple).

### AD-005 : Nuxt 4 avec TailwindCSS 4

**Decision** : Nuxt 4 (derniere version stable) avec TailwindCSS 4 et module @nuxtjs/tailwindcss.
**Rationale** : Stack imposee par la constitution. TailwindCSS 4 offre le nouveau moteur CSS-first.

### AD-006 : Plugins client-only pour Chart.js, GSAP, Mermaid

**Decision** : Chart.js (via vue-chartjs), GSAP et Mermaid sont enregistres comme plugins `.client.ts` dans Nuxt.
**Rationale** : Ces librairies manipulent le DOM et ne sont pas compatibles SSR. Le suffixe `.client.ts` garantit qu'elles ne sont chargees que cote client.

## Complexity Tracking

> Aucune violation de constitution a justifier.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
