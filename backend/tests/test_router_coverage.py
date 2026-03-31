"""Tests supplémentaires pour le router documents (couverture T057).

Couvre les endpoints reanalyze, preview et les cas limites.
"""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.conftest import make_unique_email


async def register_and_login(client: AsyncClient) -> str:
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Moussa Keita",
        "company_name": "SolairePlus",
    }
    await client.post("/api/auth/register", json=data)
    resp = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    return resp.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def upload_doc(client: AsyncClient, token: str) -> str:
    with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
        mock_save.return_value = f"uploads/test/{uuid.uuid4()}/doc.pdf"
        resp = await client.post(
            "/api/documents/upload",
            headers=headers(token),
            files={"files": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
        )
    return resp.json()["documents"][0]["id"]


class TestReanalyzeEndpoint:
    """Tests du endpoint POST /{id}/reanalyze."""

    @pytest.mark.asyncio
    async def test_reanalyze_existing_document(self, client: AsyncClient) -> None:
        token = await register_and_login(client)
        doc_id = await upload_doc(client, token)

        resp = await client.post(
            f"/api/documents/{doc_id}/reanalyze",
            headers=headers(token),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == doc_id
        assert body["status"] == "processing"
        assert "relancée" in body["message"]

    @pytest.mark.asyncio
    async def test_reanalyze_nonexistent_document(self, client: AsyncClient) -> None:
        token = await register_and_login(client)

        resp = await client.post(
            f"/api/documents/{uuid.uuid4()}/reanalyze",
            headers=headers(token),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_reanalyze_other_user_document(self, client: AsyncClient) -> None:
        token1 = await register_and_login(client)
        token2 = await register_and_login(client)
        doc_id = await upload_doc(client, token1)

        resp = await client.post(
            f"/api/documents/{doc_id}/reanalyze",
            headers=headers(token2),
        )

        assert resp.status_code == 403


class TestPreviewEndpoint:
    """Tests du endpoint GET /{id}/preview."""

    @pytest.mark.asyncio
    async def test_preview_nonexistent_document(self, client: AsyncClient) -> None:
        token = await register_and_login(client)

        resp = await client.get(
            f"/api/documents/{uuid.uuid4()}/preview",
            headers=headers(token),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_other_user_document(self, client: AsyncClient) -> None:
        token1 = await register_and_login(client)
        token2 = await register_and_login(client)
        doc_id = await upload_doc(client, token1)

        resp = await client.get(
            f"/api/documents/{doc_id}/preview",
            headers=headers(token2),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_preview_missing_file(self, client: AsyncClient) -> None:
        """Le fichier physique n'existe pas sur le disque."""
        token = await register_and_login(client)
        doc_id = await upload_doc(client, token)

        resp = await client.get(
            f"/api/documents/{doc_id}/preview",
            headers=headers(token),
        )

        # Le fichier n'existe pas vraiment sur le disque
        assert resp.status_code == 404


class TestUploadMaxFiles:
    """Tests du nombre max de fichiers."""

    @pytest.mark.asyncio
    async def test_upload_exceeds_max_files(self, client: AsyncClient) -> None:
        token = await register_and_login(client)

        files = [
            ("files", (f"doc{i}.pdf", b"%PDF content", "application/pdf"))
            for i in range(6)
        ]

        resp = await client.post(
            "/api/documents/upload",
            headers=headers(token),
            files=files,
        )

        assert resp.status_code == 400
        assert "Maximum" in resp.json()["detail"]


class TestListWithFilters:
    """Tests des filtres de liste."""

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, client: AsyncClient) -> None:
        token = await register_and_login(client)

        # Upload 3 documents
        for i in range(3):
            await upload_doc(client, token)

        # Page 1 avec limit 2
        resp = await client.get(
            "/api/documents/?page=1&limit=2",
            headers=headers(token),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["documents"]) == 2
        assert body["page"] == 1
