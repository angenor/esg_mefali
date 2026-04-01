"""Tests du service de rappels (T041)."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.action_plan import (
    ActionItem,
    ActionItemCategory,
    ActionItemPriority,
    ActionItemStatus,
    ActionPlan,
    PlanStatus,
    Reminder,
    ReminderType,
)


# --- Helpers ---


def _make_reminder(
    user_id: uuid.UUID,
    reminder_type: ReminderType = ReminderType.action_due,
    scheduled_at: datetime | None = None,
    sent: bool = False,
) -> MagicMock:
    """Créer un mock Reminder pour les tests."""
    reminder = MagicMock(spec=Reminder)
    reminder.id = uuid.uuid4()
    reminder.user_id = user_id
    reminder.action_item_id = uuid.uuid4()
    reminder.type = reminder_type
    reminder.message = "Rappel de test"
    reminder.scheduled_at = scheduled_at or (datetime.now(tz=timezone.utc) + timedelta(hours=1))
    reminder.sent = sent
    reminder.created_at = datetime.now(tz=timezone.utc)
    reminder.action_item = None
    return reminder


# --- Tests create_reminder ---


class TestCreateReminder:
    """Tests de création de rappels."""

    @pytest.mark.asyncio
    async def test_create_reminder_success(self, db_session):
        """T041-01 : Créer un rappel valide."""
        from app.modules.action_plan.service import create_reminder

        user_id = uuid.uuid4()

        # Créer un plan et une action
        plan = ActionPlan(
            user_id=user_id,
            title="Plan test",
            timeframe=12,
            status=PlanStatus.active,
            total_actions=1,
            completed_actions=0,
        )
        db_session.add(plan)
        await db_session.flush()

        item = ActionItem(
            plan_id=plan.id,
            title="Action test",
            category=ActionItemCategory.environment,
            priority=ActionItemPriority.medium,
            status=ActionItemStatus.todo,
            completion_percentage=0,
            sort_order=0,
        )
        db_session.add(item)
        await db_session.flush()

        scheduled = datetime.now(tz=timezone.utc) + timedelta(days=1)
        reminder = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=item.id,
            reminder_type="action_due",
            message="Test rappel",
            scheduled_at=scheduled,
        )

        assert reminder is not None
        assert reminder.user_id == user_id
        assert reminder.action_item_id == item.id
        assert reminder.message == "Test rappel"
        assert reminder.sent is False

    @pytest.mark.asyncio
    async def test_create_reminder_without_action_item(self, db_session):
        """T041-02 : Créer un rappel sans action associée."""
        from app.modules.action_plan.service import create_reminder

        user_id = uuid.uuid4()
        scheduled = datetime.now(tz=timezone.utc) + timedelta(days=1)

        reminder = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Rappel personnalisé",
            scheduled_at=scheduled,
        )

        assert reminder is not None
        assert reminder.action_item_id is None
        assert reminder.type == ReminderType.custom


# --- Tests get_upcoming_reminders ---


class TestGetUpcomingReminders:
    """Tests de récupération des rappels à venir."""

    @pytest.mark.asyncio
    async def test_get_upcoming_sorted_by_date(self, db_session):
        """T041-03 : Rappels triés par scheduled_at ASC."""
        from app.modules.action_plan.service import create_reminder, get_upcoming_reminders

        user_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        # Créer 3 rappels à des dates différentes
        r1 = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Rappel 3 jours",
            scheduled_at=now + timedelta(days=3),
        )
        r2 = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Rappel 1 jour",
            scheduled_at=now + timedelta(days=1),
        )
        r3 = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Rappel 2 jours",
            scheduled_at=now + timedelta(days=2),
        )

        reminders = await get_upcoming_reminders(db=db_session, user_id=user_id, limit=10)

        assert len(reminders) == 3
        assert reminders[0].message == "Rappel 1 jour"
        assert reminders[1].message == "Rappel 2 jours"
        assert reminders[2].message == "Rappel 3 jours"

    @pytest.mark.asyncio
    async def test_get_upcoming_excludes_sent(self, db_session):
        """T041-04 : Les rappels envoyés sont exclus."""
        from app.modules.action_plan.service import create_reminder, get_upcoming_reminders, mark_reminder_sent

        user_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        r1 = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Non envoyé",
            scheduled_at=now + timedelta(days=1),
        )
        r2 = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Envoyé",
            scheduled_at=now + timedelta(days=2),
        )

        # Marquer r2 comme envoyé
        await mark_reminder_sent(db=db_session, reminder_id=r2.id, user_id=user_id)

        reminders = await get_upcoming_reminders(db=db_session, user_id=user_id, limit=10)

        assert len(reminders) == 1
        assert reminders[0].message == "Non envoyé"

    @pytest.mark.asyncio
    async def test_get_upcoming_respects_limit(self, db_session):
        """T041-05 : Le paramètre limit est respecté."""
        from app.modules.action_plan.service import create_reminder, get_upcoming_reminders

        user_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        for i in range(5):
            await create_reminder(
                db=db_session,
                user_id=user_id,
                action_item_id=None,
                reminder_type="custom",
                message=f"Rappel {i}",
                scheduled_at=now + timedelta(days=i + 1),
            )

        reminders = await get_upcoming_reminders(db=db_session, user_id=user_id, limit=3)
        assert len(reminders) == 3

    @pytest.mark.asyncio
    async def test_get_upcoming_filter_by_type(self, db_session):
        """T041-06 : Filtrer par type de rappel."""
        from app.modules.action_plan.service import create_reminder, get_upcoming_reminders

        user_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="Custom",
            scheduled_at=now + timedelta(days=1),
        )
        await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="intermediary_followup",
            message="Intermédiaire",
            scheduled_at=now + timedelta(days=2),
        )

        reminders = await get_upcoming_reminders(
            db=db_session, user_id=user_id, limit=10, reminder_type="intermediary_followup"
        )

        assert len(reminders) == 1
        assert reminders[0].message == "Intermédiaire"


# --- Tests mark_reminder_sent ---


class TestMarkReminderSent:
    """Tests du marquage d'un rappel comme envoyé."""

    @pytest.mark.asyncio
    async def test_mark_as_sent(self, db_session):
        """T041-07 : Marquer un rappel comme envoyé."""
        from app.modules.action_plan.service import create_reminder, mark_reminder_sent

        user_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        reminder = await create_reminder(
            db=db_session,
            user_id=user_id,
            action_item_id=None,
            reminder_type="custom",
            message="À envoyer",
            scheduled_at=now + timedelta(days=1),
        )

        updated = await mark_reminder_sent(db=db_session, reminder_id=reminder.id, user_id=user_id)
        assert updated.sent is True
