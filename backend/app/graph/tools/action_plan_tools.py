"""Tools LangChain pour le noeud plan d'action.

Trois tools exposes au LLM :
- generate_action_plan : generer un plan d'action ESG
- update_action_item : mettre a jour le statut d'une action
- get_action_plan : consulter le plan d'action actif
"""

import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user

logger = logging.getLogger(__name__)


@tool
async def generate_action_plan(timeframe: int, config: RunnableConfig) -> str:
    """Generer un plan d'action ESG personnalise pour l'entreprise.

    Utilise cet outil quand l'utilisateur demande a creer ou generer un plan
    d'action, une feuille de route, ou un programme d'amelioration ESG.
    Le plan est sauvegarde en base et visible sur /action-plan.

    Args:
        timeframe: Horizon du plan en mois (6, 12 ou 24).
    """
    from app.modules.action_plan.service import generate_action_plan as gen_plan

    try:
        db, user_id = get_db_and_user(config)

        plan = await gen_plan(db=db, user_id=user_id, timeframe=timeframe)

        items_preview = []
        for item in (plan.items or [])[:5]:
            status = item.status.value if hasattr(item.status, "value") else item.status
            items_preview.append(f"  - {item.title} ({item.category}, {status})")
        items_text = "\n".join(items_preview) if items_preview else "  Aucune action generee."

        return (
            f"Plan d'action genere avec succes !\n"
            f"- Titre : {plan.title}\n"
            f"- Horizon : {plan.timeframe} mois\n"
            f"- Nombre d'actions : {plan.total_actions}\n"
            f"- Premieres actions :\n{items_text}\n\n"
            f"Le plan complet est visible sur la page /action-plan."
        )
    except Exception as e:
        logger.exception("Erreur lors de la generation du plan d'action")
        return f"Erreur lors de la generation du plan d'action : {e}"


@tool
async def update_action_item(
    action_id: str,
    config: RunnableConfig,
    status: str | None = None,
    completion_percentage: int | None = None,
) -> str:
    """Mettre a jour le statut ou la progression d'une action du plan.

    Utilise cet outil quand l'utilisateur indique avoir progresse sur une action,
    l'avoir completee, ou souhaite changer son statut.

    Args:
        action_id: Identifiant UUID de l'action a mettre a jour.
        status: Nouveau statut (pending, in_progress, completed, cancelled).
        completion_percentage: Pourcentage de completion (0-100).
    """
    from app.modules.action_plan.service import update_action_item as update_item

    try:
        db, user_id = get_db_and_user(config)

        updates: dict = {}
        if status is not None:
            updates["status"] = status
        if completion_percentage is not None:
            updates["completion_percentage"] = completion_percentage

        if not updates:
            return "Aucune modification fournie. Precisez le statut ou le pourcentage de completion."

        item = await update_item(
            db=db,
            item_id=uuid.UUID(action_id),
            user_id=user_id,
            updates=updates,
        )

        item_status = item.status.value if hasattr(item.status, "value") else item.status

        return (
            f"Action mise a jour avec succes :\n"
            f"- Titre : {item.title}\n"
            f"- Statut : {item_status}\n"
            f"- Completion : {item.completion_percentage}%"
        )
    except Exception as e:
        logger.exception("Erreur lors de la mise a jour de l'action %s", action_id)
        return f"Erreur lors de la mise a jour de l'action : {e}"


@tool
async def get_action_plan(config: RunnableConfig) -> str:
    """Consulter le plan d'action actif de l'utilisateur et sa progression.

    Utilise cet outil quand l'utilisateur demande a voir son plan d'action,
    sa progression, ou les prochaines actions a realiser.
    Ne necessite aucun parametre.
    """
    from app.modules.action_plan.service import get_active_plan

    try:
        db, user_id = get_db_and_user(config)

        plan = await get_active_plan(db=db, user_id=user_id)

        if plan is None:
            return (
                "Aucun plan d'action actif trouve. "
                "Proposez a l'utilisateur de generer un plan d'action "
                "en precisant l'horizon souhaite (6, 12 ou 24 mois)."
            )

        completed = plan.completed_actions
        total = plan.total_actions
        pct = int((completed / total) * 100) if total > 0 else 0

        # Lister les actions non completees
        pending_items = []
        for item in (plan.items or []):
            item_status = item.status.value if hasattr(item.status, "value") else item.status
            if item_status != "completed":
                pending_items.append(
                    f"  - {item.title} ({item.category}, {item_status}, {item.completion_percentage}%)"
                )

        pending_text = "\n".join(pending_items[:5]) if pending_items else "  Toutes les actions sont completees !"

        return (
            f"Plan d'action actif :\n"
            f"- Titre : {plan.title}\n"
            f"- Horizon : {plan.timeframe} mois\n"
            f"- Progression : {completed}/{total} actions ({pct}%)\n"
            f"- Prochaines actions :\n{pending_text}"
        )
    except Exception as e:
        logger.exception("Erreur lors de la consultation du plan d'action")
        return f"Erreur lors de la consultation du plan d'action : {e}"


ACTION_PLAN_TOOLS = [generate_action_plan, update_action_item, get_action_plan]
