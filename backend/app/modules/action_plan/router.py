"""Endpoints REST pour le module Plan d'Action."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.action_plan.schemas import (
    ActionItemResponse,
    ActionItemUpdate,
    ActionItemsListResponse,
    ActionPlanCreate,
    ActionPlanResponse,
    ProgressByCategory,
    ReminderCreate,
    ReminderResponse,
    RemindersListResponse,
)
from app.modules.action_plan.service import (
    create_reminder,
    generate_action_plan,
    get_active_plan,
    get_plan_items,
    get_upcoming_reminders,
    update_action_item,
)

router = APIRouter()


@router.post("/generate", response_model=ActionPlanResponse, status_code=201)
async def generate_plan(
    payload: ActionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionPlanResponse:
    """Générer un nouveau plan d'action personnalisé via LLM."""
    plan = await generate_action_plan(db, current_user.id, payload.timeframe)
    return ActionPlanResponse.model_validate(plan)


@router.get("/", response_model=ActionPlanResponse)
async def get_active_plan_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionPlanResponse:
    """Récupérer le plan d'action actif de l'utilisateur."""
    plan = await get_active_plan(db, current_user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Aucun plan d'action actif trouvé.")
    return ActionPlanResponse.model_validate(plan)


@router.get("/{plan_id}/items", response_model=ActionItemsListResponse)
async def list_plan_items(
    plan_id: str,
    category: str | None = Query(None, description="Filtrer par catégorie"),
    status: str | None = Query(None, description="Filtrer par statut"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'items par page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionItemsListResponse:
    """Récupérer les actions d'un plan avec filtres et pagination."""
    import uuid as uuid_mod

    try:
        plan_uuid = uuid_mod.UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="ID de plan invalide.") from exc

    items, total, progress = await get_plan_items(
        db=db,
        plan_id=plan_uuid,
        user_id=current_user.id,
        category=category,
        status=status,
        page=page,
        limit=limit,
    )

    # Convertir le progress en format schema
    progress_out: dict = {}
    for key, value in progress.items():
        if key == "global_percentage":
            progress_out[key] = value
        elif isinstance(value, dict):
            progress_out[key] = ProgressByCategory(
                total=value["total"],
                completed=value["completed"],
                percentage=value["percentage"],
            )

    return ActionItemsListResponse(
        items=[ActionItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
        progress=progress_out,
    )


@router.patch("/items/{item_id}", response_model=ActionItemResponse)
async def update_item(
    item_id: str,
    payload: ActionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionItemResponse:
    """Mettre à jour une action (statut, progression, date)."""
    import uuid as uuid_mod

    try:
        item_uuid = uuid_mod.UUID(item_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="ID d'action invalide.") from exc

    item = await update_action_item(
        db=db,
        item_id=item_uuid,
        user_id=current_user.id,
        updates=payload.model_dump(exclude_none=True),
    )
    return ActionItemResponse.model_validate(item)


# --- Rappels ---


@router.post("/reminders/", response_model=ReminderResponse, status_code=201)
async def create_reminder_endpoint(
    payload: ReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderResponse:
    """Créer un rappel lié à une action."""
    reminder = await create_reminder(
        db=db,
        user_id=current_user.id,
        action_item_id=payload.action_item_id,
        reminder_type=payload.type.value,
        message=payload.message,
        scheduled_at=payload.scheduled_at,
    )
    return ReminderResponse.model_validate(reminder)


@router.get("/reminders/upcoming", response_model=RemindersListResponse)
async def get_upcoming_reminders_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Nombre max de rappels"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RemindersListResponse:
    """Récupérer les prochains rappels non envoyés."""
    reminders = await get_upcoming_reminders(db=db, user_id=current_user.id, limit=limit)
    return RemindersListResponse(
        items=[ReminderResponse.model_validate(r) for r in reminders],
        total=len(reminders),
    )
