# Quickstart: 015-fix-toolcall-esg-timeout

## Prerequis

```bash
cd backend
source venv/bin/activate
```

## Fichiers a modifier (6 fichiers)

### Backend

1. `backend/app/graph/tools/application_tools.py` — Ajouter `create_fund_application`
2. `backend/app/graph/tools/esg_tools.py` — Ajouter `batch_save_esg_criteria`
3. `backend/app/prompts/application.py` — Renforcer le ROLE et les instructions tool calling
4. `backend/app/prompts/credit.py` — Renforcer les instructions tool calling (noms explicites)
5. `backend/app/prompts/esg_scoring.py` — Ajouter instruction batch
6. `backend/app/graph/nodes.py` — Ajouter `request_timeout=60` dans `get_llm()`

### Tests

7. `backend/tests/test_prompts/test_tool_instructions.py` — Tests unitaires prompts

## Validation

```bash
# Tests existants (non-regression)
cd backend && pytest tests/ -v

# Test specifique prompts
pytest tests/test_prompts/ -v
```

## Points d'attention

- NE PAS modifier `graph.py` — l'architecture `create_tool_loop` est correcte
- NE PAS modifier les noeuds dans `nodes.py` (sauf `get_llm()`) — le binding tools et la boucle ToolNode fonctionnent
- Le tool `create_fund_application` doit etre ajoute a la liste `APPLICATION_TOOLS` pour etre inclus dans le graphe
- Le tool `batch_save_esg_criteria` doit etre ajoute a la liste `ESG_TOOLS`
