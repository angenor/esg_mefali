"""Tests pour le prompt du module credit vert (US2)."""

from app.prompts.credit import CREDIT_PROMPT, build_credit_prompt


def test_credit_prompt_contains_tool_names():
    """T007 — Le prompt credit mentionne les noms des 3 tools."""
    prompt = CREDIT_PROMPT
    assert "generate_credit_score" in prompt
    assert "get_credit_score" in prompt
    assert "generate_credit_certificate" in prompt


def test_credit_prompt_contains_absolute_rule():
    """T007 — Le prompt credit contient la REGLE ABSOLUE."""
    prompt = CREDIT_PROMPT
    assert "RÈGLE ABSOLUE" in prompt or "REGLE ABSOLUE" in prompt


def test_credit_prompt_mentions_data_sources():
    """Le prompt credit mentionne les sources de donnees."""
    prompt = CREDIT_PROMPT
    assert "profil" in prompt.lower()
    assert "ESG" in prompt
    assert "carbone" in prompt.lower()


def test_credit_prompt_has_tools_section():
    """Le prompt credit a une section OUTILS DISPONIBLES."""
    prompt = CREDIT_PROMPT
    assert "OUTILS DISPONIBLES" in prompt
