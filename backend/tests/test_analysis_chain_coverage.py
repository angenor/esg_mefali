"""Tests supplémentaires pour la chaîne d'analyse (couverture T057).

Couvre le fallback dégradé et le formatage du prompt.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chains.analysis import ANALYSIS_PROMPT, analyze_document_text
from app.modules.documents.schemas import (
    DocumentAnalysisOutput,
    DocumentTypeEnum,
    ESGRelevantInfo,
)


class TestAnalyzeDocumentText:
    """Tests de la fonction publique analyze_document_text."""

    @pytest.mark.asyncio
    async def test_returns_degraded_output_on_llm_error(self) -> None:
        """En cas d'erreur LLM, retourne un résultat dégradé."""
        with patch(
            "app.chains.analysis._run_analysis_chain",
            side_effect=Exception("LLM timeout"),
        ):
            result = await analyze_document_text("Texte quelconque")

        assert result.document_type == DocumentTypeEnum.autre
        assert "Analyse impossible" in result.summary
        assert result.key_findings == []

    @pytest.mark.asyncio
    async def test_returns_analysis_output_on_success(self) -> None:
        """En cas de succès, retourne la sortie structurée."""
        expected = DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.bilan_financier,
            summary="Bilan financier 2024 de la société.",
            key_findings=["CA: 500M XOF", "Résultat net: 50M XOF"],
            structured_data={"chiffre_affaires": "500M XOF"},
            esg_relevant_info=ESGRelevantInfo(
                environmental=["Réduction émissions de 10%"],
            ),
        )

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await analyze_document_text("Bilan financier...")

        assert result.document_type == DocumentTypeEnum.bilan_financier
        assert "Bilan financier" in result.summary

    @pytest.mark.asyncio
    async def test_passes_type_hint_to_chain(self) -> None:
        """Le type hint est transmis à la chaîne."""
        expected = DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.facture,
            summary="Facture",
            key_findings=[],
            structured_data={},
            esg_relevant_info=ESGRelevantInfo(),
        )

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_chain:
            await analyze_document_text("Facture...", document_type_hint="facture")
            mock_chain.assert_called_once_with("Facture...", "facture")


class TestAnalysisPrompt:
    """Tests de la structure du prompt."""

    def test_prompt_contains_esg_instructions(self) -> None:
        assert "ESG" in ANALYSIS_PROMPT
        assert "Environmental" in ANALYSIS_PROMPT
        assert "Social" in ANALYSIS_PROMPT
        assert "Governance" in ANALYSIS_PROMPT

    def test_prompt_mentions_uemoa(self) -> None:
        assert "UEMOA" in ANALYSIS_PROMPT

    def test_prompt_has_format_placeholders(self) -> None:
        assert "{type_hint}" in ANALYSIS_PROMPT
        assert "{document_text}" in ANALYSIS_PROMPT
