"""Chaîne LangChain pour l'extraction structurée du profil entreprise."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.modules.company.schemas import ProfileExtraction

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Tu es un extracteur d'informations d'entreprise.
Analyse le message de l'utilisateur et extrais UNIQUEMENT les informations d'entreprise mentionnées \
avec une confiance élevée.

Règles :
- Ne retourne que les champs explicitement mentionnés dans le message
- Si une information est ambiguë, ne la retourne PAS (laisse le champ null)
- Si le message contient des corrections ("en fait", "plutôt", "non"), retiens la dernière version
- Les montants en "millions" doivent être convertis en valeur absolue (50 millions = 50000000)
- Détecte les secteurs parmi : agriculture, energie, recyclage, transport, construction, textile, agroalimentaire, services, commerce, artisanat, autre
- Les villes africaines francophones sont les plus probables (Abidjan, Dakar, Bamako, Ouagadougou, etc.)
- Pour employee_count, cherche des nombres suivis de "employés", "salariés", "personnes", "collaborateurs"
- Pour les booléens ESG, retourne true/false seulement si explicitement mentionné

Profil actuel de l'entreprise (pour contexte, ne le répète pas) :
{current_profile}

Message de l'utilisateur à analyser :
{user_message}"""


async def _run_extraction(
    user_message: str,
    current_profile: dict,
) -> ProfileExtraction:
    """Exécuter l'extraction structurée via le LLM."""
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    structured_llm = llm.with_structured_output(ProfileExtraction)

    profile_str = "\n".join(
        f"- {k}: {v}" for k, v in current_profile.items()
        if v is not None and v != ""
    ) or "Aucun profil renseigné"

    prompt = EXTRACTION_PROMPT.format(
        current_profile=profile_str,
        user_message=user_message,
    )

    result = await structured_llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=user_message),
    ])

    return result


async def extract_profile_from_message(
    user_message: str,
    current_profile: dict,
) -> ProfileExtraction:
    """Extraire les informations de profil depuis un message utilisateur.

    Retourne un ProfileExtraction avec uniquement les champs détectés.
    En cas d'erreur, retourne une extraction vide.
    """
    try:
        return await _run_extraction(user_message, current_profile)
    except Exception:
        logger.exception("Erreur lors de l'extraction du profil")
        return ProfileExtraction()
