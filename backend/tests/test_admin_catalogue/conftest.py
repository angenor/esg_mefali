"""Fixtures locales pour les tests du module admin_catalogue (Story 10.4 AC8)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


ADMIN_EMAIL = "admin@mefali.test"
NON_ADMIN_EMAIL = "pme-user@example.com"


@pytest.fixture
async def authenticated_client(override_auth) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP authentifie avec user PME standard (email non-whiteliste).

    `override_auth` (conftest global) pose un MagicMock avec email
    `test-override@example.com` qui n'est jamais dans `ADMIN_MEFALI_EMAILS`
    -> toutes les routes admin_catalogue renvoient 403.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_authenticated_client(
    monkeypatch,
) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP authentifie avec email whiteliste admin (AC4 §3).

    Pose `ADMIN_MEFALI_EMAILS=admin@mefali.test` via monkeypatch et override
    `get_current_user` avec un user dont l'email matche. Les endpoints
    admin_catalogue renvoient donc 501 (POST stubs) ou 200 (GET fact-types).
    """
    from app.api.deps import get_current_user
    from app.main import app

    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", ADMIN_EMAIL)

    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = ADMIN_EMAIL
    mock_user.is_active = True

    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    del app.dependency_overrides[get_current_user]


@pytest.fixture
async def seed_admin_user(db_session):
    """Insere un `users` row (FK `actor_user_id` d'`admin_catalogue_audit_trail`).

    Utilise par les tests `test_audit_trail_service.py` et
    `test_audit_trail_atomicity.py` qui appellent `record_audit_event`
    directement — la FK `users.id` doit etre satisfaite (ON DELETE RESTRICT
    cote migration 026).
    """
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"audit-actor-{uuid.uuid4().hex[:8]}@mefali.test",
        hashed_password="hash",
        full_name="Audit Actor",
        company_name="Mefali",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user
