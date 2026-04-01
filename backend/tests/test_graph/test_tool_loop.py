"""Tests pour la fonction create_tool_loop() et la boucle conditionnelle."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from app.graph.graph import MAX_TOOL_CALLS_PER_TURN, _should_continue_tool_loop


@tool
def dummy_tool(message: str) -> str:
    """Outil de test."""
    return f"OK: {message}"


class TestShouldContinueToolLoop:
    """Tests pour _should_continue_tool_loop()."""

    def test_no_messages_returns_end(self):
        """Pas de messages → end."""
        state = {"messages": [], "tool_call_count": 0}
        assert _should_continue_tool_loop(state) == "end"

    def test_ai_message_without_tool_calls_returns_end(self):
        """Message AI sans tool_calls → end."""
        state = {
            "messages": [AIMessage(content="Bonjour")],
            "tool_call_count": 0,
        }
        assert _should_continue_tool_loop(state) == "end"

    def test_ai_message_with_tool_calls_returns_continue(self):
        """Message AI avec tool_calls et compteur < max → continue."""
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"id": "call_1", "name": "dummy_tool", "args": {"message": "test"}}],
        )
        state = {"messages": [ai_msg], "tool_call_count": 0}
        assert _should_continue_tool_loop(state) == "continue"

    def test_tool_call_count_at_max_returns_end(self):
        """Compteur au plafond → end même avec tool_calls."""
        ai_msg = AIMessage(
            content="",
            tool_calls=[{"id": "call_1", "name": "dummy_tool", "args": {"message": "test"}}],
        )
        state = {"messages": [ai_msg], "tool_call_count": MAX_TOOL_CALLS_PER_TURN}
        assert _should_continue_tool_loop(state) == "end"

    def test_human_message_returns_end(self):
        """Dernier message est HumanMessage → end."""
        state = {
            "messages": [HumanMessage(content="hello")],
            "tool_call_count": 0,
        }
        assert _should_continue_tool_loop(state) == "end"

    def test_tool_message_returns_end(self):
        """Dernier message est ToolMessage → end."""
        state = {
            "messages": [ToolMessage(content="result", tool_call_id="call_1")],
            "tool_call_count": 0,
        }
        assert _should_continue_tool_loop(state) == "end"
