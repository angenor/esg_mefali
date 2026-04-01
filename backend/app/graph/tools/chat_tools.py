"""Tools LangChain pour le noeud chat (lecture seule).

Quatre tools de consultation pour que le LLM reponde
avec des donnees temps reel depuis la base de donnees.
"""

import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user

logger = logging.getLogger(__name__)


@tool
async def get_user_dashboard_summary(config: RunnableConfig) -> str:
    """Obtenir le resume du tableau de bord de l'utilisateur.

    Utilise cet outil quand l'utilisateur pose des questions generales sur
    ses resultats, sa progression, ou demande un resume de sa situation.
    Retourne les scores ESG, carbone, credit et financements.
    """
    from app.modules.dashboard.service import get_dashboard_summary

    try:
        db, user_id = get_db_and_user(config)

        summary = await get_dashboard_summary(db=db, user_id=user_id)

        parts: list[str] = ["Tableau de bord de l'utilisateur :"]

        # ESG
        esg = summary.get("esg")
        if esg:
            parts.append(
                f"- ESG : score global {esg.get('overall_score', 'N/A')}/100 "
                f"(E: {esg.get('environment_score', 'N/A')}, "
                f"S: {esg.get('social_score', 'N/A')}, "
                f"G: {esg.get('governance_score', 'N/A')})"
            )
        else:
            parts.append("- ESG : aucune evaluation realisee")

        # Carbone
        carbon = summary.get("carbon")
        if carbon:
            parts.append(
                f"- Carbone : {carbon.get('total_emissions_tco2e', 'N/A')} tCO2e "
                f"(annee {carbon.get('year', 'N/A')})"
            )
        else:
            parts.append("- Carbone : aucun bilan realise")

        # Credit
        credit = summary.get("credit")
        if credit:
            parts.append(
                f"- Credit vert : score {credit.get('combined_score', 'N/A')}/100 "
                f"(risque : {credit.get('risk_level', 'N/A')})"
            )
        else:
            parts.append("- Credit vert : aucun score calcule")

        # Financement
        financing = summary.get("financing", {})
        matched = financing.get("matched_funds", 0)
        interested = financing.get("interested_funds", 0)
        parts.append(f"- Financements : {matched} fonds matches, {interested} marques d'interet")

        return "\n".join(parts)

    except Exception as e:
        logger.exception("Erreur lors de la recuperation du tableau de bord")
        return f"Erreur lors de la recuperation du tableau de bord : {e}"


@tool
async def get_company_profile_chat(config: RunnableConfig) -> str:
    """Consulter le profil de l'entreprise de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande des informations sur
    son profil entreprise, ses donnees, ou veut verifier ce qui est enregistre.
    """
    from app.modules.company.service import FIELD_LABELS, compute_completion, get_profile

    try:
        db, user_id = get_db_and_user(config)

        profile = await get_profile(db, user_id)

        if profile is None:
            return (
                "Aucun profil entreprise enregistre. "
                "L'utilisateur doit d'abord partager des informations sur son entreprise."
            )

        completion = compute_completion(profile)

        lines: list[str] = ["Profil entreprise :"]
        for field_name in (completion.identity_fields.filled + completion.esg_fields.filled):
            value = getattr(profile, field_name, None)
            if value is not None:
                display_value = value.value if hasattr(value, "value") else value
                label = FIELD_LABELS.get(field_name, field_name)
                lines.append(f"- {label} : {display_value}")

        lines.append(
            f"\nCompletion : identite {completion.identity_completion}% | "
            f"ESG {completion.esg_completion}% | "
            f"global {completion.overall_completion}%"
        )

        missing_labels = [
            FIELD_LABELS.get(f, f)
            for f in (completion.identity_fields.missing + completion.esg_fields.missing)
        ]
        if missing_labels:
            lines.append(f"Champs manquants : {', '.join(missing_labels)}")

        return "\n".join(lines)

    except Exception as e:
        logger.exception("Erreur lors de la consultation du profil")
        return f"Erreur lors de la consultation du profil : {e}"


@tool
async def get_esg_assessment_chat(
    config: RunnableConfig,
    assessment_id: str | None = None,
) -> str:
    """Consulter l'evaluation ESG la plus recente de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande son score ESG,
    ses resultats d'evaluation, ou veut connaitre sa performance ESG.

    Args:
        assessment_id: Identifiant UUID de l'evaluation (optionnel, prend la plus recente par defaut).
    """
    import uuid

    from app.modules.esg.service import get_assessment, get_resumable_assessment

    try:
        db, user_id = get_db_and_user(config)

        assessment = None
        if assessment_id:
            assessment = await get_assessment(db=db, assessment_id=uuid.UUID(assessment_id), user_id=user_id)
        else:
            assessment = await get_resumable_assessment(db=db, user_id=user_id)

        if assessment is None:
            return "Aucune evaluation ESG trouvee pour cet utilisateur."

        status = assessment.status.value if hasattr(assessment.status, "value") else assessment.status

        result = (
            f"Evaluation ESG :\n"
            f"- ID : {assessment.id}\n"
            f"- Statut : {status}\n"
            f"- Secteur : {assessment.sector}"
        )

        if status == "completed" and assessment.overall_score is not None:
            result += (
                f"\n- Score global : {assessment.overall_score}/100\n"
                f"- Environnement : {assessment.environment_score}/100\n"
                f"- Social : {assessment.social_score}/100\n"
                f"- Gouvernance : {assessment.governance_score}/100"
            )

        return result

    except Exception as e:
        logger.exception("Erreur lors de la consultation de l'evaluation ESG")
        return f"Erreur lors de la consultation de l'evaluation ESG : {e}"


@tool
async def get_carbon_summary_chat(
    config: RunnableConfig,
    assessment_id: str | None = None,
) -> str:
    """Consulter le bilan carbone le plus recent de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande son empreinte carbone,
    ses emissions, ou veut connaitre son bilan carbone.

    Args:
        assessment_id: Identifiant UUID du bilan (optionnel, prend le plus recent par defaut).
    """
    import uuid

    from app.modules.carbon.service import get_assessment, get_resumable_assessment

    try:
        db, user_id = get_db_and_user(config)

        assessment = None
        if assessment_id:
            assessment = await get_assessment(db, uuid.UUID(assessment_id), user_id)
        else:
            assessment = await get_resumable_assessment(db, user_id)

        if assessment is None:
            return "Aucun bilan carbone trouve pour cet utilisateur."

        status = assessment.status.value if hasattr(assessment.status, "value") else assessment.status
        total = assessment.total_emissions_tco2e or 0.0

        result = (
            f"Bilan carbone :\n"
            f"- ID : {assessment.id}\n"
            f"- Annee : {assessment.year}\n"
            f"- Statut : {status}\n"
            f"- Emissions totales : {total} tCO2e"
        )

        if assessment.sector:
            result += f"\n- Secteur : {assessment.sector}"

        return result

    except Exception as e:
        logger.exception("Erreur lors de la consultation du bilan carbone")
        return f"Erreur lors de la consultation du bilan carbone : {e}"


CHAT_TOOLS = [
    get_user_dashboard_summary,
    get_company_profile_chat,
    get_esg_assessment_chat,
    get_carbon_summary_chat,
]
