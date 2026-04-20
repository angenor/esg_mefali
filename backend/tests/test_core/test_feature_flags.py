"""Tests pour les feature flags (Story 10.2 AC4, AC8)."""

from __future__ import annotations

import pytest

from app.core.feature_flags import is_project_model_enabled


def test_is_project_model_enabled_defaults_false(monkeypatch):
    """Test 10 — sans env var -> False (défaut MVP sûr)."""
    monkeypatch.delenv("ENABLE_PROJECT_MODEL", raising=False)
    assert is_project_model_enabled() is False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("YES", True),
        ("Yes", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("", False),
        ("no", False),
        ("disabled", False),
        ("2", False),
        ("random", False),
    ],
)
def test_is_project_model_enabled_truthy_values(monkeypatch, value, expected):
    """Test 11 — valeurs truthy/falsy case-insensitive (table-driven)."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", value)
    assert is_project_model_enabled() is expected
