"""Tests des endpoints du router credit vert."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.credit.router import _score_to_response


# --- Helpers ---


def _make_score_mock(
    version: int = 1,
    combined: float = 74.5,
    solvability: float = 68.0,
    green_impact: float = 81.0,
    confidence_level: float = 0.85,
    confidence_label: str = "good",
    expired: bool = False,
    score_breakdown: dict | None = None,
    data_sources: dict | None = None,
    recommendations: list | None = None,
) -> MagicMock:
    """Creer un mock CreditScore pour les tests du router."""
    now = datetime.now(tz=timezone.utc)
    score = MagicMock()
    score.id = uuid.uuid4()
    score.version = version
    score.combined_score = combined
    score.solvability_score = solvability
    score.green_impact_score = green_impact
    score.confidence_level = confidence_level
    score.confidence_label = confidence_label
    score.generated_at = now - timedelta(days=30)
    score.valid_until = now - timedelta(days=1) if expired else now + timedelta(days=150)
    score.score_breakdown = score_breakdown or {"solvability": {"total": solvability}, "green_impact": {"total": green_impact}}
    score.data_sources = data_sources or {"sources": [], "overall_coverage": 0.5}
    score.recommendations = recommendations or []
    return score


# --- Tests helpers router (T008) ---


class TestScoreToResponse:
    """Tests de la conversion ORM -> dict reponse."""

    def test_basic_conversion(self):
        """T008-01 : Conversion basique d'un score ORM."""
        score = _make_score_mock()

        result = _score_to_response(score)

        assert result["id"] == str(score.id)
        assert result["version"] == 1
        assert result["combined_score"] == 74.5
        assert result["confidence_label"] == "good"

    def test_string_confidence_label(self):
        """T008-02 : Gestion d'un label confiance deja string."""
        score = _make_score_mock(confidence_label="medium")

        result = _score_to_response(score)
        assert result["confidence_label"] == "medium"

    def test_enum_confidence_label(self):
        """Gestion d'un label confiance sous forme d'enum."""
        score = _make_score_mock()
        label_enum = MagicMock()
        label_enum.value = "excellent"
        score.confidence_label = label_enum

        result = _score_to_response(score)
        assert result["confidence_label"] == "excellent"


class TestGenerateEndpoint:
    """Tests du endpoint POST /generate."""

    @pytest.mark.asyncio
    async def test_generate_requires_profile(self):
        """POST /generate leve 422 sans profil."""
        from fastapi import HTTPException

        from app.modules.credit.router import generate_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        # Simuler absence de profil
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_score(db=mock_db, current_user=mock_user)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_409_concurrent(self):
        """POST /generate retourne 409 si generation en cours."""
        from fastapi import HTTPException

        from app.modules.credit.router import generate_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        # Simuler profil existant
        mock_profile_result = MagicMock()
        mock_profile_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_profile_result)

        # Simuler ValueError (generation en cours)
        with patch(
            "app.modules.credit.router.generate_score.__module__",
            create=True,
        ):
            with patch(
                "app.modules.credit.service.generate_credit_score",
                new_callable=AsyncMock,
                side_effect=ValueError("Generation en cours"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await generate_score(db=mock_db, current_user=mock_user)
                assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """POST /generate retourne 201 avec score genere."""
        from app.modules.credit.router import generate_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        # Simuler profil existant
        mock_profile_result = MagicMock()
        mock_profile_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_profile_result)

        mock_score = _make_score_mock()
        with patch(
            "app.modules.credit.service.generate_credit_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            result = await generate_score(db=mock_db, current_user=mock_user)
            assert result.combined_score == 74.5
            mock_db.commit.assert_awaited_once()


class TestGetScoreEndpoint:
    """Tests du endpoint GET /score."""

    @pytest.mark.asyncio
    async def test_get_score_404_when_no_score(self):
        """GET /score retourne 404 si aucun score."""
        from fastapi import HTTPException

        from app.modules.credit.router import get_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_score(db=mock_db, current_user=mock_user)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_score_success(self):
        """GET /score retourne le score avec indicateur expiration."""
        from app.modules.credit.router import get_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_score = _make_score_mock()

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            result = await get_score(db=mock_db, current_user=mock_user)
            assert result.combined_score == 74.5
            assert result.is_expired is False

    @pytest.mark.asyncio
    async def test_get_score_expired(self):
        """GET /score marque le score comme expire."""
        from app.modules.credit.router import get_score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_score = _make_score_mock(expired=True)

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            result = await get_score(db=mock_db, current_user=mock_user)
            assert result.is_expired is True


class TestGetBreakdownEndpoint:
    """Tests du endpoint GET /score/breakdown."""

    @pytest.mark.asyncio
    async def test_get_breakdown_404_when_no_score(self):
        """GET /score/breakdown retourne 404 si aucun score."""
        from fastapi import HTTPException

        from app.modules.credit.router import get_breakdown

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_breakdown(db=mock_db, current_user=mock_user)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_breakdown_success(self):
        """GET /score/breakdown retourne le detail complet."""
        from app.modules.credit.router import get_breakdown

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_score = _make_score_mock()
        # Schema-compatible breakdown
        mock_score.score_breakdown = {
            "solvability": {
                "total": 68.0,
                "factors": {
                    "activity_regularity": {"score": 70, "weight": 0.20, "details": "test"},
                    "information_coherence": {"score": 60, "weight": 0.20, "details": "test"},
                    "governance": {"score": 55, "weight": 0.20, "details": "test"},
                    "financial_transparency": {"score": 75, "weight": 0.20, "details": "test"},
                    "engagement_seriousness": {"score": 80, "weight": 0.20, "details": "test"},
                },
            },
            "green_impact": {
                "total": 81.0,
                "factors": {
                    "esg_global_score": {"score": 72, "weight": 0.40, "details": "test"},
                    "esg_trend": {"score": 85, "weight": 0.20, "details": "test"},
                    "carbon_engagement": {"score": 80, "weight": 0.20, "details": "test"},
                    "green_projects": {"score": 90, "weight": 0.20, "details": "test"},
                },
            },
        }
        mock_score.data_sources = {"sources": [], "overall_coverage": 0.5}
        mock_score.recommendations = [
            {"action": "Ameliorez votre profil", "impact": "high", "category": "solvability"}
        ]

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            result = await get_breakdown(db=mock_db, current_user=mock_user)
            assert result.score_breakdown is not None
            assert result.data_sources is not None
            assert result.recommendations is not None


class TestGetHistoryEndpoint:
    """Tests du endpoint GET /score/history."""

    @pytest.mark.asyncio
    async def test_history_empty(self):
        """GET /score/history retourne une liste vide."""
        from app.modules.credit.router import get_history

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        with patch(
            "app.modules.credit.service.get_score_history",
            new_callable=AsyncMock,
            return_value=([], 0),
        ):
            result = await get_history(limit=10, offset=0, db=mock_db, current_user=mock_user)
            assert result.total == 0
            assert result.scores == []

    @pytest.mark.asyncio
    async def test_history_default_pagination(self):
        """GET /score/history respecte la pagination par defaut."""
        from app.modules.credit.router import get_history

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        scores = [_make_score_mock(version=i) for i in range(3)]
        with patch(
            "app.modules.credit.service.get_score_history",
            new_callable=AsyncMock,
            return_value=(scores, 3),
        ):
            result = await get_history(limit=10, offset=0, db=mock_db, current_user=mock_user)
            assert result.total == 3
            assert len(result.scores) == 3
            assert result.limit == 10
            assert result.offset == 0

    @pytest.mark.asyncio
    async def test_history_custom_pagination(self):
        """GET /score/history avec pagination personnalisee."""
        from app.modules.credit.router import get_history

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        scores = [_make_score_mock(version=2)]
        with patch(
            "app.modules.credit.service.get_score_history",
            new_callable=AsyncMock,
            return_value=(scores, 5),
        ):
            result = await get_history(
                limit=1, offset=1, db=mock_db, current_user=mock_user
            )
            assert result.total == 5
            assert len(result.scores) == 1
            assert result.limit == 1
            assert result.offset == 1


class TestGetCertificateEndpoint:
    """Tests du endpoint GET /score/certificate."""

    @pytest.mark.asyncio
    async def test_certificate_404_when_no_score(self):
        """GET /score/certificate retourne 404 si aucun score."""
        from fastapi import HTTPException

        from app.modules.credit.router import get_certificate

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_certificate(db=mock_db, current_user=mock_user)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_certificate_410_when_expired(self):
        """GET /score/certificate retourne 410 si score expire."""
        from fastapi import HTTPException

        from app.modules.credit.router import get_certificate

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.company_name = "Test"

        mock_score = _make_score_mock(expired=True)

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_certificate(db=mock_db, current_user=mock_user)
            assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_certificate_success(self):
        """GET /score/certificate retourne un PDF."""
        from app.modules.credit.router import get_certificate

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.company_name = "EcoVert SARL"

        mock_score = _make_score_mock()

        # Mock pour le profil entreprise
        mock_profile_result = MagicMock()
        mock_profile_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_profile_result)

        with patch(
            "app.modules.credit.service.get_latest_score",
            new_callable=AsyncMock,
            return_value=mock_score,
        ):
            with patch(
                "app.modules.credit.certificate.generate_certificate_pdf",
                return_value=b"%PDF-1.4 test-pdf",
            ):
                result = await get_certificate(db=mock_db, current_user=mock_user)
                assert result.status_code == 200
                assert result.media_type == "application/pdf"


class TestScoreExpiryDetection:
    """Tests de la detection d'expiration du score."""

    def test_not_expired(self):
        """Score non expire."""
        now = datetime.now(tz=timezone.utc)
        valid_until = now + timedelta(days=30)
        assert valid_until > now

    def test_expired(self):
        """Score expire."""
        now = datetime.now(tz=timezone.utc)
        valid_until = now - timedelta(days=1)
        assert valid_until < now
