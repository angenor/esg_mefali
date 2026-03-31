"""Nœuds du graphe de conversation LangGraph."""

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.graph.state import ConversationState
from app.modules.company.service import FIELD_LABELS, IDENTITY_FIELDS
from app.prompts.system import build_system_prompt

logger = logging.getLogger(__name__)

TITLE_PROMPT = (
    "Résume cette conversation en un titre court (5 mots maximum) en français. "
    "Réponds uniquement avec le titre, sans guillemets ni ponctuation finale."
)

# Heuristiques pour détecter des infos de profil dans un message
_PROFILE_KEYWORDS = [
    r"\bemploy[ée]s?\b", r"\bsalari[ée]s?\b", r"\beffectifs?\b",
    r"\bchiffre d'affaires\b", r"\brevenu\b", r"\b[Cc][Aa]\b",
    r"\bmillions?\b", r"\bFCFA\b", r"\bXOF\b",
    r"\bagriculture\b", r"\b[ée]nergie\b", r"\brecyclage\b",
    r"\btransport\b", r"\bconstruction\b", r"\btextile\b",
    r"\bagroalimentaire\b", r"\bcommerce\b", r"\bartisan",
    r"\bAbidjan\b", r"\bDakar\b", r"\bBamako\b", r"\bOuagadougou\b",
    r"\bLom[ée]\b", r"\bCotonou\b", r"\bNiamey\b", r"\bConakry\b",
    r"\bDouala\b", r"\bYaound[ée]\b", r"\bKinshasa\b",
    r"\bentreprise\b", r"\bsoci[ée]t[ée]\b", r"\bSARL\b", r"\bSA\b",
    r"\bcr[ée][ée]e?\s+en\b", r"\bfond[ée]e?\s+en\b",
    r"\bd[ée]chets?\b", r"\b[ée]nerg[ée]tique\b", r"\bformation\b",
    r"\bgouvernance\b", r"\benvironnement", r"\bgenre\b",
    r"\d+\s*personnes?\b", r"\d+\s*employ",
]
_PROFILE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _PROFILE_KEYWORDS]

# Heuristiques pour détecter une demande de module spécifique (ESG, carbone, financement)
_MODULE_KEYWORDS = [
    r"\bscoring\s+ESG\b", r"\bscore\s+ESG\b", r"\banalyse\s+ESG\b",
    r"\bconformit[ée]\s+ESG\b", r"\baudit\s+ESG\b", r"\b[ée]valuation\s+ESG\b",
    r"\bempreinte\s+carbone\b", r"\bcarbone\b", r"\btCO2", r"\bCO2\b",
    r"\b[ée]missions?\s+de\s+gaz\b", r"\bgaz\s+[àa]\s+effet\b",
    r"\bfonds?\s+verts?\b", r"\bfinancement\s+vert\b", r"\bfonds?\s+climat\b",
    r"\bGCF\b", r"\bFEM\b", r"\bBOAD\b", r"\bBAD\b",
    r"\bsubvention", r"\bcr[ée]dit\s+vert\b",
    r"\bplan\s+d'action\b", r"\bfeuille\s+de\s+route\b",
    r"\bdossier\s+de\s+candidature\b",
]
_MODULE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _MODULE_KEYWORDS]


def _detect_module_request(text: str) -> bool:
    """Détecter si un message est une demande de module spécifique."""
    return any(pattern.search(text) for pattern in _MODULE_PATTERNS)


def _compute_identity_completion(profile: dict | None) -> float:
    """Calculer le pourcentage de complétion identité/localisation."""
    if not profile:
        return 0.0
    filled = sum(
        1 for field in IDENTITY_FIELDS
        if profile.get(field) is not None and profile.get(field) != ""
    )
    return (filled / len(IDENTITY_FIELDS)) * 100 if IDENTITY_FIELDS else 0.0


def _build_profiling_instructions(profile: dict | None) -> str:
    """Construire les instructions de profilage avec les champs manquants."""
    missing_fields: list[str] = []
    for field in IDENTITY_FIELDS:
        value = profile.get(field) if profile else None
        if value is None or value == "":
            label = FIELD_LABELS.get(field, field)
            missing_fields.append(f"- {field} ({label})")

    if not missing_fields:
        return ""

    return (
        "PROFILAGE GUIDÉ : Le profil de l'entreprise est incomplet. "
        "Intègre naturellement UNE question sur un champ manquant dans ta réponse. "
        "Ne pose pas la question de façon abrupte, intègre-la dans le fil de la conversation.\n"
        "Champs manquants :\n" + "\n".join(missing_fields)
    )


def get_llm() -> ChatOpenAI:
    """Créer une instance du LLM configurée pour OpenRouter."""
    return ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        streaming=True,
    )


def _detect_profile_info(text: str) -> bool:
    """Détecter si un message contient potentiellement des infos de profil."""
    return any(pattern.search(text) for pattern in _PROFILE_PATTERNS)


async def router_node(state: ConversationState) -> ConversationState:
    """Nœud routeur : analyse le message et décide du routage.

    - Détecte si le message contient des infos extractibles
    - Détecte la présence d'un document uploadé
    - Vérifie si le profil est < 70% pour le profilage guidé
    - Stocke les décisions de routage dans le state
    """
    messages = state["messages"]
    user_profile = state.get("user_profile")

    # Récupérer le dernier message utilisateur
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    # Détecter la présence d'un document uploadé
    has_document = state.get("document_upload") is not None

    # Décider si on doit extraire des infos de profil
    should_extract = _detect_profile_info(last_user_msg) if last_user_msg else False

    # Profilage guidé : injecter des instructions si profil < 70% et message générique
    profiling_instructions: str | None = None
    identity_pct = _compute_identity_completion(user_profile)
    if identity_pct < 70.0 and last_user_msg and not _detect_module_request(last_user_msg):
        instructions = _build_profiling_instructions(user_profile)
        if instructions:
            profiling_instructions = instructions

    return {
        "profile_updates": [] if should_extract else None,
        "profiling_instructions": profiling_instructions,
        "has_document": has_document,
    }


async def analyze_document_for_chat(
    document_id: str,
    user_id: str,
) -> tuple:
    """Analyser un document pour le contexte chat.

    Charge le document depuis la BDD, lance l'analyse, et retourne
    le document et l'analyse.
    """
    import uuid as uuid_mod

    from app.chains.analysis import analyze_document_text
    from app.core.database import async_session_factory
    from app.modules.documents.service import (
        analyze_document,
        get_document,
    )

    async with async_session_factory() as db:
        document = await get_document(db, uuid_mod.UUID(document_id))
        if document is None:
            raise ValueError(f"Document {document_id} introuvable")

        # Lancer l'analyse si pas encore faite
        if document.analysis is None:
            analysis = await analyze_document(db, document)
        else:
            analysis = document.analysis

        await db.commit()
        return document, analysis


async def document_node(state: ConversationState) -> ConversationState:
    """Nœud document : analyse le document uploadé et injecte le résumé.

    Appelé quand le routeur détecte un document uploadé.
    Analyse le document, stocke les résultats, et ajoute le résumé
    au state pour enrichir le contexte du chat_node.
    """
    doc_upload = state.get("document_upload")
    if not doc_upload:
        return {"document_analysis_summary": None}

    document_id = doc_upload.get("document_id")
    user_id = doc_upload.get("user_id")

    try:
        document, analysis = await analyze_document_for_chat(
            document_id=document_id,
            user_id=user_id,
        )

        # Construire le résumé pour injection dans le contexte
        summary_parts = [
            f"Document analysé : {doc_upload.get('filename', 'document')}",
            f"Type : {analysis.document_type.value if hasattr(analysis, 'document_type') else getattr(document, 'document_type', 'inconnu')}",
        ]

        if hasattr(analysis, "summary") and analysis.summary:
            summary_parts.append(f"Résumé : {analysis.summary}")

        if hasattr(analysis, "key_findings") and analysis.key_findings:
            findings = analysis.key_findings
            if isinstance(findings, list):
                findings_text = "\n".join(f"- {f}" for f in findings[:5])
                summary_parts.append(f"Points clés :\n{findings_text}")

        if hasattr(analysis, "esg_relevant_info") and analysis.esg_relevant_info:
            esg = analysis.esg_relevant_info
            if hasattr(esg, "model_dump"):
                esg = esg.model_dump()
            if isinstance(esg, dict):
                esg_parts = []
                for pillar, items in esg.items():
                    if items:
                        esg_parts.append(f"  {pillar}: {', '.join(items[:3])}")
                if esg_parts:
                    summary_parts.append("ESG :\n" + "\n".join(esg_parts))

        analysis_summary = "\n\n".join(summary_parts)

        return {"document_analysis_summary": analysis_summary}

    except Exception:
        logger.exception("Erreur lors de l'analyse du document dans le chat")
        return {
            "document_analysis_summary": (
                f"Document reçu : {doc_upload.get('filename', 'document')}. "
                "Une erreur est survenue lors de l'analyse. "
                "Veuillez réessayer ou uploader le document depuis la page Documents."
            ),
        }


async def chat_node(state: ConversationState) -> ConversationState:
    """Nœud principal : envoie les messages au LLM et retourne la réponse."""
    llm = get_llm()

    user_profile = state.get("user_profile")
    context_memory = state.get("context_memory", [])
    profiling_instructions = state.get("profiling_instructions")
    document_summary = state.get("document_analysis_summary")

    # Construire le prompt système dynamique
    system_prompt = build_system_prompt(
        user_profile, context_memory, profiling_instructions,
        document_analysis_summary=document_summary,
    )

    # Ajouter le prompt système en tête
    messages = state["messages"]
    chat_messages = [SystemMessage(content=system_prompt), *[
        m for m in messages if not isinstance(m, SystemMessage)
    ]]

    response = await llm.ainvoke(chat_messages)

    return {"messages": [response]}


async def profiling_node(state: ConversationState) -> ConversationState:
    """Nœud de profilage : extrait les infos d'entreprise du message.

    Appelé quand le routeur détecte des infos extractibles.
    Utilise la chaîne d'extraction structurée pour analyser le message
    et retourne les champs extraits dans profile_updates.
    """
    from app.chains.extraction import extract_profile_from_message
    from app.modules.company.service import FIELD_LABELS

    messages = state["messages"]
    user_profile = state.get("user_profile") or {}

    # Récupérer le dernier message utilisateur
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {"profile_updates": []}

    extraction = await extract_profile_from_message(last_user_msg, user_profile)

    # Convertir l'extraction en liste de mises à jour (dictionnaire plat)
    profile_updates: list[dict] = []
    for field, value in extraction.flat_dict().items():
        display_value = value.value if hasattr(value, "value") else value
        profile_updates.append({
            "field": field,
            "value": display_value,
            "label": FIELD_LABELS.get(field, field),
        })

    return {"profile_updates": profile_updates}


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
        return title[:50] if title else "Conversation"
    except Exception:
        logger.exception("Erreur lors de la génération du titre")
        return "Conversation"
