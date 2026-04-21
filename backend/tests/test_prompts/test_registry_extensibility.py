"""Test d'extensibilite du registre (AC7 Story 10.8).

Verifie qu'ajouter une 4e instruction transverse = 1 bloc InstructionEntry dans
INSTRUCTION_REGISTRY, sans modification des 7 modules metier. Simule l'ajout
via monkeypatch d'un registre etendu, puis asserte que les modules cibles
recoivent bien la nouvelle instruction tandis que les autres restent inchanges.
"""

from __future__ import annotations

import pytest

from app.prompts.registry import INSTRUCTION_REGISTRY, InstructionEntry, build_prompt


@pytest.mark.unit
def test_adding_new_instruction_propagates_to_targeted_modules_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC7 : ajouter une InstructionEntry → SEUL les modules listes dans
    applies_to la recoivent. Aucun autre fichier a modifier.

    Scenario : on imagine une future `RATE_LIMIT_INSTRUCTION` destinee uniquement
    aux modules `chat` et `esg_scoring` (priority 30, entre style et widget).
    """
    fake_marker = "## RATE LIMIT HINT — test ext"
    extended_registry = INSTRUCTION_REGISTRY + (
        InstructionEntry(
            name="rate_limit_hint",
            applies_to=("chat", "esg_scoring"),
            priority=30,
            template=fake_marker,
        ),
    )
    monkeypatch.setattr(
        "app.prompts.registry.INSTRUCTION_REGISTRY", extended_registry
    )

    # Les 2 modules cibles recoivent la nouvelle instruction
    chat_prompt = build_prompt(module="chat")
    esg_prompt = build_prompt(module="esg_scoring")
    assert fake_marker in chat_prompt
    assert fake_marker in esg_prompt

    # Les 5 autres modules ne la recoivent PAS
    for other_module in ("carbon", "financing", "application", "credit", "action_plan"):
        other_prompt = build_prompt(module=other_module)
        assert fake_marker not in other_prompt, (
            f"Module '{other_module}' a recu rate_limit_hint alors qu'il n'est "
            f"pas dans applies_to — le filtre du registre est casse."
        )

    # Ordre deterministe verifie : priority=30 entre style(10) et widget(50)
    idx_style = chat_prompt.find("## STYLE DE COMMUNICATION")
    idx_rate = chat_prompt.find(fake_marker)
    idx_widget = chat_prompt.find("## OUTIL INTERACTIF")
    assert idx_style < idx_rate < idx_widget, (
        f"Ordre injection incorrect : style={idx_style}, rate={idx_rate}, widget={idx_widget}"
    )
