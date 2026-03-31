"""Tests unitaires de generation de graphiques SVG pour les rapports ESG (T014).

Verifie la generation de radar chart, bar chart et benchmark chart en SVG.
"""

import pytest


class TestRadarChartSvg:
    """Tests du graphique radar 3 piliers E-S-G."""

    @pytest.mark.asyncio
    async def test_radar_chart_returns_svg_string(self) -> None:
        """T014-01 : Le radar chart retourne une chaine SVG valide."""
        from app.modules.reports.charts import generate_radar_chart_svg

        scores = {
            "environment": 72.0,
            "social": 58.0,
            "governance": 85.0,
        }
        svg = generate_radar_chart_svg(scores)
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg

    @pytest.mark.asyncio
    async def test_radar_chart_contains_labels(self) -> None:
        """T014-02 : Le radar chart contient les labels des piliers."""
        from app.modules.reports.charts import generate_radar_chart_svg

        scores = {
            "environment": 72.0,
            "social": 58.0,
            "governance": 85.0,
        }
        svg = generate_radar_chart_svg(scores)
        assert "Environnement" in svg
        assert "Social" in svg
        assert "Gouvernance" in svg

    @pytest.mark.asyncio
    async def test_radar_chart_handles_zero_scores(self) -> None:
        """T014-03 : Le radar chart gere les scores a zero."""
        from app.modules.reports.charts import generate_radar_chart_svg

        scores = {
            "environment": 0.0,
            "social": 0.0,
            "governance": 0.0,
        }
        svg = generate_radar_chart_svg(scores)
        assert "<svg" in svg


class TestBarChartSvg:
    """Tests du graphique en barres de progression par critere."""

    @pytest.mark.asyncio
    async def test_bar_chart_returns_svg_string(self) -> None:
        """T014-04 : Le bar chart retourne une chaine SVG valide."""
        from app.modules.reports.charts import generate_bar_chart_svg

        criteria_scores = [
            {"code": "E1", "label": "Emissions GES", "score": 7, "max": 10},
            {"code": "E2", "label": "Energie", "score": 5, "max": 10},
            {"code": "E3", "label": "Dechets", "score": 8, "max": 10},
        ]
        svg = generate_bar_chart_svg(criteria_scores, "Environnement")
        assert isinstance(svg, str)
        assert "<svg" in svg

    @pytest.mark.asyncio
    async def test_bar_chart_contains_labels(self) -> None:
        """T014-05 : Le bar chart affiche les labels des criteres."""
        from app.modules.reports.charts import generate_bar_chart_svg

        criteria_scores = [
            {"code": "E1", "label": "Emissions GES", "score": 7, "max": 10},
        ]
        svg = generate_bar_chart_svg(criteria_scores, "Environnement")
        assert "Emissions GES" in svg


class TestBenchmarkChartSvg:
    """Tests du graphique de benchmarking sectoriel."""

    @pytest.mark.asyncio
    async def test_benchmark_chart_returns_svg_string(self) -> None:
        """T014-06 : Le benchmark chart retourne une chaine SVG valide."""
        from app.modules.reports.charts import generate_benchmark_chart_svg

        company_scores = {
            "environment": 72.0,
            "social": 58.0,
            "governance": 85.0,
            "overall": 71.7,
        }
        sector_averages = {
            "environment": 55.0,
            "social": 60.0,
            "governance": 50.0,
            "overall": 55.0,
        }
        svg = generate_benchmark_chart_svg(company_scores, sector_averages, "Agriculture")
        assert isinstance(svg, str)
        assert "<svg" in svg

    @pytest.mark.asyncio
    async def test_benchmark_chart_contains_sector_name(self) -> None:
        """T014-07 : Le benchmark chart affiche le nom du secteur."""
        from app.modules.reports.charts import generate_benchmark_chart_svg

        company_scores = {"environment": 72.0, "social": 58.0, "governance": 85.0, "overall": 71.7}
        sector_averages = {"environment": 55.0, "social": 60.0, "governance": 50.0, "overall": 55.0}
        svg = generate_benchmark_chart_svg(company_scores, sector_averages, "Agriculture")
        assert "Agriculture" in svg
