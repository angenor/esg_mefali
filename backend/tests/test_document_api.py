"""Tests d'intégration des endpoints documents (T017).

Tests POST /upload, GET /, GET /{id}, DELETE /{id}.
Écrits AVANT l'implémentation (TDD RED phase).
"""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

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
