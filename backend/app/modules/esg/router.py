"""Endpoints REST pour le module ESG."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.esg.schemas import (
    BenchmarkResponse,
    CriteriaScoreResponse,
    ESGAssessmentCreate,
    ESGAssessmentList,
    ESGAssessmentResponse,
    ESGAssessmentSummary,
    EvaluateRequest,
    EvaluateResponse,
    PillarScoreResponse,
    ScoreResponse,
)

router = APIRouter()


@router.post("/assessments", response_model=ESGAssessmentResponse, status_code=201)
async def create_assessment(
    body: ESGAssessmentCreate | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ESGAssessmentResponse:
    """Creer une nouvelle evaluation ESG."""
    from app.modules.company.service import get_or_create_profile
    from app.modules.esg.service import create_assessment as create_assessment_svc

    # Verifier que le profil a un secteur
    profile = await get_or_create_profile(db, current_user.id)
    if not profile.sector:
        raise HTTPException(
            status_code=400,
            detail="Profil entreprise incomplet : secteur manquant. Renseignez votre secteur d'activite.",
        )

    conversation_id = body.conversation_id if body else None

    assessment = await create_assessment_svc(
        db=db,
        user_id=current_user.id,
        sector=profile.sector.value,
        conversation_id=conversation_id,
    )
    await db.commit()
    await db.refresh(assessment)

    return ESGAssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=ESGAssessmentList)
async def list_assessments(
    status: str | None = Query(None, description="Filtrer par statut"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ESGAssessmentList:
    """Lister les evaluations ESG de l'utilisateur."""
    from app.modules.esg.service import list_assessments as list_assessments_svc

    assessments, total = await list_assessments_svc(
        db=db,
        user_id=current_user.id,
        status=status,
        page=page,
        limit=limit,
    )

    return ESGAssessmentList(
        data=[ESGAssessmentSummary.model_validate(a) for a in assessments],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/assessments/{assessment_id}", response_model=ESGAssessmentResponse)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ESGAssessmentResponse:
    """Detail complet d'une evaluation ESG."""
    from app.modules.esg.service import get_assessment as get_assessment_svc

    assessment = await get_assessment_svc(
        db=db,
        assessment_id=assessment_id,
        user_id=current_user.id,
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Evaluation non trouvee.")

    return ESGAssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/evaluate", response_model=EvaluateResponse)
async def evaluate_assessment(
    assessment_id: uuid.UUID,
    body: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvaluateResponse:
    """Mettre a jour l'etat de l'evaluation apres une interaction."""
    from app.modules.esg.service import (
        compute_progress_percent,
        get_assessment as get_assessment_svc,
    )

    assessment = await get_assessment_svc(
        db=db,
        assessment_id=assessment_id,
        user_id=current_user.id,
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Evaluation non trouvee.")

    evaluated = assessment.evaluated_criteria or []
    progress = compute_progress_percent(evaluated)

    return EvaluateResponse(
        assessment_id=assessment.id,
        status=assessment.status,
        current_pillar=assessment.current_pillar,
        evaluated_criteria=evaluated,
        progress_percent=progress,
        total_criteria=30,
    )


@router.get("/assessments/{assessment_id}/score", response_model=ScoreResponse)
async def get_score(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScoreResponse:
    """Score detaille avec ventilation par critere."""
    from app.modules.esg.criteria import CRITERIA_BY_CODE, PILLAR_CRITERIA
    from app.modules.esg.service import get_assessment as get_assessment_svc, get_score_color
    from app.modules.esg.weights import get_criterion_weight

    assessment = await get_assessment_svc(
        db=db,
        assessment_id=assessment_id,
        user_id=current_user.id,
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Evaluation non trouvee.")

    if assessment.overall_score is None:
        raise HTTPException(status_code=400, detail="Evaluation non terminee.")

    assessment_data = assessment.assessment_data or {}
    criteria_scores = assessment_data.get("criteria_scores", {})

    pillars: dict[str, PillarScoreResponse] = {}
    pillar_score_map = {
        "environment": assessment.environment_score or 0,
        "social": assessment.social_score or 0,
        "governance": assessment.governance_score or 0,
    }

    for pillar_key, pillar_criteria in PILLAR_CRITERIA.items():
        criteria_list: list[CriteriaScoreResponse] = []
        for c in pillar_criteria:
            score_data = criteria_scores.get(c.code, {})
            criteria_list.append(CriteriaScoreResponse(
                code=c.code,
                label=c.label,
                score=score_data.get("score", 0),
                max=10,
                weight=get_criterion_weight(assessment.sector, c.code),
            ))
        pillars[pillar_key] = PillarScoreResponse(
            score=pillar_score_map[pillar_key],
            criteria=criteria_list,
        )

    return ScoreResponse(
        assessment_id=assessment.id,
        status=assessment.status,
        overall_score=assessment.overall_score,
        color=get_score_color(assessment.overall_score),
        pillars=pillars,
        strengths_count=len(assessment.strengths or []),
        gaps_count=len(assessment.gaps or []),
        recommendations_count=len(assessment.recommendations or []),
    )


@router.get("/benchmarks/{sector}", response_model=BenchmarkResponse)
async def get_benchmark(
    sector: str,
    current_user: User = Depends(get_current_user),
) -> BenchmarkResponse:
    """Benchmark sectoriel pour comparaison.

    Si le secteur n'est pas connu, retourne un benchmark general (moyenne tous secteurs).
    """
    from app.modules.esg.weights import get_sector_benchmark

    benchmark = get_sector_benchmark(sector)
    if benchmark is not None:
        return BenchmarkResponse(
            sector=benchmark["sector"],
            sector_label=benchmark["sector_label"],
            averages=benchmark["averages"],
            top_criteria=benchmark["top_criteria"],
            weak_criteria=benchmark["weak_criteria"],
        )

    # Benchmark de repli : moyenne generale
    return BenchmarkResponse(
        sector="general",
        sector_label=f"{sector.capitalize()} (moyenne generale)",
        averages={"environment": 48, "social": 47, "governance": 44, "overall": 46},
        top_criteria=[],
        weak_criteria=[],
    )
