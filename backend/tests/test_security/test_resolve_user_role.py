"""Unit tests pour ``resolve_user_role`` + ``ADMIN_ROLES``.

Story 10.5 AC1 — fonction pure, pas de PostgreSQL requis (utilise
``monkeypatch.setenv`` pour simuler les whitelists).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.core.rls import ADMIN_ROLES, resolve_user_role


def _fake_user(email: str):
    """Mock utilisateur minimal (évite instancier le modèle ORM)."""
    return SimpleNamespace(id=uuid.uuid4(), email=email)


def test_admin_roles_contains_exactly_two_values():
    """``ADMIN_ROLES`` doit être un frozenset strict {admin_mefali, admin_super}."""
    assert ADMIN_ROLES == frozenset({"admin_mefali", "admin_super"})
    assert isinstance(ADMIN_ROLES, frozenset)


def test_resolve_user_role_returns_admin_super(monkeypatch: pytest.MonkeyPatch):
    """Email ∈ ADMIN_SUPER_EMAILS → ``admin_super``."""
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "boss@mefali.com")
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "")
    assert resolve_user_role(_fake_user("boss@mefali.com")) == "admin_super"


def test_resolve_user_role_returns_admin_mefali(monkeypatch: pytest.MonkeyPatch):
    """Email ∈ ADMIN_MEFALI_EMAILS mais pas SUPER → ``admin_mefali``."""
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "")
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "ops@mefali.com")
    assert resolve_user_role(_fake_user("ops@mefali.com")) == "admin_mefali"


def test_resolve_user_role_returns_user_for_unlisted_email(
    monkeypatch: pytest.MonkeyPatch,
):
    """Email non-listé → ``user`` (fail-safe)."""
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "boss@mefali.com")
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "ops@mefali.com")
    assert resolve_user_role(_fake_user("pme@example.com")) == "user"


def test_resolve_user_role_super_precedes_mefali(monkeypatch: pytest.MonkeyPatch):
    """Si email dans les 2 listes → admin_super l'emporte (précédence)."""
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "dual@mefali.com")
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "dual@mefali.com")
    assert resolve_user_role(_fake_user("dual@mefali.com")) == "admin_super"


def test_resolve_user_role_fail_closed_on_missing_env(monkeypatch: pytest.MonkeyPatch):
    """Variables d'env absentes → tout user devient ``user`` (fail-closed)."""
    monkeypatch.delenv("ADMIN_SUPER_EMAILS", raising=False)
    monkeypatch.delenv("ADMIN_MEFALI_EMAILS", raising=False)
    assert resolve_user_role(_fake_user("anyone@example.com")) == "user"


def test_resolve_user_role_case_insensitive(monkeypatch: pytest.MonkeyPatch):
    """Email matching case-insensitive + trim whitespace."""
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "  OPS@Mefali.com ")
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "")
    assert resolve_user_role(_fake_user("ops@mefali.COM")) == "admin_mefali"
