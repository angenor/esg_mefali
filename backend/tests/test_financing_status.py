"""Tests des endpoints statut et intermediaire du module Financement Vert (US5)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.financing import MatchStatus


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


def _make_match(status: str = "suggested"):
    """Creer un mock de FundMatch."""
    fund = MagicMock()
    fund.id = uuid.uuid4()
    fund.name = "SUNREF"
    fund.organization = "AFD"
    fund.fund_type = MagicMock(value="regional")
    fund.access_type = MagicMock(value="intermediary_required")
    fund.intermediary_type = MagicMock(value="partner_bank")
    fund.min_amount_xof = 5_000_000
    fund.max_amount_xof = 500_000_000

    match = MagicMock()
    match.id = uuid.uuid4()
    match.fund_id = fund.id
    match.fund = fund
    match.compatibility_score = 75
    match.matching_criteria = {"sector": 90, "esg": 60}
    match.missing_criteria = {}
    match.recommended_intermediaries = [
        {"id": str(uuid.uuid4()), "name": "SIB", "city": "Abidjan"}
    ]
    match.estimated_timeline_months = 6
    match.status = MagicMock(value=status)
    match.contacted_intermediary_id = None
    return match


@pytest.mark.asyncio
async def test_update_status_suggested_to_interested(mock_user):
    """PATCH /matches/{id}/status : suggested -> interested OK."""
    match = _make_match("suggested")
    updated = _make_match("interested")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=match,
        ),
        patch(
            "app.modules.financing.service.update_match_status",
            new_callable=AsyncMock,
            return_value=updated,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/financing/matches/{match.id}/status",
                json={"status": "interested"},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "interested"


@pytest.mark.asyncio
async def test_update_status_invalid_transition(mock_user):
    """PATCH /matches/{id}/status : transition invalide -> 409."""
    match = _make_match("suggested")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=match,
        ),
        patch(
            "app.modules.financing.service.update_match_status",
            new_callable=AsyncMock,
            side_effect=ValueError("Transition invalide"),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/financing/matches/{match.id}/status",
                json={"status": "submitted"},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_status_not_found(mock_user):
    """PATCH /matches/{id}/status : match non trouve -> 404."""
    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/financing/matches/{uuid.uuid4()}/status",
                json={"status": "interested"},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_intermediary_success(mock_user):
    """PATCH /matches/{id}/intermediary : choix OK."""
    match = _make_match("interested")
    intermediary_id = uuid.uuid4()
    updated = _make_match("contacting_intermediary")
    updated.contacted_intermediary_id = intermediary_id

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=match,
        ),
        patch(
            "app.modules.financing.service.update_match_intermediary",
            new_callable=AsyncMock,
            return_value=updated,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/financing/matches/{match.id}/intermediary",
                json={"intermediary_id": str(intermediary_id)},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_intermediary_not_linked(mock_user):
    """PATCH /matches/{id}/intermediary : intermediaire non lie -> 409."""
    match = _make_match("interested")

    with (
        patch("app.api.deps.get_current_user", return_value=mock_user),
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=match,
        ),
        patch(
            "app.modules.financing.service.update_match_intermediary",
            new_callable=AsyncMock,
            side_effect=ValueError("Cet intermediaire n'est pas lie a ce fonds."),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/api/financing/matches/{match.id}/intermediary",
                json={"intermediary_id": str(uuid.uuid4())},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 409
