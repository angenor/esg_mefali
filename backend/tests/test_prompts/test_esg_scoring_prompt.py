"""Tests pour le prompt ESG scoring (US1)."""

from app.prompts.esg_scoring import ESG_SCORING_PROMPT, build_esg_prompt


def test_esg_prompt_contains_absolute_rule():
    """T003 — Le prompt ESG contient 'REGLE ABSOLUE'."""
    prompt = build_esg_prompt()
    assert "REGLE ABSOLUE" in prompt or "RÈGLE ABSOLUE" in prompt


def test_esg_prompt_mentions_batch_save():
    """T003 — Le prompt ESG mentionne batch_save_esg_criteria."""
    prompt = build_esg_prompt()
    assert "batch_save_esg_criteria" in prompt


def test_esg_prompt_save_before_visual():
    """T003 — La section SAUVEGARDE apparaît avant INSTRUCTIONS VISUELLES."""
    prompt = ESG_SCORING_PROMPT
    save_pos = prompt.find("SAUVEGARDE")
    visual_pos = prompt.find("INSTRUCTIONS VISUELLES")
    assert save_pos > 0, "Section SAUVEGARDE absente"
    assert visual_pos > 0, "Section INSTRUCTIONS VISUELLES absente"
    assert save_pos < visual_pos, "SAUVEGARDE doit apparaître avant INSTRUCTIONS VISUELLES"
