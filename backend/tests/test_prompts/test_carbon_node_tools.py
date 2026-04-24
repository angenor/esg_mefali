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


def test_carbon_prompt_bans_consumo_vocabulary():
    """BUG-V3-003 — Le prompt bannit explicitement "consumo" (pt/es)."""
    from app.prompts.carbon import CARBON_PROMPT
    # Le prompt doit contenir la regle de vocabulaire et le mot interdit.
    assert "VOCABULAIRE OBLIGATOIRE" in CARBON_PROMPT
    assert "consumo" in CARBON_PROMPT  # liste comme interdit
    assert "INTERDITS" in CARBON_PROMPT or "INTERDIT" in CARBON_PROMPT


def test_build_carbon_prompt_contains_vocabulary_rule():
    """BUG-V3-003 — build_carbon_prompt() propage la regle de vocabulaire."""
    from app.prompts.carbon import build_carbon_prompt
    prompt = build_carbon_prompt()
    assert "VOCABULAIRE OBLIGATOIRE" in prompt
    assert "consommation" in prompt.lower()
