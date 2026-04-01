"""Schemas Pydantic pour le module Plan d'Action."""

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


# --- Enums ---


class ActionItemCategoryEnum(str, Enum):
    """Categorie d'une action."""

    environment = "environment"
    social = "social"
    governance = "governance"
    financing = "financing"
    carbon = "carbon"
    intermediary_contact = "intermediary_contact"


class ActionItemStatusEnum(str, Enum):
    """Statut d'une action."""

    todo = "todo"
    in_progress = "in_progress"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


class ActionItemPriorityEnum(str, Enum):
    """Priorite d'une action."""

    high = "high"
    medium = "medium"
    low = "low"


class ReminderTypeEnum(str, Enum):
    """Type de rappel."""

    action_due = "action_due"
    assessment_renewal = "assessment_renewal"
    fund_deadline = "fund_deadline"
    intermediary_followup = "intermediary_followup"
    custom = "custom"


class BadgeTypeEnum(str, Enum):
    """Type de badge."""

    first_carbon = "first_carbon"
    esg_above_50 = "esg_above_50"
    first_application = "first_application"
    first_intermediary_contact = "first_intermediary_contact"
    full_journey = "full_journey"


class PlanStatusEnum(str, Enum):
    """Statut du plan."""

    active = "active"
    archived = "archived"


# --- Action Plan ---


class ActionPlanCreate(BaseModel):
    """Creation d'un plan d'action."""

    timeframe: int = Field(..., description="Horizon en mois : 6, 12 ou 24")


class ActionItemResponse(BaseModel):
    """Action retournee par l'API."""

    id: uuid.UUID
    plan_id: uuid.UUID
    title: str
    description: str | None = None
    category: ActionItemCategoryEnum
    priority: ActionItemPriorityEnum
    status: ActionItemStatusEnum
    due_date: date | None = None
    estimated_cost_xof: int | None = None
    estimated_benefit: str | None = None
    completion_percentage: int = 0
    related_fund_id: uuid.UUID | None = None
    related_intermediary_id: uuid.UUID | None = None
    intermediary_name: str | None = None
    intermediary_address: str | None = None
    intermediary_phone: str | None = None
    intermediary_email: str | None = None
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionPlanResponse(BaseModel):
    """Plan d'action retourne par l'API."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    timeframe: int
    status: PlanStatusEnum
    total_actions: int = 0
    completed_actions: int = 0
    items: list[ActionItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionPlanSummary(BaseModel):
    """Resume du plan d'action (sans items)."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    timeframe: int
    status: PlanStatusEnum
    total_actions: int = 0
    completed_actions: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionItemUpdate(BaseModel):
    """Mise a jour d'une action."""

    status: ActionItemStatusEnum | None = None
    completion_percentage: int | None = Field(None, ge=0, le=100)
    due_date: date | None = None


class ProgressByCategory(BaseModel):
    """Avancement par categorie."""

    total: int
    completed: int
    percentage: int


class ActionItemsListResponse(BaseModel):
    """Liste paginee des actions avec progression."""

    items: list[ActionItemResponse]
    total: int
    page: int
    limit: int
    progress: dict[str, ProgressByCategory | int] = Field(default_factory=dict)


# --- Reminders ---


class ReminderCreate(BaseModel):
    """Creation d'un rappel."""

    action_item_id: uuid.UUID | None = None
    type: ReminderTypeEnum
    message: str = Field(..., max_length=500)
    scheduled_at: datetime


class ReminderResponse(BaseModel):
    """Rappel retourne par l'API."""

    id: uuid.UUID
    user_id: uuid.UUID
    action_item_id: uuid.UUID | None = None
    type: ReminderTypeEnum
    message: str
    scheduled_at: datetime
    sent: bool = False
    created_at: datetime
    action_item: ActionItemResponse | None = None

    model_config = {"from_attributes": True}


class RemindersListResponse(BaseModel):
    """Liste des rappels."""

    items: list[ReminderResponse]
    total: int


# --- Badges ---


class BadgeResponse(BaseModel):
    """Badge retourne par l'API."""

    id: uuid.UUID
    user_id: uuid.UUID
    badge_type: BadgeTypeEnum
    unlocked_at: datetime

    model_config = {"from_attributes": True}
