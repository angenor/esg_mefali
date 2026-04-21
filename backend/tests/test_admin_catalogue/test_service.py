"""Tests du service du module admin_catalogue (Story 10.4 AC5, AC8)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from app.modules.admin_catalogue.enums import (
    NodeStateEnum,
)
from app.modules.admin_catalogue.service import (
    create_criterion,
    create_derivation_rule,
    create_pack,
    create_referential,
    list_fact_types,
    transition_workflow_state,
)


_STUB_CALLS = [
    pytest.param(
        lambda db: create_criterion(
            db,
            code="c1",
            label_fr="C1",
            dimension="E",
            description=None,
            actor_user_id=uuid.uuid4(),
        ),
        id="create_criterion",
    ),
    pytest.param(
        lambda db: create_referential(
            db,
            code="r1",
            label_fr="R1",
            description=None,
            actor_user_id=uuid.uuid4(),
        ),
        id="create_referential",
    ),
    pytest.param(
        lambda db: create_pack(
            db,
            code="p1",
            label_fr="P1",
            actor_user_id=uuid.uuid4(),
        ),
        id="create_pack",
    ),
    pytest.param(
        lambda db: create_derivation_rule(
            db,
            criterion_id=uuid.uuid4(),
            rule_type="threshold",
            rule_json={},
            actor_user_id=uuid.uuid4(),
        ),
        id="create_derivation_rule",
    ),
    pytest.param(
        lambda db: transition_workflow_state(
            db,
            entity_type="Criterion",
            entity_id=uuid.uuid4(),
            from_state=NodeStateEnum.draft,
            to_state=NodeStateEnum.review_requested,
            actor_user_id=uuid.uuid4(),
        ),
        id="transition_workflow_state",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("invoke", _STUB_CALLS)
async def test_5_remaining_stub_service_functions_raise_not_implemented(invoke):
    """Test 12 — 5 stubs service -> NotImplementedError (record_audit_event
    implementee Story 10.12, pattern shims legacy signature byte-identique)."""
    db_mock = AsyncMock()
    with pytest.raises(NotImplementedError) as exc_info:
        await invoke(db_mock)
    msg = str(exc_info.value)
    assert "Story 10.4 skeleton" in msg, (
        f"message stub attendu 'Story 10.4 skeleton', obtenu : {msg}"
    )
    assert ("Epic 13" in msg) or ("Story 10.12" in msg), (
        f"message stub doit referencer Epic 13 ou Story 10.12, obtenu : {msg}"
    )


@pytest.mark.asyncio
async def test_list_fact_types_returns_registry_tuple_as_list():
    """Test 13 — list_fact_types retourne une list[str] effective >= 12 entrees."""
    result = await list_fact_types()
    assert isinstance(result, list)
    assert len(result) >= 12
    assert "energy_consumption_kwh" in result
    assert all(isinstance(x, str) for x in result)
