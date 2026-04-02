"""Tests pour les tool_instructions du esg_scoring_node (US1)."""

import ast
import textwrap

from app.graph.nodes import esg_scoring_node


def test_esg_node_source_contains_batch_save_in_tools():
    """T004 — Les tool_instructions du esg_scoring_node incluent batch_save_esg_criteria."""
    import inspect
    source = inspect.getsource(esg_scoring_node)
    assert "batch_save_esg_criteria" in source


def test_esg_node_source_contains_absolute_rule():
    """T004 — Les tool_instructions du esg_scoring_node contiennent REGLE ABSOLUE."""
    import inspect
    source = inspect.getsource(esg_scoring_node)
    assert "REGLE ABSOLUE" in source or "RÈGLE ABSOLUE" in source
