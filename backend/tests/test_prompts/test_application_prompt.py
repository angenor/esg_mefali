"""Tests pour le prompt et les tools du module candidature (US1)."""

from app.prompts.application import APPLICATION_PROMPT, build_application_prompt
from app.graph.tools.application_tools import APPLICATION_TOOLS


def test_application_prompt_contains_tool_names():
    """T002 — Le prompt application mentionne les noms des tools."""
    prompt = APPLICATION_PROMPT
    assert "submit_fund_application_draft" in prompt
    assert "generate_application_section" in prompt
    assert "update_application_section" in prompt
    assert "get_application_checklist" in prompt
    assert "simulate_financing" in prompt
    assert "export_application" in prompt


def test_application_prompt_contains_absolute_rule():
    """T002 — Le prompt application contient la REGLE ABSOLUE."""
    prompt = APPLICATION_PROMPT
    assert "RÈGLE ABSOLUE" in prompt or "REGLE ABSOLUE" in prompt


def test_submit_fund_application_draft_in_tools():
    """T003 — submit_fund_application_draft existe dans APPLICATION_TOOLS.

    H1 post-review 9.7 : renomme depuis `create_fund_application` pour eviter
    le conflit avec financing_tools.create_fund_application (nom ambigu pour le LLM).
    """
    tool_names = [t.name for t in APPLICATION_TOOLS]
    assert "submit_fund_application_draft" in tool_names


def test_application_tools_count():
    """T003 — APPLICATION_TOOLS contient 6 tools."""
    assert len(APPLICATION_TOOLS) == 6


def test_application_prompt_active_role():
    """Le prompt a un ROLE actif, pas passif."""
    prompt = APPLICATION_PROMPT
    # Ne doit plus contenir "Tu informes" comme role principal
    assert "Tu informes l'utilisateur sur l'etat" not in prompt
