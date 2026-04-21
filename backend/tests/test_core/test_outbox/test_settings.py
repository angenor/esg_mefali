"""Tests unit — Settings Pydantic worker Outbox (Story 10.10 AC6)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

pytestmark = pytest.mark.unit


def test_settings_domain_events_worker_fields_defaults(monkeypatch):
    """Les deux champs worker Outbox existent avec leurs défauts attendus."""
    monkeypatch.delenv("DOMAIN_EVENTS_WORKER_ENABLED", raising=False)
    monkeypatch.delenv("DOMAIN_EVENTS_WORKER_INTERVAL_S", raising=False)

    s = Settings()
    assert s.domain_events_worker_enabled is True
    assert s.domain_events_worker_interval_s == 30


def test_settings_domain_events_worker_enabled_env_coercion(monkeypatch):
    """DOMAIN_EVENTS_WORKER_ENABLED=false → False (coercion Pydantic)."""
    monkeypatch.setenv("DOMAIN_EVENTS_WORKER_ENABLED", "false")
    s = Settings()
    assert s.domain_events_worker_enabled is False


def test_settings_interval_below_5_raises_validation_error(monkeypatch):
    """Borne ge=5 — hot-loop par configuration accidentelle refusé."""
    monkeypatch.setenv("DOMAIN_EVENTS_WORKER_INTERVAL_S", "2")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_interval_above_3600_raises_validation_error(monkeypatch):
    """Borne le=3600 — worker dormant 1 jour refusé."""
    monkeypatch.setenv("DOMAIN_EVENTS_WORKER_INTERVAL_S", "7200")
    with pytest.raises(ValidationError):
        Settings()
