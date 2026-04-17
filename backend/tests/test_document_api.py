"""Tests d'intégration des endpoints documents (T017).

Tests POST /upload, GET /, GET /{id}, DELETE /{id}.
Écrits AVANT l'implémentation (TDD RED phase).
"""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_unique_email


# ─── Helpers ──────────────────────────────────────────────────────────


async def create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Créer un utilisateur et retourner ses données + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Fatou Diallo",
        "company_name": "EcoVert SARL",
    }
    await client.post("/api/auth/register", json=data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login_response.json()["access_token"]
    return data, token


def auth_headers(token: str) -> dict[str, str]:
    """Headers d'authentification."""
    return {"Authorization": f"Bearer {token}"}


# ─── Tests POST /api/documents/upload ──────────────────────────────


class TestUploadEndpoint:
    """Tests du endpoint d'upload."""

    @pytest.mark.asyncio
    async def test_upload_single_pdf(self, client: AsyncClient) -> None:
        """Upload d'un seul PDF retourne 201 avec le document créé."""
        _, token = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            response = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files={"files": ("rapport.pdf", b"%PDF-1.4 content", "application/pdf")},
            )

        assert response.status_code == 201
        body = response.json()
        assert "documents" in body
        assert len(body["documents"]) == 1
        assert body["documents"][0]["original_filename"] == "rapport.pdf"
        assert body["documents"][0]["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_upload_rejects_invalid_mime(self, client: AsyncClient) -> None:
        """Upload d'un fichier non autorisé retourne 400."""
        _, token = await create_authenticated_user(client)

        response = await client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            files={"files": ("virus.exe", b"malware", "application/x-msdownload")},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient) -> None:
        """Upload sans token retourne 401."""
        response = await client.post(
            "/api/documents/upload",
            files={"files": ("test.pdf", b"content", "application/pdf")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, client: AsyncClient) -> None:
        """Upload de plusieurs fichiers retourne tous les documents."""
        _, token = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            response = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files=[
                    ("files", ("doc1.pdf", b"%PDF-1.4 content1", "application/pdf")),
                    ("files", ("doc2.pdf", b"%PDF-1.4 content2", "application/pdf")),
                ],
            )

        assert response.status_code == 201
        assert len(response.json()["documents"]) == 2


# ─── Tests GET /api/documents/ ──────────────────────────────────────


class TestListEndpoint:
    """Tests du endpoint de liste."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient) -> None:
        """Un utilisateur sans documents voit une liste vide."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/documents/",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["documents"] == []
        assert body["total"] == 0

    @pytest.mark.asyncio
    async def test_list_only_own_documents(self, client: AsyncClient) -> None:
        """Un utilisateur ne voit que ses propres documents."""
        _, token1 = await create_authenticated_user(client)
        _, token2 = await create_authenticated_user(client)

        # Upload un document pour user1
        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            await client.post(
                "/api/documents/upload",
                headers=auth_headers(token1),
                files={"files": ("doc1.pdf", b"%PDF content", "application/pdf")},
            )

        # User2 ne doit pas voir le document de user1
        response = await client.get(
            "/api/documents/",
            headers=auth_headers(token2),
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0


# ─── Tests GET /api/documents/{id} ─────────────────────────────────


class TestDetailEndpoint:
    """Tests du endpoint de détail."""

    @pytest.mark.asyncio
    async def test_get_document_detail(self, client: AsyncClient) -> None:
        """Récupérer le détail d'un document existant."""
        _, token = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files={"files": ("doc.pdf", b"%PDF content", "application/pdf")},
            )

        doc_id = upload_resp.json()["documents"][0]["id"]
        response = await client.get(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert response.json()["id"] == doc_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client: AsyncClient) -> None:
        """Un document inexistant retourne 404."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            f"/api/documents/{uuid.uuid4()}",
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_user_document(self, client: AsyncClient) -> None:
        """Accéder au document d'un autre utilisateur retourne 403."""
        _, token1 = await create_authenticated_user(client)
        _, token2 = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token1),
                files={"files": ("doc.pdf", b"%PDF content", "application/pdf")},
            )

        doc_id = upload_resp.json()["documents"][0]["id"]

        # User2 essaie d'accéder au document de user1
        response = await client.get(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token2),
        )

        assert response.status_code == 403


# ─── Tests DELETE /api/documents/{id} ────────────────────────────────


class TestDeleteEndpoint:
    """Tests du endpoint de suppression."""

    @pytest.mark.asyncio
    async def test_delete_document(self, client: AsyncClient) -> None:
        """Supprimer un document retourne 204."""
        _, token = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files={"files": ("doc.pdf", b"%PDF content", "application/pdf")},
            )

        doc_id = upload_resp.json()["documents"][0]["id"]

        with patch("app.modules.documents.service._delete_file_from_disk"):
            response = await client.delete(
                f"/api/documents/{doc_id}",
                headers=auth_headers(token),
            )

        assert response.status_code == 204

        # Vérifier que le document n'existe plus
        response = await client.get(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_user_document(self, client: AsyncClient) -> None:
        """Supprimer le document d'un autre utilisateur retourne 403."""
        _, token1 = await create_authenticated_user(client)
        _, token2 = await create_authenticated_user(client)

        with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token1),
                files={"files": ("doc.pdf", b"%PDF content", "application/pdf")},
            )

        doc_id = upload_resp.json()["documents"][0]["id"]

        response = await client.delete(
            f"/api/documents/{doc_id}",
            headers=auth_headers(token2),
        )

        assert response.status_code == 403


# ─── Tests GET /api/documents/quota (AC5) ───────────────────────────


class TestQuotaEndpoint:
    """Tests du endpoint de consultation du quota (dette spec 004 §3.2)."""

    @pytest.mark.asyncio
    async def test_quota_endpoint_requires_auth(
        self, client: AsyncClient
    ) -> None:
        """GET /api/documents/quota sans token retourne 401."""
        response = await client.get("/api/documents/quota")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_quota_endpoint_returns_correct_structure(
        self, client: AsyncClient
    ) -> None:
        """Après upload, GET /api/documents/quota retourne les 5 champs corrects."""
        _, token = await create_authenticated_user(client)

        # Upload un document de 2 MB pour avoir des valeurs non-nulles
        two_mb = 2 * 1024 * 1024
        content = b"%PDF-1.4" + b"x" * (two_mb - 8)

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files={"files": ("doc.pdf", content, "application/pdf")},
            )
        assert upload_resp.status_code == 201

        response = await client.get(
            "/api/documents/quota",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "bytes_used",
            "bytes_limit",
            "docs_count",
            "docs_limit",
            "usage_percent",
        }
        assert body["bytes_used"] == two_mb
        assert body["bytes_limit"] == 100 * 1024 * 1024
        assert body["docs_count"] == 1
        assert body["docs_limit"] == 50
        assert 0 <= body["usage_percent"] <= 100

    @pytest.mark.asyncio
    async def test_quota_endpoint_reflects_delete(
        self, client: AsyncClient
    ) -> None:
        """Review P2 (AC4 end-to-end) — DELETE décrémente bytes_used visible via GET /quota."""
        _, token = await create_authenticated_user(client)

        # Upload 2 fichiers de 2 MB (batch sous MAX_FILES_PER_UPLOAD=5).
        two_mb = 2 * 1024 * 1024
        content = b"%PDF-1.4" + b"x" * (two_mb - 8)

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            upload_resp = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files=[
                    ("files", ("a.pdf", content, "application/pdf")),
                    ("files", ("b.pdf", content, "application/pdf")),
                ],
            )
        assert upload_resp.status_code == 201
        doc_ids = [d["id"] for d in upload_resp.json()["documents"]]

        # GET /quota avant delete
        before = await client.get(
            "/api/documents/quota", headers=auth_headers(token)
        )
        assert before.status_code == 200
        assert before.json()["bytes_used"] == 2 * two_mb
        assert before.json()["docs_count"] == 2

        # DELETE un document
        with patch(
            "app.modules.documents.service._delete_file_from_disk"
        ):
            delete_resp = await client.delete(
                f"/api/documents/{doc_ids[0]}",
                headers=auth_headers(token),
            )
        assert delete_resp.status_code == 204

        # GET /quota après delete : bytes_used décrémenté de 2 MB
        after = await client.get(
            "/api/documents/quota", headers=auth_headers(token)
        )
        assert after.status_code == 200
        assert after.json()["bytes_used"] == two_mb
        assert after.json()["docs_count"] == 1

    @pytest.mark.asyncio
    async def test_quota_endpoint_usage_percent_realistic(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Review P5 (AC5) — usage_percent = max(bytes_pct, docs_pct) sur valeurs non-triviales.

        Pré-remplit 50 MB / 5 docs directement en BDD (plus rapide que
        uploader 50 MB via HTTP). bytes_pct=50%, docs_pct=10%, max=50%.
        """
        from sqlalchemy import select

        from app.models.user import User
        from tests.test_document_upload import _fill_user_quota

        data, token = await create_authenticated_user(client)

        result = await db_session.execute(
            select(User).where(User.email == data["email"])
        )
        user = result.scalar_one()

        await _fill_user_quota(
            db_session,
            user.id,
            bytes_total=50 * 1024 * 1024,
            docs_count=5,
        )
        await db_session.commit()

        response = await client.get(
            "/api/documents/quota", headers=auth_headers(token)
        )

        assert response.status_code == 200
        body = response.json()
        assert body["bytes_used"] == 50 * 1024 * 1024
        assert body["docs_count"] == 5
        # bytes_pct = 50/100 = 50% ; docs_pct = 5/50 = 10% ; max = 50%
        assert body["usage_percent"] == 50

    @pytest.mark.asyncio
    async def test_upload_returns_413_on_quota_exceeded(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Review P6 — POST /api/documents/upload via HTTP → 413 quand quota dépassé.

        Baisse le quota docs à 1 pour déclencher facilement le 413 sur le
        2ᵉ upload ; vérifie le code HTTP, le détail JSON, et que le 413
        passe bien par le router (pas par le check service).
        """
        from app.core.config import settings

        _, token = await create_authenticated_user(client)

        # Quota docs = 1 : un seul upload autorisé.
        monkeypatch.setattr(settings, "quota_docs_per_user", 1)

        with patch(
            "app.modules.documents.service._save_file_to_disk"
        ) as mock_save:
            mock_save.return_value = "uploads/test/doc/test.pdf"
            first = await client.post(
                "/api/documents/upload",
                headers=auth_headers(token),
                files={"files": ("first.pdf", b"%PDF-1.4 content", "application/pdf")},
            )
        assert first.status_code == 201

        # 2ᵉ upload : 1 + 1 = 2 > 1 → 413 via le pré-check router.
        second = await client.post(
            "/api/documents/upload",
            headers=auth_headers(token),
            files={"files": ("second.pdf", b"%PDF-1.4 content", "application/pdf")},
        )

        assert second.status_code == 413
        detail = second.json()["detail"]
        assert "Quota atteint" in detail
        assert "documents" in detail
