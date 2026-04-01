"""Compilation du graphe LangGraph pour la conversation."""

from langgraph.graph import END, StateGraph

from app.graph.checkpointer import create_checkpointer
from app.graph.nodes import action_plan_node, application_node, carbon_node, chat_node, credit_node, document_node, esg_scoring_node, financing_node, router_node
from app.graph.state import ConversationState


def _route_after_router(state: ConversationState) -> str:
    """Décider du prochain nœud après le routeur.

    Priorité : ESG > carbon > financing > application > credit > action_plan > document > chat.
    """
    if state.get("_route_esg"):
        return "esg_scoring"
    if state.get("_route_carbon"):
        return "carbon"
    if state.get("_route_financing"):
        return "financing"
    if state.get("_route_application"):
        return "application"
    if state.get("_route_credit"):
        return "credit"
    if state.get("_route_action_plan"):
        return "action_plan"
    if state.get("has_document"):
        return "document"
    return "chat"


def build_graph() -> StateGraph:
    """Construire le graphe de conversation multi-nœuds.

    Structure :
        START → router_node → [esg]          → esg_scoring_node → END
                             → [carbon]       → carbon_node → END
                             → [financing]    → financing_node → END
                             → [application]  → application_node → END
                             → [credit]       → credit_node → END
                             → [action_plan]  → action_plan_node → END
                             → [has_document] → document_node → chat_node → END
                             → [no_document]  → chat_node → END
    """
    graph = StateGraph(ConversationState)

    graph.add_node("router", router_node)
    graph.add_node("document", document_node)
    graph.add_node("chat", chat_node)
    graph.add_node("esg_scoring", esg_scoring_node)
    graph.add_node("carbon", carbon_node)
    graph.add_node("financing", financing_node)
    graph.add_node("application", application_node)
    graph.add_node("credit", credit_node)
    graph.add_node("action_plan", action_plan_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "esg_scoring": "esg_scoring",
            "carbon": "carbon",
            "financing": "financing",
            "application": "application",
            "credit": "credit",
            "action_plan": "action_plan",
            "document": "document",
            "chat": "chat",
        },
    )
    graph.add_edge("document", "chat")
    graph.add_edge("chat", END)
    graph.add_edge("esg_scoring", END)
    graph.add_edge("carbon", END)
    graph.add_edge("financing", END)
    graph.add_edge("application", END)
    graph.add_edge("credit", END)
    graph.add_edge("action_plan", END)

    return graph


async def create_compiled_graph():
    """Compiler le graphe avec le checkpointer.

    Appelé dans le lifespan FastAPI.
    Utilise MemorySaver par défaut (le checkpointer PostgreSQL nécessite
    une gestion de connexion async context manager dans le lifespan).
    """
    graph = build_graph()
    from langgraph.checkpoint.memory import MemorySaver
    return graph.compile(checkpointer=MemorySaver())
