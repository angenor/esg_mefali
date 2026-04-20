"""Fixtures locales pour les tests du module maturity (Story 10.3 AC8)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def authenticated_client(override_auth) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP authentifie (Depends(get_current_user) override)."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def company_factory(db_session):
    """Fabrique de companies pour satisfaire la FK `formalization_plans.company_id`."""
    from app.models.user import User
    from app.modules.projects.models import Company

    async def _make(name: str = "Test Co Maturity") -> Company:
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


@pytest.fixture
async def level_factory(db_session):
    """Fabrique de AdminMaturityLevel (unique level + unique code)."""
    from app.modules.maturity.models import AdminMaturityLevel

    counter = {"n": 0}

    async def _make(level: int | None = None, code: str | None = None) -> AdminMaturityLevel:
        counter["n"] += 1
        resolved_level = level if level is not None else counter["n"]
        resolved_code = code if code is not None else f"level-{counter['n']}"
        obj = AdminMaturityLevel(
            id=uuid.uuid4(),
            level=resolved_level,
            code=resolved_code,
            label_fr=f"Niveau {resolved_level}",
            workflow_state="draft",
            is_published=False,
        )
        db_session.add(obj)
        await db_session.flush()
        return obj

    return _make
