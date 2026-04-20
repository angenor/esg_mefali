"""Tools LangChain pour le noeud `maturity` (squelette Epic 12).

Story 10.3 - module `maturity/` squelette (AC4).
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Expose un unique tool stub `declare_maturity_level` **wrappe with_retry**
(regle d'or 9.7 : instrumentation DES la creation, pas de dette a rattraper
— valide en 10.2 avec `projects_tools.create_project`).

La journalisation `tool_call_logs` est automatique via le wrapper — ne
JAMAIS appeler `log_tool_call` manuellement dans le corps du tool (CQ-11).

Epic 12 Story 12.1 reecrira `declare_maturity_level` pour invoquer le
service metier `app.modules.maturity.service.declare_maturity_level`.
"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import with_retry


@tool
async def declare_maturity_level(
    level: str,
    config: RunnableConfig | None = None,
) -> str:
    """Declarer le niveau de maturite administrative de l'entreprise (stub Epic 12).

    Args:
        level: Code du niveau (ex. « informel », « rccm_nif », « comptes_cnps »,
               « ohada_audite »). Validation effective differee a Epic 12
               (match contre `AdminMaturityLevel.code`).
    Returns:
        Message d'etat du squelette (pas de raise — evite crash cote LLM,
        lecon 10.2).
    """
    # AC4 : corps stub explicite, Epic 12 invoquera le service metier.
    return "Module maturity non encore implémenté (Epic 12)."


# AC4 : instrumentation with_retry + node_name="maturity" des la creation.
MATURITY_TOOLS = [
    with_retry(declare_maturity_level, max_retries=2, node_name="maturity"),
]
