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


# ─── Tests quota cumulé par utilisateur (spec 004 §3.2) ──────────────


async def _fill_user_quota(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    bytes_total: int = 0,
    docs_count: int = 0,
) -> None:
    """Pré-remplir rapidement le quota d'un utilisateur via insertion directe.

    Bien plus rapide que N appels à ``upload_document`` (pas d'écriture disque,
    pas de validation MIME, pas d'embeddings).
    """
    from app.models.document import Document, DocumentStatus

    if docs_count <= 0:
        return

    per_doc_size = bytes_total // docs_count if docs_count else 0

    documents = [
        Document(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=f"fixture_{i}.pdf",
            original_filename=f"fixture_{i}.pdf",
            mime_type="application/pdf",
            file_size=per_doc_size,
            storage_path=f"uploads/{user_id}/fixture_{i}/fixture_{i}.pdf",
            status=DocumentStatus.uploaded,
        )
        for i in range(docs_count)
    ]

    db.add_all(documents)
    await db.flush()


class TestQuota:
    """Tests du quota cumulé de stockage par utilisateur (spec 004 §3.2)."""

    @pytest.mark.asyncio
    async def test_quota_allows_under_limit(
        self, db_session: AsyncSession
    ) -> None:
        """AC1 — 10 uploads de 9 MB (total 90 MB) sont tous acceptés."""
        from app.modules.documents.service import (
            check_user_storage_quota,
            upload_document,
        )

        user_id = uuid.uuid4()
        nine_mb = 9 * 1024 * 1024

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = f"uploads/{user_id}/doc/test.pdf"
            for idx in range(10):
                await upload_document(
                    db=db_session,
                    user_id=user_id,
                    filename=f"doc_{idx}.pdf",
                    content=b"%PDF-1.4 content" + bytes(str(idx), "utf-8"),
                    content_type="application/pdf",
                    file_size=nine_mb,
                )

        bytes_used, docs_count = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used == 10 * nine_mb
        assert docs_count == 10

    @pytest.mark.asyncio
    async def test_quota_rejects_over_bytes_limit(
        self, db_session: AsyncSession
    ) -> None:
        """AC2 — 95 MB utilisés + upload 10 MB → QuotaExceededError avec message MB.

        Note : on teste à 95 MB + 10 MB (= 105 MB > 100 MB) plutôt que 90 + 15
        parce que MAX_FILE_SIZE=10 MB rejetterait un fichier de 15 MB AVANT
        le check quota.
        """
        from app.modules.documents.service import (
            QuotaExceededError,
            upload_document,
        )

        user_id = uuid.uuid4()
        # 10 docs totalisant 95 MB (sous les limites 50 docs / 100 MB)
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=95 * 1024 * 1024,
            docs_count=10,
        )

        with pytest.raises(QuotaExceededError) as exc_info:
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="big.pdf",
                content=b"%PDF content",
                content_type="application/pdf",
                file_size=10 * 1024 * 1024,  # 10 MB = 95 + 10 = 105 > 100
            )

        message = str(exc_info.value)
        assert "Quota atteint" in message
        # Review P9 — assertion stricte sur le format complet « 95/100 MB »
        # (plutôt que substrings isolés qui matcheraient « 1950 » ou « 9500 »).
        assert "95/100 MB" in message

    @pytest.mark.asyncio
    async def test_quota_rejects_over_docs_count_limit(
        self, db_session: AsyncSession
    ) -> None:
        """AC3 — 50 documents exacts + upload 1 Ko → QuotaExceededError message documents."""
        from app.modules.documents.service import (
            QuotaExceededError,
            upload_document,
        )

        user_id = uuid.uuid4()
        # 50 documents de 1024 bytes chacun = 50 KB (loin sous 100 MB)
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=50 * 1024,
            docs_count=50,
        )

        with pytest.raises(QuotaExceededError) as exc_info:
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="tiny.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=1024,
            )

        message = str(exc_info.value)
        assert "Quota atteint" in message
        # Review P9 — format exact « 50/50 documents ».
        assert "50/50 documents" in message

    @pytest.mark.asyncio
    async def test_quota_releases_on_delete(
        self, db_session: AsyncSession
    ) -> None:
        """AC4 — atteindre le quota, supprimer 20 MB, ré-uploader OK.

        Review P10 — fidélité au scénario AC4 (« 100 MB → delete 20 MB → 80 MB »)
        via `_fill_user_quota(100 MB, 5 docs)` qui produit 20 MB par doc.
        Le « ré-upload 15 MB » du spec est ramené à 9 MB car MAX_FILE_SIZE=10 MB.
        """
        from app.models.document import Document
        from app.modules.documents.service import (
            check_user_storage_quota,
            delete_document,
            upload_document,
        )

        user_id = uuid.uuid4()
        # 5 documents de 20 MB = 100 MB (quota bytes atteint) — fidèle à AC4.
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=100 * 1024 * 1024,
            docs_count=5,
        )

        bytes_used, docs_count = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used == 100 * 1024 * 1024
        assert docs_count == 5

        # Supprimer un document de 20 MB (conforme AC4).
        from sqlalchemy import select

        result = await db_session.execute(
            select(Document).where(Document.user_id == user_id).limit(1)
        )
        doc = result.scalar_one()
        assert doc.file_size == 20 * 1024 * 1024  # garantit la fidélité du fixture
        with patch(
            "app.modules.documents.service._delete_file_from_disk"
        ):
            await delete_document(db_session, doc)

        # AC4 : après delete, bytes_used = 100 - 20 = 80 MB exactement.
        bytes_used, docs_count = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used == 80 * 1024 * 1024
        assert docs_count == 4

        # AC4 : nouvel upload accepté (spec dit 15 MB, mais MAX_FILE_SIZE=10 MB
        # bloquerait ; on utilise 9 MB → 89 MB < 100 MB, logique identique).
        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = f"uploads/{user_id}/new/new.pdf"
            new_doc = await upload_document(
                db=db_session,
                user_id=user_id,
                filename="new.pdf",
                content=b"%PDF content",
                content_type="application/pdf",
                file_size=9 * 1024 * 1024,
            )

        assert new_doc.file_size == 9 * 1024 * 1024
        bytes_used_final, docs_count_final = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used_final == 89 * 1024 * 1024
        assert docs_count_final == 5

    @pytest.mark.asyncio
    async def test_quota_isolated_per_user(
        self, db_session: AsyncSession
    ) -> None:
        """AC6 — user A à 95 MB refusé, user B à 0 MB accepté (même payload 10 MB)."""
        from app.modules.documents.service import (
            QuotaExceededError,
            upload_document,
        )

        user_a = uuid.uuid4()
        user_b = uuid.uuid4()

        # Remplir user A à 95 MB (10 docs)
        await _fill_user_quota(
            db_session,
            user_a,
            bytes_total=95 * 1024 * 1024,
            docs_count=10,
        )

        # user A → refusé sur 10 MB (95 + 10 = 105 > 100)
        with pytest.raises(QuotaExceededError):
            await upload_document(
                db=db_session,
                user_id=user_a,
                filename="blocked.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=10 * 1024 * 1024,
            )

        # user B → accepté sur 10 MB (0 + 10 = 10 << 100)
        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = f"uploads/{user_b}/new/test.pdf"
            doc_b = await upload_document(
                db=db_session,
                user_id=user_b,
                filename="accepted.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=10 * 1024 * 1024,
            )

        assert doc_b.user_id == user_b

    @pytest.mark.asyncio
    async def test_quota_endpoint_returns_usage(
        self, db_session: AsyncSession
    ) -> None:
        """AC5 — check_user_storage_quota() reflète bytes/docs réels + usage_percent."""
        from app.modules.documents.service import check_user_storage_quota

        user_id = uuid.uuid4()
        # 5 docs de 10 MB chacun = 50 MB
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=50 * 1024 * 1024,
            docs_count=5,
        )

        bytes_used, docs_count = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used == 50 * 1024 * 1024
        assert docs_count == 5

        # Calcul usage_percent (max bytes/docs) : 50/100 = 50% > 5/50 = 10%
        bytes_limit = 100 * 1024 * 1024
        docs_limit = 50
        bytes_pct = min(100, round(bytes_used / bytes_limit * 100))
        docs_pct = min(100, round(docs_count / docs_limit * 100))
        assert max(bytes_pct, docs_pct) == 50

    @pytest.mark.asyncio
    async def test_quota_reads_env_var_override(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC7 — monkeypatch.setattr quota_bytes_per_user_mb=200 permet d'aller au-delà de 100 MB."""
        from app.core.config import settings
        from app.modules.documents.service import (
            QuotaExceededError,
            check_user_storage_quota,
            upload_document,
        )

        user_id = uuid.uuid4()
        # Pré-remplir 95 MB (10 docs). Upload 10 MB → 95+10=105 MB :
        # - refusé avec défaut 100 MB
        # - accepté avec override 200 MB
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=95 * 1024 * 1024,
            docs_count=10,
        )

        # Avec la valeur par défaut (100 MB), l'upload de 10 MB est refusé.
        with pytest.raises(QuotaExceededError):
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="blocked.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=10 * 1024 * 1024,
            )

        # Override live du quota à 200 MB → le même upload doit passer.
        monkeypatch.setattr(settings, "quota_bytes_per_user_mb", 200)

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = f"uploads/{user_id}/ok/ok.pdf"
            doc = await upload_document(
                db=db_session,
                user_id=user_id,
                filename="ok.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=10 * 1024 * 1024,
            )

        assert doc.user_id == user_id
        # Review P1 — preuve stricte que l'override a bien permis d'atteindre
        # 105 MB cumulés, soit au-dessus du défaut 100 MB.
        bytes_used_after, _ = await check_user_storage_quota(
            db_session, user_id
        )
        assert bytes_used_after == 105 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_quota_docs_message_prioritized_on_simultaneous_breach(
        self, db_session: AsyncSession
    ) -> None:
        """Review P3 — invariant AC3 : si docs ET bytes débordent, le message
        doit parler de « documents » (docs check en premier).
        """
        from app.modules.documents.service import (
            QuotaExceededError,
            upload_document,
        )

        user_id = uuid.uuid4()
        # 50 docs (= quota docs atteint) ET ~99 MB (quasi quota bytes).
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=99 * 1024 * 1024,
            docs_count=50,
        )

        with pytest.raises(QuotaExceededError) as exc_info:
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="over.pdf",
                content=b"%PDF",
                # 2 MB : ferait à la fois docs=51 et bytes ≈ 101 MB
                content_type="application/pdf",
                file_size=2 * 1024 * 1024,
            )

        message = str(exc_info.value)
        # L'invariant : docs check fire AVANT bytes check → message « documents »
        assert "Quota atteint" in message
        assert "documents" in message
        assert "MB" not in message

    @pytest.mark.asyncio
    async def test_quota_reads_docs_env_var_override(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Review P4 (AC7) — override de quota_docs_per_user via setattr permet
        d'aller au-delà du défaut 50 documents.
        """
        from app.core.config import settings
        from app.modules.documents.service import (
            QuotaExceededError,
            upload_document,
        )

        user_id = uuid.uuid4()
        # 50 docs (quota atteint) + bytes négligeables
        await _fill_user_quota(
            db_session,
            user_id,
            bytes_total=50 * 1024,
            docs_count=50,
        )

        # Avec défaut 50, un upload de plus est refusé.
        with pytest.raises(QuotaExceededError):
            await upload_document(
                db=db_session,
                user_id=user_id,
                filename="blocked.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=1024,
            )

        # Override live à 100 → le même upload doit passer.
        monkeypatch.setattr(settings, "quota_docs_per_user", 100)

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = f"uploads/{user_id}/ok/ok.pdf"
            doc = await upload_document(
                db=db_session,
                user_id=user_id,
                filename="ok.pdf",
                content=b"%PDF",
                content_type="application/pdf",
                file_size=1024,
            )

        assert doc.user_id == user_id

    def test_quota_settings_bind_env_vars_at_startup(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Review P8 (AC7 binding startup) — les env vars QUOTA_* sont lues par
        pydantic-settings lors de l'instanciation de Settings().
        """
        from app.core.config import Settings

        monkeypatch.setenv("QUOTA_BYTES_PER_USER_MB", "200")
        monkeypatch.setenv("QUOTA_DOCS_PER_USER", "100")

        # Re-instancier Settings : pydantic-settings relit l'environnement.
        fresh_settings = Settings()

        assert fresh_settings.quota_bytes_per_user_mb == 200
        assert fresh_settings.quota_docs_per_user == 100


# ─── Story 10.6 post-review HIGH-10.6-1 : delete_document rétrocompat ───


class TestDeleteDocumentLegacyPaths:
    """Tests rétrocompatibilité Story 10.6 HIGH-10.6-1.

    Vérifie que `delete_document` supprime **réellement** les fichiers
    physiques pour les 2 variantes de `storage_path` co-existantes :
      - **Legacy** : ``uploads/<uid>/<did>/<filename>`` (antérieur à 10.6)
      - **Post-10.6** : ``documents/<uid>/<did>/<filename>`` (clé opaque)
    """

    @pytest.mark.asyncio
    async def test_delete_document_removes_legacy_file_from_disk(
        self,
        db_session: AsyncSession,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HIGH-10.6-1 — row legacy avec `uploads/<uid>/<did>/<file>`
        doit être **physiquement supprimé** (zéro orphelin → RGPD FR65)."""
        from pathlib import Path as _Path

        from app.models.document import Document, DocumentStatus
        from app.modules.documents import service as doc_service
        from app.modules.documents.service import delete_document

        # Redirige UPLOADS_DIR vers le tmp_path pour isoler le filesystem test
        fake_uploads_dir = tmp_path / "uploads"
        fake_uploads_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(doc_service, "UPLOADS_DIR", fake_uploads_dir)

        # Seed d'un fichier physique legacy
        user_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        legacy_rel = f"uploads/{user_id}/{doc_id}/legacy.pdf"
        legacy_abs = tmp_path / legacy_rel
        legacy_abs.parent.mkdir(parents=True, exist_ok=True)
        legacy_abs.write_bytes(b"%PDF-1.4 legacy")
        assert legacy_abs.exists()

        # Row BDD pointant sur la clé legacy
        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename="legacy.pdf",
            original_filename="legacy.pdf",
            mime_type="application/pdf",
            file_size=15,
            storage_path=legacy_rel,
            status=DocumentStatus.uploaded,
        )
        db_session.add(doc)
        await db_session.flush()

        # Act
        await delete_document(db_session, doc)

        # Assert — effet observable : fichier réellement absent du disque
        assert not _Path(legacy_abs).exists(), (
            "Legacy storage_path non supprimé — fuite RGPD (HIGH-10.6-1)"
        )

    @pytest.mark.asyncio
    async def test_delete_document_removes_modern_key_via_storage_provider(
        self,
        db_session: AsyncSession,
    ) -> None:
        """HIGH-10.6-1 — row post-10.6 (`documents/<uid>/<did>/<file>`)
        doit passer par `storage.delete()` et disparaître du provider."""
        from app.core.storage import get_storage_provider
        from app.models.document import Document, DocumentStatus
        from app.modules.documents.service import delete_document

        storage = get_storage_provider()
        user_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        modern_key = f"documents/{user_id}/{doc_id}/modern.pdf"

        # Seed via le provider (respecte la fixture auto-use isolate_storage_provider)
        await storage.put(modern_key, b"%PDF-1.4 modern")
        assert await storage.exists(modern_key) is True

        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename="modern.pdf",
            original_filename="modern.pdf",
            mime_type="application/pdf",
            file_size=15,
            storage_path=modern_key,
            status=DocumentStatus.uploaded,
        )
        db_session.add(doc)
        await db_session.flush()

        # Act
        await delete_document(db_session, doc)

        # Assert — effet observable : provider ne trouve plus la clé
        assert await storage.exists(modern_key) is False
