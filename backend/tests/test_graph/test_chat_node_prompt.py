"""Tests du prompt système construit par chat_node.

BUG-V2-001 + BUG-V2-002 : verifier que le prompt contient
- la puce « reponse textuelle visible apres tool call »
- un rappel linguistique francais en fin de prompt
- LANGUAGE_INSTRUCTION toujours present en tete (non-regression)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.nodes import chat_node
from app.graph.state import ConversationState


def _make_state(**overrides) -> ConversationState:
    """State minimal pour chat_node."""
    defaults: dict = {
        "messages": [HumanMessage(content="Bonjour")],
        "user_id": "test-user-id",
        "user_profile": {"sector": "agriculture", "city": "Dakar"},
        "context_memory": [],
        "profile_updates": None,
        "profiling_instructions": None,
        "document_upload": None,
        "document_analysis_summary": None,
        "has_document": False,
        "esg_assessment": None,
        "_route_esg": False,
        "carbon_data": None,
        "_route_carbon": False,
        "financing_data": None,
        "_route_financing": False,
        "application_data": None,
        "_route_application": False,
        "credit_data": None,
        "_route_credit": False,
        "action_plan_data": None,
        "_route_action_plan": False,
        "tool_call_count": 0,
        "active_module": None,
        "active_module_data": None,
        "current_page": None,
        "guidance_stats": None,
    }
    defaults.update(overrides)
    return defaults  # type: ignore[return-value]


async def _capture_system_prompt(state: ConversationState) -> str:
    """Invoque chat_node avec un LLM mocke et retourne le contenu du SystemMessage."""
    captured: dict = {}

    async def fake_ainvoke(messages, **kwargs):
        captured["messages"] = messages
        return AIMessage(content="ok")

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_llm.ainvoke = AsyncMock(side_effect=fake_ainvoke)

    with patch("app.graph.nodes.get_llm", return_value=mock_llm):
        await chat_node(state)

    messages = captured.get("messages") or []
    sys_messages = [m for m in messages if isinstance(m, SystemMessage)]
    assert sys_messages, "chat_node doit injecter un SystemMessage en tete"
    return sys_messages[0].content  # type: ignore[return-value]


# ── BUG-V2-002 : post-tool reminder ────────────────────────────────────


class TestPostToolReminder:
    @pytest.mark.asyncio
    async def test_chat_node_prompt_contains_post_tool_reminder(self) -> None:
        """Le prompt doit forcer une reponse textuelle apres tool call."""
        prompt = await _capture_system_prompt(_make_state())
        assert "Après avoir utilisé un outil" in prompt
        assert "réponse textuelle visible" in prompt
        assert "Ne laisse jamais ta réponse vide" in prompt


# ── BUG-V2-001 : language reminder en fin de prompt ────────────────────


class TestLanguageReminderTail:
    @pytest.mark.asyncio
    async def test_chat_node_prompt_ends_with_language_reminder(self) -> None:
        """Le prompt doit se terminer par un rappel linguistique francais."""
        prompt = await _capture_system_prompt(_make_state())
        # Prendre les 500 derniers caracteres pour verifier la position finale
        tail = prompt[-500:]
        assert "RAPPEL FINAL" in tail
        assert "français" in tail
        # Interdiction explicite du chinois dans le rappel
        assert "chinois" in tail


# ── Non-regression : LANGUAGE_INSTRUCTION en tete via build_system_prompt ──


class TestLanguageInstructionHead:
    @pytest.mark.asyncio
    async def test_chat_node_prompt_language_instruction_still_at_head(self) -> None:
        """LANGUAGE_INSTRUCTION doit rester en tete (non-regression)."""
        prompt = await _capture_system_prompt(_make_state())
        # Les 200 premiers caracteres contiennent l'instruction de tete
        head = prompt[:300]
        assert "LANGUE OBLIGATOIRE" in head
        assert "TOUJOURS répondre en français" in head
