"""Tests du router REST ESG (T020).

Verifie les endpoints CRUD ESG : creation, liste, detail, score, benchmark.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import make_unique_email


async def create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Creer un utilisateur et retourner ses donnees + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Aminata Toure",
        "company_name": "GreenTech SARL",
    }
    await client.post("/api/auth/register", json=data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login_response.json()["access_token"]
    return data, token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def set_user_sector(client: AsyncClient, token: str, sector: str = "agriculture") -> None:
    """Configurer le secteur du profil utilisateur."""
    await client.patch(
        "/api/company/profile",
        headers=auth_headers(token),
        json={"sector": sector},
    )


class TestCreateAssessment:
    """Tests POST /api/esg/assessments."""

    @pytest.mark.asyncio
    async def test_create_assessment_success(self, client: AsyncClient) -> None:
        """T020-01 : Creation reussie d'une evaluation."""
        _, token = await create_authenticated_user(client)
        await set_user_sector(client, token, "agriculture")

        response = await client.post(
            "/api/esg/assessments",
            headers=auth_headers(token),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "draft"
        assert body["sector"] == "agriculture"
        assert body["overall_score"] is None

    @pytest.mark.asyncio
    async def test_create_assessment_no_sector(self, client: AsyncClient) -> None:
        """T020-02 : Echec si secteur manquant."""
        _, token = await create_authenticated_user(client)

        response = await client.post(
            "/api/esg/assessments",
            headers=auth_headers(token),
        )
        assert response.status_code == 400
        assert "secteur" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_assessment_unauthenticated(self, client: AsyncClient) -> None:
        """T020-03 : Echec sans authentification."""
        response = await client.post("/api/esg/assessments")
        assert response.status_code in (401, 403)


class TestListAssessments:
    """Tests GET /api/esg/assessments."""

    @pytest.mark.asyncio
    async def test_list_assessments_empty(self, client: AsyncClient) -> None:
        """T020-04 : Liste vide par defaut."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/esg/assessments",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_list_assessments_with_data(self, client: AsyncClient) -> None:
        """T020-05 : Liste avec evaluations."""
        _, token = await create_authenticated_user(client)
        await set_user_sector(client, token, "energie")

        # Creer 2 evaluations
        await client.post("/api/esg/assessments", headers=auth_headers(token))
        await client.post("/api/esg/assessments", headers=auth_headers(token))

        response = await client.get(
            "/api/esg/assessments",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["data"]) == 2


class TestGetAssessment:
    """Tests GET /api/esg/assessments/{id}."""

    @pytest.mark.asyncio
    async def test_get_assessment_success(self, client: AsyncClient) -> None:
        """T020-06 : Detail d'une evaluation."""
        _, token = await create_authenticated_user(client)
        await set_user_sector(client, token, "recyclage")

        create_resp = await client.post("/api/esg/assessments", headers=auth_headers(token))
        assessment_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/esg/assessments/{assessment_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["id"] == assessment_id

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, client: AsyncClient) -> None:
        """T020-07 : 404 pour evaluation inexistante."""
        _, token = await create_authenticated_user(client)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/api/esg/assessments/{fake_id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 404


class TestGetBenchmark:
    """Tests GET /api/esg/benchmarks/{sector}."""

    @pytest.mark.asyncio
    async def test_get_benchmark_success(self, client: AsyncClient) -> None:
        """T020-08 : Benchmark sectoriel pour agriculture."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/esg/benchmarks/agriculture",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["sector"] == "agriculture"
        assert body["sector_label"] == "Agriculture"
        assert "averages" in body

    @pytest.mark.asyncio
    async def test_get_benchmark_unknown_sector_returns_fallback(self, client: AsyncClient) -> None:
        """T020-09 : secteur inconnu retourne un benchmark general de repli."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/esg/benchmarks/inconnu",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sector"] == "general"
        assert "averages" in data
