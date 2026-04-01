"""Tests pour les tools ESG du noeud d'evaluation."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.esg_tools import (
    create_esg_assessment,
    finalize_esg_assessment,
    get_esg_assessment,
    save_esg_criterion_score,
)


# --- Helpers pour creer des mocks d'assessment ---


def _make_assessment(
    *,
    assessment_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    status: str = "draft",
    sector: str = "agriculture",
    current_pillar: str = "environment",
    evaluated_criteria: list | None = None,
    assessment_data: dict | None = None,
    overall_score: float | None = None,
    environment_score: float | None = None,
    social_score: float | None = None,
    governance_score: float | None = None,
    strengths: list | None = None,
    gaps: list | None = None,
    recommendations: list | None = None,
    sector_benchmark: dict | None = None,
) -> MagicMock:
    """Creer un mock d'ESGAssessment avec les attributs donnes."""
    mock = MagicMock()
    mock.id = assessment_id or uuid.uuid4()
    mock.user_id = user_id or uuid.uuid4()

    # Simuler l'enum status
    status_enum = MagicMock()
    status_enum.value = status
    mock.status = status_enum

    mock.sector = sector
    mock.current_pillar = current_pillar
    mock.evaluated_criteria = evaluated_criteria or []
    mock.assessment_data = assessment_data or {}
    mock.overall_score = overall_score
    mock.environment_score = environment_score
    mock.social_score = social_score
    mock.governance_score = governance_score
    mock.strengths = strengths
    mock.gaps = gaps
    mock.recommendations = recommendations
    mock.sector_benchmark = sector_benchmark

    return mock


# --- Tests create_esg_assessment ---


class TestCreateEsgAssessment:
    """Tests pour le tool create_esg_assessment."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.create_assessment", new_callable=AsyncMock)
    async def test_create_success(
        self,
        mock_create: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Creer une evaluation ESG avec succes."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment = _make_assessment(status="draft", sector="services")
        mock_create.return_value = assessment

        result = await create_esg_assessment.ainvoke(input={}, config=mock_config)

        assert "creee avec succes" in result
        assert str(assessment.id) in result
        assert "draft" in result
        mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.create_assessment", new_callable=AsyncMock)
    async def test_create_error(
        self,
        mock_create: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Retourner un message d'erreur en cas d'exception."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        mock_create.side_effect = RuntimeError("DB connection lost")

        result = await create_esg_assessment.ainvoke(input={}, config=mock_config)

        assert "Erreur" in result
        assert "DB connection lost" in result


# --- Tests save_esg_criterion_score ---


class TestSaveEsgCriterionScore:
    """Tests pour le tool save_esg_criterion_score."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.update_assessment", new_callable=AsyncMock)
    async def test_save_criterion_success(
        self,
        mock_update: AsyncMock,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Sauvegarder un critere avec succes, retourne le compte et le score partiel."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment_id = uuid.uuid4()
        assessment = _make_assessment(
            assessment_id=assessment_id,
            status="in_progress",
            sector="agriculture",
            evaluated_criteria=["E1"],
            assessment_data={"criteria_scores": {"E1": {"score": 7, "justification": "Bon"}}},
        )
        mock_get.return_value = assessment
        mock_update.return_value = assessment

        result = await save_esg_criterion_score.ainvoke(
            input={
                "assessment_id": str(assessment_id),
                "criterion_code": "E2",
                "score": 6,
                "justification": "Pratiques moderees",
            },
            config=mock_config,
        )

        assert "E2 enregistre" in result
        assert "6/10" in result
        assert "2/30" in result
        mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    async def test_save_criterion_assessment_not_found(
        self,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Retourner une erreur si l'evaluation n'existe pas."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        mock_get.return_value = None
        fake_id = str(uuid.uuid4())

        result = await save_esg_criterion_score.ainvoke(
            input={
                "assessment_id": fake_id,
                "criterion_code": "E1",
                "score": 5,
                "justification": "Test",
            },
            config=mock_config,
        )

        assert "introuvable" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.update_assessment", new_callable=AsyncMock)
    async def test_save_criterion_updates_pillar(
        self,
        mock_update: AsyncMock,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Verifier que le pilier courant est mis a jour selon le code critere."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment_id = uuid.uuid4()
        assessment = _make_assessment(
            assessment_id=assessment_id,
            current_pillar="environment",
            evaluated_criteria=[],
            assessment_data={},
        )
        mock_get.return_value = assessment
        mock_update.return_value = assessment

        # Sauvegarder un critere social -> pilier doit changer
        await save_esg_criterion_score.ainvoke(
            input={
                "assessment_id": str(assessment_id),
                "criterion_code": "S3",
                "score": 8,
                "justification": "Excellente formation",
            },
            config=mock_config,
        )

        call_kwargs = mock_update.call_args.kwargs
        assert call_kwargs["current_pillar"] == "social"


# --- Tests finalize_esg_assessment ---


class TestFinalizeEsgAssessment:
    """Tests pour le tool finalize_esg_assessment."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.finalize_assessment_with_benchmark", new_callable=AsyncMock)
    async def test_finalize_success(
        self,
        mock_finalize: AsyncMock,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Finaliser une evaluation avec succes, retourne les scores finaux."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment_id = uuid.uuid4()

        # Assessment avant finalisation
        assessment = _make_assessment(
            assessment_id=assessment_id,
            status="in_progress",
            assessment_data={"criteria_scores": {"E1": {"score": 7, "justification": "OK"}}},
        )
        mock_get.return_value = assessment

        # Assessment apres finalisation
        finalized = _make_assessment(
            assessment_id=assessment_id,
            status="completed",
            overall_score=65.0,
            environment_score=72.0,
            social_score=60.0,
            governance_score=63.0,
            strengths=[{"title": "Bonne gestion"}],
            gaps=[{"title": "Manque ethique"}],
            recommendations=[{"title": "Ameliorer G3"}],
            sector_benchmark={"position": "above_average", "percentile": 68},
        )
        mock_finalize.return_value = finalized

        result = await finalize_esg_assessment.ainvoke(
            input={"assessment_id": str(assessment_id)},
            config=mock_config,
        )

        assert "finalisee avec succes" in result
        assert "65.0/100" in result
        assert "72.0/100" in result
        assert "above_average" in result
        assert "Points forts : 1" in result
        assert "Recommandations : 1" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    async def test_finalize_assessment_not_found(
        self,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Retourner une erreur si l'evaluation n'existe pas."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        mock_get.return_value = None
        fake_id = str(uuid.uuid4())

        result = await finalize_esg_assessment.ainvoke(
            input={"assessment_id": fake_id},
            config=mock_config,
        )

        assert "introuvable" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.finalize_assessment_with_benchmark", new_callable=AsyncMock)
    async def test_finalize_error(
        self,
        mock_finalize: AsyncMock,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Retourner un message d'erreur en cas d'exception."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment = _make_assessment(assessment_data={"criteria_scores": {}})
        mock_get.return_value = assessment
        mock_finalize.side_effect = RuntimeError("Calcul impossible")

        result = await finalize_esg_assessment.ainvoke(
            input={"assessment_id": str(uuid.uuid4())},
            config=mock_config,
        )

        assert "Erreur" in result
        assert "Calcul impossible" in result

    def test_docstring_contains_confirmation_instruction(self) -> None:
        """FR-019 : le docstring du tool doit indiquer de demander confirmation."""
        docstring = finalize_esg_assessment.description or ""
        assert "confirme" in docstring.lower() or "confirmation" in docstring.lower()


# --- Tests get_esg_assessment ---


class TestGetEsgAssessment:
    """Tests pour le tool get_esg_assessment."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    async def test_get_with_id(
        self,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Recuperer une evaluation par ID."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment_id = uuid.uuid4()
        assessment = _make_assessment(
            assessment_id=assessment_id,
            status="in_progress",
            sector="energie",
            current_pillar="social",
            evaluated_criteria=["E1", "E2", "E3"],
        )
        mock_get.return_value = assessment

        result = await get_esg_assessment.ainvoke(
            input={"assessment_id": str(assessment_id)},
            config=mock_config,
        )

        assert str(assessment_id) in result
        assert "in_progress" in result
        assert "3/30" in result
        mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_get_without_id_finds_resumable(
        self,
        mock_resumable: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Sans ID, chercher une evaluation en cours a reprendre."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment = _make_assessment(
            status="in_progress",
            evaluated_criteria=["E1", "E2"],
        )
        mock_resumable.return_value = assessment

        result = await get_esg_assessment.ainvoke(input={}, config=mock_config)

        assert "trouvee" in result
        assert "2/30" in result
        mock_resumable.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_get_without_id_none_found(
        self,
        mock_resumable: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Sans ID et aucune evaluation en cours, retourner un message informatif."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        mock_resumable.return_value = None

        result = await get_esg_assessment.ainvoke(input={}, config=mock_config)

        assert "Aucune evaluation ESG en cours" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    async def test_get_completed_shows_scores(
        self,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Une evaluation completee affiche les scores finaux."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        assessment_id = uuid.uuid4()
        assessment = _make_assessment(
            assessment_id=assessment_id,
            status="completed",
            overall_score=72.5,
            environment_score=80.0,
            social_score=65.0,
            governance_score=72.5,
            evaluated_criteria=[f"E{i}" for i in range(1, 11)]
            + [f"S{i}" for i in range(1, 11)]
            + [f"G{i}" for i in range(1, 11)],
        )
        mock_get.return_value = assessment

        result = await get_esg_assessment.ainvoke(
            input={"assessment_id": str(assessment_id)},
            config=mock_config,
        )

        assert "72.5/100" in result
        assert "80.0/100" in result
        assert "30/30" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.esg_tools.get_db_and_user")
    @patch("app.modules.esg.service.get_assessment", new_callable=AsyncMock)
    async def test_get_with_id_not_found(
        self,
        mock_get: AsyncMock,
        mock_get_db_user: MagicMock,
        mock_db: AsyncMock,
        mock_user_id: uuid.UUID,
        mock_config: dict,
    ) -> None:
        """Retourner un message d'erreur si l'ID n'existe pas."""
        mock_get_db_user.return_value = (mock_db, mock_user_id)
        mock_get.return_value = None
        fake_id = str(uuid.uuid4())

        result = await get_esg_assessment.ainvoke(
            input={"assessment_id": fake_id},
            config=mock_config,
        )

        assert "Aucune evaluation ESG trouvee" in result
        assert fake_id in result
