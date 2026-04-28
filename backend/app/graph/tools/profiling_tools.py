"""Tools LangChain pour le noeud de profilage entreprise.

Deux tools exposés au LLM :
- update_company_profile : mise à jour partielle du profil
- get_company_profile : consultation du profil et complétion
"""

import json
import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry
from app.modules.company.schemas import CompanyProfileUpdate
from app.modules.company.service import FIELD_LABELS, compute_completion
from app.services.profile_extraction import extract_profile_from_text

logger = logging.getLogger(__name__)

# V8-AXE1 : seuil de declenchement du fallback regex deterministe.
# >= 2 args null/whitespace indique un echec d'extraction massif (BUG-V7-001 /
# BUG-V7.1-001), pas une omission intentionnelle d'un seul champ par le LLM.
_REGEX_FALLBACK_NULL_THRESHOLD = 2

# Champs eligibles au merge regex (strictement alignes sur les cles renvoyees
# par extract_profile_from_text). `city` n'est volontairement PAS dans le
# fallback : extract_profile_from_text ne le couvre pas (trop de faux positifs
# avec un dict statique), donc l'inclure introduisait un biais de seuil
# (review V8-AXE1 MOYEN-2).
_REGEX_FALLBACK_FIELDS = frozenset(
    {"company_name", "sector", "employee_count", "country"}
)


def _is_effectively_null(value: object) -> bool:
    """True si la valeur LLM est None ou une chaine vide/whitespace.

    Le contrôle existant (BUG-V6-011) considere "" et "   " comme equivalents
    a None. Pour le seuil de fallback, ces valeurs doivent etre comptees comme
    nulles afin de ne pas masquer un echec d'extraction massif (review V8-AXE1
    MOYEN-1 : LLM passant 5 chaines vides equivaut a 5 nulls).
    """
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


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

    EXTRACTION OBLIGATOIRE — Quand l'utilisateur mentionne plusieurs informations
    dans un seul message, tu DOIS extraire TOUS les champs reconnaissables en
    UN SEUL appel à cet outil. Ne jamais appeler avec des arguments null si
    l'information est présente dans le message.

    EXEMPLES :

    1. User : "AgriVert Sarl, Agriculture, 15 employés, Sénégal"
       → update_company_profile(company_name="AgriVert Sarl", sector="agriculture",
                                employee_count=15, country="Sénégal")

    2. User : "Mon entreprise EcoSolaire dans le solaire à Abidjan, 30 personnes"
       → update_company_profile(company_name="EcoSolaire", sector="energie",
                                employee_count=30, city="Abidjan",
                                country="Côte d'Ivoire")

    3. User : "Je suis Mariam de TextileVert, secteur textile, 8 employés à Bamako"
       → update_company_profile(company_name="TextileVert", sector="textile",
                                employee_count=8, city="Bamako", country="Mali")
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

    # V8-AXE1 : fallback regex deterministe quand le LLM extrait mal les
    # champs structures depuis le langage naturel (BUG-V7-001 / BUG-V7.1-001).
    # Active si >= 2 des 5 champs cibles sont None ET que le dernier message
    # utilisateur est disponible dans le RunnableConfig. Le LLM gagne toujours
    # sur le regex (les valeurs LLM non-null ne sont jamais ecrasees).
    null_target_count = sum(
        1 for f in _REGEX_FALLBACK_FIELDS if _is_effectively_null(local_vars.get(f))
    )
    if null_target_count >= _REGEX_FALLBACK_NULL_THRESHOLD:
        configurable = (config or {}).get("configurable", {}) if config else {}
        last_user_message = configurable.get("last_user_message") or ""
        if isinstance(last_user_message, str) and last_user_message.strip():
            regex_extracted = extract_profile_from_text(last_user_message)
            filled_by_regex: list[str] = []
            for field_name, regex_value in regex_extracted.items():
                # LLM > regex : ne combler QUE si la valeur LLM est null/vide.
                if _is_effectively_null(local_vars.get(field_name)):
                    local_vars[field_name] = regex_value
                    filled_by_regex.append(field_name)
            if filled_by_regex:
                # Tronquer user_id pour ne pas exposer l'UUID complet en logs
                # (review V8-AXE1 ÉLEVÉ-3 : PII RGPD).
                user_id_log = str(user_id)[:8]
                logger.info(
                    "regex_fallback_triggered tool=update_company_profile "
                    "user_id=%s null_field_count=%d regex_filled_fields=%s",
                    user_id_log,
                    null_target_count,
                    filled_by_regex,
                    extra={
                        "metric": "regex_fallback_triggered",
                        "tool_name": "update_company_profile",
                        "user_id": user_id_log,
                        "null_field_count": null_target_count,
                        "regex_filled_fields": filled_by_regex,
                    },
                )

    for field_name, value in local_vars.items():
        if value is not None:
            raw_updates[field_name] = value

    if not raw_updates:
        return "Aucun champ fourni pour la mise à jour."

    # CONTROLE RUNTIME : rejeter les payloads compose's exclusivement de
    # chaines vides ou whitespace-only (BUG-V6-011 : LLM appelle le tool
    # avec des champs "  " ou "" sans valeur reelle).
    cleaned: dict = {}
    for field_name, value in raw_updates.items():
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            cleaned[field_name] = stripped
        else:
            cleaned[field_name] = value
    if not cleaned:
        return (
            "ERREUR : aucun champ utile fourni (valeurs vides ou espaces). "
            "Verifie l'extraction depuis la conversation avant de rappeler "
            "update_company_profile."
        )
    raw_updates = cleaned

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
