"""Tests comportementaux de build_prompt() (AC2 Story 10.8).

Verifie l'ordre d'injection deterministe (priority ASC, name ASC), le filtrage
par applies_to (application exclut guided_tour), la concatenation avec base,
et la tolerance a variables=None/{}.
"""

from __future__ import annotations

import pytest

from app.prompts.registry import build_prompt


@pytest.mark.unit
def test_build_prompt_orders_style_then_widget_then_guided_tour_for_chat() -> None:
    """AC2 : pour module='chat', ordre strict style (10) → widget (50) → guided_tour (90)."""
    prompt = build_prompt(module="chat")

    idx_style = prompt.find("## STYLE DE COMMUNICATION")
    idx_widget = prompt.find("## OUTIL INTERACTIF")
    idx_guided = prompt.find("## OUTIL GUIDAGE VISUEL")

    assert idx_style >= 0, "STYLE marqueur absent"
    assert idx_widget >= 0, "WIDGET marqueur absent"
    assert idx_guided >= 0, "GUIDED_TOUR marqueur absent"
    assert idx_style < idx_widget < idx_guided, (
        f"Ordre incorrect: style={idx_style}, widget={idx_widget}, guided={idx_guided}"
    )


@pytest.mark.unit
def test_build_prompt_application_excludes_guided_tour() -> None:
    """AC2 : module='application' exclut guided_tour (parite historique)."""
    prompt = build_prompt(module="application")

    assert "## STYLE DE COMMUNICATION" in prompt
    assert "## OUTIL INTERACTIF" in prompt
    assert "## OUTIL GUIDAGE VISUEL" not in prompt
    assert "trigger_guided_tour" not in prompt


@pytest.mark.unit
def test_build_prompt_accepts_none_variables_when_no_required_vars() -> None:
    """AC2 : variables=None sans required_vars → pas d'erreur (instruction vide OK)."""
    prompt_none = build_prompt(module="application", variables=None)
    prompt_empty = build_prompt(module="application", variables={})
    assert prompt_none == prompt_empty
    assert len(prompt_none) > 0


@pytest.mark.unit
def test_build_prompt_prepends_base_with_double_newline() -> None:
    """AC2 : base='INTRO' → 'INTRO\\n\\n<instructions>'."""
    prompt_with_base = build_prompt(module="application", base="INTRO CUSTOM")
    prompt_no_base = build_prompt(module="application")

    assert prompt_with_base.startswith("INTRO CUSTOM\n\n")
    assert prompt_with_base.endswith(prompt_no_base)
