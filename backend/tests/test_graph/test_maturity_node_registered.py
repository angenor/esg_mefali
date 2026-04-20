"""Smoke test : maturity_node enregistre dans le graphe (Story 10.3 AC5, AC8)."""

from __future__ import annotations


def test_maturity_node_registered_in_graph_but_not_routable():
    """Test 14 — maturity + maturity_tools presents AND non-atteignable depuis router.

    AC5 §5 interdit d'ajouter 'maturity' dans `_route_after_router`. Le node
    existe dans le graphe mais n'est pas atteignable depuis une conversation
    normale (pattern squelette — Epic 12 ajoutera l'heuristique).
    """
    from app.graph.graph import _route_after_router, build_graph

    graph = build_graph()
    nodes = set(graph.nodes.keys())

    # Presence dans le graphe (AC5 §enregistrement)
    assert "maturity" in nodes, "maturity node absent du StateGraph"
    assert "maturity_tools" in nodes, "maturity_tools (ToolNode) absent du StateGraph"

    # Non-atteignabilite depuis le router pour des messages aleatoires (AC5 §interdit)
    # Aucun des flags `_route_*` connus ne declenche 'maturity'.
    sample_states = [
        {
            "messages": [],
            "_route_esg": False,
            "_route_carbon": False,
            "_route_financing": False,
            "_route_application": False,
            "_route_credit": False,
            "_route_action_plan": False,
            "has_document": False,
        },
        {
            "messages": [],
            "_route_esg": True,  # flag ESG actif
        },
        {
            "messages": [],
            "_route_carbon": True,  # flag carbon actif
        },
    ]
    for state in sample_states:
        result = _route_after_router(state)
        assert result != "maturity", (
            f"_route_after_router ne doit jamais router vers 'maturity' "
            f"tant qu'Epic 12 n'active pas l'heuristique (obtenu : {result})"
        )
