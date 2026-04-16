# Guide de développement — ESG Mefali

## 1. Prérequis

| Outil | Version minimale | Usage |
|---|---|---|
| Docker + Docker Compose | 24+ | Orchestration complète (voie recommandée) |
| Git | 2.30+ | Gestion de version |
| Node.js | 20 LTS | Dev frontend hors Docker |
| Python | 3.12 | Dev backend hors Docker |
| PostgreSQL | 16 + `pgvector` | BDD locale hors Docker |
| OpenRouter API key | — | Obligatoire pour le chat IA (modèle Claude Sonnet 4) |

## 2. Démarrage rapide (Docker — recommandé)

```bash
# 1. Cloner
git clone <repo-url>
cd esg_mefali

# 2. Configurer l'environnement
cp .env.example .env
# → éditer .env et renseigner OPENROUTER_API_KEY

# 3. Lancer les 3 services (postgres + backend + frontend)
make dev

# 4. Appliquer les migrations Alembic
make migrate

# 5. Vérifier
# Frontend   : http://localhost:3000
# Backend    : http://localhost:8000
# Swagger    : http://localhost:8000/docs
# PostgreSQL : localhost:5432 (user/pass : postgres/postgres)
```

## 3. Commandes Makefile

| Commande | Effet |
|---|---|
| `make dev` | `docker compose up -d` — démarre postgres, backend (reload), frontend (HMR) |
| `make build` | `docker compose build` — reconstruit les images |
| `make migrate` | Exécute `alembic upgrade head` dans le conteneur backend |
| `make test` | Lance tests backend puis frontend |
| `make test-back` | `pytest tests/ -v --cov=app --cov-report=term-missing` (backend uniquement) |
| `make test-front` | `npm run test` + `npm run test:e2e` (frontend uniquement) |
| `make down` | Arrête les services sans supprimer les volumes |
| `make logs` | Tail des logs combinés |
| `make clean` | Arrête + supprime volumes (⚠️ efface la BDD) |

## 4. Développement local sans Docker

### Backend (venv obligatoire)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # ⚠️ À chaque nouvelle session
pip install -r requirements.txt -r requirements-dev.txt

# S'assurer que postgres + pgvector tourne (via Docker ou install local)
docker compose up postgres -d

# Migrations
alembic upgrade head

# Run
uvicorn app.main:app --reload --port 8000
```

Vérification de l'environnement virtuel actif : `which python` doit retourner `backend/venv/bin/python`.

### Frontend

```bash
cd frontend
npm install
npm run dev         # HMR sur http://localhost:3000
npm run build       # Build SSR production
npm run preview     # Sert le build
```

### Base de données seule

```bash
docker compose up postgres -d
# Se connecter : psql postgresql://postgres:postgres@localhost:5432/esg_mefali
```

## 5. Variables d'environnement critiques

Voir [.env.example](../.env.example) pour la liste exhaustive. Indispensables en dev :

| Variable | Valeur par défaut (dev) | Rôle |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/esg_mefali` | Chaîne SQLAlchemy asyncpg |
| `SECRET_KEY` | généré à l'install | Signe les JWT |
| `JWT_ALGORITHM` | `HS256` | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` (dev) / `480` (prod) | Durée de vie de l'access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Durée de vie du refresh token |
| `OPENROUTER_API_KEY` | (à fournir) | Accès au LLM Claude Sonnet 4 |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | — |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4-20250514` | — |
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000/api` (dev) / `/api` (prod) | Base URL API côté frontend |
| `DEBUG` | `true` (dev) / `false` (prod) | Active les échos utiles |

## 6. Workflow de développement

### Conventions générales

- **Langue** : code et identifiants en **anglais**, commentaires et UI en **français avec accents** (é, è, ê, à, ç, ù — obligatoires).
- **Structure Nuxt 4** : tout le code source dans `frontend/app/`.
- **Composables et composants UI** : vérifier la réutilisabilité avant de créer. Si un pattern visuel se répète plus de 2 fois, l'extraire dans `components/ui/`.
- **Dark mode obligatoire** sur chaque composant : utiliser les variantes `dark:` Tailwind (`dark:bg-dark-card`, `dark:text-surface-dark-text`, etc.). Variables CSS définies dans `frontend/app/assets/css/main.css` via `@theme`.
- **Backend Python** : jamais d'installation globale, toujours via venv.
- **Pas de fichiers interdits de modification dans les specs** — la modification est toujours autorisée si elle sert la cohérence.

### Cycle feature

1. **Recherche & réutilisation** — vérifier `specs/`, les composants existants, les tools LangChain existants, les composables.
2. **Planification** — utiliser le workflow BMM (`_bmad/`) ou SpecKit (`specs/`).
3. **Implémentation TDD** — écrire les tests (RED), implémenter (GREEN), refactorer.
4. **Dark mode + accessibilité** — vérifier au passage.
5. **Tests** — `make test` doit rester vert (935+ tests backend, ~60 tests frontend unit + E2E).
6. **Commit** — format conventionnel (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## 7. Tests

### Backend

```bash
cd backend
source venv/bin/activate
pytest                                    # Tous les tests
pytest tests/test_graph/                  # Scoped (ex: nodes LangGraph)
pytest -k "interactive_question"          # Par mot-clef
pytest --cov=app --cov-report=term-missing
```

Configuration dans [backend/pytest.ini](../backend/pytest.ini). Fixtures partagées dans [backend/tests/conftest.py](../backend/tests/conftest.py) : SQLite in-memory pour la rapidité, `AsyncClient` FastAPI, `db_session` brut.

### Frontend — unitaires (Vitest)

```bash
cd frontend
npm run test                              # Interactive
npm run test -- --run                     # CI (sans watch)
npm run test -- tests/composables/useChat.test.ts
```

Config : [frontend/vitest.config.ts](../frontend/vitest.config.ts). Environnement `happy-dom`, setup `tests/setup.ts` (patchs `import.meta.client/server`).

### Frontend — E2E (Playwright)

```bash
cd frontend
npm run test:e2e                          # Backend mocké via tests/e2e/fixtures/mock-backend.ts
npm run test:e2e -- --headed              # Voir le navigateur
PLAYWRIGHT_SLOWMO=200 npm run test:e2e   # Ralentir pour debug
PLAYWRIGHT_FULL_MOTION=1 npm run test:e2e # Désactiver reducedMotion
```

Config : [frontend/playwright.config.ts](../frontend/playwright.config.ts). Un seul worker, Chromium, port dédié 4321 pour éviter les conflits avec le dev server (3000). Backend mocké intégralement (pas de dépendance Postgres / OpenRouter en E2E mockée).

Specs E2E existantes :
- `tests/e2e/8-1-parcours-fatou.spec.ts` — parcours ESG complet
- `tests/e2e/8-2-parcours-moussa.spec.ts` — parcours carbone + financement
- `tests/e2e-live/8-3-parcours-aminata.sh` — parcours Aminata (stack live, pas de mock)

### Tests E2E "live" (shell)

Le dossier `frontend/tests/e2e-live/` contient des tests bash exécutés contre une stack réelle (backend + LLM + Postgres). Prérequis : services up (`make dev`), compte seed. Helpers dans `lib/` (assertions, env, login).

```bash
cd frontend/tests/e2e-live
./8-3-parcours-aminata.sh
```

## 8. Migrations BDD

```bash
# Créer une nouvelle migration
cd backend && source venv/bin/activate
alembic revision -m "add_my_table" --autogenerate

# Appliquer
alembic upgrade head

# Revenir en arrière d'un cran
alembic downgrade -1

# Historique
alembic history
```

Les migrations vivent dans [backend/alembic/versions/](../backend/alembic/versions/). 13 migrations au total (voir [data-models-backend.md](./data-models-backend.md)).

## 9. Linting & formatage

- **Backend** : `ruff check app/` + `ruff format app/`.
- **Frontend** : pas de linter dédié côté frontend (hors `tsc` via `nuxt typecheck`). Convention de style portée par les revues de code.

## 10. Ressources internes

- Spécifications détaillées : [specs/](../specs/)
- Contexte produit : [CLAUDE.md](../CLAUDE.md) (conventions, stack, domaine)
- Workflows BMM : [_bmad/bmm/](../_bmad/bmm/)
- Artefacts de planification : `_bmad-output/planning-artifacts/`

## 11. Problèmes courants

| Symptôme | Cause probable | Solution |
|---|---|---|
| Chat ne stream pas | `OPENROUTER_API_KEY` manquant ou invalide | Vérifier `.env`, redémarrer backend |
| Frontend 401 en boucle | Refresh token expiré / SECRET_KEY changé | Vider `localStorage`, se reconnecter |
| Migration Alembic refuse | Venv non activé | `source backend/venv/bin/activate` |
| `pgvector` introuvable | Extension non installée | `CREATE EXTENSION IF NOT EXISTS vector;` (géré par migration 001) |
| Tests E2E flaky | Motion activé par défaut | S'assurer que `reducedMotion: 'reduce'` (par défaut) |
| Port 3000 / 8000 / 5432 occupé | Autre service local | Arrêter ou mapper différemment dans `docker-compose.yml` |

Voir aussi le backlog de dette technique : [technical-debt-backlog.md](./technical-debt-backlog.md).
