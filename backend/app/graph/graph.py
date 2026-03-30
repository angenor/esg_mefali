"""Compilation du graphe LangGraph pour la conversation."""

from langgraph.graph import END, StateGraph

from app.graph.checkpointer import create_checkpointer
from app.graph.nodes import chat_node, router_node
from app.graph.state import ConversationState


def build_graph() -> StateGraph:
    """Construire le graphe de conversation multi-nœuds.

    Structure :
        START → router_node → chat_node → END
    Le router_node analyse le message et prépare le state
    (détection d'extraction, instructions de profilage).
    Le profiling_node sera ajouté en phase 3 (US1).
    """
    graph = StateGraph(ConversationState)

    graph.add_node("router", router_node)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "chat")
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
