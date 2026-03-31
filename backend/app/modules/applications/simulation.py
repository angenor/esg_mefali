"""Simulateur de financement pour les dossiers de candidature (US6)."""

import logging
import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import FundApplication

logger = logging.getLogger(__name__)

# Taux d'economies annuelles estimees (% du montant investi)
_SAVINGS_RATE = 0.15
# Frais intermediaire par defaut si pas d'info (%)
_DEFAULT_FEE_RATE = 0.03
# Impact carbone estime par MXOF investi (tCO2e)
_CARBON_IMPACT_PER_MXOF = 1.7
# Montant eligible par defaut si pas de min/max
_DEFAULT_ELIGIBLE_XOF = 50_000_000


def _estimate_eligible_amount(fund) -> int:
    """Estimer le montant eligible a partir des bornes du fonds."""
    min_amt = fund.min_amount_xof
    max_amt = fund.max_amount_xof

    if min_amt and max_amt:
        return (min_amt + max_amt) // 2
    if max_amt:
        return max_amt // 2
    if min_amt:
        return min_amt * 2
    return _DEFAULT_ELIGIBLE_XOF


def _estimate_roi_green(eligible_amount: int) -> dict:
    """Estimer le ROI vert (economies annuelles et payback)."""
    annual_savings = int(eligible_amount * _SAVINGS_RATE)
    payback_months = int(12 / _SAVINGS_RATE) if _SAVINGS_RATE > 0 else 0
    return {
        "annual_savings_xof": annual_savings,
        "payback_months": payback_months,
    }


def _build_timeline(
    fund,
    intermediary,
    target_type: str,
) -> list[dict[str, str]]:
    """Construire la timeline du parcours de financement."""
    timeline: list[dict[str, str]] = [
        {"step": "Préparation du dossier", "duration_weeks": "2-4"},
    ]

    if target_type == "intermediary_bank":
        timeline.append(
            {"step": "Traitement par la banque", "duration_weeks": "2-4"}
        )
    elif target_type in ("intermediary_agency", "intermediary_developer"):
        label = "agence" if target_type == "intermediary_agency" else "développeur"
        timeline.append(
            {"step": f"Instruction par l'intermédiaire ({label})", "duration_weeks": "3-6"}
        )

    timeline.append(
        {"step": "Soumission au fonds", "duration_weeks": "1-2"}
    )

    # Estimer la duree d'examen du fonds
    review_months = fund.typical_timeline_months or 6
    review_weeks_min = max(4, review_months * 4 // 2)
    review_weeks_max = review_months * 4
    timeline.append(
        {"step": "Examen par le fonds", "duration_weeks": f"{review_weeks_min}-{review_weeks_max}"}
    )

    return timeline


def _estimate_intermediary_fees(
    intermediary,
    eligible_amount: int,
) -> int:
    """Estimer les frais d'intermediaire."""
    if intermediary is None:
        return 0

    fee_rate = _DEFAULT_FEE_RATE

    # Tenter d'extraire un pourcentage depuis typical_fees
    if intermediary.typical_fees:
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*[-–à]\s*(\d+(?:[.,]\d+)?)\s*%", intermediary.typical_fees)
        if match:
            low = float(match.group(1).replace(",", "."))
            high = float(match.group(2).replace(",", "."))
            fee_rate = (low + high) / 200  # moyenne en decimal
        else:
            single_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", intermediary.typical_fees)
            if single_match:
                fee_rate = float(single_match.group(1).replace(",", ".")) / 100

    return int(eligible_amount * fee_rate)


async def run_simulation(
    db: AsyncSession,
    application: FundApplication,
) -> dict:
    """Executer la simulation de financement pour un dossier."""
    fund = application.fund
    intermediary = application.intermediary
    target_type = (
        application.target_type.value
        if hasattr(application.target_type, "value")
        else application.target_type
    )

    # Estimations
    eligible_amount = _estimate_eligible_amount(fund)
    roi_green = _estimate_roi_green(eligible_amount)
    timeline = _build_timeline(fund, intermediary, target_type)
    fees = _estimate_intermediary_fees(intermediary, eligible_amount)
    carbon_impact = round(eligible_amount / 1_000_000 * _CARBON_IMPACT_PER_MXOF, 1)

    result = {
        "eligible_amount_xof": eligible_amount,
        "roi_green": roi_green,
        "timeline": timeline,
        "carbon_impact_tco2e": carbon_impact,
        "intermediary_fees_xof": fees,
        "estimated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Stocker le resultat dans le dossier
    application.simulation = result
    application.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return result
