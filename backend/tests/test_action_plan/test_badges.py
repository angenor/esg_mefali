"""Tests du service de badges (T048)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.action_plan import (
    ActionItem,
    ActionItemCategory,
    ActionItemPriority,
    ActionItemStatus,
    ActionPlan,
    Badge,
    BadgeType,
    PlanStatus,
)


# --- Tests check_and_award_badges ---


class TestCheckAndAwardBadges:
    """Tests de l'attribution automatique des badges."""

    @pytest.mark.asyncio
    async def test_first_carbon_badge(self, db_session):
        """T048-01 : Badge first_carbon quand un bilan carbone complété existe."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        # Simuler un bilan carbone complété
        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=False,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        badge_types = [b.badge_type for b in new_badges]
        assert BadgeType.first_carbon in badge_types

    @pytest.mark.asyncio
    async def test_esg_above_50_badge(self, db_session):
        """T048-02 : Badge esg_above_50 quand le score ESG > 50."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=False,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        badge_types = [b.badge_type for b in new_badges]
        assert BadgeType.esg_above_50 in badge_types

    @pytest.mark.asyncio
    async def test_first_application_badge(self, db_session):
        """T048-03 : Badge first_application quand une candidature soumise."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=False,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        badge_types = [b.badge_type for b in new_badges]
        assert BadgeType.first_application in badge_types

    @pytest.mark.asyncio
    async def test_first_intermediary_contact_badge(self, db_session):
        """T048-04 : Badge first_intermediary_contact quand action intermédiaire terminée."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=True,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        badge_types = [b.badge_type for b in new_badges]
        assert BadgeType.first_intermediary_contact in badge_types

    @pytest.mark.asyncio
    async def test_full_journey_badge(self, db_session):
        """T048-05 : Badge full_journey quand toutes les conditions sont remplies."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=True,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        badge_types = [b.badge_type for b in new_badges]
        assert BadgeType.full_journey in badge_types

    @pytest.mark.asyncio
    async def test_no_duplicate_badges(self, db_session):
        """T048-06 : Pas de doublon de badge pour le même utilisateur."""
        from app.modules.action_plan.badges import check_and_award_badges

        user_id = uuid.uuid4()

        # Pré-créer un badge first_carbon
        existing_badge = Badge(
            user_id=user_id,
            badge_type=BadgeType.first_carbon,
        )
        db_session.add(existing_badge)
        await db_session.flush()

        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=False,
        ):
            new_badges = await check_and_award_badges(db_session, user_id)

        # first_carbon ne doit pas apparaître à nouveau
        assert len(new_badges) == 0


# --- Tests safe_check_and_award_badges (BUG-V7.1-013) ---


class TestSafeCheckAndAwardBadges:
    """Helper fire-and-forget appele aux call-sites de finalization."""

    @pytest.mark.asyncio
    async def test_passes_through_on_success(self, db_session):
        """Cas nominal : delegue a check_and_award_badges et renvoie les badges."""
        from app.modules.action_plan.badges import safe_check_and_award_badges

        user_id = uuid.uuid4()
        with patch(
            "app.modules.action_plan.badges._has_completed_carbon",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "app.modules.action_plan.badges._has_esg_above_50",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_submitted_application",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "app.modules.action_plan.badges._has_completed_intermediary_contact",
            new_callable=AsyncMock,
            return_value=False,
        ):
            new_badges = await safe_check_and_award_badges(db_session, user_id)

        assert any(b.badge_type == BadgeType.first_carbon for b in new_badges)

    @pytest.mark.asyncio
    async def test_swallows_exception_returns_empty(self):
        """En cas d'exception, retourne [] sans propager (fire-and-forget)."""
        from app.modules.action_plan.badges import safe_check_and_award_badges

        broken_db = MagicMock()
        # MagicMock execute() retourne un MagicMock non-awaitable → leve TypeError
        # quand check_and_award_badges tente await db.execute(...).
        with patch(
            "app.modules.action_plan.badges.check_and_award_badges",
            new_callable=AsyncMock,
            side_effect=RuntimeError("BDD indisponible"),
        ):
            result = await safe_check_and_award_badges(broken_db, uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_integration_carbon_completion_awards_badge(self, db_session):
        """BUG-V7.1-013 : safe_check_and_award_badges declenche first_carbon
        apres qu'un CarbonAssessment ait ete persiste avec status=completed."""
        from app.models.carbon import CarbonAssessment, CarbonStatusEnum
        from app.modules.action_plan.badges import safe_check_and_award_badges

        user_id = uuid.uuid4()
        # Simuler l'effet d'un complete_assessment sans appeler le tool LangGraph.
        assessment = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=user_id,
            year=2026,
            sector="agriculture",
            total_emissions_tco2e=16.9,
            status=CarbonStatusEnum.completed,
        )
        db_session.add(assessment)
        await db_session.flush()

        new_badges = await safe_check_and_award_badges(db_session, user_id)

        badge_types = {b.badge_type for b in new_badges}
        assert BadgeType.first_carbon in badge_types

    @pytest.mark.asyncio
    async def test_integration_idempotent_second_call(self, db_session):
        """Deuxieme appel = no-op (badge deja attribue)."""
        from app.models.carbon import CarbonAssessment, CarbonStatusEnum
        from app.modules.action_plan.badges import safe_check_and_award_badges

        user_id = uuid.uuid4()
        assessment = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=user_id,
            year=2026,
            sector="agriculture",
            total_emissions_tco2e=16.9,
            status=CarbonStatusEnum.completed,
        )
        db_session.add(assessment)
        await db_session.flush()

        first_call = await safe_check_and_award_badges(db_session, user_id)
        second_call = await safe_check_and_award_badges(db_session, user_id)

        assert any(b.badge_type == BadgeType.first_carbon for b in first_call)
        assert second_call == []


# --- Tests get_user_badges ---


class TestGetUserBadges:
    """Tests de récupération des badges."""

    @pytest.mark.asyncio
    async def test_get_user_badges(self, db_session):
        """T048-07 : Récupérer tous les badges d'un utilisateur."""
        from app.modules.action_plan.badges import get_user_badges

        user_id = uuid.uuid4()

        db_session.add(Badge(user_id=user_id, badge_type=BadgeType.first_carbon))
        db_session.add(Badge(user_id=user_id, badge_type=BadgeType.esg_above_50))
        await db_session.flush()

        badges = await get_user_badges(db_session, user_id)
        assert len(badges) == 2

    @pytest.mark.asyncio
    async def test_get_user_badges_empty(self, db_session):
        """T048-08 : Pas de badges pour un nouvel utilisateur."""
        from app.modules.action_plan.badges import get_user_badges

        user_id = uuid.uuid4()
        badges = await get_user_badges(db_session, user_id)
        assert len(badges) == 0
