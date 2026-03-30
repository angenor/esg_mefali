"""Compilation du graphe LangGraph pour la conversation."""

from langgraph.graph import StateGraph

from app.graph.checkpointer import create_checkpointer
from app.graph.nodes import chat_node
from app.graph.state import ConversationState


def build_graph() -> StateGraph:
    """Construire le graphe de conversation (sans checkpointer)."""
    graph = StateGraph(ConversationState)
    graph.add_node("chat", chat_node)
    graph.set_entry_point("chat")
    graph.set_finish_point("chat")
    return graph


async def create_compiled_graph():
    """Compiler le graphe avec le checkpointer.

    Appelé dans le lifespan FastAPI.
    Utilise MemorySaver par defaut (le checkpointer PostgreSQL necessite
    une gestion de connexion async context manager dans le lifespan).
    """
    graph = build_graph()
    from langgraph.checkpoint.memory import MemorySaver
    return graph.compile(checkpointer=MemorySaver())
