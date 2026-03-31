"""Tests pour la generation de la fiche de preparation intermediaire."""

import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_fund():
    fund = MagicMock()
    fund.id = uuid.uuid4()
    fund.name = "SUNREF"
    fund.organization = "AFD"
    fund.description = "Ligne de credit verte"
    fund.sectors_eligible = ["energie", "industrie"]
    return fund


def _make_intermediary():
    inter = MagicMock()
    inter.id = uuid.uuid4()
    inter.name = "SIB"
    inter.contact_email = "green@sib.ci"
    inter.contact_phone = "+225 27 20 30 40 50"
    inter.physical_address = "Abidjan, Plateau, Rue du Commerce"
    return inter


def _make_application(
    target_type: str = "intermediary_bank",
    with_intermediary: bool = True,
):
    fund = _make_fund()
    inter = _make_intermediary() if with_intermediary else None

    app_mock = MagicMock()
    app_mock.id = uuid.uuid4()
    app_mock.user_id = uuid.uuid4()
    app_mock.fund = fund
    app_mock.intermediary = inter
    app_mock.target_type = MagicMock(value=target_type)
    app_mock.status = MagicMock(value="in_progress")
    app_mock.sections = {
        "company_banking_history": {
            "title": "Historique bancaire",
            "content": "<p>Contenu</p>",
            "status": "generated",
            "updated_at": "2026-03-31T10:00:00Z",
        },
    }
    app_mock.checklist = [
        {"key": "rccm", "name": "RCCM", "status": "provided", "document_id": str(uuid.uuid4()), "required_by": "intermediary_bank"},
        {"key": "bilans", "name": "Bilans comptables", "status": "missing", "document_id": None, "required_by": "intermediary_bank"},
    ]
    app_mock.intermediary_prep = None
    app_mock.created_at = datetime.now(timezone.utc)
    app_mock.updated_at = datetime.now(timezone.utc)
    return app_mock


# --- Tests generate_prep_sheet ---


@pytest.mark.asyncio
async def test_generate_prep_sheet_success():
    """Generer la fiche de preparation avec succes."""
    mock_weasyprint = MagicMock()
    mock_weasyprint.HTML.return_value.write_pdf.return_value = b"%PDF-prep-sheet"

    with patch.dict(sys.modules, {"weasyprint": mock_weasyprint}):
        from app.modules.applications.prep_sheet import generate_prep_sheet

        application = _make_application()
        db = AsyncMock()

        # Mock LLM pour les questions
        mock_response = MagicMock()
        mock_response.content = "1. Question 1\n2. Question 2\n3. Question 3\n4. Question 4\n5. Question 5"

        with (
            patch("app.graph.nodes.get_llm") as mock_get_llm,
        ):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            pdf_bytes = await generate_prep_sheet(db, application)

    assert pdf_bytes == b"%PDF-prep-sheet"


@pytest.mark.asyncio
async def test_generate_prep_sheet_no_intermediary():
    """Fiche de preparation sans intermediaire → ValueError."""
    from app.modules.applications.prep_sheet import generate_prep_sheet

    application = _make_application(target_type="fund_direct", with_intermediary=False)
    db = AsyncMock()

    with pytest.raises(ValueError, match="intermediaire"):
        await generate_prep_sheet(db, application)


@pytest.mark.asyncio
async def test_prep_sheet_contains_intermediary_info():
    """La fiche contient les coordonnees de l'intermediaire."""
    from app.modules.applications.prep_sheet import _render_prep_sheet_html

    application = _make_application()
    questions = ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]

    html = _render_prep_sheet_html(
        application=application,
        esg_score=72,
        carbon_total=150.5,
        available_documents=["RCCM"],
        questions=questions,
    )

    assert "SIB" in html
    assert "green@sib.ci" in html
    assert "+225 27 20 30 40 50" in html
    assert "Abidjan, Plateau" in html


@pytest.mark.asyncio
async def test_prep_sheet_includes_all_elements():
    """La fiche contient les 6 elements requis."""
    from app.modules.applications.prep_sheet import _render_prep_sheet_html

    application = _make_application()

    html = _render_prep_sheet_html(
        application=application,
        esg_score=72,
        carbon_total=150.5,
        available_documents=["RCCM", "Bilan 2024"],
        questions=["Q1?", "Q2?", "Q3?"],
    )

    # Les 6 elements : resume entreprise, score ESG, bilan carbone, eligibilite, docs, questions
    assert "SUNREF" in html  # Fonds (eligibilite)
    assert "72" in html  # Score ESG
    assert "150" in html  # Bilan carbone
    assert "RCCM" in html  # Documents disponibles
    assert "Q1?" in html  # Questions
