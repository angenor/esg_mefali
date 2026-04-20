"""Test fact_type_registry immutable + country-agnostic (Story 10.4 AC7, AC8)."""

from __future__ import annotations

from app.modules.admin_catalogue.fact_type_registry import FACT_TYPE_CATALOGUE


_BANNED_COUNTRY_STRINGS = [
    "Sénégal", "Senegal",
    "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast",
    "Mali", "Burkina Faso", "Niger", "Togo", "Bénin", "Benin",
    "Guinée", "Guinee", "Guinea",
]


def test_fact_type_catalogue_is_immutable_tuple_and_country_agnostic():
    """Test 14 — FACT_TYPE_CATALOGUE est un tuple + aucune valeur pays."""
    assert isinstance(FACT_TYPE_CATALOGUE, tuple), (
        "FACT_TYPE_CATALOGUE doit etre un tuple immutable"
    )
    assert len(FACT_TYPE_CATALOGUE) >= 12

    for value in FACT_TYPE_CATALOGUE:
        for banned in _BANNED_COUNTRY_STRINGS:
            assert banned not in value, (
                f"FACT_TYPE_CATALOGUE contient le pays banni '{banned}' dans '{value}'"
            )
