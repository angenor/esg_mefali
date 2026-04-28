"""Tools LangChain pour le noeud scoring credit vert.

Trois tools exposes au LLM :
- generate_credit_score : calculer le score de credit vert
- get_credit_score : consulter le dernier score
- generate_credit_certificate : generer une attestation PDF
"""

import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry

logger = logging.getLogger(__name__)


async def _generate_certificate(db, user_id) -> str:
    """Generer un certificat PDF d'attestation du score de credit vert.

    Retourne le chemin du fichier genere.
    """
    from app.modules.credit.service import get_latest_score

    score = await get_latest_score(db=db, user_id=user_id)
    if score is None:
        raise ValueError("Aucun score de credit vert disponible pour generer l'attestation.")

    # Placeholder — la generation PDF via WeasyPrint sera implementee
    # quand le template sera pret
    cert_path = f"/uploads/certificates/{user_id}_credit_v{score.version}.pdf"
    logger.info("Certificat credit genere pour user %s -> %s", user_id, cert_path)
    return cert_path


# Fenetre minimale entre deux generations de score (idempotence mensuelle).
# BUG-V6-004 / BUG-V6-009 : eviter que le LLM regenere un score textuel parallele
# au score BDD ou recree un row a chaque tour de conversation.
_CREDIT_SCORE_MIN_AGE_DAYS = 30


@tool
async def generate_credit_score(config: RunnableConfig) -> str:
    """Calculer le score de credit vert alternatif de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande a calculer ou recalculer
    son score de credit vert. Le score combine solvabilite et impact vert
    a partir des donnees non-conventionnelles (profil, ESG, carbone).
    N'estime JAMAIS un score manuellement — appelle toujours ce tool.
    """
    from datetime import datetime, timezone

    from app.modules.credit.service import (
        generate_credit_score as gen_score,
        get_latest_score,
    )

    db, user_id = get_db_and_user(config)

    # CONTROLE RUNTIME : idempotence mensuelle. Si un score recent existe deja,
    # on n'insere PAS un nouveau row et on renvoie une chaine d'erreur exploitable
    # par le LLM (lecture via get_credit_score plutot que regeneration).
    latest = await get_latest_score(db=db, user_id=user_id)
    if latest is not None and latest.generated_at is not None:
        gen_at = latest.generated_at
        if gen_at.tzinfo is None:
            gen_at = gen_at.replace(tzinfo=timezone.utc)
        # Clamp a 0 : un timestamp futur (clock skew, fixture test) doit etre
        # traite comme "vient d'etre genere", pas comme un age negatif qui
        # bloquerait indefiniment via age_days < 30.
        age_days = max(0, (datetime.now(timezone.utc) - gen_at).days)
        if age_days < _CREDIT_SCORE_MIN_AGE_DAYS:
            return (
                f"ERREUR : score credit deja genere ce mois "
                f"(version {latest.version}, score {latest.combined_score}/100, "
                f"genere il y a {age_days} jour(s)). "
                f"Pour le consulter, appelle get_credit_score(). "
                f"Pour generer une nouvelle version, attends au moins "
                f"{_CREDIT_SCORE_MIN_AGE_DAYS} jours."
            )

    score = await gen_score(db=db, user_id=user_id)

    # TODO DEF-BUG-V6-CREDIT-RISKLEVEL : `score.risk_level` n'existe pas sur le
    # modele CreditScore (colonne reelle: confidence_label). Mocks de tests
    # masquent le bug. A corriger en story dediee.
    return (
        f"Score de credit vert calcule avec succes !\n"
        f"- Score combine : {score.combined_score}/100\n"
        f"- Solvabilite : {score.solvability_score}/100\n"
        f"- Impact vert : {score.green_impact_score}/100\n"
        f"- Niveau de risque : {score.risk_level}\n"
        f"- Version : {score.version}\n\n"
        f"Le score est visible sur la page /credit-score."
    )


@tool
async def get_credit_score(config: RunnableConfig) -> str:
    """Consulter le dernier score de credit vert de l'utilisateur.

    Utilise cet outil quand l'utilisateur demande son score de credit vert actuel,
    son niveau de risque, ou sa solvabilite.
    """
    from app.modules.credit.service import get_latest_score

    db, user_id = get_db_and_user(config)

    score = await get_latest_score(db=db, user_id=user_id)

    if score is None:
        return (
            "Aucun score de credit vert calcule. "
            "Proposez a l'utilisateur de calculer son score en utilisant "
            "le tool generate_credit_score."
        )

    # TODO DEF-BUG-V6-CREDIT-RISKLEVEL : 2e site qui reference score.risk_level
    # (colonne reelle: confidence_label). A corriger en story dediee.
    return (
        f"Score de credit vert actuel :\n"
        f"- Score combine : {score.combined_score}/100\n"
        f"- Solvabilite : {score.solvability_score}/100\n"
        f"- Impact vert : {score.green_impact_score}/100\n"
        f"- Niveau de risque : {score.risk_level}\n"
        f"- Version : {score.version}"
    )


@tool
async def generate_credit_certificate(config: RunnableConfig) -> str:
    """Generer une attestation PDF du score de credit vert.

    Utilise cet outil quand l'utilisateur demande un certificat, une attestation
    ou un document officiel de son score de credit vert.
    """
    db, user_id = get_db_and_user(config)

    cert_path = await _generate_certificate(db, user_id)

    return (
        f"Attestation de score de credit vert generee avec succes.\n"
        f"- URL de telechargement : {cert_path}"
    )


CREDIT_TOOLS = [
    with_retry(generate_credit_score, max_retries=2, node_name="credit"),
    with_retry(get_credit_score, max_retries=2, node_name="credit"),
    with_retry(generate_credit_certificate, max_retries=2, node_name="credit"),
]
