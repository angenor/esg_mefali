"""Tests du financing_node LangGraph (US6)."""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes import _detect_financing_request, _FINANCING_PATTERNS
from tests.conftest import make_conversation_state


class TestFinancingDetection:
    """Tests de detection d'intention financement."""

    def test_detect_financement_vert(self):
        assert _detect_financing_request("Comment obtenir un financement vert ?")

    def test_detect_fonds_vert(self):
        assert _detect_financing_request("Quels sont les fonds verts disponibles ?")

    def test_detect_sunref(self):
        assert _detect_financing_request("Comment acceder au SUNREF ?")

    def test_detect_gcf(self):
        assert _detect_financing_request("Le GCF finance-t-il l'agriculture ?")

    def test_detect_intermediaire(self):
        assert _detect_financing_request("Quel intermediaire contacter pour le BOAD ?")

    def test_detect_credit_carbone(self):
        assert _detect_financing_request("Comment vendre du credit carbone ?")

    def test_detect_banque_partenaire(self):
        assert _detect_financing_request("Quelle banque partenaire pour SUNREF en CI ?")

    def test_detect_dossier_candidature(self):
        assert _detect_financing_request("Comment preparer mon dossier de candidature ?")

    def test_detect_subvention(self):
        assert _detect_financing_request("Y a-t-il une subvention climat ?")

    def test_no_detect_bonjour(self):
        assert not _detect_financing_request("Bonjour, comment allez-vous ?")

    def test_no_detect_esg(self):
        # Les mots ESG sans contexte financement ne devraient pas trigger
        assert not _detect_financing_request("Mon score ESG est de 65")

    def test_no_detect_carbone_seul(self):
        # "carbone" seul sans contexte financement
        assert not _detect_financing_request("Mon empreinte carbone est elevee")


@pytest.mark.asyncio
async def test_financing_node_generates_response():
    """Le financing_node genere une reponse avec des blocs visuels."""
    from langchain_core.messages import AIMessage, HumanMessage

    mock_response = AIMessage(
        content=(
            "Voici les fonds recommandes pour votre profil :\n\n"
            "```table\n"
            '{"headers":["Fonds","Score","Acces"],"rows":[["SUNREF","78%","Via banque"]]}\n'
            "```\n\n"
            "Pour acceder au SUNREF :\n\n"
            "```mermaid\n"
            "graph TD\n"
            "  A[PME] --> B[Banque partenaire]\n"
            "  B --> C[SUNREF/AFD]\n"
            "```"
        )
    )

    with (
        patch("app.graph.nodes.get_llm") as mock_llm_factory,
        patch("app.graph.nodes._fetch_rag_context_for_financing", new_callable=AsyncMock, return_value=""),
    ):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm_factory.return_value = mock_llm

        from app.graph.nodes import financing_node

        state = make_conversation_state(
            messages=[HumanMessage(content="Comment acceder au financement SUNREF ?")],
            user_profile={"sector": "agriculture", "city": "Abidjan"},
            financing_data=None,
            _route_financing=True,
        )

        result = await financing_node(state)

    assert "messages" in result
    response_text = result["messages"][0].content
    assert "SUNREF" in response_text
    assert "table" in response_text or "mermaid" in response_text


@pytest.mark.asyncio
async def test_financing_node_without_esg_redirects():
    """Le financing_node redirige vers ESG si pas de score disponible."""
    from langchain_core.messages import AIMessage, HumanMessage

    mock_response = AIMessage(
        content=(
            "Je remarque que vous n'avez pas encore de score ESG. "
            "Pour vous recommander les meilleurs financements, je vous conseille "
            "de realiser d'abord votre evaluation ESG sur la page /esg."
        )
    )

    with (
        patch("app.graph.nodes.get_llm") as mock_llm_factory,
        patch("app.graph.nodes._fetch_rag_context_for_financing", new_callable=AsyncMock, return_value=""),
    ):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm_factory.return_value = mock_llm

        from app.graph.nodes import financing_node

        state = make_conversation_state(
            messages=[HumanMessage(content="Quels financements pour moi ?")],
            user_profile={"sector": "agriculture"},
            financing_data=None,
            _route_financing=True,
        )

        result = await financing_node(state)

    assert "messages" in result
