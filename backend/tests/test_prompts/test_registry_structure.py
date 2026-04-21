"""Tests structure du registre (AC1 Story 10.8).

Verifie l'immutabilite et la composition du registre central :
- INSTRUCTION_REGISTRY est un tuple (pas list ni dict).
- InstructionEntry est frozen (assignation lève FrozenInstanceError).
- Les 3 entrees initiales (style/widget/guided_tour) sont presentes avec les
  applies_to exacts.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.prompts.registry import INSTRUCTION_REGISTRY, InstructionEntry


@pytest.mark.unit
def test_registry_is_frozen_tuple() -> None:
    """AC1 : INSTRUCTION_REGISTRY est bien un tuple (immutable)."""
    assert type(INSTRUCTION_REGISTRY) is tuple
    # Defense en profondeur : tentative de reassignation d'un index.
    with pytest.raises(TypeError):
        INSTRUCTION_REGISTRY[0] = "mutated"  # type: ignore[index]


@pytest.mark.unit
def test_instruction_entry_is_frozen_dataclass() -> None:
    """AC1 : InstructionEntry frozen → assignation lève FrozenInstanceError."""
    entry = INSTRUCTION_REGISTRY[0]
    with pytest.raises(FrozenInstanceError):
        entry.name = "mutated"  # type: ignore[misc]


@pytest.mark.unit
def test_registry_contains_three_initial_instructions() -> None:
    """AC1 : les 3 entrees initiales sont presentes avec applies_to exacts."""
    by_name = {e.name: e for e in INSTRUCTION_REGISTRY}
    assert set(by_name.keys()) == {"style", "widget", "guided_tour"}

    # style : tous les 7 modules
    assert set(by_name["style"].applies_to) == {
        "chat", "esg_scoring", "carbon", "financing",
        "application", "credit", "action_plan",
    }
    # widget : tous les 7 modules (idem style)
    assert set(by_name["widget"].applies_to) == {
        "chat", "esg_scoring", "carbon", "financing",
        "application", "credit", "action_plan",
    }
    # guided_tour : 6 modules (exclut application — parite historique)
    assert set(by_name["guided_tour"].applies_to) == {
        "chat", "esg_scoring", "carbon", "financing",
        "credit", "action_plan",
    }
    assert "application" not in by_name["guided_tour"].applies_to

    # Assertions priorites (ordre semantique verrouille)
    assert by_name["style"].priority == 10
    assert by_name["widget"].priority == 50
    assert by_name["guided_tour"].priority == 90

    # Chaque entree est bien du bon type
    for entry in INSTRUCTION_REGISTRY:
        assert isinstance(entry, InstructionEntry)
