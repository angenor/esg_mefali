# Quickstart: Evaluation et Scoring ESG

**Feature**: 005-esg-scoring-assessment

## Prerequis

- Features 001-004 implementees et fonctionnelles
- PostgreSQL avec extension pgvector
- Variables d'environnement configurees (`.env`)

## Demarrage rapide

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Flux utilisateur principal

1. L'utilisateur se connecte et a un profil entreprise renseigne (secteur, pays, taille)
2. Dans le chat, il ecrit "Je veux evaluer mon entreprise sur les criteres ESG"
3. Le `router_node` detecte l'intention ESG et route vers `esg_scoring_node`
4. Le noeud ESG cree une evaluation (status: draft) et commence par le pilier Environnement
5. Claude pose des questions sur les criteres E1-E10, adaptees au secteur
6. A la fin du pilier E, un bloc `progress` est affiche dans le chat avec les scores
7. Meme processus pour les piliers Social (S1-S10) et Gouvernance (G1-G10)
8. A la fin, Claude affiche : radar chart (3 piliers), gauge (score global), table (recommandations)
9. L'evaluation est sauvegardee en base (status: completed)
10. L'utilisateur peut consulter la page /esg/results pour une vue persistante

## Tester l'API directement

```bash
# Creer une evaluation
curl -X POST http://localhost:8000/api/esg/assessments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Voir les evaluations
curl http://localhost:8000/api/esg/assessments \
  -H "Authorization: Bearer $TOKEN"

# Score detaille
curl http://localhost:8000/api/esg/assessments/{id}/score \
  -H "Authorization: Bearer $TOKEN"

# Benchmark sectoriel
curl http://localhost:8000/api/esg/benchmarks/agriculture \
  -H "Authorization: Bearer $TOKEN"
```

## Points d'attention

- Le `esg_scoring_node` redirige vers `profiling_node` si le profil est incomplet
- L'evaluation peut etre interrompue et reprise (status: in_progress, criteres evalues persistes)
- Le RAG enrichit l'evaluation si des documents ont ete uploades (feature 004)
- Les blocs visuels (progress, chart, gauge, table, mermaid) sont generes par le LLM dans le chat
- La page /esg/results charge les donnees via l'API REST, independamment du chat
