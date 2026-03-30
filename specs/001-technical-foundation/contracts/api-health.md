# API Contract: Health Check

**Base path**: `/api`
**Authentification** : Aucune (endpoint public)

## GET /api/health

Verifier l'etat du backend et de ses dependances.

**Reponse 200** (systeme sain) :
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

**Reponse 503** (systeme degrade) :
```json
{
  "status": "degraded",
  "database": "disconnected",
  "version": "0.1.0"
}
```
