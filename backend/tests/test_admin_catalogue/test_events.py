"""Test events.py — 5 constantes domain events declarees (Story 10.4 AC1)."""

from __future__ import annotations

from app.modules.admin_catalogue import events


def test_five_event_type_constants_declared():
    """Chaque constante event_type existe + prefixe `catalogue.` + valeur explicite."""
    assert events.CATALOGUE_CRITERION_PUBLISHED_EVENT_TYPE == (
        "catalogue.criterion_published"
    )
    assert events.CATALOGUE_REFERENTIAL_PUBLISHED_EVENT_TYPE == (
        "catalogue.referential_published"
    )
    assert events.CATALOGUE_PACK_PUBLISHED_EVENT_TYPE == (
        "catalogue.pack_published"
    )
    assert events.CATALOGUE_RULE_PUBLISHED_EVENT_TYPE == (
        "catalogue.rule_published"
    )
    assert events.CATALOGUE_ENTITY_RETIRED_EVENT_TYPE == (
        "catalogue.entity_retired"
    )
