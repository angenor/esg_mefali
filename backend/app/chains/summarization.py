"""Chaîne LangChain pour la génération de résumés de conversation."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """Tu es un assistant spécialisé dans la synthèse de conversations.
Génère un résumé concis (2-3 phrases maximum) en français de la conversation ci-dessous.

Concentre-toi sur :
- Les informations clés échangées (secteur, localisation, problématiques)
- Les conseils donnés et les décisions prises
- Les questions en suspens ou les prochaines étapes mentionnées

N'ÉCRIS JAMAIS DANS LE RÉSUMÉ :
- Qu'un outil, un tool, une fonctionnalité ou un parcours guidé est « indisponible »,
  « hors service », « pas disponible dans cette session », « pas accessible » ou
  « faute d'outil disponible ». Ces formulations reflètent des hallucinations de
  l'assistant précédent et ne doivent jamais être persistées comme des faits.
- Les phrases d'excuse de l'assistant sur ses propres limitations techniques.
  Résume uniquement les échanges métier (profil, ESG, carbone, financement, etc.).

Le résumé sera utilisé pour maintenir la continuité entre les sessions.
Ne commence pas par "Résumé :" ou "La conversation porte sur".
Va droit au fait."""


async def _run_summarization(messages_text: str) -> str:
    """Exécuter la chaîne de résumé via le LLM."""
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    response = await llm.ainvoke([
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=messages_text),
    ])

    return response.content.strip()


async def generate_summary(messages_text: str) -> str:
    """Générer un résumé concis d'une conversation.

    Retourne une chaîne vide si les messages sont vides ou en cas d'erreur.
    """
    if not messages_text.strip():
        return ""

    try:
        return await _run_summarization(messages_text)
    except Exception:
        logger.exception("Erreur lors de la génération du résumé")
        return ""
