"""Tests supplémentaires pour nodes.py (couverture T057).

Couvre analyze_document_for_chat, document_node avec ESG,
et les cas limites du routeur.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


# ─── analyze_document_for_chat ────────────────────────────────────────


class TestAnalyzeDocumentForChat:
    """Tests de la fonction analyze_document_for_chat."""

    @pytest.mark.asyncio
    async def test_returns_document_and_analysis(self) -> None:
        from app.graph.nodes import analyze_document_for_chat

        mock_doc = MagicMock()
        mock_doc.analysis = MagicMock()
        mock_doc.analysis.summary = "Résumé test"

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.core.database.async_session_factory",
            return_value=mock_db,
        ), patch(
            "app.modules.documents.service.get_document",
            new_callable=AsyncMock,
            return_value=mock_doc,
        ):
            doc, analysis = await analyze_document_for_chat(
                str(uuid.uuid4()), str(uuid.uuid4()),
            )

        assert analysis.summary == "Résumé test"

    @pytest.mark.asyncio
    async def test_triggers_analysis_when_missing(self) -> None:
        from app.graph.nodes import analyze_document_for_chat

        mock_analysis = MagicMock()
        mock_analysis.summary = "Analyse lancée"

        mock_doc = MagicMock()
        mock_doc.analysis = None

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.core.database.async_session_factory",
            return_value=mock_db,
        ), patch(
            "app.modules.documents.service.get_document",
            new_callable=AsyncMock,
            return_value=mock_doc,
        ), patch(
            "app.modules.documents.service.analyze_document",
            new_callable=AsyncMock,
            return_value=mock_analysis,
        ):
            doc, analysis = await analyze_document_for_chat(
                str(uuid.uuid4()), str(uuid.uuid4()),
            )

        assert analysis.summary == "Analyse lancée"

    @pytest.mark.asyncio
    async def test_raises_on_document_not_found(self) -> None:
        from app.graph.nodes import analyze_document_for_chat

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.core.database.async_session_factory",
            return_value=mock_db,
        ), patch(
            "app.modules.documents.service.get_document",
            new_callable=AsyncMock,
            return_value=None,
        ), pytest.raises(ValueError, match="introuvable"):
            await analyze_document_for_chat(
                str(uuid.uuid4()), str(uuid.uuid4()),
            )


# ─── document_node ESG details ───────────────────────────────────────


class TestDocumentNodeESGDetails:
    """Tests du document_node avec données ESG riches."""

    @pytest.mark.asyncio
    async def test_includes_esg_in_summary(self) -> None:
        from app.graph.nodes import document_node

        mock_analysis = MagicMock()
        mock_analysis.summary = "Bilan de l'entreprise"
        mock_analysis.key_findings = ["Point 1", "Point 2"]
        mock_analysis.esg_relevant_info = MagicMock()
        mock_analysis.esg_relevant_info.model_dump.return_value = {
            "environmental": ["Réduction CO2 de 20%"],
            "social": ["50 emplois créés"],
            "governance": [],
        }
        mock_analysis.document_type = MagicMock()
        mock_analysis.document_type.value = "rapport_activite"

        mock_doc = MagicMock()

        state = {
            "messages": [HumanMessage(content="Analyse")],
            "document_upload": {
                "document_id": str(uuid.uuid4()),
                "filename": "rapport.pdf",
                "user_id": str(uuid.uuid4()),
            },
            "document_analysis_summary": None,
        }

        with patch(
            "app.graph.nodes.analyze_document_for_chat",
            new_callable=AsyncMock,
            return_value=(mock_doc, mock_analysis),
        ):
            result = await document_node(state)

        summary = result["document_analysis_summary"]
        assert "ESG" in summary
        assert "Réduction CO2" in summary
        assert "50 emplois" in summary

    @pytest.mark.asyncio
    async def test_no_document_returns_none(self) -> None:
        from app.graph.nodes import document_node

        state = {
            "messages": [HumanMessage(content="Bonjour")],
            "document_upload": None,
            "document_analysis_summary": None,
        }

        result = await document_node(state)
        assert result["document_analysis_summary"] is None


# ─── generate_title ──────────────────────────────────────────────────


class TestGenerateTitle:
    """Tests de la génération de titres."""

    @pytest.mark.asyncio
    async def test_generate_title_success(self) -> None:
        from app.graph.nodes import generate_title

        mock_response = MagicMock()
        mock_response.content = "Discussion ESG"

        with patch("app.graph.nodes.get_llm") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_factory.return_value = mock_llm

            title = await generate_title("Bonjour", "Comment puis-je vous aider?")

        assert title == "Discussion ESG"

    @pytest.mark.asyncio
    async def test_generate_title_fallback_on_error(self) -> None:
        from app.graph.nodes import generate_title

        with patch("app.graph.nodes.get_llm") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("API error"))
            mock_llm_factory.return_value = mock_llm

            title = await generate_title("Bonjour", "Aide")

        assert title == "Conversation"

    @pytest.mark.asyncio
    async def test_generate_title_truncates_long_title(self) -> None:
        from app.graph.nodes import generate_title

        mock_response = MagicMock()
        mock_response.content = "A" * 100

        with patch("app.graph.nodes.get_llm") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_factory.return_value = mock_llm

            title = await generate_title("Long message", "Long response")

        assert len(title) <= 50
