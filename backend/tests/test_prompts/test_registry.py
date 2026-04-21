"""Tests unit exhaustifs du registre (AC8 Story 10.8).

10 tests verrouillent les invariants du registre et du builder :
filtre, ordre, substitution, erreurs explicites, determinisme.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.prompts.registry import (
    INSTRUCTION_REGISTRY,
    InstructionEntry,
    SUPPORTED_MODULES,
    UnboundPromptVariableError,
    UnknownPromptModuleError,
    build_prompt,
)


@pytest.mark.unit
def test_registry_is_frozen_tuple() -> None:
    """INSTRUCTION_REGISTRY est un tuple (pas list ni dict)."""
    assert type(INSTRUCTION_REGISTRY) is tuple


@pytest.mark.unit
def test_instruction_entry_is_frozen_dataclass() -> None:
    """InstructionEntry frozen — assignation lève FrozenInstanceError."""
    entry = InstructionEntry(
        name="x", applies_to=("chat",), priority=1, template="X"
    )
    with pytest.raises(FrozenInstanceError):
        entry.priority = 999  # type: ignore[misc]


@pytest.mark.unit
def test_build_prompt_filters_by_applies_to(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une entree non-applicable au module courant est filtree."""
    fake_registry = (
        InstructionEntry(
            name="only_chat", applies_to=("chat",), priority=10, template="CHAT-ONLY"
        ),
        InstructionEntry(
            name="only_esg", applies_to=("esg_scoring",), priority=10, template="ESG-ONLY"
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    assert "CHAT-ONLY" in build_prompt(module="chat")
    assert "ESG-ONLY" not in build_prompt(module="chat")
    assert "ESG-ONLY" in build_prompt(module="esg_scoring")
    assert "CHAT-ONLY" not in build_prompt(module="esg_scoring")


@pytest.mark.unit
def test_build_prompt_orders_by_priority_then_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tie-break par name alphabetique quand priorities egales."""
    fake_registry = (
        InstructionEntry(
            name="zebra", applies_to=("chat",), priority=10, template="Z"
        ),
        InstructionEntry(
            name="alpha", applies_to=("chat",), priority=10, template="A"
        ),
        InstructionEntry(
            name="middle", applies_to=("chat",), priority=5, template="M"
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    prompt = build_prompt(module="chat")
    # Ordre attendu : priority 5 (middle), puis priority 10 triee par name (alpha, zebra)
    assert prompt == "M\n\nA\n\nZ"


@pytest.mark.unit
def test_build_prompt_substitutes_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Template.substitute applique ${var} → valeur."""
    fake_registry = (
        InstructionEntry(
            name="greet",
            applies_to=("chat",),
            priority=10,
            template="Hello ${name}",
            required_vars=("name",),
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    prompt = build_prompt(module="chat", variables={"name": "Mefali"})
    assert prompt == "Hello Mefali"


@pytest.mark.unit
def test_build_prompt_raises_on_missing_required_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """required_vars present mais absent de variables → UnboundPromptVariableError."""
    fake_registry = (
        InstructionEntry(
            name="needs_foo",
            applies_to=("chat",),
            priority=10,
            template="X",
            required_vars=("foo",),
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    with pytest.raises(UnboundPromptVariableError) as exc_info:
        build_prompt(module="chat", variables={"bar": "value"})

    msg = str(exc_info.value)
    assert "'foo'" in msg or "foo" in msg
    assert "needs_foo" in msg


@pytest.mark.unit
def test_build_prompt_raises_on_unknown_module() -> None:
    """Module hors SUPPORTED_MODULES → UnknownPromptModuleError listant les supportes."""
    with pytest.raises(UnknownPromptModuleError) as exc_info:
        build_prompt(module="nonexistent_module")

    msg = str(exc_info.value)
    assert "nonexistent_module" in msg
    # Verifie que la liste des supportes est citee (aide au diagnostic)
    for supported in SUPPORTED_MODULES:
        assert supported in msg


@pytest.mark.unit
def test_build_prompt_accepts_empty_variables_when_no_required_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instruction sans required_vars + variables=None → OK."""
    fake_registry = (
        InstructionEntry(
            name="static", applies_to=("chat",), priority=10, template="STATIC CONTENT"
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    assert build_prompt(module="chat", variables=None) == "STATIC CONTENT"
    assert build_prompt(module="chat", variables={}) == "STATIC CONTENT"


@pytest.mark.unit
def test_build_prompt_prepends_base(monkeypatch: pytest.MonkeyPatch) -> None:
    """base='INTRO' → 'INTRO\\n\\n<instructions>'."""
    fake_registry = (
        InstructionEntry(
            name="inst", applies_to=("chat",), priority=10, template="INSTRUCTION"
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    prompt = build_prompt(module="chat", base="INTRO")
    assert prompt == "INTRO\n\nINSTRUCTION"


@pytest.mark.unit
def test_build_prompt_is_deterministic_across_calls() -> None:
    """10 appels successifs produisent des strings byte-identiques."""
    prompts = [build_prompt(module="chat") for _ in range(10)]
    for p in prompts[1:]:
        assert p == prompts[0]


@pytest.mark.unit
def test_build_prompt_raises_when_template_references_unprovided_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Template reference ${var} non declaree dans required_vars et absente de variables
    → UnboundPromptVariableError (defense en profondeur)."""
    fake_registry = (
        InstructionEntry(
            name="leaky",
            applies_to=("chat",),
            priority=10,
            template="Hello ${missing_var}",
            # required_vars volontairement vide → le template a un var non declaree
        ),
    )
    monkeypatch.setattr("app.prompts.registry.INSTRUCTION_REGISTRY", fake_registry)

    with pytest.raises(UnboundPromptVariableError) as exc_info:
        build_prompt(module="chat", variables={})

    assert "missing_var" in str(exc_info.value)
    assert "leaky" in str(exc_info.value)
