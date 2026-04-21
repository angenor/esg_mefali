"""Tests d'integration registre → 7 modules metier (AC3 Story 10.8).

Pour chacun des 7 build_<module>_prompt(), verifie que les marqueurs attendus
des instructions transverses sont bien presents dans le prompt final concatene
(regle d'or 10.5 : effet observable, pas structure intermediaire).
"""

from __future__ import annotations

import pytest

from app.prompts.action_plan import build_action_plan_prompt
from app.prompts.application import build_application_prompt
from app.prompts.carbon import build_carbon_prompt
from app.prompts.credit import build_credit_prompt
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.financing import build_financing_prompt
from app.prompts.system import build_system_prompt


STYLE_MARKER = "## STYLE DE COMMUNICATION"
WIDGET_MARKER = "## OUTIL INTERACTIF"
GUIDED_TOUR_MARKER = "## OUTIL GUIDAGE VISUEL"


@pytest.mark.unit
def test_system_prompt_integration_all_three_instructions() -> None:
    """system.py (chat) post HIGH-10.8-1 : STYLE (conditionnel post-onboarding)
    + WIDGET + GUIDED_TOUR — toutes via le registre (module='chat').
    WIDGET etait avant injecte manuellement dans nodes.py:1197."""
    prompt = build_system_prompt(
        user_profile={"company_name": "X", "sector": "recyclage"}
    )
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt


@pytest.mark.unit
def test_esg_scoring_prompt_integration_all_three_instructions() -> None:
    """esg_scoring : 3 instructions transverses via registry (style+widget+guided_tour)."""
    prompt = build_esg_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt


@pytest.mark.unit
def test_carbon_prompt_integration_all_three_instructions() -> None:
    """carbon : 3 instructions transverses via registry."""
    prompt = build_carbon_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt


@pytest.mark.unit
def test_financing_prompt_integration_all_three_instructions() -> None:
    """financing : 3 instructions transverses via registry."""
    prompt = build_financing_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt


@pytest.mark.unit
def test_application_prompt_integration_excludes_guided_tour() -> None:
    """application : style + widget SEULEMENT (parite historique — pas de guided_tour)."""
    prompt = build_application_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER not in prompt
    # Defense en profondeur : pas de reference au tool trigger_guided_tour
    assert "trigger_guided_tour" not in prompt


@pytest.mark.unit
def test_credit_prompt_integration_all_three_instructions() -> None:
    """credit : 3 instructions transverses via registry."""
    prompt = build_credit_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt


@pytest.mark.unit
def test_action_plan_prompt_integration_all_three_instructions() -> None:
    """action_plan : 3 instructions transverses via registry."""
    prompt = build_action_plan_prompt()
    assert STYLE_MARKER in prompt
    assert WIDGET_MARKER in prompt
    assert GUIDED_TOUR_MARKER in prompt
