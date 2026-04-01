"""Tests des endpoints du router dashboard."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# --- Helpers ---


async def _register_and_login(client: AsyncClient) -> dict[str, str]:
    """Créer un compte et retourner les headers d'authentification."""
    email = f"dash-{uuid.uuid4().hex[:8]}@example.com"
    password = "DashTest1234!"

    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Dashboard User",
            "company_name": "Test Corp",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests GET /api/dashboard/summary ---


class TestDashboardSummaryEndpoint:
    """Tests de l'endpoint GET /api/dashboard/summary."""

    @pytest.mark.asyncio
    async def test_returns_200_with_data(self, client: AsyncClient):
        """T015-01 : Utilisateur authentifié → 200 avec structure DashboardSummary."""
        headers = await _register_and_login(client)

        resp = await client.get("/api/dashboard/summary", headers=headers)

        assert resp.status_code == 200
        data = resp.json()

        # Structure de base présente
        assert "esg" in data
        assert "carbon" in data
        assert "credit" in data
        assert "financing" in data
        assert "next_actions" in data
        assert "recent_activity" in data
        assert "badges" in data

    @pytest.mark.asyncio
    async def test_returns_200_nulls_for_new_user(self, client: AsyncClient):
        """T015-02 : Nouvel utilisateur → sections nullable nulles."""
        headers = await _register_and_login(client)

        resp = await client.get("/api/dashboard/summary", headers=headers)

        assert resp.status_code == 200
        data = resp.json()

        # Sections nullables vides pour un nouvel utilisateur
        assert data["esg"] is None
        assert data["carbon"] is None
        assert data["credit"] is None

        # Sections toujours présentes avec valeurs par défaut
        financing = data["financing"]
        assert financing["recommended_funds_count"] == 0
        assert financing["active_applications_count"] == 0
        assert financing["has_intermediary_paths"] is False

        assert data["next_actions"] == []
        assert data["recent_activity"] == []
        assert data["badges"] == []

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self, client: AsyncClient):
        """T015-03 : Sans authentification → 401."""
        resp = await client.get("/api/dashboard/summary")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_token(self, client: AsyncClient):
        """T015-04 : Token invalide → 401."""
        resp = await client.get(
            "/api/dashboard/summary",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_financing_defaults(self, client: AsyncClient):
        """T015-05 : Section financing avec valeurs par défaut correctes."""
        headers = await _register_and_login(client)

        resp = await client.get("/api/dashboard/summary", headers=headers)

        assert resp.status_code == 200
        financing = resp.json()["financing"]

        assert isinstance(financing["recommended_funds_count"], int)
        assert isinstance(financing["active_applications_count"], int)
        assert isinstance(financing["application_statuses"], dict)
        assert isinstance(financing["has_intermediary_paths"], bool)

    @pytest.mark.asyncio
    async def test_summary_response_is_isolated_per_user(self, client: AsyncClient):
        """T015-06 : Chaque utilisateur voit uniquement ses données."""
        headers_a = await _register_and_login(client)
        headers_b = await _register_and_login(client)

        resp_a = await client.get("/api/dashboard/summary", headers=headers_a)
        resp_b = await client.get("/api/dashboard/summary", headers=headers_b)

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        # Les deux sont des nouveaux utilisateurs sans données
        assert resp_a.json()["esg"] is None
        assert resp_b.json()["esg"] is None
