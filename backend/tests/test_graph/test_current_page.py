"""Tests Story 3.1 : Transmission de la page courante au backend.

Verifie que current_page est accepte dans ConversationState et
transmis correctement via stream_graph_events.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_conversation_state


class TestConversationStateCurrentPage:
    """AC4, AC5 — current_page dans ConversationState."""

    def test_current_page_accepte_dans_state(self):
        """ConversationState accepte current_page."""
        state = make_conversation_state(current_page="/carbon/results")
        assert state["current_page"] == "/carbon/results"

    def test_current_page_none_par_defaut(self):
        """current_page vaut None par defaut."""
        state = make_conversation_state()
        assert state["current_page"] is None

    def test_coexistence_current_page_et_active_module(self):
        """AC5 — current_page et active_module coexistent sans conflit."""
        state = make_conversation_state(
            active_module="esg_scoring",
            active_module_data={"step": 3},
            current_page="/esg",
        )
        assert state["active_module"] == "esg_scoring"
        assert state["active_module_data"] == {"step": 3}
        assert state["current_page"] == "/esg"

    def test_current_page_dans_initial_state_complet(self):
        """current_page est present dans un state complet avec toutes les cles."""
        state = make_conversation_state()
        assert "current_page" in state
        assert "active_module" in state
        assert "active_module_data" in state


class AsyncIteratorEmpty:
    """Async iterable vide pour mocker astream_events."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class TestStreamGraphEventsCurrentPage:
    """AC4 — current_page transmis a stream_graph_events et present dans initial_state."""

    @pytest.mark.asyncio
    async def test_current_page_dans_initial_state(self):
        """stream_graph_events inclut current_page dans initial_state."""
        captured_state = {}

        async def mock_astream_events(state, *, version=None, config=None, **kwargs):
            captured_state.update(state)
            return
            yield  # noqa: E501 — force async generator

        mock_graph = MagicMock()
        mock_graph.astream_events = mock_astream_events

        with patch("app.main.compiled_graph", mock_graph):
            from app.api.chat import stream_graph_events

            mock_db = AsyncMock()
            async for _ in stream_graph_events(
                content="test",
                conversation_id=str(uuid.uuid4()),
                user_id=uuid.uuid4(),
                db=mock_db,
                current_page="/financing",
            ):
                pass

            assert captured_state.get("current_page") == "/financing"

    @pytest.mark.asyncio
    async def test_current_page_none_par_defaut_dans_stream(self):
        """stream_graph_events passe current_page=None si non fourni."""
        captured_state = {}

        async def mock_astream_events(state, *, version=None, config=None, **kwargs):
            captured_state.update(state)
            return
            yield  # noqa: E501 — force async generator

        mock_graph = MagicMock()
        mock_graph.astream_events = mock_astream_events

        with patch("app.main.compiled_graph", mock_graph):
            from app.api.chat import stream_graph_events

            mock_db = AsyncMock()
            async for _ in stream_graph_events(
                content="test",
                conversation_id=str(uuid.uuid4()),
                user_id=uuid.uuid4(),
                db=mock_db,
            ):
                pass

            assert captured_state.get("current_page") is None


class TestNodesPassCurrentPageToPrompts:
    """Story 3.2 — AC1, AC5 : les noeuds passent current_page aux build_*_prompt."""

    def test_chat_node_build_system_prompt_no_page_context(self):
        """AC1 — build_system_prompt n'injecte plus PAGE_CONTEXT (deplace dans chat_node apres WIDGET)."""
        from app.prompts.system import build_system_prompt

        result = build_system_prompt(current_page="/carbon/results")
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_esg_node_passes_current_page_to_build_esg_prompt(self):
        """AC5 — esg_scoring_node passe current_page a build_esg_prompt."""
        from app.prompts.esg_scoring import build_esg_prompt

        result = build_esg_prompt(current_page="/esg")
        assert "CONTEXTE DE NAVIGATION" in result
        assert "/esg" in result

    def test_node_without_current_page_no_context(self):
        """AC3 — sans current_page, pas de contexte de navigation."""
        from app.prompts.system import build_system_prompt

        result = build_system_prompt()
        assert "CONTEXTE DE NAVIGATION" not in result
