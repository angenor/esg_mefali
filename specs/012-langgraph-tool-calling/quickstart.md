# Quickstart: Intégration Tool Calling LangGraph

## Prérequis

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt  # langchain-core>=0.3.0, langgraph>=0.2.0
```

## Vérification de compatibilité tool calling

```bash
# Test rapide que bind_tools fonctionne avec OpenRouter
python -c "
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from app.core.config import settings

@tool
def test_tool(message: str) -> str:
    \"\"\"Outil de test.\"\"\"
    return f'OK: {message}'

llm = ChatOpenAI(
    model=settings.openrouter_model,
    base_url=settings.openrouter_base_url,
    api_key=settings.openrouter_api_key,
)
llm_with_tools = llm.bind_tools([test_tool])
response = llm_with_tools.invoke('Dis bonjour en utilisant le test_tool')
print('Tool calls:', response.tool_calls)
print('Content:', response.content)
"
```

## Structure des fichiers à modifier/créer

```
backend/app/
├── graph/
│   ├── state.py          # MODIFIER — ajouter user_id au TypedDict
│   ├── nodes.py          # MODIFIER — refactorer chaque noeud pour bind_tools
│   ├── graph.py          # MODIFIER — ajouter les ToolNodes et boucles conditionnelles
│   └── tools/            # CRÉER — répertoire des tools par noeud
│       ├── __init__.py
│       ├── profiling_tools.py
│       ├── esg_tools.py
│       ├── carbon_tools.py
│       ├── financing_tools.py
│       ├── application_tools.py
│       ├── credit_tools.py
│       ├── document_tools.py
│       ├── action_plan_tools.py
│       ├── chat_tools.py
│       └── common.py     # helpers partagés (get_db_and_user, log_tool_call)
├── api/
│   └── chat.py           # MODIFIER — utiliser astream_events() au lieu de llm.astream()
├── models/
│   └── tool_call_log.py  # CRÉER — modèle SQLAlchemy pour la journalisation
└── modules/
    ├── applications/
    │   └── service.py    # ÉTENDRE — simulate(), export()
    └── credit/
        └── service.py    # ÉTENDRE — generate_certificate()

frontend/app/
├── composables/
│   └── useChat.ts        # MODIFIER — gérer les nouveaux événements SSE
└── components/
    └── chat/
        └── ToolCallIndicator.vue  # CRÉER — indicateur visuel tool call
```

## Ordre d'implémentation recommandé

1. **Infrastructure** : `state.py`, `tools/common.py`, `ToolCallLog` model, migration Alembic
2. **Premier noeud pilote** : `profiling_tools.py` + refactoring `profiling_node` dans `nodes.py`
3. **SSE refactoring** : `chat.py` avec `astream_events()`
4. **Frontend** : `useChat.ts` + `ToolCallIndicator.vue`
5. **Tests E2E du pilote** : vérifier le flow complet profiling
6. **Déploiement des autres noeuds** : ESG → Carbon → Financing → Application → Credit → Document → Action Plan → Chat
7. **Journalisation** : logging des tool calls
8. **Tests complets** : couverture 80%+

## Commandes de développement

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Migration (après création du modèle ToolCallLog)
alembic revision --autogenerate -m "add tool_call_logs table"
alembic upgrade head

# Tests backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend
cd frontend && npm run dev

# Tests frontend
npm run test
```
