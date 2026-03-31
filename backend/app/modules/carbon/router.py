"""Endpoints REST pour le module Calculateur d'Empreinte Carbone."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.carbon import CarbonStatusEnum
from app.models.user import User
from app.modules.carbon.schemas import (
    AddEntriesRequest,
    AddEntriesResponse,
    BenchmarkDetailResponse,
    CarbonAssessmentCreate,
    CarbonAssessmentList,
    CarbonAssessmentResponse,
    CarbonAssessmentSummary,
    CarbonSummaryResponse,
    CategoryBreakdown,
    EquivalenceResponse,
    SectorBenchmarkResponse,
)

router = APIRouter()


@router.post("/assessments", response_model=CarbonAssessmentResponse, status_code=201)
async def create_assessment(
    body: CarbonAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonAssessmentResponse:
    """Creer un nouveau bilan carbone pour l'annee specifiee."""
    from app.modules.carbon.service import create_assessment as create_svc

    # Recuperer le secteur du profil si disponible
    sector: str | None = None
    try:
        from app.modules.company.service import get_or_create_profile

        profile = await get_or_create_profile(db, current_user.id)
        if profile.sector:
            sector = profile.sector.value if hasattr(profile.sector, "value") else profile.sector
    except Exception:
        pass

    try:
        assessment = await create_svc(
            db=db,
            user_id=current_user.id,
            year=body.year,
            sector=sector,
            conversation_id=body.conversation_id,
        )
        await db.commit()
        await db.refresh(assessment)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return CarbonAssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=CarbonAssessmentList)
async def list_assessments(
    status: str | None = Query(None, description="Filtrer par statut (in_progress|completed)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonAssessmentList:
    """Lister les bilans carbone de l'utilisateur."""
    from app.modules.carbon.service import list_assessments as list_svc

    assessments, total = await list_svc(
        db=db,
        user_id=current_user.id,
        status=status,
        page=page,
        limit=limit,
    )

    return CarbonAssessmentList(
        items=[CarbonAssessmentSummary.model_validate(a) for a in assessments],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/assessments/{assessment_id}", response_model=CarbonAssessmentResponse)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonAssessmentResponse:
    """Detail complet d'un bilan carbone avec ses entrees."""
    from app.modules.carbon.service import get_assessment as get_svc

    assessment = await get_svc(db=db, assessment_id=assessment_id, user_id=current_user.id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Bilan carbone non trouve.")

    return CarbonAssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/entries", response_model=AddEntriesResponse, status_code=201)
async def add_entries(
    assessment_id: uuid.UUID,
    body: AddEntriesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AddEntriesResponse:
    """Ajouter des entrees d'emissions a un bilan en cours."""
    from app.modules.carbon.service import add_entries as add_svc, get_assessment as get_svc

    assessment = await get_svc(db=db, assessment_id=assessment_id, user_id=current_user.id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Bilan carbone non trouve.")

    try:
        entries_data = [e.model_dump() for e in body.entries]
        added, total, completed = await add_svc(
            db=db,
            assessment=assessment,
            entries_data=entries_data,
            mark_category_complete=body.mark_category_complete,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AddEntriesResponse(
        entries_added=added,
        total_emissions_tco2e=total,
        completed_categories=completed,
    )


@router.get("/assessments/{assessment_id}/summary", response_model=CarbonSummaryResponse)
async def get_summary(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CarbonSummaryResponse:
    """Resume complet d'un bilan pour la page resultats."""
    from app.modules.carbon.service import get_assessment as get_svc, get_assessment_summary

    assessment = await get_svc(db=db, assessment_id=assessment_id, user_id=current_user.id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Bilan carbone non trouve.")

    summary = await get_assessment_summary(db, assessment)

    # Convertir en schema de reponse
    by_category = {
        k: CategoryBreakdown(**v) for k, v in summary["by_category"].items()
    }
    equivalences = [EquivalenceResponse(**e) for e in summary["equivalences"]]
    sector_benchmark = (
        SectorBenchmarkResponse(**summary["sector_benchmark"])
        if summary.get("sector_benchmark")
        else None
    )

    return CarbonSummaryResponse(
        assessment_id=assessment.id,
        year=summary["year"],
        status=summary["status"],
        total_emissions_tco2e=summary["total_emissions_tco2e"],
        by_category=by_category,
        equivalences=equivalences,
        reduction_plan=summary.get("reduction_plan"),
        sector_benchmark=sector_benchmark,
    )


@router.get("/benchmarks/{sector}", response_model=BenchmarkDetailResponse)
async def get_benchmark(
    sector: str,
    current_user: User = Depends(get_current_user),
) -> BenchmarkDetailResponse:
    """Benchmark carbone pour un secteur donne."""
    from app.modules.carbon.benchmarks import get_sector_benchmark

    benchmark = get_sector_benchmark(sector)
    if benchmark is None:
        raise HTTPException(
            status_code=404,
            detail="Donnees de benchmark non disponibles pour ce secteur",
        )

    return BenchmarkDetailResponse(
        sector=benchmark.get("sector", sector),
        average_emissions_tco2e=benchmark["average_emissions_tco2e"],
        median_emissions_tco2e=benchmark["median_emissions_tco2e"],
        by_category=benchmark["by_category"],
        sample_size=benchmark["sample_size"],
        source=benchmark["source"],
        fallback_sector=benchmark.get("fallback_from"),
    )
