"""Tests pour le mapping d'événements LangGraph → SSE dans stream_graph_events()."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.chat import stream_graph_events


class MockChunk:
    """Simule un chunk de streaming LLM."""

    def __init__(self, content: str):
        self.content = content


@pytest.mark.asyncio
async def test_stream_without_compiled_graph():
    """Si le graphe n'est pas compilé, retourne une erreur."""
    with patch("app.main.compiled_graph", None):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "indisponible" in events[0]["content"]


@pytest.mark.asyncio
async def test_stream_token_events():
    """Les événements on_chat_model_stream sont mappés en tokens SSE."""
    mock_graph = AsyncMock()

    async def mock_astream_events(state, config, version):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MockChunk("Bonjour")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MockChunk(" monde")}}

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        assert len(events) == 2
        assert events[0] == {"type": "token", "content": "Bonjour"}
        assert events[1] == {"type": "token", "content": " monde"}


@pytest.mark.asyncio
async def test_stream_tool_call_events():
    """Les événements on_tool_start/end sont mappés en tool_call_start/end SSE."""
    mock_graph = AsyncMock()

    async def mock_astream_events(state, config, version):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MockChunk("Je sauvegarde")}}
        yield {
            "event": "on_tool_start",
            "name": "update_company_profile",
            "data": {"input": {"sector": "agriculture"}},
            "run_id": "call_abc",
        }
        yield {
            "event": "on_tool_end",
            "name": "update_company_profile",
            "data": {"output": "Profil mis à jour"},
            "run_id": "call_abc",
        }
        yield {"event": "on_chat_model_stream", "data": {"chunk": MockChunk(" votre profil")}}

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="je suis dans l'agriculture",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        assert len(events) == 4
        assert events[0]["type"] == "token"
        assert events[1]["type"] == "tool_call_start"
        assert events[1]["tool_name"] == "update_company_profile"
        assert events[2]["type"] == "tool_call_end"
        assert events[2]["success"] is True
        assert events[3]["type"] == "token"


@pytest.mark.asyncio
async def test_stream_profile_tool_emits_sse_metadata():
    """Un tool_call_end avec métadonnées <!--SSE:...--> émet profile_update/completion."""
    import json

    mock_graph = AsyncMock()
    sse_metadata = json.dumps({
        "__sse_profile__": True,
        "changed_fields": [
            {"field": "sector", "value": "agriculture", "label": "Secteur"},
            {"field": "city", "value": "Bouaké", "label": "Ville"},
        ],
        "completion": {
            "identity_completion": 37.5,
            "esg_completion": 0.0,
            "overall_completion": 18.8,
        },
    })
    tool_output = f"Profil mis à jour\n<!--SSE:{sse_metadata}-->"

    async def mock_astream_events(state, config, version):
        yield {
            "event": "on_tool_end",
            "name": "update_company_profile",
            "data": {"output": tool_output},
            "run_id": "call_profile",
        }

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        event_types = [e["type"] for e in events]
        assert "tool_call_end" in event_types
        assert "profile_update" in event_types
        assert "profile_completion" in event_types

        # Vérifier le contenu des events profil
        profile_updates = [e for e in events if e["type"] == "profile_update"]
        assert len(profile_updates) == 2
        assert profile_updates[0]["field"] == "sector"
        assert profile_updates[0]["value"] == "agriculture"
        assert profile_updates[1]["field"] == "city"

        completion = next(e for e in events if e["type"] == "profile_completion")
        assert completion["identity_completion"] == 37.5
        assert completion["overall_completion"] == 18.8


@pytest.mark.asyncio
async def test_stream_guided_tour_marker():
    """Un tool_call_end avec __sse_guided_tour__ émet un event guided_tour SSE."""
    import json

    mock_graph = AsyncMock()
    sse_metadata = json.dumps({
        "__sse_guided_tour__": True,
        "type": "guided_tour",
        "tour_id": "show_esg_results",
        "context": {"score": 72},
    })
    tool_output = f"Parcours guide 'show_esg_results' declenche.\n\n<!--SSE:{sse_metadata}-->"

    async def mock_astream_events(state, config, version):
        yield {
            "event": "on_tool_end",
            "name": "trigger_guided_tour",
            "data": {"output": tool_output},
            "run_id": "call_tour",
        }

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        event_types = [e["type"] for e in events]
        assert "tool_call_end" in event_types
        assert "guided_tour" in event_types

        tour_event = next(e for e in events if e["type"] == "guided_tour")
        assert tour_event["tour_id"] == "show_esg_results"
        assert tour_event["context"] == {"score": 72}
        # Le flag __sse_guided_tour__ ne doit PAS etre dans le payload emis
        assert "__sse_guided_tour__" not in tour_event


@pytest.mark.asyncio
async def test_stream_guided_tour_without_context():
    """Un event guided_tour avec context vide est emis correctement."""
    import json

    mock_graph = AsyncMock()
    sse_metadata = json.dumps({
        "__sse_guided_tour__": True,
        "type": "guided_tour",
        "tour_id": "show_dashboard_overview",
        "context": {},
    })
    tool_output = f"Parcours guide declenche.\n\n<!--SSE:{sse_metadata}-->"

    async def mock_astream_events(state, config, version):
        yield {
            "event": "on_tool_end",
            "name": "trigger_guided_tour",
            "data": {"output": tool_output},
            "run_id": "call_tour2",
        }

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        tour_event = next(e for e in events if e["type"] == "guided_tour")
        assert tour_event["tour_id"] == "show_dashboard_overview"
        assert tour_event["context"] == {}


@pytest.mark.asyncio
async def test_stream_tool_error_event():
    """Les événements on_tool_error sont mappés en tool_call_error SSE."""
    mock_graph = AsyncMock()

    async def mock_astream_events(state, config, version):
        yield {
            "event": "on_tool_error",
            "name": "update_company_profile",
            "data": {"error": "DB connection failed"},
            "run_id": "call_err",
        }

    mock_graph.astream_events = mock_astream_events

    with patch("app.main.compiled_graph", mock_graph):
        events = []
        async for event in stream_graph_events(
            content="test",
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            db=AsyncMock(),
        ):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "tool_call_error"
        assert events[0]["tool_name"] == "update_company_profile"
        assert "DB connection failed" in events[0]["error_message"]
