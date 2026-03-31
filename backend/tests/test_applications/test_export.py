"""Tests pour l'export PDF et Word des dossiers."""

import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_application(
    target_type: str = "fund_direct",
    sections: dict | None = None,
):
    fund = MagicMock()
    fund.id = uuid.uuid4()
    fund.name = "FNDE"
    fund.organization = "Etat du Senegal"

    app_mock = MagicMock()
    app_mock.id = uuid.uuid4()
    app_mock.fund = fund
    app_mock.intermediary = None
    app_mock.target_type = MagicMock(value=target_type)
    app_mock.status = MagicMock(value="in_progress")
    app_mock.sections = sections or {
        "company_presentation": {
            "title": "Présentation de l'entreprise",
            "content": "<p>Entreprise ABC est spécialisée...</p>",
            "status": "generated",
            "updated_at": "2026-03-31T10:00:00Z",
        },
        "project_description": {
            "title": "Description du projet",
            "content": "<p>Le projet vise à installer...</p>",
            "status": "validated",
            "updated_at": "2026-03-31T11:00:00Z",
        },
    }
    app_mock.created_at = datetime.now(timezone.utc)
    return app_mock


# --- Tests export PDF ---


@pytest.mark.asyncio
async def test_export_pdf():
    """Export PDF avec WeasyPrint (mocke)."""
    # Mock weasyprint au niveau sys.modules pour eviter l'import des libs systeme
    mock_weasyprint = MagicMock()
    mock_weasyprint.HTML.return_value.write_pdf.return_value = b"%PDF-fake"
    with patch.dict(sys.modules, {"weasyprint": mock_weasyprint}):
        from app.modules.applications.export import export_application

        application = _make_application()
        file_bytes, content_type, filename = await export_application(
            application, format="pdf"
        )

    assert file_bytes == b"%PDF-fake"
    assert content_type == "application/pdf"
    assert filename.endswith(".pdf")


@pytest.mark.asyncio
async def test_export_docx():
    """Export Word avec python-docx."""
    from app.modules.applications.export import export_application

    application = _make_application()
    file_bytes, content_type, filename = await export_application(
        application, format="docx"
    )

    assert len(file_bytes) > 0
    assert content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert filename.endswith(".docx")


@pytest.mark.asyncio
async def test_export_invalid_format():
    """Format invalide → ValueError."""
    from app.modules.applications.export import export_application

    application = _make_application()
    with pytest.raises(ValueError, match="Format non supporte"):
        await export_application(application, format="csv")


@pytest.mark.asyncio
async def test_export_pdf_with_empty_sections():
    """Export PDF avec sections vides (content=None)."""
    mock_weasyprint = MagicMock()
    mock_weasyprint.HTML.return_value.write_pdf.return_value = b"%PDF-fake"
    with patch.dict(sys.modules, {"weasyprint": mock_weasyprint}):
        from app.modules.applications.export import export_application

        application = _make_application(sections={
            "company_presentation": {
                "title": "Présentation",
                "content": None,
                "status": "not_generated",
                "updated_at": None,
            },
        })
        file_bytes, _, _ = await export_application(application, format="pdf")

    assert file_bytes == b"%PDF-fake"


@pytest.mark.asyncio
async def test_export_docx_with_intermediary():
    """Export Word avec intermediaire."""
    from app.modules.applications.export import export_application

    application = _make_application()
    inter = MagicMock()
    inter.name = "SIB"
    application.intermediary = inter

    file_bytes, content_type, filename = await export_application(
        application, format="docx"
    )

    assert len(file_bytes) > 0
    assert filename.endswith(".docx")
