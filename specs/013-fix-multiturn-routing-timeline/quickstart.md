# Quickstart: 013-fix-multiturn-routing-timeline

## Prerequis

```bash
cd /Users/mac/Documents/projets/2025/esg_mefali
git checkout 013-fix-multiturn-routing-timeline
source backend/venv/bin/activate
```

## Fichiers a modifier

### BUG-1: Routing multi-tour (7 fichiers backend)

1. **State** : `backend/app/graph/state.py`
   - Ajouter `active_module` et `active_module_data` au TypedDict

2. **Router** : `backend/app/graph/nodes.py` (fonction `router_node`)
   - Ajouter logique : active_module prioritaire → classification changement de sujet → classification normale

3. **Noeuds specialistes** (dans `backend/app/graph/nodes.py`) :
   - `esg_scoring_node` : activer/desactiver active_module, mettre a jour active_module_data
   - `carbon_node` : idem
   - `financing_node` : idem
   - `application_node` : idem
   - `credit_node` : idem
   - `action_plan_node` : idem

### BUG-2: Format timeline (4 fichiers)

4. **Frontend** : `frontend/app/components/richblocks/TimelineBlock.vue`
   - Ajouter normalisation des variantes (phases/items → events, aliases de champs)

5. **Prompts** :
   - `backend/app/prompts/action_plan.py` : phases → events
   - `backend/app/prompts/carbon.py` : items → events
   - `backend/app/prompts/financing.py` : items → events

## Lancer les tests

```bash
# Tests existants (verification non-regression)
cd backend && python -m pytest tests/test_graph/ -v

# Tous les tests
python -m pytest tests/ -v --tb=short

# Frontend
cd ../frontend && npx vitest run
```

## Verification manuelle

1. Demarrer le backend : `cd backend && uvicorn app.main:app --reload`
2. Demarrer le frontend : `cd frontend && npm run dev`
3. Ouvrir le chat, dire "Je veux faire mon evaluation ESG"
4. Repondre aux questions successives → verifier que les criteres sont sauvegardes
5. Dire "Parlons de financement" → verifier le changement de module
