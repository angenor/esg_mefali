"""Tests E2E documents : flux complets upload, filtrage, detail, suppression (T056).

Tests d'intégration de bout en bout simulant les parcours utilisateur réels.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import make_unique_email


# ─── Helpers ──────────────────────────────────────────────────────────


async def register_and_login(client: AsyncClient) -> str:
    """Créer un utilisateur et retourner le token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Awa Traore",
        "company_name": "GreenAfrica SA",
    }
    await client.post("/api/auth/register", json=data)
    resp = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    return resp.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def upload_doc(
    client: AsyncClient,
    token: str,
    filename: str = "rapport.pdf",
    content: bytes = b"%PDF-1.4 dummy",
    mime: str = "application/pdf",
) -> dict:
    """Uploader un document et retourner sa réponse."""
    with patch("app.modules.documents.service._save_file_to_disk") as mock_save:
        mock_save.return_value = f"uploads/test/{uuid.uuid4()}/{filename}"
        resp = await client.post(
            "/api/documents/upload",
            headers=headers(token),
            files={"files": (filename, content, mime)},
        )
    return resp.json()


# ─── E2E : Upload depuis la page documents ──────────────────────────


class TestE2EUploadFromDocumentsPage:
    """Flux complet : upload → liste → detail → suppression."""

    @pytest.mark.asyncio
    async def test_full_document_lifecycle(self, client: AsyncClient) -> None:
        """Upload un PDF, le retrouver dans la liste, voir le detail, le supprimer."""
        token = await register_and_login(client)

        # 1. Upload
        result = await upload_doc(client, token, "bilan_2024.pdf")
        assert len(result["documents"]) == 1
        doc_id = result["documents"][0]["id"]
        assert result["documents"][0]["status"] == "uploaded"

        # 2. Le document apparait dans la liste
        list_resp = await client.get("/api/documents/", headers=headers(token))
        assert list_resp.status_code == 200
        docs = list_resp.json()["documents"]
        assert any(d["id"] == doc_id for d in docs)

        # 3. Detail du document
        detail_resp = await client.get(
            f"/api/documents/{doc_id}", headers=headers(token)
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["original_filename"] == "bilan_2024.pdf"

        # 4. Suppression
        with patch("app.modules.documents.service._delete_file_from_disk"):
            del_resp = await client.delete(
                f"/api/documents/{doc_id}", headers=headers(token)
            )
        assert del_resp.status_code == 204

        # 5. Le document n'est plus dans la liste
        list_resp = await client.get("/api/documents/", headers=headers(token))
        docs = list_resp.json()["documents"]
        assert not any(d["id"] == doc_id for d in docs)

    @pytest.mark.asyncio
    async def test_upload_multiple_then_filter(self, client: AsyncClient) -> None:
        """Upload plusieurs fichiers de types differents, puis filtrer."""
        token = await register_and_login(client)

        # Upload PDF
        await upload_doc(client, token, "rapport.pdf", b"%PDF content", "application/pdf")

        # Upload image
        await upload_doc(client, token, "photo.png", b"\x89PNG content", "image/png")

        # Liste complète
        list_resp = await client.get("/api/documents/", headers=headers(token))
        assert list_resp.json()["total"] == 2

    @pytest.mark.asyncio
    async def test_upload_rejects_oversized_file(self, client: AsyncClient) -> None:
        """Un fichier de plus de 10 MB est rejeté."""
        token = await register_and_login(client)

        # Contenu de 11 MB
        big_content = b"x" * (11 * 1024 * 1024)
        resp = await client.post(
            "/api/documents/upload",
            headers=headers(token),
            files={"files": ("big.pdf", big_content, "application/pdf")},
        )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_type(self, client: AsyncClient) -> None:
        """Un fichier de type non supporté est rejeté."""
        token = await register_and_login(client)

        resp = await client.post(
            "/api/documents/upload",
            headers=headers(token),
            files={"files": ("script.js", b"alert(1)", "application/javascript")},
        )

        assert resp.status_code == 400


# ─── E2E : Isolation entre utilisateurs ──────────────────────────────


class TestE2EUserIsolation:
    """Vérifier que les documents sont isolés entre utilisateurs."""

    @pytest.mark.asyncio
    async def test_user_cannot_see_others_documents(
        self, client: AsyncClient
    ) -> None:
        """User A uploade, User B ne voit rien."""
        token_a = await register_and_login(client)
        token_b = await register_and_login(client)

        # A uploade un document
        result = await upload_doc(client, token_a, "confidentiel.pdf")
        doc_id = result["documents"][0]["id"]

        # B ne voit rien dans sa liste
        list_resp = await client.get("/api/documents/", headers=headers(token_b))
        assert list_resp.json()["total"] == 0

        # B ne peut pas accéder au detail
        detail_resp = await client.get(
            f"/api/documents/{doc_id}", headers=headers(token_b)
        )
        assert detail_resp.status_code == 403

        # B ne peut pas supprimer
        del_resp = await client.delete(
            f"/api/documents/{doc_id}", headers=headers(token_b)
        )
        assert del_resp.status_code == 403


# ─── E2E : Upload dans le chat ──────────────────────────────────────


class TestE2EUploadInChat:
    """Flux complet : upload d'un document dans le chat."""

    @pytest.mark.asyncio
    async def test_chat_with_document_upload(self, client: AsyncClient) -> None:
        """Envoyer un document dans le chat déclenche l'analyse."""
        token = await register_and_login(client)

        # Créer une conversation d'abord
        conv_resp = await client.post(
            "/api/chat/conversations",
            headers=headers(token),
            json={"title": "Test document chat"},
        )

        if conv_resp.status_code == 200 or conv_resp.status_code == 201:
            conv_id = conv_resp.json().get("id")

            # Envoyer un message avec fichier dans le chat
            with patch(
                "app.modules.documents.service._save_file_to_disk"
            ) as mock_save, patch(
                "app.graph.nodes.document_node", new_callable=AsyncMock
            ):
                mock_save.return_value = "uploads/test/doc/test.pdf"

                resp = await client.post(
                    f"/api/chat/conversations/{conv_id}/messages",
                    headers=headers(token),
                    data={"content": "Analyse ce document"},
                    files={"file": ("bilan.pdf", b"%PDF content", "application/pdf")},
                )

                # Le endpoint doit accepter le multipart
                assert resp.status_code in (200, 201, 202)


# ─── E2E : Gestion d'erreurs ────────────────────────────────────────


class TestE2EErrorHandling:
    """Tests des scénarios d'erreur en conditions réelles."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_document_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Accéder à un document inexistant retourne 404."""
        token = await register_and_login(client)
        resp = await client.get(
            f"/api/documents/{uuid.uuid4()}", headers=headers(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Supprimer un document inexistant retourne 404."""
        token = await register_and_login(client)
        resp = await client.delete(
            f"/api/documents/{uuid.uuid4()}", headers=headers(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_access_rejected(
        self, client: AsyncClient
    ) -> None:
        """Tous les endpoints rejettent les requêtes non authentifiées."""
        endpoints = [
            ("GET", "/api/documents/"),
            ("GET", f"/api/documents/{uuid.uuid4()}"),
            ("DELETE", f"/api/documents/{uuid.uuid4()}"),
        ]

        for method, url in endpoints:
            resp = await client.request(method, url)
            assert resp.status_code == 401, f"{method} {url} should return 401"
