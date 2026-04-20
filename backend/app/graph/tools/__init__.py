"""Tools LangChain pour les nœuds LangGraph du conseiller ESG.

Ce package expose le registre agrégé ``INSTRUMENTED_TOOLS`` — l'ensemble des
outils `@tool` wrappés par ``with_retry`` et journalisés dans
``tool_call_logs`` (FR-021 + FR-022 + NFR75).

Chaque module métier expose une liste dédiée utilisée comme sous-ensemble
par le ``ToolNode`` LangGraph correspondant dans ``graph.py``.

Voir ``backend/app/graph/tools/README.md`` pour le guide d'ajout d'un tool.
"""

from app.graph.tools.action_plan_tools import ACTION_PLAN_TOOLS
from app.graph.tools.application_tools import APPLICATION_TOOLS
from app.graph.tools.carbon_tools import CARBON_TOOLS
from app.graph.tools.chat_tools import CHAT_TOOLS
from app.graph.tools.credit_tools import CREDIT_TOOLS
from app.graph.tools.document_tools import DOCUMENT_TOOLS
from app.graph.tools.esg_tools import ESG_TOOLS
from app.graph.tools.financing_tools import FINANCING_TOOLS
from app.graph.tools.guided_tour_tools import GUIDED_TOUR_TOOLS
from app.graph.tools.interactive_tools import INTERACTIVE_TOOLS
# Story 10.3 — maturity_tools ajoute entre PROJECTS et ESG (ordre Cluster A -> A' -> ESG)
from app.graph.tools.maturity_tools import MATURITY_TOOLS
from app.graph.tools.profiling_tools import PROFILING_TOOLS
# Story 10.2 — projects_tools ajoute entre PROFILING et ESG (ordre alpha logique nouveaute)
from app.graph.tools.projects_tools import PROJECTS_TOOLS

INSTRUMENTED_TOOLS: list = [
    *PROFILING_TOOLS,
    *PROJECTS_TOOLS,
    *MATURITY_TOOLS,  # Story 10.3 — Cluster A -> A' -> ESG
    *ESG_TOOLS,
    *CARBON_TOOLS,
    *FINANCING_TOOLS,
    *CREDIT_TOOLS,
    *APPLICATION_TOOLS,
    *DOCUMENT_TOOLS,
    *ACTION_PLAN_TOOLS,
    *CHAT_TOOLS,
    *INTERACTIVE_TOOLS,
    *GUIDED_TOUR_TOOLS,
]

__all__ = [
    "ACTION_PLAN_TOOLS",
    "APPLICATION_TOOLS",
    "CARBON_TOOLS",
    "CHAT_TOOLS",
    "CREDIT_TOOLS",
    "DOCUMENT_TOOLS",
    "ESG_TOOLS",
    "FINANCING_TOOLS",
    "GUIDED_TOUR_TOOLS",
    "INSTRUMENTED_TOOLS",
    "INTERACTIVE_TOOLS",
    "MATURITY_TOOLS",
    "PROFILING_TOOLS",
    "PROJECTS_TOOLS",
]
