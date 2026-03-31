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
