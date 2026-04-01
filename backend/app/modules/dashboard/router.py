"""Router FastAPI pour le module Dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.dashboard.schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    """Retourner la vue synthétique du tableau de bord pour l'utilisateur courant."""
    from app.modules.dashboard.service import get_dashboard_summary

    data = await get_dashboard_summary(db, current_user.id)
    return DashboardSummary(**data)
