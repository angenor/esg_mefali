# Implementation Plan: Tableau de bord principal et plan d'action

**Branch**: `011-dashboard-action-plan` | **Date**: 2026-04-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-dashboard-action-plan/spec.md`

## Summary

Implémentation des modules 6 (Plan d'Action) et 7 (Tableau de Bord) de la plateforme ESG Mefali. Le dashboard agrège les données de tous les modules existants (ESG, carbone, crédit vert, financements) en 4 cartes de synthèse avec une carte "Financements" enrichie intégrant le statut des parcours intermédiaires. Le plan d'action est généré par Claude avec des actions concrètes liées aux intermédiaires financiers (coordonnées, rendez-vous, préparation de dossiers). Le système inclut des rappels typés, une gamification par badges et des blocs visuels dans le chat (timeline, table, mermaid, gauge, chart).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy async, LangGraph, LangChain, WeasyPrint (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend)
**Storage**: PostgreSQL 16 + pgvector, Alembic pour migrations
**Testing**: pytest (backend), Vitest + Playwright E2E (frontend)
**Target Platform**: Web application (serveur Linux, navigateurs modernes)
**Project Type**: Web-service (monolithe modulaire backend + SPA frontend)
**Performance Goals**: Dashboard < 3s, génération plan < 30s
**Constraints**: Interface 100% français, dark mode obligatoire, connexions lentes supportées
**Scale/Scope**: PME africaines francophones, ~2 nouvelles pages frontend, ~2 nouveaux modules backend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | UI en français, code en anglais, référentiels UEMOA/BCEAO intégrés via modules existants |
| II. Architecture Modulaire | PASS | 2 modules séparés (dashboard, action_plan) avec frontières claires, communication via API internes |
| III. Conversation-Driven UX | PASS | Plan d'action généré via chat avec blocs visuels, noeud LangGraph dédié (action_plan_node) |
| IV. Test-First | PASS | Tests écrits avant implémentation, couverture >= 80% ciblée |
| V. Sécurité & Données | PASS | Validation Pydantic, requêtes SQLAlchemy ORM, auth Bearer token |
| VI. Inclusivité | PASS | États vides avec guidage, messages d'erreur en français, dark mode |
| VII. Simplicité & YAGNI | PASS | Monolithe modulaire, rappels in-app uniquement (pas email/SMS), badges simples sans système de points |

## Project Structure

### Documentation (this feature)

```text
specs/011-dashboard-action-plan/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-endpoints.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── action_plan.py     # ActionPlan, ActionItem, Reminder, Badge
│   │   └── ... (existants)
│   ├── modules/
│   │   ├── dashboard/
│   │   │   ├── __init__.py
│   │   │   ├── router.py      # GET /api/dashboard/summary
│   │   │   ├── service.py     # Agrégation données cross-modules
│   │   │   └── schemas.py     # DashboardSummary, ActivityEvent
│   │   └── action_plan/
│   │       ├── __init__.py
│   │       ├── router.py      # CRUD plan, items, reminders
│   │       ├── service.py     # Génération plan via LLM, badges
│   │       ├── schemas.py     # ActionPlan, ActionItem, Reminder, Badge schemas
│   │       └── badges.py      # Définitions et conditions des badges
│   ├── graph/
│   │   ├── nodes.py           # + action_plan_node (nouveau)
│   │   ├── graph.py           # + route action_plan
│   │   └── state.py           # + action_plan_data
│   └── prompts/
│       └── action_plan.py     # Prompt système plan d'action
├── alembic/
│   └── versions/
│       └── xxx_add_action_plan_tables.py
└── tests/
    ├── test_dashboard/
    │   ├── test_router.py
    │   └── test_service.py
    └── test_action_plan/
        ├── test_router.py
        ├── test_service.py
        └── test_badges.py

frontend/
├── app/
│   ├── pages/
│   │   ├── dashboard.vue          # Page dashboard (remplace index.vue placeholder)
│   │   └── action-plan/
│   │       └── index.vue          # Page plan d'action avec timeline
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── ScoreCard.vue      # Carte générique score (ESG, carbone, crédit)
│   │   │   ├── FinancingCard.vue  # Carte financements enrichie
│   │   │   ├── NextActions.vue    # Section prochaines actions
│   │   │   └── ActivityFeed.vue   # Section activité récente
│   │   └── action-plan/
│   │       ├── Timeline.vue       # Timeline visuelle des actions
│   │       ├── ActionCard.vue     # Carte détail action (avec intermédiaire)
│   │       ├── CategoryFilter.vue # Filtre par catégorie
│   │       ├── ProgressBar.vue    # Barre progression globale
│   │       ├── BadgeGrid.vue      # Grille des badges
│   │       └── ReminderForm.vue   # Formulaire création rappel
│   ├── stores/
│   │   ├── dashboard.ts           # Store dashboard
│   │   └── actionPlan.ts          # Store plan d'action
│   ├── composables/
│   │   ├── useDashboard.ts        # API dashboard
│   │   └── useActionPlan.ts       # API plan d'action + rappels
│   └── types/
│       ├── dashboard.ts           # Types dashboard
│       └── actionPlan.ts          # Types plan d'action
└── tests/
    └── ... (Vitest + Playwright)
```

**Structure Decision**: Structure web application avec backend/frontend séparés, suivant le pattern modulaire existant. Chaque nouveau module backend suit le pattern router/service/schemas. Chaque page frontend suit le pattern composable + store + components dédiés.

## Complexity Tracking

Aucune violation de constitution détectée. Pas de justification nécessaire.
