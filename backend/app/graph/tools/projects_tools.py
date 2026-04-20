"""Tools LangChain pour le noeud `project` (squelette Epic 11).

Story 10.2 - module `projects/` squelette (AC5).
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].

Expose un unique tool stub `create_project` **wrappe with_retry** (regle
d'or 9.7 : instrumentation DES la creation, pas de dette a rattraper).
La journalisation `tool_call_logs` est automatique via le wrapper — ne
JAMAIS appeler `log_tool_call` manuellement dans le corps du tool (CQ-11).

Epic 11 Story 11-1 reecrira `create_project` pour invoquer le service
metier `app.modules.projects.service.create_project`.
"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import with_retry


@tool
async def create_project(
    name: str,
    state: str = "idée",
    config: RunnableConfig | None = None,
) -> str:
    """Creer un projet pour l'entreprise (stub Epic 11).

    Args:
        name: Nom du projet (ex. « Ferme solaire 50 kW »).
        state: Etat initial (par defaut « idée »).
    Returns:
        Message d'etat du squelette (pas de raise — evite crash cote LLM).
    """
    # AC5 : corps stub explicite, Epic 11 invoquera le service metier.
    return "Module projects non encore implémenté (Epic 11)."


# AC5 : instrumentation with_retry + node_name="project" des la creation.
PROJECTS_TOOLS = [
    with_retry(create_project, max_retries=2, node_name="project"),
]
