"""Tests de la gestion d'erreurs du service documents (T055/T057).

Couvre les cas d'erreurs : PDF protégé, OCR échoué, timeout, espace disque,
fichiers manquants, sanitisation.
"""

import uuid
from collections import namedtuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.documents.service import (
    _check_disk_space,
    _sanitize_filename,
    _validate_file_size,
    _validate_mime_type,
    analyze_document,
    extract_text,
)


# ─── Validation ──────────────────────────────────────────────────────


class TestValidation:
    """Tests des fonctions de validation."""

    def test_validate_mime_type_accepts_pdf(self) -> None:
        _validate_mime_type("application/pdf")

    def test_validate_mime_type_accepts_png(self) -> None:
        _validate_mime_type("image/png")

    def test_validate_mime_type_accepts_jpeg(self) -> None:
        _validate_mime_type("image/jpeg")

    def test_validate_mime_type_rejects_unknown(self) -> None:
        with pytest.raises(ValueError, match="Type de fichier non accepté"):
            _validate_mime_type("application/x-executable")

    def test_validate_file_size_accepts_valid(self) -> None:
        _validate_file_size(1024)

    def test_validate_file_size_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="fichier est vide"):
            _validate_file_size(0)

    def test_validate_file_size_rejects_oversized(self) -> None:
        with pytest.raises(ValueError, match="taille maximale"):
            _validate_file_size(11 * 1024 * 1024)


# ─── Sanitisation ────────────────────────────────────────────────────


class TestSanitizeFilename:
    """Tests du nettoyage des noms de fichiers."""

    def test_removes_path_traversal(self) -> None:
        assert ".." not in _sanitize_filename("../../etc/passwd")

    def test_removes_slashes(self) -> None:
        result = _sanitize_filename("path/to/file.pdf")
        assert "/" not in result

    def test_replaces_spaces(self) -> None:
        assert " " not in _sanitize_filename("my file name.pdf")

    def test_removes_dangerous_chars(self) -> None:
        result = _sanitize_filename('file<>:"|?*.pdf')
        assert "<" not in result
        assert ">" not in result

    def test_truncates_long_names(self) -> None:
        long_name = "a" * 300 + ".pdf"
        result = _sanitize_filename(long_name)
        assert len(result) <= 255

    def test_returns_default_for_empty(self) -> None:
        assert _sanitize_filename("") == "document"


# ─── Espace disque ───────────────────────────────────────────────────


class TestDiskSpace:
    """Tests de la vérification d'espace disque."""

    def test_check_disk_space_raises_on_low_space(self) -> None:
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        with patch(
            "app.modules.documents.service.shutil.disk_usage",
            return_value=DiskUsage(100, 99, 1),
        ):
            with pytest.raises(ValueError, match="Espace disque insuffisant"):
                _check_disk_space()

    def test_check_disk_space_passes_with_enough_space(self) -> None:
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        with patch(
            "app.modules.documents.service.shutil.disk_usage",
            return_value=DiskUsage(1_000_000_000, 500_000_000, 500_000_000),
        ):
            _check_disk_space()  # Ne doit pas lever d'exception

    def test_check_disk_space_handles_os_error(self) -> None:
        with patch(
            "app.modules.documents.service.shutil.disk_usage",
            side_effect=OSError("No such device"),
        ):
            _check_disk_space()  # Ne doit pas lever d'exception, juste logger


# ─── Extraction de texte ─────────────────────────────────────────────


class TestExtractText:
    """Tests de l'extraction de texte avec gestion d'erreurs."""

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_mime(self) -> None:
        with pytest.raises(ValueError, match="Type MIME non supporté"):
            await extract_text("/tmp/file.txt", "text/plain")

    @pytest.mark.asyncio
    async def test_extract_pdf_password_protected(self) -> None:
        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_doc.close = MagicMock()

        with patch("fitz.open", return_value=mock_doc):
            with pytest.raises(ValueError, match="protege par un mot de passe"):
                await extract_text("/tmp/test.pdf", "application/pdf")

    @pytest.mark.asyncio
    async def test_extract_pdf_corrupt_file(self) -> None:
        with patch("fitz.open", side_effect=Exception("Cannot open")):
            with pytest.raises(ValueError, match="corrompu ou protege"):
                await extract_text("/tmp/broken.pdf", "application/pdf")

    @pytest.mark.asyncio
    async def test_extract_ocr_tesseract_not_found(self) -> None:
        import pytesseract

        with patch("PIL.Image.open"), patch(
            "pytesseract.image_to_string",
            side_effect=pytesseract.TesseractNotFoundError(),
        ):
            with pytest.raises(ValueError, match="Tesseract OCR"):
                await extract_text("/tmp/photo.png", "image/png")

    @pytest.mark.asyncio
    async def test_extract_docx(self) -> None:
        with patch("docx2txt.process", return_value="Contenu Word"):
            result = await extract_text(
                "/tmp/doc.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        assert result == "Contenu Word"

    @pytest.mark.asyncio
    async def test_extract_xlsx(self) -> None:
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [("Colonne A", "Colonne B")]

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Feuille1"]
        mock_wb.__getitem__ = MagicMock(return_value=mock_ws)
        mock_wb.close = MagicMock()

        with patch("openpyxl.load_workbook", return_value=mock_wb):
            result = await extract_text(
                "/tmp/data.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        assert "Feuille1" in result
        assert "Colonne A" in result


# ─── Analyse avec timeout ────────────────────────────────────────────


class TestAnalyzeDocument:
    """Tests de l'analyse de document avec gestion d'erreurs."""

    @pytest.mark.asyncio
    async def test_analyze_document_file_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_doc = MagicMock()
        mock_doc.id = uuid.uuid4()
        mock_doc.storage_path = "uploads/nonexistent/file.pdf"
        mock_doc.original_filename = "file.pdf"
        mock_doc.status = "uploaded"

        with pytest.raises(FileNotFoundError, match="introuvable"):
            await analyze_document(mock_db, mock_doc)

    @pytest.mark.asyncio
    async def test_analyze_document_sets_error_status_on_failure(self) -> None:
        mock_db = AsyncMock()
        mock_doc = MagicMock()
        mock_doc.id = uuid.uuid4()
        mock_doc.storage_path = "uploads/nonexistent/file.pdf"
        mock_doc.original_filename = "file.pdf"
        mock_doc.status = "uploaded"

        with pytest.raises(FileNotFoundError):
            await analyze_document(mock_db, mock_doc)

        # Le statut doit être passé à error
        assert mock_doc.status.value == "error" or mock_doc.status == "error"
