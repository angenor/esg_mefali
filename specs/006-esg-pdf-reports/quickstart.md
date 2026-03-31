# Quickstart: Génération de Rapports ESG en PDF

**Feature**: 006-esg-pdf-reports

## Prérequis

### Dépendances système (WeasyPrint)

```bash
# macOS
brew install pango cairo libffi

# Ubuntu/Debian
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```

### Dépendances Python

```bash
source backend/venv/bin/activate
pip install weasyprint matplotlib jinja2
```

### Dépendances Frontend

Aucune nouvelle dépendance frontend requise.

## Démarrage rapide

### 1. Migration base de données

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 2. Créer le répertoire de stockage

```bash
mkdir -p backend/uploads/reports
```

### 3. Vérifier les prérequis

```bash
# Vérifier WeasyPrint
python -c "import weasyprint; print('WeasyPrint OK')"

# Vérifier matplotlib
python -c "import matplotlib; print('matplotlib OK')"
```

### 4. Tester la génération

```bash
# Lancer le backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Générer un rapport (nécessite une évaluation ESG complétée)
curl -X POST http://localhost:8000/api/reports/esg/{assessment_id}/generate \
  -H "Authorization: Bearer {token}"
```

## Structure des fichiers clés

| Fichier | Rôle |
|---------|------|
| `backend/app/modules/reports/service.py` | Logique de génération PDF |
| `backend/app/modules/reports/charts.py` | Graphiques matplotlib → SVG |
| `backend/app/modules/reports/templates/esg_report.html` | Template HTML du rapport |
| `backend/app/modules/reports/templates/esg_report.css` | Styles CSS print |
| `backend/app/modules/reports/router.py` | Endpoints API |
| `frontend/app/pages/reports/index.vue` | Page liste des rapports |
| `frontend/app/components/esg/ReportButton.vue` | Bouton génération + progression |

## Workflow de génération

```
1. Utilisateur clique "Générer le rapport PDF"
2. Frontend POST /api/reports/esg/{id}/generate
3. Backend crée l'entrée Report (status: generating)
4. Backend génère les graphiques SVG (matplotlib)
5. Backend appelle Claude pour le résumé exécutif
6. Backend rend le template HTML (Jinja2)
7. Backend convertit HTML → PDF (WeasyPrint)
8. Backend sauvegarde le PDF, met à jour status: completed
9. Frontend poll /api/reports/{id}/status
10. Utilisateur télécharge via GET /api/reports/{id}/download
```
