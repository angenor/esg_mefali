"""Tests des endpoints REST rappels (T042)."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.action_plan import Reminder, ReminderType


# --- Helpers ---


def _make_mock_user():
    """Créer un mock User pour le middleware d'auth."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


def _make_mock_reminder(
    user_id: uuid.UUID,
    reminder_type: str = "action_due",
    sent: bool = False,
) -> MagicMock:
    """Créer un mock Reminder."""
    reminder = MagicMock()
    reminder.id = uuid.uuid4()
    reminder.user_id = user_id
    reminder.action_item_id = uuid.uuid4()
    reminder.type = ReminderType(reminder_type)
    reminder.message = "Test rappel"
    reminder.scheduled_at = datetime.now(tz=timezone.utc) + timedelta(days=1)
    reminder.sent = sent
    reminder.created_at = datetime.now(tz=timezone.utc)
    reminder.action_item = None
    return reminder


# --- Tests POST /reminders/ ---


class TestCreateReminderEndpoint:
    """Tests de l'endpoint POST /api/action-plan/reminders/."""

    @pytest.mark.asyncio
    async def test_create_reminder_201(self):
        """T042-01 : POST /reminders/ retourne 201 avec données valides."""
        from app.modules.action_plan.router import create_reminder_endpoint
        from app.modules.action_plan.schemas import ReminderCreate

        mock_db = AsyncMock()
        mock_user = _make_mock_user()
        mock_reminder = _make_mock_reminder(mock_user.id)

        with patch(
            "app.modules.action_plan.router.create_reminder",
            new=AsyncMock(return_value=mock_reminder),
        ):
            payload = ReminderCreate(
                action_item_id=mock_reminder.action_item_id,
                type="action_due",
                message="Test rappel",
                scheduled_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
            )
            result = await create_reminder_endpoint(
                payload=payload,
                db=mock_db,
                current_user=mock_user,
            )

        assert result.message == "Test rappel"


# --- Tests GET /reminders/upcoming ---


class TestUpcomingRemindersEndpoint:
    """Tests de l'endpoint GET /api/action-plan/reminders/upcoming."""

    @pytest.mark.asyncio
    async def test_get_upcoming_200(self):
        """T042-02 : GET /reminders/upcoming retourne les rappels."""
        from app.modules.action_plan.router import get_upcoming_reminders_endpoint

        mock_db = AsyncMock()
        mock_user = _make_mock_user()
        mock_reminders = [
            _make_mock_reminder(mock_user.id),
            _make_mock_reminder(mock_user.id, reminder_type="intermediary_followup"),
        ]

        with patch(
            "app.modules.action_plan.router.get_upcoming_reminders",
            new=AsyncMock(return_value=mock_reminders),
        ):
            result = await get_upcoming_reminders_endpoint(
                limit=10,
                db=mock_db,
                current_user=mock_user,
            )

        assert result.total == 2
        assert len(result.items) == 2
