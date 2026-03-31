"""Tests de generation du certificat PDF de credit vert."""

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_score(
    combined: float = 74.5,
    solvability: float = 68.0,
    green_impact: float = 81.0,
    confidence_level: float = 0.85,
    confidence_label: str = "bon",
    version: int = 3,
    expired: bool = False,
) -> MagicMock:
    """Creer un mock CreditScore pour les tests."""
    now = datetime.now(tz=timezone.utc)
    score = MagicMock()
    score.combined_score = combined
    score.solvability_score = solvability
    score.green_impact_score = green_impact
    score.confidence_level = confidence_level
    score.confidence_label = confidence_label
    score.version = version
    score.generated_at = now - timedelta(days=30)
    score.valid_until = now - timedelta(days=1) if expired else now + timedelta(days=150)
    score.score_breakdown = {
        "solvability": {
            "total": solvability,
            "factors": {
                "activity_regularity": {"score": 70, "weight": 0.20, "details": "Activite reguliere"},
                "information_coherence": {"score": 60, "weight": 0.20, "details": "Coherent"},
                "governance": {"score": 55, "weight": 0.20, "details": "Basique"},
                "financial_transparency": {"score": 75, "weight": 0.20, "details": "3 documents"},
                "engagement_seriousness": {"score": 80, "weight": 0.20, "details": "2 intermediaires"},
            },
        },
        "green_impact": {
            "total": green_impact,
            "factors": {
                "esg_global_score": {"score": 72, "weight": 0.40, "details": "ESG 72/100"},
                "esg_trend": {"score": 85, "weight": 0.20, "details": "Amelioration"},
                "carbon_engagement": {"score": 80, "weight": 0.20, "details": "Bilan realise"},
                "green_projects": {"score": 90, "weight": 0.20, "details": "2 candidatures"},
            },
        },
    }
    score.recommendations = [
        {"action": "Completez votre profil", "impact": "high", "category": "solvability"},
    ]
    return score


def _mock_weasyprint() -> MagicMock:
    """Creer un mock WeasyPrint qui retourne un faux PDF."""
    mock_wp = MagicMock()
    mock_wp.HTML.return_value.write_pdf.return_value = b"%PDF-1.4 mock-certificate-pdf-content"
    return mock_wp


def _generate_with_mock(score: MagicMock, **kwargs) -> bytes:
    """Generer un certificat avec WeasyPrint mocke."""
    mock_wp = _mock_weasyprint()

    # Forcer le reimport du module certificate avec le mock WeasyPrint
    # Supprimer le module du cache pour forcer le reimport
    if "app.modules.credit.certificate" in sys.modules:
        del sys.modules["app.modules.credit.certificate"]

    with patch.dict(sys.modules, {"weasyprint": mock_wp}):
        from app.modules.credit.certificate import generate_certificate_pdf

        return generate_certificate_pdf(score=score, **kwargs)


class TestGenerateCertificatePdf:
    """Tests pour la generation de l'attestation PDF."""

    def test_generate_pdf_returns_bytes(self) -> None:
        """Le PDF genere doit etre un bytes non vide."""
        score = _make_mock_score()
        pdf = _generate_with_mock(
            score=score,
            company_name="AgriVert SA",
            sector="agriculture",
            location="Abidjan",
        )

        assert isinstance(pdf, bytes)
        assert len(pdf) > 10

    def test_pdf_starts_with_pdf_header(self) -> None:
        """Le PDF doit commencer par le magic number %PDF."""
        score = _make_mock_score()
        pdf = _generate_with_mock(score=score, company_name="Test SARL")

        assert pdf[:5] == b"%PDF-"

    def test_weasyprint_called_with_html(self) -> None:
        """WeasyPrint.HTML doit etre appele avec le contenu HTML genere."""
        mock_wp = _mock_weasyprint()
        score = _make_mock_score()

        if "app.modules.credit.certificate" in sys.modules:
            del sys.modules["app.modules.credit.certificate"]

        with patch.dict(sys.modules, {"weasyprint": mock_wp}):
            from app.modules.credit.certificate import generate_certificate_pdf

            generate_certificate_pdf(
                score=score,
                company_name="SolarTech Mali",
                sector="energie",
                location="Bamako",
            )

        # Verifier que HTML() a ete appele avec du contenu string
        mock_wp.HTML.assert_called_once()
        call_kwargs = mock_wp.HTML.call_args
        html_string = call_kwargs.kwargs.get("string") or call_kwargs[1].get("string", "")
        assert "SolarTech Mali" in html_string
        assert "energie" in html_string
        assert "Bamako" in html_string

    def test_html_contains_scores(self) -> None:
        """Le HTML genere doit contenir les scores numeriques."""
        mock_wp = _mock_weasyprint()
        score = _make_mock_score(combined=82.3, solvability=75.0, green_impact=89.6)

        if "app.modules.credit.certificate" in sys.modules:
            del sys.modules["app.modules.credit.certificate"]

        with patch.dict(sys.modules, {"weasyprint": mock_wp}):
            from app.modules.credit.certificate import generate_certificate_pdf

            generate_certificate_pdf(score=score, company_name="Test")

        call_kwargs = mock_wp.HTML.call_args
        html_string = call_kwargs.kwargs.get("string") or call_kwargs[1].get("string", "")
        assert "82.3" in html_string
        assert "75.0" in html_string
        assert "89.6" in html_string

    def test_html_contains_disclaimer(self) -> None:
        """Le HTML genere doit contenir la mention legale."""
        mock_wp = _mock_weasyprint()
        score = _make_mock_score()

        if "app.modules.credit.certificate" in sys.modules:
            del sys.modules["app.modules.credit.certificate"]

        with patch.dict(sys.modules, {"weasyprint": mock_wp}):
            from app.modules.credit.certificate import generate_certificate_pdf

            generate_certificate_pdf(score=score, company_name="Test")

        call_kwargs = mock_wp.HTML.call_args
        html_string = call_kwargs.kwargs.get("string") or call_kwargs[1].get("string", "")
        assert "informatif" in html_string
        assert "credit officiel" in html_string

    def test_pdf_with_empty_breakdown(self) -> None:
        """Le PDF doit fonctionner meme avec un breakdown vide."""
        score = _make_mock_score()
        score.score_breakdown = {}
        pdf = _generate_with_mock(score=score, company_name="Test")

        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_with_no_sector(self) -> None:
        """Le PDF doit fonctionner sans secteur ni localisation."""
        score = _make_mock_score()
        pdf = _generate_with_mock(
            score=score,
            company_name="Minimal Corp",
            sector="",
            location="",
        )

        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_html_contains_confidence_label_fr(self) -> None:
        """Le HTML doit afficher le label de confiance en francais."""
        mock_wp = _mock_weasyprint()
        score = _make_mock_score(confidence_label="good")

        if "app.modules.credit.certificate" in sys.modules:
            del sys.modules["app.modules.credit.certificate"]

        with patch.dict(sys.modules, {"weasyprint": mock_wp}):
            from app.modules.credit.certificate import generate_certificate_pdf

            generate_certificate_pdf(score=score, company_name="Test")

        call_kwargs = mock_wp.HTML.call_args
        html_string = call_kwargs.kwargs.get("string") or call_kwargs[1].get("string", "")
        assert "Bon" in html_string

    def test_html_contains_factors(self) -> None:
        """Le HTML doit afficher les facteurs du breakdown."""
        mock_wp = _mock_weasyprint()
        score = _make_mock_score()

        if "app.modules.credit.certificate" in sys.modules:
            del sys.modules["app.modules.credit.certificate"]

        with patch.dict(sys.modules, {"weasyprint": mock_wp}):
            from app.modules.credit.certificate import generate_certificate_pdf

            generate_certificate_pdf(score=score, company_name="Test")

        call_kwargs = mock_wp.HTML.call_args
        html_string = call_kwargs.kwargs.get("string") or call_kwargs[1].get("string", "")
        assert "Activite reguliere" in html_string
        assert "ESG 72/100" in html_string
