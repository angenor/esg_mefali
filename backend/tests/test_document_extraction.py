"""Tests unitaires de l'extraction de texte par type de fichier (T015).

Valide l'extraction de texte depuis PDF, images, Word et Excel.
Écrits AVANT l'implémentation (TDD RED phase).
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


# ─── Tests extraction PDF textuel ────────────────────────────────────


class TestPDFExtraction:
    """Tests d'extraction de texte depuis des PDF."""

    @pytest.mark.asyncio
    async def test_extract_text_from_textual_pdf(self) -> None:
        """Un PDF textuel retourne du texte via PyMuPDF."""
        from app.modules.documents.service import extract_text

        # Créer un PDF minimal avec PyMuPDF
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Rapport annuel ESG 2024")
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            f.flush()
            text = await extract_text(f.name, "application/pdf")

        os.unlink(f.name)
        assert "Rapport annuel ESG 2024" in text
        assert len(text) > 10

    @pytest.mark.asyncio
    async def test_extract_text_fallback_ocr_for_scanned_pdf(self) -> None:
        """Un PDF scanné (texte vide via PyMuPDF) déclenche l'OCR."""
        from app.modules.documents.service import extract_text

        # Simuler un PDF sans texte extractible
        with patch("app.modules.documents.service._extract_text_pymupdf", return_value=""):
            with patch(
                "app.modules.documents.service._extract_text_ocr",
                return_value="Texte OCR reconnu",
            ):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(b"%PDF-1.4 fake scanned")
                    f.flush()
                    text = await extract_text(f.name, "application/pdf")

                os.unlink(f.name)
                assert "Texte OCR reconnu" in text


# ─── Tests extraction images ────────────────────────────────────────


class TestImageExtraction:
    """Tests d'extraction OCR depuis les images."""

    @pytest.mark.asyncio
    async def test_extract_text_from_png(self) -> None:
        """Une image PNG passe par l'OCR Tesseract."""
        from app.modules.documents.service import extract_text

        with patch(
            "app.modules.documents.service._extract_text_ocr",
            return_value="Contenu OCR depuis image",
        ):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(b"fake png content")
                f.flush()
                text = await extract_text(f.name, "image/png")

            os.unlink(f.name)
            assert "Contenu OCR depuis image" in text

    @pytest.mark.asyncio
    async def test_extract_text_from_jpeg(self) -> None:
        """Une image JPEG passe par l'OCR Tesseract."""
        from app.modules.documents.service import extract_text

        with patch(
            "app.modules.documents.service._extract_text_ocr",
            return_value="Contenu OCR JPEG",
        ):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(b"fake jpeg content")
                f.flush()
                text = await extract_text(f.name, "image/jpeg")

            os.unlink(f.name)
            assert "Contenu OCR JPEG" in text


# ─── Tests OCR bilingue FR+EN (story 9.4) ──────────────────────────


def _get_pytesseract_lang_arg(mock_ocr: MagicMock) -> str | None:
    # Recupere `lang` passe a pytesseract.image_to_string (kwargs ou 2e arg positionnel).
    call = mock_ocr.call_args
    if "lang" in call.kwargs:
        return call.kwargs["lang"]
    if len(call.args) >= 2:
        return call.args[1]
    return None


class TestOCRBilingual:
    """Tests verrouillant le contrat OCR bilingue (fra+eng).

    Detecte tout refactor qui reverterait silencieusement a lang="fra"
    et casserait l'extraction des documents de bailleurs anglophones
    (GCF, FEM, BAD — coeur de la value proposition Mefali).

    Source : spec-audits/index.md §P1 #8 (reclasse P2->P1 le 2026-04-16).
    """

    def test_ocr_passes_fra_plus_eng_to_pytesseract(self) -> None:
        """AC1 + AC6 — `lang="fra+eng"` est bien transmis a pytesseract.

        Test de contrat : si un futur refactor repasse a lang="fra",
        ce test echoue et empeche la regression metier critique.
        """
        from app.modules.documents.service import _extract_text_ocr

        with patch("PIL.Image.open"), patch(
            "pytesseract.image_to_string", return_value="texte mock"
        ) as mock_ocr:
            _extract_text_ocr("/tmp/fake.png")

        assert mock_ocr.called, "pytesseract.image_to_string non appele"
        lang = _get_pytesseract_lang_arg(mock_ocr)
        assert lang == "fra+eng", (
            f"lang='fra+eng' attendu, recu lang={lang!r}. "
            "Ne jamais revenir a lang='fra' — casse les documents GCF/FEM/BAD."
        )

    def test_ocr_french_document_unchanged(self) -> None:
        """AC1 — Extraction d'un document 100 % francais reste fonctionnelle.

        Non-regression : le passage a fra+eng ne degrade pas la
        reconnaissance des accents et mots francais.
        """
        from app.modules.documents.service import _extract_text_ocr

        french_text = (
            "Rapport ESG 2024 — Gouvernance d'entreprise, émissions de "
            "gaz à effet de serre, résilience climatique. Signé à Dakar."
        )
        with patch("PIL.Image.open"), patch(
            "pytesseract.image_to_string", return_value=french_text
        ):
            result = _extract_text_ocr("/tmp/rapport_fr.png")

        assert "gouvernance" in result.lower()
        assert "émissions" in result.lower(), (
            "Les accents francais doivent etre preserves dans la chaine extraite."
        )

    def test_ocr_english_document_extracts_keywords(self) -> None:
        """AC2 — Extraction d'un document GCF/FEM anglais retrouve les
        mots-cles ESG anglais (climate, emissions, governance, etc.).
        """
        from app.modules.documents.service import _extract_text_ocr

        gcf_extract = (
            "Green Climate Fund — Funding Proposal Template. "
            "Climate mitigation and adaptation. Governance arrangements. "
            "Sustainability risk framework. Project emissions baseline."
        )
        with patch("PIL.Image.open"), patch(
            "pytesseract.image_to_string", return_value=gcf_extract
        ) as mock_ocr:
            result = _extract_text_ocr("/tmp/gcf_proposal.png")

        # Contrat bilingue (AC6) verifie meme sur document 100% anglais.
        assert _get_pytesseract_lang_arg(mock_ocr) == "fra+eng", (
            "Meme pour un document 100% anglais, lang='fra+eng' doit etre passe "
            "a pytesseract (sinon regression du contrat bilingue)."
        )

        keywords = {
            "climate", "emissions", "governance",
            "sustainability", "mitigation", "adaptation",
        }
        found = {kw for kw in keywords if kw in result.lower()}
        assert len(found) >= 4, (
            f"Au moins 4 mots-cles ESG anglais attendus sur {len(keywords)}, "
            f"trouves : {found}"
        )

    def test_ocr_mixed_fr_en_document_extracts_both(self) -> None:
        """AC3 — PDF bilingue (RFP GCF partiellement traduit) : les 2
        langues sont capturees dans une seule extraction.
        """
        from app.modules.documents.service import _extract_text_ocr

        mixed_extract = (
            "Executive Summary — Climate mitigation project. "
            "Page 2: Résumé exécutif — Projet d'atténuation des émissions. "
            "Gouvernance conforme aux exigences BCEAO."
        )
        with patch("PIL.Image.open"), patch(
            "pytesseract.image_to_string", return_value=mixed_extract
        ) as mock_ocr:
            result = _extract_text_ocr("/tmp/mixed_rfp.png")

        # Contrat bilingue (AC6) verifie meme sur document mixte.
        assert _get_pytesseract_lang_arg(mock_ocr) == "fra+eng", (
            "Document mixte : lang='fra+eng' doit etre passe a pytesseract."
        )

        french_hits = [
            word for word in ("gouvernance", "atténuation", "émissions")
            if word in result.lower()
        ]
        english_hits = [
            word for word in ("climate", "mitigation", "summary")
            if word in result.lower()
        ]

        assert french_hits, f"Aucun mot francais detecte : {result!r}"
        assert english_hits, f"Aucun mot anglais detecte : {result!r}"


# ─── Tests extraction Word ──────────────────────────────────────────


class TestWordExtraction:
    """Tests d'extraction de texte depuis des fichiers Word."""

    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self) -> None:
        """Un fichier Word retourne du texte via docx2txt."""
        from app.modules.documents.service import extract_text

        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with patch(
            "app.modules.documents.service._extract_text_docx",
            return_value="Contenu du document Word",
        ):
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                f.write(b"fake docx")
                f.flush()
                text = await extract_text(f.name, mime)

            os.unlink(f.name)
            assert "Contenu du document Word" in text


# ─── Tests extraction Excel ─────────────────────────────────────────


class TestExcelExtraction:
    """Tests d'extraction de texte depuis des fichiers Excel."""

    @pytest.mark.asyncio
    async def test_extract_text_from_xlsx(self) -> None:
        """Un fichier Excel retourne le contenu des cellules."""
        from app.modules.documents.service import extract_text

        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        with patch(
            "app.modules.documents.service._extract_text_xlsx",
            return_value="Cellule A1: Chiffre d'affaires\nCellule B1: 500000000",
        ):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                f.write(b"fake xlsx")
                f.flush()
                text = await extract_text(f.name, mime)

            os.unlink(f.name)
            assert "Chiffre d'affaires" in text


# ─── Tests gestion d'erreurs ────────────────────────────────────────


class TestExtractionErrors:
    """Tests de la gestion d'erreurs d'extraction."""

    @pytest.mark.asyncio
    async def test_unsupported_mime_type_raises(self) -> None:
        """Un MIME type non supporté lève une erreur."""
        from app.modules.documents.service import extract_text

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"texte brut")
            f.flush()
            with pytest.raises(ValueError, match="non supporté"):
                await extract_text(f.name, "text/plain")

        os.unlink(f.name)
