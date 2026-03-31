"""Tests de la chaîne d'extraction structurée (US1)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.company.schemas import (
    ESGExtraction,
    IdentityExtraction,
    ProfileExtraction,
    SectorEnum,
)


class TestExtractionChain:
    """Tests de la chaîne d'extraction de profil depuis un message."""

    @pytest.mark.asyncio
    async def test_extracts_fields_from_french_message(self) -> None:
        """Un message FR avec infos d'entreprise retourne les bons champs."""
        from app.chains.extraction import extract_profile_from_message

        mock_extraction = ProfileExtraction(
            identity=IdentityExtraction(
                sector=SectorEnum.recyclage,
                city="Abidjan",
                employee_count=15,
            ),
        )

        with patch(
            "app.chains.extraction._run_extraction",
            new_callable=AsyncMock,
            return_value=mock_extraction,
        ):
            result = await extract_profile_from_message(
                "je fais du recyclage de plastique à Abidjan avec 15 employés",
                current_profile={},
            )

        flat = result.flat_dict()
        assert flat["sector"] == SectorEnum.recyclage
        assert flat["city"] == "Abidjan"
        assert flat["employee_count"] == 15

    @pytest.mark.asyncio
    async def test_empty_message_returns_no_fields(self) -> None:
        """Un message vide retourne une extraction sans champs."""
        from app.chains.extraction import extract_profile_from_message

        mock_extraction = ProfileExtraction()

        with patch(
            "app.chains.extraction._run_extraction",
            new_callable=AsyncMock,
            return_value=mock_extraction,
        ):
            result = await extract_profile_from_message(
                "Bonjour",
                current_profile={},
            )

        assert len(result.flat_dict()) == 0

    @pytest.mark.asyncio
    async def test_ambiguous_message_only_high_confidence(self) -> None:
        """Un message ambigu ne retourne que les champs haute confiance."""
        from app.chains.extraction import extract_profile_from_message

        mock_extraction = ProfileExtraction(
            identity=IdentityExtraction(
                sector=SectorEnum.agroalimentaire,
            ),
        )

        with patch(
            "app.chains.extraction._run_extraction",
            new_callable=AsyncMock,
            return_value=mock_extraction,
        ):
            result = await extract_profile_from_message(
                "on est dans le commerce, enfin plutôt l'agroalimentaire",
                current_profile={},
            )

        flat = result.flat_dict()
        assert flat["sector"] == SectorEnum.agroalimentaire
        assert "city" not in flat
