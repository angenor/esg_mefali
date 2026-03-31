"""Tests unitaires de la chaîne d'analyse LangChain (T016).

Valide que la chaîne d'analyse produit un résumé structuré
à partir du texte extrait d'un document.
Écrits AVANT l'implémentation (TDD RED phase).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.documents.schemas import DocumentAnalysisOutput, DocumentTypeEnum


# ─── Tests chaîne d'analyse ─────────────────────────────────────────


class TestAnalysisChain:
    """Tests de la chaîne d'analyse documentaire."""

    @pytest.mark.asyncio
    async def test_analyze_financial_report(self) -> None:
        """Un bilan financier produit un résumé structuré avec données chiffrées."""
        from app.chains.analysis import analyze_document_text

        mock_output = DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.bilan_financier,
            summary="Bilan financier 2024 de la société EcoVert.",
            key_findings=[
                "Chiffre d'affaires de 500M XOF",
                "Résultat net de 25M XOF",
            ],
            structured_data={
                "chiffre_affaires": 500_000_000,
                "resultat_net": 25_000_000,
            },
            esg_relevant_info={
                "environmental": ["Investissement énergies renouvelables"],
                "social": ["40% femmes"],
                "governance": ["Rapports financiers publiés"],
            },
        )

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await analyze_document_text(
                text="Bilan financier exercice 2024...",
                document_type_hint=None,
            )

        assert result.document_type == DocumentTypeEnum.bilan_financier
        assert "EcoVert" in result.summary
        assert len(result.key_findings) >= 2
        assert result.structured_data.get("chiffre_affaires") == 500_000_000

    @pytest.mark.asyncio
    async def test_analyze_returns_structured_output(self) -> None:
        """L'analyse retourne toujours un DocumentAnalysisOutput valide."""
        from app.chains.analysis import analyze_document_text

        mock_output = DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.autre,
            summary="Document générique.",
            key_findings=["Point clé 1"],
            structured_data={},
        )

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await analyze_document_text(
                text="Contenu quelconque...",
                document_type_hint=None,
            )

        assert isinstance(result, DocumentAnalysisOutput)
        assert result.summary is not None
        assert isinstance(result.key_findings, list)

    @pytest.mark.asyncio
    async def test_analyze_handles_llm_failure(self) -> None:
        """En cas d'échec LLM, retourne un résultat dégradé."""
        from app.chains.analysis import analyze_document_text

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            side_effect=Exception("LLM timeout"),
        ):
            result = await analyze_document_text(
                text="Contenu...",
                document_type_hint=None,
            )

        assert result.document_type == DocumentTypeEnum.autre
        assert "erreur" in result.summary.lower() or "impossible" in result.summary.lower()

    @pytest.mark.asyncio
    async def test_analyze_with_type_hint(self) -> None:
        """Un type de document fourni est utilisé comme indice."""
        from app.chains.analysis import analyze_document_text

        mock_output = DocumentAnalysisOutput(
            document_type=DocumentTypeEnum.facture,
            summary="Facture du fournisseur XYZ.",
            key_findings=["Montant: 150 000 XOF"],
            structured_data={"montant_total": 150_000},
        )

        with patch(
            "app.chains.analysis._run_analysis_chain",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await analyze_document_text(
                text="Facture n°2024-001...",
                document_type_hint="facture",
            )

        assert result.document_type == DocumentTypeEnum.facture
