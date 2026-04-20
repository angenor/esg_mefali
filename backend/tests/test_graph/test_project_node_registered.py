"""Smoke test : project_node enregistré dans le graphe (Story 10.2 AC6, AC8)."""

from __future__ import annotations


def test_project_node_registered_in_graph():
    """Bonus — project + project_tools présents dans le StateGraph compilé."""
    from app.graph.graph import build_graph

    graph = build_graph()
    nodes = set(graph.nodes.keys())
    assert "project" in nodes
    assert "project_tools" in nodes
