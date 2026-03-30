"""Fixtures de test pytest pour le backend ESG Mefali.

Utilise SQLite async en mémoire pour les tests unitaires.
Les tests d'intégration avec PostgreSQL sont exécutés via Docker.
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.models.base import Base

# SQLite async en mémoire pour les tests rapides
# PostgreSQL via Docker pour les tests d'intégration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true",
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_db():
    """Créer et détruire les tables pour chaque test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dépendance de test pour remplacer la session de BDD."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Import app après configuration pour éviter les effets de bord
from app.main import app  # noqa: E402

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour tester les endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Session de base de données pour les tests directs."""
    async with test_session_factory() as session:
        yield session


def make_unique_email() -> str:
    """Générer un email unique pour les tests."""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"
