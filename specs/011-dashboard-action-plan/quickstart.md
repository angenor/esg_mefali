# Quickstart: Tableau de bord principal et plan d'action

**Feature**: 011-dashboard-action-plan

## Prérequis

- Backend running : `source backend/venv/bin/activate && uvicorn app.main:app --reload`
- Frontend running : `cd frontend && npm run dev`
- PostgreSQL avec les tables des modules 001-010
- Migrations appliquées : `cd backend && alembic upgrade head`

## Migration

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "add action_plan dashboard tables"
alembic upgrade head
```

## Vérification rapide

### 1. Dashboard summary

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/dashboard/summary | python -m json.tool
```

Doit retourner les données agrégées ESG/carbone/crédit/financements (ou null si pas de données).

### 2. Générer un plan d'action

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeframe": 12}' \
  http://localhost:8000/api/action-plan/generate | python -m json.tool
```

Doit retourner un plan avec ~10-15 actions catégorisées.

### 3. Lister les actions

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/action-plan/{plan_id}/items?category=intermediary_contact" | python -m json.tool
```

Doit retourner uniquement les actions de type contact intermédiaire avec coordonnées.

### 4. Chat — plan d'action

Dans le chat, taper :
> "Génère mon plan d'action sur 12 mois"

Doit afficher des blocs visuels : timeline, table, mermaid, gauge, chart.

## Tests

```bash
# Backend
cd backend && source venv/bin/activate
pytest tests/test_dashboard/ tests/test_action_plan/ -v --cov

# Frontend
cd frontend && npx vitest run
```

## Pages frontend

- **Dashboard** : http://localhost:3000/dashboard
- **Plan d'action** : http://localhost:3000/action-plan
