"""Tests unitaires pour les tools credit vert."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.credit_tools import (
    CREDIT_TOOLS,
    generate_credit_certificate,
    generate_credit_score,
    get_credit_score,
)


def _make_credit_score(**overrides):
    """Creer un mock de CreditScore."""
    score = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "combined_score": 72,
        "solvability_score": 68,
        "green_impact_score": 76,
        "risk_level": "moyen",
        "version": 1,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(score, key, value)
    return score


class TestGenerateCreditScore:
    """Tests pour generate_credit_score."""

    @pytest.mark.asyncio
    @patch("app.modules.credit.service.generate_credit_score", new_callable=AsyncMock)
    async def test_generate_success(self, mock_generate, mock_config):
        """Generation du score retourne le resultat."""
        score = _make_credit_score()
        mock_generate.return_value = score

        result = await generate_credit_score.ainvoke({}, config=mock_config)

        assert "72" in result
        mock_generate.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "app.modules.credit.service.generate_credit_score",
        new_callable=AsyncMock,
        side_effect=Exception("Insufficient data"),
    )
    async def test_generate_handles_error(self, mock_generate, mock_config):
        """Erreur retourne un message lisible."""
        result = await generate_credit_score.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestGenerateCreditScoreIdempotenceMonthly:
    """BUG-V6-004 / V6-009 : garde runtime idempotence mensuelle."""

    @pytest.mark.asyncio
    async def test_rejects_recent_duplicate(self, mock_config):
        """Score genere il y a 5 jours -> ERREUR, pas de nouvelle generation."""
        recent = _make_credit_score(version=1, combined_score=65)
        recent.generated_at = datetime.now(timezone.utc) - timedelta(days=5)

        with (
            patch(
                "app.modules.credit.service.get_latest_score",
                new_callable=AsyncMock,
                return_value=recent,
            ),
            patch(
                "app.modules.credit.service.generate_credit_score",
                new_callable=AsyncMock,
            ) as mock_gen,
        ):
            result = await generate_credit_score.ainvoke({}, config=mock_config)

        assert "ERREUR" in result
        assert "version 1" in result
        assert "65" in result
        assert "get_credit_score" in result
        # Critique : aucune regeneration BDD.
        mock_gen.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_succeeds_after_30_days(self, mock_config):
        """Score genere il y a 60 jours -> nouvelle generation autorisee."""
        old = _make_credit_score(version=1, combined_score=50)
        old.generated_at = datetime.now(timezone.utc) - timedelta(days=60)

        new_score = _make_credit_score(version=2, combined_score=72)

        with (
            patch(
                "app.modules.credit.service.get_latest_score",
                new_callable=AsyncMock,
                return_value=old,
            ),
            patch(
                "app.modules.credit.service.generate_credit_score",
                new_callable=AsyncMock,
                return_value=new_score,
            ) as mock_gen,
        ):
            result = await generate_credit_score.ainvoke({}, config=mock_config)

        assert "ERREUR" not in result
        assert "72" in result
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_proceeds_when_no_previous_score(self, mock_config):
        """Aucun score anterieur -> generation autorisee (1ere fois)."""
        new_score = _make_credit_score(version=1, combined_score=58)

        with (
            patch(
                "app.modules.credit.service.get_latest_score",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.modules.credit.service.generate_credit_score",
                new_callable=AsyncMock,
                return_value=new_score,
            ) as mock_gen,
        ):
            result = await generate_credit_score.ainvoke({}, config=mock_config)

        assert "ERREUR" not in result
        assert "58" in result
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_error_message_invites_get_credit_score(self, mock_config):
        """Le message d'erreur DOIT mentionner get_credit_score (LLM doit savoir lire)."""
        recent = _make_credit_score(version=3, combined_score=80)
        recent.generated_at = datetime.now(timezone.utc) - timedelta(days=1)

        with (
            patch(
                "app.modules.credit.service.get_latest_score",
                new_callable=AsyncMock,
                return_value=recent,
            ),
            patch(
                "app.modules.credit.service.generate_credit_score",
                new_callable=AsyncMock,
            ),
        ):
            result = await generate_credit_score.ainvoke({}, config=mock_config)

        # Message exploitable par le LLM : il doit savoir quoi faire ensuite.
        assert "get_credit_score" in result
        assert "30" in result  # Mention du delai de regeneration.


class TestGetCreditScore:
    """Tests pour get_credit_score."""

    @pytest.mark.asyncio
    @patch("app.modules.credit.service.get_latest_score", new_callable=AsyncMock)
    async def test_score_found(self, mock_get, mock_config):
        """Score existant retourne les details."""
        score = _make_credit_score()
        mock_get.return_value = score

        result = await get_credit_score.ainvoke({}, config=mock_config)

        assert "72" in result
        mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.credit.service.get_latest_score", new_callable=AsyncMock)
    async def test_no_score(self, mock_get, mock_config):
        """Pas de score retourne un message."""
        mock_get.return_value = None

        result = await get_credit_score.ainvoke({}, config=mock_config)

        assert "Aucun" in result or "aucun" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.credit.service.get_latest_score",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_get_handles_error(self, mock_get, mock_config):
        """Erreur retourne un message lisible."""
        result = await get_credit_score.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestGenerateCreditCertificate:
    """Tests pour generate_credit_certificate."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.credit_tools._generate_certificate", new_callable=AsyncMock)
    async def test_certificate_success(self, mock_gen, mock_config):
        """Generation du certificat retourne l'URL."""
        mock_gen.return_value = "/uploads/certificates/attestation.pdf"

        result = await generate_credit_certificate.ainvoke({}, config=mock_config)

        assert "pdf" in result.lower() or "attestation" in result.lower() or "certificat" in result.lower()

    @pytest.mark.asyncio
    @patch(
        "app.graph.tools.credit_tools._generate_certificate",
        new_callable=AsyncMock,
        side_effect=Exception("No score"),
    )
    async def test_certificate_handles_error(self, mock_gen, mock_config):
        """Erreur retourne un message lisible."""
        result = await generate_credit_certificate.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestCreditToolsExport:
    """Tests pour l'export du module."""

    def test_tools_list_count(self):
        """CREDIT_TOOLS contient 3 tools."""
        assert len(CREDIT_TOOLS) == 3

    def test_tool_names(self):
        """Les tools ont les bons noms."""
        names = {t.name for t in CREDIT_TOOLS}
        assert names == {"generate_credit_score", "get_credit_score", "generate_credit_certificate"}

    def test_tools_have_french_descriptions(self):
        """Les descriptions des tools sont en francais."""
        for t in CREDIT_TOOLS:
            assert any(
                word in t.description.lower()
                for word in ["credit", "score", "attestation", "certificat", "calculer", "generer", "consulter"]
            ), f"Description manque de termes francais : {t.description}"
