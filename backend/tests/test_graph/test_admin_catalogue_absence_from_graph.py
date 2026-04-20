"""Test smoke — AUCUN admin_node ni tool admin_catalogue (Story 10.4 AC6, AC8).

Clarification 2 architecture.md : le module admin_catalogue est UI-only, sans
couplage LLM. Defense anti-regression : si quelqu'un ajoute `admin_node`,
`admin_catalogue_node` ou `catalogue_node` au graphe, ou un tool admin sous
`app/graph/tools/`, ce test echoue immediatement.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_no_admin_node_in_compiled_graph():
    """Test 16 — compiled_graph.nodes ne contient aucun admin/admin_catalogue/catalogue."""
    from app.graph.graph import create_compiled_graph

    compiled = await create_compiled_graph()
    nodes = set(compiled.nodes.keys())

    forbidden = {"admin", "admin_catalogue", "catalogue"}
    intersection = nodes & forbidden
    assert intersection == set(), (
        f"Le graphe compile ne doit contenir aucun noeud admin_catalogue. "
        f"Noeuds interdits trouves : {intersection}. "
        f"Le module admin_catalogue est UI-only (Clarification 2 architecture.md)."
    )

    # Verifier egalement qu'aucun module Python n'existe sous app/graph/tools/admin*
    tools_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "graph"
        / "tools"
    )
    admin_files = list(tools_dir.glob("admin*.py"))
    assert admin_files == [], (
        f"Aucun fichier admin*.py ne doit exister sous app/graph/tools/ "
        f"(module UI-only). Fichiers trouves : {[f.name for f in admin_files]}"
    )


def test_no_admin_catalogue_tool_in_instrumented_tools():
    """Test 17 — INSTRUMENTED_TOOLS count figé à 36 post-10.4 + aucun tool admin_catalogue."""
    from app.graph.tools import INSTRUMENTED_TOOLS

    # AC8 #17 — count fige post-10.4. La valeur inclut TOUS les tools :
    # fonctionnels par module (36 — documentes README) + INTERACTIVE_TOOLS
    # (1 : ask_interactive_question) + GUIDED_TOUR_TOOLS (1 :
    # trigger_guided_tour) = 38. Si une story future ajoute un tool legitime,
    # mettre a jour cette valeur. Si admin_catalogue a ajoute un tool,
    # REJETER (module UI-only — Clarification 2 architecture.md).
    assert len(INSTRUMENTED_TOOLS) == 38, (
        f"INSTRUMENTED_TOOLS count a change ({len(INSTRUMENTED_TOOLS)} vs 38 attendu post-10.4). "
        f"Si intentionnel (nouvelle story avec tool legitime), mettre a jour cette valeur. "
        f"Si admin_catalogue a ajoute un tool, REJETER — module UI-only (Clarification 2)."
    )

    for tool in INSTRUMENTED_TOOLS:
        name = getattr(tool, "name", "")
        assert not name.startswith("admin_"), (
            f"Tool admin_catalogue detecte dans INSTRUMENTED_TOOLS : {name}. "
            f"Le module admin_catalogue est UI-only (Clarification 2)."
        )
        assert "catalogue" not in name.lower(), (
            f"Tool catalogue detecte dans INSTRUMENTED_TOOLS : {name}."
        )
