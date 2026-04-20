"""Tests pour le tool LangChain create_project (Story 10.2 AC5, AC8)."""

from __future__ import annotations

import uuid

import pytest

from app.graph.tools.projects_tools import PROJECTS_TOOLS


def test_create_project_tool_is_wrapped_with_retry():
    """Test 12 — enforcement CQ-11 : le tool porte la sentinelle with_retry."""
    assert len(PROJECTS_TOOLS) == 1
    tool = PROJECTS_TOOLS[0]
    assert tool.name == "create_project"
    assert getattr(tool, "_is_wrapped_by_with_retry", False) is True


@pytest.mark.asyncio
async def test_create_project_tool_returns_skeleton_message(db_session):
    """Test 13 — invocation retourne le message squelette Epic 11."""
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hash",
        full_name="Test",
        company_name="Test Co",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    config = {
        "configurable": {
            "db": db_session,
            "user_id": user.id,
            "conversation_id": None,
            "active_module": "project",
        }
    }

    tool = PROJECTS_TOOLS[0]
    result = await tool.ainvoke({"name": "Ferme solaire", "state": "idée"}, config=config)

    assert "non encore implémenté" in result
    assert "Epic 11" in result
