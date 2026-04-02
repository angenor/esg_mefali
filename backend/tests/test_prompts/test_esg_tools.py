"""Tests pour les tools et le prompt du module ESG (US3)."""

from app.graph.tools.esg_tools import ESG_TOOLS
from app.prompts.esg_scoring import ESG_SCORING_PROMPT


def test_batch_save_esg_criteria_in_tools():
    """T010 — batch_save_esg_criteria existe dans ESG_TOOLS."""
    tool_names = [t.name for t in ESG_TOOLS]
    assert "batch_save_esg_criteria" in tool_names


def test_esg_tools_count():
    """T010 — ESG_TOOLS contient 5 tools (4 existants + batch)."""
    assert len(ESG_TOOLS) == 5


def test_batch_tool_accepts_criteria_list():
    """T010 — Le tool batch accepte une liste de criteres."""
    batch_tool = None
    for t in ESG_TOOLS:
        if t.name == "batch_save_esg_criteria":
            batch_tool = t
            break
    assert batch_tool is not None
    schema = batch_tool.args_schema.schema() if hasattr(batch_tool, 'args_schema') else {}
    # Verifier que 'criteria' est dans les parametres
    props = schema.get("properties", {})
    assert "criteria" in props, f"Le tool batch doit avoir un parametre 'criteria', got: {list(props.keys())}"


def test_esg_prompt_contains_batch_instruction():
    """T011 — Le prompt ESG contient l'instruction d'utiliser le batch."""
    assert "batch_save_esg_criteria" in ESG_SCORING_PROMPT


def test_esg_prompt_mentions_batch_strategy():
    """T011 — Le prompt ESG mentionne la strategie de sauvegarde par lot."""
    prompt_lower = ESG_SCORING_PROMPT.lower()
    assert "sauvegarde par lot" in prompt_lower or "batch" in prompt_lower
