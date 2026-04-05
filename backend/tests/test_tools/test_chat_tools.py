"""Tests unitaires pour les tools chat (lecture seule)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.chat_tools import (
    CHAT_TOOLS,
    get_carbon_summary_chat,
    get_company_profile_chat,
    get_esg_assessment_chat,
    get_user_dashboard_summary,
)


class TestGetUserDashboardSummary:
    """Tests pour get_user_dashboard_summary."""

    @pytest.mark.asyncio
    @patch("app.modules.dashboard.service.get_dashboard_summary", new_callable=AsyncMock)
    async def test_dashboard_summary_success(self, mock_get_summary, mock_config):
        """Resume dashboard retourne les donnees formatees."""
        mock_get_summary.return_value = {
            "esg": {"overall_score": 65, "status": "completed"},
            "carbon": {"total_emissions_tco2e": 12.5, "year": 2025},
            "credit": {"combined_score": 72, "risk_level": "moyen"},
            "financing": {"matched_funds": 3, "interested_funds": 1},
        }

        result = await get_user_dashboard_summary.ainvoke({}, config=mock_config)

        assert "65" in result or "ESG" in result
        assert "12.5" in result or "carbone" in result.lower()
        mock_get_summary.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.dashboard.service.get_dashboard_summary", new_callable=AsyncMock)
    async def test_dashboard_empty(self, mock_get_summary, mock_config):
        """Dashboard vide retourne un message informatif."""
        mock_get_summary.return_value = {
            "esg": None,
            "carbon": None,
            "credit": None,
            "financing": {"matched_funds": 0, "interested_funds": 0},
        }

        result = await get_user_dashboard_summary.ainvoke({}, config=mock_config)

        assert isinstance(result, str)

    @pytest.mark.asyncio
    @patch(
        "app.modules.dashboard.service.get_dashboard_summary",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_dashboard_handles_error(self, mock_get_summary, mock_config):
        """Erreur retourne un message lisible."""
        result = await get_user_dashboard_summary.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestGetCompanyProfileChat:
    """Tests pour get_company_profile_chat."""

    @pytest.mark.asyncio
    @patch("app.modules.company.service.get_profile", new_callable=AsyncMock)
    async def test_profile_exists(self, mock_get_profile, mock_config):
        """Profil existant retourne les informations."""
        profile = MagicMock()
        profile.company_name = "EcoAfrik"
        profile.sector = MagicMock(value="agriculture")
        profile.city = "Abidjan"
        profile.country = "Cote d'Ivoire"
        profile.employee_count = 25
        mock_get_profile.return_value = profile

        result = await get_company_profile_chat.ainvoke({}, config=mock_config)

        assert "EcoAfrik" in result
        mock_get_profile.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.company.service.get_profile", new_callable=AsyncMock)
    async def test_no_profile(self, mock_get_profile, mock_config):
        """Pas de profil retourne un message."""
        mock_get_profile.return_value = None

        result = await get_company_profile_chat.ainvoke({}, config=mock_config)

        assert "Aucun" in result or "aucun" in result


class TestGetEsgAssessmentChat:
    """Tests pour get_esg_assessment_chat."""

    @pytest.mark.asyncio
    @patch("app.modules.esg.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_assessment_found(self, mock_get, mock_config):
        """Evaluation ESG trouvee retourne le resume."""
        assessment = MagicMock()
        assessment.id = uuid.uuid4()
        assessment.status = MagicMock(value="completed")
        assessment.overall_score = 72
        assessment.environment_score = 68
        assessment.social_score = 75
        assessment.governance_score = 73
        assessment.sector = "agriculture"
        mock_get.return_value = assessment

        result = await get_esg_assessment_chat.ainvoke({}, config=mock_config)

        assert "72" in result
        mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.esg.service.get_latest_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_no_assessment(self, mock_resumable, mock_latest, mock_config):
        """Pas d'evaluation retourne un message."""
        mock_resumable.return_value = None
        mock_latest.return_value = None

        result = await get_esg_assessment_chat.ainvoke({}, config=mock_config)

        assert "Aucune" in result or "aucune" in result

    @pytest.mark.asyncio
    @patch("app.modules.esg.service.get_latest_assessment", new_callable=AsyncMock)
    @patch("app.modules.esg.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_completed_assessment_found_via_latest(self, mock_resumable, mock_latest, mock_config):
        """Evaluation completed trouvee via get_latest_assessment."""
        mock_resumable.return_value = None
        assessment = MagicMock()
        assessment.id = uuid.uuid4()
        assessment.status = MagicMock(value="completed")
        assessment.overall_score = 63
        assessment.environment_score = 59
        assessment.social_score = 70
        assessment.governance_score = 60
        assessment.sector = "recyclage"
        mock_latest.return_value = assessment

        result = await get_esg_assessment_chat.ainvoke({}, config=mock_config)

        assert "63" in result
        mock_resumable.assert_awaited_once()
        mock_latest.assert_awaited_once()


class TestGetCarbonSummaryChat:
    """Tests pour get_carbon_summary_chat."""

    @pytest.mark.asyncio
    @patch("app.modules.carbon.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_carbon_found(self, mock_get, mock_config):
        """Bilan carbone trouve retourne le resume."""
        assessment = MagicMock()
        assessment.id = uuid.uuid4()
        assessment.year = 2025
        assessment.status = MagicMock(value="completed")
        assessment.total_emissions_tco2e = 45.3
        assessment.sector = "agriculture"
        mock_get.return_value = assessment

        result = await get_carbon_summary_chat.ainvoke({}, config=mock_config)

        assert "45.3" in result or "2025" in result
        mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.carbon.service.get_resumable_assessment", new_callable=AsyncMock)
    async def test_no_carbon(self, mock_get, mock_config):
        """Pas de bilan retourne un message."""
        mock_get.return_value = None

        result = await get_carbon_summary_chat.ainvoke({}, config=mock_config)

        assert "Aucun" in result or "aucun" in result


class TestChatToolsExport:
    """Tests pour l'export du module."""

    def test_tools_list_count(self):
        """CHAT_TOOLS contient 4 tools."""
        assert len(CHAT_TOOLS) == 4

    def test_tool_names(self):
        """Les tools ont les bons noms."""
        names = {t.name for t in CHAT_TOOLS}
        assert names == {
            "get_user_dashboard_summary",
            "get_company_profile_chat",
            "get_esg_assessment_chat",
            "get_carbon_summary_chat",
        }

    def test_tools_have_french_descriptions(self):
        """Les descriptions des tools sont en francais."""
        for t in CHAT_TOOLS:
            assert any(
                word in t.description.lower()
                for word in ["consulter", "obtenir", "resume", "profil", "bilan", "evaluation", "tableau"]
            ), f"Description manque de termes francais : {t.description}"
