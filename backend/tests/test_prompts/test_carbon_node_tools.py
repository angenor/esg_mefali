"""Tests pour les tool_instructions du carbon_node (US2)."""


def test_carbon_node_source_contains_absolute_rule():
    """T008 — Les tool_instructions du carbon_node contiennent REGLE ABSOLUE."""
    import inspect
    from app.graph.nodes import carbon_node
    source = inspect.getsource(carbon_node)
    assert "REGLE ABSOLUE" in source or "RÈGLE ABSOLUE" in source


def test_carbon_node_source_contains_save_emission_entry():
    """T008 — Les tool_instructions du carbon_node mentionnent save_emission_entry."""
    import inspect
    from app.graph.nodes import carbon_node
    source = inspect.getsource(carbon_node)
    assert "save_emission_entry" in source
