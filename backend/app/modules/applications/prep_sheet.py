"""Generation de la fiche de preparation intermediaire PDF."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "prep_sheet.html"


def _render_prep_sheet_html(
    application,
    esg_score: int | None = None,
    carbon_total: float | None = None,
    available_documents: list[str] | None = None,
    questions: list[str] | None = None,
) -> str:
    """Rendre le template HTML de la fiche de preparation."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template(TEMPLATE_NAME)

    fund = application.fund
    intermediary = application.intermediary

    return template.render(
        fund_name=fund.name if fund else "Fonds",
        fund_organization=fund.organization if fund else "",
        fund_description=fund.description if fund else "",
        intermediary_name=intermediary.name if intermediary else "Intermédiaire",
        intermediary_email=intermediary.contact_email if intermediary else None,
        intermediary_phone=intermediary.contact_phone if intermediary else None,
        intermediary_address=intermediary.physical_address if intermediary else None,
        company_summary=None,  # A enrichir avec le profil utilisateur
        esg_score=esg_score,
        carbon_total=carbon_total,
        available_documents=available_documents or [],
        questions=questions or [],
        generated_date=datetime.now(timezone.utc).strftime("%d/%m/%Y"),
    )


async def _generate_questions(
    fund_name: str,
    intermediary_name: str,
    target_type: str,
) -> list[str]:
    """Generer 5 questions pertinentes via LLM."""
    try:
        from app.graph.nodes import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_llm()
        prompt = f"""Tu es un conseiller en financement vert pour les PME africaines.

Genere exactement 5 questions pertinentes qu'une PME devrait poser a l'intermediaire {intermediary_name}
pour preparer sa candidature au fonds {fund_name}.

Le type de destinataire est : {target_type}.

Reponds avec uniquement les 5 questions numerotees (1. ... 2. ... etc.), sans introduction ni conclusion.
Les questions doivent etre en francais, concretes et adaptees au contexte africain."""

        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Genere les 5 questions."),
        ])

        # Parser les questions
        lines = response.content.strip().split("\n")
        questions = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Retirer le numero/tiret en debut
                cleaned = line.lstrip("0123456789.-) ").strip()
                if cleaned:
                    questions.append(cleaned)
        return questions[:5]
    except Exception as e:
        logger.warning("Impossible de generer les questions : %s", e)
        return [
            "Quels sont les critères d'éligibilité spécifiques pour notre profil d'entreprise ?",
            "Quel est le calendrier typique de traitement d'un dossier ?",
            "Quels documents supplémentaires pourraient renforcer notre candidature ?",
            "Y a-t-il des frais de dossier ou commissions à prévoir ?",
            "Pouvez-vous nous accompagner dans la constitution du dossier ?",
        ]


async def generate_prep_sheet(
    db: AsyncSession,
    application,
) -> bytes:
    """Generer la fiche de preparation intermediaire en PDF.

    Collecte les donnees (ESG, carbone, documents) et genere un PDF
    de 2-3 pages avec resume entreprise, scores, eligibilite,
    documents disponibles, questions et coordonnees intermediaire.
    """
    target_val = application.target_type.value if hasattr(application.target_type, 'value') else application.target_type
    if target_val == "fund_direct":
        raise ValueError("La fiche de preparation n'est disponible que pour les dossiers avec intermediaire")

    # Collecter les documents disponibles depuis la checklist
    available_documents = [
        item["name"]
        for item in (application.checklist or [])
        if item.get("status") == "provided"
    ]

    # Generer les questions via LLM
    fund_name = application.fund.name if application.fund else "Fonds"
    intermediary_name = application.intermediary.name if application.intermediary else "Intermédiaire"
    questions = await _generate_questions(fund_name, intermediary_name, target_val)

    # Rendre le HTML
    html_content = _render_prep_sheet_html(
        application=application,
        esg_score=None,  # A enrichir avec les donnees ESG reelles
        carbon_total=None,  # A enrichir avec les donnees carbone reelles
        available_documents=available_documents,
        questions=questions,
    )

    # Generer le PDF
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
