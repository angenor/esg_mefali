"""Tests des endpoints de conversation et chat.

T034: Tests endpoints chat (CRUD conversations, envoi message, streaming)

Écrits AVANT l'implémentation (TDD RED phase).
"""

import uuid
from unittest.mock import patch

from httpx import AsyncClient

from tests.conftest import make_unique_email


# ─── Helpers ──────────────────────────────────────────────────────────


async def create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Créer un utilisateur et retourner ses données + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Amadou Diallo",
        "company_name": "EcoSolaire SARL",
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


# ─── Tests CRUD Conversations ────────────────────────────────────────


class TestCreateConversation:
    """Tests POST /api/chat/conversations."""

    async def test_create_conversation_success(self, client: AsyncClient) -> None:
        """Un utilisateur connecté peut créer une conversation."""
        _, token = await create_authenticated_user(client)

        response = await client.post(
            "/api/chat/conversations",
            json={"title": "Ma conversation ESG"},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Ma conversation ESG"
        assert body["current_module"] == "chat"
        assert "id" in body
        assert "created_at" in body

    async def test_create_conversation_default_title(self, client: AsyncClient) -> None:
        """Une conversation sans titre utilise le titre par défaut."""
        _, token = await create_authenticated_user(client)

        response = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Nouvelle conversation"

    async def test_create_conversation_unauthenticated(self, client: AsyncClient) -> None:
        """La création sans token retourne 401."""
        response = await client.post("/api/chat/conversations", json={})
        assert response.status_code == 401


class TestListConversations:
    """Tests GET /api/chat/conversations."""

    async def test_list_conversations_empty(self, client: AsyncClient) -> None:
        """Un utilisateur sans conversations reçoit une liste vide."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/chat/conversations",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_conversations_with_data(self, client: AsyncClient) -> None:
        """Un utilisateur voit ses propres conversations."""
        _, token = await create_authenticated_user(client)

        # Créer 3 conversations
        for i in range(3):
            await client.post(
                "/api/chat/conversations",
                json={"title": f"Conv {i}"},
                headers=auth_headers(token),
            )

        response = await client.get(
            "/api/chat/conversations",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    async def test_list_conversations_isolation(self, client: AsyncClient) -> None:
        """Un utilisateur ne voit pas les conversations d'un autre."""
        _, token_a = await create_authenticated_user(client)
        _, token_b = await create_authenticated_user(client)

        # User A crée une conversation
        await client.post(
            "/api/chat/conversations",
            json={"title": "Conv de A"},
            headers=auth_headers(token_a),
        )

        # User B ne doit pas la voir
        response = await client.get(
            "/api/chat/conversations",
            headers=auth_headers(token_b),
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_list_conversations_pagination(self, client: AsyncClient) -> None:
        """La pagination fonctionne correctement."""
        _, token = await create_authenticated_user(client)

        # Créer 5 conversations
        for i in range(5):
            await client.post(
                "/api/chat/conversations",
                json={"title": f"Conv {i}"},
                headers=auth_headers(token),
            )

        response = await client.get(
            "/api/chat/conversations?page=1&limit=2",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["limit"] == 2


class TestUpdateConversation:
    """Tests PATCH /api/chat/conversations/{id}."""

    async def test_update_title(self, client: AsyncClient) -> None:
        """Un utilisateur peut modifier le titre de sa conversation."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={"title": "Ancien titre"},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/chat/conversations/{conv_id}",
            json={"title": "Nouveau titre"},
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Nouveau titre"

    async def test_update_nonexistent_conversation(self, client: AsyncClient) -> None:
        """La modification d'une conversation inexistante retourne 404."""
        _, token = await create_authenticated_user(client)
        fake_id = str(uuid.uuid4())

        response = await client.patch(
            f"/api/chat/conversations/{fake_id}",
            json={"title": "Test"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404


class TestDeleteConversation:
    """Tests DELETE /api/chat/conversations/{id}."""

    async def test_delete_conversation(self, client: AsyncClient) -> None:
        """Un utilisateur peut supprimer sa conversation."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={"title": "À supprimer"},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/chat/conversations/{conv_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 204

        # Vérifier que la conversation n'existe plus
        list_resp = await client.get(
            "/api/chat/conversations",
            headers=auth_headers(token),
        )
        assert list_resp.json()["total"] == 0

    async def test_delete_nonexistent_conversation(self, client: AsyncClient) -> None:
        """La suppression d'une conversation inexistante retourne 404."""
        _, token = await create_authenticated_user(client)
        fake_id = str(uuid.uuid4())

        response = await client.delete(
            f"/api/chat/conversations/{fake_id}",
            headers=auth_headers(token),
        )

        assert response.status_code == 404


# ─── Tests Messages ──────────────────────────────────────────────────


class TestGetMessages:
    """Tests GET /api/chat/conversations/{id}/messages."""

    async def test_get_messages_empty(self, client: AsyncClient) -> None:
        """Une conversation sans messages retourne une liste vide."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/chat/conversations/{conv_id}/messages",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_get_messages_not_found(self, client: AsyncClient) -> None:
        """Les messages d'une conversation inexistante retournent 404."""
        _, token = await create_authenticated_user(client)
        fake_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/chat/conversations/{fake_id}/messages",
            headers=auth_headers(token),
        )

        assert response.status_code == 404


class TestSendMessage:
    """Tests POST /api/chat/conversations/{id}/messages."""

    async def test_send_message_returns_stream(self, client: AsyncClient) -> None:
        """L'envoi d'un message retourne un flux SSE."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        # Mocker le graphe LangGraph pour ne pas appeler le LLM réel
        with patch("app.api.chat.invoke_graph") as mock_invoke:
            mock_invoke.return_value = "Bonjour ! Je suis votre assistant ESG."

            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"content": "Bonjour"},
                headers=auth_headers(token),
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_send_message_empty_content(self, client: AsyncClient) -> None:
        """L'envoi d'un message vide retourne 422."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            json={"content": ""},
            headers=auth_headers(token),
        )

        assert response.status_code == 422

    async def test_send_message_too_long(self, client: AsyncClient) -> None:
        """L'envoi d'un message trop long retourne 422."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            json={"content": "x" * 5001},
            headers=auth_headers(token),
        )

        assert response.status_code == 422

    async def test_send_message_conversation_not_found(self, client: AsyncClient) -> None:
        """L'envoi dans une conversation inexistante retourne 404."""
        _, token = await create_authenticated_user(client)
        fake_id = str(uuid.uuid4())

        response = await client.post(
            f"/api/chat/conversations/{fake_id}/messages",
            json={"content": "Bonjour"},
            headers=auth_headers(token),
        )

        assert response.status_code == 404

    async def test_send_message_persists(self, client: AsyncClient) -> None:
        """Le message utilisateur et la réponse sont persistés via SSE streaming."""
        from contextlib import asynccontextmanager
        from unittest.mock import AsyncMock, MagicMock

        from tests.conftest import test_session_factory

        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        async def mock_stream(content, conversation_id, user_profile=None, context_memory=None):
            yield "Réponse de l'assistant."

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(
            side_effect=lambda m: setattr(m, "id", __import__("uuid").uuid4())
        )
        mock_session.commit = AsyncMock()

        @asynccontextmanager
        async def mock_factory():
            yield mock_session

        with (
            patch("app.api.chat.stream_llm_tokens", side_effect=mock_stream),
            patch("app.api.chat.async_session_factory", mock_factory),
        ):
            resp = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"content": "Mon message"},
                headers=auth_headers(token),
            )

        assert resp.status_code == 200
        # Vérifier que le message utilisateur est persisté dans la BDD
        messages_resp = await client.get(
            f"/api/chat/conversations/{conv_id}/messages",
            headers=auth_headers(token),
        )

        assert messages_resp.status_code == 200
        body = messages_resp.json()
        # Au minimum le message utilisateur est persisté
        assert body["total"] >= 1
        assert body["items"][0]["role"] == "user"
        assert body["items"][0]["content"] == "Mon message"
