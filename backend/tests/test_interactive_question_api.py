"""Tests d'integration des endpoints REST interactive_questions (feature 018)."""

from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import make_unique_email, test_session_factory


pytestmark = pytest.mark.asyncio


async def _create_user_and_token(client: AsyncClient) -> tuple[dict, str]:
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Test User",
        "company_name": "Test Co",
    }
    await client.post("/api/auth/register", json=data)
    login = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    return data, login.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_conversation(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/chat/conversations",
        json={"title": "Test"},
        headers=_headers(token),
    )
    return resp.json()["id"]


async def _seed_pending_question(
    conversation_id: str,
    *,
    question_type: str = "qcu",
    requires_justification: bool = False,
    options: list[dict] | None = None,
    min_selections: int = 1,
    max_selections: int = 1,
) -> str:
    """Inserer directement une question pending en BDD pour le test."""
    from app.models.interactive_question import (
        InteractiveQuestion,
        InteractiveQuestionState,
    )

    async with test_session_factory() as db:
        q = InteractiveQuestion(
            conversation_id=uuid.UUID(conversation_id),
            module="profiling",
            question_type=question_type,
            prompt="Test question ?",
            options=options or [
                {"id": "a", "label": "Option A"},
                {"id": "b", "label": "Option B"},
                {"id": "c", "label": "Option C"},
            ],
            min_selections=min_selections,
            max_selections=max_selections,
            requires_justification=requires_justification,
            justification_prompt="Pourquoi ?" if requires_justification else None,
            state=InteractiveQuestionState.PENDING.value,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return str(q.id)


# ─── GET /interactive-questions ──────────────────────────────────────


async def test_list_interactive_questions_empty(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    conv_id = await _create_conversation(client, token)
    resp = await client.get(
        f"/api/chat/conversations/{conv_id}/interactive-questions",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []


async def test_list_interactive_questions_with_data(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    conv_id = await _create_conversation(client, token)
    qid = await _seed_pending_question(conv_id)

    resp = await client.get(
        f"/api/chat/conversations/{conv_id}/interactive-questions",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == qid
    assert items[0]["state"] == "pending"


async def test_list_interactive_questions_filter_state(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    conv_id = await _create_conversation(client, token)
    await _seed_pending_question(conv_id)
    resp = await client.get(
        f"/api/chat/conversations/{conv_id}/interactive-questions?state=answered",
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_list_interactive_questions_forbidden_for_other_user(
    client: AsyncClient,
):
    _, token_a = await _create_user_and_token(client)
    _, token_b = await _create_user_and_token(client)
    conv_id_a = await _create_conversation(client, token_a)

    resp = await client.get(
        f"/api/chat/conversations/{conv_id_a}/interactive-questions",
        headers=_headers(token_b),
    )
    assert resp.status_code == 404  # get_user_conversation lance 404 si pas owner


# ─── POST /interactive-questions/{id}/abandon ───────────────────────


async def test_abandon_question_valid(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    conv_id = await _create_conversation(client, token)
    qid = await _seed_pending_question(conv_id)

    resp = await client.post(
        f"/api/chat/interactive-questions/{qid}/abandon",
        headers=_headers(token),
        json={},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["state"] == "abandoned"


async def test_abandon_unknown_returns_404(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/chat/interactive-questions/{fake_id}/abandon",
        headers=_headers(token),
        json={},
    )
    assert resp.status_code == 404


async def test_abandon_already_answered_returns_409(client: AsyncClient):
    _, token = await _create_user_and_token(client)
    conv_id = await _create_conversation(client, token)
    qid = await _seed_pending_question(conv_id)

    # Premier abandon : OK
    await client.post(
        f"/api/chat/interactive-questions/{qid}/abandon",
        headers=_headers(token),
        json={},
    )
    # Second abandon : 409
    resp = await client.post(
        f"/api/chat/interactive-questions/{qid}/abandon",
        headers=_headers(token),
        json={},
    )
    assert resp.status_code == 409


async def test_abandon_forbidden_other_user(client: AsyncClient):
    _, token_a = await _create_user_and_token(client)
    _, token_b = await _create_user_and_token(client)
    conv_id_a = await _create_conversation(client, token_a)
    qid = await _seed_pending_question(conv_id_a)

    resp = await client.post(
        f"/api/chat/interactive-questions/{qid}/abandon",
        headers=_headers(token_b),
        json={},
    )
    assert resp.status_code == 403
