"""Tests du carbon_node et de la detection d'intent carbone (T015).

Verifie le routage, la progression par categories, et la generation de visualisations.
"""

import pytest

from app.graph.nodes import _detect_carbon_request, _has_active_carbon_assessment


class TestCarbonIntentDetection:
    """Tests de la detection d'intent carbone."""

    @pytest.mark.parametrize("message", [
        "Je veux faire mon bilan carbone",
        "Calculer mon empreinte carbone",
        "Quel est mon impact carbone ?",
        "Je voudrais connaitre mes emissions de gaz a effet de serre",
        "Combien de tCO2e j'emets ?",
        "Mon empreinte ecologique",
        "reduction des emissions",
    ])
    def test_detect_carbon_request_positive(self, message: str) -> None:
        """T015-01 : Detection positive des requetes carbone."""
        assert _detect_carbon_request(message) is True

    @pytest.mark.parametrize("message", [
        "Bonjour, comment allez-vous ?",
        "Je veux mon score ESG",
        "Quels fonds verts sont disponibles ?",
        "Aidez-moi avec mon dossier",
        "Quelle est la meteo ?",
    ])
    def test_detect_carbon_request_negative(self, message: str) -> None:
        """T015-02 : Pas de detection pour messages non-carbone."""
        assert _detect_carbon_request(message) is False

    def test_has_active_carbon_assessment_true(self) -> None:
        """T015-03 : Detection d'un bilan carbone actif."""
        state = {"carbon_data": {"status": "in_progress", "assessment_id": "abc"}}
        assert _has_active_carbon_assessment(state) is True

    def test_has_active_carbon_assessment_false_completed(self) -> None:
        """T015-04 : Bilan complete n'est pas actif."""
        state = {"carbon_data": {"status": "completed", "assessment_id": "abc"}}
        assert _has_active_carbon_assessment(state) is False

    def test_has_active_carbon_assessment_false_none(self) -> None:
        """T015-05 : Pas de carbon_data."""
        state = {}
        assert _has_active_carbon_assessment(state) is False


class TestCarbonNodeHelpers:
    """Tests des helpers du carbon_node."""

    def test_build_initial_carbon_state_services(self) -> None:
        """T015-06 : Etat initial pour secteur services (3 categories)."""
        from app.modules.carbon.service import build_initial_carbon_state

        state = build_initial_carbon_state("test-id", sector="services")
        assert state["applicable_categories"] == ["energy", "transport", "waste"]
        assert state["current_category"] == "energy"

    def test_build_initial_carbon_state_agriculture(self) -> None:
        """T015-07 : Etat initial pour agriculture (4 categories)."""
        from app.modules.carbon.service import build_initial_carbon_state

        state = build_initial_carbon_state("test-id", sector="agriculture")
        assert "agriculture" in state["applicable_categories"]
        assert len(state["applicable_categories"]) == 4

    def test_get_next_category_progression(self) -> None:
        """T015-08 : Progression correcte des categories."""
        from app.modules.carbon.service import get_next_category

        cats = ["energy", "transport", "waste", "agriculture"]
        assert get_next_category("energy", cats) == "transport"
        assert get_next_category("transport", cats) == "waste"
        assert get_next_category("waste", cats) == "agriculture"
        assert get_next_category("agriculture", cats) is None

    def test_get_next_category_unknown(self) -> None:
        """T015-09 : None si categorie inconnue."""
        from app.modules.carbon.service import get_next_category

        assert get_next_category("unknown", ["energy", "transport"]) is None


# === V8-AXE3 : forçage déterministe finalize_carbon_assessment ===


class TestCarbonNodeForceFinalize:
    """Tests runtime : carbon_node injecte un AIMessage(tool_calls=[finalize_carbon_assessment])
    sans appeler le LLM quand l'utilisateur demande explicitement la finalisation et que toutes
    les catégories applicables sont complétées (BUG-V7-006 / BUG-V7.1-005)."""

    @pytest.mark.asyncio
    async def test_carbon_node_forces_finalize_without_calling_llm(self) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        from langchain_core.messages import HumanMessage

        from app.graph.nodes import carbon_node
        from tests.conftest import make_conversation_state

        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data={
                "assessment_id": "11111111-1111-1111-1111-111111111111",
                "status": "in_progress",
                "applicable_categories": ["energy", "transport", "waste"],
                "completed_categories": ["energy", "transport", "waste"],
                "current_category": "waste",
                "entries": [],
                "total_emissions_tco2e": 12.5,
                "sector": "services",
                "year": 2026,
            },
            user_profile={"company_name": "Test", "sector": "services"},
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            result = await carbon_node(state)

            # Le LLM ne doit JAMAIS être invoqué quand le forçage déclenche.
            mock_llm.ainvoke.assert_not_called()

        assert "messages" in result and len(result["messages"]) == 1
        forced = result["messages"][0]
        assert hasattr(forced, "tool_calls") and forced.tool_calls
        assert forced.tool_calls[0]["name"] == "finalize_carbon_assessment"
        assert forced.tool_calls[0]["args"] == {"assessment_id": "11111111-1111-1111-1111-111111111111"}
        assert result["active_module"] == "carbon"
        # F1 (review V8-AXE3) : compteur de tool_call incrémenté.
        assert result["tool_call_count"] == 1

    @pytest.mark.asyncio
    async def test_carbon_node_no_force_when_categories_incomplete(self) -> None:
        """Pas de forçage si completed_categories incomplet → comportement normal (LLM appelé)."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from langchain_core.messages import AIMessage, HumanMessage

        from app.graph.nodes import carbon_node
        from tests.conftest import make_conversation_state

        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data={
                "assessment_id": "11111111-1111-1111-1111-111111111111",
                "status": "in_progress",
                "applicable_categories": ["energy", "transport", "waste"],
                "completed_categories": ["energy"],  # incomplet
                "current_category": "transport",
                "entries": [],
                "total_emissions_tco2e": 0.0,
                "sector": "services",
                "year": 2026,
            },
            user_profile={"company_name": "Test", "sector": "services"},
        )

        with patch("app.graph.nodes.get_llm") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="Il manque transport et waste avant de finaliser."
            ))
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm_fn.return_value = mock_llm

            result = await carbon_node(state)

            # Le LLM DOIT être appelé (comportement normal préservé).
            mock_llm.ainvoke.assert_called_once()

        # La réponse vient du LLM (pas un AIMessage avec tool_calls forcé).
        forced_or_text = result["messages"][0]
        assert not getattr(forced_or_text, "tool_calls", None)
