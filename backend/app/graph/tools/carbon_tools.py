"""Tools LangChain pour le noeud de bilan carbone."""

import json
import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user

logger = logging.getLogger(__name__)


@tool
async def create_carbon_assessment(year: int, config: RunnableConfig) -> str:
    """Creer un nouveau bilan carbone annuel pour l'utilisateur.

    Utilise le secteur du profil entreprise si disponible.
    Un seul bilan par annee est autorise.

    Args:
        year: Annee du bilan carbone (ex: 2025).
    """
    from app.modules.carbon.service import create_assessment
    from app.modules.company.service import get_profile

    try:
        db, user_id = get_db_and_user(config)
        configurable = (config or {}).get("configurable", {})
        conversation_id = configurable.get("conversation_id")

        # Recuperer le secteur depuis le profil entreprise
        sector = None
        try:
            profile = await get_profile(db, user_id)
            if profile and profile.sector:
                sector = profile.sector
                if hasattr(sector, "value"):
                    sector = sector.value
        except Exception:
            logger.debug("Impossible de recuperer le profil entreprise pour le secteur")

        conv_id = uuid.UUID(str(conversation_id)) if conversation_id else None
        assessment = await create_assessment(
            db=db,
            user_id=user_id,
            year=year,
            sector=sector,
            conversation_id=conv_id,
        )

        return json.dumps({
            "status": "success",
            "assessment_id": str(assessment.id),
            "year": assessment.year,
            "sector": assessment.sector or "non defini",
            "message": f"Bilan carbone {year} cree avec succes.",
        }, ensure_ascii=False)

    except ValueError as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
        }, ensure_ascii=False)
    except Exception as e:
        logger.exception("Erreur lors de la creation du bilan carbone")
        return json.dumps({
            "status": "error",
            "message": f"Erreur lors de la creation du bilan : {e}",
        }, ensure_ascii=False)


@tool
async def save_emission_entry(
    assessment_id: str,
    category: str,
    quantity: float,
    unit: str,
    source_description: str,
    subcategory: str | None = None,
    config: RunnableConfig = None,
) -> str:
    """Enregistrer une entree d'emission dans le bilan carbone.

    Cherche le facteur d'emission correspondant, calcule les tCO2e,
    et ajoute l'entree au bilan.

    Args:
        assessment_id: UUID du bilan carbone.
        category: Categorie d'emission (energy, transport, waste, industrial, agriculture).
        quantity: Quantite consommee (ex: 500 kWh, 200 litres).
        unit: Unite de la quantite (kWh, L, kg, etc.).
        source_description: Description de la source (ex: "Electricite bureau principal").
        subcategory: Sous-categorie / cle du facteur d'emission (ex: electricity_ci, diesel_generator).
    """
    from app.modules.carbon.emission_factors import EMISSION_FACTORS, compute_emissions_tco2e
    from app.modules.carbon.service import add_entries, get_assessment

    try:
        db, user_id = get_db_and_user(config)

        # Recuperer le bilan
        assessment = await get_assessment(db, uuid.UUID(assessment_id), user_id)
        if assessment is None:
            return json.dumps({
                "status": "error",
                "message": f"Bilan carbone introuvable (id={assessment_id}).",
            }, ensure_ascii=False)

        # Rechercher le facteur d'emission
        factor_key = subcategory
        if factor_key and factor_key in EMISSION_FACTORS:
            factor_info = EMISSION_FACTORS[factor_key]
        else:
            # Chercher par categorie : prendre le premier facteur correspondant
            factor_info = None
            for key, info in EMISSION_FACTORS.items():
                if info.get("category") == category:
                    factor_info = info
                    factor_key = key
                    break

            if factor_info is None:
                return json.dumps({
                    "status": "error",
                    "message": (
                        f"Aucun facteur d'emission trouve pour la categorie '{category}'"
                        f" et sous-categorie '{subcategory}'."
                    ),
                }, ensure_ascii=False)

        emission_factor = factor_info["factor"]
        emissions_tco2e = compute_emissions_tco2e(quantity, emission_factor)

        entry_data = {
            "category": category,
            "subcategory": factor_key,
            "quantity": quantity,
            "unit": unit,
            "emission_factor": emission_factor,
            "emissions_tco2e": emissions_tco2e,
            "source_description": source_description,
        }

        added_count, total, completed_cats = await add_entries(
            db=db,
            assessment=assessment,
            entries_data=[entry_data],
        )

        return json.dumps({
            "status": "success",
            "entry": {
                "category": category,
                "subcategory": factor_key,
                "quantity": quantity,
                "unit": unit,
                "emission_factor_kgco2e": emission_factor,
                "emissions_tco2e": emissions_tco2e,
                "source_description": source_description,
            },
            "total_emissions_tco2e": total,
            "message": (
                f"Entree enregistree : {quantity} {unit} de {factor_info['label']}"
                f" = {emissions_tco2e} tCO2e. Total actuel : {total} tCO2e."
            ),
        }, ensure_ascii=False)

    except Exception as e:
        logger.exception("Erreur lors de l'enregistrement de l'entree d'emission")
        return json.dumps({
            "status": "error",
            "message": f"Erreur lors de l'enregistrement : {e}",
        }, ensure_ascii=False)


@tool
async def finalize_carbon_assessment(
    assessment_id: str,
    config: RunnableConfig,
) -> str:
    """Finaliser un bilan carbone et calculer le total des emissions.

    IMPORTANT : N'appelle ce tool que si l'utilisateur a explicitement confirme
    vouloir finaliser. Demande d'abord confirmation.

    Args:
        assessment_id: UUID du bilan carbone a finaliser.
    """
    from app.modules.carbon.service import complete_assessment, get_assessment

    try:
        db, user_id = get_db_and_user(config)

        assessment = await get_assessment(db, uuid.UUID(assessment_id), user_id)
        if assessment is None:
            return json.dumps({
                "status": "error",
                "message": f"Bilan carbone introuvable (id={assessment_id}).",
            }, ensure_ascii=False)

        if assessment.status.value == "completed":
            return json.dumps({
                "status": "error",
                "message": "Ce bilan est deja finalise.",
            }, ensure_ascii=False)

        completed = await complete_assessment(db=db, assessment=assessment)

        return json.dumps({
            "status": "success",
            "assessment_id": str(completed.id),
            "total_emissions_tco2e": completed.total_emissions_tco2e or 0.0,
            "year": completed.year,
            "message": (
                f"Bilan carbone {completed.year} finalise. "
                f"Total : {completed.total_emissions_tco2e or 0.0} tCO2e."
            ),
        }, ensure_ascii=False)

    except Exception as e:
        logger.exception("Erreur lors de la finalisation du bilan carbone")
        return json.dumps({
            "status": "error",
            "message": f"Erreur lors de la finalisation : {e}",
        }, ensure_ascii=False)


@tool
async def get_carbon_summary(
    assessment_id: str | None = None,
    config: RunnableConfig = None,
) -> str:
    """Obtenir le resume complet d'un bilan carbone (emissions, repartition, equivalences, benchmark).

    Si aucun assessment_id n'est fourni, cherche le bilan en cours de l'utilisateur.

    Args:
        assessment_id: UUID du bilan carbone (optionnel).
    """
    from app.modules.carbon.service import (
        get_assessment,
        get_assessment_summary,
        get_latest_assessment,
        get_resumable_assessment,
    )

    try:
        db, user_id = get_db_and_user(config)

        assessment = None
        if assessment_id:
            assessment = await get_assessment(db, uuid.UUID(assessment_id), user_id)
        else:
            # Priorite au bilan in_progress (reprise de questionnaire).
            # Fallback sur le dernier bilan quel que soit son statut pour
            # permettre la consultation d'un bilan completed.
            assessment = await get_resumable_assessment(db, user_id)
            if assessment is None:
                assessment = await get_latest_assessment(db, user_id)

        if assessment is None:
            return json.dumps({
                "status": "error",
                "message": "Aucun bilan carbone trouve.",
            }, ensure_ascii=False)

        summary = await get_assessment_summary(db=db, assessment=assessment)

        return json.dumps({
            "status": "success",
            "summary": summary,
        }, ensure_ascii=False)

    except Exception as e:
        logger.exception("Erreur lors de la recuperation du resume carbone")
        return json.dumps({
            "status": "error",
            "message": f"Erreur lors de la recuperation du resume : {e}",
        }, ensure_ascii=False)


CARBON_TOOLS = [
    create_carbon_assessment,
    save_emission_entry,
    finalize_carbon_assessment,
    get_carbon_summary,
]
