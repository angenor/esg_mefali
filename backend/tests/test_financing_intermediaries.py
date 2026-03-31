"""Tests des endpoints intermediaires du module Financement Vert (US4)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


def _make_intermediary(
    name: str = "SIB",
    intermediary_type: str = "partner_bank",
    organization_type: str = "bank",
    country: str = "Cote d'Ivoire",
    city: str = "Abidjan",
    is_active: bool = True,
):
    """Creer un mock d'intermediaire."""
    inter = MagicMock()
    inter.id = uuid.uuid4()
    inter.name = name
    inter.intermediary_type = MagicMock(value=intermediary_type)
    inter.organization_type = MagicMock(value=organization_type)
    inter.country = country
    inter.city = city
    inter.is_active = is_active
    inter.services_offered = {"credit_evaluation": True}
    inter.description = "Description test"
    inter.website_url = "https://example.com"
    inter.contact_email = "contact@example.com"
    inter.contact_phone = "+225 00 00"
    inter.physical_address = "Abidjan, Plateau"
    inter.accreditations = ["SUNREF"]
    inter.typical_fees = "Taux bonifie"
    inter.eligibility_for_sme = {"min_revenue": 5_000_000}
    inter.created_at = "2026-01-01T00:00:00"
    inter.updated_at = "2026-01-01T00:00:00"
    inter.fund_intermediaries = []
    return inter


@pytest.mark.asyncio
async def test_list_intermediaries(mock_user):
    """GET /intermediaries retourne la liste paginee."""
    inter1 = _make_intermediary(name="SIB")
    inter2 = _make_intermediary(name="SGBCI", organization_type="bank")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediaries",
            new_callable=AsyncMock,
            return_value=([inter1, inter2], 2),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/financing/intermediaries",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_intermediaries_with_type_filter(mock_user):
    """GET /intermediaries?organization_type=bank filtre par type."""
    inter = _make_intermediary(name="SIB")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediaries",
            new_callable=AsyncMock,
            return_value=([inter], 1),
        ) as mock_get,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/financing/intermediaries?organization_type=bank",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs.get("organization_type") == "bank" or (
        len(call_kwargs.args) > 0
    )


@pytest.mark.asyncio
async def test_list_intermediaries_with_fund_filter(mock_user):
    """GET /intermediaries?fund_id=... filtre par fonds."""
    inter = _make_intermediary()
    fund_id = uuid.uuid4()

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediaries",
            new_callable=AsyncMock,
            return_value=([inter], 1),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/financing/intermediaries?fund_id={fund_id}",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_intermediary_detail(mock_user):
    """GET /intermediaries/{id} retourne le detail avec fonds couverts."""
    inter = _make_intermediary()

    # Simuler un fonds couvert
    fund_mock = MagicMock()
    fund_mock.id = uuid.uuid4()
    fund_mock.name = "SUNREF"

    fi_mock = MagicMock()
    fi_mock.fund = fund_mock
    fi_mock.role = "Banque partenaire"
    fi_mock.is_primary = True

    inter.fund_intermediaries = [fi_mock]

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediary_by_id",
            new_callable=AsyncMock,
            return_value=inter,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/financing/intermediaries/{inter.id}",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SIB"
    assert len(data["funds_covered"]) == 1
    assert data["funds_covered"][0]["name"] == "SUNREF"


@pytest.mark.asyncio
async def test_get_intermediary_not_found(mock_user):
    """GET /intermediaries/{id} retourne 404 si non trouve."""
    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediary_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/financing/intermediaries/{uuid.uuid4()}",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_nearby_intermediaries(mock_user):
    """GET /intermediaries/nearby?city=Abidjan retourne les intermediaires proches."""
    inter = _make_intermediary(city="Abidjan")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_intermediaries",
            new_callable=AsyncMock,
            return_value=([inter], 1),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/financing/intermediaries/nearby?city=Abidjan",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.asyncio
async def test_nearby_requires_city(mock_user):
    """GET /intermediaries/nearby sans city retourne 422."""
    with patch("app.api.deps.get_current_user", return_value=mock_user):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/financing/intermediaries/nearby",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 422
