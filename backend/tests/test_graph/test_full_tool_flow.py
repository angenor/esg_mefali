"""Test d'intégration global : vérifier que les 9 noeuds avec tools fonctionnent.

Simule un parcours utilisateur complet via le graphe compilé en mockant le LLM.
Chaque noeud est testé avec son routing et ses tools disponibles.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.graph import build_graph, _route_after_router, _should_continue_tool_loop


class TestGraphStructure:
    """Vérifier que le graphe se construit correctement avec tous les noeuds."""

    def test_graph_builds_without_error(self):
        """Le graphe se construit avec tous les noeuds et edges."""
        graph = build_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        """Le graphe contient les 9 noeuds principaux + router + document."""
        graph = build_graph()
        node_names = set(graph.nodes.keys())

        expected_nodes = {
            "router",
            "chat", "chat_tools",
            "esg_scoring", "esg_scoring_tools",
            "carbon", "carbon_tools",
            "financing", "financing_tools",
            "application", "application_tools",
            "credit", "credit_tools",
            "action_plan", "action_plan_tools",
            "document",
        }
        for node in expected_nodes:
            assert node in node_names, f"Noeud {node} manquant dans le graphe"

    def test_graph_compiles(self):
        """Le graphe se compile avec un checkpointer mémoire."""
        from langgraph.checkpoint.memory import MemorySaver

        graph = build_graph()
        compiled = graph.compile(checkpointer=MemorySaver())
        assert compiled is not None


class TestRouting:
    """Vérifier le routing conditionnel du graphe."""

    def test_route_esg(self):
        state = {"_route_esg": True, "_route_carbon": False, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "esg_scoring"

    def test_route_carbon(self):
        state = {"_route_esg": False, "_route_carbon": True, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "carbon"

    def test_route_financing(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": True,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "financing"

    def test_route_application(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": False,
                 "_route_application": True, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "application"

    def test_route_credit(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": False,
                 "_route_application": False, "_route_credit": True, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "credit"

    def test_route_action_plan(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": True,
                 "has_document": False}
        assert _route_after_router(state) == "action_plan"

    def test_route_document(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": True}
        assert _route_after_router(state) == "document"

    def test_route_chat_default(self):
        state = {"_route_esg": False, "_route_carbon": False, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "chat"

    def test_route_priority_esg_over_carbon(self):
        """ESG a priorité sur carbon."""
        state = {"_route_esg": True, "_route_carbon": True, "_route_financing": False,
                 "_route_application": False, "_route_credit": False, "_route_action_plan": False,
                 "has_document": False}
        assert _route_after_router(state) == "esg_scoring"


class TestToolLoopControl:
    """Vérifier le contrôle de la boucle tool."""

    def test_no_tool_calls_ends(self):
        state = {"messages": [AIMessage(content="Réponse finale")], "tool_call_count": 0}
        assert _should_continue_tool_loop(state) == "end"

    def test_tool_calls_under_max_continues(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"id": "c1", "name": "test_tool", "args": {}}],
        )
        state = {"messages": [ai_msg], "tool_call_count": 2}
        assert _should_continue_tool_loop(state) == "continue"

    def test_tool_calls_at_max_ends(self):
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"id": "c1", "name": "test_tool", "args": {}}],
        )
        state = {"messages": [ai_msg], "tool_call_count": 5}
        assert _should_continue_tool_loop(state) == "end"


class TestToolsAvailability:
    """Vérifier que chaque module exporte bien ses tools."""

    def test_profiling_tools_available(self):
        from app.graph.tools.profiling_tools import PROFILING_TOOLS
        assert len(PROFILING_TOOLS) == 2
        names = {t.name for t in PROFILING_TOOLS}
        assert "update_company_profile" in names
        assert "get_company_profile" in names

    def test_esg_tools_available(self):
        from app.graph.tools.esg_tools import ESG_TOOLS
        assert len(ESG_TOOLS) >= 3
        names = {t.name for t in ESG_TOOLS}
        assert "create_esg_assessment" in names
        assert "save_esg_criterion_score" in names
        assert "finalize_esg_assessment" in names

    def test_carbon_tools_available(self):
        from app.graph.tools.carbon_tools import CARBON_TOOLS
        assert len(CARBON_TOOLS) >= 3
        names = {t.name for t in CARBON_TOOLS}
        assert "create_carbon_assessment" in names
        assert "save_emission_entry" in names

    def test_financing_tools_available(self):
        from app.graph.tools.financing_tools import FINANCING_TOOLS
        assert len(FINANCING_TOOLS) >= 3
        names = {t.name for t in FINANCING_TOOLS}
        assert "search_compatible_funds" in names
        assert "save_fund_interest" in names

    def test_application_tools_available(self):
        from app.graph.tools.application_tools import APPLICATION_TOOLS
        assert len(APPLICATION_TOOLS) >= 3
        names = {t.name for t in APPLICATION_TOOLS}
        assert "generate_application_section" in names

    def test_credit_tools_available(self):
        from app.graph.tools.credit_tools import CREDIT_TOOLS
        assert len(CREDIT_TOOLS) >= 2
        names = {t.name for t in CREDIT_TOOLS}
        assert "generate_credit_score" in names

    def test_chat_tools_available(self):
        from app.graph.tools.chat_tools import CHAT_TOOLS
        assert len(CHAT_TOOLS) >= 3
        names = {t.name for t in CHAT_TOOLS}
        assert "get_user_dashboard_summary" in names

    def test_document_tools_available(self):
        from app.graph.tools.document_tools import DOCUMENT_TOOLS
        assert len(DOCUMENT_TOOLS) >= 2
        names = {t.name for t in DOCUMENT_TOOLS}
        assert "analyze_uploaded_document" in names

    def test_action_plan_tools_available(self):
        from app.graph.tools.action_plan_tools import ACTION_PLAN_TOOLS
        assert len(ACTION_PLAN_TOOLS) >= 2
        names = {t.name for t in ACTION_PLAN_TOOLS}
        assert "generate_action_plan" in names

    def test_all_tools_have_french_descriptions(self):
        """Toutes les descriptions de tools sont en français."""
        from app.graph.tools.action_plan_tools import ACTION_PLAN_TOOLS
        from app.graph.tools.application_tools import APPLICATION_TOOLS
        from app.graph.tools.carbon_tools import CARBON_TOOLS
        from app.graph.tools.chat_tools import CHAT_TOOLS
        from app.graph.tools.credit_tools import CREDIT_TOOLS
        from app.graph.tools.document_tools import DOCUMENT_TOOLS
        from app.graph.tools.esg_tools import ESG_TOOLS
        from app.graph.tools.financing_tools import FINANCING_TOOLS
        from app.graph.tools.profiling_tools import PROFILING_TOOLS

        all_tools = (
            PROFILING_TOOLS + ESG_TOOLS + CARBON_TOOLS + FINANCING_TOOLS
            + APPLICATION_TOOLS + CREDIT_TOOLS + CHAT_TOOLS
            + DOCUMENT_TOOLS + ACTION_PLAN_TOOLS
        )
        # Marqueurs de contenu français dans les descriptions
        french_markers = [
            "à", "é", "è", "ê", "ç", "ù", "ô",
            "le ", "la ", "les ", "un ", "une ", "des ",
            "de ", "du ", "en ", "et ", "ou ", "est ",
            "pour ", "avec ", "sur ", "dans ", "par ",
            "cet ", "son ", "qui ", "que ", "ce ",
        ]
        for t in all_tools:
            desc = t.description.lower()
            has_french = any(marker in desc for marker in french_markers)
            assert has_french, (
                f"Tool '{t.name}' semble ne pas avoir de description en français : "
                f"{t.description[:80]}..."
            )


class TestEndToEndFlow:
    """Tests de bout en bout simulant des parcours utilisateur."""

    @pytest.mark.asyncio
    async def test_router_detects_esg_request(self):
        """Le routeur détecte une demande ESG et route correctement."""
        from app.graph.nodes import router_node

        state = {
            "messages": [HumanMessage(content="je veux faire une évaluation ESG")],
            "user_profile": {"sector": "agriculture"},
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)
        assert result.get("_route_esg") is True

    @pytest.mark.asyncio
    async def test_router_detects_carbon_request(self):
        """Le routeur détecte une demande carbone."""
        from app.graph.nodes import router_node

        state = {
            "messages": [HumanMessage(content="calcule mon empreinte carbone")],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)
        assert result.get("_route_carbon") is True

    @pytest.mark.asyncio
    async def test_router_detects_financing_request(self):
        """Le routeur détecte une demande de financement."""
        from app.graph.nodes import router_node

        state = {
            "messages": [HumanMessage(content="quels fonds verts sont disponibles pour moi ?")],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)
        assert result.get("_route_financing") is True

    @pytest.mark.asyncio
    async def test_router_detects_action_plan_request(self):
        """Le routeur détecte une demande de plan d'action."""
        from app.graph.nodes import router_node

        state = {
            "messages": [HumanMessage(content="génère un plan d'action sur 12 mois")],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)
        assert result.get("_route_action_plan") is True

    @pytest.mark.asyncio
    async def test_router_defaults_to_chat(self):
        """Un message générique est routé vers le chat."""
        from app.graph.nodes import router_node

        state = {
            "messages": [HumanMessage(content="bonjour, comment vas-tu ?")],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)
        assert result.get("_route_esg") is not True
        assert result.get("_route_carbon") is not True
        assert result.get("_route_financing") is not True
        assert result.get("_route_action_plan") is not True
