"""Tests du credit_node LangGraph — detection d'intent et generation de blocs visuels."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from tests.conftest import make_conversation_state


# --- Tests detection intent credit ---


class TestDetectCreditRequest:
    """Tests pour la detection des requetes de scoring credit vert."""

    def test_detect_score_credit_vert(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Quel est mon score de credit vert ?")

    def test_detect_scoring_credit(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Je veux mon scoring de credit")

    def test_detect_score_solvabilite(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Mon score de solvabilite")

    def test_detect_note_credit(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Ma note de credit vert")

    def test_detect_attestation_credit(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Je voudrais une attestation de credit")

    def test_detect_generer_score(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert _detect_credit_request("Genere mon score de credit")

    def test_no_false_positive_esg(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert not _detect_credit_request("Quel est mon score ESG ?")

    def test_no_false_positive_carbone(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert not _detect_credit_request("Calcule mon empreinte carbone")

    def test_no_false_positive_financement(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert not _detect_credit_request("Je cherche un financement vert")

    def test_no_false_positive_generic(self) -> None:
        from app.graph.nodes import _detect_credit_request

        assert not _detect_credit_request("Bonjour, comment allez-vous ?")


# --- Tests credit_node ---


class TestCreditNode:
    """Tests pour le noeud credit_node LangGraph."""

    @pytest.mark.asyncio
    async def test_credit_node_generates_visual_blocks(self) -> None:
        """credit_node doit retourner une reponse avec des blocs visuels."""
        from app.graph.nodes import credit_node

        mock_response = AIMessage(content=(
            "Voici votre score de credit vert :\n\n"
            "```gauge\n"
            '{"value": 74.5, "max": 100, "label": "Score Credit Vert"}\n'
            "```\n\n"
            "Votre score combine est de 74.5/100."
        ))

        state = make_conversation_state(
            messages=[HumanMessage(content="Quel est mon score de credit vert ?")],
            user_profile={"company_name": "Entreprise Test", "sector": "agriculture"},
            credit_data=None,
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = (
                    "Score combine: 74.5/100\nSolvabilite: 68.0\nImpact vert: 81.0",
                    [
                        {"version": 3, "combined_score": 74.5, "solvability_score": 68.0,
                         "green_impact_score": 81.0, "generated_at": "2026-03-31T10:00:00"},
                    ],
                )

                result = await credit_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "score" in result["messages"][0].content.lower() or "credit" in result["messages"][0].content.lower()

    @pytest.mark.asyncio
    async def test_credit_node_no_score(self) -> None:
        """credit_node gere l'absence de score genere."""
        from app.graph.nodes import credit_node

        mock_response = AIMessage(content=(
            "Vous n'avez pas encore de score de credit vert. "
            "Rendez-vous sur la page /credit-score pour en generer un."
        ))

        state = make_conversation_state(
            messages=[HumanMessage(content="Mon score de credit vert")],
            user_profile=None,
            credit_data=None,
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = ("Aucun score genere.", [])

                result = await credit_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_credit_node_forces_generate_score_without_calling_llm(self) -> None:
        """V8-AXE3 : credit_node injecte un AIMessage(tool_calls=[generate_credit_score])
        sans appeler le LLM quand l'utilisateur demande explicitement le calcul.

        Régression BUG-V7-008 / BUG-V7.1-010 : le LLM (MiniMax comme Claude) refuse
        d'invoquer generate_credit_score. On force l'appel côté backend."""
        from app.graph.nodes import credit_node

        state = make_conversation_state(
            messages=[HumanMessage(content="évalue ma solvabilité")],
            user_profile={"company_name": "Test", "sector": "agriculture"},
            credit_data=None,
            user_id="user-123",
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = ("Aucun score genere.", [])

                result = await credit_node(state)

                # Le LLM ne doit JAMAIS être invoqué quand le forçage déclenche.
                mock_llm.ainvoke.assert_not_called()

        assert "messages" in result and len(result["messages"]) == 1
        forced = result["messages"][0]
        assert hasattr(forced, "tool_calls") and forced.tool_calls
        assert forced.tool_calls[0]["name"] == "generate_credit_score"
        assert forced.tool_calls[0]["args"] == {}
        assert result["active_module"] == "credit"
        # F1 (review V8-AXE3) : compteur de tool_call incrémenté.
        assert result["tool_call_count"] == 1

    @pytest.mark.asyncio
    async def test_credit_node_no_force_when_informational_question(self) -> None:
        """Question informationnelle → pas de forçage, LLM appelé normalement."""
        from app.graph.nodes import credit_node

        state = make_conversation_state(
            messages=[HumanMessage(content="C'est quoi un score crédit vert ?")],
            user_profile={"company_name": "Test"},
            credit_data=None,
            user_id="user-123",
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="Le score crédit vert mesure votre solvabilité combinée à votre impact environnemental."
            ))
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = ("Aucun score genere.", [])

                result = await credit_node(state)

                # Le LLM DOIT être appelé (comportement normal préservé).
                mock_llm.ainvoke.assert_called_once()

        forced_or_text = result["messages"][0]
        assert not getattr(forced_or_text, "tool_calls", None)

    @pytest.mark.asyncio
    async def test_credit_node_no_force_when_user_id_absent(self) -> None:
        """user_id absent → pas de forçage (le tool échouerait sinon)."""
        from app.graph.nodes import credit_node

        state = make_conversation_state(
            messages=[HumanMessage(content="évalue ma solvabilité")],
            user_profile={"company_name": "Test"},
            credit_data=None,
            user_id=None,
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="Veuillez vous connecter pour obtenir votre score."
            ))
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = ("Aucun score genere.", [])

                result = await credit_node(state)

                # Le LLM DOIT être appelé (comportement normal préservé).
                mock_llm.ainvoke.assert_called_once()

        forced_or_text = result["messages"][0]
        assert not getattr(forced_or_text, "tool_calls", None)

    @pytest.mark.asyncio
    async def test_credit_node_preserves_credit_data(self) -> None:
        """credit_node preserve credit_data dans le state."""
        from app.graph.nodes import credit_node

        mock_response = AIMessage(content="Votre score est de 74.5/100.")
        existing_credit_data = {
            "last_score_id": "abc-123",
            "last_score": 74.5,
            "generating": False,
        }

        state = make_conversation_state(
            messages=[HumanMessage(content="Mon score credit vert")],
            user_profile={"company_name": "Test"},
            credit_data=existing_credit_data,
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            with patch("app.graph.nodes._fetch_credit_scoring_context", new_callable=AsyncMock) as mock_ctx:
                mock_ctx.return_value = ("Score combine: 74.5", [])

                result = await credit_node(state)

        assert result.get("credit_data") == existing_credit_data


# --- Tests routage credit dans router_node ---


class TestRouterNodeCredit:
    """Tests d'integration du routage credit dans router_node."""

    @pytest.mark.asyncio
    async def test_router_routes_to_credit(self) -> None:
        """router_node doit activer _route_credit pour une demande credit."""
        from app.graph.nodes import router_node

        state = make_conversation_state(
            messages=[HumanMessage(content="Quel est mon score de credit vert ?")],
            user_profile={"company_name": "Test"},
        )

        result = await router_node(state)
        assert result.get("_route_credit") is True

    @pytest.mark.asyncio
    async def test_router_no_credit_for_esg(self) -> None:
        """router_node ne doit pas router vers credit pour une demande ESG."""
        from app.graph.nodes import router_node

        state = make_conversation_state(
            messages=[HumanMessage(content="Quel est mon score ESG ?")],
            user_profile={"company_name": "Test"},
        )

        result = await router_node(state)
        assert result.get("_route_credit") is False
