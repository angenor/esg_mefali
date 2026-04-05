"""Tests pour les instructions tool calling du module carbone (US2)."""


def test_carbon_prompt_contains_absolute_rule():
    """T008 — Le prompt carbone contient REGLE ABSOLUE."""
    from app.prompts.carbon import CARBON_PROMPT
    assert "REGLE ABSOLUE" in CARBON_PROMPT or "RÈGLE ABSOLUE" in CARBON_PROMPT


def test_carbon_prompt_contains_save_emission_entry():
    """T008 — Le prompt carbone mentionne save_emission_entry."""
    from app.prompts.carbon import CARBON_PROMPT
    assert "save_emission_entry" in CARBON_PROMPT


def test_carbon_prompt_contains_workflow():
    """Le prompt carbone contient un workflow obligatoire numerote."""
    from app.prompts.carbon import CARBON_PROMPT
    assert "WORKFLOW OBLIGATOIRE" in CARBON_PROMPT
    assert "create_carbon_assessment" in CARBON_PROMPT
    assert "finalize_carbon_assessment" in CARBON_PROMPT
