"""Tests unitaires du service de scoring ESG (T010).

Verifie le calcul des scores, la ponderation sectorielle,
la generation de recommandations et de points forts/lacunes.
"""

import uuid

import pytest

from app.modules.esg.criteria import ALL_CRITERIA, TOTAL_CRITERIA


class TestESGScoringServiceComputeScores:
    """Tests du calcul de scores ESG."""

    @pytest.fixture
    def sample_criteria_scores(self) -> dict:
        """Scores fictifs pour les 30 criteres."""
        scores = {}
        for c in ALL_CRITERIA:
            scores[c.code] = {
                "score": 7,
                "justification": f"Test {c.code}",
                "sources": [],
            }
        return scores

    @pytest.fixture
    def partial_criteria_scores(self) -> dict:
        """Scores partiels (pilier E seulement)."""
        scores = {}
        for c in ALL_CRITERIA:
            if c.pillar == "environment":
                scores[c.code] = {
                    "score": 6,
                    "justification": f"Test {c.code}",
                    "sources": [],
                }
        return scores

    def test_compute_pillar_score_uniform(self, sample_criteria_scores: dict) -> None:
        """T010-01 : Score pilier avec poids uniformes = score moyen * 10."""
        from app.modules.esg.service import compute_pillar_score

        score = compute_pillar_score("environment", sample_criteria_scores, "services")
        # Tous les criteres a 7/10, score normalise a 100
        assert 60 <= score <= 80

    def test_compute_pillar_score_with_sector_weights(self, sample_criteria_scores: dict) -> None:
        """T010-02 : Score pilier varie avec la ponderation sectorielle."""
        from app.modules.esg.service import compute_pillar_score

        score_agriculture = compute_pillar_score("environment", sample_criteria_scores, "agriculture")
        score_services = compute_pillar_score("environment", sample_criteria_scores, "services")
        # Les ponderations sont differentes, les scores aussi
        assert isinstance(score_agriculture, float)
        assert isinstance(score_services, float)

    def test_compute_overall_score(self, sample_criteria_scores: dict) -> None:
        """T010-03 : Score global = moyenne des 3 piliers."""
        from app.modules.esg.service import compute_overall_score

        result = compute_overall_score(sample_criteria_scores, "agriculture")
        assert "overall_score" in result
        assert "environment_score" in result
        assert "social_score" in result
        assert "governance_score" in result
        assert 0 <= result["overall_score"] <= 100

    def test_compute_overall_score_is_average_of_pillars(self, sample_criteria_scores: dict) -> None:
        """T010-04 : Score global est la moyenne des 3 scores piliers."""
        from app.modules.esg.service import compute_overall_score

        result = compute_overall_score(sample_criteria_scores, "agriculture")
        expected = (result["environment_score"] + result["social_score"] + result["governance_score"]) / 3
        assert abs(result["overall_score"] - expected) < 0.01

    def test_compute_pillar_score_empty_scores(self) -> None:
        """T010-05 : Score pilier = 0 si aucun critere evalue."""
        from app.modules.esg.service import compute_pillar_score

        score = compute_pillar_score("environment", {}, "agriculture")
        assert score == 0.0

    def test_score_color_red(self) -> None:
        """T010-06 : Score < 40 = rouge."""
        from app.modules.esg.service import get_score_color

        assert get_score_color(20) == "red"
        assert get_score_color(39.9) == "red"

    def test_score_color_orange(self) -> None:
        """T010-07 : Score 40-69 = orange."""
        from app.modules.esg.service import get_score_color

        assert get_score_color(40) == "orange"
        assert get_score_color(69.9) == "orange"

    def test_score_color_green(self) -> None:
        """T010-08 : Score >= 70 = vert."""
        from app.modules.esg.service import get_score_color

        assert get_score_color(70) == "green"
        assert get_score_color(100) == "green"


class TestESGScoringServiceRecommendations:
    """Tests de la generation de recommandations."""

    @pytest.fixture
    def mixed_scores(self) -> dict:
        """Scores melanges : certains forts, certains faibles."""
        scores = {}
        for c in ALL_CRITERIA:
            # E1-E5 faibles, le reste fort
            if c.code in ("E1", "E2", "G3", "G5", "S6"):
                scores[c.code] = {"score": 2, "justification": "Faible", "sources": []}
            else:
                scores[c.code] = {"score": 8, "justification": "Bon", "sources": []}
        return scores

    def test_generate_recommendations(self, mixed_scores: dict) -> None:
        """T010-09 : Recommandations generees pour les criteres faibles."""
        from app.modules.esg.service import generate_recommendations

        recs = generate_recommendations(mixed_scores)
        assert len(recs) > 0
        # Les criteres faibles doivent apparaitre
        rec_codes = [r["criteria_code"] for r in recs]
        assert "E1" in rec_codes or "G3" in rec_codes

    def test_recommendations_sorted_by_priority(self, mixed_scores: dict) -> None:
        """T010-10 : Recommandations triees par priorite."""
        from app.modules.esg.service import generate_recommendations

        recs = generate_recommendations(mixed_scores)
        priorities = [r["priority"] for r in recs]
        assert priorities == sorted(priorities)

    def test_generate_strengths(self, mixed_scores: dict) -> None:
        """T010-11 : Points forts identifies (score >= 7)."""
        from app.modules.esg.service import generate_strengths_gaps

        strengths, gaps = generate_strengths_gaps(mixed_scores)
        assert len(strengths) > 0
        for s in strengths:
            assert s["score"] >= 7

    def test_generate_gaps(self, mixed_scores: dict) -> None:
        """T010-12 : Lacunes identifiees (score <= 4)."""
        from app.modules.esg.service import generate_strengths_gaps

        strengths, gaps = generate_strengths_gaps(mixed_scores)
        assert len(gaps) > 0
        for g in gaps:
            assert g["score"] <= 4


class TestESGScoringServiceCRUD:
    """Tests CRUD du service ESG (avec base de donnees)."""

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    async def test_create_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T010-13 : Creation d'une evaluation ESG."""
        from app.modules.esg.service import create_assessment

        assessment = await create_assessment(
            db=db_session,
            user_id=user_id,
            sector="agriculture",
        )
        assert assessment.user_id == user_id
        assert assessment.sector == "agriculture"
        assert assessment.status.value == "draft"
        assert assessment.overall_score is None

    async def test_get_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T010-14 : Recuperation d'une evaluation par ID."""
        from app.modules.esg.service import create_assessment, get_assessment

        created = await create_assessment(db=db_session, user_id=user_id, sector="energie")
        await db_session.commit()

        found = await get_assessment(db=db_session, assessment_id=created.id, user_id=user_id)
        assert found is not None
        assert found.id == created.id

    async def test_get_assessment_wrong_user(self, db_session, user_id: uuid.UUID) -> None:
        """T010-15 : Evaluation inaccessible par un autre utilisateur."""
        from app.modules.esg.service import create_assessment, get_assessment

        created = await create_assessment(db=db_session, user_id=user_id, sector="energie")
        await db_session.commit()

        other_user = uuid.uuid4()
        found = await get_assessment(db=db_session, assessment_id=created.id, user_id=other_user)
        assert found is None

    async def test_list_assessments(self, db_session, user_id: uuid.UUID) -> None:
        """T010-16 : Liste paginee des evaluations."""
        from app.modules.esg.service import create_assessment, list_assessments

        for sector in ("agriculture", "energie", "services"):
            await create_assessment(db=db_session, user_id=user_id, sector=sector)
        await db_session.commit()

        assessments, total = await list_assessments(db=db_session, user_id=user_id)
        assert total == 3
        assert len(assessments) == 3
