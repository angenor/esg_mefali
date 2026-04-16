# Guide de déploiement — ESG Mefali

## 1. Architecture de déploiement

Deux environnements officiels :

| Environnement | Orchestration | Accès | Reverse proxy |
|---|---|---|---|
| **Dev local** | `docker-compose.yml` | `http://localhost:{3000,8000}` | Aucun |
| **Prod VPS** | `docker-compose.prod.yml` + `deploy.sh` | `https://esg.mefali.com` | nginx UAfricas (multi-tenant) |

### Prod — Vue d'ensemble

```
┌─────────────────────────┐
│  Internet (443)         │
└──────────┬──────────────┘
           │ HTTPS (TLS 1.2+, HSTS)
           ▼
┌─────────────────────────┐
│  nginx (UAfricas)       │ /opt/uafricas/nginx
│  - SSL termination      │ esg-mefali-vhost.conf
│  - reverse proxy /api/  │
│  - reverse proxy /      │
└──────────┬──────────────┘
           │  uafricas_net (docker network externe, partagé)
           │
┌──────────┴──────────────────────────────────────┐
│  docker-compose.prod.yml (esg_mefali_net)       │
│                                                 │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐    │
│  │ frontend│   │  backend │   │ postgres │    │
│  │ Nuxt SSR│   │  FastAPI │   │ pgvector │    │
│  │ :3010   │   │  :8010   │   │  :5434   │    │
│  │ (loopb) │   │  (loopb) │   │  (loopb) │    │
│  └─────────┘   └──────────┘   └──────────┘    │
│                     │              │           │
│                     │         ┌────┴────┐     │
│                     │         │ postgres │     │
│                     │         │ _data    │     │
│                     │         └──────────┘     │
│                     │                          │
│                ┌────┴────────┐                 │
│                │ backend_    │                 │
│                │ uploads     │                 │
│                └─────────────┘                 │
└────────────────────────────────────────────────┘
```

**Points-clés** :
- Les trois services sont liés à `127.0.0.1:{3010,8010,5434}` et ne sont **pas** exposés directement sur l'internet.
- L'accès public passe **obligatoirement** par nginx UAfricas via le réseau Docker externe `uafricas_net`.
- Volumes persistés : `postgres_data` (BDD) + `backend_uploads` (fichiers utilisateurs).

## 2. Prérequis serveur

- Debian/Ubuntu récent (testé sur 22.04).
- Docker + Docker Compose v2.
- Accès SSH root à la machine cible (`root@<ip>` par défaut dans `deploy.sh`).
- Domaine ou sous-domaine pointant (A record) vers l'IP du VPS.
- Nginx UAfricas déjà installé et opérationnel sur le VPS (multi-tenant nginx).

Variables utilisées par `deploy.sh` (à adapter en tête du script) :
- `VPS_HOST=root@161.97.92.63`
- `DOMAIN=esg.mefali.com`
- `INSTALL_DIR=/opt/esg_mefali`
- `UAFRICAS_DIR=/opt/uafricas`

## 3. Procédure de déploiement initial

```bash
# Depuis la machine locale, après avoir poussé main en remote :
./deploy.sh setup      # Provisionne le VPS (clone repo, génère secrets, .env)
                        # → SSH sur le VPS, installe Docker si absent, clone /opt/esg_mefali

./deploy.sh vhost-install
# Copie nginx/esg-mefali-vhost.conf.example → /opt/uafricas/nginx/conf.d/esg-mefali-vhost.conf
# (à éditer pour activer les lignes SSL une fois le certificat émis)

./deploy.sh ssl
# Émet le certificat Let's Encrypt via certbot --standalone
# (stoppe temporairement nginx UAfricas sur :80 le temps du challenge)
# Copie fullchain.pem + privkey.pem dans /opt/uafricas/nginx/ssl/esg-mefali/
# Installe un cron de renouvellement automatique

./deploy.sh deploy
# git pull origin main + docker compose -f docker-compose.prod.yml build + up -d
# Attend 25s, puis vérifie /api/health et le frontend
```

**⚠️ Avant le premier `deploy`** : éditer `/opt/esg_mefali/.env` sur le VPS et renseigner `OPENROUTER_API_KEY`. Les autres secrets (`SECRET_KEY`, `POSTGRES_PASSWORD`) sont générés par `setup` via `openssl rand`.

## 4. Déploiements itératifs

```bash
./deploy.sh update     # git pull + rebuild rapide des conteneurs applicatifs
./deploy.sh deploy     # Plus complet (rebuild images, redémarre stack, healthcheck)
./deploy.sh migrate    # Exécute alembic upgrade head sur le backend en prod
./deploy.sh restart    # docker compose restart
./deploy.sh logs       # Tail des logs combinés
./deploy.sh status     # État des containers
./deploy.sh shell      # Ouvre un shell dans le conteneur backend
```

## 5. Rétention / sauvegardes

```bash
./deploy.sh backup     # pg_dump + archive uploads/ dans /opt/backups/esg_mefali/<timestamp>/
./deploy.sh restore <timestamp>   # Restaure depuis une sauvegarde datée
```

**Fréquence recommandée** : cron quotidien (à ajouter manuellement au crontab du VPS — pas automatisé par `deploy.sh`).

## 6. Configuration nginx (reverse proxy)

Référence : [nginx/esg-mefali-vhost.conf.example](../nginx/esg-mefali-vhost.conf.example). Points saillants :

| Bloc | Contenu clé |
|---|---|
| `server_name` | `esg.mefali.com` |
| SSL | Certificats Let's Encrypt dans `/opt/uafricas/nginx/ssl/esg-mefali/` |
| TLS | Versions 1.2 + 1.3 uniquement |
| En-têtes sécurité | `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, CSP |
| `location /api/` | `proxy_pass http://esg_mefali_backend:8000;` — timeouts 600s, buffering **désactivé** (SSE) |
| `location /` | `proxy_pass http://esg_mefali_frontend:3000;` — SSR Nuxt + upgrade WebSocket |
| ACME | `location ^~ /.well-known/acme-challenge/` pour le renouvellement Let's Encrypt |
| Upload max | `client_max_body_size 50M;` |

### Directives critiques pour le SSE

Dans `location /api/` :

```nginx
proxy_buffering off;
proxy_cache off;
proxy_request_buffering off;
chunked_transfer_encoding on;
proxy_read_timeout 600s;
```

Sans ces directives, nginx bufferiserait la réponse streamée du backend et le chat apparaîtrait figé côté frontend.

## 7. Variables d'environnement prod

Fichier attendu : `/opt/esg_mefali/.env` (non versionné).

```env
# Backend
DATABASE_URL=postgresql+asyncpg://esg_mefali:<postgres_password>@postgres:5432/esg_mefali
SECRET_KEY=<64-char-hex>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=30
OPENROUTER_API_KEY=<clef_OR>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
DEBUG=false

# Postgres
POSTGRES_USER=esg_mefali
POSTGRES_PASSWORD=<password>
POSTGRES_DB=esg_mefali
POSTGRES_PORT=5434

# Frontend
NODE_ENV=production
NUXT_PUBLIC_API_BASE=/api
```

## 8. Observabilité

- Logs : `docker compose logs -f backend` ou `./deploy.sh logs`.
- Healthcheck HTTP : `GET /api/health` renvoie `{status, database, version}`.
- Audit des tool calls LangGraph : table `tool_call_logs` (user_id, conversation_id, node_name, tool_name, duration_ms, status, error_message, retry_count). Requêtes analytiques recommandées :
  ```sql
  SELECT tool_name, status, COUNT(*), AVG(duration_ms)
  FROM tool_call_logs
  WHERE created_at > NOW() - INTERVAL '24 hours'
  GROUP BY tool_name, status
  ORDER BY COUNT(*) DESC;
  ```
- Aucune métrique Prometheus / trace distribuée n'est encore en place (voir [technical-debt-backlog.md](./technical-debt-backlog.md)).

## 9. CI/CD

**État actuel** : pas de pipeline GitHub Actions. Les déploiements sont déclenchés manuellement via `./deploy.sh`. Les tests locaux (`make test`) font office de porte de qualité.

**Pistes futures** (documentées dans la dette technique) :
- Workflow GitHub Actions : lint + tests backend + tests frontend unit + Playwright sur PR.
- Build et push d'images Docker taggées vers un registry privé.
- Déploiement staging → prod via SSH deploy key.

## 10. Rollback

En cas de déploiement défectueux :

```bash
# Restaurer la dernière sauvegarde BDD + uploads
./deploy.sh restore <timestamp_précédent>

# Revenir à un commit stable
ssh root@<vps> "cd /opt/esg_mefali && git reset --hard <sha> && ./deploy.sh deploy"
```

Aucune stratégie de blue/green automatisée. Le downtime d'un rollback est de l'ordre de 30 secondes (le temps du rebuild + up).

## 11. Sécurité

- Secrets générés via `openssl rand`, jamais en clair dans git.
- CORS backend **actuellement codé en dur** sur `http://localhost:3000` dans [backend/app/main.py](../backend/app/main.py) — à rendre configurable avant public. Voir [technical-debt-backlog.md](./technical-debt-backlog.md).
- Pas de rate limiting ni de WAF en place. Recommandations : fail2ban côté nginx + middleware FastAPI (`slowapi`) avant ouverture publique large.
- `SECRET_KEY` jamais loggué, jamais exposé. Rotation : regénérer + relancer le backend invalidera tous les JWT émis (utilisateurs relogueront).
- Uploads stockés sur disque local du VPS. Pas de scan antivirus.
