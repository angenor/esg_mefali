# Implementation Plan: Interface de Chat Conversationnel avec Rendu Visuel Enrichi

**Branch**: `002-chat-rich-visuals` | **Date**: 2026-03-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-chat-rich-visuals/spec.md`

## Summary

Implementer l'interface de chat conversationnel complete avec rendu visuel enrichi (Rich Blocks). Le chat de base (streaming SSE, CRUD conversations) existe deja. Cette feature ajoute : la page /chat avec panneau lateral + zone de conversation, le systeme de parsing et rendu des 6 types de blocs visuels (chart, mermaid, table, gauge, progress, timeline), le mode guide, le responsive mobile, et les ameliorations du systeme prompt. Le backend est largement en place — l'essentiel du travail porte sur le frontend.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**:
- Frontend : Nuxt 4.4.2, Vue 3 Composition API, Pinia, TailwindCSS 4.2, GSAP, Chart.js 4.4, Mermaid 11.4, vue-chartjs 5.3
- Backend : FastAPI 0.115+, SQLAlchemy async, LangGraph 0.2+, LangChain 0.3+, Claude via OpenRouter
**Storage**: PostgreSQL 16 + pgvector (async via asyncpg)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Playwright (frontend)
**Target Platform**: Web (desktop + mobile), navigateurs modernes
**Project Type**: Web application (monolithe modulaire)
**Performance Goals**: Premiere reponse streaming < 5s, chargement conversation < 3s
**Constraints**: Interface integralement en francais, dark mode obligatoire, responsive mobile
**Scale/Scope**: PME africaines francophones, usage initial modere (< 1000 utilisateurs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Notes |
|----------|--------|-------|
| I. Francophone-First | PASS | UI en francais, code en anglais, commentaires francais |
| II. Architecture Modulaire | PASS | Feature dans le module Agent Conversationnel, frontieres claires |
| III. Conversation-Driven UX | PASS | Chat comme interface principale, mode guide |
| IV. Test-First (NON-NEGOTIABLE) | PASS | Vitest + Playwright (frontend), pytest (backend) |
| V. Securite & Donnees | PASS | JSON.parse() (pas eval), sanitization XSS, rate limiting |
| VI. Inclusivite & Accessibilite | PASS | Mode guide, responsive mobile, messages d'erreur francais |
| VII. Simplicite & YAGNI | PASS | Pas de sur-ingenierie, composants simples, monolithe modulaire |

## Project Structure

### Documentation (this feature)

```text
specs/002-chat-rich-visuals/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/chat.py              # EXISTANT — endpoints chat (ajout: rename, rate limit)
│   ├── graph/nodes.py           # EXISTANT — chat_node (ajout: titre auto-genere)
│   ├── prompts/system.py        # EXISTANT — enrichir avec instructions visuelles
│   ├── models/conversation.py   # EXISTANT — pas de changement
│   └── models/message.py        # EXISTANT — pas de changement
└── tests/
    ├── test_chat.py             # EXISTANT — enrichir avec nouveaux tests
    └── test_title_generation.py # NOUVEAU — tests generation titre

frontend/
├── app/
│   ├── pages/
│   │   └── chat.vue                    # NOUVEAU — page principale chat
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatMessage.vue         # EXISTANT — enrichir avec MessageParser
│   │   │   ├── ChatInput.vue           # EXISTANT — ajout blocage pendant streaming
│   │   │   ├── ConversationList.vue    # EXISTANT — ajout recherche, rename, drawer mobile
│   │   │   ├── MessageParser.vue       # NOUVEAU — parse markdown + rich blocks
│   │   │   └── WelcomeMessage.vue      # NOUVEAU — mode guide (diagramme accueil)
│   │   ├── richblocks/
│   │   │   ├── ChartBlock.vue          # NOUVEAU — graphiques Chart.js
│   │   │   ├── MermaidBlock.vue        # NOUVEAU — diagrammes Mermaid
│   │   │   ├── TableBlock.vue          # NOUVEAU — tableaux styles
│   │   │   ├── GaugeBlock.vue          # NOUVEAU — jauges circulaires
│   │   │   ├── ProgressBlock.vue       # NOUVEAU — barres de progression
│   │   │   ├── TimelineBlock.vue       # NOUVEAU — frises chronologiques
│   │   │   ├── BlockError.vue          # NOUVEAU — fallback erreur visuelle
│   │   │   └── BlockPlaceholder.vue    # NOUVEAU — placeholder streaming
│   │   └── ui/
│   │       └── FullscreenModal.vue     # NOUVEAU — modale plein ecran (Agrandir)
│   ├── composables/
│   │   ├── useChat.ts                  # EXISTANT — ajout rename, recherche, rate limit feedback
│   │   └── useMessageParser.ts         # NOUVEAU — logique de parsing des blocs
│   ├── stores/
│   │   └── ui.ts                       # EXISTANT — ajout etat drawer mobile
│   └── types/
│       ├── index.ts                    # EXISTANT — ajout types rich blocks
│       └── richblocks.ts              # NOUVEAU — types des 6 blocs visuels
└── tests/
    ├── unit/
    │   ├── useMessageParser.test.ts    # NOUVEAU — tests parsing blocs
    │   ├── ChartBlock.test.ts          # NOUVEAU — tests rendu chart
    │   ├── MermaidBlock.test.ts        # NOUVEAU — tests rendu mermaid
    │   ├── TableBlock.test.ts          # NOUVEAU — tests rendu table
    │   ├── GaugeBlock.test.ts          # NOUVEAU — tests rendu gauge
    │   ├── ProgressBlock.test.ts       # NOUVEAU — tests rendu progress
    │   └── TimelineBlock.test.ts       # NOUVEAU — tests rendu timeline
    └── e2e/
        └── chat.spec.ts                # NOUVEAU — E2E flux chat complet
```

**Structure Decision**: Structure web application existante (backend/ + frontend/). Aucun nouveau repertoire de premier niveau. Les ajouts se font dans l'arborescence existante. Les composants rich blocks sont regroupes dans `components/richblocks/` pour la cohesion.

## Complexity Tracking

Aucune violation de constitution detectee. Pas de complexite additionnelle a justifier.
