"""Tests de la dependance require_admin_mefali (Story 10.4 AC4, AC8)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.modules.admin_catalogue.dependencies import require_admin_mefali


def _make_user(email: str) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.is_active = True
    return user


@pytest.mark.asyncio
async def test_require_admin_mefali_whitelists_email_from_env(monkeypatch):
    """Test 18 (bonus) — emails whitelistes via ADMIN_MEFALI_EMAILS passent ; autres -> 403."""
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "a@x.com,admin@mefali.test")

    whitelisted = _make_user("admin@mefali.test")
    result = await require_admin_mefali(current_user=whitelisted)
    assert result is whitelisted

    also_whitelisted = _make_user("a@x.com")
    result2 = await require_admin_mefali(current_user=also_whitelisted)
    assert result2 is also_whitelisted

    non_whitelisted = _make_user("b@x.com")
    with pytest.raises(HTTPException) as exc_info:
        await require_admin_mefali(current_user=non_whitelisted)
    assert exc_info.value.status_code == 403
    assert "admin_mefali" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_admin_mefali_returns_403_if_env_var_empty(monkeypatch):
    """Test 19 (bonus) — env absente ou vide -> 403 (fail-closed par defaut)."""
    monkeypatch.delenv("ADMIN_MEFALI_EMAILS", raising=False)

    user = _make_user("any@user.com")
    with pytest.raises(HTTPException) as exc_info:
        await require_admin_mefali(current_user=user)
    assert exc_info.value.status_code == 403

    # Meme resultat avec env vide explicit
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "")
    with pytest.raises(HTTPException) as exc_info2:
        await require_admin_mefali(current_user=user)
    assert exc_info2.value.status_code == 403
