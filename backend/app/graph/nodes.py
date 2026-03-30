"""Nœuds du graphe de conversation LangGraph."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.graph.state import ConversationState
from app.prompts.system import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

TITLE_PROMPT = (
    "Résume cette conversation en un titre court (5 mots maximum) en français. "
    "Réponds uniquement avec le titre, sans guillemets ni ponctuation finale."
)


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


async def generate_title(user_content: str, assistant_content: str) -> str:
    """Générer un titre court pour une conversation à partir du premier échange."""
    llm = get_llm()
    context = f"Message utilisateur : {user_content[:200]}\nRéponse assistant : {assistant_content[:200]}"
    try:
        response = await llm.ainvoke([
            SystemMessage(content=TITLE_PROMPT),
            HumanMessage(content=context),
        ])
        title = response.content.strip().rstrip(".")
        # Limiter a 50 caracteres
        return title[:50] if title else "Conversation"
    except Exception:
        logger.exception("Erreur lors de la génération du titre")
        return "Conversation"
