"""Generation de la fiche de preparation PDF pour un rendez-vous financement."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent
TEMPLATE_NAME = "preparation_template.html"

CRITERIA_LABELS = {
    "sector": "Secteur d'activite",
    "esg": "Score ESG",
    "size": "Taille / chiffre d'affaires",
    "location": "Localisation geographique",
    "documents": "Documents disponibles",
}


def _render_preparation_html(
    company_name: str,
    company_sector: str,
    company_city: str,
    fund_name: str,
    fund_organization: str,
    compatibility_score: int,
    matching_criteria: dict[str, int],
    missing_criteria: dict[str, list[str]],
    esg_score: int | None,
    carbon_total: float | None,
    intermediary_name: str | None,
    intermediary_contact: str | None,
    intermediary_address: str | None,
    required_documents: list[str],
    timeline_months: int,
) -> str:
    """Rendre le template HTML de la fiche de preparation."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template(TEMPLATE_NAME)

    return template.render(
        company_name=company_name,
        company_sector=company_sector,
        company_city=company_city,
        fund_name=fund_name,
        fund_organization=fund_organization,
        compatibility_score=compatibility_score,
        matching_criteria=matching_criteria,
        missing_criteria=missing_criteria,
        criteria_labels=CRITERIA_LABELS,
        esg_score=esg_score,
        carbon_total=carbon_total,
        intermediary_name=intermediary_name,
        intermediary_contact=intermediary_contact,
        intermediary_address=intermediary_address,
        required_documents=required_documents,
        timeline_months=timeline_months,
    )


async def generate_preparation_sheet(
    company_name: str,
    company_sector: str,
    company_city: str,
    fund_name: str,
    fund_organization: str,
    compatibility_score: int,
    matching_criteria: dict[str, int],
    missing_criteria: dict[str, list[str]],
    esg_score: int | None = None,
    carbon_total: float | None = None,
    intermediary_name: str | None = None,
    intermediary_contact: str | None = None,
    intermediary_address: str | None = None,
    required_documents: list[str] | None = None,
    timeline_months: int = 6,
) -> bytes:
    """Generer le PDF de la fiche de preparation.

    Utilise WeasyPrint pour convertir le HTML en PDF.
    Retourne les bytes du PDF.
    """
    html_content = _render_preparation_html(
        company_name=company_name,
        company_sector=company_sector,
        company_city=company_city,
        fund_name=fund_name,
        fund_organization=fund_organization,
        compatibility_score=compatibility_score,
        matching_criteria=matching_criteria,
        missing_criteria=missing_criteria,
        esg_score=esg_score,
        carbon_total=carbon_total,
        intermediary_name=intermediary_name,
        intermediary_contact=intermediary_contact,
        intermediary_address=intermediary_address,
        required_documents=required_documents or [],
        timeline_months=timeline_months,
    )

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
