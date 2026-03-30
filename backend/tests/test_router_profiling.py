"""Tests du routeur pour le profilage guidé (US3).

T035: Vérifier que le routeur injecte les instructions de profilage
quand le profil identité/localisation est < 70% et que le message
est générique, et ne les injecte PAS quand le message est une
demande de module spécifique ou que le profil est >= 70%.

Écrits AVANT l'implémentation (TDD RED phase).
"""

import pytest
from langchain_core.messages import HumanMessage

from app.graph.nodes import router_node
from app.graph.state import ConversationState


def _make_state(
    message: str,
    user_profile: dict | None = None,
) -> ConversationState:
    """Créer un state minimal pour tester le routeur."""
    return ConversationState(
        messages=[HumanMessage(content=message)],
        user_profile=user_profile,
        context_memory=[],
        profile_updates=None,
    )


# Profil à 25% identité (2/8 remplis : country par défaut + sector)
PROFILE_LOW_COMPLETION = {
    "sector": "recyclage",
    "country": "Côte d'Ivoire",
}

# Profil à 75% identité (6/8 remplis)
PROFILE_HIGH_COMPLETION = {
    "company_name": "EcoPlast SARL",
    "sector": "recyclage",
    "sub_sector": "recyclage de plastique",
    "employee_count": 15,
    "city": "Abidjan",
    "country": "Côte d'Ivoire",
}

# Profil vide (seul country par défaut)
PROFILE_EMPTY = {
    "country": "Côte d'Ivoire",
}


class TestRouterProfilingInjection:
    """Tests de l'injection de profilage guidé par le routeur."""

    @pytest.mark.asyncio
    async def test_low_profile_generic_message_injects_profiling(self) -> None:
        """Profil < 70% + message générique → instructions de profilage injectées."""
        state = _make_state(
            "Bonjour, je voudrais des conseils ESG",
            user_profile=PROFILE_LOW_COMPLETION,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is not None
        instructions = result["profiling_instructions"]
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # Les instructions doivent mentionner des champs manquants
        assert "company_name" in instructions or "Nom" in instructions

    @pytest.mark.asyncio
    async def test_low_profile_esg_request_no_injection(self) -> None:
        """Profil < 70% + demande ESG/scoring → PAS d'injection de profilage."""
        state = _make_state(
            "Je voudrais faire un scoring ESG de mon entreprise",
            user_profile=PROFILE_LOW_COMPLETION,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is None

    @pytest.mark.asyncio
    async def test_low_profile_carbon_request_no_injection(self) -> None:
        """Profil < 70% + demande empreinte carbone → PAS d'injection."""
        state = _make_state(
            "Comment calculer mon empreinte carbone ?",
            user_profile=PROFILE_LOW_COMPLETION,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is None

    @pytest.mark.asyncio
    async def test_low_profile_financing_request_no_injection(self) -> None:
        """Profil < 70% + demande financement → PAS d'injection."""
        state = _make_state(
            "Quels fonds verts sont disponibles pour mon projet ?",
            user_profile=PROFILE_LOW_COMPLETION,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is None

    @pytest.mark.asyncio
    async def test_high_profile_generic_message_no_injection(self) -> None:
        """Profil >= 70% + message générique → PAS d'injection."""
        state = _make_state(
            "Bonjour, je voudrais des conseils ESG",
            user_profile=PROFILE_HIGH_COMPLETION,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is None

    @pytest.mark.asyncio
    async def test_no_profile_generic_message_injects_profiling(self) -> None:
        """Pas de profil + message générique → instructions de profilage."""
        state = _make_state(
            "Bonjour, comment puis-je améliorer ma démarche ESG ?",
            user_profile=None,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is not None

    @pytest.mark.asyncio
    async def test_empty_profile_generic_message_injects_profiling(self) -> None:
        """Profil quasi-vide + message générique → instructions de profilage."""
        state = _make_state(
            "Quels sont les avantages de la RSE ?",
            user_profile=PROFILE_EMPTY,
        )

        result = await router_node(state)

        assert result.get("profiling_instructions") is not None

    @pytest.mark.asyncio
    async def test_profiling_instructions_list_missing_fields(self) -> None:
        """Les instructions de profilage doivent lister les champs manquants."""
        state = _make_state(
            "Pouvez-vous m'aider ?",
            user_profile=PROFILE_LOW_COMPLETION,
        )

        result = await router_node(state)

        instructions = result.get("profiling_instructions", "")
        # Doit contenir des champs manquants du profil identité
        # (company_name, sub_sector, employee_count, annual_revenue_xof, year_founded, city)
        missing_mentioned = sum(1 for field in [
            "company_name", "employee_count", "city", "year_founded",
        ] if field in instructions or FIELD_LABEL_MAP.get(field, "") in instructions)
        assert missing_mentioned >= 1


# Labels attendus dans les instructions
FIELD_LABEL_MAP = {
    "company_name": "Nom de l'entreprise",
    "sector": "Secteur",
    "sub_sector": "Sous-secteur",
    "employee_count": "Nombre d'employés",
    "annual_revenue_xof": "Chiffre d'affaires",
    "city": "Ville",
    "country": "Pays",
    "year_founded": "Année de création",
}
