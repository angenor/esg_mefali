"""Tests de la génération de résumé de conversation (US2)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.chains.summarization import generate_summary


class TestGenerateSummary:
    """Tests de la chaîne de résumé de conversation."""

    @pytest.mark.asyncio
    async def test_generates_summary_from_messages(self) -> None:
        """Un résumé est généré à partir des messages d'un thread."""
        messages_text = (
            "Utilisateur: Je fais du recyclage de plastique à Abidjan\n"
            "Assistant: Excellent ! Le recyclage est un secteur clé pour l'ESG...\n"
            "Utilisateur: Quels fonds verts sont disponibles ?\n"
            "Assistant: Pour le recyclage en Côte d'Ivoire, je recommande..."
        )

        mock_response = AsyncMock()
        mock_response.content = (
            "Discussion sur une entreprise de recyclage de plastique à Abidjan. "
            "Exploration des fonds verts disponibles pour le secteur en Côte d'Ivoire."
        )

        with patch(
            "app.chains.summarization._run_summarization",
            new_callable=AsyncMock,
            return_value=mock_response.content,
        ):
            result = await generate_summary(messages_text)

        assert "recyclage" in result
        assert "Abidjan" in result or "Côte d'Ivoire" in result

    @pytest.mark.asyncio
    async def test_empty_messages_returns_empty(self) -> None:
        """Des messages vides retournent un résumé vide."""
        result = await generate_summary("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_error_returns_empty_string(self) -> None:
        """En cas d'erreur LLM, retourne une chaîne vide."""
        with patch(
            "app.chains.summarization._run_summarization",
            new_callable=AsyncMock,
            side_effect=Exception("LLM error"),
        ):
            result = await generate_summary("Some messages here")

        assert result == ""
