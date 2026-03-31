# Implementation Plan: Calculateur d'Empreinte Carbone Conversationnel

**Branch**: `007-carbon-footprint-calculator` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-carbon-footprint-calculator/spec.md`

## Summary

Implemente le Module 4 (Calculateur d'Empreinte Carbone) : un questionnaire conversationnel guide par l'IA qui collecte les donnees d'emissions par categorie, calcule le bilan carbone en tCO2e avec les facteurs d'emission Afrique de l'Ouest, et affiche des visualisations progressives inline dans le chat (barres, donut, jauge, tableaux, timeline). Inclut une page de resultats persistante, un plan de reduction personnalise avec chiffrage FCFA, et une comparaison sectorielle.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy async, LangGraph, LangChain, Claude API via OpenRouter (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend)
**Storage**: PostgreSQL 16 + pgvector, Alembic pour migrations
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web (navigateur desktop/mobile)
**Project Type**: web-service (monolithe modulaire FastAPI + Nuxt)
**Performance Goals**: Reponse conversationnelle < 3s, graphiques inline < 2s apres reponse
**Constraints**: Facteurs d'emission specifiques Afrique de l'Ouest, unites locales (FCFA, litres, km)
**Scale/Scope**: PME africaines francophones, ~5 categories d'emissions, bilans annuels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | UI en francais, unites FCFA/litres/km, referentiels UEMOA |
| II. Architecture Modulaire | PASS | Module carbon isole dans modules/carbon/, noeud dedie carbon_node |
| III. Conversation-Driven UX | PASS | Collecte via questionnaire conversationnel dans le chat |
| IV. Test-First | PASS | Tests ecrits avant implementation (TDD) |
| V. Securite & Donnees | PASS | Validation Pydantic, SQLAlchemy ORM parametrise |
| VI. Inclusivite | PASS | Questions simples, unites locales, equivalences parlantes |
| VII. Simplicite & YAGNI | PASS | Pas de microservice, traitement synchrone, facteurs en constantes |

## Project Structure

### Documentation (this feature)

```text
specs/007-carbon-footprint-calculator/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API endpoints)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── graph/
│   │   ├── nodes.py          # + carbon_node() ajout
│   │   └── state.py          # + carbon_data dans ConversationState
│   ├── models/
│   │   ├── __init__.py        # + imports carbon models
│   │   └── carbon.py          # NEW: CarbonAssessment, CarbonEmissionEntry
│   ├── modules/
│   │   └── carbon/            # NEW: module complet
│   │       ├── __init__.py
│   │       ├── router.py      # Endpoints REST /api/carbon/*
│   │       ├── service.py     # Logique metier calculs emissions
│   │       ├── schemas.py     # Schemas Pydantic requete/reponse
│   │       ├── emission_factors.py  # Constantes facteurs emission AO
│   │       └── benchmarks.py  # Donnees benchmarks sectoriels
│   ├── prompts/
│   │   └── carbon.py          # NEW: Prompt systeme carbon_node
│   └── main.py               # + inclusion carbon_router
├── alembic/
│   └── versions/
│       └── 007_add_carbon_tables.py  # NEW: migration
└── tests/
    ├── test_carbon_service.py    # NEW: tests unitaires service
    ├── test_carbon_router.py     # NEW: tests integration endpoints
    └── test_carbon_node.py       # NEW: tests noeud LangGraph

frontend/
├── app/
│   ├── pages/
│   │   └── carbon/
│   │       ├── index.vue      # NEW: liste des bilans
│   │       └── results.vue    # NEW: dashboard resultats
│   ├── composables/
│   │   └── useCarbon.ts       # NEW: API calls carbon
│   ├── types/
│   │   └── carbon.ts          # NEW: types TypeScript carbon
│   ├── stores/
│   │   └── carbon.ts          # NEW: store Pinia carbon
│   └── components/
│       └── layout/
│           └── AppSidebar.vue # + entree navigation "Empreinte Carbone"
```

**Structure Decision**: Suit le pattern modulaire existant (modules/esg/ comme reference). Le module carbon/ suit exactement la meme organisation que esg/ (router, service, schemas) avec l'ajout de fichiers specifiques pour les facteurs d'emission et benchmarks.

## Phase 0: Research

### Decisions

1. **Facteurs d'emission** : Utiliser les facteurs fournis dans la spec (source : grilles ADEME adaptees Afrique de l'Ouest). Extensibles via le fichier emission_factors.py.
2. **Categories d'emissions** : 5 categories principales alignees sur le GHG Protocol simplifie : Energie (electricite, generateurs), Transport (vehicules, deplacements), Dechets, Processus industriels (si applicable), Agriculture (si applicable).
3. **Pattern du carbon_node** : Suit exactement le pattern du esg_scoring_node existant — machine a etats dans le ConversationState avec progression par categorie, stockage partiel en JSON, visualisations inline via blocs chart/gauge/table/timeline.
4. **Benchmarks sectoriels** : Donnees estimees stockees en constantes Python (comme esg/weights.py), pas de source externe.
5. **Equivalences parlantes** : Calcul base sur des constantes connues (1 vol Paris-Dakar ≈ 1.2 tCO2e, 1 an de voiture ≈ 2.4 tCO2e, etc.).

### Patterns existants reutilises

| Pattern | Source | Reutilisation |
|---------|--------|---------------|
| Module structure | modules/esg/ | router.py, service.py, schemas.py |
| LangGraph node | graph/nodes.py → esg_scoring_node | carbon_node avec meme pattern etat |
| ConversationState extension | graph/state.py | + champ carbon_data: dict |
| Router node routing | graph/nodes.py → router_node | + detection intent carbone |
| Prompt template | prompts/esg_scoring.py | Template carbone avec instructions visuelles |
| Frontend page | pages/esg/ | pages/carbon/ (index + results) |
| Composable | composables/useEsg.ts | useCarbon.ts meme structure |
| Types | types/esg.ts | types/carbon.ts |
| Migration | alembic/versions/006_* | 007_add_carbon_tables.py |
| Sidebar nav | AppSidebar.vue navItems | + entree Empreinte Carbone |

## Phase 1: Design

### Architecture des composants

```
Chat Input → router_node (detect carbon intent)
                ↓
          carbon_node ←→ CarbonService
                ↓              ↓
        Reponse chat      Persist to DB
        + blocs visuels   (CarbonAssessment + entries)
                ↓
        Frontend renders
        (ChartBlock, GaugeBlock, TableBlock, TimelineBlock)
```

### Flux conversationnel du carbon_node

```
1. Detection intent → Creer CarbonAssessment (status: in_progress)
2. Categorie ENERGIE
   - Questions: consommation electrique (kWh/mois ou FCFA), generateur (litres diesel/mois)
   - Calcul → CarbonEmissionEntry
   - Afficher: ```chart (bar horizontal) emissions par categorie
3. Categorie TRANSPORT
   - Questions: vehicules (litres essence/gasoil par mois), deplacements
   - Calcul → CarbonEmissionEntry
   - Afficher: ```chart (bar horizontal) mis a jour
4. Categorie DECHETS
   - Questions: volume dechets, type traitement
   - Calcul → CarbonEmissionEntry
   - Afficher: ```chart (bar horizontal) mis a jour
5. [Optionnel] PROCESSUS INDUSTRIELS / AGRICULTURE selon secteur
6. FINALISATION
   - Afficher: ```chart (doughnut) repartition par source
   - Afficher: ```gauge total tCO2e + equivalence
   - Afficher: ```table plan de reduction
   - Afficher: ```chart (bar) comparaison sectorielle
   - Afficher: ```timeline plan d'action temporel
   - Mettre a jour CarbonAssessment (status: completed, total_emissions_tco2e)
```

### Facteurs d'emission (emission_factors.py)

```python
EMISSION_FACTORS = {
    "electricity_ci": {"factor": 0.41, "unit": "kgCO2e/kWh", "label": "Electricite (reseau CI)"},
    "diesel_generator": {"factor": 2.68, "unit": "kgCO2e/L", "label": "Generateur diesel"},
    "gasoline": {"factor": 2.31, "unit": "kgCO2e/L", "label": "Essence"},
    "diesel_transport": {"factor": 2.68, "unit": "kgCO2e/L", "label": "Gasoil"},
    "butane_gas": {"factor": 2.98, "unit": "kgCO2e/kg", "label": "Gaz butane"},
    "waste_landfill": {"factor": 0.5, "unit": "kgCO2e/kg", "label": "Dechets (enfouissement)"},
    "waste_incineration": {"factor": 1.1, "unit": "kgCO2e/kg", "label": "Dechets (incineration)"},
}

EQUIVALENCES = {
    "flight_paris_dakar": {"value": 1.2, "unit": "tCO2e", "label": "vol Paris-Dakar"},
    "car_year_avg": {"value": 2.4, "unit": "tCO2e", "label": "annee de conduite moyenne"},
    "tree_year_absorption": {"value": 0.025, "unit": "tCO2e", "label": "arbre absorbe par an"},
}
```

### Etat carbone dans ConversationState

```python
# carbon_data dans ConversationState
{
    "assessment_id": "uuid",
    "status": "in_progress",  # in_progress | completed
    "current_category": "energy",  # energy | transport | waste | industrial | agriculture
    "completed_categories": ["energy"],
    "entries": [
        {
            "category": "energy",
            "subcategory": "electricity",
            "quantity": 500,
            "unit": "kWh",
            "emission_factor": 0.41,
            "emissions_tco2e": 0.205
        }
    ],
    "total_emissions_tco2e": 0.205,
    "sector": "agriculture"
}
```

### Constitution Check (Post-Design)

| Principe | Statut | Notes |
|----------|--------|-------|
| I. Francophone-First | PASS | Questions en FR, unites locales, equivalences contextualisees |
| II. Architecture Modulaire | PASS | Module carbon/ isole, schemas Pydantic, types TS dedies |
| III. Conversation-Driven UX | PASS | Questionnaire via chat, pas de formulaire |
| IV. Test-First | PASS | Tests prevus avant implementation |
| V. Securite & Donnees | PASS | Validation Pydantic, ORM parametrise, pas de donnees sensibles |
| VI. Inclusivite | PASS | Unites FCFA/litres, equivalences parlantes, questions simples |
| VII. Simplicite & YAGNI | PASS | Facteurs en constantes, pas de service externe, benchmarks estimes |

## Complexity Tracking

> Aucune violation de la constitution. Pas de complexite additionnelle non justifiee.
