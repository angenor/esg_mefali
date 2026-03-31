"""Tests unitaires du service d'upload documents (T014).

Valide la validation MIME, la taille, le stockage local et la sanitisation.
Écrits AVANT l'implémentation (TDD RED phase).
"""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.schemas import DocumentStatusEnum


# ─── Constantes ──────────────────────────────────────────────────────

ALLOWED_MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Tests validation MIME ──────────────────────────────────────────


class TestUploadValidation:
    """Tests de validation des fichiers uploadés."""

    @pytest.mark.asyncio
    async def test_reject_invalid_mime_type(self, db_session: AsyncSession) -> None:
        """Un fichier avec un MIME type non autorisé est rejeté."""
        from app.modules.documents.service import upload_document

        user_id = uuid.uuid4()
        with pytest.raises(ValueError, match="Type de fichier non accepté"):
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="malware.exe",
                content=b"fake content",
                content_type="application/x-msdownload",
                file_size=100,
            )

    @pytest.mark.asyncio
    async def test_reject_oversized_file(self, db_session: AsyncSession) -> None:
        """Un fichier dépassant 10 MB est rejeté."""
        from app.modules.documents.service import upload_document

        user_id = uuid.uuid4()
        with pytest.raises(ValueError, match="taille maximale"):
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="huge.pdf",
                content=b"x" * (MAX_FILE_SIZE + 1),
                content_type="application/pdf",
                file_size=MAX_FILE_SIZE + 1,
            )

    @pytest.mark.asyncio
    async def test_accept_valid_pdf(self, db_session: AsyncSession) -> None:
        """Un PDF valide est accepté et stocké."""
        from app.modules.documents.service import upload_document

        user_id = uuid.uuid4()
        content = b"%PDF-1.4 fake content"

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = f"uploads/{user_id}/doc_id/test.pdf"
            doc = await upload_document(
                db=db_session,
                user_id=user_id,
                filename="rapport_2024.pdf",
                content=content,
                content_type="application/pdf",
                file_size=len(content),
            )

        assert doc.status.value == DocumentStatusEnum.uploaded.value
        assert doc.mime_type == "application/pdf"
        assert doc.original_filename == "rapport_2024.pdf"
        assert doc.user_id == user_id

    @pytest.mark.asyncio
    async def test_sanitize_filename(self, db_session: AsyncSession) -> None:
        """Les caractères spéciaux dans les noms de fichier sont sanitisés."""
        from app.modules.documents.service import _sanitize_filename

        assert _sanitize_filename("../../etc/passwd") == "etcpasswd"
        assert _sanitize_filename("fichier avec espaces.pdf") == "fichier_avec_espaces.pdf"
        assert _sanitize_filename("rapport<>2024.pdf") == "rapport2024.pdf"
        assert _sanitize_filename("normal.pdf") == "normal.pdf"

    @pytest.mark.asyncio
    async def test_accept_all_valid_mime_types(self, db_session: AsyncSession) -> None:
        """Tous les types MIME autorisés sont acceptés."""
        from app.modules.documents.service import _validate_mime_type

        for mime in ALLOWED_MIMES:
            _validate_mime_type(mime)  # Ne doit pas lever d'exception

    @pytest.mark.asyncio
    async def test_reject_empty_file(self, db_session: AsyncSession) -> None:
        """Un fichier vide est rejeté."""
        from app.modules.documents.service import upload_document

        user_id = uuid.uuid4()
        with pytest.raises(ValueError, match="vide"):
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="empty.pdf",
                content=b"",
                content_type="application/pdf",
                file_size=0,
            )
