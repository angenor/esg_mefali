"""Tests pour le prompt financement (US3)."""

from app.prompts.financing import FINANCING_PROMPT, build_financing_prompt


def test_financing_prompt_no_detailed_fund_list():
    """T011 — Le prompt financement NE CONTIENT PLUS la liste détaillée des 12 fonds."""
    prompt = FINANCING_PROMPT
    # Ces noms de fonds spécifiques ne doivent plus être listés en dur
    assert "SUNREF (AFD/Proparco)" not in prompt
    assert "FNDE (Cote d'Ivoire)" not in prompt or "FNDE (Côte d'Ivoire)" not in prompt
    assert "Gold Standard, Verra, IFC Green Bond" not in prompt


def test_financing_prompt_no_detailed_intermediary_list():
    """T011 — Le prompt financement NE CONTIENT PLUS la liste détaillée des 14 intermédiaires."""
    prompt = FINANCING_PROMPT
    # Les noms détaillés d'intermédiaires ne doivent plus être listés
    assert "SIB, SGBCI, Banque Atlantique" not in prompt
    assert "South Pole, EcoAct" not in prompt


def test_financing_prompt_contains_absolute_rule():
    """T011 — Le prompt financement contient REGLE ABSOLUE."""
    prompt = build_financing_prompt()
    assert "REGLE ABSOLUE" in prompt or "RÈGLE ABSOLUE" in prompt


def test_financing_prompt_references_search_tool():
    """T011 — Le prompt financement référence search_compatible_funds."""
    prompt = FINANCING_PROMPT
    assert "search_compatible_funds" in prompt
