"""État de la conversation LangGraph."""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ConversationState(TypedDict):
    """État partagé entre les nœuds du graphe de conversation."""

    messages: Annotated[list, add_messages]
