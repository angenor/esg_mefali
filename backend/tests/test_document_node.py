"""Tests unitaires du document_node LangGraph (T025)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


@pytest.fixture
def sample_state():
    """State de base avec upload document."""
    return {
        "messages": [HumanMessage(content="Voici mon bilan financier")],
        "user_profile": {"company_name": "Test SARL"},
        "context_memory": [],
        "profile_updates": None,
        "profiling_instructions": None,
        "document_upload": {
            "document_id": str(uuid.uuid4()),
            "filename": "bilan_2024.pdf",
            "user_id": str(uuid.uuid4()),
        },
        "document_analysis_summary": None,
    }


@pytest.fixture
def state_without_document():
    """State sans upload document."""
    return {
        "messages": [HumanMessage(content="Bonjour")],
        "user_profile": None,
        "context_memory": [],
        "profile_updates": None,
        "profiling_instructions": None,
        "document_upload": None,
        "document_analysis_summary": None,
    }


@pytest.mark.asyncio
async def test_router_detects_document_upload(sample_state):
    """Le router doit detecter la presence d'un document upload."""
    from app.graph.nodes import router_node

    result = await router_node(sample_state)
    assert result.get("has_document") is True


@pytest.mark.asyncio
async def test_router_no_document(state_without_document):
    """Le router ne detecte pas de document quand il n'y en a pas."""
    from app.graph.nodes import router_node

    result = await router_node(state_without_document)
    assert result.get("has_document") is not True


@pytest.mark.asyncio
async def test_document_node_analyzes_document(sample_state):
    """Le document_node doit analyser le document et injecter le resume."""
    from app.graph.nodes import document_node

    mock_analysis = MagicMock()
    mock_analysis.summary = "Resume du bilan financier 2024"
    mock_analysis.key_findings = ["CA de 500M XOF"]
    mock_analysis.esg_relevant_info = MagicMock()
    mock_analysis.esg_relevant_info.model_dump.return_value = {
        "environmental": [],
        "social": [],
        "governance": [],
    }
    mock_analysis.document_type = MagicMock()
    mock_analysis.document_type.value = "bilan_financier"
    mock_analysis.structured_data = {"chiffre_affaires": 500000000}

    mock_doc = MagicMock()
    mock_doc.id = uuid.uuid4()
    mock_doc.status = "analyzed"

    with patch(
        "app.graph.nodes.analyze_document_for_chat",
        new_callable=AsyncMock,
        return_value=(mock_doc, mock_analysis),
    ):
        result = await document_node(sample_state)

    assert result["document_analysis_summary"] is not None
    assert "Resume du bilan financier" in result["document_analysis_summary"]


@pytest.mark.asyncio
async def test_document_node_handles_error(sample_state):
    """Le document_node gere les erreurs d'analyse gracieusement."""
    from app.graph.nodes import document_node

    with patch(
        "app.graph.nodes.analyze_document_for_chat",
        new_callable=AsyncMock,
        side_effect=Exception("Erreur d'analyse"),
    ):
        result = await document_node(sample_state)

    assert result["document_analysis_summary"] is not None
    assert "erreur" in result["document_analysis_summary"].lower()
