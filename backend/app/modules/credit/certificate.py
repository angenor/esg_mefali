"""Generation d'attestation PDF pour le score de credit vert."""


def generate_certificate_pdf(
    score: object,
    company_name: str = "Entreprise",
    sector: str = "",
    location: str = "",
) -> bytes:
    """Generer le PDF d'attestation de score de credit vert.

    Utilise WeasyPrint + Jinja2. Implementation complete en Phase 7 (US5).
    """
    try:
        from weasyprint import HTML
    except ImportError:
        # Fallback si WeasyPrint non installe
        return b"%PDF-1.4 placeholder"

    from jinja2 import Template
    from pathlib import Path

    template_path = Path(__file__).parent / "certificate_template.html"
    if not template_path.exists():
        return b"%PDF-1.4 placeholder"

    template_content = template_path.read_text(encoding="utf-8")
    template = Template(template_content)

    confidence_label_fr = {
        "very_low": "Tres faible",
        "low": "Faible",
        "medium": "Moyen",
        "good": "Bon",
        "excellent": "Excellent",
    }
    label = score.confidence_label
    if hasattr(label, "value"):
        label = label.value

    html_content = template.render(
        company_name=company_name,
        sector=sector,
        location=location,
        combined_score=score.combined_score,
        solvability_score=score.solvability_score,
        green_impact_score=score.green_impact_score,
        confidence_level=score.confidence_level,
        confidence_label=confidence_label_fr.get(label, label),
        version=score.version,
        generated_at=score.generated_at.strftime("%d/%m/%Y") if score.generated_at else "",
        valid_until=score.valid_until.strftime("%d/%m/%Y") if score.valid_until else "",
        score_breakdown=score.score_breakdown if hasattr(score, "score_breakdown") else {},
    )

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
