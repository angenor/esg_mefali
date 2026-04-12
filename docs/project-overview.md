# ESG Mefali — Vue d'ensemble du projet

> **Type de projet :** Monorepo multi-parts (Frontend Nuxt 4 + Backend FastAPI)
> **Date de documentation :** 2026-04-12
> **Version applicative :** 0.1.0

## 1. Mission et contexte métier

**ESG Mefali** est une plateforme conversationnelle IA qui démocratise l'accès à la finance durable pour les **PME africaines francophones** (zone UEMOA / CEDEAO).

Elle combine :

- Analyse de **conformité ESG** (Environnement, Social, Gouvernance) contextualisée Afrique
- Conseil en **financement vert** (GCF, FEM, BOAD, BAD, SUNREF, FNDE, etc.)
- **Scoring de crédit alternatif** fondé sur des données non-conventionnelles (Mobile Money, photos IA)
- **Calculateur d'empreinte carbone** avec facteurs d'émission adaptés à l'Afrique de l'Ouest
- **Plan d'action** personnalisé et **gamification** (badges, rappels, timeline)

### Public cible

- PME africaines francophones, y compris secteur informel
- Secteurs : agriculture, énergie, recyclage, transport, industrie légère, services
- Taille : TPE à ETI (moins de 250 employés)

### Référentiels ESG

- Taxonomies vertes UEMOA et BCEAO
- Réglementations CEDEAO
- Standards internationaux : Gold Standard, Verra, REDD+
- Objectifs de Développement Durable ciblés : ODD 8, 9, 10, 12, 13, 17

## 2. Architecture globale

**Type :** Monorepo à 2 parties, communication REST/SSE synchrone.

```
┌──────────────────────────────────┐         ┌──────────────────────────────────┐
│  FRONTEND (Nuxt 4 + Vue 3)       │         │  BACKEND (FastAPI + LangGraph)   │
│                                  │  HTTPS  │                                  │
│  · 18 pages routes               │◄───────►│  · 13 routers REST (~73 endpoints)│
│  · 56 composants Vue             │  + SSE  │  · 9 nœuds LangGraph spécialisés │
│  · 14 composables                │         │  · ~100 tools LangChain          │
│  · 11 stores Pinia               │         │  · 16 modèles SQLAlchemy         │
│  · Chart.js / Mermaid / GSAP     │         │  · Prompts système dynamiques    │
└──────────────────────────────────┘         └──────────────┬───────────────────┘
                                                            │
                                                            ▼
                                             ┌──────────────────────────────┐
                                             │  PostgreSQL 16 + pgvector    │
                                             │  (embeddings RAG documents   │
                                             │   et fonds de financement)   │
                                             └──────────────────────────────┘
                                                            │
                                                            ▼
                                             ┌──────────────────────────────┐
                                             │  OpenRouter (Claude Sonnet 4)│
                                             │  pour chat + tool calling    │
                                             └──────────────────────────────┘
```

## 3. Stack technique synthétique

| Couche | Technologies |
|---|---|
| **Frontend** | Nuxt 4.4, Vue 3 Composition API, TypeScript strict, Pinia 3, TailwindCSS 4, Chart.js 4, GSAP 3, Mermaid 11, Vitest, Playwright |
| **Backend** | Python 3.12, FastAPI ≥0.115, SQLAlchemy async 2, asyncpg, Alembic, Pydantic v2, LangGraph ≥0.2, LangChain Core ≥0.3, WeasyPrint, PyMuPDF, python-docx, Jinja2 |
| **Base de données** | PostgreSQL 16 (image `pgvector/pgvector:pg16`), extension `pgvector` pour embeddings |
| **LLM** | Claude Sonnet 4 (`anthropic/claude-sonnet-4-20250514`) via OpenRouter |
| **Auth** | JWT HS256 (access 8h + refresh 30j), bcrypt, python-jose |
| **Infra** | Docker Compose (3 services : postgres, backend, frontend), nginx reverse proxy en prod |
| **Tests** | Backend : pytest + pytest-asyncio, SQLite in-memory, ~935 tests. Frontend : Vitest (unit) + Playwright (E2E) |

## 4. Modules fonctionnels (8 modules métier)

Chaque module existe **en miroir** entre le frontend (pages + composants + store + composable) et le backend (router + service + nœud LangGraph + prompts + tools).

| # | Module | Rôle | Pages / Routes clés |
|---|---|---|---|
| 1 | **Agent conversationnel** | Chat multimodal FR, profilage entreprise, mémoire contextuelle, SSE streaming, questions interactives (widgets QCU/QCM) | `/chat`, `POST /api/chat/messages` |
| 2 | **Analyseur ESG** | Upload/OCR documents, grille E-S-G contextualisée Afrique, scoring dynamique /100, 30 critères, benchmark sectoriel | `/esg`, `/esg/results`, `/api/esg/*` |
| 3 | **Conseiller Financement Vert** | BDD de 12 fonds réels + 14 intermédiaires, matching projet-financement, générateur de dossiers | `/financing`, `/financing/[id]`, `/api/financing/*` |
| 4 | **Calculateur Carbone** | Questionnaire par catégorie (énergie, transport, déchets, industriel, agriculture), calcul tCO2e scope 1/2/3, plan réduction, benchmark 9 secteurs | `/carbon`, `/carbon/results`, `/api/carbon/*` |
| 5 | **Scoring Crédit Vert** | Données non-conventionnelles (Mobile Money, photos IA), score hybride solvabilité+impact, certificat PDF | `/credit-score`, `/api/credit/*` |
| 6 | **Plan d'Action** | Feuille de route 6-12-24 mois, items catégorisés (environment/social/governance/financing/carbon), rappels cron, bibliothèque de ressources, badges | `/action-plan`, `/api/action-plan/*` |
| 7 | **Tableau de Bord** | Agrégation ESG/carbone/crédit/financement en 4 cartes synthétiques, flux d'activité, prochaines étapes | `/dashboard`, `/api/dashboard/summary` |
| 8 | **Documents & Rapports** | Upload PDF/DOCX/XLSX, OCR, embeddings pgvector, RAG, génération rapports PDF WeasyPrint (ESG, carbone, crédit) | `/documents`, `/reports`, `/api/documents/*`, `/api/reports/*` |

## 5. Flux utilisateur principal

1. Inscription (`/register`) — Détection automatique du pays via IP, initialisation du `CompanyProfile`
2. Connexion (`/login`) — Tokens JWT stockés en `localStorage`
3. Complétion progressive du profil entreprise via le chat (secteur, CA, effectifs, localisation)
4. Dialogue libre ou module spécialisé via le routeur LangGraph (classification d'intent LLM)
5. Upload de documents (pdf, docx, xlsx) → OCR + embeddings pgvector → analyse LLM
6. Évaluation ESG guidée, calcul carbone, matching financement, scoring crédit
7. Génération d'un plan d'action consolidé et de rapports PDF téléchargeables
8. Suivi continu via dashboard, rappels et badges de gamification

## 6. Liens vers la documentation détaillée

- [Architecture Frontend](./architecture-frontend.md)
- [Architecture Backend](./architecture-backend.md)
- [Architecture d'intégration](./integration-architecture.md)
- [Arbre des sources annoté](./source-tree-analysis.md)
- [Inventaire des composants frontend](./component-inventory-frontend.md)
- [Modèles de données backend](./data-models-backend.md)
- [Contrats d'API REST](./api-contracts-backend.md)
- [Guide de développement](./development-guide.md)
- [Guide de déploiement](./deployment-guide.md)
- [Index maître](./index.md)

## 7. Conventions clés

- **Langue du code** : anglais pour identifiants, français pour commentaires
- **Langue UI/UX** : français obligatoire, accents compris (é, è, à, ç, ù…)
- **Dark mode** : obligatoire sur tout nouveau composant, variantes `dark:` Tailwind systématiques
- **Réutilisabilité** : extraire les patterns répétés en `components/ui/`
- **Nommage BDD** : `snake_case` pluriel (ex. `companies`, `esg_scores`)
- **Python venv** : toujours activer `backend/venv` avant toute commande Python
