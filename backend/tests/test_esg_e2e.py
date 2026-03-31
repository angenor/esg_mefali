"""Tests E2E du parcours complet ESG : creation, evaluation, resultats.

Teste l'integration des differentes couches du module ESG
sans appeler le LLM (mock).
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.esg.criteria import ALL_CRITERIA, PILLAR_CRITERIA, PILLAR_ORDER
from app.modules.esg.service import (
    build_initial_esg_state,
    compute_benchmark_comparison,
    compute_overall_score,
    finalize_assessment_with_benchmark,
    generate_recommendations,
    generate_strengths_gaps,
    get_next_pillar,
    get_resumable_assessment,
    search_relevant_chunks,
)


@pytest.fixture
def full_criteria_scores() -> dict:
    """Scores complets simulant une evaluation terminee."""
    scores: dict[str, dict] = {}
    # Simuler des scores varies
    score_values = [8, 6, 4, 7, 5, 9, 3, 7, 6, 8]
    for pillar in PILLAR_ORDER:
        criteria = PILLAR_CRITERIA[pillar]
        for i, criterion in enumerate(criteria):
            scores[criterion.code] = {
                "score": score_values[i],
                "justification": f"Evaluation de {criterion.label}",
                "sources": [],
            }
    return scores


class TestE2EEvaluationFlow:
    """Test du flux complet d'evaluation ESG."""

    def test_full_scoring_pipeline(self, full_criteria_scores: dict):
        """Test du pipeline : scores -> recommandations -> benchmark."""
        sector = "agriculture"

        # Etape 1 : Calculer les scores
        scores = compute_overall_score(full_criteria_scores, sector)
        assert "overall_score" in scores
        assert "environment_score" in scores
        assert "social_score" in scores
        assert "governance_score" in scores
        assert 0 <= scores["overall_score"] <= 100

        # Etape 2 : Generer recommandations
        recommendations = generate_recommendations(full_criteria_scores)
        assert isinstance(recommendations, list)
        # Les criteres avec score <= 4 doivent avoir des recommandations
        weak_count = sum(
            1 for d in full_criteria_scores.values() if d["score"] <= 4
        )
        assert len(recommendations) == weak_count

        # Etape 3 : Identifier points forts et lacunes
        strengths, gaps = generate_strengths_gaps(full_criteria_scores)
        assert isinstance(strengths, list)
        assert isinstance(gaps, list)
        strong_count = sum(
            1 for d in full_criteria_scores.values() if d["score"] >= 7
        )
        assert len(strengths) == strong_count

        # Etape 4 : Benchmark sectoriel
        benchmark = compute_benchmark_comparison(sector, scores)
        assert benchmark is not None
        assert benchmark["sector"] == "agriculture"
        assert "averages" in benchmark
        assert "position" in benchmark
        assert benchmark["position"] in ("above_average", "average", "below_average")

    def test_pillar_progression(self):
        """Test de la progression entre piliers E -> S -> G."""
        assert get_next_pillar("environment") == "social"
        assert get_next_pillar("social") == "governance"
        assert get_next_pillar("governance") is None
        assert get_next_pillar("unknown") is None

    def test_initial_state_structure(self):
        """Test de la structure initiale de l'etat ESG."""
        state = build_initial_esg_state("test-id", "agriculture")
        assert state["assessment_id"] == "test-id"
        assert state["status"] == "in_progress"
        assert state["current_pillar"] == "environment"
        assert state["evaluated_criteria"] == []
        assert state["partial_scores"] == {}


class TestBenchmarkComparison:
    """Tests du benchmark sectoriel."""

    def test_known_sector_benchmark(self):
        """Benchmark avec un secteur connu."""
        scores = {"overall_score": 70, "environment_score": 75, "social_score": 68, "governance_score": 67}
        result = compute_benchmark_comparison("agriculture", scores)
        assert result is not None
        assert result["sector"] == "agriculture"
        assert "percentile" in result

    def test_unknown_sector_fallback(self):
        """Benchmark de repli pour un secteur inconnu."""
        scores = {"overall_score": 60, "environment_score": 65, "social_score": 58, "governance_score": 57}
        result = compute_benchmark_comparison("secteur_inconnu", scores)
        assert result is not None
        assert result["sector"] == "general"
        assert "averages" in result

    def test_above_average_detection(self):
        """Detection du positionnement au-dessus de la moyenne."""
        scores = {"overall_score": 80, "environment_score": 85, "social_score": 78, "governance_score": 77}
        result = compute_benchmark_comparison("agriculture", scores)
        assert result["position"] == "above_average"

    def test_below_average_detection(self):
        """Detection du positionnement en-dessous de la moyenne."""
        scores = {"overall_score": 20, "environment_score": 25, "social_score": 18, "governance_score": 17}
        result = compute_benchmark_comparison("agriculture", scores)
        assert result["position"] == "below_average"


class TestRAGIntegration:
    """Tests de l'integration RAG dans le flux ESG."""

    @pytest.mark.asyncio
    async def test_rag_search_with_known_criteria(self):
        """La recherche RAG fonctionne avec un critere connu."""
        mock_db = AsyncMock()
        with patch(
            "app.modules.esg.service._search_chunks_by_query",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await search_relevant_chunks(
                db=mock_db,
                criteria_code="E1",
                user_id=uuid.uuid4(),
            )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_rag_search_with_unknown_criteria_returns_empty(self):
        """La recherche RAG retourne vide pour un critere inconnu."""
        mock_db = AsyncMock()
        result = await search_relevant_chunks(
            db=mock_db,
            criteria_code="UNKNOWN",
            user_id=uuid.uuid4(),
        )
        assert result == []


class TestResumableAssessment:
    """Tests de la reprise d'evaluation interrompue."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_assessment(self):
        """Retourne None si aucune evaluation en cours."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_resumable_assessment(mock_db, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_in_progress_assessment(self):
        """Retourne une evaluation in_progress existante."""
        mock_db = AsyncMock()
        mock_assessment = MagicMock()
        mock_assessment.status = "in_progress"
        mock_assessment.current_pillar = "social"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_assessment
        mock_db.execute.return_value = mock_result

        result = await get_resumable_assessment(mock_db, uuid.uuid4())
        assert result is not None
        assert result.status == "in_progress"
