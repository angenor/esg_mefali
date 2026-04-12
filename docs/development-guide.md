# Guide de développement — ESG Mefali

## 1. Prérequis

| Outil | Version minimale | Usage |
|---|---|---|
| Docker Desktop | 4.20+ | Dev via `docker compose` |
| Git | 2.40+ | |
| Node.js | 24.x (LTS récent) | Dev frontend local |
| Python | **3.12** (préférence projet) | Dev backend local |
| PostgreSQL | 16 + pgvector | Optionnel si hors Docker |
| Make | | `make dev`, `make test`, ... |

> **⚠️ venv local actuellement basé sur Python 3.14** — les rules projet recommandent 3.12. À harmoniser lors de la prochaine revue de dépendances.

## 2. Installation rapide (Docker)

```bash
# 1. Cloner le dépôt
git clone <repo-url>
cd esg_mefali

# 2. Copier la configuration
cp .env.example .env

# 3. Éditer .env et ajouter OPENROUTER_API_KEY (obligatoire pour le chat IA)
#    Modifier SECRET_KEY en production

# 4. Lancer les 3 services (postgres + backend + frontend)
make dev
```

Services disponibles :

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Redoc | http://localhost:8000/redoc |
| PostgreSQL | `localhost:5432` (user `postgres` / password `postgres` / db `esg_mefali`) |

## 3. Commandes Makefile

```bash
make dev          # Démarre Docker Compose (postgres + backend + frontend)
make build        # Build de production
make migrate      # Exécute alembic upgrade head dans le container backend
make test         # Tests backend + frontend
make test-back    # Tests backend seulement (pytest + couverture)
make test-front   # Tests frontend seulement (vitest)
make down         # Stop les services
make logs         # Stream logs des 3 services
make clean        # Stop + suppression des volumes (⚠️ efface la BDD)
```

## 4. Variables d'environnement

Fichier `.env` (à la racine) :

```env
# Base de données
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/esg_mefali

# Sécurité
SECRET_KEY=changez-cette-cle-en-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60      # Dev ; prod recommandé 480 (8h)
REFRESH_TOKEN_EXPIRE_DAYS=30

# IA (OpenRouter)
OPENROUTER_API_KEY=votre-cle-openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514

# Frontend
NUXT_PUBLIC_API_BASE=http://localhost:8000/api
```

> Les variables `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` sont supportées en alias pour rétro-compatibilité (mapping dans `Settings.model_post_init`).

## 5. Développement local (sans Docker)

### 5.1 Backend

```bash
cd backend

# Création du venv (une seule fois)
python3.12 -m venv venv

# Activation à chaque session
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt -r requirements-dev.txt

# Vérifier que le bon Python est actif
which python                       # doit pointer vers backend/venv/bin/python

# Lancer un PostgreSQL pgvector en local (via Docker)
docker compose up postgres -d

# Migrations
alembic upgrade head

# Démarrer le serveur en hot-reload
uvicorn app.main:app --reload --port 8000
```

> **Règle projet** : ne jamais installer de packages Python globalement — toujours dans le venv.

### 5.2 Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Si le backend est hors Docker, pointer le frontend via :

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000/api npm run dev
```

## 6. Base de données

- **Image Docker** : `pgvector/pgvector:pg16`
- **Extension** : `CREATE EXTENSION IF NOT EXISTS vector` (appliquée par la 1ʳᵉ migration)
- **Migrations** : `alembic/versions/` — 13 migrations au 2026-04-12
- **Nommage** : tables `snake_case` pluriel (`companies`, `esg_scores`, `carbon_assessments`)

### Créer une migration

```bash
cd backend
source venv/bin/activate

# Après modification d'un modèle SQLAlchemy
alembic revision --autogenerate -m "add xyz column"

# Relire le fichier généré (autogenerate n'est pas parfait)
# puis appliquer
alembic upgrade head
```

## 7. Tests

### 7.1 Backend — pytest asynchrone

Config : `backend/pytest.ini` (`asyncio_mode=auto`).

```bash
cd backend
source venv/bin/activate

# Tous les tests avec couverture
pytest tests/ -v --cov=app --cov-report=term-missing

# Un seul fichier
pytest tests/test_esg_scoring.py -v

# Un seul test
pytest tests/test_chat.py::test_streaming_sse -v

# Via Make (dans Docker)
make test-back
```

Cible de couverture : **80 %** (rule `common/testing.md`).

### 7.2 Frontend — Vitest + Playwright

```bash
cd frontend
npm run test            # Vitest unit tests
npm run test:e2e        # Playwright E2E (framework prêt, scénarios à ajouter)
```

> **Dette actuelle** : la couverture frontend est très faible (2 tests unitaires). À renforcer — feature TDD recommandée.

### 7.3 Workflow TDD

Suivre la rule `common/testing.md` :

1. Écrire le test (RED) → le test doit échouer
2. Implémenter (GREEN) → minimum viable
3. Refactor (IMPROVE)
4. Vérifier couverture 80 %+

Pour nouvelles features : utiliser l'agent **tdd-guide**.

## 8. Qualité et linting

### Python

| Outil | Usage |
|---|---|
| `black` | Formatter automatique |
| `isort` | Tri des imports |
| `ruff` | Linter rapide (remplace flake8) |
| `mypy` | Type checking statique |
| `bandit` | Audit sécurité statique |

Lancement manuel :

```bash
cd backend && source venv/bin/activate
black app/ tests/
isort app/ tests/
ruff check app/ tests/
mypy app/
bandit -r app/
```

### TypeScript

| Outil | Usage |
|---|---|
| `tsc --noEmit` | Type checking (strict mode) |
| `prettier` | Formatter |
| `eslint` | (à configurer si non présent) |

```bash
cd frontend
npx tsc --noEmit                      # Vérification TypeScript globale
```

## 9. Conventions code

### Langue
- **Identifiants** : anglais (variables, fonctions, classes)
- **Commentaires** : français
- **UI / docs** : français, accents obligatoires (é, è, ê, à, ç, ù)

### Python
- PEP 8 + annotations de type sur toutes les signatures
- `snake_case` pour fonctions, variables, fichiers
- `PascalCase` pour classes
- Dataclasses immutables (`frozen=True`) quand pertinent

### TypeScript
- `strict: true` dans `tsconfig.json`
- `interface` pour les DTO et props de composants
- Éviter `any`, préférer `unknown` + narrowing
- Props de composants typées via `interface`, émissions via `defineEmits<T>`

### Commits Git
Format conventional :

```
<type>: <description courte>

<corps optionnel>
```

Types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

**Attribution désactivée globalement** via `~/.claude/settings.json`. Ne pas ajouter de `Co-Authored-By` sauf demande explicite.

### Dark mode (OBLIGATOIRE)

Chaque composant / page / layout doit avoir les variantes `dark:` :

```html
<div class="bg-white dark:bg-dark-card text-surface-text dark:text-surface-dark-text">
  <p class="text-gray-600 dark:text-gray-400">...</p>
</div>
```

## 10. Ajouter une feature (workflow complet)

1. **Spec** : créer `specs/NNN-feature-name/` avec `spec.md`, `plan.md`, `tasks.md` (skills `speckit.*`)
2. **Research** : GitHub search + Context7 + registry avant toute nouvelle implémentation (rule `common/development-workflow.md`)
3. **Planning** : utiliser l'agent `planner` pour les features complexes
4. **TDD** : tests d'abord via l'agent `tdd-guide`
5. **Implémentation** :
   - Backend : model → migration → schema → service → router → tool LangChain → nœud graphe → prompt
   - Frontend : types → store → composable → composants → page
6. **Code review** : agent `code-reviewer` puis `security-reviewer`
7. **Tests** : couverture 80 %+
8. **Commit** : format conventional
9. **PR** : via `gh pr create`, inclure le test plan

## 11. Debugging utile

| Problème | Piste |
|---|---|
| Chat ne répond pas | Vérifier `OPENROUTER_API_KEY` dans `.env` ; logs : `make logs` → chercher `Graphe LangGraph initialisé` |
| Migration échoue | `docker compose exec backend alembic current` + inspecter `alembic_version` |
| Embeddings vides | Vérifier `CREATE EXTENSION vector;` dans la BDD |
| CORS errors | Le backend autorise uniquement `http://localhost:3000` en dur (`app/main.py`) |
| Dark mode qui ne persiste pas | `stores/ui.ts` lit `localStorage.theme` au montage ; vérifier `auth.global.ts` |
| Tests async qui boguent | Vérifier `asyncio_mode=auto` dans `pytest.ini` |

## 12. Références internes

- [Architecture Backend](./architecture-backend.md)
- [Architecture Frontend](./architecture-frontend.md)
- [Contrats d'API](./api-contracts-backend.md)
- [Modèles de données](./data-models-backend.md)
- [Guide de déploiement](./deployment-guide.md)
