# Guide de déploiement — ESG Mefali

## 1. Architecture de déploiement

Production orchestrée par Docker Compose avec :

- Un fichier dédié `docker-compose.prod.yml`
- Dockerfiles production : `backend/Dockerfile.prod`, `frontend/Dockerfile.prod`
- Un reverse proxy **Nginx** (dossier `nginx/`) en amont
- Un script de déploiement `deploy.sh` (~20 Ko) pour l'orchestration complète

```
        Internet
           │
           ▼
    ┌──────────────┐
    │    Nginx     │  ← TLS, rate limiting, reverse proxy
    └──────┬───────┘
           │
    ┌──────┴─────────────┐
    │                    │
    ▼                    ▼
┌─────────┐         ┌─────────┐
│Frontend │         │ Backend │
│Nuxt 4   │         │FastAPI  │
│  :3000  │         │  :8000  │
└─────────┘         └────┬────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ PostgreSQL 16 │
                 │   pgvector    │
                 │     :5432     │
                 └───────────────┘
```

## 2. Prérequis infrastructure

- Docker Engine 24.x+ et Docker Compose v2
- Nom de domaine et certificats TLS (Let's Encrypt recommandé, Nginx configuré)
- **Clé `OPENROUTER_API_KEY`** valide (crédits OpenRouter provisionnés)
- Volume persistant pour `postgres_data` (snapshots RGPD compliant)
- Volume persistant pour `backend/uploads/` (documents utilisateurs, rapports PDF)

## 3. Variables d'environnement prod

Créer un `.env` de production avec :

```env
# BDD
DATABASE_URL=postgresql+asyncpg://<user>:<password>@postgres:5432/esg_mefali

# Sécurité (OBLIGATOIRE — générer aléatoirement)
SECRET_KEY=<64 caractères aléatoires générés (ex. openssl rand -hex 32)>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480       # 8 h
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM
OPENROUTER_API_KEY=<votre clé OpenRouter prod>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514

# Frontend
NUXT_PUBLIC_API_BASE=https://api.<votre-domaine>/api

# Debug off
DEBUG=false
```

> ⚠️ `SECRET_KEY` par défaut dans `.env.example` est un placeholder. Ne jamais le laisser en production.

## 4. Déploiement

### 4.1 Via `deploy.sh`

```bash
# Sur le serveur de prod
cd /opt/esg_mefali
git pull origin main
./deploy.sh
```

Le script gère :

- Build des images `docker-compose.prod.yml`
- Migrations Alembic automatiques
- Redémarrage progressif (pas de downtime)
- Vérification `/api/health`

### 4.2 Déploiement manuel

```bash
# Build
docker compose -f docker-compose.prod.yml build

# Démarrer
docker compose -f docker-compose.prod.yml up -d

# Appliquer les migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Vérifier la santé
curl https://api.<votre-domaine>/api/health
```

## 5. Migrations

Les migrations Alembic sont **obligatoires** à chaque montée de version. Procédure :

1. `git pull`
2. `docker compose -f docker-compose.prod.yml build backend`
3. **Backup DB** avant migration : `docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres esg_mefali > backup-$(date +%F).sql`
4. `docker compose -f docker-compose.prod.yml exec backend alembic upgrade head`
5. Vérifier `alembic current`

## 6. Points d'attention prod

### Sécurité

- [ ] `SECRET_KEY` surchargée (jamais la valeur d'exemple)
- [ ] TLS actif sur le domaine (Nginx + Let's Encrypt)
- [ ] CORS : côté backend c'est en dur sur `http://localhost:3000` dans `app/main.py`. **À externaliser** via env `CORS_ORIGINS` avant la mise en production publique
- [ ] Rate limiting sur les endpoints sensibles (`/auth/login`, `/chat/messages`) — actuellement absent côté backend, implémenter en Nginx en attendant slowapi
- [ ] Rotation régulière des secrets (bcrypt, JWT)
- [ ] Logs sanitisés (ne jamais logger `hashed_password`, `access_token`, `OPENROUTER_API_KEY`)
- [ ] Pare-feu : port 5432 PostgreSQL non exposé publiquement

### Observabilité

- [ ] Logs centralisés (Loki, CloudWatch, Datadog...)
- [ ] Monitoring `/api/health` (uptime check)
- [ ] Alertes sur taux d'erreur 5xx, latence P95, utilisation mémoire
- [ ] Suivi des coûts OpenRouter (dashboard + budget alerts)
- [ ] Table `tool_call_logs` = source d'observabilité pour les tools LangChain

### Performance

- [ ] Nombre de workers Uvicorn (typiquement `--workers 4` pour CPU 4 cœurs)
- [ ] Pool size SQLAlchemy async (`pool_size=20`, `max_overflow=10`)
- [ ] Cache HTTP côté Nginx pour assets statiques frontend
- [ ] CDN en amont (Cloudflare, Bunny) pour les assets Nuxt
- [ ] Pagination systématique sur les listes — déjà respecté dans la plupart des routers

### Backup & résilience

- [ ] `pg_dump` quotidien + rétention 30 jours
- [ ] Dump `backend/uploads/` (rsync vers stockage objet) — idéalement migrer vers MinIO/S3
- [ ] Tests de restauration mensuels
- [ ] Documentation du runbook d'incident

## 7. Nginx — configuration reverse proxy

Dossier `nginx/` (à inspecter lors d'un déploiement réel). Points typiques à couvrir :

- Terminaison TLS avec certificats Let's Encrypt
- Redirection `http → https`
- `proxy_pass` vers `frontend:3000` et `backend:8000`
- `proxy_read_timeout` large pour le streaming SSE (ex. `300s`)
- `proxy_buffering off` pour les endpoints SSE (`/api/chat/*/messages`)
- Rate limiting basique (`limit_req_zone`) sur `/api/auth/login`
- Headers de sécurité (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

## 8. Rollback

```bash
# Revenir à un tag git précédent
git checkout <tag>
./deploy.sh

# Si échec migration :
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d esg_mefali -f /backup-<date>.sql
docker compose -f docker-compose.prod.yml exec backend alembic downgrade <revision_target>
```

## 9. Mise à l'échelle

Étapes recommandées pour scaler :

1. **Externaliser la BDD** sur un service managé (RDS, Scaleway Managed, Neon) avec réplicas de lecture
2. **Séparer le stockage fichiers** : MinIO ou S3 (configurable en un point — `backend/uploads/`)
3. **Passer les tâches longues en async** : Celery + Redis (aujourd'hui synchrone) — documents, rapports PDF, génération de plans
4. **Horizontal scaling backend** : plusieurs replicas Uvicorn derrière Nginx (stateless, seul le checkpointer LangGraph doit être partagé → migration vers `langgraph-checkpoint-postgres` déjà installée)
5. **CDN** pour le frontend Nuxt (build statique ou SSR sur serverless)
6. **Rate limiting** distribué via Redis

## 10. Coûts à surveiller

| Poste | Ordre de grandeur |
|---|---|
| Serveur de calcul (backend + frontend) | 2-4 vCPU, 4-8 Go RAM |
| PostgreSQL managé | 2 vCPU, 4 Go RAM, 50 Go stockage |
| Stockage documents uploadés | Variable (prévoir 100 Go+) |
| OpenRouter (Claude Sonnet 4) | **Variable clé** : surveiller le budget, utiliser le cache / compact prompts |
| Bande passante SSE | Moyenne (tokens streamés) |

## 11. Références

- [Architecture Backend](./architecture-backend.md)
- [Guide de développement](./development-guide.md)
- [Architecture d'intégration](./integration-architecture.md)
- Fichier `deploy.sh` à la racine
- Dossier `nginx/`
