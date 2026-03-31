# Implementation Plan: Fund Application Generator

**Branch**: `009-fund-application-generator` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-fund-application-generator/spec.md`

## Summary

Generation automatique de dossiers de candidature aux fonds verts, avec contenu adapte au destinataire (fonds direct, banque partenaire, agence d'implementation, developpeur carbone). Le systeme utilise des templates de sections differencies par target_type, genere le contenu via LLM + RAG pgvector, produit des fiches de preparation intermediaire en PDF, et integre un simulateur de financement avec timeline enrichie. Le tout est accessible via une API REST, des pages frontend dediees, et le chat conversationnel LangGraph.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy async, LangGraph, LangChain, WeasyPrint, Jinja2, python-docx (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, toast-ui/editor, Chart.js (frontend)
**Storage**: PostgreSQL 16 + pgvector (embeddings), Alembic pour migrations
**Testing**: pytest (backend), Vitest + Playwright (frontend)
**Target Platform**: Web (serveur Linux, navigateur desktop/mobile)
**Project Type**: Web application (monolithe modulaire FastAPI + Nuxt)
**Performance Goals**: Generation de section < 30s, export PDF < 10s, simulation < 2s
**Constraints**: Interface integralement en francais, dark mode obligatoire, ton adapte au destinataire
**Scale/Scope**: ~100 utilisateurs PME, 12 fonds, 14 intermediaires, 5 templates de dossier

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Commentaire |
|----------|--------|-------------|
| I. Francophone-First | PASS | UI en francais, code en anglais, referentiels UEMOA/BCEAO integres dans les templates |
| II. Architecture Modulaire | PASS | Nouveau module `applications` avec frontieres claires, communique via API/schemas |
| III. Conversation-Driven | PASS | application_node integre au graphe LangGraph pour guidance conversationnelle |
| IV. Test-First | PASS | TDD prevu (pytest backend, Vitest frontend), objectif 80% couverture |
| V. Securite & Donnees | PASS | Schemas Pydantic, SQLAlchemy ORM, pas de secrets en code, validation entrees |
| VI. Inclusivite | PASS | Messages d'erreur en francais, lazy loading, connexions lentes prises en compte |
| VII. Simplicite & YAGNI | PASS | Templates en code (pas en BDD), pas d'abstraction prematuree, WeasyPrint existant reutilise |

**Post-Phase 1 Re-Check**: Tous les principes respectes. L'ajout de python-docx est la seule nouvelle dependance. Les 5 templates sont definis en Python (dictionnaires), pas en BDD.

## Project Structure

### Documentation (this feature)

```text
specs/009-fund-application-generator/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart
├── contracts/
│   └── api.md           # API contracts (10 endpoints)
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── application.py          # FundApplication + TargetType + ApplicationStatus
│   ├── modules/
│   │   └── applications/
│   │       ├── __init__.py
│   │       ├── router.py            # 10 endpoints REST
│   │       ├── service.py           # Logique metier + generation LLM
│   │       ├── schemas.py           # Schemas Pydantic
│   │       ├── templates.py         # Configuration templates par target_type
│   │       ├── export.py            # Export PDF (WeasyPrint) + Word (python-docx)
│   │       ├── prep_sheet.py        # Fiche preparation intermediaire PDF
│   │       ├── simulation.py        # Simulateur de financement
│   │       └── templates/
│   │           ├── application_export.html
│   │           └── prep_sheet.html
│   └── graph/
│       ├── nodes.py                 # + application_node
│       └── graph.py                 # + routing "application"
└── tests/
    └── test_applications/
        ├── test_router.py
        ├── test_service.py
        ├── test_templates.py
        ├── test_export.py
        ├── test_simulation.py
        └── test_prep_sheet.py

frontend/
├── app/
│   ├── pages/
│   │   └── applications/
│   │       ├── index.vue            # Liste dossiers
│   │       └── [id].vue             # Detail (sections, checklist, prep, simulation)
│   ├── composables/
│   │   └── useApplications.ts
│   └── stores/
│       └── applications.ts
└── tests/
    └── applications/
        └── applications.spec.ts
```

**Structure Decision**: Extension du monolithe modulaire existant. Le module `applications` suit le pattern des 6 modules precedents (router + service + schemas). Le node LangGraph est ajoute dans le fichier nodes.py existant.

## Complexity Tracking

Aucune violation de constitution a justifier. La complexite est contenue par la reutilisation des patterns existants (WeasyPrint, LangGraph nodes, module structure).
