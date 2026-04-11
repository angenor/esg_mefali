"""Tests unitaires des schemas Pydantic InteractiveQuestion (feature 018)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.interactive_question import (
    InteractiveOption,
    InteractiveQuestionAnswerInput,
    InteractiveQuestionCreate,
)


# ─── InteractiveOption ───────────────────────────────────────────────


def test_option_valid():
    opt = InteractiveOption(id="agri", label="Agriculture", emoji="🌾")
    assert opt.id == "agri"
    assert opt.label == "Agriculture"


def test_option_id_pattern_rejected():
    with pytest.raises(ValidationError):
        InteractiveOption(id="Agri", label="Bad")  # majuscule interdite


def test_option_id_too_long():
    with pytest.raises(ValidationError):
        InteractiveOption(id="a" * 33, label="Bad")


def test_option_label_too_long():
    with pytest.raises(ValidationError):
        InteractiveOption(id="a", label="x" * 121)


# ─── InteractiveQuestionCreate ───────────────────────────────────────


def _opts(n: int = 3) -> list[dict]:
    return [{"id": f"opt{i}", "label": f"Label {i}"} for i in range(n)]


def test_create_qcu_valid():
    q = InteractiveQuestionCreate(
        question_type="qcu",
        prompt="Quel est ton secteur ?",
        options=_opts(3),
        module="profiling",
    )
    assert q.min_selections == 1
    assert q.max_selections == 1
    assert q.module == "profiling"


def test_create_qcu_rejects_min_max_not_one():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcu",
            prompt="Test",
            options=_opts(3),
            min_selections=2,
            max_selections=2,
            module="chat",
        )


def test_create_qcm_valid():
    q = InteractiveQuestionCreate(
        question_type="qcm",
        prompt="Quelles sources d'energie ?",
        options=_opts(5),
        min_selections=1,
        max_selections=3,
        module="carbon",
    )
    assert q.max_selections == 3


def test_create_qcm_rejects_min_gt_max():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcm",
            prompt="Test",
            options=_opts(3),
            min_selections=3,
            max_selections=2,
            module="chat",
        )


def test_create_qcm_rejects_max_gt_options():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcm",
            prompt="Test",
            options=_opts(3),
            min_selections=1,
            max_selections=5,
            module="chat",
        )


def test_create_rejects_too_few_options():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcu",
            prompt="Test",
            options=_opts(1),
            module="chat",
        )


def test_create_rejects_too_many_options():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcu",
            prompt="Test",
            options=_opts(9),
            module="chat",
        )


def test_create_rejects_duplicate_ids():
    with pytest.raises(ValidationError) as exc_info:
        InteractiveQuestionCreate(
            question_type="qcm",
            prompt="Test",
            options=[{"id": "a", "label": "A"}, {"id": "a", "label": "B"}],
            max_selections=2,
            module="chat",
        )
    assert "DUPLICATE_OPTION_ID" in str(exc_info.value)


def test_create_rejects_inconsistent_justification_qcu_with_flag():
    with pytest.raises(ValidationError) as exc_info:
        InteractiveQuestionCreate(
            question_type="qcu",
            prompt="Test",
            options=_opts(3),
            requires_justification=True,
            module="chat",
        )
    assert "INCONSISTENT_JUSTIFICATION" in str(exc_info.value)


def test_create_rejects_inconsistent_justification_type_without_flag():
    with pytest.raises(ValidationError) as exc_info:
        InteractiveQuestionCreate(
            question_type="qcu_justification",
            prompt="Test",
            options=_opts(3),
            requires_justification=False,
            justification_prompt="Pourquoi ?",
            module="chat",
        )
    assert "INCONSISTENT_JUSTIFICATION" in str(exc_info.value)


def test_create_qcu_justification_valid():
    q = InteractiveQuestionCreate(
        question_type="qcu_justification",
        prompt="Test",
        options=_opts(3),
        requires_justification=True,
        justification_prompt="Raconte-nous !",
        module="esg_scoring",
    )
    assert q.requires_justification is True
    assert q.justification_prompt == "Raconte-nous !"


def test_create_rejects_prompt_too_long():
    with pytest.raises(ValidationError):
        InteractiveQuestionCreate(
            question_type="qcu",
            prompt="x" * 501,
            options=_opts(3),
            module="chat",
        )


# ─── InteractiveQuestionAnswerInput ──────────────────────────────────


def test_answer_input_valid():
    import uuid
    a = InteractiveQuestionAnswerInput(
        question_id=uuid.uuid4(),
        values=["partial"],
        justification="Quelques mots",
    )
    assert a.values == ["partial"]


def test_answer_input_justification_too_long():
    import uuid
    with pytest.raises(ValidationError):
        InteractiveQuestionAnswerInput(
            question_id=uuid.uuid4(),
            values=["a"],
            justification="x" * 401,
        )


def test_answer_input_values_required():
    import uuid
    with pytest.raises(ValidationError):
        InteractiveQuestionAnswerInput(
            question_id=uuid.uuid4(),
            values=[],
        )
