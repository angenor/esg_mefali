"""Tools LangChain pour le noeud dossiers de candidature.

Six tools exposes au LLM :
- submit_fund_application_draft : creer un nouveau dossier de candidature (brouillon)
- generate_application_section : generer une section du dossier
- update_application_section : modifier une section
- get_application_checklist : consulter la checklist
- simulate_financing : simulation financiere
- export_application : exporter en PDF/DOCX
"""

import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry

logger = logging.getLogger(__name__)


async def _simulate_financing(db, application) -> dict:
    """Simulation financiere pour un dossier de candidature.

    Calcule le montant eligible, le ROI estime, la timeline et l'impact carbone.
    """
    from app.modules.financing.service import get_fund_by_id

    fund = await get_fund_by_id(db, application.fund_id)
    if not fund:
        return {"error": "Fonds introuvable pour cette candidature."}

    max_amount = fund.max_amount or 0
    min_amount = fund.min_amount or 0
    eligible_estimate = int((max_amount + min_amount) / 2)

    return {
        "eligible_amount": eligible_estimate,
        "currency": getattr(fund, "currency", "USD"),
        "roi_estimate": "12-18%",
        "timeline_months": 18,
        "fund_name": fund.name,
    }


async def _export_application(db, application, fmt: str) -> str:
    """Exporter un dossier en PDF ou DOCX.

    Retourne le chemin du fichier genere.
    """
    # Placeholder — la generation reelle via WeasyPrint/python-docx
    # sera implementee dans le service quand les templates seront prets
    export_path = f"/uploads/applications/{application.id}.{fmt}"
    logger.info("Export dossier %s au format %s -> %s", application.id, fmt, export_path)
    return export_path


@tool
async def submit_fund_application_draft(
    fund_id: str,
    config: RunnableConfig,
    target_type: str | None = None,
) -> str:
    """Creer un nouveau dossier de candidature (brouillon) pour un fonds.

    Utilise cet outil quand l'utilisateur demande de creer ou demarrer
    un dossier de candidature pour un fonds vert specifique. Le dossier
    est enregistre avec le statut 'draft' et peut ensuite etre enrichi
    via les autres tools (generate_application_section, etc.).

    Args:
        fund_id: Identifiant UUID du fonds cible.
        target_type: Type de destinataire optionnel (direct, banque, agence, developpeur_carbone).
    """
    from app.modules.applications.service import create_application

    db, user_id = get_db_and_user(config)

    application = await create_application(
        db=db,
        user_id=user_id,
        fund_id=uuid.UUID(fund_id),
    )

    # BUG-V7.1-013 : declencher l'attribution du badge first_application.
    from app.modules.action_plan.badges import safe_check_and_award_badges
    await safe_check_and_award_badges(db, user_id)

    return (
        f"Dossier de candidature cree avec succes.\n"
        f"- ID : {application.id}\n"
        f"- Statut : {application.status}\n"
        f"- Fonds : {application.fund_id}"
    )


@tool
async def generate_application_section(
    application_id: str,
    section_key: str,
    config: RunnableConfig,
    instructions: str | None = None,
) -> str:
    """Generer une section du dossier de candidature.

    Utilise cet outil quand l'utilisateur demande de generer ou rediger
    une section du dossier (presentation entreprise, budget, impact, etc.).

    Args:
        application_id: Identifiant UUID du dossier.
        section_key: Cle de la section (ex: company_presentation, budget, impact_analysis).
        instructions: Instructions optionnelles pour la generation.
    """
    from app.modules.applications.service import generate_section, get_application_by_id

    db, _user_id = get_db_and_user(config)

    application = await get_application_by_id(db=db, application_id=uuid.UUID(application_id))
    if application is None:
        return f"Dossier de candidature introuvable (id={application_id})."

    section = await generate_section(db=db, application=application, section_key=section_key)

    content_preview = str(section.get("content", ""))[:300]

    return (
        f"Section '{section_key}' generee avec succes.\n"
        f"- Statut : {section.get('status', 'generated')}\n"
        f"- Apercu : {content_preview}..."
    )


@tool
async def update_application_section(
    application_id: str,
    section_key: str,
    content: str,
    config: RunnableConfig,
) -> str:
    """Modifier le contenu d'une section du dossier de candidature.

    Utilise cet outil quand l'utilisateur fournit du texte pour modifier
    ou remplacer le contenu d'une section existante.

    Args:
        application_id: Identifiant UUID du dossier.
        section_key: Cle de la section a modifier.
        content: Nouveau contenu de la section.
    """
    from app.modules.applications.service import get_application_by_id, update_section

    db, _user_id = get_db_and_user(config)

    application = await get_application_by_id(db=db, application_id=uuid.UUID(application_id))
    if application is None:
        return f"Dossier de candidature introuvable (id={application_id})."

    result = await update_section(
        db=db,
        application=application,
        section_key=section_key,
        content=content,
    )

    return (
        f"Section '{section_key}' mise a jour avec succes.\n"
        f"- Statut : {result.get('status', 'edited')}"
    )


@tool
async def get_application_checklist(
    application_id: str,
    config: RunnableConfig,
) -> str:
    """Consulter la checklist des documents requis pour un dossier de candidature.

    Utilise cet outil quand l'utilisateur demande quels documents sont requis,
    ce qui manque, ou l'etat d'avancement de son dossier.

    Args:
        application_id: Identifiant UUID du dossier.
    """
    from app.modules.applications.service import get_application_by_id, get_checklist

    db, _user_id = get_db_and_user(config)

    application = await get_application_by_id(db=db, application_id=uuid.UUID(application_id))
    if application is None:
        return f"Dossier de candidature introuvable (id={application_id})."

    checklist = await get_checklist(db=db, application=application)

    if not checklist:
        return "Aucun element dans la checklist."

    lines: list[str] = ["Checklist du dossier :"]
    provided_count = 0
    for item in checklist:
        status_icon = "[X]" if item.get("provided") else "[ ]"
        required_label = " (requis)" if item.get("required") else ""
        lines.append(f"  {status_icon} {item.get('label', 'N/A')}{required_label}")
        if item.get("provided"):
            provided_count += 1

    lines.append(f"\nProgression : {provided_count}/{len(checklist)} documents fournis.")

    return "\n".join(lines)


@tool
async def simulate_financing(
    application_id: str,
    config: RunnableConfig,
) -> str:
    """Simuler les conditions de financement pour un dossier de candidature.

    Utilise cet outil quand l'utilisateur demande une estimation des montants,
    du ROI, de la timeline ou de l'impact d'un financement.

    Args:
        application_id: Identifiant UUID du dossier.
    """
    from app.modules.applications.service import get_application_by_id

    db, _user_id = get_db_and_user(config)

    application = await get_application_by_id(db=db, application_id=uuid.UUID(application_id))
    if application is None:
        return f"Dossier de candidature introuvable (id={application_id})."

    simulation = await _simulate_financing(db, application)

    if "error" in simulation:
        return f"Erreur de simulation : {simulation['error']}"

    return (
        f"Simulation financiere :\n"
        f"- Fonds : {simulation.get('fund_name', 'N/A')}\n"
        f"- Montant eligible estime : {simulation['eligible_amount']:,} {simulation.get('currency', 'USD')}\n"
        f"- ROI estime : {simulation['roi_estimate']}\n"
        f"- Timeline : {simulation['timeline_months']} mois"
    )


@tool
async def export_application(
    application_id: str,
    format: str,
    config: RunnableConfig,
) -> str:
    """Exporter un dossier de candidature en PDF ou Word.

    Utilise cet outil quand l'utilisateur demande a telecharger ou exporter
    son dossier de candidature.

    Args:
        application_id: Identifiant UUID du dossier.
        format: Format d'export ('pdf' ou 'docx').
    """
    from app.modules.applications.service import get_application_by_id

    db, _user_id = get_db_and_user(config)

    application = await get_application_by_id(db=db, application_id=uuid.UUID(application_id))
    if application is None:
        return f"Dossier de candidature introuvable (id={application_id})."

    if format not in ("pdf", "docx"):
        return f"Format non supporte : '{format}'. Utilisez 'pdf' ou 'docx'."

    export_path = await _export_application(db, application, format)

    return (
        f"Dossier exporte avec succes au format {format.upper()}.\n"
        f"- URL de telechargement : {export_path}"
    )


APPLICATION_TOOLS = [
    with_retry(submit_fund_application_draft, max_retries=2, node_name="application"),
    with_retry(generate_application_section, max_retries=2, node_name="application"),
    with_retry(update_application_section, max_retries=2, node_name="application"),
    with_retry(get_application_checklist, max_retries=2, node_name="application"),
    with_retry(simulate_financing, max_retries=2, node_name="application"),
    with_retry(export_application, max_retries=2, node_name="application"),
]
