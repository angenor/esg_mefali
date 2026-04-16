# ESG Mefali — Vue d'ensemble du projet

> **Type de projet :** Monorepo multi-parts (Frontend Nuxt 4 + Backend FastAPI)
> **Dernière mise à jour :** 2026-04-16
> **Langue de documentation :** Français (code et identifiants en anglais)

## 1. Mission et contexte produit

**ESG Mefali** est une plateforme conversationnelle IA qui démocratise l'accès à la finance durable pour les PME africaines francophones. Elle combine :

1. **Analyse de conformité ESG** adaptée au contexte africain (UEMOA, BCEAO, CEDEAO, ODD 8/9/10/12/13/17).
2. **Conseil en financement vert** avec une base de 12 fonds réels (GCF, FEM, BOAD, BAD, SUNREF, FNDE…) et un catalogue d'intermédiaires.
3. **Scoring de crédit vert alternatif** basé sur des données non conventionnelles (Mobile Money, photos IA).
4. **Calcul d'empreinte carbone** contextualisé Afrique de l'Ouest, avec équivalences parlantes en FCFA.
5. **Plan d'action** personnalisé (6/12/24 mois) avec rappels et badges.
6. **Dashboard** agrégé multi-modules.

**Public cible** : PME francophones zone UEMOA/CEDEAO, secteurs agriculture, énergie, recyclage, transport ; le secteur informel est explicitement pris en compte.

## 2. Stack technique

### Frontend — Nuxt 4

| Couche | Techno |
|---|---|
| Framework | Nuxt 4.4 + Vue 3 Composition API |
| Langage | TypeScript 5 (strict) |
| State | Pinia 3 |
| Styling | TailwindCSS 4 + dark mode (`@theme`) |
| Animations | GSAP |
| Tours guidés | driver.js (lazy-loadé) |
| Charts | Chart.js + vue-chartjs |
| Diagrammes | Mermaid |
| Tests | Vitest (unit) + Playwright (E2E mocké) + bash (E2E live) |

### Backend — FastAPI

| Couche | Techno |
|---|---|
| Framework | FastAPI 0.115 (async) |
| Langage | Python 3.12 |
| ORM | SQLAlchemy 2 async + asyncpg |
| Migrations | Alembic |
| Base de données | PostgreSQL 16 + pgvector |
| LLM orchestration | LangGraph 0.2 + LangChain 0.3 |
| LLM provider | OpenRouter (Claude Sonnet 4) |
| Auth | JWT HS256 (python-jose + bcrypt) |
| Documents | PyMuPDF + pytesseract + pdf2image + docx2txt + openpyxl |
| PDF output | WeasyPrint + Jinja2 + matplotlib |
| Tests | pytest 8 + pytest-asyncio + pytest-cov |

### Infrastructure

- **Conteneurisation** : Docker Compose (dev + prod).
- **Reverse proxy** (prod) : nginx UAfricas (multi-tenant, mutualisé).
- **Déploiement** : `deploy.sh` (SSH root, certificats Let's Encrypt automatisés).

## 3. Classification

- **Type de dépôt** : monorepo.
- **Parties** : 2 (frontend + backend) — déploiement conjoint.
- **Architecture** : client-serveur classique, orchestration LLM côté serveur, streaming SSE unidirectionnel.
- **Pattern** : modulaire par domaine métier (10 modules backend, composition identique côté frontend).

## 4. Chiffres clés

| Indicateur | Valeur |
|---|---|
| Endpoints REST | 73 |
| Nœuds LangGraph | 9 |
| Tools LangChain | ~36 répartis dans 12 fichiers |
| Modèles ORM | 22 classes |
| Migrations Alembic | 13 |
| Prompts modules | 11 |
| Pages frontend | 17 |
| Composants Vue | 60 |
| Composables | 18 |
| Stores Pinia | 11 |
| Tours guidés | 6 |
| Tests backend | ~50 fichiers (~935 assertions cible) |
| Tests frontend unitaires | ~37 fichiers |
| Tests E2E Playwright | 2 parcours + 1 parcours live (shell) |

## 5. Journal des grandes évolutions

Historique synthétique (voir `specs/001` à `018` + commits post-018 pour le détail) :

| Spec | Module livré |
|---|---|
| 001 | Fondation technique |
| 002 | Chat avec visualisations enrichies |
| 003 | Profilage entreprise + mémoire conversationnelle |
| 004 | Upload + analyse documents (OCR + embeddings pgvector) |
| 005 | Scoring ESG 30 critères + benchmark sectoriel |
| 006 | Rapports ESG PDF (WeasyPrint + matplotlib) |
| 007 | Calculateur empreinte carbone |
| 008 | Matching financement vert |
| 009 | Générateur dossiers de candidature |
| 010 | Scoring crédit vert |
| 011 | Dashboard + plan d'action + badges |
| 012 | Tool calling LangGraph (migration) |
| 013 | Fix routage multi-tour (`active_module`) + format timeline |
| 014 | Style de communication concis |
| 015 | Fix tool calling ESG + timeout + `create_fund_application` + `batch_save_esg_criteria` |
| 016 | Fix persistance tool calls |
| 017 | Fix tests failing |
| 018 | Widgets interactifs (QCU / QCM / justification) |
| 019 | Tour guidé (driver.js) + JWT transparent + SSE resilience + chat widget flottant |

## 6. Décisions architecturales majeures

- **LangGraph au cœur** : le backend expose une API REST classique, mais le chat est piloté par un graphe compilé à 9 nœuds + tool calling avec boucle (max 5 itérations).
- **SSE via fetch streaming** : pas d'`EventSource` (pour pouvoir poster FormData + Authorization). Reader partagé au niveau module côté frontend (`useChat.ts`).
- **Widget flottant** : depuis la spec 019, la page `/chat` n'existe plus — le chat est accessible sur toutes les pages via le widget, le contexte de page courante est transmis au backend pour adaptation du prompt.
- **Tours guidés consentis** : un widget interactif QCU yes/no précède chaque tour. Le comptage d'acceptation/refus module la fréquence des propositions (cap 5 refus).
- **Persistance des widgets interactifs** : table satellite `interactive_questions`, invariant d'une seule question pending par conversation.
- **Multi-turn routing** : champs `active_module` + `active_module_data` dans l'état LangGraph pour ne pas perdre le contexte sur les flux ESG/carbon longs (spec 013).

## 7. Conventions projet (rappel)

- **Langue** : UI + doc en français accentué (é, è, ê, à, ç, ù…). Code et identifiants en anglais. Tables en snake_case pluriel.
- **Nuxt 4** : toutes les sources dans `frontend/app/`.
- **Dark mode** : obligatoire sur chaque composant (`dark:` variants Tailwind, variables `@theme`).
- **Réutilisation** : pattern > 2 occurrences ⇒ extraction en composant `ui/` ou composable.
- **Python venv** : jamais d'installation globale, `source backend/venv/bin/activate` à chaque session.

## 8. Liens vers la documentation détaillée

- [index.md](./index.md) — master index de navigation
- [source-tree-analysis.md](./source-tree-analysis.md) — arborescence annotée
- [architecture-frontend.md](./architecture-frontend.md) — architecture Nuxt 4
- [architecture-backend.md](./architecture-backend.md) — architecture FastAPI + LangGraph
- [integration-architecture.md](./integration-architecture.md) — contrats frontend ↔ backend
- [api-contracts-backend.md](./api-contracts-backend.md) — endpoints REST + SSE
- [data-models-backend.md](./data-models-backend.md) — schéma BDD complet
- [component-inventory-frontend.md](./component-inventory-frontend.md) — catalogue composants/composables/stores
- [development-guide.md](./development-guide.md) — setup + commandes + conventions
- [deployment-guide.md](./deployment-guide.md) — procédures prod + nginx + SSL
- [technical-debt-backlog.md](./technical-debt-backlog.md) — dette technique priorisée

## 9. Prise en main rapide

```bash
git clone <repo> && cd esg_mefali
cp .env.example .env       # Éditer OPENROUTER_API_KEY
make dev                   # Postgres + Backend + Frontend via Docker
make migrate               # Applique les migrations Alembic
# Ouvrir http://localhost:3000 et créer un compte
```

Voir [development-guide.md](./development-guide.md) pour les alternatives sans Docker.
