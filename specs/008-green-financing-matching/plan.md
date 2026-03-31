# Implementation Plan: Financements Verts — BDD, Matching & Parcours d'Acces

**Branch**: `008-green-financing-matching` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-green-financing-matching/spec.md`

## Summary

Module de financement vert avec base de donnees de 12 fonds reels et 14+ intermediaires (banques, agences ONU, developpeurs carbone), matching intelligent pondere (secteur 30%, ESG 25%, taille 15%, localisation 10%, documents 20%), et parcours d'acces complets via intermediaires avec diagrammes visuels. Integration LangGraph pour les conseils conversationnels avec blocs visuels (Mermaid, tableaux, timelines).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy async, LangGraph, LangChain, WeasyPrint, Jinja2 (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend)
**Storage**: PostgreSQL 16 + pgvector (embeddings), Alembic pour migrations
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web (Linux server backend, navigateur frontend)
**Project Type**: Web application (monolithe modulaire)
**Performance Goals**: Matching instantane (<1s pour 12 fonds), generation parcours <5s (appel LLM)
**Constraints**: Embeddings via OpenRouter, fiche PDF via WeasyPrint
**Scale/Scope**: 12 fonds, 14+ intermediaires, 1 page frontend avec 3 onglets + detail

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | UI en francais, code en anglais, referentiels UEMOA/BCEAO integres, secteur informel pris en compte dans le matching |
| II. Architecture Modulaire | PASS | Module `financing` independant dans `modules/financing/`, frontieres claires via schemas Pydantic et types TypeScript |
| III. Conversation-Driven | PASS | financing_node integre au graphe LangGraph, guide l'utilisateur via le chat avec blocs visuels |
| IV. Test-First | PASS | Tests pytest avant implementation, couverture 80%+ ciblee |
| V. Securite & Donnees | PASS | Auth JWT sur tous les endpoints, requetes parametrees SQLAlchemy, validation Pydantic |
| VI. Inclusivite | PASS | Messages en francais, badges visuels clairs (couleurs + texte), fiche imprimable |
| VII. Simplicite & YAGNI | PASS | Scoring deterministe (pas de ML), seed statique (pas de sync externe), une seule page avec onglets |

**Re-check post-Phase 1**: Tous les principes restent conformes. Pas de violation.

## Project Structure

### Documentation (this feature)

```text
specs/008-green-financing-matching/
├── spec.md              # Specification fonctionnelle
├── plan.md              # Ce fichier
├── research.md          # Decisions techniques et recherche
├── data-model.md        # Modele de donnees detaille
├── quickstart.md        # Guide de demarrage rapide
├── contracts/
│   └── api.md           # Contrats d'API REST
├── checklists/
│   └── requirements.md  # Checklist qualite specification
└── tasks.md             # (genere par /speckit.tasks)
```

### Source Code (repository root)

```text
backend/app/
├── models/
│   └── financing.py                    # Fund, Intermediary, FundIntermediary, FundMatch, FinancingChunk
├── modules/
│   └── financing/
│       ├── __init__.py
│       ├── router.py                   # APIRouter avec endpoints /api/financing/*
│       ├── schemas.py                  # Pydantic: Create/Response/Summary/List schemas
│       ├── service.py                  # Matching, CRUD, RAG, generation parcours
│       ├── seed.py                     # 12 fonds + 14+ intermediaires + liaisons + embeddings
│       ├── preparation_sheet.py        # Generation fiche PDF (WeasyPrint + Jinja2)
│       └── preparation_template.html   # Template HTML pour la fiche
├── graph/
│   ├── state.py                        # + financing_data, _route_financing
│   ├── nodes.py                        # + financing_node()
│   └── graph.py                        # + noeud financing dans le graphe compile
└── main.py                             # + include_router financing

frontend/app/
├── pages/
│   └── financing/
│       ├── index.vue                   # Page principale (3 onglets: Recommandations, Fonds, Intermediaires)
│       └── [id].vue                    # Detail d'un fonds (compatibilite, parcours, intermediaires)
├── composables/
│   └── useFinancing.ts                 # Appels API fetch + headers auth
├── stores/
│   └── financing.ts                    # Pinia setup store
├── types/
│   └── financing.ts                    # Interfaces TypeScript
├── components/
│   ├── financing/                      # Composants specifiques financement
│   └── layout/
│       └── AppSidebar.vue              # + entree "Financement" dans navItems

alembic/versions/
└── 008_add_financing_tables.py         # Migration DDL

tests/
├── backend/
│   └── test_financing/
│       ├── test_models.py
│       ├── test_service.py
│       ├── test_matching.py
│       ├── test_router.py
│       └── test_financing_node.py
└── frontend/
    └── financing/
        └── useFinancing.test.ts
```

**Structure Decision**: Application web (Option 2) — backend FastAPI + frontend Nuxt, coherent avec l'architecture existante du projet. Le module financing suit exactement le pattern des modules existants (esg, carbon, documents, reports).

## Complexity Tracking

Aucune violation de constitution a justifier. Le design respecte tous les principes.
