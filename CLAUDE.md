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
- Composants dans `components/` avec nommage PascalCase
- Stores Pinia dans `stores/`

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

## Commandes Utiles

```bash
# Frontend
cd frontend && npm run dev

# Backend
cd backend && uvicorn app.main:app --reload

# Base de donnees
alembic upgrade head
```
