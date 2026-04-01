"""Logique de gamification — attribution automatique des badges."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import Badge, BadgeType

logger = logging.getLogger(__name__)


# --- Conditions de déclenchement ---


async def _has_completed_carbon(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Vérifier si l'utilisateur a au moins un bilan carbone complété."""
    from app.models.carbon import CarbonAssessment, CarbonStatusEnum

    result = await db.execute(
        select(CarbonAssessment.id)
        .where(CarbonAssessment.user_id == user_id)
        .where(CarbonAssessment.status == CarbonStatusEnum.completed)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _has_esg_above_50(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Vérifier si l'utilisateur a un score ESG > 50."""
    from app.models.esg import ESGAssessment, ESGStatusEnum

    result = await db.execute(
        select(ESGAssessment.overall_score)
        .where(ESGAssessment.user_id == user_id)
        .where(ESGAssessment.status == ESGStatusEnum.completed)
        .where(ESGAssessment.overall_score > 50)
        .order_by(ESGAssessment.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _has_submitted_application(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Vérifier si l'utilisateur a soumis au moins une candidature."""
    from app.models.application import FundApplication

    result = await db.execute(
        select(FundApplication.id)
        .where(FundApplication.user_id == user_id)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _has_completed_intermediary_contact(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Vérifier si l'utilisateur a complété au moins une action de type intermediary_contact."""
    from app.models.action_plan import ActionItem, ActionItemCategory, ActionItemStatus, ActionPlan

    result = await db.execute(
        select(ActionItem.id)
        .join(ActionPlan, ActionItem.plan_id == ActionPlan.id)
        .where(ActionPlan.user_id == user_id)
        .where(ActionItem.category == ActionItemCategory.intermediary_contact)
        .where(ActionItem.status == ActionItemStatus.completed)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


# Mapping badge → condition function name (pour résolution dynamique via globals())
BADGE_CONDITION_NAMES: dict[BadgeType, str] = {
    BadgeType.first_carbon: "_has_completed_carbon",
    BadgeType.esg_above_50: "_has_esg_above_50",
    BadgeType.first_application: "_has_submitted_application",
    BadgeType.first_intermediary_contact: "_has_completed_intermediary_contact",
}


# --- Fonctions principales ---


async def check_and_award_badges(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Badge]:
    """Vérifier toutes les conditions de badges et attribuer ceux manquants.

    Returns:
        Liste des nouveaux badges attribués.
    """
    import sys

    this_module = sys.modules[__name__]

    # Récupérer les badges existants
    existing_result = await db.execute(
        select(Badge.badge_type).where(Badge.user_id == user_id)
    )
    existing_types = {row for row in existing_result.scalars().all()}

    new_badges: list[Badge] = []

    # Vérifier chaque badge individuel
    for badge_type, condition_name in BADGE_CONDITION_NAMES.items():
        if badge_type in existing_types:
            continue

        # Résolution dynamique pour que les patches unittest fonctionnent
        condition_fn = getattr(this_module, condition_name)
        if await condition_fn(db, user_id):
            badge = Badge(user_id=user_id, badge_type=badge_type)
            db.add(badge)
            new_badges.append(badge)

    # Vérifier full_journey : toutes les conditions individuelles remplies
    if BadgeType.full_journey not in existing_types:
        required = set(BADGE_CONDITION_NAMES.keys())
        all_types_now = existing_types | {b.badge_type for b in new_badges}
        if required.issubset(all_types_now):
            badge = Badge(user_id=user_id, badge_type=BadgeType.full_journey)
            db.add(badge)
            new_badges.append(badge)

    if new_badges:
        await db.commit()
        for badge in new_badges:
            await db.refresh(badge)

    return new_badges


async def get_user_badges(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Badge]:
    """Récupérer tous les badges d'un utilisateur."""
    result = await db.execute(
        select(Badge)
        .where(Badge.user_id == user_id)
        .order_by(Badge.unlocked_at.desc())
    )
    return list(result.scalars().all())
