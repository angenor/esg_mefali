# Implementation Plan: Intégration Tool Calling LangGraph

**Branch**: `012-langgraph-tool-calling` | **Date**: 2026-04-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-langgraph-tool-calling/spec.md`

## Summary

Transformer le conseiller IA d'un chatbot passif en agent capable d'agir en intégrant le tool calling LangChain dans les 9 noeuds LangGraph. Les tools appellent les services métier existants pour sauvegarder/lire/modifier les données en base. Le chemin SSE est refactoré pour utiliser `astream_events()` de LangGraph, permettant le streaming natif des tokens et des événements tool call. L'injection du `user_id` et de la session DB se fait via `RunnableConfig`.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x strict (frontend)
**Primary Dependencies**: FastAPI, LangChain (>=0.3.0), LangGraph (>=0.2.0), langchain-openai (>=0.3.0), SQLAlchemy async
**Storage**: PostgreSQL 16 + pgvector, Alembic pour migrations
**Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)
**Target Platform**: Web application (serveur Linux, navigateurs modernes)
**Project Type**: Web service (monolithe modulaire FastAPI + Nuxt 4)
**Performance Goals**: Tool call execution < 2s, réponse complète (avec tools) < 10s
**Constraints**: Max 5 tool calls par tour, 1 retry automatique par tool, journalisation complète
**Scale/Scope**: 9 noeuds LangGraph × 32 tools total, 1 nouveau modèle DB, 3 nouveaux événements SSE

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Notes |
|----------|--------|-------|
| I. Francophone-First | PASS | UI en français, code en anglais, descriptions tools en français pour le LLM |
| II. Architecture Modulaire | PASS | Tools dans `graph/tools/` par noeud, appellent les services existants des modules |
| III. Conversation-Driven UX | PASS | Le tool calling EST la concrétisation de cette vision — les actions se font via le chat |
| IV. Test-First | PASS | TDD prévu pour chaque noeud : tests des tools isolés, tests d'intégration avec mock LLM |
| V. Sécurité & Données | PASS | user_id injecté via RunnableConfig (pas visible par le LLM), validation Pydantic dans les services |
| VI. Inclusivité | PASS | Messages d'erreur tools en français, indicateurs visuels pendant l'exécution |
| VII. Simplicité & YAGNI | PASS | Pas de nouvelle abstraction — pattern ToolNode standard de LangGraph, services existants réutilisés |

### Post-Phase 1 Re-check

| Principe | Statut | Notes |
|----------|--------|-------|
| II. Architecture Modulaire | PASS | Les tools sont dans un répertoire dédié `graph/tools/`, pas mélangés dans les noeuds. Chaque fichier correspond à un module métier. |
| VII. Simplicité | PASS | `ToolNode` est le pattern standard, pas une abstraction custom. 1 seul nouveau modèle DB (ToolCallLog). |

## Project Structure

### Documentation (this feature)

```text
specs/012-langgraph-tool-calling/
├── plan.md              # Ce fichier
├── spec.md              # Spécification
├── research.md          # Recherche Phase 0
├── data-model.md        # Modèle de données Phase 1
├── quickstart.md        # Guide démarrage Phase 1
├── contracts/
│   ├── sse-events.md    # Contrat événements SSE
│   └── tools-catalog.md # Catalogue des tools par noeud
├── checklists/
│   └── requirements.md  # Checklist qualité spec
└── tasks.md             # Tâches Phase 2 (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── graph/
│   │   ├── state.py          # MODIFIER — ajouter user_id
│   │   ├── nodes.py          # MODIFIER — refactorer 9 noeuds pour bind_tools + boucle ToolNode
│   │   ├── graph.py          # MODIFIER — ajouter ToolNodes conditionnels par noeud
│   │   └── tools/            # CRÉER — 10 fichiers de tools
│   │       ├── __init__.py
│   │       ├── common.py
│   │       ├── profiling_tools.py
│   │       ├── esg_tools.py
│   │       ├── carbon_tools.py
│   │       ├── financing_tools.py
│   │       ├── application_tools.py
│   │       ├── credit_tools.py
│   │       ├── document_tools.py
│   │       ├── action_plan_tools.py
│   │       └── chat_tools.py
│   ├── api/
│   │   └── chat.py           # MODIFIER — SSE via astream_events()
│   ├── models/
│   │   └── tool_call_log.py  # CRÉER
│   └── modules/
│       ├── applications/service.py  # ÉTENDRE — simulate(), export()
│       └── credit/service.py        # ÉTENDRE — generate_certificate()
└── tests/
    ├── test_tools/            # CRÉER — tests unitaires par fichier de tools
    │   ├── test_profiling_tools.py
    │   ├── test_esg_tools.py
    │   ├── test_carbon_tools.py
    │   ├── test_financing_tools.py
    │   ├── test_application_tools.py
    │   ├── test_credit_tools.py
    │   ├── test_document_tools.py
    │   ├── test_action_plan_tools.py
    │   └── test_chat_tools.py
    └── test_graph/
        ├── test_nodes_tool_calling.py  # CRÉER — tests d'intégration noeuds + tools
        └── test_sse_tool_events.py     # CRÉER — tests SSE avec tool calls

frontend/
├── app/
│   ├── composables/
│   │   └── useChat.ts                  # MODIFIER — gérer tool_call_start/end/error
│   └── components/
│       └── chat/
│           └── ToolCallIndicator.vue   # CRÉER — indicateur visuel
└── tests/  # Non requis pour cette feature (les tests E2E couvrent)
```

**Structure Decision**: Structure web application existante (backend/ + frontend/) conservée. Nouveau répertoire `backend/app/graph/tools/` pour les tools LangChain, organisé par noeud (1 fichier = 1 noeud). Pas de nouveau package ni module — les tools importent les services existants.

## Architecture des Noeuds avec Tool Calling

### Pattern par noeud

Chaque noeud spécialiste suit ce pattern dans le graphe LangGraph :

```
specialist_node (LLM + bind_tools)
  → should_continue? (vérifie tool_calls dans la réponse)
    → Oui : tool_node (exécute les tools) → retour à specialist_node
    → Non : END (réponse finale sans tool calls)
```

Le compteur de boucles est géré dans le state pour respecter le max de 5 tools par tour.

### Graphe révisé

```
START → router_node → [conditional routing]
  → profiling_node ⟲ profiling_tool_node
  → esg_scoring_node ⟲ esg_tool_node
  → carbon_node ⟲ carbon_tool_node
  → financing_node ⟲ financing_tool_node
  → application_node ⟲ application_tool_node
  → credit_node ⟲ credit_tool_node
  → document_node ⟲ document_tool_node
  → action_plan_node ⟲ action_plan_tool_node
  → chat_node ⟲ chat_tool_node
→ END
```

### SSE avec astream_events()

Le handler SSE utilise `compiled_graph.astream_events()` qui émet :
- `on_chat_model_stream` → événement SSE `token`
- `on_tool_start` → événement SSE `tool_call_start`
- `on_tool_end` → événement SSE `tool_call_end`

Le mapping des événements LangGraph → SSE se fait dans `api/chat.py`.

## Complexity Tracking

Aucune violation de la constitution détectée. Pas de justification nécessaire.
