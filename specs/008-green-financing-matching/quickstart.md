# Quickstart: 008-green-financing-matching

## Prerequis

- Features 001-007 implementees et fonctionnelles
- PostgreSQL avec pgvector actif
- Backend venv active : `source backend/venv/bin/activate`

## Demarrage rapide

### 1. Migration BDD

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

La migration `008_add_financing_tables.py` est deja creee dans `alembic/versions/`.

### 2. Seed des donnees

```bash
cd backend
python -m app.modules.financing.seed
```

Cela cree :
- 12 fonds verts avec criteres reels
- 14+ intermediaires avec coordonnees
- ~50 liaisons fonds-intermediaires
- Embeddings pour la recherche semantique

### 3. Lancer le backend

```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Tester les endpoints

```bash
# Liste des fonds
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/financing/funds

# Recommandations pour l'utilisateur
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/financing/matches

# Detail d'un fonds avec intermediaires
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/financing/funds/{fund_id}
```

### 5. Frontend

```bash
cd frontend
npm run dev
```

Naviguer vers `/financing` dans le navigateur.

### 6. Test chat

Dans le chat, taper : "Comment acceder au financement SUNREF ?"
Verifier que le diagramme Mermaid du parcours d'acces s'affiche.

## Structure des fichiers crees

```
backend/app/
  models/financing.py              # Fund, Intermediary, FundIntermediary, FundMatch, FinancingChunk
  modules/financing/
    __init__.py
    router.py                      # Endpoints /api/financing/*
    schemas.py                     # Pydantic schemas
    service.py                     # Logique metier + matching + RAG
    seed.py                        # Donnees initiales (12 fonds, 14+ intermediaires)
    preparation_sheet.py           # Generation fiche PDF
    preparation_template.html      # Template Jinja2
  graph/
    nodes.py                       # + financing_node()
    state.py                       # + financing_data, _route_financing
    graph.py                       # + noeud financing dans le graphe

frontend/app/
  pages/financing/
    index.vue                      # Page principale (3 onglets)
    [id].vue                       # Detail d'un fonds
  composables/useFinancing.ts      # Appels API
  stores/financing.ts              # Pinia store
  types/financing.ts               # Interfaces TypeScript
  components/layout/AppSidebar.vue # + entree navigation
```
