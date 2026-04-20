"""Tests de la validation `aws_region` NFR24 data residency.

Story 10.6 post-review MEDIUM-10.6-2 — fail-fast boot si région hors UE.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import ALLOWED_EU_REGIONS, Settings


def test_settings_accepts_eu_west_3_default():
    """Default eu-west-3 (Paris) doit être accepté — NFR24 tranché."""
    settings = Settings()
    assert settings.aws_region == "eu-west-3"


@pytest.mark.parametrize("region", sorted(ALLOWED_EU_REGIONS))
def test_settings_accepts_all_eu_regions(monkeypatch, region: str):
    """Toutes les régions UE whitelistées (plans de contingence §D8) acceptées."""
    monkeypatch.setenv("AWS_REGION", region)
    settings = Settings()
    assert settings.aws_region == region


@pytest.mark.parametrize(
    "non_eu_region",
    ["us-east-1", "us-west-2", "ap-south-1", "ap-northeast-1", "sa-east-1"],
)
def test_settings_rejects_non_eu_regions(monkeypatch, non_eu_region: str):
    """Fail-fast : toute région hors UE est refusée au boot (NFR24)."""
    monkeypatch.setenv("AWS_REGION", non_eu_region)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    err_text = str(exc_info.value)
    assert "NFR24" in err_text or "UE region" in err_text
    assert non_eu_region in err_text


def test_settings_rejects_empty_region(monkeypatch):
    """Région vide refusée (fail-closed, pas de fallback silencieux)."""
    monkeypatch.setenv("AWS_REGION", "")
    with pytest.raises(ValidationError):
        Settings()
