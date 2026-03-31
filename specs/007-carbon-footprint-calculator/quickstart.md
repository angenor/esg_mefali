# Quickstart: Calculateur d'Empreinte Carbone

**Feature**: 007-carbon-footprint-calculator

## Prerequis

- Backend en cours d'execution (`uvicorn app.main:app --reload`)
- Frontend en cours d'execution (`npm run dev`)
- PostgreSQL avec migrations a jour (`alembic upgrade head`)
- Un utilisateur connecte avec un profil entreprise (secteur renseigne)

## Tester la fonctionnalite

### 1. Via le Chat (experience principale)

1. Aller sur `/chat`
2. Taper : "Je veux faire mon bilan carbone" ou "Calculer mon empreinte carbone"
3. Repondre aux questions categorie par categorie
4. Observer les graphiques a barres progressifs dans le chat
5. A la fin, verifier le donut, la jauge, le tableau et la timeline

### 2. Via la page Carbon

1. Aller sur `/carbon` (lien dans la sidebar)
2. Voir la liste des bilans existants
3. Cliquer sur un bilan complete pour voir les resultats

### 3. Via l'API directement

```bash
# Creer un bilan
curl -X POST http://localhost:8000/api/carbon/assessments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026}'

# Ajouter des entrees
curl -X POST http://localhost:8000/api/carbon/assessments/$ID/entries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entries": [{"category": "energy", "subcategory": "electricity", "quantity": 5000, "unit": "kWh", "emission_factor": 0.41, "emissions_tco2e": 2.05}], "mark_category_complete": "energy"}'

# Resume
curl http://localhost:8000/api/carbon/assessments/$ID/summary \
  -H "Authorization: Bearer $TOKEN"

# Benchmark sectoriel
curl http://localhost:8000/api/carbon/benchmarks/agriculture \
  -H "Authorization: Bearer $TOKEN"
```

## Lancer les tests

```bash
# Backend
cd backend && source venv/bin/activate
pytest tests/test_carbon_service.py -v
pytest tests/test_carbon_router.py -v
pytest tests/test_carbon_node.py -v

# Tous les tests carbon
pytest tests/ -k carbon -v
```
