# Quickstart: Foundation Technique ESG Mefali

## Prerequis

- Docker et Docker Compose installes
- Git

## Demarrage rapide

```bash
# 1. Cloner le projet
git clone <repo-url>
cd esg_mefali

# 2. Copier la configuration
cp .env.example .env
# Editer .env avec vos cles (OPENROUTER_API_KEY obligatoire)

# 3. Lancer les 3 services
make dev
# Ou directement : docker compose up --build
```

## Acces

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Application Nuxt |
| Backend API | http://localhost:8000 | API FastAPI |
| Swagger Docs | http://localhost:8000/docs | Documentation interactive |
| PostgreSQL | localhost:5432 | Base de donnees |

## Premier parcours

1. Ouvrir http://localhost:3000
2. Cliquer sur "S'inscrire"
3. Remplir le formulaire (email, mot de passe, nom, entreprise)
4. Se connecter avec les identifiants crees
5. Utiliser le panneau de chat IA a droite pour envoyer un message

## Variables d'environnement requises

```env
# Base de donnees
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/esg_mefali

# Securite
SECRET_KEY=votre-cle-secrete-a-changer
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# IA (OpenRouter)
OPENROUTER_API_KEY=votre-cle-openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514

# Frontend
NUXT_PUBLIC_API_BASE=http://localhost:8000/api
```

## Commandes utiles

```bash
make dev          # Lancer en mode developpement
make build        # Build de production
make migrate      # Executer les migrations Alembic
make test         # Lancer tous les tests
make test-back    # Tests backend uniquement
make test-front   # Tests frontend uniquement
make down         # Arreter les services
make logs         # Voir les logs
```

## Developpement local (sans Docker)

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Base de donnees
PostgreSQL 16 avec pgvector doit etre installe localement ou via Docker :
```bash
docker compose up postgres -d
```
