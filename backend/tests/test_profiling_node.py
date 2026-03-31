"""Tests du profiling_node (US1)."""

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.graph.state import ConversationState
from app.modules.company.schemas import (
    IdentityExtraction,
    ProfileExtraction,
    SectorEnum,
)


class TestProfilingNode:
    """Tests du nœud de profilage."""

    @pytest.mark.asyncio
    async def test_extraction_updates_profile(self) -> None:
        """Le profiling_node extrait et met à jour le profil."""
        from app.graph.nodes import profiling_node

        mock_extraction = ProfileExtraction(
            identity=IdentityExtraction(
                sector=SectorEnum.recyclage,
                city="Abidjan",
                employee_count=15,
            ),
        )

        state: ConversationState = {
            "messages": [
                HumanMessage(
                    content="je fais du recyclage à Abidjan avec 15 employés"
                ),
            ],
            "user_profile": {"country": "Côte d'Ivoire"},
            "context_memory": [],
            "profile_updates": [],
            "profiling_instructions": None,
        }

        with patch(
            "app.chains.extraction.extract_profile_from_message",
            new_callable=AsyncMock,
            return_value=mock_extraction,
        ):
            result = await profiling_node(state)

        updates = result["profile_updates"]
        assert len(updates) == 3
        fields_updated = {u["field"] for u in updates}
        assert "sector" in fields_updated
        assert "city" in fields_updated
        assert "employee_count" in fields_updated

    @pytest.mark.asyncio
    async def test_no_extraction_returns_empty_updates(self) -> None:
        """Aucune extraction → profile_updates vide."""
        from app.graph.nodes import profiling_node

        mock_extraction = ProfileExtraction()

        state: ConversationState = {
            "messages": [HumanMessage(content="Bonjour")],
            "user_profile": {},
            "context_memory": [],
            "profile_updates": [],
            "profiling_instructions": None,
        }

        with patch(
            "app.chains.extraction.extract_profile_from_message",
            new_callable=AsyncMock,
            return_value=mock_extraction,
        ):
            result = await profiling_node(state)

        assert result["profile_updates"] == []
