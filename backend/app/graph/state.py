"""État de la conversation LangGraph."""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ConversationState(TypedDict):
    """État partagé entre les nœuds du graphe de conversation."""

    messages: Annotated[list, add_messages]
    user_profile: dict | None
    context_memory: list[str]
    profile_updates: list[dict] | None
    profiling_instructions: str | None
    document_upload: dict | None
    document_analysis_summary: str | None
    has_document: bool
    esg_assessment: dict | None
    _route_esg: bool
    carbon_data: dict | None
    _route_carbon: bool
    financing_data: dict | None
    _route_financing: bool
    application_data: dict | None
    _route_application: bool
