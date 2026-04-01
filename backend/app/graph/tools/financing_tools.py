"""Tools LangChain pour le noeud de financement vert.

Quatre tools exposes au LLM :
- search_compatible_funds : rechercher les fonds compatibles
- save_fund_interest : marquer un interet pour un fonds
- get_fund_details : consulter les details d'un fonds
- create_fund_application : creer une candidature
"""

import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user

logger = logging.getLogger(__name__)


@tool
async def search_compatible_funds(config: RunnableConfig) -> str:
    """Rechercher les fonds de financement compatibles avec le profil de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande quels financements sont
    disponibles, quels fonds correspondent a son profil, ou cherche des
    subventions ou credits verts. Collecte automatiquement le profil,
    le score ESG et le bilan carbone pour le matching.
    """
    from app.modules.company.service import get_profile
    from app.modules.financing.service import get_fund_matches

    try:
        db, user_id = get_db_and_user(config)

        # Recuperer le profil pour le matching
        profile = await get_profile(db, user_id)

        sector = None
        revenue = None
        country = None
        city = None
        if profile:
            sector = profile.sector
            if hasattr(sector, "value"):
                sector = sector.value
            revenue = profile.annual_revenue_xof
            country = profile.country
            city = profile.city

        matches = await get_fund_matches(
            db=db,
            user_id=user_id,
            company_sector=sector,
            company_revenue=revenue,
            company_country=country,
            company_city=city,
        )

        if not matches:
            return (
                "Aucun fonds compatible trouve. "
                "Completez votre profil entreprise et realisez une evaluation ESG "
                "pour ameliorer le matching."
            )

        lines: list[str] = [f"{len(matches)} fonds compatibles trouves :"]
        for m in matches[:5]:
            fund = m.fund
            fund_type = fund.fund_type.value if hasattr(fund.fund_type, "value") else fund.fund_type
            lines.append(
                f"- {fund.name} ({fund_type}) — "
                f"score compatibilite : {m.compatibility_score}% — "
                f"montant : {fund.min_amount:,}-{fund.max_amount:,}"
            )

        if len(matches) > 5:
            lines.append(f"  ... et {len(matches) - 5} autres fonds.")

        return "\n".join(lines)

    except Exception as e:
        logger.exception("Erreur lors de la recherche de fonds compatibles")
        return f"Erreur lors de la recherche de fonds : {e}"


@tool
async def save_fund_interest(fund_id: str, config: RunnableConfig) -> str:
    """Enregistrer l'interet de l'utilisateur pour un fonds specifique.

    Utilise cet outil quand l'utilisateur indique etre interesse par un fonds,
    souhaite en savoir plus, ou veut demarrer une candidature.

    Args:
        fund_id: Identifiant UUID du fonds.
    """
    from app.modules.financing.service import get_match_by_fund, update_match_status

    try:
        db, user_id = get_db_and_user(config)

        match = await get_match_by_fund(db=db, user_id=user_id, fund_id=uuid.UUID(fund_id))

        if match is None:
            return (
                f"Aucun matching trouve pour le fonds {fund_id}. "
                "Lancez d'abord une recherche de fonds compatibles."
            )

        from app.models.financing import MatchStatus
        updated = await update_match_status(db=db, match=match, new_status=MatchStatus.interested)

        fund_name = match.fund.name if match.fund else fund_id

        return (
            f"Interet enregistre pour le fonds '{fund_name}'.\n"
            f"Vous pouvez maintenant creer un dossier de candidature "
            f"ou consulter les details de ce fonds."
        )

    except Exception as e:
        logger.exception("Erreur lors de l'enregistrement de l'interet pour le fonds %s", fund_id)
        return f"Erreur lors de l'enregistrement de l'interet : {e}"


@tool
async def get_fund_details(fund_id: str, config: RunnableConfig) -> str:
    """Consulter les details complets d'un fonds de financement.

    Utilise cet outil quand l'utilisateur demande des informations detaillees
    sur un fonds specifique : criteres d'eligibilite, montants, secteurs cibles.

    Args:
        fund_id: Identifiant UUID du fonds.
    """
    from app.modules.financing.service import get_fund_by_id

    try:
        db, _user_id = get_db_and_user(config)

        fund = await get_fund_by_id(db=db, fund_id=uuid.UUID(fund_id))

        if fund is None:
            return f"Fonds introuvable (id={fund_id})."

        fund_type = fund.fund_type.value if hasattr(fund.fund_type, "value") else fund.fund_type
        sectors = ", ".join(fund.sectors) if fund.sectors else "Tous secteurs"
        countries = ", ".join(fund.eligible_countries) if fund.eligible_countries else "Tous pays"

        return (
            f"Details du fonds :\n"
            f"- Nom : {fund.name}\n"
            f"- Type : {fund_type}\n"
            f"- Description : {fund.description or 'N/A'}\n"
            f"- Montant : {fund.min_amount:,} - {fund.max_amount:,} {fund.currency}\n"
            f"- Secteurs : {sectors}\n"
            f"- Pays eligibles : {countries}\n"
            f"- Statut : {fund.status}"
        )

    except Exception as e:
        logger.exception("Erreur lors de la consultation du fonds %s", fund_id)
        return f"Erreur lors de la consultation du fonds : {e}"


@tool
async def create_fund_application(
    fund_id: str,
    config: RunnableConfig,
    intermediary_id: str | None = None,
) -> str:
    """Creer un dossier de candidature pour un fonds de financement.

    Utilise cet outil quand l'utilisateur souhaite demarrer une candidature
    ou postuler a un fonds. Cree le dossier en base avec le statut 'draft'.

    Args:
        fund_id: Identifiant UUID du fonds cible.
        intermediary_id: Identifiant UUID de l'intermediaire (optionnel).
    """
    from app.modules.applications.service import create_application

    try:
        db, user_id = get_db_and_user(config)

        interm_uuid = uuid.UUID(intermediary_id) if intermediary_id else None

        application = await create_application(
            db=db,
            user_id=user_id,
            fund_id=uuid.UUID(fund_id),
            intermediary_id=interm_uuid,
        )

        return (
            f"Dossier de candidature cree avec succes !\n"
            f"- ID : {application.id}\n"
            f"- Statut : {application.status}\n"
            f"Vous pouvez maintenant generer les sections du dossier."
        )

    except Exception as e:
        logger.exception("Erreur lors de la creation du dossier de candidature")
        return f"Erreur lors de la creation du dossier : {e}"


FINANCING_TOOLS = [
    search_compatible_funds,
    save_fund_interest,
    get_fund_details,
    create_fund_application,
]
