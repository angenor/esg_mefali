"""Chaîne LangChain pour l'analyse intelligente de documents."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.modules.documents.schemas import (
    DocumentAnalysisOutput,
    DocumentTypeEnum,
    ESGRelevantInfo,
)

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Tu es un analyste expert en documents d'entreprise et en ESG (Environnement, Social, Gouvernance) \
spécialisé dans le contexte des PME africaines francophones.

Analyse le texte du document fourni et produis une analyse structurée complète.

Instructions :
1. **Type de document** : identifie le type parmi : statuts_juridiques, rapport_activite, facture, contrat, \
politique_interne, bilan_financier, autre.{type_hint}
2. **Résumé** : rédige un résumé en français de 3-5 phrases couvrant les points essentiels.
3. **Points clés** : extrais 5-10 points clés factuels (chiffres, dates, noms, décisions importantes).
4. **Données structurées** : extrais les données chiffrées clés dans un dictionnaire (montants, effectifs, \
dates, ratios). Utilise des noms de clés en français snake_case.
5. **Informations ESG** : classe les informations pertinentes par pilier :
   - Environmental : pratiques environnementales, énergie, déchets, émissions
   - Social : emploi, formation, diversité, conditions de travail
   - Governance : transparence, gouvernance, conformité, audit

Contexte : PME en zone UEMOA/CEDEAO. Devise principale : XOF (franc CFA).

Texte du document :
{document_text}"""


async def _run_analysis_chain(
    text: str,
    document_type_hint: str | None = None,
) -> DocumentAnalysisOutput:
    """Exécuter la chaîne d'analyse via le LLM."""
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    structured_llm = llm.with_structured_output(DocumentAnalysisOutput)

    type_hint_text = ""
    if document_type_hint:
        type_hint_text = f"\n   Indice : le document semble être un '{document_type_hint}'."

    # Tronquer le texte si trop long (limite ~15k chars pour garder de la marge)
    truncated_text = text[:15_000]
    if len(text) > 15_000:
        truncated_text += "\n\n[... texte tronqué ...]"

    prompt = ANALYSIS_PROMPT.format(
        type_hint=type_hint_text,
        document_text=truncated_text,
    )

    result = await structured_llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Analyse ce document et produis le résultat structuré."),
    ])

    return result


async def analyze_document_text(
    text: str,
    document_type_hint: str | None = None,
) -> DocumentAnalysisOutput:
    """Analyser le texte d'un document et retourner une sortie structurée.

    En cas d'erreur LLM, retourne un résultat dégradé.
    """
    try:
        return await _run_analysis_chain(text, document_type_hint)
    except Exception:
        logger.exception("Erreur lors de l'analyse du document")
        return DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.autre,
            summary="Analyse impossible — une erreur est survenue lors du traitement.",
            key_findings=[],
            structured_data={},
            esg_relevant_info=ESGRelevantInfo(),
        )
