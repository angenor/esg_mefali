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
