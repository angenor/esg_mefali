"""Seed l'utilisateur Aminata pour les tests E2E live (story 8.3).

Cree :
- Un User `aminata1@gmail.com` (mot de passe `Aminata2026!`).
- Son CompanyProfile (Recyclage Plus Senegal, secteur recyclage, Senegal).
- Une ESGAssessment `completed` avec 30 criteres notes (score global ~70/100,
  >= 3 forces, >= 3 recommandations) afin que la page `/esg/results` affiche
  les 3 sections cibles du tour `show_esg_results`.

Idempotent : si l'email existe deja, le script affiche un message et exit 0.

Usage :
    cd backend
    source venv/bin/activate
    python scripts/seed_aminata.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Permet d'executer le script depuis n'importe ou : on ajoute le dossier
# `backend/` (parent de `scripts/`) au sys.path pour resoudre `app.*`.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.company import CompanyProfile, SectorEnum  # noqa: E402
from app.models.esg import ESGAssessment, ESGStatusEnum  # noqa: E402
from app.models.user import User  # noqa: E402
from app.modules.esg.criteria import ALL_CRITERIA  # noqa: E402
from app.modules.esg.service import (  # noqa: E402
    compute_benchmark_comparison,
    compute_overall_score,
    generate_recommendations,
    generate_strengths_gaps,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_aminata")

AMINATA_EMAIL = "aminata1@gmail.com"
AMINATA_PASSWORD = "Aminata2026!"  # noqa: S105 — compte de test local, jamais en prod
AMINATA_FULL_NAME = "Aminata Diop"
AMINATA_COMPANY = "Recyclage Plus Senegal"
AMINATA_COUNTRY = "SN"
AMINATA_SECTOR = SectorEnum.recyclage


# Profil de scoring : melange de scores hauts (>=7 -> forces),
# moyens (5-6 -> ni force ni gap) et bas (<=4 -> recommandations).
# Cible : score global ~ 65-72/100 sur secteur recyclage.
_SCORE_PROFILE: dict[str, int] = {
    # Environnement (E1-E10) — secteur recyclage : valeurs hautes attendues
    "E1": 9, "E2": 8, "E3": 7, "E4": 8, "E5": 7,
    "E6": 6, "E7": 7, "E8": 4, "E9": 5, "E10": 3,
    # Social (S1-S10)
    "S1": 8, "S2": 7, "S3": 7, "S4": 6, "S5": 8,
    "S6": 5, "S7": 6, "S8": 4, "S9": 7, "S10": 5,
    # Gouvernance (G1-G10)
    "G1": 7, "G2": 8, "G3": 5, "G4": 6, "G5": 4,
    "G6": 3, "G7": 5, "G8": 7, "G9": 6, "G10": 5,
}


def _build_criteria_scores() -> dict[str, dict[str, Any]]:
    """Construit le dict criteria_scores pour les 30 criteres."""
    scores: dict[str, dict[str, Any]] = {}
    for criterion in ALL_CRITERIA:
        score = _SCORE_PROFILE.get(criterion.code, 6)
        scores[criterion.code] = {
            "score": score,
            "justification": (
                f"[Seed Aminata] {criterion.label} — pratiques mises en place "
                f"dans le cadre des activites de recyclage."
            ),
            "sources": [],
        }
    return scores


async def _user_exists(session: AsyncSession, email: str) -> bool:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none() is not None


async def _seed(session: AsyncSession) -> int:
    if await _user_exists(session, AMINATA_EMAIL):
        logger.info("User Aminata deja seed (%s), skipping.", AMINATA_EMAIL)
        return 0

    # 1) Utilisateur
    user = User(
        email=AMINATA_EMAIL,
        hashed_password=hash_password(AMINATA_PASSWORD),
        full_name=AMINATA_FULL_NAME,
        company_name=AMINATA_COMPANY,
    )
    session.add(user)
    await session.flush()
    logger.info("User cree : %s (id=%s)", user.email, user.id)

    # 2) Profil entreprise
    profile = CompanyProfile(
        user_id=user.id,
        company_name=AMINATA_COMPANY,
        sector=AMINATA_SECTOR,
        sub_sector="recyclage plastique et metaux",
        employee_count=22,
        annual_revenue_xof=120_000_000,
        year_founded=2018,
        city="Dakar",
        country=AMINATA_COUNTRY,
        has_waste_management=True,
        has_energy_policy=True,
        has_gender_policy=True,
        has_training_program=True,
        has_financial_transparency=False,
        governance_structure="SARL — gerance familiale + 1 administrateur externe",
        environmental_practices=(
            "Collecte et tri de dechets plastiques + metaux ; partenariats avec "
            "10 ecoles ; valorisation 80 t/an."
        ),
        social_practices=(
            "Equipe paritaire ; formation hebdomadaire HSE ; mutuelle sante."
        ),
        notes="Seed E2E story 8.3 — parcours Aminata.",
    )
    session.add(profile)
    await session.flush()
    logger.info("CompanyProfile cree : %s (id=%s)", profile.company_name, profile.id)

    # 3) Evaluation ESG completed
    criteria_scores = _build_criteria_scores()
    sector_str = AMINATA_SECTOR.value
    scores = compute_overall_score(criteria_scores, sector_str)
    strengths, gaps = generate_strengths_gaps(criteria_scores)
    recommendations = generate_recommendations(criteria_scores)
    benchmark = compute_benchmark_comparison(sector_str, scores)

    assessment = ESGAssessment(
        user_id=user.id,
        sector=sector_str,
        status=ESGStatusEnum.completed,
        overall_score=scores["overall_score"],
        environment_score=scores["environment_score"],
        social_score=scores["social_score"],
        governance_score=scores["governance_score"],
        assessment_data={
            "criteria_scores": criteria_scores,
            "pillar_details": {
                "environment": {
                    "raw_score": scores["environment_score"],
                    "weighted_score": scores["environment_score"],
                    "weights_applied": {},
                },
                "social": {
                    "raw_score": scores["social_score"],
                    "weighted_score": scores["social_score"],
                    "weights_applied": {},
                },
                "governance": {
                    "raw_score": scores["governance_score"],
                    "weighted_score": scores["governance_score"],
                    "weights_applied": {},
                },
            },
        },
        strengths=strengths,
        gaps=gaps,
        recommendations=recommendations,
        sector_benchmark=benchmark,
        evaluated_criteria=[c.code for c in ALL_CRITERIA],
        current_pillar=None,
    )
    session.add(assessment)
    await session.flush()

    logger.info(
        "ESGAssessment creee : id=%s, overall=%s, strengths=%d, "
        "recommendations=%d",
        assessment.id,
        assessment.overall_score,
        len(strengths),
        len(recommendations),
    )

    # Garde-fous metier exiges par AC1 :
    if assessment.overall_score is None or assessment.overall_score < 50:
        logger.error(
            "Score global %s < 50 — AC1 viole. Ajuster _SCORE_PROFILE.",
            assessment.overall_score,
        )
        return 1
    if len(strengths) < 3:
        logger.error("Strengths insuffisants (%d < 3) — AC1 viole.", len(strengths))
        return 1
    if len(recommendations) < 3:
        logger.error(
            "Recommendations insuffisantes (%d < 3) — AC1 viole.", len(recommendations)
        )
        return 1

    return 0


async def main() -> int:
    async with async_session_factory() as session:
        try:
            code = await _seed(session)
            if code == 0:
                await session.commit()
            else:
                await session.rollback()
            return code
        except Exception:
            await session.rollback()
            logger.exception("Erreur pendant le seed.")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
