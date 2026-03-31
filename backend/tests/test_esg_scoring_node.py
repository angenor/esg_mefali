"""Tests du esg_scoring_node (T012).

Verifie le flux d'evaluation, la gestion d'etat et la detection d'intention ESG.
"""

import pytest
import re

from app.graph.state import ConversationState


class TestESGIntentDetection:
    """Tests de detection d'intention ESG dans le router_node."""

    def test_detect_esg_keywords(self) -> None:
        """T012-01 : Detection des mots-cles ESG."""
        from app.graph.nodes import _detect_esg_request

        assert _detect_esg_request("Je veux evaluer mon entreprise sur les criteres ESG") is True
        assert _detect_esg_request("Lancer une evaluation ESG") is True
        assert _detect_esg_request("Quel est mon score ESG ?") is True
        assert _detect_esg_request("scoring ESG de mon entreprise") is True

    def test_no_esg_keywords(self) -> None:
        """T012-02 : Pas de detection pour messages generiques."""
        from app.graph.nodes import _detect_esg_request

        assert _detect_esg_request("Bonjour, comment allez-vous ?") is False
        assert _detect_esg_request("Quelles sont vos capacites ?") is False
        assert _detect_esg_request("Parlez-moi du financement vert") is False

    def test_detect_esg_continuation(self) -> None:
        """T012-03 : Detection d'une evaluation ESG en cours via le state."""
        from app.graph.nodes import _has_active_esg_assessment

        state_with_esg = {"esg_assessment": {"assessment_id": "123", "status": "in_progress"}}
        assert _has_active_esg_assessment(state_with_esg) is True

        state_without = {"esg_assessment": None}
        assert _has_active_esg_assessment(state_without) is False

        state_completed = {"esg_assessment": {"assessment_id": "123", "status": "completed"}}
        assert _has_active_esg_assessment(state_completed) is False


class TestESGScoringNodeState:
    """Tests de gestion d'etat du noeud ESG."""

    def test_initial_esg_state_structure(self) -> None:
        """T012-04 : Structure de l'etat ESG initial."""
        from app.modules.esg.service import build_initial_esg_state

        state = build_initial_esg_state("assessment-id-123", "agriculture")
        assert state["assessment_id"] == "assessment-id-123"
        assert state["status"] == "in_progress"
        assert state["current_pillar"] == "environment"
        assert state["evaluated_criteria"] == []
        assert state["partial_scores"] == {}

    def test_next_pillar_after_environment(self) -> None:
        """T012-05 : Transition du pilier E vers S."""
        from app.modules.esg.service import get_next_pillar

        assert get_next_pillar("environment") == "social"

    def test_next_pillar_after_social(self) -> None:
        """T012-06 : Transition du pilier S vers G."""
        from app.modules.esg.service import get_next_pillar

        assert get_next_pillar("social") == "governance"

    def test_next_pillar_after_governance(self) -> None:
        """T012-07 : Apres le pilier G, evaluation terminee."""
        from app.modules.esg.service import get_next_pillar

        assert get_next_pillar("governance") is None

    def test_progress_percent_calculation(self) -> None:
        """T012-08 : Calcul du pourcentage de progression."""
        from app.modules.esg.service import compute_progress_percent

        assert compute_progress_percent([]) == 0.0
        assert compute_progress_percent(["E1", "E2", "E3"]) == 10.0
        assert compute_progress_percent([f"E{i}" for i in range(1, 11)]) == pytest.approx(33.33, abs=0.1)
        # 30 criteres = 100%
        all_codes = [f"{p}{i}" for p in ("E", "S", "G") for i in range(1, 11)]
        assert compute_progress_percent(all_codes) == 100.0
