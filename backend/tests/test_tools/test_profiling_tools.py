"""Tests unitaires pour les tools de profilage entreprise."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.profiling_tools import (
    PROFILING_TOOLS,
    get_company_profile,
    update_company_profile,
)
from app.modules.company.schemas import CompletionResponse, FieldStatus


def _make_profile(**overrides):
    """Créer un mock de CompanyProfile avec des valeurs par défaut."""
    profile = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "company_name": None,
        "sector": None,
        "sub_sector": None,
        "employee_count": None,
        "annual_revenue_xof": None,
        "city": None,
        "country": "Côte d'Ivoire",
        "year_founded": None,
        "has_waste_management": None,
        "has_energy_policy": None,
        "has_gender_policy": None,
        "has_training_program": None,
        "has_financial_transparency": None,
        "governance_structure": None,
        "environmental_practices": None,
        "social_practices": None,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(profile, key, value)
    return profile


def _make_completion(
    identity_pct: float = 12.5,
    esg_pct: float = 0.0,
    overall_pct: float = 6.2,
    identity_filled: list | None = None,
    identity_missing: list | None = None,
    esg_filled: list | None = None,
    esg_missing: list | None = None,
) -> CompletionResponse:
    """Créer un CompletionResponse pour les tests."""
    return CompletionResponse(
        identity_completion=identity_pct,
        esg_completion=esg_pct,
        overall_completion=overall_pct,
        identity_fields=FieldStatus(
            filled=identity_filled or ["country"],
            missing=identity_missing or [
                "company_name", "sector", "sub_sector",
                "employee_count", "annual_revenue_xof",
                "year_founded", "city",
            ],
        ),
        esg_fields=FieldStatus(
            filled=esg_filled or [],
            missing=esg_missing or [
                "has_waste_management", "has_energy_policy",
                "has_gender_policy", "has_training_program",
                "has_financial_transparency", "governance_structure",
                "environmental_practices", "social_practices",
            ],
        ),
    )


class TestUpdateCompanyProfile:
    """Tests pour update_company_profile."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_update_single_field(
        self,
        mock_get_or_create,
        mock_update,
        mock_compute,
        mock_config,
    ):
        """Mise à jour d'un seul champ retourne le champ modifié et la complétion."""
        profile = _make_profile(company_name="Solaris")
        mock_get_or_create.return_value = profile
        # Story 9.5 : update_profile retourne un 3-uplet (profile, changed, skipped).
        mock_update.return_value = (
            profile,
            [{"field": "company_name", "value": "Solaris", "label": "Nom de l'entreprise"}],
            [],
        )
        mock_compute.return_value = _make_completion(
            identity_pct=25.0, overall_pct=12.5,
            identity_filled=["country", "company_name"],
            identity_missing=["sector", "sub_sector", "employee_count", "annual_revenue_xof", "year_founded", "city"],
        )

        result = await update_company_profile.ainvoke(
            {"company_name": "Solaris"},
            config=mock_config,
        )

        assert "Solaris" in result
        assert "Nom de l'entreprise" in result
        assert "identité 25.0%" in result
        assert "global 12.5%" in result
        mock_get_or_create.assert_awaited_once()
        mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_update_multiple_fields(
        self,
        mock_get_or_create,
        mock_update,
        mock_compute,
        mock_config,
    ):
        """Mise à jour de plusieurs champs retourne tous les champs modifiés."""
        profile = _make_profile(company_name="EcoAfrik", sector="agriculture", city="Abidjan")
        mock_get_or_create.return_value = profile
        # Story 9.5 : update_profile retourne un 3-uplet (profile, changed, skipped).
        mock_update.return_value = (
            profile,
            [
                {"field": "company_name", "value": "EcoAfrik", "label": "Nom de l'entreprise"},
                {"field": "sector", "value": "agriculture", "label": "Secteur"},
                {"field": "city", "value": "Abidjan", "label": "Ville"},
            ],
            [],
        )
        mock_compute.return_value = _make_completion(identity_pct=50.0, overall_pct=25.0)

        result = await update_company_profile.ainvoke(
            {"company_name": "EcoAfrik", "sector": "agriculture", "city": "Abidjan"},
            config=mock_config,
        )

        assert "EcoAfrik" in result
        assert "Secteur" in result
        assert "Ville" in result
        assert "Profil mis à jour avec succès" in result

    @pytest.mark.asyncio
    async def test_update_no_fields_provided(self, mock_config):
        """Aucun champ fourni retourne un message explicite."""
        result = await update_company_profile.ainvoke({}, config=mock_config)
        assert "Aucun champ fourni" in result

    @pytest.mark.asyncio
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_update_no_changes(
        self,
        mock_get_or_create,
        mock_update,
        mock_config,
    ):
        """Valeurs identiques retourne un message 'aucun changement'."""
        profile = _make_profile(company_name="Solaris")
        mock_get_or_create.return_value = profile
        # Story 9.5 : update_profile retourne un 3-uplet (profile, changed, skipped).
        mock_update.return_value = (profile, [], [])

        result = await update_company_profile.ainvoke(
            {"company_name": "Solaris"},
            config=mock_config,
        )

        assert "Aucun changement" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.company.service.get_or_create_profile",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_update_handles_error(
        self,
        mock_get_or_create,
        mock_config,
    ):
        """Erreur DB retourne un message d'erreur lisible."""
        result = await update_company_profile.ainvoke(
            {"company_name": "Test"},
            config=mock_config,
        )

        assert "Erreur" in result
        assert "DB error" in result


class TestGetCompanyProfile:
    """Tests pour get_company_profile."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.get_profile", new_callable=AsyncMock)
    async def test_existing_profile(
        self,
        mock_get_profile,
        mock_compute,
        mock_config,
    ):
        """Profil existant retourne le résumé et la complétion."""
        profile = _make_profile(company_name="Solaris", country="Côte d'Ivoire")
        mock_get_profile.return_value = profile
        mock_compute.return_value = _make_completion(
            identity_pct=25.0,
            esg_pct=0.0,
            overall_pct=12.5,
            identity_filled=["company_name", "country"],
            identity_missing=["sector", "sub_sector", "employee_count", "annual_revenue_xof", "year_founded", "city"],
            esg_filled=[],
            esg_missing=[
                "has_waste_management", "has_energy_policy",
                "has_gender_policy", "has_training_program",
                "has_financial_transparency", "governance_structure",
                "environmental_practices", "social_practices",
            ],
        )

        result = await get_company_profile.ainvoke({}, config=mock_config)

        assert "Solaris" in result
        assert "identité 25.0%" in result
        assert "global 12.5%" in result
        assert "Champs manquants" in result

    @pytest.mark.asyncio
    @patch("app.modules.company.service.get_profile", new_callable=AsyncMock)
    async def test_no_profile(
        self,
        mock_get_profile,
        mock_config,
    ):
        """Profil inexistant retourne un message invitant à partager des infos."""
        mock_get_profile.return_value = None

        result = await get_company_profile.ainvoke({}, config=mock_config)

        assert "Aucun profil" in result
        assert "Partagez des informations" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.get_profile", new_callable=AsyncMock)
    async def test_profile_missing_fields_listed(
        self,
        mock_get_profile,
        mock_compute,
        mock_config,
    ):
        """Les champs manquants sont listés avec leurs labels français."""
        profile = _make_profile(company_name="Test")
        mock_get_profile.return_value = profile
        mock_compute.return_value = _make_completion(
            identity_filled=["company_name"],
            identity_missing=["sector", "city"],
            esg_filled=[],
            esg_missing=["has_waste_management"],
        )

        result = await get_company_profile.ainvoke({}, config=mock_config)

        assert "Secteur" in result
        assert "Ville" in result
        assert "Gestion des déchets" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.company.service.get_profile",
        new_callable=AsyncMock,
        side_effect=Exception("Connection lost"),
    )
    async def test_get_handles_error(
        self,
        mock_get_profile,
        mock_config,
    ):
        """Erreur retourne un message d'erreur lisible."""
        result = await get_company_profile.ainvoke({}, config=mock_config)

        assert "Erreur" in result
        assert "Connection lost" in result


class TestProfilingToolsExport:
    """Tests pour l'export du module."""

    def test_profiling_tools_list(self):
        """PROFILING_TOOLS contient les deux tools."""
        assert len(PROFILING_TOOLS) == 2

    def test_tool_names(self):
        """Les tools ont les bons noms."""
        names = {t.name for t in PROFILING_TOOLS}
        assert names == {"update_company_profile", "get_company_profile"}

    def test_tools_have_french_descriptions(self):
        """Les descriptions des tools sont en français."""
        for t in PROFILING_TOOLS:
            # Les docstrings françaises contiennent des accents ou mots français
            assert any(
                word in t.description.lower()
                for word in ["profil", "entreprise", "outil", "utilise"]
            ), f"Description manque de termes français : {t.description}"
