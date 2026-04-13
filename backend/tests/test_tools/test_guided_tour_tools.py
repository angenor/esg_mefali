"""Tests unitaires pour le tool trigger_guided_tour (feature 019)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.graph.tools.guided_tour_tools import (
    GUIDED_TOUR_TOOLS,
    trigger_guided_tour,
)


class TestTriggerGuidedTour:
    """Tests pour trigger_guided_tour."""

    @pytest.mark.asyncio
    async def test_basic_trigger_returns_marker(self, mock_config):
        """Appel basique retourne le marker SSE avec tour_id."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_esg_results"},
            config=mock_config,
        )

        assert "show_esg_results" in result
        assert "<!--SSE:" in result
        assert "-->".rstrip() in result

        # Extraire et verifier le payload SSE
        start = result.index("<!--SSE:") + len("<!--SSE:")
        end = result.index("-->", start)
        payload = json.loads(result[start:end])

        assert payload["__sse_guided_tour__"] is True
        assert payload["type"] == "guided_tour"
        assert payload["tour_id"] == "show_esg_results"
        assert payload["context"] == {}

    @pytest.mark.asyncio
    async def test_trigger_with_context(self, mock_config):
        """Le context optionnel est inclus dans le marker SSE."""
        ctx = {"total_tco2": 47, "score": 72}
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_carbon_results", "context": ctx},
            config=mock_config,
        )

        start = result.index("<!--SSE:") + len("<!--SSE:")
        end = result.index("-->", start)
        payload = json.loads(result[start:end])

        assert payload["tour_id"] == "show_carbon_results"
        assert payload["context"]["total_tco2"] == 47
        assert payload["context"]["score"] == 72

    @pytest.mark.asyncio
    async def test_trigger_with_none_context(self, mock_config):
        """context=None produit un dict vide dans le payload."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_dashboard_overview", "context": None},
            config=mock_config,
        )

        start = result.index("<!--SSE:") + len("<!--SSE:")
        end = result.index("-->", start)
        payload = json.loads(result[start:end])

        assert payload["context"] == {}

    @pytest.mark.asyncio
    async def test_trigger_missing_config_returns_error(self):
        """Sans config valide, retourne un message d'erreur."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_esg_results"},
            config={"configurable": {}},
        )

        assert "Erreur" in result
        assert "<!--SSE:" not in result

    @pytest.mark.asyncio
    async def test_trigger_logs_tool_call(self, mock_config, mock_db):
        """L'appel est journalise dans tool_call_logs."""
        with patch("app.graph.tools.guided_tour_tools.log_tool_call", new_callable=AsyncMock) as mock_log:
            await trigger_guided_tour.ainvoke(
                {"tour_id": "show_esg_results"},
                config=mock_config,
            )

            mock_log.assert_awaited_once()
            call_kwargs = mock_log.call_args
            assert call_kwargs.kwargs["tool_name"] == "trigger_guided_tour"
            assert call_kwargs.kwargs["tool_args"]["tour_id"] == "show_esg_results"
            assert call_kwargs.kwargs["status"] == "success"

    @pytest.mark.asyncio
    async def test_trigger_log_failure_non_blocking(self, mock_config):
        """Une erreur de journalisation ne bloque pas le tool."""
        with patch(
            "app.graph.tools.guided_tour_tools.log_tool_call",
            new_callable=AsyncMock,
            side_effect=Exception("DB unavailable"),
        ):
            result = await trigger_guided_tour.ainvoke(
                {"tour_id": "show_esg_results"},
                config=mock_config,
            )

            # Le tool retourne quand meme le marker
            assert "<!--SSE:" in result
            assert "show_esg_results" in result

    @pytest.mark.asyncio
    async def test_trigger_with_active_module(self, mock_db, mock_user_id, mock_conversation_id):
        """Le module actif est utilise pour la journalisation."""
        config = {
            "configurable": {
                "db": mock_db,
                "user_id": mock_user_id,
                "conversation_id": mock_conversation_id,
                "active_module": "esg_scoring",
            },
        }

        with patch("app.graph.tools.guided_tour_tools.log_tool_call", new_callable=AsyncMock) as mock_log:
            await trigger_guided_tour.ainvoke(
                {"tour_id": "show_esg_results"},
                config=config,
            )

            assert mock_log.call_args.kwargs["node_name"] == "esg_scoring"

    @pytest.mark.asyncio
    async def test_trigger_returns_user_facing_message(self, mock_config):
        """Le texte retourne contient un message lisible pour le LLM."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_financing_catalog"},
            config=mock_config,
        )

        assert "Parcours guide" in result
        assert "show_financing_catalog" in result


class TestTriggerGuidedTourHardening:
    """Tests pour les garde-fous ajoutes en review (story 6.1)."""

    @pytest.mark.asyncio
    async def test_rejects_empty_tour_id(self, mock_config):
        """Un tour_id vide retourne une erreur sans marker."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": ""},
            config=mock_config,
        )
        assert "Erreur" in result
        assert "tour_id invalide" in result
        assert "<!--SSE:" not in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tour_id",
        [
            "Show_Esg",
            "show-esg",
            "show esg",
            "1_show",
            "show_esg-->",
            "<!--show",
            "show/../esg",
        ],
    )
    async def test_rejects_malformed_tour_id(self, mock_config, tour_id):
        """Un tour_id qui ne respecte pas le regex snake_case est rejete."""
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": tour_id},
            config=mock_config,
        )
        assert "tour_id invalide" in result
        assert "<!--SSE:" not in result

    @pytest.mark.asyncio
    async def test_context_with_html_comment_sequence_escapes_safely(self, mock_config):
        """Une valeur de context contenant `-->` n'ecrase pas le marker SSE."""
        hostile = {"note": "fin -->"}
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_esg_results", "context": hostile},
            config=mock_config,
        )

        # Le marker doit rester extractible (une seule occurrence de `-->` a la fin)
        assert result.count("-->") == 1
        start = result.index("<!--SSE:") + len("<!--SSE:")
        end = result.index("-->", start)
        payload = json.loads(result[start:end])

        # Apres decodage JSON, la valeur originale est restauree
        assert payload["context"]["note"] == "fin -->"

    @pytest.mark.asyncio
    async def test_invalid_uuid_conversation_id_does_not_crash(
        self, mock_db, mock_user_id
    ):
        """Un conversation_id non-UUID ne fait pas crasher le tool."""
        config = {
            "configurable": {
                "db": mock_db,
                "user_id": mock_user_id,
                "conversation_id": "not-a-valid-uuid",
            },
        }
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_esg_results"},
            config=config,
        )
        # Le tool retourne quand meme le marker (fallback conversation_id=None)
        assert "<!--SSE:" in result
        assert "show_esg_results" in result

    @pytest.mark.asyncio
    async def test_non_json_serializable_context_does_not_crash(self, mock_config):
        """Un context contenant des objets non-serialisables est tolere via default=str."""
        from datetime import datetime

        ctx = {"when": datetime(2026, 4, 13, 12, 0, 0)}
        result = await trigger_guided_tour.ainvoke(
            {"tour_id": "show_dashboard_overview", "context": ctx},
            config=mock_config,
        )

        assert "<!--SSE:" in result
        start = result.index("<!--SSE:") + len("<!--SSE:")
        end = result.index("-->", start)
        payload = json.loads(result[start:end])
        # datetime serialise via default=str (isoformat-like)
        assert "2026-04-13" in payload["context"]["when"]


class TestGuidedTourToolsExport:
    """Tests pour l'export GUIDED_TOUR_TOOLS."""

    def test_export_contains_trigger(self):
        """GUIDED_TOUR_TOOLS exporte trigger_guided_tour."""
        assert len(GUIDED_TOUR_TOOLS) == 1
        assert GUIDED_TOUR_TOOLS[0] == trigger_guided_tour

    def test_tool_has_name(self):
        """Le tool a un nom exploitable par LangChain."""
        assert trigger_guided_tour.name == "trigger_guided_tour"

    def test_tool_has_description(self):
        """Le tool a une description pour le LLM."""
        assert "parcours" in trigger_guided_tour.description.lower()
