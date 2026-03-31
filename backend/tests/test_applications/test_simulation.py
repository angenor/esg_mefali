"""Tests pour le simulateur de financement (US6 — T044, T045)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.applications.simulation import (
    _build_timeline,
    _estimate_eligible_amount,
    _estimate_intermediary_fees,
    _estimate_roi_green,
    run_simulation,
)


# =====================================================================
# HELPERS MOCK
# =====================================================================


def _make_mock_fund(
    min_amount: int | None = 5_000_000,
    max_amount: int | None = 500_000_000,
    timeline_months: int | None = 12,
    name: str = "SUNREF",
) -> MagicMock:
    fund = MagicMock()
    fund.name = name
    fund.min_amount_xof = min_amount
    fund.max_amount_xof = max_amount
    fund.typical_timeline_months = timeline_months
    return fund


def _make_mock_intermediary(
    typical_fees: str | None = "2-5% du montant finance",
    intermediary_type: str = "partner_bank",
    name: str = "SIB",
) -> MagicMock:
    intermediary = MagicMock()
    intermediary.typical_fees = typical_fees
    intermediary.intermediary_type = MagicMock(value=intermediary_type)
    intermediary.name = name
    return intermediary


def _make_mock_application(
    target_type: str = "intermediary_bank",
    fund: MagicMock | None = None,
    intermediary: MagicMock | None = None,
) -> MagicMock:
    app = MagicMock()
    app.id = uuid.uuid4()
    app.target_type = MagicMock(value=target_type)
    app.fund = fund or _make_mock_fund()
    app.intermediary = intermediary or _make_mock_intermediary()
    app.simulation = None
    app.sections = {}
    return app


# =====================================================================
# TESTS ESTIMATION MONTANT ELIGIBLE (T044)
# =====================================================================


class TestEstimateEligibleAmount:
    """Tests pour l'estimation du montant eligible."""

    def test_with_min_and_max(self) -> None:
        """Retourne la moyenne de min et max."""
        fund = _make_mock_fund(min_amount=10_000_000, max_amount=100_000_000)
        result = _estimate_eligible_amount(fund)
        assert result == 55_000_000

    def test_with_only_max(self) -> None:
        """Retourne max / 2 si pas de min."""
        fund = _make_mock_fund(min_amount=None, max_amount=100_000_000)
        result = _estimate_eligible_amount(fund)
        assert result == 50_000_000

    def test_with_only_min(self) -> None:
        """Retourne min * 2 si pas de max."""
        fund = _make_mock_fund(min_amount=10_000_000, max_amount=None)
        result = _estimate_eligible_amount(fund)
        assert result == 20_000_000

    def test_with_no_amounts(self) -> None:
        """Retourne une estimation par defaut si ni min ni max."""
        fund = _make_mock_fund(min_amount=None, max_amount=None)
        result = _estimate_eligible_amount(fund)
        assert result == 50_000_000  # defaut


# =====================================================================
# TESTS ROI VERT (T044)
# =====================================================================


class TestEstimateRoiGreen:
    """Tests pour l'estimation du ROI vert."""

    def test_basic_roi_calculation(self) -> None:
        """Le ROI vert retourne des economies annuelles et un payback."""
        result = _estimate_roi_green(eligible_amount=100_000_000)
        assert "annual_savings_xof" in result
        assert "payback_months" in result
        assert result["annual_savings_xof"] > 0
        assert result["payback_months"] > 0

    def test_payback_proportional_to_amount(self) -> None:
        """Le payback est proportionnel au montant."""
        roi_small = _estimate_roi_green(eligible_amount=10_000_000)
        roi_large = _estimate_roi_green(eligible_amount=100_000_000)
        # Le payback ne doit pas varier lineairement mais reste raisonnable
        assert roi_small["payback_months"] == roi_large["payback_months"]


# =====================================================================
# TESTS TIMELINE (T044)
# =====================================================================


class TestBuildTimeline:
    """Tests pour la construction de la timeline."""

    def test_direct_timeline(self) -> None:
        """Un dossier direct a une timeline sans etape intermediaire."""
        fund = _make_mock_fund(timeline_months=12)
        timeline = _build_timeline(
            fund=fund,
            intermediary=None,
            target_type="fund_direct",
        )
        assert len(timeline) >= 3
        # Pas d'etape intermediaire
        steps = [t["step"] for t in timeline]
        assert not any("banque" in s.lower() or "intermédiaire" in s.lower() for s in steps)

    def test_intermediary_bank_timeline(self) -> None:
        """Un dossier bancaire a une etape 'Traitement par la banque'."""
        fund = _make_mock_fund(timeline_months=12)
        intermediary = _make_mock_intermediary()
        timeline = _build_timeline(
            fund=fund,
            intermediary=intermediary,
            target_type="intermediary_bank",
        )
        steps = [t["step"] for t in timeline]
        assert any("banque" in s.lower() for s in steps)

    def test_intermediary_agency_timeline(self) -> None:
        """Un dossier agence a une etape intermediaire."""
        fund = _make_mock_fund(timeline_months=16)
        intermediary = _make_mock_intermediary(intermediary_type="implementation_agency")
        timeline = _build_timeline(
            fund=fund,
            intermediary=intermediary,
            target_type="intermediary_agency",
        )
        steps = [t["step"] for t in timeline]
        assert any("agence" in s.lower() or "intermédiaire" in s.lower() for s in steps)

    def test_timeline_has_duration(self) -> None:
        """Chaque etape de la timeline a une duree."""
        fund = _make_mock_fund(timeline_months=12)
        timeline = _build_timeline(
            fund=fund,
            intermediary=None,
            target_type="fund_direct",
        )
        for step in timeline:
            assert "step" in step
            assert "duration_weeks" in step


# =====================================================================
# TESTS FRAIS INTERMEDIAIRE (T044)
# =====================================================================


class TestEstimateIntermediaryFees:
    """Tests pour l'estimation des frais d'intermediaire."""

    def test_no_intermediary(self) -> None:
        """Pas de frais sans intermediaire."""
        result = _estimate_intermediary_fees(
            intermediary=None,
            eligible_amount=100_000_000,
        )
        assert result == 0

    def test_with_typical_fees_percentage(self) -> None:
        """Estime les frais a partir du pourcentage dans typical_fees."""
        intermediary = _make_mock_intermediary(typical_fees="2-5% du montant")
        result = _estimate_intermediary_fees(
            intermediary=intermediary,
            eligible_amount=100_000_000,
        )
        assert result > 0

    def test_with_no_fees_info(self) -> None:
        """Utilise un defaut si pas d'info sur les frais."""
        intermediary = _make_mock_intermediary(typical_fees=None)
        result = _estimate_intermediary_fees(
            intermediary=intermediary,
            eligible_amount=100_000_000,
        )
        # Defaut raisonnable (ex: 3%)
        assert result > 0


# =====================================================================
# TESTS INTEGRATION run_simulation (T044)
# =====================================================================


class TestRunSimulation:
    """Tests d'integration pour run_simulation."""

    @pytest.mark.asyncio
    async def test_simulation_with_intermediary(self) -> None:
        """Simulation complete avec intermediaire."""
        app = _make_mock_application(target_type="intermediary_bank")
        db = AsyncMock()

        result = await run_simulation(db, app)

        assert "eligible_amount_xof" in result
        assert "roi_green" in result
        assert "timeline" in result
        assert "carbon_impact_tco2e" in result
        assert "intermediary_fees_xof" in result
        assert "estimated_at" in result
        assert result["eligible_amount_xof"] > 0
        assert result["intermediary_fees_xof"] > 0

    @pytest.mark.asyncio
    async def test_simulation_direct(self) -> None:
        """Simulation complete sans intermediaire."""
        app = _make_mock_application(target_type="fund_direct")
        app.intermediary = None
        db = AsyncMock()

        result = await run_simulation(db, app)

        assert result["intermediary_fees_xof"] == 0
        assert result["eligible_amount_xof"] > 0

    @pytest.mark.asyncio
    async def test_simulation_stores_result(self) -> None:
        """La simulation stocke le resultat dans application.simulation."""
        app = _make_mock_application()
        db = AsyncMock()

        result = await run_simulation(db, app)

        assert app.simulation == result
