"""Tests pour le parsing et la transmission du Form field `guidance_stats`.

Story 6.4 — frequence adaptative (FR17). Couvre :
  1. Helper pur `_parse_guidance_stats(raw: str | None)` → fallback None sur anomalie.
  2. Endpoint `POST /api/chat/conversations/{id}/messages` → le Form field est
     correctement parse et injecte dans `ConversationState["guidance_stats"]`.

Review 6.4 P1 + P2 : tests deplaces sous `test_api/` + ajout de tests
endpoint-level via `httpx.AsyncClient` (pas seulement le helper).
"""

import uuid
from unittest.mock import patch

from httpx import AsyncClient

from app.api.chat import _parse_guidance_stats
from tests.conftest import make_unique_email


# ─── Helpers ──────────────────────────────────────────────────────────


async def _create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Creer un utilisateur et retourner ses donnees + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Amadou Diallo",
        "company_name": "EcoSolaire SARL",
    }
    await client.post("/api/auth/register", json=data)
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    return data, login_resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_conversation(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/chat/conversations",
        json={},
        headers=_auth_headers(token),
    )
    return resp.json()["id"]


# ─── Helper pur ───────────────────────────────────────────────────────


class TestParseGuidanceStats:
    """Helper pur de parsing du Form field guidance_stats."""

    def test_returns_none_when_field_absent(self) -> None:
        assert _parse_guidance_stats(None) is None

    def test_returns_none_when_field_empty_string(self) -> None:
        assert _parse_guidance_stats("") is None

    def test_parses_valid_json_payload(self) -> None:
        result = _parse_guidance_stats('{"refusal_count":3,"acceptance_count":2}')
        assert result == {"refusal_count": 3, "acceptance_count": 2}

    def test_returns_none_when_invalid_json(self) -> None:
        assert _parse_guidance_stats("not-json") is None
        assert _parse_guidance_stats("{broken") is None

    def test_returns_none_when_not_a_dict(self) -> None:
        assert _parse_guidance_stats("[1, 2, 3]") is None
        assert _parse_guidance_stats('"string"') is None
        assert _parse_guidance_stats("42") is None

    def test_returns_none_when_negative_values(self) -> None:
        assert _parse_guidance_stats(
            '{"refusal_count":-1,"acceptance_count":0}'
        ) is None
        assert _parse_guidance_stats(
            '{"refusal_count":0,"acceptance_count":-5}'
        ) is None

    def test_returns_none_when_non_integer_values(self) -> None:
        assert _parse_guidance_stats(
            '{"refusal_count":"3","acceptance_count":2}'
        ) is None
        assert _parse_guidance_stats(
            '{"refusal_count":3.5,"acceptance_count":2}'
        ) is None
        assert _parse_guidance_stats(
            '{"refusal_count":null,"acceptance_count":0}'
        ) is None

    def test_returns_none_when_missing_keys(self) -> None:
        assert _parse_guidance_stats('{"refusal_count":3}') is None
        assert _parse_guidance_stats('{"acceptance_count":2}') is None
        assert _parse_guidance_stats("{}") is None

    def test_accepts_zero_values(self) -> None:
        assert _parse_guidance_stats(
            '{"refusal_count":0,"acceptance_count":0}'
        ) == {"refusal_count": 0, "acceptance_count": 0}

    def test_rejects_boolean_masquerading_as_int(self) -> None:
        # True vaut 1, False vaut 0 — pour eviter tout ambiguite de type,
        # on rejette explicitement les booleens cote helper.
        assert _parse_guidance_stats(
            '{"refusal_count":true,"acceptance_count":false}'
        ) is None

    # Review 6.4 P8 — cap MAX_STATS_CAP

    def test_clamps_values_above_max_stats_cap(self) -> None:
        """Valeurs > MAX_STATS_CAP sont clampees au plafond (defense en profondeur)."""
        result = _parse_guidance_stats(
            '{"refusal_count":9999999,"acceptance_count":9999999}'
        )
        assert result is not None
        assert result["refusal_count"] <= 5
        assert result["acceptance_count"] <= 5

    # Review 6.4 P11 — cap longueur brute avant json.loads

    def test_returns_none_when_raw_payload_too_long(self) -> None:
        """Un payload brut > 500 chars est rejete avant json.loads (protection CPU)."""
        huge = '{"refusal_count":1,"acceptance_count":1,"pad":"' + "x" * 1000 + '"}'
        assert _parse_guidance_stats(huge) is None


# ─── Endpoint-level (review 6.4 P2) ──────────────────────────────────


class TestGuidanceStatsEndpoint:
    """Tests POST /api/chat/conversations/{id}/messages avec guidance_stats.

    Verifie que le Form field est correctement parse et injecte dans
    `ConversationState["guidance_stats"]` via `stream_graph_events`.
    """

    async def test_post_messages_parses_guidance_stats_form_field(
        self, client: AsyncClient
    ) -> None:
        """guidance_stats valide → injecte dans initial_state du graphe."""
        _, token = await _create_authenticated_user(client)
        conv_id = await _create_conversation(client, token)

        captured: dict = {}

        async def _capture_stream(**kwargs):
            captured["guidance_stats"] = kwargs.get("guidance_stats")
            if False:
                yield  # generator signature

        with patch("app.api.chat.stream_graph_events", side_effect=_capture_stream):
            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={
                    "content": "Bonjour",
                    "guidance_stats": '{"refusal_count":3,"acceptance_count":1}',
                },
                headers=_auth_headers(token),
            )

        assert response.status_code == 200
        assert captured["guidance_stats"] == {"refusal_count": 3, "acceptance_count": 1}

    async def test_post_messages_without_guidance_stats_sets_none(
        self, client: AsyncClient
    ) -> None:
        """Absence du Form field → guidance_stats=None (backward-compat)."""
        _, token = await _create_authenticated_user(client)
        conv_id = await _create_conversation(client, token)

        captured: dict = {}

        async def _capture_stream(**kwargs):
            captured["guidance_stats"] = kwargs.get("guidance_stats")
            if False:
                yield

        with patch("app.api.chat.stream_graph_events", side_effect=_capture_stream):
            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={"content": "Bonjour"},
                headers=_auth_headers(token),
            )

        assert response.status_code == 200
        assert captured["guidance_stats"] is None

    async def test_post_messages_invalid_guidance_stats_json_fallback_none(
        self, client: AsyncClient
    ) -> None:
        """JSON invalide → fallback silencieux, pas de HTTP 500."""
        _, token = await _create_authenticated_user(client)
        conv_id = await _create_conversation(client, token)

        captured: dict = {}

        async def _capture_stream(**kwargs):
            captured["guidance_stats"] = kwargs.get("guidance_stats")
            if False:
                yield

        with patch("app.api.chat.stream_graph_events", side_effect=_capture_stream):
            response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                data={
                    "content": "Bonjour",
                    "guidance_stats": "not-valid-json",
                },
                headers=_auth_headers(token),
            )

        assert response.status_code == 200
        assert captured["guidance_stats"] is None
