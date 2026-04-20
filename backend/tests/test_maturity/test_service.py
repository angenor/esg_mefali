"""Tests de la surface d'API du service maturity (Story 10.3 AC6, AC8)."""

from __future__ import annotations

import uuid

import pytest

from app.modules.maturity import service as maturity_service

_SKELETON_MARKER = "Story 10.3 skeleton"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fn_name,kwargs",
    [
        (
            "declare_maturity_level",
            lambda: {
                "company_id": uuid.uuid4(),
                "level_code": "informel",
                "actor_user_id": uuid.uuid4(),
            },
        ),
        (
            "get_formalization_plan",
            lambda: {"company_id": uuid.uuid4()},
        ),
        (
            "list_published_levels",
            lambda: {},
        ),
        (
            "get_requirements_for_country_level",
            lambda: {"country": "country-var", "level_id": uuid.uuid4()},
        ),
        (
            "create_formalization_plan",
            lambda: {
                "company_id": uuid.uuid4(),
                "current_level_id": uuid.uuid4(),
                "target_level_id": uuid.uuid4(),
                "actions": [],
            },
        ),
    ],
    ids=[
        "declare_maturity_level",
        "get_formalization_plan",
        "list_published_levels",
        "get_requirements_for_country_level",
        "create_formalization_plan",
    ],
)
async def test_all_5_service_functions_raise_not_implemented(
    db_session, fn_name, kwargs
):
    """Test 11 — parametrize : 5 fonctions service -> NotImplementedError avec marker."""
    fn = getattr(maturity_service, fn_name)
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await fn(db_session, **kwargs())


def test_events_module_exposes_event_types():
    """Bonus — events.py expose les 3 constantes (preparation CCC-14)."""
    from app.modules.maturity import events

    assert events.MATURITY_LEVEL_UPGRADED_EVENT_TYPE == "maturity.level_upgraded"
    assert (
        events.MATURITY_LEVEL_DOWNGRADED_EVENT_TYPE
        == "maturity.level_downgraded"
    )
    assert (
        events.FORMALIZATION_PLAN_GENERATED_EVENT_TYPE
        == "maturity.formalization_plan_generated"
    )
