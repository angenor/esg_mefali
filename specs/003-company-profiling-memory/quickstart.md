# Quickstart: 003-company-profiling-memory

## Prerequis

- Python 3.12 + venv actif (`source backend/venv/bin/activate`)
- Node.js 20+ + npm
- PostgreSQL 16 en cours d'execution
- Variables d'environnement configurees (`.env`)

## Demarrage rapide

### 1. Migration base de donnees

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 2. Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm run dev
```

### 4. Verification

1. Se connecter a l'application
2. Ouvrir le chat et ecrire : "Je suis une entreprise de recyclage de plastique basee a Abidjan avec 15 employes"
3. Verifier :
   - Le chat repond normalement avec des conseils contextualises
   - Une notification apparait : "Profil mis a jour : secteur = Recyclage"
   - Le badge dans la sidebar affiche un pourcentage > 0%
4. Naviguer vers la page Profil dans la sidebar
5. Verifier que les champs extraits sont affiches

## Tests

### Backend
```bash
cd backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend
```bash
cd frontend
npm run test
```

## Nouveaux endpoints a tester

```bash
# Obtenir le profil
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/company/profile

# Mettre a jour manuellement
curl -X PATCH -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "EcoPlast SARL", "sector": "recyclage"}' \
  http://localhost:8000/api/company/profile

# Obtenir la completion
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/company/profile/completion
```
