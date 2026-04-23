"""Tests vérifiant que LANGUAGE_INSTRUCTION est en tête de chaque builder spécialiste."""

import importlib

import pytest

from app.prompts.system import LANGUAGE_INSTRUCTION
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.carbon import build_carbon_prompt
from app.prompts.financing import build_financing_prompt
from app.prompts.application import build_application_prompt
from app.prompts.credit import build_credit_prompt
from app.prompts.action_plan import build_action_plan_prompt

_BUILDERS = [
    build_esg_prompt,
    build_carbon_prompt,
    build_financing_prompt,
    build_application_prompt,
    build_credit_prompt,
    build_action_plan_prompt,
]


def test_all_specialist_builders_start_with_language_instruction():
    """Tous les builders spécialistes doivent commencer par LANGUAGE_INSTRUCTION."""
    for builder in _BUILDERS:
        prompt = builder()
        assert prompt.startswith(LANGUAGE_INSTRUCTION), (
            f"{builder.__name__} ne commence pas par LANGUAGE_INSTRUCTION"
        )


def test_all_specialist_builders_contain_language_instruction_exactly_once():
    """LANGUAGE_INSTRUCTION ne doit apparaître qu'une seule fois (garde contre duplication future)."""
    for builder in _BUILDERS:
        prompt = builder()
        count = prompt.count(LANGUAGE_INSTRUCTION)
        assert count == 1, (
            f"{builder.__name__} contient LANGUAGE_INSTRUCTION {count} fois (attendu 1)"
        )


@pytest.mark.parametrize("builder_name,import_path", [
    ("build_esg_prompt", "app.prompts.esg_scoring"),
    ("build_carbon_prompt", "app.prompts.carbon"),
    ("build_financing_prompt", "app.prompts.financing"),
    ("build_application_prompt", "app.prompts.application"),
    ("build_credit_prompt", "app.prompts.credit"),
    ("build_action_plan_prompt", "app.prompts.action_plan"),
])
def test_specialist_builder_starts_with_language_instruction_parametrized(
    builder_name: str, import_path: str
):
    """Vérifie individuellement chaque builder (facilite l'identification d'un builder défaillant)."""
    module = importlib.import_module(import_path)
    builder = getattr(module, builder_name)
    prompt = builder()
    assert prompt.startswith(LANGUAGE_INSTRUCTION), (
        f"{builder_name} ne commence pas par LANGUAGE_INSTRUCTION"
    )
