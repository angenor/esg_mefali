"""Tests de la validation `env_name` NFR73 — ségrégation environnements.

Story 10.7 AC1 — fail-fast boot si ENV_NAME non reconnu.
Pattern miroir Story 10.6 `test_config_aws_region.py` (ALLOWED_EU_REGIONS).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import ALLOWED_ENV_NAMES, Settings


def test_settings_accepts_default_env_name_dev(monkeypatch):
    """Default `dev` accepté — DEV local docker-compose (NFR73)."""
    monkeypatch.delenv("ENV_NAME", raising=False)
    settings = Settings()
    assert settings.env_name == "dev"
    assert settings.is_production() is False


@pytest.mark.parametrize("env", sorted(ALLOWED_ENV_NAMES))
def test_settings_accepts_all_allowed_env_names(monkeypatch, env: str):
    """Tous les env whitelistés (dev/staging/prod) acceptés."""
    monkeypatch.setenv("ENV_NAME", env)
    # PROD interdit debug=True — garde-fou indépendant
    monkeypatch.setenv("DEBUG", "false")
    settings = Settings()
    assert settings.env_name == env
    assert settings.is_production() == (env == "prod")


@pytest.mark.parametrize(
    "invalid_env",
    ["test", "preprod", "production", "", "DEV", "qa"],
)
def test_settings_rejects_invalid_env_names(monkeypatch, invalid_env: str):
    """Fail-fast : toute valeur hors whitelist refusée (NFR73 isolation)."""
    monkeypatch.setenv("ENV_NAME", invalid_env)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    err_text = str(exc_info.value)
    assert "NFR73" in err_text or "env_name" in err_text


def test_settings_rejects_prod_with_debug_true(monkeypatch):
    """Garde-fou PROD — debug=True interdit (NFR73 anti-leak traces stack)."""
    monkeypatch.setenv("ENV_NAME", "prod")
    monkeypatch.setenv("DEBUG", "true")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    err_text = str(exc_info.value)
    assert "debug" in err_text.lower() or "NFR73" in err_text
