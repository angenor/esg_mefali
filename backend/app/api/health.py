"""Router health check : vérification de l'état du système."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Vérifier l'état du backend et de la base de données."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Health check: connexion DB échouée", exc_info=True)
        db_status = "disconnected"

    status = "healthy" if db_status == "connected" else "degraded"
    status_code = 200 if status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "database": db_status,
            "version": settings.app_version,
        },
    )
