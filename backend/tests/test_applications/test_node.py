"""Tests pour le application_node LangGraph (US9 — T055)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.prompts.application import build_application_prompt


# =====================================================================
# TESTS build_application_prompt
# =====================================================================


class TestBuildApplicationPrompt:
    """Tests pour la construction du prompt application."""

    def test_default_prompt(self) -> None:
        """Le prompt par defaut contient les placeholders."""
        prompt = build_application_prompt()
        assert "Aucun profil disponible." in prompt
        assert "Aucun dossier en cours." in prompt

    def test_prompt_with_context(self) -> None:
        """Le prompt contient le contexte fourni."""
        prompt = build_application_prompt(
            company_context="PME AgriVert, Abidjan",
            application_context="Dossier SUNREF via SIB, 3/5 sections generees",
        )
        assert "PME AgriVert, Abidjan" in prompt
        assert "Dossier SUNREF via SIB" in prompt

    def test_prompt_contains_visual_instructions(self) -> None:
        """Le prompt contient les instructions pour les blocs visuels."""
        prompt = build_application_prompt()
        assert "```mermaid" in prompt
        assert "```progress" in prompt
        assert "```table" in prompt
        assert "```timeline" in prompt
        assert "```gauge" in prompt

    def test_prompt_mentions_target_types(self) -> None:
        """Le prompt mentionne les 4 types de destinataires."""
        prompt = build_application_prompt()
        assert "fund_direct" in prompt
        assert "intermediary_bank" in prompt
        assert "intermediary_agency" in prompt
        assert "intermediary_developer" in prompt


# =====================================================================
# TESTS application_node
# =====================================================================


class TestApplicationNode:
    """Tests pour le noeud application_node."""

    @pytest.mark.asyncio
    async def test_application_node_returns_messages(self) -> None:
        """Le node retourne des messages et application_data."""
        from app.graph.nodes import application_node

        mock_response = MagicMock()
        mock_response.content = "Votre dossier SUNREF est en bonne voie !"

        state = {
            "messages": [MagicMock(content="Quel est l'etat de mon dossier ?")],
            "user_profile": {"sector": "agriculture", "company_name": "AgriVert"},
            "application_data": {
                "application_id": "test-id",
                "fund_name": "SUNREF",
                "target_type": "intermediary_bank",
                "status": "in_progress",
                "sections_total": 6,
                "sections_generated": 3,
            },
        }

        with patch("app.graph.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = await application_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Votre dossier SUNREF est en bonne voie !"

    @pytest.mark.asyncio
    async def test_application_node_without_application_data(self) -> None:
        """Le node fonctionne meme sans donnees de dossier."""
        from app.graph.nodes import application_node

        mock_response = MagicMock()
        mock_response.content = "Vous n'avez pas encore de dossier en cours."

        state = {
            "messages": [MagicMock(content="Mon dossier de candidature")],
            "user_profile": None,
            "application_data": None,
        }

        with patch("app.graph.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = await application_node(state)

        assert "messages" in result

    @pytest.mark.asyncio
    async def test_application_node_builds_context_from_data(self) -> None:
        """Le node utilise application_data pour construire le contexte."""
        from app.graph.nodes import application_node

        mock_response = MagicMock()
        mock_response.content = "Reponse"

        state = {
            "messages": [MagicMock(content="Mon dossier")],
            "user_profile": {"company_name": "TestCorp"},
            "application_data": {
                "application_id": "abc-123",
                "fund_name": "FEM",
                "target_type": "intermediary_agency",
                "status": "review",
                "sections_total": 5,
                "sections_generated": 5,
                "intermediary_name": "PNUD",
                "checklist_complete": 4,
                "checklist_total": 6,
            },
        }

        captured_messages = None

        async def capture_invoke(messages):
            nonlocal captured_messages
            captured_messages = messages
            return mock_response

        with patch("app.graph.nodes.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = capture_invoke
            mock_get_llm.return_value = mock_llm

            await application_node(state)

        # Verifier que le system prompt contient les infos du dossier
        assert captured_messages is not None
        system_content = captured_messages[0].content
        assert "FEM" in system_content
        assert "intermediary_agency" in system_content
        assert "PNUD" in system_content
