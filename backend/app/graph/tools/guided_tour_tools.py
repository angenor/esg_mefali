"""Tool LangChain trigger_guided_tour (feature 019).

Permet au LLM de declencher un parcours guide visuel pour l'utilisateur.
Un marker SSE est embarque dans le retour du tool, intercepte par stream_graph_events.
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry

logger = logging.getLogger(__name__)

# Format attendu pour un tour_id : identifiant snake_case, evite l'injection de
# sequences `-->` / `<!--` qui casseraient le marker SSE `<!--SSE:...-->`
_VALID_TOUR_ID = re.compile(r"^[a-z][a-z0-9_]*$")


@tool
async def trigger_guided_tour(
    tour_id: str,
    context: dict | None = None,
    config: RunnableConfig = None,  # type: ignore[assignment]
) -> str:
    """Declencher un parcours guide visuel pour l'utilisateur.

    Utilise cet outil pour lancer un guidage interactif qui montre
    visuellement a l'utilisateur les elements de l'interface.

    Args:
        tour_id: Identifiant du parcours (ex: show_esg_results, show_carbon_results).
        context: Donnees contextuelles optionnelles pour personnaliser le parcours.
    """
    # Validation du tour_id (format + non vide) pour eviter l'injection SSE
    if not tour_id or not _VALID_TOUR_ID.match(tour_id):
        logger.warning("trigger_guided_tour: tour_id invalide (%r)", tour_id)
        return "Erreur : tour_id invalide (format attendu : snake_case minuscule)."

    try:
        get_db_and_user(config)
    except ValueError as exc:
        logger.warning("trigger_guided_tour: config manquante (%s)", exc)
        return "Erreur : contexte technique indisponible, retente."

    sse_payload = {
        "__sse_guided_tour__": True,
        "type": "guided_tour",
        "tour_id": tour_id,
        "context": context or {},
    }
    # Serialisation defensive :
    #   - default=str pour tolerer datetime / bytes / UUID dans context sans crasher
    #   - remplacement `-->` → `--\u003e` pour empecher qu'une valeur de context
    #     contenant cette sequence ne tronque le marker SSE `<!--SSE:...-->`.
    #     Le decodeur JSON cote client restituera `>` correctement.
    sse_marker = json.dumps(sse_payload, default=str).replace("-->", "--\\u003e")

    # H3 (post-review 9.7) : log inline supprime ; le wrapper `with_retry`
    # emet deja la ligne success avec les 12 colonnes (AC4).
    return f"Parcours guide '{tour_id}' declenche pour l'utilisateur.\n\n<!--SSE:{sse_marker}-->"


GUIDED_TOUR_TOOLS = [with_retry(trigger_guided_tour, max_retries=2, node_name="")]
