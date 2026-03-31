# Implementation Plan: Evaluation et Scoring ESG Contextualise

**Branch**: `005-esg-scoring-assessment` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-esg-scoring-assessment/spec.md`

## Summary

Implementer le module metier central de la plateforme : evaluation ESG conversationnelle (30 criteres, 3 piliers) avec scoring dynamique pondere par secteur, enrichissement documentaire via RAG, benchmarking sectoriel, et page de resultats persistante. Le systeme s'integre dans le graph LangGraph existant via un nouveau noeud `esg_scoring_node` et exploite les blocs visuels du chat (progress, chart, gauge, table, mermaid) deja implementes.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangGraph, LangChain, SQLAlchemy async, PyMuPDF, Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs
**Storage**: PostgreSQL 16 + pgvector (embeddings), stockage fichiers local
**Testing**: pytest (backend), Vitest + Playwright (frontend)
**Target Platform**: Web (navigateur desktop/mobile)
**Project Type**: Web-service (monolithe modulaire : FastAPI backend + Nuxt frontend)
**Performance Goals**: Evaluation complete < 20 min, page resultats < 3s, streaming temps reel
**Constraints**: Interface francais, contexte PME africaines UEMOA/CEDEAO, secteur informel
**Scale/Scope**: Centaines d'utilisateurs, 30 criteres ESG, 6+ secteurs avec benchmarks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Detail |
|----------|--------|--------|
| I. Francophone-First | PASS | UI en francais, questions adaptees zone UEMOA/CEDEAO, secteur informel pris en compte |
| II. Architecture Modulaire | PASS | Nouveau module `esg` isole dans `modules/esg/`, communication via schemas Pydantic/TypeScript |
| III. Conversation-Driven UX | PASS | Evaluation conduite via le chat LangGraph, pas de formulaire complexe |
| IV. Test-First | PASS | TDD obligatoire, pytest backend, Vitest frontend, couverture 80%+ |
| V. Securite & Donnees | PASS | Validation Pydantic, SQLAlchemy ORM (pas de SQL brut), pas de secrets dans le code |
| VI. Inclusivite & Accessibilite | PASS | Messages en francais clairs, mode guide pour evaluation, connexion lente prise en compte |
| VII. Simplicite & YAGNI | PASS | Monolithe modulaire, stockage local, traitement synchrone, pas d'abstraction prematuree |

## Project Structure

### Documentation (this feature)

```text
specs/005-esg-scoring-assessment/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 : recherche et decisions
├── data-model.md        # Phase 1 : modele de donnees
├── quickstart.md        # Phase 1 : guide demarrage rapide
├── contracts/           # Phase 1 : contrats API
│   └── esg-api.md       # Endpoints ESG
└── tasks.md             # Phase 2 : taches (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── graph/
│   │   ├── state.py          # + champ esg_assessment dans ConversationState
│   │   ├── nodes.py          # + esg_scoring_node, modification router_node
│   │   └── graph.py          # + routage conditionnel vers esg_scoring_node
│   ├── modules/
│   │   └── esg/
│   │       ├── __init__.py
│   │       ├── service.py     # ESGScoringService (grille, ponderation, scoring, benchmark)
│   │       ├── schemas.py     # Pydantic : ESGAssessmentCreate/Response, CriteriaScore, etc.
│   │       ├── router.py      # Endpoints REST /api/esg/*
│   │       ├── criteria.py    # Definition des 30 criteres (E1-E10, S1-S10, G1-G10)
│   │       └── weights.py     # Ponderations sectorielles
│   ├── models/
│   │   └── esg.py             # ESGAssessment SQLAlchemy model
│   ├── chains/
│   │   └── esg_evaluation.py  # Chain LLM pour evaluation conversationnelle ESG
│   └── prompts/
│       └── esg_scoring.py     # Prompts systeme pour le noeud ESG avec instructions visuelles
├── alembic/
│   └── versions/
│       └── xxx_add_esg_assessment.py  # Migration Alembic
└── tests/
    ├── test_esg_service.py
    ├── test_esg_router.py
    ├── test_esg_scoring_node.py
    └── test_esg_criteria.py

frontend/
├── app/
│   ├── pages/
│   │   ├── esg.vue            # Page ESG principale (invitation ou evaluation en cours)
│   │   └── esg/
│   │       └── results.vue    # Page resultats persistante
│   ├── components/
│   │   └── esg/
│   │       ├── ScoreCircle.vue      # Cercle de progression colore (score global)
│   │       ├── CriteriaProgress.vue # Barres de progression des 30 criteres
│   │       ├── StrengthsBadges.vue  # Points forts avec badges verts
│   │       ├── Recommendations.vue  # Recommandations priorisees
│   │       └── ScoreHistory.vue     # Graphique evolution temporelle
│   ├── composables/
│   │   └── useEsg.ts          # API calls ESG + state management
│   ├── stores/
│   │   └── esg.ts             # Store Pinia pour l'etat ESG
│   └── types/
│       └── esg.ts             # Types TypeScript ESG
```

**Structure Decision**: Extension de la structure existante (monolithe modulaire). Le nouveau module `esg/` suit le pattern etabli par `company/` et `documents/`. Le noeud LangGraph est ajoute dans `graph/nodes.py` existant (pas de fichier separe, coherence avec l'existant). Les composants frontend ESG sont dans un dossier dedie `components/esg/`.

## Complexity Tracking

> Pas de violation de constitution. Aucune complexite supplementaire non justifiee.
