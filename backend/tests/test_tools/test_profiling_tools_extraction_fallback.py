"""Tests integration V8-AXE1 : merge regex fallback dans update_company_profile.

Couvre les 4 cas critiques :
- LLM-PARTIEL : LLM extrait 1/5 champ, regex comble 3 autres.
- LLM-OK : LLM extrait tous les champs, regex non declenchee.
- LLM-NULL + texte vide : pas de regex, comportement nominal.
- LLM-PRIORITY : LLM passe sector="services" sur texte "agriculture", LLM gagne.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.runnables import RunnableConfig

from app.graph.tools.profiling_tools import update_company_profile
from app.modules.company.schemas import CompletionResponse, FieldStatus


def _make_profile(**overrides):
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
        "country": None,
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


def _make_completion(identity_pct: float = 50.0, overall_pct: float = 25.0) -> CompletionResponse:
    return CompletionResponse(
        identity_completion=identity_pct,
        esg_completion=0.0,
        overall_completion=overall_pct,
        identity_fields=FieldStatus(filled=[], missing=[]),
        esg_fields=FieldStatus(filled=[], missing=[]),
    )


def _config_with_message(mock_db, user_id, message: str | None) -> RunnableConfig:
    """Build a RunnableConfig with optional last_user_message in configurable."""
    configurable: dict = {
        "db": mock_db,
        "user_id": user_id,
        "conversation_id": uuid.UUID("00000000-0000-0000-0000-000000000099"),
        "thread_id": "00000000-0000-0000-0000-000000000099",
    }
    if message is not None:
        configurable["last_user_message"] = message
    return {"configurable": configurable}


class TestRegexFallbackTriggered:
    """Cas LLM-PARTIEL et LLM-TOUS-NULL : regex comble les trous."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_llm_partial_regex_fills_missing(
        self, mock_get, mock_update, mock_compute, mock_db, mock_user_id,
    ):
        """LLM extrait employee_count seul ; regex comble company_name/sector/country."""
        profile = _make_profile()
        mock_get.return_value = profile
        mock_update.return_value = (profile, [
            {"field": "company_name", "value": "AgriVert Sarl", "label": "Nom de l'entreprise"},
            {"field": "sector", "value": "agriculture", "label": "Secteur"},
            {"field": "employee_count", "value": 15, "label": "Nombre d'employés"},
            {"field": "country", "value": "Sénégal", "label": "Pays"},
        ], [])
        mock_compute.return_value = _make_completion(identity_pct=50.0)

        config = _config_with_message(
            mock_db, mock_user_id,
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal",
        )

        # LLM ne passe que employee_count (BUG-V7.1-001 reproduit).
        result = await update_company_profile.ainvoke(
            {"employee_count": 15}, config=config,
        )

        # Verifier que update_profile a recu les 4 champs (regex a comble).
        mock_update.assert_awaited_once()
        sent_updates = mock_update.await_args.args[2]
        assert sent_updates.company_name == "AgriVert Sarl"
        assert sent_updates.sector == "agriculture"
        assert sent_updates.employee_count == 15
        assert sent_updates.country == "Sénégal"
        assert "Profil mis à jour" in result

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_llm_all_null_regex_extracts_all(
        self, mock_get, mock_update, mock_compute, mock_db, mock_user_id,
    ):
        """LLM passe tous args=null (BUG-V7-001) ; regex extrait 4/5 champs."""
        profile = _make_profile()
        mock_get.return_value = profile
        mock_update.return_value = (profile, [
            {"field": "company_name", "value": "AgriVert Sarl", "label": "Nom"},
        ], [])
        mock_compute.return_value = _make_completion()

        config = _config_with_message(
            mock_db, mock_user_id,
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal",
        )

        result = await update_company_profile.ainvoke({}, config=config)

        # Sans regex, le tool aurait retourne "Aucun champ fourni".
        assert "Aucun champ fourni" not in result
        mock_update.assert_awaited_once()
        sent_updates = mock_update.await_args.args[2]
        assert sent_updates.company_name == "AgriVert Sarl"
        assert sent_updates.sector == "agriculture"
        assert sent_updates.employee_count == 15
        assert sent_updates.country == "Sénégal"


class TestRegexFallbackInactive:
    """Cas LLM-OK et texte absent : regex pas declenchee ou inutile."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.extract_profile_from_text")
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_llm_complete_no_regex_call(
        self, mock_get, mock_update, mock_compute, mock_extract, mock_db, mock_user_id,
    ):
        """4 champs LLM => 1 seul null parmi les 5 cibles => pas de regex."""
        profile = _make_profile()
        mock_get.return_value = profile
        mock_update.return_value = (profile, [
            {"field": "company_name", "value": "AgriVert Sarl", "label": "Nom"},
        ], [])
        mock_compute.return_value = _make_completion()

        config = _config_with_message(
            mock_db, mock_user_id,
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal",
        )

        await update_company_profile.ainvoke(
            {
                "company_name": "AgriVert Sarl",
                "sector": "agriculture",
                "employee_count": 15,
                "country": "Sénégal",
                # city reste null (1 seul null < seuil 2) => pas de regex
            },
            config=config,
        )

        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.extract_profile_from_text")
    async def test_no_last_user_message_no_regex(
        self, mock_extract, mock_db, mock_user_id,
    ):
        """LLM tous null + last_user_message absent => message nominal."""
        config = _config_with_message(mock_db, mock_user_id, None)

        result = await update_company_profile.ainvoke({}, config=config)

        assert "Aucun champ fourni" in result
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.extract_profile_from_text")
    async def test_empty_last_user_message_no_regex(
        self, mock_extract, mock_db, mock_user_id,
    ):
        """LLM tous null + last_user_message vide/whitespace => regex non appelee."""
        config = _config_with_message(mock_db, mock_user_id, "   ")

        result = await update_company_profile.ainvoke({}, config=config)

        assert "Aucun champ fourni" in result
        mock_extract.assert_not_called()


class TestLLMWhitespaceCountedAsNull:
    """Scenario WHITESPACE-LLM (spec I/O Matrix) + review V8-AXE1 MOYEN-1.

    Le LLM passant des chaines vides ou whitespace doit etre traite comme nul
    pour le seuil de fallback. Sans cela, un LLM bogue qui renvoie 5 chaines
    vides echappait au filet de securite regex.
    """

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_whitespace_llm_triggers_regex_fallback(
        self, mock_get, mock_update, mock_compute, mock_db, mock_user_id,
    ):
        """LLM passe company_name='   ' (whitespace) => regex doit toujours combler."""
        profile = _make_profile()
        mock_get.return_value = profile
        mock_update.return_value = (profile, [
            {"field": "company_name", "value": "AgriVert Sarl", "label": "Nom"},
        ], [])
        mock_compute.return_value = _make_completion()

        config = _config_with_message(
            mock_db, mock_user_id,
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal",
        )

        # LLM passe une chaine whitespace (assimile a null par le seuil).
        # 4 autres champs effectivement null => seuil franchi (>=2).
        await update_company_profile.ainvoke(
            {"company_name": "   "},
            config=config,
        )

        # Le tool a quand meme appele update_profile avec les 4 champs regex.
        mock_update.assert_awaited_once()
        sent_updates = mock_update.await_args.args[2]
        assert sent_updates.company_name == "AgriVert Sarl"
        assert sent_updates.sector == "agriculture"
        assert sent_updates.employee_count == 15
        assert sent_updates.country == "Sénégal"


class TestLLMPriorityOverRegex:
    """Le LLM gagne toujours quand il fournit une valeur non-null."""

    @pytest.mark.asyncio
    @patch("app.graph.tools.profiling_tools.compute_completion")
    @patch("app.modules.company.service.update_profile", new_callable=AsyncMock)
    @patch("app.modules.company.service.get_or_create_profile", new_callable=AsyncMock)
    async def test_llm_sector_wins_over_regex(
        self, mock_get, mock_update, mock_compute, mock_db, mock_user_id,
    ):
        """LLM passe sector="services" sur texte "agriculture" => LLM gagne."""
        profile = _make_profile()
        mock_get.return_value = profile
        mock_update.return_value = (profile, [
            {"field": "sector", "value": "services", "label": "Secteur"},
        ], [])
        mock_compute.return_value = _make_completion()

        config = _config_with_message(
            mock_db, mock_user_id,
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal",
        )

        await update_company_profile.ainvoke(
            {"sector": "services"},  # LLM extrait mal mais avec une valeur non-null
            config=config,
        )

        sent_updates = mock_update.await_args.args[2]
        # LLM gagne sur le champ qu'il a fourni.
        assert sent_updates.sector == "services"
        # Mais le regex comble les autres trous (≥2 nulls => active).
        assert sent_updates.company_name == "AgriVert Sarl"
        assert sent_updates.country == "Sénégal"
