"""Fallback deterministe pour la generation de plan d'action.

Pattern §4decies (Lecon 40) : si le LLM echoue malgre les retries
internes du service (LLMGuardError), on bascule sur un template JSON
statique pour garantir la disponibilite du feature.

Usage typique depuis `action_plan_tools.generate_action_plan` :

    try:
        await gen_plan_via_llm(...)
    except LLMGuardError:
        plan = await persist_fallback_plan(db, user_id, timeframe)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import (
    ActionItem,
    ActionItemCategory,
    ActionItemPriority,
    ActionItemStatus,
    ActionPlan,
    PlanStatus,
)
from app.models.company import CompanyProfile

logger = logging.getLogger(__name__)


_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "action_plan_default.json"


# --- Helpers ---


class FallbackTemplateError(RuntimeError):
    """Le template fallback est introuvable ou corrompu."""


def _load_template() -> dict[str, Any]:
    """Charger le template JSON depuis le disque (sans cache pour eviter
    les surprises en tests qui modifieraient le fichier).

    Raises:
        FallbackTemplateError: si le fichier est absent, illisible, ou
            ne contient pas un JSON valide. L'exception est convertie en
            message exploitable par le LLM cote tool, jamais propagee.
    """
    try:
        with _TEMPLATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        logger.error(
            "Template fallback introuvable : %s", _TEMPLATE_PATH,
            extra={"metric": "action_plan_fallback_template_missing"},
        )
        raise FallbackTemplateError(
            f"Template fallback introuvable : {_TEMPLATE_PATH}"
        ) from exc
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(
            "Template fallback corrompu (%s) : %s", _TEMPLATE_PATH, exc,
            extra={"metric": "action_plan_fallback_template_corrupt"},
        )
        raise FallbackTemplateError(
            f"Template fallback corrompu : {exc}"
        ) from exc


def _coerce_str(raw: Any) -> str | None:
    """Convertir une valeur (Enum, str, int) en str affichable.

    Pour les Enum, on prefere `.value` plutot que `str(e)` qui produirait
    `"SectorEnum.agriculture"`.
    """
    if raw is None:
        return None
    if hasattr(raw, "value"):
        return str(raw.value)
    return str(raw)


def _substitute_placeholders(text: str, profile: dict[str, Any]) -> str:
    """Substituer {{sector}}, {{employee_count}}, {{country}} dans une
    chaine. Valeurs absentes -> defaut neutre."""
    sector = _coerce_str(profile.get("sector")) or "votre secteur"
    employee_count = _coerce_str(profile.get("employee_count")) or "vos"
    country = _coerce_str(profile.get("country")) or "votre pays"
    return (
        text.replace("{{sector}}", sector)
        .replace("{{employee_count}}", employee_count)
        .replace("{{country}}", country)
    )


def _safe_priority(raw: str) -> ActionItemPriority:
    try:
        return ActionItemPriority(raw)
    except (ValueError, TypeError):
        logger.warning(
            "Template drift: priority=%r non reconnu, fallback=medium",
            raw,
            extra={"metric": "action_plan_template_drift", "field": "priority"},
        )
        return ActionItemPriority.medium


def _safe_category(raw: str) -> ActionItemCategory:
    try:
        return ActionItemCategory(raw)
    except (ValueError, TypeError):
        logger.warning(
            "Template drift: category=%r non reconnu, fallback=governance",
            raw,
            extra={"metric": "action_plan_template_drift", "field": "category"},
        )
        return ActionItemCategory.governance


# --- API publique ---


def generate_fallback_actions(
    profile: dict[str, Any],
    timeframe: int,
) -> list[dict[str, Any]]:
    """Generer la liste des actions du fallback (sans persistance).

    Args:
        profile: dict contenant `sector`, `employee_count`, `country`.
        timeframe: horizon du plan en mois (utilise pour borner les dates).

    Returns:
        Liste de 10 dicts prets a etre inseres comme ActionItem.
        Chaque dict contient : title, description, category, priority,
        due_date (date ISO), estimated_cost_xof, estimated_benefit.
    """
    template = _load_template()
    raw_actions = template.get("actions", [])
    today = date.today()

    actions: list[dict[str, Any]] = []
    for raw in raw_actions:
        offset_months = int(raw.get("due_date_offset_months", timeframe))
        # Borner sur le timeframe + marge de 3 mois (coherent avec service.py)
        effective_offset = min(offset_months, timeframe + 3)
        due = today + timedelta(days=effective_offset * 31)

        actions.append(
            {
                "title": _substitute_placeholders(str(raw.get("title", "")), profile)[:500],
                "description": _substitute_placeholders(
                    str(raw.get("description", "")), profile
                ),
                "category": str(raw.get("category", "governance")),
                "priority": str(raw.get("priority", "medium")),
                "due_date": due.isoformat(),
                "estimated_cost_xof": int(raw.get("estimated_cost_xof", 0) or 0),
                "estimated_benefit": _substitute_placeholders(
                    str(raw.get("estimated_benefit", "")), profile
                ),
            }
        )

    return actions


async def persist_fallback_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    timeframe: int,
    reason: str = "llm_guard_error",
) -> ActionPlan:
    """Creer un plan d'action complet a partir du template fallback.

    Charge le profil, archive l'ancien plan actif, insere un nouveau
    plan + 10 items et logue `fallback_triggered`. Tout se fait dans
    un seul commit final pour eviter qu'un crash mid-operation laisse
    l'utilisateur sans plan actif (review V8-AXE2 finding #1).

    Args:
        db: session async.
        user_id: identifiant utilisateur.
        timeframe: horizon en mois.
        reason: motif du fallback exploitable par les metriques
            (`llm_guard_error` | `count_below_min`).

    Raises:
        HTTPException 428: si le profil entreprise est manquant.
        FallbackTemplateError: si le template JSON est introuvable
            ou corrompu (le tool appelant convertit en message LLM).
    """
    from sqlalchemy.orm import selectinload

    # 1. Profil entreprise (meme contrat que le service LLM)
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile_obj = result.scalar_one_or_none()
    if profile_obj is None:
        raise HTTPException(
            status_code=428,
            detail="Profil entreprise requis pour generer un plan d'action.",
        )

    profile_dict = {
        "sector": getattr(profile_obj, "sector", None),
        "employee_count": getattr(profile_obj, "employee_count", None),
        "country": getattr(profile_obj, "country", None),
    }

    # 2. Generer les actions deterministes (peut lever FallbackTemplateError)
    actions = generate_fallback_actions(profile_dict, timeframe)

    # 3. Archiver l'ancien plan actif (DANS la meme transaction que l'insert
    # du nouveau plan : un seul commit final pour garantir l'atomicite).
    await db.execute(
        update(ActionPlan)
        .where(ActionPlan.user_id == user_id)
        .where(ActionPlan.status == PlanStatus.active)
        .values(status=PlanStatus.archived)
    )

    # 4. Creer le nouveau plan
    company_name = getattr(profile_obj, "company_name", None) or "votre entreprise"
    plan = ActionPlan(
        user_id=user_id,
        title=f"Plan d'action ESG {timeframe} mois — {company_name} (fallback)",
        timeframe=timeframe,
        status=PlanStatus.active,
        total_actions=len(actions),
        completed_actions=0,
    )
    db.add(plan)
    await db.flush()

    # 5. Inserer les items
    for idx, action in enumerate(actions):
        try:
            due = date.fromisoformat(action["due_date"])
        except (ValueError, TypeError):
            due = None

        item = ActionItem(
            plan_id=plan.id,
            title=action["title"],
            description=action["description"],
            category=_safe_category(action["category"]),
            priority=_safe_priority(action["priority"]),
            status=ActionItemStatus.todo,
            due_date=due,
            estimated_cost_xof=action.get("estimated_cost_xof"),
            estimated_benefit=action.get("estimated_benefit"),
            completion_percentage=0,
            sort_order=idx,
        )
        db.add(item)

    # 6. Single commit final (atomicite) puis recharge eager des items
    # pour que les appelants puissent lire `plan.items` en async sans
    # declencher un lazy-load detaches (review finding #10).
    await db.commit()

    reload = await db.execute(
        select(ActionPlan)
        .options(selectinload(ActionPlan.items))
        .where(ActionPlan.id == plan.id)
    )
    plan = reload.scalar_one()

    logger.warning(
        "fallback_triggered user_id=%s reason=%s final_count=%d",
        user_id,
        reason,
        len(actions),
        extra={
            "metric": "action_plan_fallback",
            "user_id": str(user_id),
            "reason": reason,
            "final_count": len(actions),
        },
    )

    return plan
