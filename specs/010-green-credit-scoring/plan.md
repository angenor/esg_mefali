# Implementation Plan: Scoring de Credit Vert Alternatif

**Branch**: `010-green-credit-scoring` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-green-credit-scoring/spec.md`

## Summary

Module de scoring de credit vert alternatif combinant solvabilite (50%) et impact vert (50%) pour les PME africaines francophones. Algorithme hybride integrant les donnees existantes (profil, ESG, carbone, candidatures) et les interactions avec les intermediaires financiers comme signal d'engagement. Inclut visualisations conversationnelles (jauge, radar, progression, mermaid), historique versionne, attestation PDF, et page frontend dediee.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy async, LangGraph, LangChain, WeasyPrint, Jinja2 (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend)
**Storage**: PostgreSQL 16 + pgvector, Alembic pour migrations
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web (serveur Linux, navigateur desktop/mobile)
**Project Type**: Web application (monolithe modulaire FastAPI + Nuxt)
**Performance Goals**: Generation du score < 10s, attestation PDF < 5s
**Constraints**: Donnees sensibles (scores financiers), consentement explicite requis, interface francais
**Scale/Scope**: PME zone UEMOA/CEDEAO, scoring sur 100 points, historique multi-versions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | Interface 100% francais, referentiels UEMOA/BCEAO, secteur informel pris en compte |
| II. Architecture Modulaire | PASS | Module credit isole dans modules/credit/, frontières claires, communication via schemas Pydantic/TypeScript |
| III. Conversation-Driven | PASS | credit_node LangGraph guide l'utilisateur, blocs visuels dans le chat |
| IV. Test-First | PASS | TDD obligatoire, pytest backend, Vitest frontend, couverture 80%+ |
| V. Securite & Donnees | PASS | Schemas Pydantic pour validation, requetes parametrees SQLAlchemy, pas de secrets dans le code, consentement pour donnees scoring |
| VI. Inclusivite | PASS | Messages d'erreur en francais, etats vides guides, recommandations actionnables |
| VII. Simplicite & YAGNI | PASS | Monolithe modulaire, pas de microservice, WeasyPrint existant reutilise, stockage local |

**Gate Result**: PASS — Aucune violation.

## Project Structure

### Documentation (this feature)

```text
specs/010-green-credit-scoring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md           # REST API contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── graph/
│   │   ├── state.py             # + credit_data, _route_credit
│   │   ├── nodes.py             # + credit_node()
│   │   └── graph.py             # + credit node routing
│   ├── models/
│   │   └── credit.py            # CreditScore, CreditDataPoint
│   ├── modules/
│   │   └── credit/
│   │       ├── __init__.py
│   │       ├── router.py        # 5 endpoints REST
│   │       ├── service.py       # Logique calcul scoring
│   │       ├── schemas.py       # Pydantic request/response
│   │       ├── certificate.py   # Generation attestation PDF
│   │       └── certificate_template.html  # Template Jinja2
│   ├── prompts/
│   │   └── credit.py            # Prompt systeme credit_node
│   └── main.py                  # + include credit_router
└── tests/
    └── test_credit/
        ├── test_service.py      # Tests algorithme scoring
        ├── test_router.py       # Tests endpoints API
        ├── test_node.py         # Tests credit_node LangGraph
        └── test_certificate.py  # Tests generation PDF

frontend/
├── app/
│   ├── composables/
│   │   └── useCreditScore.ts    # API composable
│   ├── stores/
│   │   └── creditScore.ts       # Pinia store
│   ├── pages/
│   │   └── credit-score/
│   │       └── index.vue        # Page principale score
│   └── components/
│       └── credit/
│           ├── ScoreGauge.vue       # Jauge circulaire score combine
│           ├── SubScoreGauges.vue   # Deux jauges solvabilite/impact
│           ├── FactorsRadar.vue     # Radar des facteurs
│           ├── DataCoverage.vue     # Progression couverture sources
│           ├── ScoreHistory.vue     # Graphique evolution temporelle
│           ├── Recommendations.vue  # Actions d'amelioration
│           └── CertificateButton.vue # Bouton attestation PDF
└── tests/
    └── credit-score.test.ts     # Tests composable + store
```

**Structure Decision**: Architecture web application conforme au pattern existant (modules/financing, modules/applications). Module backend isole avec router/service/schemas/PDF. Frontend avec page dediee, composable API, store Pinia, et composants specialises.

## Complexity Tracking

> Aucune violation de la constitution — pas de justification necessaire.
