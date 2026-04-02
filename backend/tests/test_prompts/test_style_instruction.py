"""Tests pour l'injection de STYLE_INSTRUCTION dans les prompts."""

import pytest

from app.prompts.system import STYLE_INSTRUCTION, build_system_prompt, _has_minimum_profile
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.carbon import build_carbon_prompt
from app.prompts.financing import build_financing_prompt
from app.prompts.credit import build_credit_prompt
from app.prompts.application import build_application_prompt
from app.prompts.action_plan import build_action_plan_prompt


# --- US1 : Prompts specialises ---


def test_style_instruction_in_esg_prompt():
    """T004 — build_esg_prompt() contient STYLE_INSTRUCTION."""
    prompt = build_esg_prompt()
    assert STYLE_INSTRUCTION in prompt


def test_style_instruction_in_carbon_prompt():
    """T005 — build_carbon_prompt() contient STYLE_INSTRUCTION."""
    prompt = build_carbon_prompt()
    assert STYLE_INSTRUCTION in prompt


def test_style_instruction_in_all_specialized_prompts():
    """T006 — Les 6 modules specialises contiennent STYLE_INSTRUCTION."""
    prompts = {
        "esg": build_esg_prompt(),
        "carbon": build_carbon_prompt(),
        "financing": build_financing_prompt(),
        "credit": build_credit_prompt(),
        "application": build_application_prompt(),
        "action_plan": build_action_plan_prompt(),
    }
    for name, prompt in prompts.items():
        assert STYLE_INSTRUCTION in prompt, f"STYLE_INSTRUCTION absent dans {name}"


def test_style_instruction_contains_examples():
    """T007 — STYLE_INSTRUCTION contient au moins un exemple BON et un MAUVAIS."""
    assert "BON" in STYLE_INSTRUCTION
    assert "MAUVAIS" in STYLE_INSTRUCTION


# --- US2 : Chat general conditionnel ---


def test_style_instruction_present_with_profile():
    """T014 — build_system_prompt() inclut STYLE_INSTRUCTION quand profil >= 2 champs."""
    profile = {"sector": "recyclage", "city": "Abidjan"}
    prompt = build_system_prompt(user_profile=profile)
    assert "STYLE DE COMMUNICATION" in prompt


def test_style_instruction_absent_without_profile():
    """T015 — build_system_prompt() exclut STYLE_INSTRUCTION sans profil."""
    prompt = build_system_prompt()
    assert "STYLE DE COMMUNICATION" not in prompt


def test_style_instruction_absent_minimal_profile():
    """T016 — build_system_prompt() exclut STYLE_INSTRUCTION si profil < 2 champs."""
    profile = {"sector": "recyclage"}
    prompt = build_system_prompt(user_profile=profile)
    assert "STYLE DE COMMUNICATION" not in prompt


# --- US3 : Couverture des regles ---


def test_style_instruction_contains_rules():
    """T018 — STYLE_INSTRUCTION couvre les mots-cles de chaque regle."""
    text = STYLE_INSTRUCTION.lower()
    # FR-001 / FR-009 : concision
    assert "concr" in text  # "concrète" ou "concret"
    # FR-002 : redondance visuels
    assert "bloc visuel" in text
    # FR-003 : politesse
    assert "politesse" in text or "formule" in text
    # FR-004 : recapitulatif
    assert "récapitule" in text or "recapitule" in text or "récapitul" in text
    # FR-005 : confirmation courte
    assert "confirmation" in text or "1 seule phrase" in text
    # FR-006 : emoji
    assert "emoji" in text
    # FR-009 : information nouvelle
    assert "information nouvelle" in text


# --- Helper _has_minimum_profile ---


@pytest.mark.parametrize("profile,expected", [
    ({}, False),
    ({"sector": "recyclage"}, False),
    ({"sector": "recyclage", "city": "Abidjan"}, True),
    ({"sector": "", "city": None}, False),
    ({"sector": "recyclage", "city": "Abidjan", "employee_count": 25}, True),
    ({"has_waste_management": False, "sector": ""}, False),
])
def test_has_minimum_profile(profile: dict, expected: bool):
    """Verifie la logique de detection post-onboarding."""
    assert _has_minimum_profile(profile) == expected
