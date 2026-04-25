"""Tools LangChain pour le noeud d'evaluation ESG."""

import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry
from app.modules.esg.criteria import CRITERIA_BY_CODE, PILLAR_CRITERIA, PILLAR_LABELS

# Codes attendus par lettre de pilier (E1-E10, S1-S10, G1-G10).
_PILLAR_LETTER_TO_KEY = {"E": "environment", "S": "social", "G": "governance"}
_EXPECTED_CODES_BY_LETTER: dict[str, frozenset[str]] = {
    letter: frozenset(c.code for c in PILLAR_CRITERIA[key])
    for letter, key in _PILLAR_LETTER_TO_KEY.items()
}


def _normalize_code(raw: object) -> str:
    """Normaliser un code critere : trim + upper. Tolerant aux non-string."""
    if not isinstance(raw, str):
        return str(raw)
    return raw.strip().upper()


def _validate_pillar_completeness(
    request_codes: list[str],
    already_evaluated: list[str],
) -> str | None:
    """Valider que chaque pilier touche par la requete est complet via l'union.

    Retourne None si valide, sinon une chaine d'erreur explicite a renvoyer au LLM.
    Effets de bord : aucun. Idempotent.
    Tolere une variation casse/whitespace dans les codes ('e1' -> 'E1').
    """
    # 1. Normaliser et detecter les codes inconnus avant tout regroupement.
    normalized = [_normalize_code(c) for c in request_codes]
    invalid = sorted({code for code in normalized if code not in CRITERIA_BY_CODE})
    if invalid:
        return (
            f"ERREUR : codes invalides : {', '.join(invalid)}. "
            f"Les codes valides sont E1-E10, S1-S10, G1-G10. "
            f"Corrige les codes et rappelle batch_save_esg_criteria."
        )

    # 2. Identifier les piliers touches par la requete (par lettre prefixee).
    request_dedup = set(normalized)
    touched_letters = {code[0] for code in request_dedup}
    persisted = {_normalize_code(c) for c in already_evaluated}

    # 3. Pour chaque pilier touche, verifier la completude via l'union.
    errors: list[str] = []
    for letter in sorted(touched_letters):
        expected = _EXPECTED_CODES_BY_LETTER[letter]
        request_for_pillar = {c for c in request_dedup if c.startswith(letter)}
        persisted_for_pillar = {c for c in persisted if c.startswith(letter)}
        union_for_pillar = request_for_pillar | persisted_for_pillar
        missing = expected - union_for_pillar
        if missing:
            pillar_label = PILLAR_LABELS[_PILLAR_LETTER_TO_KEY[letter]]
            count = 10 - len(missing)
            errors.append(
                f"ERREUR : pilier {letter} ({pillar_label}) incomplet ({count}/10). "
                f"Codes manquants : {', '.join(sorted(missing))}. "
                f"Tu DOIS evaluer les 10 criteres {letter}1-{letter}10 avant de passer "
                f"au pilier suivant. Pose des questions complementaires couvrant ces "
                f"criteres puis rappelle batch_save_esg_criteria avec les criteres "
                f"manquants (les deja sauves sont conserves)."
            )

    if errors:
        return "\n\n".join(errors)
    return None


@tool
async def create_esg_assessment(config: RunnableConfig) -> str:
    """Creer une nouvelle evaluation ESG pour l'utilisateur.

    Utilise le secteur du profil utilisateur (ou 'services' par defaut).
    Retourne l'identifiant de l'evaluation creee.
    """
    from app.modules.esg.service import create_assessment

    db, user_id = get_db_and_user(config)
    configurable = (config or {}).get("configurable", {})
    conversation_id = configurable.get("conversation_id")

    # Recuperer le secteur depuis le profil utilisateur si disponible
    sector = "services"
    if configurable.get("user_profile"):
        sector = configurable["user_profile"].get("sector", "services")

    assessment = await create_assessment(
        db=db,
        user_id=user_id,
        sector=sector,
        conversation_id=uuid.UUID(str(conversation_id)) if conversation_id else None,
    )

    return (
        f"Evaluation ESG creee avec succes.\n"
        f"- ID : {assessment.id}\n"
        f"- Secteur : {assessment.sector}\n"
        f"- Statut : {assessment.status.value}"
    )


@tool
async def save_esg_criterion_score(
    assessment_id: str,
    criterion_code: str,
    score: int,
    justification: str,
    config: RunnableConfig,
) -> str:
    """Sauvegarder le score d'un critere ESG dans l'evaluation en cours.

    Args:
        assessment_id: Identifiant UUID de l'evaluation ESG.
        criterion_code: Code du critere (ex: E1, S3, G7).
        score: Note de 0 a 10.
        justification: Justification de la note attribuee.
    """
    from app.modules.esg.service import (
        compute_overall_score,
        compute_progress_percent,
        get_assessment,
        update_assessment,
    )

    db, user_id = get_db_and_user(config)

    assessment = await get_assessment(
        db=db,
        assessment_id=uuid.UUID(assessment_id),
        user_id=user_id,
    )
    if assessment is None:
        return f"Erreur : evaluation ESG {assessment_id} introuvable."

    # Mettre a jour les scores des criteres (copie immutable)
    criteria_scores = dict((assessment.assessment_data or {}).get("criteria_scores", {}))
    criteria_scores[criterion_code] = {
        "score": score,
        "justification": justification,
    }

    # Mettre a jour la liste des criteres evalues (copie immutable)
    evaluated_criteria = list(assessment.evaluated_criteria or [])
    if criterion_code not in evaluated_criteria:
        evaluated_criteria.append(criterion_code)

    # Determiner le pilier courant a partir du code critere
    current_pillar = assessment.current_pillar
    if criterion_code.startswith("E"):
        current_pillar = "environment"
    elif criterion_code.startswith("S"):
        current_pillar = "social"
    elif criterion_code.startswith("G"):
        current_pillar = "governance"

    # Persister la mise a jour
    assessment_data = dict(assessment.assessment_data or {})
    assessment_data["criteria_scores"] = criteria_scores

    from app.models.esg import ESGStatusEnum

    await update_assessment(
        db=db,
        assessment=assessment,
        assessment_data=assessment_data,
        evaluated_criteria=evaluated_criteria,
        current_pillar=current_pillar,
        status=ESGStatusEnum.in_progress,
    )

    # Calculer la progression et les scores partiels
    progress = compute_progress_percent(evaluated_criteria)
    scores = compute_overall_score(criteria_scores, assessment.sector)

    return (
        f"Critere {criterion_code} enregistre : {score}/10.\n"
        f"- Criteres evalues : {len(evaluated_criteria)}/30\n"
        f"- Progression : {progress}%\n"
        f"- Scores partiels — E: {scores['environment_score']}, "
        f"S: {scores['social_score']}, G: {scores['governance_score']}, "
        f"Global: {scores['overall_score']}"
    )


@tool
async def finalize_esg_assessment(
    assessment_id: str,
    config: RunnableConfig,
) -> str:
    """Finaliser l'evaluation ESG et calculer les scores definitifs, le benchmark sectoriel et les recommandations.

    N'appelle ce tool que si l'utilisateur a explicitement confirme vouloir finaliser.
    Demande d'abord confirmation.

    Args:
        assessment_id: Identifiant UUID de l'evaluation ESG a finaliser.
    """
    from app.modules.esg.service import finalize_assessment_with_benchmark, get_assessment

    db, user_id = get_db_and_user(config)

    assessment = await get_assessment(
        db=db,
        assessment_id=uuid.UUID(assessment_id),
        user_id=user_id,
    )
    if assessment is None:
        return f"Erreur : evaluation ESG {assessment_id} introuvable."

    criteria_scores = (assessment.assessment_data or {}).get("criteria_scores", {})

    finalized = await finalize_assessment_with_benchmark(
        db=db,
        assessment=assessment,
        criteria_scores=criteria_scores,
    )

    benchmark_info = ""
    if finalized.sector_benchmark:
        position = finalized.sector_benchmark.get("position", "N/A")
        percentile = finalized.sector_benchmark.get("percentile", "N/A")
        benchmark_info = f"- Position sectorielle : {position}\n- Percentile : {percentile}e\n"

    strengths_count = len(finalized.strengths or [])
    gaps_count = len(finalized.gaps or [])
    reco_count = len(finalized.recommendations or [])

    return (
        f"Evaluation ESG finalisee avec succes !\n"
        f"- Score global : {finalized.overall_score}/100\n"
        f"- Environnement : {finalized.environment_score}/100\n"
        f"- Social : {finalized.social_score}/100\n"
        f"- Gouvernance : {finalized.governance_score}/100\n"
        f"{benchmark_info}"
        f"- Points forts : {strengths_count}\n"
        f"- Lacunes identifiees : {gaps_count}\n"
        f"- Recommandations : {reco_count}"
    )


@tool
async def get_esg_assessment(
    config: RunnableConfig,
    assessment_id: str | None = None,
) -> str:
    """Recuperer une evaluation ESG existante.

    Si aucun identifiant n'est fourni, cherche une evaluation en cours (brouillon ou en progression)
    pour l'utilisateur.

    Args:
        assessment_id: Identifiant UUID de l'evaluation (optionnel).
    """
    from app.modules.esg.service import (
        compute_progress_percent,
        get_assessment,
        get_resumable_assessment,
    )

    db, user_id = get_db_and_user(config)

    assessment = None
    if assessment_id:
        assessment = await get_assessment(
            db=db,
            assessment_id=uuid.UUID(assessment_id),
            user_id=user_id,
        )
    else:
        assessment = await get_resumable_assessment(db=db, user_id=user_id)

    if assessment is None:
        if assessment_id:
            return f"Aucune evaluation ESG trouvee avec l'ID {assessment_id}."
        return "Aucune evaluation ESG en cours trouvee pour cet utilisateur."

    status = assessment.status.value if hasattr(assessment.status, "value") else assessment.status
    evaluated = assessment.evaluated_criteria or []
    progress = compute_progress_percent(evaluated)

    summary = (
        f"Evaluation ESG trouvee :\n"
        f"- ID : {assessment.id}\n"
        f"- Statut : {status}\n"
        f"- Secteur : {assessment.sector}\n"
        f"- Pilier en cours : {assessment.current_pillar or 'N/A'}\n"
        f"- Criteres evalues : {len(evaluated)}/30\n"
        f"- Progression : {progress}%"
    )

    if status == "completed" and assessment.overall_score is not None:
        summary += (
            f"\n- Score global : {assessment.overall_score}/100\n"
            f"- Environnement : {assessment.environment_score}/100\n"
            f"- Social : {assessment.social_score}/100\n"
            f"- Gouvernance : {assessment.governance_score}/100"
        )

    return summary


@tool
async def batch_save_esg_criteria(
    assessment_id: str,
    criteria: list[dict],
    config: RunnableConfig,
) -> str:
    """Sauvegarder plusieurs criteres ESG en un seul appel dans l'evaluation en cours.

    Utilise ce tool pour sauvegarder un pilier entier (10 criteres) en une seule transaction
    au lieu de 10 appels sequentiels a save_esg_criterion_score.

    Args:
        assessment_id: Identifiant UUID de l'evaluation ESG.
        criteria: Liste de criteres, chaque element est un dict avec :
            - criterion_code (str): Code du critere (ex: E1, S3, G7)
            - score (int): Note de 0 a 10
            - justification (str): Justification de la note attribuee
    """
    from app.models.esg import ESGStatusEnum
    from app.modules.esg.service import (
        compute_overall_score,
        compute_progress_percent,
        get_assessment,
        update_assessment,
    )

    db, user_id = get_db_and_user(config)

    assessment = await get_assessment(
        db=db,
        assessment_id=uuid.UUID(assessment_id),
        user_id=user_id,
    )
    if assessment is None:
        return f"Erreur : evaluation ESG {assessment_id} introuvable."

    if not criteria:
        return "Erreur : la liste de criteres est vide."

    # Validation runtime de la completude des piliers (BUG-V5-003).
    # On deduplique les codes ; en cas de doublon, la derniere occurrence est
    # celle qui sera persistee plus bas (politique "last write wins").
    request_codes = [c["criterion_code"] for c in criteria]
    already_evaluated = list(assessment.evaluated_criteria or [])
    validation_error = _validate_pillar_completeness(request_codes, already_evaluated)
    if validation_error is not None:
        # Aucune ecriture en BDD : idempotence garantie.
        return validation_error

    # Copie immutable des scores et criteres evalues
    criteria_scores = dict((assessment.assessment_data or {}).get("criteria_scores", {}))
    evaluated_criteria = list(assessment.evaluated_criteria or [])

    # Appliquer chaque critere (codes normalises, doublons ecrases : last write wins)
    for criterion in criteria:
        code = _normalize_code(criterion["criterion_code"])
        criteria_scores[code] = {
            "score": criterion["score"],
            "justification": criterion["justification"],
        }
        if code not in evaluated_criteria:
            evaluated_criteria.append(code)

    # Determiner le pilier courant a partir du dernier critere
    last_code = _normalize_code(criteria[-1]["criterion_code"])
    current_pillar = assessment.current_pillar
    if last_code.startswith("E"):
        current_pillar = "environment"
    elif last_code.startswith("S"):
        current_pillar = "social"
    elif last_code.startswith("G"):
        current_pillar = "governance"

    # Persister la mise a jour en une seule transaction
    assessment_data = dict(assessment.assessment_data or {})
    assessment_data["criteria_scores"] = criteria_scores

    await update_assessment(
        db=db,
        assessment=assessment,
        assessment_data=assessment_data,
        evaluated_criteria=evaluated_criteria,
        current_pillar=current_pillar,
        status=ESGStatusEnum.in_progress,
    )

    # Calculer la progression et les scores partiels
    progress = compute_progress_percent(evaluated_criteria)
    scores = compute_overall_score(criteria_scores, assessment.sector)

    saved_codes = [_normalize_code(c["criterion_code"]) for c in criteria]
    return (
        f"{len(criteria)} criteres enregistres : {', '.join(saved_codes)}.\n"
        f"- Criteres evalues : {len(evaluated_criteria)}/30\n"
        f"- Progression : {progress}%\n"
        f"- Scores partiels — E: {scores['environment_score']}, "
        f"S: {scores['social_score']}, G: {scores['governance_score']}, "
        f"Global: {scores['overall_score']}"
    )


ESG_TOOLS = [
    with_retry(create_esg_assessment, max_retries=2, node_name="esg_scoring"),
    with_retry(save_esg_criterion_score, max_retries=2, node_name="esg_scoring"),
    with_retry(finalize_esg_assessment, max_retries=2, node_name="esg_scoring"),
    with_retry(get_esg_assessment, max_retries=2, node_name="esg_scoring"),
    with_retry(batch_save_esg_criteria, max_retries=2, node_name="esg_scoring"),
]
