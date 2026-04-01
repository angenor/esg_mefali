"""Tests unitaires pour les tools document."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.document_tools import (
    DOCUMENT_TOOLS,
    analyze_uploaded_document,
    get_document_analysis,
    list_user_documents,
)


def _make_document(**overrides):
    """Creer un mock de Document."""
    doc = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "filename": "rapport-esg-2025.pdf",
        "document_type": "esg_report",
        "file_size": 1024000,
        "status": "analyzed",
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(doc, key, value)
    return doc


def _make_analysis(**overrides):
    """Creer un mock de DocumentAnalysis."""
    analysis = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "document_type": "esg_report",
        "summary": "Rapport ESG annuel de l'entreprise EcoAfrik.",
        "key_findings": ["Score E: 72", "Score S: 65", "Score G: 80"],
        "confidence_score": 0.85,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(analysis, key, value)
    return analysis


class TestAnalyzeUploadedDocument:
    """Tests pour analyze_uploaded_document."""

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.analyze_document", new_callable=AsyncMock)
    @patch("app.modules.documents.service.get_document", new_callable=AsyncMock)
    async def test_analyze_success(self, mock_get_doc, mock_analyze, mock_config):
        """Analyse d'un document retourne le resume."""
        doc = _make_document()
        analysis = _make_analysis()
        mock_get_doc.return_value = doc
        mock_analyze.return_value = analysis

        result = await analyze_uploaded_document.ainvoke(
            {"document_id": str(doc.id)},
            config=mock_config,
        )

        assert "rapport" in result.lower() or "analyse" in result.lower() or "EcoAfrik" in result
        mock_analyze.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.get_document", new_callable=AsyncMock)
    async def test_document_not_found(self, mock_get_doc, mock_config):
        """Document introuvable retourne un message d'erreur."""
        mock_get_doc.return_value = None

        result = await analyze_uploaded_document.ainvoke(
            {"document_id": str(uuid.uuid4())},
            config=mock_config,
        )

        assert "introuvable" in result.lower() or "Erreur" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.documents.service.get_document",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_analyze_handles_error(self, mock_get_doc, mock_config):
        """Erreur retourne un message lisible."""
        result = await analyze_uploaded_document.ainvoke(
            {"document_id": str(uuid.uuid4())},
            config=mock_config,
        )

        assert "Erreur" in result


class TestGetDocumentAnalysis:
    """Tests pour get_document_analysis."""

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.get_document", new_callable=AsyncMock)
    async def test_analysis_found(self, mock_get_doc, mock_config):
        """Document avec analyse retourne le resume."""
        doc = _make_document()
        doc.analysis = _make_analysis()
        mock_get_doc.return_value = doc

        result = await get_document_analysis.ainvoke(
            {"document_id": str(doc.id)},
            config=mock_config,
        )

        assert "rapport" in result.lower() or "EcoAfrik" in result

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.get_document", new_callable=AsyncMock)
    async def test_no_analysis(self, mock_get_doc, mock_config):
        """Document sans analyse retourne un message."""
        doc = _make_document()
        doc.analysis = None
        mock_get_doc.return_value = doc

        result = await get_document_analysis.ainvoke(
            {"document_id": str(doc.id)},
            config=mock_config,
        )

        assert "pas encore" in result.lower() or "aucune" in result.lower() or "analyse" in result.lower()


class TestListUserDocuments:
    """Tests pour list_user_documents."""

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.list_documents", new_callable=AsyncMock)
    async def test_documents_found(self, mock_list, mock_config):
        """Documents trouves retourne la liste."""
        mock_list.return_value = ([_make_document(), _make_document()], 2)

        result = await list_user_documents.ainvoke({}, config=mock_config)

        assert "2" in result or "document" in result.lower()
        mock_list.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.documents.service.list_documents", new_callable=AsyncMock)
    async def test_no_documents(self, mock_list, mock_config):
        """Aucun document retourne un message."""
        mock_list.return_value = ([], 0)

        result = await list_user_documents.ainvoke({}, config=mock_config)

        assert "Aucun" in result or "aucun" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.documents.service.list_documents",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_list_handles_error(self, mock_list, mock_config):
        """Erreur retourne un message lisible."""
        result = await list_user_documents.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestDocumentToolsExport:
    """Tests pour l'export du module."""

    def test_tools_list_count(self):
        """DOCUMENT_TOOLS contient 3 tools."""
        assert len(DOCUMENT_TOOLS) == 3

    def test_tool_names(self):
        """Les tools ont les bons noms."""
        names = {t.name for t in DOCUMENT_TOOLS}
        assert names == {"analyze_uploaded_document", "get_document_analysis", "list_user_documents"}

    def test_tools_have_french_descriptions(self):
        """Les descriptions des tools sont en francais."""
        for t in DOCUMENT_TOOLS:
            assert any(
                word in t.description.lower()
                for word in ["document", "analyse", "lister", "consulter"]
            ), f"Description manque de termes francais : {t.description}"
