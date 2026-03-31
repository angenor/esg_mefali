# Implementation Plan: Génération de Rapports ESG en PDF

**Branch**: `006-esg-pdf-reports` | **Date**: 2026-03-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-esg-pdf-reports/spec.md`

## Summary

Transformer les résultats d'évaluation ESG en rapports PDF professionnels téléchargeables. Le module utilise WeasyPrint (HTML → PDF) avec des graphiques matplotlib rendus en SVG inline. Le rapport de 5-10 pages comprend 9 sections : couverture, résumé exécutif IA, scores détaillés avec radar chart, points forts, axes d'amélioration, benchmarking sectoriel, conformité UEMOA/BCEAO, plan d'action et méthodologie.

## Technical Context

**Language/Version** : Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies** : FastAPI, SQLAlchemy async, WeasyPrint, matplotlib, Jinja2, LangChain (résumé IA), Nuxt 4, Vue Composition API, Pinia, TailwindCSS
**Storage** : PostgreSQL 16 + pgvector (métadonnées rapport), stockage fichier local (`/uploads/reports/`)
**Testing** : pytest (backend), Vitest (frontend)
**Target Platform** : Web (serveur Linux/macOS)
**Project Type** : Web application (monolithe modulaire)
**Performance Goals** : Génération PDF < 30 secondes (incluant appel LLM pour résumé exécutif)
**Constraints** : PDF 5-10 pages, graphiques lisibles en A4, français uniquement, génération synchrone
**Scale/Scope** : PME individuelles, ~10 rapports/jour max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Détail |
|----------|--------|--------|
| I. Francophone-First | PASS | Rapport entièrement en français, référentiels UEMOA/BCEAO intégrés |
| II. Architecture Modulaire | PASS | Nouveau module `reports/` avec frontières claires, communique via schemas Pydantic |
| III. Conversation-Driven UX | PASS | Notification dans le chat avec lien de téléchargement (P3) |
| IV. Test-First | PASS | TDD prévu : tests unitaires (service, charts), intégration (API), E2E (frontend) |
| V. Sécurité & Données | PASS | Accès rapport limité à l'utilisateur propriétaire, validation entrées, pas de secrets |
| VI. Inclusivité | PASS | PDF universel, lisible offline, messages d'erreur en français |
| VII. Simplicité & YAGNI | PASS | Stockage local, génération synchrone, pas de queue async, WeasyPrint seul |

## Project Structure

### Documentation (this feature)

```text
specs/006-esg-pdf-reports/
├── plan.md              # Ce fichier
├── spec.md              # Spécification
├── research.md          # Recherche Phase 0
├── data-model.md        # Modèle de données Phase 1
├── quickstart.md        # Guide démarrage rapide
├── contracts/           # Contrats API
│   └── api.md           # Endpoints REST
├── checklists/
│   └── requirements.md  # Checklist qualité spec
└── tasks.md             # Tâches (Phase 2 - /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── report.py                  # Modèle SQLAlchemy Report
│   ├── modules/
│   │   └── reports/
│   │       ├── __init__.py
│   │       ├── router.py              # Endpoints API reports
│   │       ├── schemas.py             # Schemas Pydantic
│   │       ├── service.py             # Logique métier génération
│   │       ├── charts.py              # Génération graphiques matplotlib SVG
│   │       └── templates/
│   │           ├── esg_report.html    # Template Jinja2 du rapport
│   │           └── esg_report.css     # Styles CSS print
│   └── prompts/
│       └── esg_report.py             # Prompts LangChain résumé exécutif
├── alembic/versions/
│   └── 006_add_reports_table.py       # Migration
├── uploads/reports/                    # Stockage PDF générés
└── tests/
    ├── test_report_service.py         # Tests unitaires service
    ├── test_report_charts.py          # Tests unitaires charts
    └── test_report_router.py          # Tests intégration API

frontend/app/
├── pages/
│   └── reports/
│       └── index.vue                  # Liste des rapports
├── components/
│   └── esg/
│       └── ReportButton.vue           # Bouton génération + progression
├── composables/
│   └── useReports.ts                  # Composable API reports
└── types/
    └── report.ts                      # Types TypeScript
```

**Structure Decision** : Nouveau module `reports/` dans la structure modulaire existante, suivant le pattern router/schemas/service des modules `esg/`, `documents/` et `company/`. Les templates HTML/CSS du rapport sont dans le module reports car ils sont spécifiques à la génération PDF (pas des assets frontend).

## Complexity Tracking

Aucune violation de constitution détectée. Pas de justification requise.
