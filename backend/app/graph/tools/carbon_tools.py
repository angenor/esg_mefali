"""Tools LangChain pour le noeud de bilan carbone."""

import json
import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry

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
    from app.services.carbon_mapping import resolve_subcategory

    db, user_id = get_db_and_user(config)

    # Recuperer le bilan
    assessment = await get_assessment(db, uuid.UUID(assessment_id), user_id)
    if assessment is None:
        return json.dumps({
            "status": "error",
            "message": f"Bilan carbone introuvable (id={assessment_id}).",
        }, ensure_ascii=False)

    # Rechercher le facteur d'emission
    # Strategie en 3 paliers (V8-AXE4 — BUG-V7-005, BUG-V7.1-006, BUG-V7.1-007) :
    # 1) Chemin rapide : subcategory deja canonique et present dans EMISSION_FACTORS.
    # 2) Mapping deterministe FR→canonique via resolve_subcategory (sur subcategory
    #    brut, puis sur source_description si necessaire).
    # 3) Fallback historique : premier facteur de la categorie.
    factor_key = subcategory
    factor_info = None

    if factor_key and factor_key in EMISSION_FACTORS:
        factor_info = EMISSION_FACTORS[factor_key]
    else:
        for hint in (subcategory, source_description):
            resolved, _alternatives = resolve_subcategory(category, hint)
            if resolved and resolved in EMISSION_FACTORS:
                factor_key = resolved
                factor_info = EMISSION_FACTORS[resolved]
                logger.info(
                    "Carbon subcategory resolved via mapping: category=%s hint=%r → %s",
                    category, hint, resolved,
                )
                break

    if factor_info is None:
        # Fallback historique : premier facteur de la categorie.
        for key, info in EMISSION_FACTORS.items():
            if info.get("category") == category:
                factor_info = info
                factor_key = key
                logger.warning(
                    "Carbon subcategory unresolved, fallback to first match: "
                    "category=%s subcategory=%r source_description=%r → %s",
                    category, subcategory, source_description, key,
                )
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

    # CONTROLE RUNTIME : dedup (assessment_id, category, subcategory) avant INSERT.
    # Si une entree existe deja pour ce couple, on UPDATE au lieu de creer un doublon
    # (regression BUG-V6-002 : doublons transport / dechets quand le LLM ne respecte
    # pas la consigne "1 saisie par sous-categorie"). Last-write-wins.
    from sqlalchemy import select as _select

    from app.models.carbon import CarbonEmissionEntry as _Entry

    existing = (
        await db.execute(
            _select(_Entry).where(
                _Entry.assessment_id == assessment.id,
                _Entry.category == category,
                _Entry.subcategory == factor_key,
            )
        )
    ).scalar_one_or_none()

    deduped = False
    if existing is not None:
        existing.quantity = quantity
        existing.unit = unit
        existing.emission_factor = emission_factor
        existing.emissions_tco2e = emissions_tco2e
        existing.source_description = source_description
        await db.flush()
        from app.modules.carbon.service import _compute_total_emissions
        total = await _compute_total_emissions(db, assessment.id)
        assessment.total_emissions_tco2e = total
        deduped = True
    else:
        entry_data = {
            "category": category,
            "subcategory": factor_key,
            "quantity": quantity,
            "unit": unit,
            "emission_factor": emission_factor,
            "emissions_tco2e": emissions_tco2e,
            "source_description": source_description,
        }
        _, total, _ = await add_entries(
            db=db, assessment=assessment, entries_data=[entry_data],
        )

    base_msg = (
        f"Entree enregistree : {quantity} {unit} de {factor_info['label']}"
        f" = {emissions_tco2e} tCO2e. Total actuel : {total} tCO2e."
    )
    return json.dumps({
        "status": "success",
        "deduped": deduped,
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
            f"[DEDUP] Entree deja saisie pour cette categorie/sous-categorie. "
            f"Mise a jour appliquee. {base_msg}"
        ) if deduped else base_msg,
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

    # BUG-V7.1-013 : declencher l'attribution du badge first_carbon
    # (et eventuellement full_journey si toutes les conditions sont remplies).
    from app.modules.action_plan.badges import safe_check_and_award_badges
    await safe_check_and_award_badges(db, user_id)

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


CARBON_TOOLS = [
    with_retry(create_carbon_assessment, max_retries=2, node_name="carbon"),
    with_retry(save_emission_entry, max_retries=2, node_name="carbon"),
    with_retry(finalize_carbon_assessment, max_retries=2, node_name="carbon"),
    with_retry(get_carbon_summary, max_retries=2, node_name="carbon"),
]
