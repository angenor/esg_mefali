"""Tools LangChain pour le noeud de profilage entreprise.

Deux tools exposés au LLM :
- update_company_profile : mise à jour partielle du profil
- get_company_profile : consultation du profil et complétion
"""

import json

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry
from app.modules.company.schemas import CompanyProfileUpdate
from app.modules.company.service import FIELD_LABELS, compute_completion


@tool
async def update_company_profile(
    config: RunnableConfig,
    company_name: str | None = None,
    sector: str | None = None,
    sub_sector: str | None = None,
    employee_count: int | None = None,
    annual_revenue_xof: int | None = None,
    city: str | None = None,
    country: str | None = None,
    year_founded: int | None = None,
    has_waste_management: bool | None = None,
    has_energy_policy: bool | None = None,
    has_gender_policy: bool | None = None,
    has_training_program: bool | None = None,
    has_financial_transparency: bool | None = None,
    governance_structure: str | None = None,
    environmental_practices: str | None = None,
    social_practices: str | None = None,
) -> str:
    """Mettre à jour le profil de l'entreprise avec les informations fournies.

    Utilise cet outil quand l'utilisateur partage des informations sur son entreprise :
    nom, secteur, nombre d'employés, chiffre d'affaires, localisation,
    ou des pratiques ESG (gestion déchets, politique énergétique, genre, etc.).
    Seuls les champs fournis seront mis à jour, les autres restent inchangés.
    """
    from app.modules.company import service as company_service

    db, user_id = get_db_and_user(config)

    # Construire le dictionnaire des champs fournis (non-None)
    raw_updates: dict = {}
    local_vars = {
        "company_name": company_name,
        "sector": sector,
        "sub_sector": sub_sector,
        "employee_count": employee_count,
        "annual_revenue_xof": annual_revenue_xof,
        "city": city,
        "country": country,
        "year_founded": year_founded,
        "has_waste_management": has_waste_management,
        "has_energy_policy": has_energy_policy,
        "has_gender_policy": has_gender_policy,
        "has_training_program": has_training_program,
        "has_financial_transparency": has_financial_transparency,
        "governance_structure": governance_structure,
        "environmental_practices": environmental_practices,
        "social_practices": social_practices,
    }
    for field_name, value in local_vars.items():
        if value is not None:
            raw_updates[field_name] = value

    if not raw_updates:
        return "Aucun champ fourni pour la mise à jour."

    updates = CompanyProfileUpdate(**raw_updates)
    profile = await company_service.get_or_create_profile(db, user_id)
    updated_profile, changed_fields, skipped_fields = await company_service.update_profile(
        db, profile, updates, source="llm",
    )

    if not changed_fields and not skipped_fields:
        return "Aucun changement détecté (les valeurs sont identiques)."

    # Calculer la complétion après mise à jour
    completion = compute_completion(updated_profile)

    # Metadonnees structurees pour les evenements SSE
    # profile_update / profile_completion (existants) + profile_skipped (story 9.5)
    sse_metadata = json.dumps({
        "__sse_profile__": True,
        "changed_fields": changed_fields,
        "skipped_fields": skipped_fields,
        "completion": {
            "identity_completion": completion.identity_completion,
            "esg_completion": completion.esg_completion,
            "overall_completion": completion.overall_completion,
        },
    })

    # Ligne de completion commune aux deux branches.
    completion_line = (
        f"Complétion : identité {completion.identity_completion}% | "
        f"ESG {completion.esg_completion}% | "
        f"global {completion.overall_completion}%"
    )

    # Cas 1 : aucun changement mais des skips → message honnête, pas de
    # « succès » trompeur (review 9.5 P3).
    if not changed_fields and skipped_fields:
        skip_labels = ", ".join(sf["label"] for sf in skipped_fields)
        return (
            f"J'ai bien noté votre demande, mais ces champs sont protégés "
            f"par votre saisie manuelle antérieure : {skip_labels}. "
            f"Aucun champ n'a été modifié.\n\n"
            f"{completion_line}\n\n"
            f"<!--SSE:{sse_metadata}-->"
        )

    # Cas 2 : au moins un changement (éventuellement accompagné de skips).
    field_lines = [
        f"- {cf['label']} : {cf['value']}"
        for cf in changed_fields
    ]
    fields_text = "\n".join(field_lines)

    skip_note = ""
    if skipped_fields:
        skip_labels = ", ".join(sf["label"] for sf in skipped_fields)
        skip_note = (
            f"\n\nNote : les champs suivants n'ont pas été modifiés car "
            f"l'utilisateur les a déjà édités manuellement : {skip_labels}."
        )

    return (
        f"Profil mis à jour avec succès :\n{fields_text}\n\n"
        f"{completion_line}"
        f"{skip_note}\n\n"
        f"<!--SSE:{sse_metadata}-->"
    )


@tool
async def get_company_profile(config: RunnableConfig) -> str:
    """Consulter le profil actuel de l'entreprise et son niveau de complétion.

    Utilise cet outil quand l'utilisateur demande à voir son profil,
    veut savoir quelles informations manquent, ou demande son pourcentage
    de complétion. Ne nécessite aucun paramètre.
    """
    from app.modules.company import service as company_service

    db, user_id = get_db_and_user(config)

    profile = await company_service.get_profile(db, user_id)

    if profile is None:
        return (
            "Aucun profil entreprise trouvé. "
            "Partagez des informations sur votre entreprise pour commencer "
            "(nom, secteur, localisation, nombre d'employés, etc.)."
        )

    completion = compute_completion(profile)

    # Construire le résumé des champs remplis
    filled_lines: list[str] = []
    all_filled = completion.identity_fields.filled + completion.esg_fields.filled
    for field_name in all_filled:
        value = getattr(profile, field_name, None)
        if value is not None:
            display_value = value.value if hasattr(value, "value") else value
            label = FIELD_LABELS.get(field_name, field_name)
            filled_lines.append(f"- {label} : {display_value}")

    filled_text = "\n".join(filled_lines) if filled_lines else "Aucun champ rempli."

    # Construire la liste des champs manquants
    all_missing = completion.identity_fields.missing + completion.esg_fields.missing
    missing_labels = [
        FIELD_LABELS.get(f, f) for f in all_missing
    ]
    missing_text = ", ".join(missing_labels) if missing_labels else "Aucun"

    return (
        f"Profil entreprise :\n{filled_text}\n\n"
        f"Complétion : identité {completion.identity_completion}% | "
        f"ESG {completion.esg_completion}% | "
        f"global {completion.overall_completion}%\n\n"
        f"Champs manquants : {missing_text}"
    )


PROFILING_TOOLS = [
    with_retry(update_company_profile, max_retries=2, node_name="profiling"),
    with_retry(get_company_profile, max_retries=2, node_name="profiling"),
]
