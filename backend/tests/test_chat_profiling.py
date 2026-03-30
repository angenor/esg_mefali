"""Tests d'intégration SSE pour le profilage (US1).

SQLite en mémoire ne supporte pas l'accès concurrent. Le SSE callback
dans chat.py utilise async_session_factory directement, ce qui crée un conflit.
On contourne en mockant la sauvegarde du message assistant dans le SSE callback.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> tuple[str, dict]:
    """Créer un utilisateur et retourner le token + headers."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Test1234!",
            "full_name": "Test User",
            "company_name": "Test Co",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "Test1234!"},
    )
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


class TestChatProfiling:
    """Tests d'intégration du streaming SSE avec extraction de profil."""

    @pytest.mark.asyncio
    async def test_message_with_profile_info_emits_events(
        self, client: AsyncClient
    ) -> None:
        """Un message avec infos génère des events token + profile_update + profile_completion."""
        _, headers = await _register_and_login(client)

        resp = await client.post(
            "/api/chat/conversations",
            headers=headers,
            json={"title": "Test profiling"},
        )
        assert resp.status_code == 201
        conv_id = resp.json()["id"]

        async def mock_stream_tokens(content, conversation_id, user_profile=None, context_memory=None):
            yield "Voici mes conseils"

        mock_extract = AsyncMock(
            return_value=(
                [
                    {"field": "sector", "value": "recyclage", "label": "Secteur"},
                    {"field": "city", "value": "Abidjan", "label": "Ville"},
                ],
                {
                    "identity_completion": 37.5,
                    "esg_completion": 0.0,
                    "overall_completion": 18.8,
                },
            )
        )

        # Mock async_session_factory comme un context manager qui fournit
        # un mock de session suffisant pour sauvegarder le message assistant
        mock_msg = MagicMock()
        mock_msg.id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=lambda m: setattr(m, "id", mock_msg.id))
        mock_session.commit = AsyncMock()

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def mock_factory():
            yield mock_session

        with (
            patch("app.api.chat.stream_llm_tokens", side_effect=mock_stream_tokens),
            patch("app.api.chat.extract_and_update_profile", mock_extract),
            patch("app.api.chat.async_session_factory", mock_factory),
        ):
            resp = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": "je fais du recyclage à Abidjan avec 15 employés"},
            )

        assert resp.status_code == 200

        events = []
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass

        event_types = [e.get("type") for e in events]
        assert "token" in event_types
        assert "done" in event_types
        assert "profile_update" in event_types
        assert "profile_completion" in event_types

        profile_updates = [e for e in events if e.get("type") == "profile_update"]
        assert any(e.get("field") == "sector" for e in profile_updates)

    @pytest.mark.asyncio
    async def test_generic_message_no_profile_events(
        self, client: AsyncClient
    ) -> None:
        """Un message générique ne génère pas d'events profil."""
        _, headers = await _register_and_login(client)

        resp = await client.post(
            "/api/chat/conversations",
            headers=headers,
            json={"title": "Test generic"},
        )
        conv_id = resp.json()["id"]

        async def mock_stream(content, conversation_id, user_profile=None, context_memory=None):
            yield "Bonjour"

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=lambda m: setattr(m, "id", uuid.uuid4()))
        mock_session.commit = AsyncMock()

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def mock_factory():
            yield mock_session

        with (
            patch("app.api.chat.stream_llm_tokens", side_effect=mock_stream),
            patch("app.api.chat.async_session_factory", mock_factory),
        ):
            resp = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": "Bonjour, comment allez-vous ?"},
            )

        events = []
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass

        event_types = [e.get("type") for e in events]
        assert "profile_update" not in event_types
        assert "token" in event_types
