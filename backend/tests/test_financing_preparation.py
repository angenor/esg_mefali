"""Tests de la generation de fiche de preparation PDF (US5)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _make_match_with_fund():
    """Creer un mock de match avec fonds complet."""
    fund = MagicMock()
    fund.id = uuid.uuid4()
    fund.name = "SUNREF (AFD/Proparco)"
    fund.organization = "AFD / Proparco"
    fund.description = "Ligne de credit verte"
    fund.fund_type = MagicMock(value="regional")
    fund.access_type = MagicMock(value="intermediary_required")
    fund.intermediary_type = MagicMock(value="partner_bank")
    fund.required_documents = ["business_plan", "financial_statements"]
    fund.typical_timeline_months = 6

    match = MagicMock()
    match.id = uuid.uuid4()
    match.user_id = uuid.uuid4()
    match.fund_id = fund.id
    match.fund = fund
    match.compatibility_score = 78
    match.matching_criteria = {"sector": 90, "esg": 65, "size": 70, "location": 80, "documents": 60}
    match.missing_criteria = {"documents": ["esg_report"]}
    match.contacted_intermediary_id = None
    match.status = MagicMock(value="interested")
    return match, fund


@pytest.mark.asyncio
@pytest.mark.usefixtures("override_auth")
async def test_preparation_sheet_endpoint(override_auth):
    """GET /matches/{id}/preparation-sheet retourne un PDF."""
    match, fund = _make_match_with_fund()
    match.user_id = override_auth.id

    pdf_bytes = b"%PDF-1.4 mock content"

    with (
        patch(
            "app.modules.financing.service.get_match_by_id",
            new_callable=AsyncMock,
            return_value=match,
        ),
        patch(
            "app.modules.financing.service.get_fund_by_id",
            new_callable=AsyncMock,
            return_value=fund,
        ),
        patch(
            "app.modules.financing.preparation_sheet.generate_preparation_sheet",
            new_callable=AsyncMock,
            return_value=pdf_bytes,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/financing/matches/{match.id}/preparation-sheet",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "fiche-preparation" in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
@pytest.mark.usefixtures("override_auth")
async def test_preparation_sheet_not_found():
    """GET /matches/{id}/preparation-sheet sans match -> 404."""
    with (
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
            response = await client.get(
                f"/api/financing/matches/{uuid.uuid4()}/preparation-sheet",
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 404


def test_generate_preparation_sheet_content():
    """Verifier que le contenu de la fiche inclut les elements requis."""
    from app.modules.financing.preparation_sheet import _render_preparation_html

    html = _render_preparation_html(
        company_name="AgriTech Sahel SARL",
        company_sector="Agriculture",
        company_city="Abidjan",
        fund_name="SUNREF (AFD/Proparco)",
        fund_organization="AFD / Proparco",
        compatibility_score=78,
        matching_criteria={"sector": 90, "esg": 65, "size": 70, "location": 80, "documents": 60},
        missing_criteria={"documents": ["esg_report"]},
        esg_score=65,
        carbon_total=3.7,
        intermediary_name="SIB",
        intermediary_contact="contact@sib.ci",
        intermediary_address="Abidjan, Plateau",
        required_documents=["business_plan", "financial_statements"],
        timeline_months=6,
    )

    assert "AgriTech Sahel SARL" in html
    assert "SUNREF" in html
    assert "78" in html
    assert "SIB" in html
    assert "business_plan" in html or "business plan" in html.lower()


def test_generate_preparation_sheet_without_scores():
    """Verifier le rendu sans score ESG ni carbone."""
    from app.modules.financing.preparation_sheet import _render_preparation_html

    html = _render_preparation_html(
        company_name="Test SARL",
        company_sector="Services",
        company_city="Dakar",
        fund_name="FNDE",
        fund_organization="Etat de Cote d'Ivoire",
        compatibility_score=45,
        matching_criteria={"sector": 50, "esg": 0},
        missing_criteria={"esg": ["Score ESG requis"]},
        esg_score=None,
        carbon_total=None,
        intermediary_name=None,
        intermediary_contact=None,
        intermediary_address=None,
        required_documents=[],
        timeline_months=3,
    )

    assert "Test SARL" in html
    assert "FNDE" in html
    assert "Non disponible" in html or "N/A" in html or "non disponible" in html
