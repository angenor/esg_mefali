# ESG Mefali - Conseiller ESG IA

Plateforme conversationnelle IA qui democratise l'acces a la finance durable pour les PME africaines francophones. Combine analyse de conformite ESG, conseil en financement vert et scoring de credit alternatif.

## Stack Technologique

### Frontend (Nuxt 4)
- **Framework** : Nuxt 4 + Vue Composition API
- **State** : Pinia
- **UI** : TailwindCSS + GSAP (animations)
- **Editeur** : toast-ui/editor
- **Graphiques** : Chart.js
- **IA Client** : LangGraph + LangChain (couche utilitaire)

### Backend (FastAPI)
- **Framework** : FastAPI (Python)
- **LLM** : Claude API (Anthropic) via OpenRouter
- **BDD** : PostgreSQL + pgvector (embeddings)
- **Stockage** : Local (MinIO/S3 plus tard)
- **Queue** : Synchrone (Redis + Celery plus tard)

## Architecture Modulaire

Le projet est organise en 8 modules :

1. **Agent Conversationnel** — Chat multimodal FR, profilage entreprise, memoire contextuelle
2. **Analyseur Conformite ESG** — Upload/OCR documents, grille E-S-G contextualisee Afrique, scoring dynamique /100, rapport PDF
3. **Conseiller Financement Vert** — BDD fonds (GCF, FEM, BOAD, BAD...), matching projet-financement, generateur de dossiers
4. **Calculateur Empreinte Carbone** — Questionnaire adapte contexte africain, calcul tCO2e, plan de reduction
5. **Scoring Credit Vert Alternatif** — Donnees non-conventionnelles (Mobile Money, photos IA), score hybride solvabilite+impact
6. **Plan d'Action** — Feuille de route 6-12-24 mois, rappels cron, bibliotheque ressources
7. **Tableau de Bord** — Dashboard scores, rapports exports, multi-utilisateurs (admin/collaborateur/lecteur)
8. **Extension Chrome** — Detection fonds, pre-remplissage formulaires, panneau guidage, suivi candidatures

## Conventions de Developpement

### Langue
- Code : anglais (variables, fonctions, classes)
- Commentaires : francais
- UI/UX : francais (interface utilisateur)
- Documentation : francais

### Frontend (Nuxt 4)
- Composition API avec `<script setup lang="ts">`
- Composables dans `composables/`
- Pages dans `pages/` avec routing automatique Nuxt
- Composants dans `components/` avec nommage PascalCase (sans prefixe de dossier, `pathPrefix: false`)
- Stores Pinia dans `stores/`
- Structure Nuxt 4 : tous les fichiers source dans `app/` (pages, components, composables, layouts, stores, etc.)

### Dark Mode (OBLIGATOIRE)
Chaque nouveau composant, page ou layout DOIT etre compatible dark mode :
- Utiliser les variantes `dark:` de Tailwind sur tous les elements visuels
- Fonds : `bg-white dark:bg-dark-card`, `bg-surface-bg dark:bg-surface-dark-bg`
- Textes : `text-surface-text dark:text-surface-dark-text`, `text-gray-600 dark:text-gray-400`
- Bordures : `border-gray-200 dark:border-dark-border`
- Inputs : `dark:bg-dark-input dark:text-surface-dark-text`
- Hover : `hover:bg-gray-50 dark:hover:bg-dark-hover`
- Le theme est gere par `stores/ui.ts` (classe `dark` sur `<html>`, persiste dans localStorage)
- Les variables de couleurs dark sont definies dans `app/assets/css/main.css` via `@theme`
- Ne jamais hardcoder des couleurs claires sans leur equivalente dark

### Reutilisabilite des Composants (OBLIGATOIRE)
- Avant de creer un nouveau composant, verifier si un composant existant peut etre reutilise ou etendu via des props
- Extraire les patterns visuels repetes (cartes, formulaires, boutons, inputs) en composants generiques dans `components/ui/`
- Les composants UI de base (boutons, inputs, badges, modals) doivent etre parametrables via props et slots, pas dupliques
- Privilegier la composition (slots, props, emit) plutot que la duplication de code
- Si un meme pattern apparait plus de 2 fois, l'extraire en composant reutilisable

### Backend (FastAPI)
- Routers dans `routers/`
- Services/logique metier dans `services/`
- Modeles SQLAlchemy dans `models/`
- Schemas Pydantic dans `schemas/`
- snake_case pour les fonctions et variables Python

### Base de Donnees
- Migrations avec Alembic
- Nommage tables : snake_case, pluriel (ex: `companies`, `esg_scores`)
- pgvector pour les embeddings de documents

## Contexte Metier

### Public Cible
- PME africaines francophones (zone UEMOA/CEDEAO)
- Secteurs : agriculture, energie, recyclage, transport, etc.
- Secteur informel pris en compte

### Referentiels ESG
- Taxonomies vertes UEMOA, BCEAO
- Reglementations CEDEAO
- Standards internationaux : Gold Standard, Verra, REDD+

### ODD Cibles
- ODD 8 (Travail decent), ODD 9 (Innovation), ODD 10 (Inclusion financiere)
- ODD 12 (Production responsable), ODD 13 (Climat), ODD 17 (Partenariats)

## Environnement Python

Le backend utilise un environnement virtuel Python (`venv`). Toujours l'activer avant d'executer des commandes Python ou d'installer des packages.

```bash
# Creation (une seule fois)
cd backend && python3 -m venv venv

# Activation (a chaque session)
source backend/venv/bin/activate

# Installation des dependances
pip install -r backend/requirements.txt
```

**Important** : Ne jamais installer de packages Python globalement. Toujours verifier que le venv est actif (`which python` doit pointer vers `backend/venv/bin/python`).

## Commandes Utiles

```bash
# Frontend
cd frontend && npm run dev

# Backend (toujours activer le venv d'abord)
source venv/bin/activate
uvicorn app.main:app --reload

# Base de donnees
alembic upgrade head
```

## Active Technologies
- Python 3.12, TypeScript 5.x (strict mode) (001-technical-foundation)
- PostgreSQL 16 + pgvector (001-technical-foundation)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) (002-chat-rich-visuals)
- PostgreSQL 16 + pgvector (async via asyncpg) (002-chat-rich-visuals)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, LangGraph, LangChain, SQLAlchemy (async), Nuxt 4, Vue Composition API, Pinia, TailwindCSS (003-company-profiling-memory)
- PostgreSQL 16 + pgvector (async via asyncpg), Alembic pour migrations (003-company-profiling-memory)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, LangGraph, LangChain, SQLAlchemy (async), PyMuPDF, pytesseract, pdf2image, docx2txt, openpyxl, Nuxt 4, Vue Composition API, Pinia, TailwindCSS (004-document-upload-analysis)
- PostgreSQL 16 + pgvector (embeddings), stockage fichiers local (/uploads/) (004-document-upload-analysis)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, LangGraph, LangChain, SQLAlchemy async, PyMuPDF, Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (005-esg-scoring-assessment)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, WeasyPrint, matplotlib, Jinja2, LangChain (resume IA), SQLAlchemy async, Nuxt 4, Vue Composition API, Pinia, TailwindCSS (006-esg-pdf-reports)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, SQLAlchemy async, LangGraph, LangChain, Claude API via OpenRouter (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend) (007-carbon-footprint-calculator)
- PostgreSQL 16 + pgvector, Alembic pour migrations (007-carbon-footprint-calculator)
- Python 3.12 (backend), TypeScript 5.x strict (frontend) + FastAPI, SQLAlchemy async, LangGraph, LangChain, WeasyPrint, Jinja2 (backend) ; Nuxt 4, Vue Composition API, Pinia, TailwindCSS, Chart.js, vue-chartjs (frontend) (008-green-financing-matching)
- PostgreSQL 16 + pgvector (embeddings), Alembic pour migrations (008-green-financing-matching)

## Recent Changes
- 008-green-financing-matching: Module conseiller financement vert (BDD 12 fonds reels GCF/FEM/BOAD/BAD/SUNREF/FNDE/etc + 14 intermediaires avec coordonnees + ~50 liaisons fund-intermediary, matching projet-financement par scoring multi-criteres secteur/ESG/taille/localisation/documents, parcours d'acces direct vs intermediaire avec etapes LLM, catalogue fonds filtrable type/secteur/montant/acces/statut, annuaire intermediaires filtrable type/pays, workflow interet→choix intermediaire→fiche preparation PDF WeasyPrint, financing_node LangGraph avec RAG pgvector + blocs visuels mermaid/table/progress/timeline, API REST /api/financing 10+ endpoints, pages /financing liste 3 onglets + /financing/[id] detail fonds, embeddings text-embedding-3-small, dark mode complet, gestion etats vides/erreurs)
- 007-carbon-footprint-calculator: Module calculateur empreinte carbone conversationnel (questionnaire guide par categorie energie/transport/dechets/industriel/agriculture, facteurs emission Afrique Ouest, equivalences parlantes FCFA, carbon_node LangGraph avec visualisations inline chart/gauge/table/timeline, API REST /api/carbon 6 endpoints, page /carbon liste bilans + /carbon/results dashboard donut/barres/equivalences/plan reduction/benchmark sectoriel/evolution temporelle, benchmarks 9 secteurs avec fallback, contrainte unicite bilan/annee, reprise bilans interrompus, dark mode, 57 tests)
- 006-esg-pdf-reports: Module generation rapports ESG PDF (WeasyPrint HTML->PDF, graphiques matplotlib SVG, resume executif IA Claude, template 9 sections, conformite UEMOA/BCEAO/ODD, API REST /api/reports, page /reports liste+preview+download, notification chat SSE, dark mode, edge cases generation simultanee)
- 005-esg-scoring-assessment: Module evaluation et scoring ESG complet (30 criteres E-S-G, ponderation sectorielle, scoring dynamique, esg_scoring_node LangGraph, API REST /api/esg, page resultats /esg, RAG documentaire par critere, benchmark sectoriel avec fallback, historique evaluations Chart.js, reprise evaluations interrompues, 71 tests, 80% couverture)
- 004-document-upload-analysis: Module complet upload/analyse documents (PyMuPDF, pytesseract, OCR, embeddings pgvector, chat integration, dark mode, 81% couverture tests)
- 001-technical-foundation: Added Python 3.12, TypeScript 5.x (strict mode)
