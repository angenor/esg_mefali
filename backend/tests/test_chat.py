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
        """L'envoi d'un message vide retourne un flux SSE d'erreur."""
        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            data={"content": ""},
            headers=auth_headers(token),
        )

        # L'endpoint retourne 200 avec SSE d'erreur (pas de validation 422)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_send_message_too_long(self, client: AsyncClient) -> None:
        """L'envoi d'un message trop long est accepté (pas de validation longueur)."""
        from unittest.mock import AsyncMock

        _, token = await create_authenticated_user(client)

        create_resp = await client.post(
            "/api/chat/conversations",
            json={},
            headers=auth_headers(token),
        )
        conv_id = create_resp.json()["id"]

        async def mock_stream(content, conversation_id, user_profile=None, context_memory=None):
            yield "Reponse."

        with patch("app.api.chat.stream_llm_tokens", side_effect=mock_stream):
            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "x" * 5001},
                headers=auth_headers(token),
            )

        # L'endpoint ne valide pas la longueur, accepte le message
        assert response.status_code == 200

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
                data={"content": "Mon message"},
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


class TestRateLimit:
    """Tests rate limiting FR-013 : 30 messages/minute/user sur /messages (SSE + JSON fallback)."""

    @staticmethod
    async def _mock_stream(*args, **kwargs):
        """Mock asynchrone de stream_graph_events retournant un token simple."""
        yield {"type": "token", "content": "ok"}

    @staticmethod
    def _make_mock_session_factory():
        """Construire un mock async_session_factory qui simule la persistance SSE."""
        from contextlib import asynccontextmanager
        from unittest.mock import AsyncMock, MagicMock

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(
            side_effect=lambda m: setattr(m, "id", uuid.uuid4())
        )
        mock_session.commit = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        @asynccontextmanager
        async def factory():
            yield mock_session

        return factory

    @staticmethod
    async def _send_one_message(
        client: AsyncClient, conv_id: str, token: str, content: str = "msg"
    ) -> int:
        """Envoyer un message et consommer le flux SSE jusqu'au bout. Retourne le status."""
        response = await client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            data={"content": content},
            headers=auth_headers(token),
        )
        # Drainer le body pour fermer proprement la connexion (evite les fuites
        # dans le pool HTTPX y compris sur les reponses d'erreur — 429, 401...).
        await response.aread()
        return response.status_code

    async def test_rate_limit_trips_at_31st_message(self, client: AsyncClient) -> None:
        """AC1 — Le 31e message dans une fenetre de 60s renvoie 429 + Retry-After."""
        _, token = await create_authenticated_user(client)
        create_resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token)
        )
        conv_id = create_resp.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            for i in range(30):
                status_code = await self._send_one_message(client, conv_id, token, f"m{i}")
                assert status_code == 200, f"Message {i + 1} a echoue (status {status_code})"

            # 31e message -> 429
            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "dépassement"},
                headers=auth_headers(token),
            )
            await response.aread()  # Drainer le body 429 pour fermer la connexion HTTPX.

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        retry_after = response.headers["Retry-After"]
        assert retry_after.isdigit(), f"Retry-After doit etre un entier, recu: {retry_after!r}"
        # AC4 — la reponse 429 est une JSONResponse, pas un StreamingResponse SSE.
        content_type = response.headers.get("content-type", "")
        assert not content_type.startswith("text/event-stream"), (
            f"AC4 viole : 429 doit precéder l'ouverture du stream SSE "
            f"(content-type recu : {content_type!r})"
        )

    async def test_rate_limit_returns_retry_after_header(self, client: AsyncClient) -> None:
        """AC1 — Header Retry-After explicitement present et numerique sur 429."""
        _, token = await create_authenticated_user(client)
        create_resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token)
        )
        conv_id = create_resp.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            for i in range(30):
                await self._send_one_message(client, conv_id, token, f"m{i}")

            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "dépassement"},
                headers=auth_headers(token),
            )
            await response.aread()  # Drainer le body 429 pour fermer la connexion HTTPX.

        assert response.status_code == 429
        assert response.headers.get("Retry-After") is not None
        assert int(response.headers["Retry-After"]) > 0

    async def test_rate_limit_resets_after_60s(self, client: AsyncClient) -> None:
        """AC2 — Apres reinitialisation de la fenetre, le message suivant passe.

        On simule le « apres 60s » par un reset explicite du storage SlowAPI
        car freezegun ne peut pas patcher time.time() dans le thread
        `threading.Timer` de `MemoryStorage` (voir Dev Notes story 9.3
        §Root cause #1). Equivalent semantique, determinisme preserve.

        NB : la fixture autouse `reset_rate_limiter` (conftest.py:43-53) tourne
        AVANT chaque test. Ici on appelle `limiter.reset()` AU MILIEU du test,
        entre les 2 phases, ce qui est une utilisation distincte et voulue.
        """
        from app.core.rate_limit import limiter

        _, token = await create_authenticated_user(client)
        create_resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token)
        )
        conv_id = create_resp.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            # Phase 1 : saturer la fenetre (30 messages OK + 1 refuse en 429).
            for i in range(30):
                status_code = await self._send_one_message(client, conv_id, token, f"m{i}")
                assert status_code == 200

            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "dépassement"},
                headers=auth_headers(token),
            )
            assert response.status_code == 429

            # Phase 2 : reset explicite du limiter (equivalent « 60s passes »).
            limiter.reset()

            status_code = await self._send_one_message(
                client, conv_id, token, "après fenêtre"
            )

        assert status_code == 200

    async def test_rate_limit_isolated_per_user(self, client: AsyncClient) -> None:
        """AC3 — Deux utilisateurs distincts ont des quotas independants."""
        _, token_a = await create_authenticated_user(client)
        _, token_b = await create_authenticated_user(client)

        create_a = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token_a)
        )
        create_b = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token_b)
        )
        conv_a = create_a.json()["id"]
        conv_b = create_b.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            # user_A epuise son quota
            for i in range(30):
                status_code = await self._send_one_message(client, conv_a, token_a, f"a{i}")
                assert status_code == 200

            over_a = await client.post(
                f"/api/chat/conversations/{conv_a}/messages",
                data={"content": "a-over"},
                headers=auth_headers(token_a),
            )
            assert over_a.status_code == 429

            # user_B doit toujours pouvoir envoyer un message
            status_b = await self._send_one_message(client, conv_b, token_b, "b1")

        assert status_b == 200

    async def test_rate_limit_on_json_fallback_endpoint(self, client: AsyncClient) -> None:
        """AC6 — Le fallback JSON /messages/json applique le meme quota 30/min."""
        _, token = await create_authenticated_user(client)
        create_resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers(token)
        )
        conv_id = create_resp.json()["id"]

        with (
            patch("app.api.chat.stream_graph_events", side_effect=self._mock_stream),
            patch("app.api.chat.async_session_factory", self._make_mock_session_factory()),
        ):
            for i in range(30):
                response = await client.post(
                    f"/api/chat/conversations/{conv_id}/messages/json",
                    json={"content": f"m{i}"},
                    headers=auth_headers(token),
                )
                if response.status_code == 200:
                    await response.aread()
                assert response.status_code == 200, f"Message {i + 1} a echoue"

            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages/json",
                json={"content": "dépassement"},
                headers=auth_headers(token),
            )
            await response.aread()  # Drainer le body 429 pour fermer la connexion HTTPX.

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    async def test_rate_limit_unauthenticated_returns_401_not_429(
        self, client: AsyncClient
    ) -> None:
        """AC7 — Sans token, l'API retourne 401 avant toute verification de quota.

        On envoie 31 requetes sans token : si l'auth guard ne precedait PAS le
        decorateur @limiter.limit, la 31e basculerait en 429. En restant a 401
        sur les 31 requetes, on prouve que l'authentification court-circuite le
        rate-limit (et donc qu'un attaquant non authentifie ne peut pas epuiser
        le quota d'un autre utilisateur).
        """
        fake_conv_id = str(uuid.uuid4())

        for i in range(31):
            response = await client.post(
                f"/api/chat/conversations/{fake_conv_id}/messages",
                data={"content": f"sans auth {i}"},
            )
            await response.aread()
            assert response.status_code == 401, (
                f"Requete {i + 1}/31 sans token : status {response.status_code}, "
                f"attendu 401 (l'auth guard doit preceder le rate-limit)"
            )
            assert response.status_code != 429, (
                f"Requete {i + 1}/31 : rate-limit declenche avant l'auth guard (AC7 viole)"
            )
