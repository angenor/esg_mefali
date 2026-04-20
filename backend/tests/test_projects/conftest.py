"""Fixtures locales pour les tests du module projects."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def authenticated_client(override_auth) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP authentifie (Depends(get_current_user) overriden)."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def company_factory(db_session):
    """Fabrique de companies de test (et de leur user proprietaire)."""
    from app.models.user import User
    from app.modules.projects.models import Company

    async def _make(name: str = "Test Co") -> Company:
        user = User(
            id=uuid.uuid4(),
            email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hash",
            full_name="Owner",
            company_name=name,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        company = Company(
            id=uuid.uuid4(),
            owner_user_id=user.id,
            name=name,
        )
        db_session.add(company)
        await db_session.flush()
        return company

    return _make
