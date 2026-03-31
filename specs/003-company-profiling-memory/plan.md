# Implementation Plan: Profilage Intelligent et Memoire Contextuelle

**Branch**: `003-company-profiling-memory` | **Date**: 2026-03-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-company-profiling-memory/spec.md`

## Summary

Implementer le profilage intelligent d'entreprise via extraction conversationnelle (Module 1.2) et la memoire contextuelle (Module 1.3). Le graphe LangGraph passe d'un noeud unique (`chat`) a un graphe multi-noeuds avec `router_node`, `chat_node` et `profiling_node`. Le profil entreprise est extrait automatiquement des messages via une chaine LangChain d'extraction structuree, stocke en base PostgreSQL, et injecte dans le prompt systeme pour personnaliser les reponses. Le frontend ajoute une page profil, un badge de completion dans la sidebar, et des notifications d'extraction dans le chat.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph, LangChain, SQLAlchemy (async), Nuxt 4, Vue Composition API, Pinia, TailwindCSS
**Storage**: PostgreSQL 16 + pgvector (async via asyncpg), Alembic pour migrations
**Testing**: pytest (backend), Vitest + Playwright E2E (frontend)
**Target Platform**: Web application (serveur Linux, navigateur desktop/mobile)
**Project Type**: Web-service (monolithe modulaire FastAPI + Nuxt)
**Performance Goals**: Extraction de profil en parallele du chat, < 1s de latence ajoutee
**Constraints**: Streaming SSE existant contourne LangGraph — necessite refactoring pour passer par le graphe
**Scale/Scope**: Monoposte a ~100 utilisateurs concurrents initialement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Commentaire |
|----------|--------|-------------|
| I. Francophone-First | PASS | UI en francais, code en anglais, referentiels UEMOA/CEDEAO integres via le prompt |
| II. Architecture Modulaire | PASS | Nouveau module `company` dans `backend/app/modules/company/`, frontieres claires via schemas Pydantic |
| III. Conversation-Driven UX | PASS | Profilage conversationnel est le coeur de la feature, formulaire en alternative |
| IV. Test-First | PASS | TDD obligatoire, pytest backend, Vitest frontend |
| V. Securite & Donnees | PASS | Schemas Pydantic pour validation, SQLAlchemy ORM (pas de SQL brut), pas de secrets dans le code |
| VI. Inclusivite | PASS | Messages en francais, interface simple, dark mode |
| VII. Simplicite & YAGNI | PASS | Monolithe modulaire, pas de microservice, extraction via LLM existant |

## Project Structure

### Documentation (this feature)

```text
specs/003-company-profiling-memory/
├── plan.md              # Ce fichier
├── spec.md              # Specification
├── research.md          # Phase 0 : recherche et decisions techniques
├── data-model.md        # Phase 1 : modele de donnees
├── quickstart.md        # Phase 1 : guide de demarrage rapide
├── contracts/           # Phase 1 : contrats d'interface API
│   └── api-contracts.md
└── tasks.md             # Phase 2 : taches (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── chat.py              # Modifie : streaming via graphe, events profil
│   │   └── company.py           # Nouveau : endpoints REST profil entreprise
│   ├── chains/
│   │   └── extraction.py        # Nouveau : chaine LangChain extraction structuree
│   ├── graph/
│   │   ├── state.py             # Modifie : ajout user_profile, context_memory
│   │   ├── graph.py             # Modifie : graphe multi-noeuds avec routeur
│   │   └── nodes.py             # Modifie : router_node, chat_node enrichi, profiling_node
│   ├── models/
│   │   └── company.py           # Nouveau : modele SQLAlchemy CompanyProfile
│   ├── modules/
│   │   └── company/
│   │       ├── __init__.py
│   │       ├── schemas.py       # Nouveau : schemas Pydantic profil
│   │       ├── service.py       # Nouveau : CRUD + calcul completion
│   │       └── router.py        # Nouveau : endpoints FastAPI
│   ├── prompts/
│   │   └── system.py            # Modifie : prompt dynamique avec profil
│   └── schemas/
│       └── chat.py              # Modifie : ajout events SSE profil
└── alembic/
    └── versions/
        └── xxx_add_company_profiles.py  # Nouvelle migration

frontend/
├── app/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatMessage.vue      # Modifie : notification extraction profil
│   │   │   └── ProfileNotification.vue  # Nouveau : notification discrete
│   │   ├── layout/
│   │   │   └── AppSidebar.vue       # Modifie : badge completion profil
│   │   └── profile/
│   │       ├── ProfileForm.vue      # Nouveau : formulaire editable par categorie
│   │       ├── ProfileProgress.vue  # Nouveau : barre de progression
│   │       └── ProfileField.vue     # Nouveau : champ individuel avec etat
│   ├── composables/
│   │   ├── useChat.ts               # Modifie : gestion events profil SSE
│   │   └── useCompanyProfile.ts     # Nouveau : composable profil entreprise
│   ├── pages/
│   │   └── profile.vue              # Nouveau : page profil
│   ├── stores/
│   │   └── company.ts               # Nouveau : store Pinia profil
│   └── types/
│       └── company.ts               # Nouveau : types TypeScript profil
```

**Structure Decision**: Extension du monolithe modulaire existant. Le module `company` suit le pattern des modules futurs (dossier dans `modules/` avec schemas, service, router). Le graphe LangGraph evolue d'un noeud unique a un graphe conditionnel multi-noeuds.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Refactoring SSE streaming pour passer par le graphe | Le profiling_node doit s'executer dans le graphe pour acceder au state partage | Contourner le graphe rendrait l'etat du profil incoherent et obligerait a dupliquer la logique |
| Execution parallele chat_node + profiling_node | FR-009 exige que l'extraction n'ajoute pas de latence | L'execution sequentielle ajouterait 1-2s de latence perceptible par l'utilisateur |
