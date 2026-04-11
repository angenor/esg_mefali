"""Tests des endpoints REST du module company (US4).

T039: Tests GET /company/profile, PATCH /company/profile,
GET /company/profile/completion — succès, 404, validation 422.

Écrits AVANT l'implémentation (TDD RED phase).
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import make_unique_email


# ─── Helpers ──────────────────────────────────────────────────────────


async def create_authenticated_user(client: AsyncClient) -> tuple[dict, str]:
    """Créer un utilisateur et retourner ses données + access token."""
    data = {
        "email": make_unique_email(),
        "password": "motdepasse123",
        "full_name": "Fatou Diallo",
        "company_name": "EcoVert SARL",
    }
    await client.post("/api/auth/register", json=data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login_response.json()["access_token"]
    return data, token


def auth_headers(token: str) -> dict[str, str]:
    """Headers d'authentification."""
    return {"Authorization": f"Bearer {token}"}


# ─── Tests GET /api/company/profile ──────────────────────────────────


class TestGetProfile:
    """Tests GET /api/company/profile."""

    @pytest.mark.asyncio
    async def test_get_profile_creates_if_not_exists(self, client: AsyncClient) -> None:
        """GET crée un profil initialisé avec le nom fourni à l'inscription."""
        _, token = await create_authenticated_user(client)

        response = await client.get(
            "/api/company/profile",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert "id" in body
        # country est None en test (géolocalisation impossible sur 127.0.0.1)
        assert body["country"] is None
        # Le company_name est pré-rempli depuis User.company_name à l'inscription
        assert body["company_name"] == "EcoVert SARL"

    @pytest.mark.asyncio
    async def test_get_profile_returns_existing(self, client: AsyncClient) -> None:
        """GET retourne le profil existant après un PATCH."""
        _, token = await create_authenticated_user(client)

        # Créer le profil via GET
        await client.get("/api/company/profile", headers=auth_headers(token))

        # Mettre à jour
        await client.patch(
            "/api/company/profile",
            json={"company_name": "TestCo", "sector": "recyclage"},
            headers=auth_headers(token),
        )

        # Vérifier la persistance
        response = await client.get(
            "/api/company/profile",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["company_name"] == "TestCo"
        assert body["sector"] == "recyclage"

    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self, client: AsyncClient) -> None:
        """GET sans token retourne 401."""
        response = await client.get("/api/company/profile")
        assert response.status_code == 401


# ─── Tests PATCH /api/company/profile ────────────────────────────────


class TestUpdateProfile:
    """Tests PATCH /api/company/profile."""

    @pytest.mark.asyncio
    async def test_update_profile_partial(self, client: AsyncClient) -> None:
        """PATCH met à jour uniquement les champs fournis."""
        _, token = await create_authenticated_user(client)

        # Créer d'abord le profil
        await client.get("/api/company/profile", headers=auth_headers(token))

        response = await client.patch(
            "/api/company/profile",
            json={
                "company_name": "EcoPlast SARL",
                "sector": "recyclage",
                "employee_count": 15,
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["company_name"] == "EcoPlast SARL"
        assert body["sector"] == "recyclage"
        assert body["employee_count"] == 15
        assert body["country"] is None

    @pytest.mark.asyncio
    async def test_update_profile_invalid_sector(self, client: AsyncClient) -> None:
        """PATCH avec secteur invalide retourne 422."""
        _, token = await create_authenticated_user(client)
        await client.get("/api/company/profile", headers=auth_headers(token))

        response = await client.patch(
            "/api/company/profile",
            json={"sector": "spatial"},
            headers=auth_headers(token),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_negative_employee_count(self, client: AsyncClient) -> None:
        """PATCH avec employee_count négatif retourne 422."""
        _, token = await create_authenticated_user(client)
        await client.get("/api/company/profile", headers=auth_headers(token))

        response = await client.patch(
            "/api/company/profile",
            json={"employee_count": -5},
            headers=auth_headers(token),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, client: AsyncClient) -> None:
        """PATCH sans token retourne 401."""
        response = await client.patch(
            "/api/company/profile",
            json={"company_name": "Test"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_esg_fields(self, client: AsyncClient) -> None:
        """PATCH met à jour les champs ESG booléens."""
        _, token = await create_authenticated_user(client)
        await client.get("/api/company/profile", headers=auth_headers(token))

        response = await client.patch(
            "/api/company/profile",
            json={
                "has_waste_management": True,
                "has_energy_policy": False,
                "governance_structure": "Comité de direction",
            },
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["has_waste_management"] is True
        assert body["has_energy_policy"] is False
        assert body["governance_structure"] == "Comité de direction"


# ─── Tests GET /api/company/profile/completion ───────────────────────


class TestGetCompletion:
    """Tests GET /api/company/profile/completion."""

    @pytest.mark.asyncio
    async def test_completion_empty_profile(self, client: AsyncClient) -> None:
        """Profil initial → seul company_name est pré-rempli (1/8)."""
        _, token = await create_authenticated_user(client)
        await client.get("/api/company/profile", headers=auth_headers(token))

        response = await client.get(
            "/api/company/profile/completion",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        # Seul company_name est pré-rempli à l'inscription (country dépend
        # de la géolocalisation IP, indisponible en test) = 1/8
        assert body["identity_completion"] == 12.5
        assert body["esg_completion"] == 0.0
        assert body["overall_completion"] == pytest.approx(6.25, abs=0.1)
        assert "company_name" in body["identity_fields"]["filled"]
        assert "country" in body["identity_fields"]["missing"]

    @pytest.mark.asyncio
    async def test_completion_partial_profile(self, client: AsyncClient) -> None:
        """Profil partiel → complétion correcte."""
        _, token = await create_authenticated_user(client)
        await client.get("/api/company/profile", headers=auth_headers(token))

        await client.patch(
            "/api/company/profile",
            json={
                "company_name": "TestCo",
                "sector": "agriculture",
                "city": "Dakar",
                "employee_count": 10,
                "has_waste_management": True,
            },
            headers=auth_headers(token),
        )

        response = await client.get(
            "/api/company/profile/completion",
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        body = response.json()
        # 4 champs identité remplis sur 8 (company_name + sector + city + employee_count) = 50%
        assert body["identity_completion"] == 50.0
        # 1 champ ESG rempli sur 8 = 12.5%
        assert body["esg_completion"] == 12.5
        assert body["overall_completion"] == pytest.approx(31.25, abs=0.1)

    @pytest.mark.asyncio
    async def test_completion_unauthenticated(self, client: AsyncClient) -> None:
        """GET completion sans token retourne 401."""
        response = await client.get("/api/company/profile/completion")
        assert response.status_code == 401
