# Quickstart — 009 Fund Application Generator

## Prerequis

- Features 001-008 implementees (profil, documents, ESG, carbone, financement)
- PostgreSQL avec pgvector operationnel
- Backend venv active avec dependances installees
- WeasyPrint installe (deja en place depuis feature 006)

## Nouvelle dependance

```bash
source backend/venv/bin/activate
pip install python-docx
pip freeze | grep python-docx >> backend/requirements.txt
```

## Migration BDD

```bash
cd backend
alembic revision --autogenerate -m "add fund_applications table"
alembic upgrade head
```

## Demarrage

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

## Verification rapide

```bash
# Creer un dossier pour un fonds direct (FNDE)
curl -X POST http://localhost:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -d '{"fund_id": "<FNDE_UUID>"}'

# Creer un dossier bancaire (SUNREF via SIB)
curl -X POST http://localhost:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -d '{"fund_id": "<SUNREF_UUID>", "intermediary_id": "<SIB_UUID>"}'

# Generer une section
curl -X POST http://localhost:8000/api/applications/<APP_ID>/generate-section \
  -H "Content-Type: application/json" \
  -d '{"section_key": "company_banking_history"}'

# Fiche de preparation intermediaire (PDF)
curl -X POST http://localhost:8000/api/applications/<APP_ID>/prep-sheet \
  --output prep-sheet.pdf
```

## Structure des fichiers crees

```
backend/app/
├── models/
│   └── application.py          # Modele FundApplication + enums
├── modules/
│   └── applications/
│       ├── __init__.py
│       ├── router.py            # 10 endpoints REST
│       ├── service.py           # Logique metier + generation LLM
│       ├── schemas.py           # Schemas Pydantic
│       ├── templates.py         # Templates de sections par target_type
│       ├── export.py            # Export PDF (WeasyPrint) + Word (python-docx)
│       ├── prep_sheet.py        # Generation fiche preparation PDF
│       ├── simulation.py        # Simulateur de financement
│       └── templates/
│           ├── application_export.html    # Template Jinja2 export dossier
│           └── prep_sheet.html            # Template Jinja2 fiche preparation
├── graph/
│   └── nodes.py                 # + application_node (ajout)
│   └── graph.py                 # + branche application (ajout)

frontend/app/
├── pages/
│   └── applications/
│       ├── index.vue            # Liste des dossiers
│       └── [id].vue             # Detail dossier (sections, checklist, prep, simulation)
├── composables/
│   └── useApplications.ts       # API calls + logique
├── stores/
│   └── applications.ts          # Store Pinia
```
