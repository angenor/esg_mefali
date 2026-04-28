"""Fixtures de test pour les tools LangChain."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.runnables import RunnableConfig


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """UUID fixe pour les tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_conversation_id() -> uuid.UUID:
    """UUID conversation fixe pour les tests."""
    return uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def mock_db() -> AsyncMock:
    """Session DB mockée avec les méthodes async courantes."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    # Par défaut, db.execute(...) retourne un Result vide (None partout) afin
    # que les nouvelles gardes runtime (BUG-V6) prennent le chemin "pas de
    # ligne existante" sans casser les tests qui ne se soucient pas de execute.
    _empty_result = MagicMock()
    _empty_result.scalar_one_or_none = MagicMock(return_value=None)
    _empty_result.scalar = MagicMock(return_value=None)
    _empty_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=_empty_result)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_config(mock_db: AsyncMock, mock_user_id: uuid.UUID, mock_conversation_id: uuid.UUID) -> RunnableConfig:
    """RunnableConfig avec db et user_id injectés."""
    return {
        "configurable": {
            "db": mock_db,
            "user_id": mock_user_id,
            "conversation_id": mock_conversation_id,
            "thread_id": str(mock_conversation_id),
        },
    }


@pytest.fixture
def mock_config_no_db(mock_user_id: uuid.UUID) -> RunnableConfig:
    """RunnableConfig sans session DB (pour tester les erreurs)."""
    return {
        "configurable": {
            "user_id": mock_user_id,
        },
    }


@pytest.fixture
def mock_config_no_user(mock_db: AsyncMock) -> RunnableConfig:
    """RunnableConfig sans user_id (pour tester les erreurs)."""
    return {
        "configurable": {
            "db": mock_db,
        },
    }
