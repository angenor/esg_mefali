"""Nœuds du graphe de conversation LangGraph."""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.graph.state import ConversationState
from app.prompts.system import SYSTEM_PROMPT


def get_llm() -> ChatOpenAI:
    """Créer une instance du LLM configurée pour OpenRouter."""
    return ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        streaming=True,
    )


async def chat_node(state: ConversationState) -> ConversationState:
    """Nœud principal : envoie les messages au LLM et retourne la réponse."""
    llm = get_llm()

    # Ajouter le prompt système en tête si absent
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

    response = await llm.ainvoke(messages)

    return {"messages": [response]}
