"""Tests V8-AXE3 — forçage déterministe d'invocation de tool dans credit_node et carbon_node.

Couvre les helpers `_should_force_credit_score` et `_should_force_finalize_carbon`
ainsi que les régressions BUG-V7-006, BUG-V7-008, BUG-V7.1-005, BUG-V7.1-010.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.graph.nodes import (
    _FORCE_CARBON_FINALIZE_RE,
    _FORCE_CREDIT_RE,
    _should_force_credit_score,
    _should_force_finalize_carbon,
)
from tests.conftest import make_conversation_state


# === Tests regex pures ===


class TestForceCreditRegex:
    """Vérifie que la regex de forçage credit matche les phrases utilisateur attendues."""

    @pytest.mark.parametrize("text", [
        "évalue ma solvabilité",
        "Evalue ma solvabilité s'il te plaît",
        "calcule mon score crédit",
        "Génère mon score de crédit vert",
        "donne moi mon score crédit",
        "Fais mon score crédit maintenant",
        "Faire le calcul du score crédit",
    ])
    def test_match_positive(self, text: str) -> None:
        assert _FORCE_CREDIT_RE.search(text) is not None

    @pytest.mark.parametrize("text", [
        "C'est quoi un score crédit vert ?",
        "Comment fonctionne la solvabilité ?",
        "Bonjour",
        "Mon empreinte carbone",
        "Je veux faire mon bilan carbone",
        # F5 (review V8-AXE3) : `note` seul ne doit plus matcher.
        "Donne-moi une note de 1 à 10 sur ma stratégie",
    ])
    def test_match_negative(self, text: str) -> None:
        assert _FORCE_CREDIT_RE.search(text) is None


class TestForceCarbonFinalizeRegex:
    """Vérifie que la regex de forçage carbon finalize matche les phrases attendues."""

    @pytest.mark.parametrize("text", [
        "Oui, finalise ce bilan",
        "Finalise mon bilan carbone",
        "Termine le bilan",
        "Valide mon bilan carbone",
        "Confirme la clôture du bilan",
        "Boucle ce bilan",
        "Clôture mon bilan",
    ])
    def test_match_positive(self, text: str) -> None:
        assert _FORCE_CARBON_FINALIZE_RE.search(text) is not None

    @pytest.mark.parametrize("text", [
        "C'est quoi un bilan carbone ?",
        "Combien j'ai d'émissions ?",
        "Bonjour",
        "Évalue ma solvabilité",
        "Je veux finaliser mon dossier de candidature",  # « dossier » pas « bilan »
    ])
    def test_match_negative(self, text: str) -> None:
        assert _FORCE_CARBON_FINALIZE_RE.search(text) is None


# === Tests _should_force_credit_score ===


class TestShouldForceCreditScore:
    """Tests du helper _should_force_credit_score."""

    def test_force_when_match_and_user_id(self) -> None:
        """Scénario I/O Matrix #1 : forçage credit déclenché."""
        state = make_conversation_state(
            user_id="user-123",
            messages=[HumanMessage(content="évalue ma solvabilité")],
        )
        assert _should_force_credit_score(state) is True

    def test_no_force_when_no_user_id(self) -> None:
        """Pré-condition KO : user_id absent → pas de forçage."""
        state = make_conversation_state(
            user_id=None,
            messages=[HumanMessage(content="évalue ma solvabilité")],
        )
        assert _should_force_credit_score(state) is False

    def test_no_force_when_no_match(self) -> None:
        """Question informationnelle → pas de forçage."""
        state = make_conversation_state(
            user_id="user-123",
            messages=[HumanMessage(content="C'est quoi un score crédit vert ?")],
        )
        assert _should_force_credit_score(state) is False

    def test_no_force_when_last_message_not_human(self) -> None:
        """Si le dernier message n'est pas un HumanMessage → pas de forçage."""
        state = make_conversation_state(
            user_id="user-123",
            messages=[
                HumanMessage(content="évalue ma solvabilité"),
                AIMessage(content="OK", tool_calls=[]),
            ],
        )
        assert _should_force_credit_score(state) is False

    def test_no_force_when_messages_empty(self) -> None:
        state = make_conversation_state(user_id="user-123", messages=[])
        assert _should_force_credit_score(state) is False

    def test_no_force_when_tool_already_called_in_turn(self) -> None:
        """Scénario I/O Matrix #5 : tool déjà appelé dans le tour → pas de re-forçage."""
        state = make_conversation_state(
            user_id="user-123",
            messages=[
                HumanMessage(content="évalue ma solvabilité"),
                AIMessage(
                    content="",
                    tool_calls=[{"name": "generate_credit_score", "args": {}, "id": "abc"}],
                ),
                ToolMessage(
                    content='{"status":"success","score":74.5}',
                    name="generate_credit_score",
                    tool_call_id="abc",
                ),
            ],
        )
        # Le dernier message n'est plus un HumanMessage → False direct.
        assert _should_force_credit_score(state) is False

    def test_force_again_in_new_turn(self) -> None:
        """Un appel tool dans un tour précédent ne bloque pas le forçage du nouveau tour."""
        state = make_conversation_state(
            user_id="user-123",
            messages=[
                HumanMessage(content="évalue ma solvabilité"),
                AIMessage(
                    content="",
                    tool_calls=[{"name": "generate_credit_score", "args": {}, "id": "abc"}],
                ),
                ToolMessage(
                    content='{"status":"success"}',
                    name="generate_credit_score",
                    tool_call_id="abc",
                ),
                AIMessage(content="Voici votre score : 74.5/100"),
                HumanMessage(content="calcule à nouveau mon score crédit"),  # nouveau tour
            ],
        )
        assert _should_force_credit_score(state) is True


# === Tests _should_force_finalize_carbon ===


class TestShouldForceFinalizeCarbon:
    """Tests du helper _should_force_finalize_carbon."""

    def _carbon_data_complete(self, assessment_id: str = "11111111-1111-1111-1111-111111111111") -> dict:
        return {
            "assessment_id": assessment_id,
            "status": "in_progress",
            "applicable_categories": ["energy", "transport", "waste"],
            "completed_categories": ["energy", "transport", "waste"],
            "current_category": "waste",
            "entries": [],
            "total_emissions_tco2e": 12.5,
            "sector": "services",
            "year": 2026,
        }

    def test_force_when_match_and_complete(self) -> None:
        """Scénario I/O Matrix #2 : forçage carbon finalize déclenché."""
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=self._carbon_data_complete(),
        )
        should, ass_id = _should_force_finalize_carbon(state)
        assert should is True
        assert ass_id == "11111111-1111-1111-1111-111111111111"

    def test_no_force_when_assessment_id_invalid_uuid(self) -> None:
        """F3 (review V8-AXE3) : assessment_id non parseable comme UUID → pas de forçage."""
        carbon_data = self._carbon_data_complete()
        carbon_data["assessment_id"] = "ass-uuid-123"  # non-UUID
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=carbon_data,
        )
        should, ass_id = _should_force_finalize_carbon(state)
        assert should is False
        assert ass_id is None

    def test_no_force_when_categories_incomplete(self) -> None:
        """Pré-condition KO : completed_categories incomplet → pas de forçage."""
        carbon_data = self._carbon_data_complete()
        carbon_data["completed_categories"] = ["energy"]
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=carbon_data,
        )
        should, ass_id = _should_force_finalize_carbon(state)
        assert should is False
        assert ass_id is None

    def test_no_force_when_assessment_id_pending(self) -> None:
        carbon_data = self._carbon_data_complete()
        carbon_data["assessment_id"] = "pending"
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=carbon_data,
        )
        should, _ = _should_force_finalize_carbon(state)
        assert should is False

    def test_no_force_when_assessment_id_missing(self) -> None:
        carbon_data = self._carbon_data_complete()
        carbon_data.pop("assessment_id")
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=carbon_data,
        )
        should, _ = _should_force_finalize_carbon(state)
        assert should is False

    def test_no_force_when_no_carbon_data(self) -> None:
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=None,
        )
        should, _ = _should_force_finalize_carbon(state)
        assert should is False

    def test_no_force_when_no_match(self) -> None:
        """Question informationnelle → pas de forçage."""
        state = make_conversation_state(
            messages=[HumanMessage(content="C'est quoi un bilan carbone ?")],
            carbon_data=self._carbon_data_complete(),
        )
        should, _ = _should_force_finalize_carbon(state)
        assert should is False

    def test_no_force_when_tool_already_called_in_turn(self) -> None:
        """Scénario I/O Matrix #5 carbon : tool déjà appelé dans le tour → pas de re-forçage."""
        state = make_conversation_state(
            messages=[
                HumanMessage(content="Oui, finalise ce bilan"),
                AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "finalize_carbon_assessment",
                        "args": {"assessment_id": "11111111-1111-1111-1111-111111111111"},
                        "id": "tc-1",
                    }],
                ),
                ToolMessage(
                    content='{"status":"success"}',
                    name="finalize_carbon_assessment",
                    tool_call_id="tc-1",
                ),
            ],
            carbon_data=self._carbon_data_complete(),
        )
        # Dernier message n'est plus HumanMessage.
        should, _ = _should_force_finalize_carbon(state)
        assert should is False

    def test_no_force_when_applicable_empty(self) -> None:
        """Edge case : applicable_categories vide → pas de forçage (rien à finaliser)."""
        carbon_data = self._carbon_data_complete()
        carbon_data["applicable_categories"] = []
        carbon_data["completed_categories"] = []
        state = make_conversation_state(
            messages=[HumanMessage(content="Oui, finalise ce bilan")],
            carbon_data=carbon_data,
        )
        should, _ = _should_force_finalize_carbon(state)
        assert should is False
