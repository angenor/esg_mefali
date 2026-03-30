"""Tests du endpoint health check : état sain et dégradé."""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient) -> None:
    """GET /api/health retourne 200 quand la DB est connectée."""
    response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_degraded(client: AsyncClient) -> None:
    """GET /api/health retourne 503 quand la DB est déconnectée."""
    from app.core.database import get_db

    async def broken_get_db():
        """Simule une session DB qui échoue sur toute requête."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = ConnectionError("DB down")
        yield mock_session

    from app.main import app

    app.dependency_overrides[get_db] = broken_get_db
    try:
        response = await client.get("/api/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"
        assert "version" in data
    finally:
        # Restaurer la dépendance de test normale
        from tests.conftest import override_get_db

        app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_health_check_returns_version(client: AsyncClient) -> None:
    """GET /api/health inclut la version de l'application."""
    response = await client.get("/api/health")

    data = response.json()
    assert data["version"] == "0.1.0"
