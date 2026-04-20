"""Tests pour le tool LangChain declare_maturity_level (Story 10.3 AC4, AC8)."""

from __future__ import annotations

import uuid

import pytest

from app.graph.tools.maturity_tools import MATURITY_TOOLS


def test_declare_maturity_level_is_wrapped_with_retry():
    """Test 12 — enforcement CQ-11 : sentinelle with_retry + node_name='maturity'."""
    assert len(MATURITY_TOOLS) == 1
    tool = MATURITY_TOOLS[0]
    assert tool.name == "declare_maturity_level"
    assert getattr(tool, "_is_wrapped_by_with_retry", False) is True


@pytest.mark.asyncio
async def test_declare_maturity_level_returns_skeleton_message(db_session):
    """Test 13 — invocation retourne le message squelette Epic 12."""
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
            "active_module": "maturity",
        }
    }

    tool = MATURITY_TOOLS[0]
    result = await tool.ainvoke({"level": "informel"}, config=config)

    assert "non encore implémenté" in result
    assert "Epic 12" in result
