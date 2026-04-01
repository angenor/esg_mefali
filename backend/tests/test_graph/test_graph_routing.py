"""Tests du graphe LangGraph refactoré (multi-nœuds avec routeur)."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes import _detect_profile_info, router_node
from app.graph.state import ConversationState


# ── Détection d'infos de profil ─────────────────────────────────────


class TestDetectProfileInfo:
    """Tests des heuristiques de détection."""

    def test_detects_employee_count(self) -> None:
        assert _detect_profile_info("on a 15 employés") is True

    def test_detects_city(self) -> None:
        assert _detect_profile_info("nous sommes basés à Abidjan") is True

    def test_detects_sector(self) -> None:
        assert _detect_profile_info("je fais du recyclage") is True

    def test_detects_revenue(self) -> None:
        assert _detect_profile_info("CA de 50 millions FCFA") is True

    def test_detects_founding_year(self) -> None:
        assert _detect_profile_info("société créée en 2015") is True

    def test_no_detection_on_generic_message(self) -> None:
        assert _detect_profile_info("Bonjour, comment allez-vous ?") is False

    def test_no_detection_on_esg_question(self) -> None:
        assert _detect_profile_info("Qu'est-ce que le scoring ESG ?") is False


# ── Router Node ─────────────────────────────────────────────────────


class TestRouterNode:
    """Tests du nœud routeur."""

    @pytest.mark.asyncio
    async def test_routes_to_extraction_on_profile_info(self) -> None:
        """Quand le message contient des infos, profile_updates est initialisé."""
        state: ConversationState = {
            "messages": [
                HumanMessage(content="je fais du recyclage à Abidjan avec 15 employés"),
            ],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)

        assert result["profile_updates"] == []

    @pytest.mark.asyncio
    async def test_no_extraction_on_generic_message(self) -> None:
        """Quand le message est générique, profile_updates reste None."""
        state: ConversationState = {
            "messages": [
                HumanMessage(content="Bonjour, j'ai besoin de conseils"),
            ],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)

        assert result["profile_updates"] is None

    @pytest.mark.asyncio
    async def test_handles_empty_messages(self) -> None:
        """Gère correctement un state sans messages."""
        state: ConversationState = {
            "messages": [],
            "user_profile": None,
            "context_memory": [],
            "profile_updates": None,
        }
        result = await router_node(state)

        assert result["profile_updates"] is None


# ── State enrichi ───────────────────────────────────────────────────


class TestConversationState:
    """Tests de la structure du state enrichi."""

    def test_state_has_profile_fields(self) -> None:
        """Le state accepte les nouveaux champs."""
        state: ConversationState = {
            "messages": [],
            "user_profile": {"sector": "recyclage", "city": "Abidjan"},
            "context_memory": ["Résumé 1", "Résumé 2"],
            "profile_updates": [{"field": "sector", "value": "recyclage"}],
        }
        assert state["user_profile"]["sector"] == "recyclage"
        assert len(state["context_memory"]) == 2
        assert len(state["profile_updates"]) == 1
