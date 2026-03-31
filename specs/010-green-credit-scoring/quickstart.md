# Quickstart: Scoring de Credit Vert Alternatif

**Feature**: 010-green-credit-scoring

## Prerequis

- Features 001-009 implementees et fonctionnelles
- PostgreSQL 16 avec pgvector
- Python 3.12 avec venv active
- Node.js avec npm

## Demarrage rapide

### Backend

```bash
cd backend
source venv/bin/activate

# Migration base de donnees (apres creation des modeles)
alembic revision --autogenerate -m "add credit score tables"
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

### Tester le module

1. **Generer un score** : `POST /api/credit/generate` (avec token auth)
2. **Consulter le score** : `GET /api/credit/score`
3. **Detail des facteurs** : `GET /api/credit/score/breakdown`
4. **Historique** : `GET /api/credit/score/history`
5. **Attestation PDF** : `GET /api/credit/score/certificate`
6. **Chat** : Demander "Quel est mon score de credit vert ?" dans le chat

### Verification

```bash
# Tests backend
cd backend
source venv/bin/activate
pytest tests/test_credit/ -v

# Tests frontend
cd frontend
npx vitest run tests/credit-score.test.ts
```

## Points d'entree du code

| Composant | Fichier |
|-----------|---------|
| Modeles BDD | `backend/app/models/credit.py` |
| Service scoring | `backend/app/modules/credit/service.py` |
| Endpoints API | `backend/app/modules/credit/router.py` |
| Node LangGraph | `backend/app/graph/nodes.py` (credit_node) |
| Page frontend | `frontend/app/pages/credit-score/index.vue` |
| Composable API | `frontend/app/composables/useCreditScore.ts` |
| Store Pinia | `frontend/app/stores/creditScore.ts` |
