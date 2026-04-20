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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reinitialiser l'etat du limiter SlowAPI entre chaque test (FR-013).

    Evite que les compteurs de rate limit persistent d'un test a l'autre et
    declenchent des faux 429 sur des tests qui envoient plus de 30 messages.
    """
    from app.core.rate_limit import limiter

    limiter.reset()
    yield


@pytest.fixture(autouse=True)
def isolate_storage_provider(tmp_path_factory, monkeypatch):
    """Story 10.6 — isole chaque test dans un storage local tmpdir dédié.

    Évite que les tests qui déclenchent `get_storage_provider().put()` (via
    `upload_document` ou `generate_esg_report_pdf`) n'écrivent dans
    `backend/uploads/` réel. Sans cette fixture, les tests legacy qui
    mockaient `_save_file_to_disk` persisteraient dans le filesystem du repo.
    """
    from app.core import storage as storage_module
    from app.core.config import settings

    tmp_dir = tmp_path_factory.mktemp("storage_test")
    monkeypatch.setattr(settings, "storage_local_path", str(tmp_dir))
    monkeypatch.setattr(settings, "storage_provider", "local")
    storage_module._reset_storage_provider_cache()
    yield
    storage_module._reset_storage_provider_cache()


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


# --- Fixture auth partagé (T001) ---

@pytest.fixture
async def override_auth():
    """Override get_current_user avec un mock user pour les tests d'endpoints protégés."""
    from unittest.mock import MagicMock

    from app.api.deps import get_current_user

    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test-override@example.com"
    mock_user.is_active = True

    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    del app.dependency_overrides[get_current_user]


# --- Helper make_conversation_state (T002) ---

def make_conversation_state(**overrides) -> dict:
    """Retourne un dict complet avec les 27 clés de ConversationState.

    Toutes les valeurs par défaut sont les 'zéro values'.
    Accepte des overrides via kwargs.
    """
    defaults = {
        "messages": [],
        "user_id": "test-user-id",
        "user_profile": None,
        "context_memory": [],
        "profile_updates": None,
        "profiling_instructions": None,
        "document_upload": None,
        "document_analysis_summary": None,
        "has_document": False,
        "esg_assessment": None,
        "_route_esg": False,
        "carbon_data": None,
        "_route_carbon": False,
        "financing_data": None,
        "_route_financing": False,
        "application_data": None,
        "_route_application": False,
        "credit_data": None,
        "_route_credit": False,
        "action_plan_data": None,
        "_route_action_plan": False,
        "tool_call_count": 0,
        "active_module": None,
        "active_module_data": None,
        "current_page": None,
    }
    return {**defaults, **overrides}
