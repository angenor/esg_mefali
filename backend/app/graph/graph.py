"""Compilation du graphe LangGraph pour la conversation."""

from langgraph.graph import END, StateGraph

from app.graph.checkpointer import create_checkpointer
from app.graph.nodes import chat_node, document_node, router_node
from app.graph.state import ConversationState


def _route_after_router(state: ConversationState) -> str:
    """Décider du prochain nœud après le routeur.

    Si un document est uploadé, passer par document_node d'abord.
    """
    if state.get("has_document"):
        return "document"
    return "chat"


def build_graph() -> StateGraph:
    """Construire le graphe de conversation multi-nœuds.

    Structure :
        START → router_node → [has_document] → document_node → chat_node → END
                            → [no_document]  → chat_node → END
    """
    graph = StateGraph(ConversationState)

    graph.add_node("router", router_node)
    graph.add_node("document", document_node)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {"document": "document", "chat": "chat"},
    )
    graph.add_edge("document", "chat")
    graph.add_edge("chat", END)

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
