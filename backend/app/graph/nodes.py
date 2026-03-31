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

# Heuristiques pour détecter une demande d'évaluation ESG spécifiquement
_ESG_KEYWORDS = [
    r"\b[ée]valuation\s+ESG\b", r"\b[ée]valuer\s+.*ESG\b",
    r"\bscoring\s+ESG\b", r"\bscore\s+ESG\b",
    r"\banalyse\s+ESG\b", r"\baudit\s+ESG\b",
    r"\blancer\s+.*[ée]valuation\b.*\bESG\b",
    r"\bmon\s+score\s+ESG\b", r"\bcriteres?\s+ESG\b",
    r"\bdiagnostic\s+ESG\b", r"\bbilan\s+ESG\b",
]
_ESG_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _ESG_KEYWORDS]

# Heuristiques pour detecter une demande de bilan carbone
_CARBON_KEYWORDS = [
    r"\bempreinte\s+carbone\b", r"\bbilan\s+carbone\b",
    r"\bcalcul.*carbone\b", r"\bcalculer.*carbone\b",
    r"\btCO2e?\b", r"\bCO2\b",
    r"\b[ée]missions?\s+de\s+gaz\b", r"\bgaz\s+[àa]\s+effet\b",
    r"\bempreinte\s+[ée]cologique\b", r"\bimpact\s+carbone\b",
    r"\br[ée]duction.*[ée]missions?\b",
]
_CARBON_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _CARBON_KEYWORDS]

# Heuristiques pour detecter une demande de financement vert
_FINANCING_KEYWORDS = [
    r"\bfinancement\s+vert\b", r"\bfonds?\s+verts?\b",
    r"\bfonds?\s+climat\b", r"\bfonds?\s+d'adaptation\b",
    r"\bSUNREF\b", r"\bGCF\b", r"\bFEM\b", r"\bBOAD\b", r"\bBAD\b",
    r"\bBIDC\b", r"\bFNDE\b", r"\bSEFA\b",
    r"\bGold\s+Standard\b", r"\bVerra\b", r"\bIFC\b", r"\bBCEAO\b",
    r"\bcr[ée]dit\s+carbone\b", r"\bcr[ée]dits?\s+verts?\b",
    r"\bsubvention.*vert\b", r"\bsubventions?\s+climat\b",
    r"\bbanque\s+partenaire\b", r"\bbanque\s+verte\b",
    r"\binterm[ée]diaire.*financ\b", r"\bfinancement.*interm[ée]diaire\b",
    r"\bdossier\s+de\s+candidature\b",
    r"\bacc[ée]der.*financement\b", r"\bfinancement.*acc[ée]der\b",
    r"\bobtenir.*financement\b", r"\bfinancement.*obtenir\b",
    r"\b[ée]ligibilit[ée].*fonds\b", r"\bfonds.*[ée]ligib\b",
    r"\bligne\s+de\s+cr[ée]dit\s+vert\b",
]
_FINANCING_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _FINANCING_KEYWORDS]


def _detect_financing_request(text: str) -> bool:
    """Detecter si un message est une demande de financement vert."""
    return any(pattern.search(text) for pattern in _FINANCING_PATTERNS)


def _detect_carbon_request(text: str) -> bool:
    """Detecter si un message est une demande de bilan carbone."""
    return any(pattern.search(text) for pattern in _CARBON_PATTERNS)


def _has_active_carbon_assessment(state: dict) -> bool:
    """Verifier si un bilan carbone est en cours dans le state."""
    carbon = state.get("carbon_data")
    if carbon is None:
        return False
    return carbon.get("status") == "in_progress"


def _detect_esg_request(text: str) -> bool:
    """Détecter si un message est une demande d'évaluation ESG."""
    return any(pattern.search(text) for pattern in _ESG_PATTERNS)


def _has_active_esg_assessment(state: dict) -> bool:
    """Vérifier si une évaluation ESG est en cours dans le state."""
    esg = state.get("esg_assessment")
    if esg is None:
        return False
    return esg.get("status") == "in_progress"


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

    # Détecter si c'est une demande ESG ou une évaluation en cours
    esg_assessment = state.get("esg_assessment")
    is_esg_request = _detect_esg_request(last_user_msg) if last_user_msg else False
    has_active_esg = _has_active_esg_assessment(state)

    # Detecter si c'est une demande de bilan carbone ou un bilan en cours
    carbon_data = state.get("carbon_data")
    is_carbon_request = _detect_carbon_request(last_user_msg) if last_user_msg else False
    has_active_carbon = _has_active_carbon_assessment(state)

    # Detecter si c'est une demande de financement
    financing_data = state.get("financing_data")
    is_financing_request = _detect_financing_request(last_user_msg) if last_user_msg else False

    # Décider si on doit extraire des infos de profil
    should_extract = _detect_profile_info(last_user_msg) if last_user_msg else False

    # Profilage guidé : injecter des instructions si profil < 70% et message générique
    profiling_instructions: str | None = None
    identity_pct = _compute_identity_completion(user_profile)
    if identity_pct < 70.0 and last_user_msg and not _detect_module_request(last_user_msg) and not is_esg_request and not has_active_esg and not is_carbon_request and not has_active_carbon and not is_financing_request:
        instructions = _build_profiling_instructions(user_profile)
        if instructions:
            profiling_instructions = instructions

    return {
        "profile_updates": [] if should_extract else None,
        "profiling_instructions": profiling_instructions,
        "has_document": has_document,
        "esg_assessment": esg_assessment,
        "_route_esg": is_esg_request or has_active_esg,
        "carbon_data": carbon_data,
        "_route_carbon": is_carbon_request or has_active_carbon,
        "financing_data": financing_data,
        "_route_financing": is_financing_request,
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


async def _fetch_rag_context_for_esg(
    user_id: str,
    current_pillar: str,
) -> str:
    """Recuperer le contexte RAG pour le pilier ESG en cours d'evaluation."""
    import uuid as uuid_mod

    from app.core.database import async_session_factory
    from app.modules.esg.service import format_rag_context, search_rag_context_for_pillar

    try:
        async with async_session_factory() as db:
            rag_context = await search_rag_context_for_pillar(
                db=db,
                pillar=current_pillar,
                user_id=uuid_mod.UUID(user_id),
                limit_per_criterion=2,
            )
            return format_rag_context(rag_context)
    except Exception:
        logger.exception("Erreur lors de la recherche RAG pour le pilier %s", current_pillar)
        return ""


async def esg_scoring_node(state: ConversationState) -> ConversationState:
    """Nœud d'évaluation ESG : conduit l'évaluation conversationnelle.

    Gère l'état de l'évaluation (création, progression, finalisation)
    et utilise un prompt spécialisé ESG pour interagir avec l'utilisateur.
    Enrichit le contexte avec les documents de l'utilisateur via RAG.
    """
    from app.prompts.esg_scoring import build_esg_prompt

    llm = get_llm()
    user_profile = state.get("user_profile") or {}
    esg_assessment = state.get("esg_assessment")
    messages = state["messages"]

    # Construire le contexte entreprise pour le prompt ESG
    company_lines: list[str] = []
    if user_profile:
        for key, value in user_profile.items():
            if value is not None and value != "":
                company_lines.append(f"- {key}: {value}")
    company_context = "\n".join(company_lines) if company_lines else "Aucun profil disponible."

    # Contexte documentaire general (si disponible)
    doc_context = state.get("document_analysis_summary") or "Aucun document analyse."

    # Si pas d'évaluation en cours, chercher une evaluation a reprendre ou en creer une nouvelle
    if esg_assessment is None or esg_assessment.get("status") == "completed":
        from app.modules.esg.service import build_initial_esg_state

        # Tenter de reprendre une evaluation interrompue
        resumable = None
        if user_id:
            try:
                import uuid as uuid_mod

                from app.core.database import async_session_factory
                from app.modules.esg.service import get_resumable_assessment

                async with async_session_factory() as db:
                    resumable = await get_resumable_assessment(db, uuid_mod.UUID(str(user_id)))
            except Exception:
                logger.exception("Erreur lors de la recherche d'evaluation a reprendre")

        if resumable is not None:
            esg_assessment = {
                "assessment_id": str(resumable.id),
                "status": resumable.status.value if hasattr(resumable.status, "value") else resumable.status,
                "current_pillar": resumable.current_pillar or "environment",
                "evaluated_criteria": resumable.evaluated_criteria or [],
                "partial_scores": (resumable.assessment_data or {}).get("criteria_scores", {}),
            }
        else:
            esg_assessment = build_initial_esg_state(
                assessment_id="pending",
                sector=user_profile.get("sector", "services"),
            )

    # Recherche RAG par pilier en cours pour enrichir l'evaluation
    current_pillar = esg_assessment.get("current_pillar", "environment")
    user_id = state.get("user_id")
    rag_context = ""
    if user_id:
        rag_context = await _fetch_rag_context_for_esg(
            user_id=str(user_id),
            current_pillar=current_pillar,
        )

    # Fusionner les contextes documentaires
    if rag_context:
        doc_context = f"{doc_context}\n\n{rag_context}"

    # Construire le prompt ESG
    system_prompt = build_esg_prompt(
        company_context=company_context,
        document_context=doc_context,
    )

    # Injecter l'état d'évaluation dans le prompt
    esg_state_context = (
        f"\n\nÉTAT DE L'ÉVALUATION EN COURS :\n"
        f"- Pilier actuel : {esg_assessment.get('current_pillar', 'environment')}\n"
        f"- Critères évalués : {esg_assessment.get('evaluated_criteria', [])}\n"
        f"- Scores partiels : {esg_assessment.get('partial_scores', {})}\n"
    )
    full_prompt = system_prompt + esg_state_context

    # Envoyer au LLM
    chat_messages = [SystemMessage(content=full_prompt), *[
        m for m in messages if not isinstance(m, SystemMessage)
    ]]

    response = await llm.ainvoke(chat_messages)

    return {
        "messages": [response],
        "esg_assessment": esg_assessment,
    }


async def carbon_node(state: ConversationState) -> ConversationState:
    """Noeud de bilan carbone : conduit le questionnaire conversationnel.

    Gere l'etat du bilan (creation, progression par categorie, finalisation)
    et utilise un prompt specialise carbone pour interagir avec l'utilisateur.
    Genere des visualisations inline (chart, gauge, table, timeline).
    """
    from app.prompts.carbon import build_carbon_prompt

    llm = get_llm()
    user_profile = state.get("user_profile") or {}
    carbon_data = state.get("carbon_data")
    messages = state["messages"]

    # Construire le contexte entreprise pour le prompt carbone
    company_lines: list[str] = []
    if user_profile:
        for key, value in user_profile.items():
            if value is not None and value != "":
                company_lines.append(f"- {key}: {value}")
    company_context = "\n".join(company_lines) if company_lines else "Aucun profil disponible."

    # Si pas de bilan en cours, chercher un bilan a reprendre ou en creer un nouveau
    if carbon_data is None or carbon_data.get("status") == "completed":
        from app.modules.carbon.service import build_initial_carbon_state

        # Tenter de reprendre un bilan interrompu
        resumable = None
        user_id = state.get("user_id")
        if user_id:
            try:
                import uuid as uuid_mod

                from app.core.database import async_session_factory
                from app.modules.carbon.service import get_resumable_assessment

                async with async_session_factory() as db:
                    resumable = await get_resumable_assessment(db, uuid_mod.UUID(str(user_id)))
            except Exception:
                logger.exception("Erreur lors de la recherche de bilan carbone a reprendre")

        if resumable is not None:
            applicable_cats = resumable.completed_categories or []
            from app.modules.carbon.emission_factors import get_applicable_categories
            all_applicable = get_applicable_categories(resumable.sector)
            # Determiner la categorie en cours (premiere non completee)
            current = all_applicable[0] if all_applicable else "energy"
            for cat in all_applicable:
                if cat not in applicable_cats:
                    current = cat
                    break

            carbon_data = {
                "assessment_id": str(resumable.id),
                "status": "in_progress",
                "current_category": current,
                "completed_categories": list(applicable_cats),
                "applicable_categories": all_applicable,
                "entries": [],
                "total_emissions_tco2e": resumable.total_emissions_tco2e or 0.0,
                "sector": resumable.sector,
            }
        else:
            sector = user_profile.get("sector", "services")
            if hasattr(sector, "value"):
                sector = sector.value
            carbon_data = build_initial_carbon_state(
                assessment_id="pending",
                sector=sector,
            )

    # Construire les categories applicables en texte
    applicable_text = ", ".join(carbon_data.get("applicable_categories", ["energy", "transport", "waste"]))

    # Construire le prompt carbone
    system_prompt = build_carbon_prompt(
        company_context=company_context,
        applicable_categories=applicable_text,
    )

    # Injecter l'etat du bilan dans le prompt
    carbon_state_context = (
        f"\n\nETAT DU BILAN CARBONE EN COURS :\n"
        f"- Categorie actuelle : {carbon_data.get('current_category', 'energy')}\n"
        f"- Categories completees : {carbon_data.get('completed_categories', [])}\n"
        f"- Categories applicables : {carbon_data.get('applicable_categories', [])}\n"
        f"- Emissions totales actuelles : {carbon_data.get('total_emissions_tco2e', 0)} tCO2e\n"
        f"- Entrees collectees : {len(carbon_data.get('entries', []))}\n"
        f"- Secteur : {carbon_data.get('sector', 'non defini')}\n"
    )
    full_prompt = system_prompt + carbon_state_context

    # Envoyer au LLM
    chat_messages = [SystemMessage(content=full_prompt), *[
        m for m in messages if not isinstance(m, SystemMessage)
    ]]

    response = await llm.ainvoke(chat_messages)

    return {
        "messages": [response],
        "carbon_data": carbon_data,
    }


async def _fetch_rag_context_for_financing(query: str) -> str:
    """Recuperer le contexte RAG pour une question de financement."""
    from app.core.database import async_session_factory
    from app.modules.financing.service import search_financing_chunks

    try:
        async with async_session_factory() as db:
            chunks = await search_financing_chunks(db, query, limit=5)
            if not chunks:
                return ""
            parts = []
            for chunk in chunks:
                source_label = chunk.source_type.value if hasattr(chunk.source_type, "value") else str(chunk.source_type)
                parts.append(f"[{source_label}] {chunk.content}")
            return "\n\n".join(parts)
    except Exception:
        logger.exception("Erreur RAG financement")
        return ""


async def financing_node(state: ConversationState) -> ConversationState:
    """Noeud de conseil en financement vert.

    Repond aux questions sur les financements verts avec des blocs visuels
    (Mermaid, tableaux, timelines, jauges). Utilise le RAG sur financing_chunks.
    """
    from app.prompts.financing import build_financing_prompt

    llm = get_llm()
    user_profile = state.get("user_profile") or {}
    financing_data = state.get("financing_data")
    messages = state["messages"]

    # Construire le contexte entreprise
    company_lines: list[str] = []
    if user_profile:
        for key, value in user_profile.items():
            if value is not None and value != "":
                company_lines.append(f"- {key}: {value}")
    company_context = "\n".join(company_lines) if company_lines else "Aucun profil disponible."

    # Recuperer le dernier message utilisateur pour le RAG
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    # Recherche RAG sur les chunks financement
    rag_context = ""
    if last_user_msg:
        rag_context = await _fetch_rag_context_for_financing(last_user_msg)

    # Construire le prompt financement
    system_prompt = build_financing_prompt(
        company_context=company_context,
        rag_context=rag_context or "Aucune information supplementaire disponible.",
    )

    # Envoyer au LLM
    chat_messages = [SystemMessage(content=system_prompt), *[
        m for m in messages if not isinstance(m, SystemMessage)
    ]]

    response = await llm.ainvoke(chat_messages)

    return {
        "messages": [response],
        "financing_data": financing_data,
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
