"""Script helper de capture des golden snapshots (Story 10.8 Task 2).

Execute manuellement UNE SEULE FOIS avant le refactor pour figer les prompts
canoniques dans backend/tests/test_prompts/golden/*.txt. Apres le refactor
(Task 7), les snapshots sont compares pour garantir zero regression semantique.

Usage:
    cd backend && python -m tests.test_prompts._capture_golden

NE PAS re-executer apres le refactor : les snapshots doivent rester identiques.
"""

from __future__ import annotations

from pathlib import Path

from app.prompts.action_plan import build_action_plan_prompt
from app.prompts.application import build_application_prompt
from app.prompts.carbon import build_carbon_prompt
from app.prompts.credit import build_credit_prompt
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.financing import build_financing_prompt
from app.prompts.system import build_system_prompt
from tests.test_prompts._canonical_profile import (
    CANONICAL_APPLICABLE_CATEGORIES,
    CANONICAL_APPLICATION_CONTEXT,
    CANONICAL_CARBON_CONTEXT,
    CANONICAL_COMPANY_CONTEXT,
    CANONICAL_DOCUMENT_CONTEXT,
    CANONICAL_ESG_CONTEXT,
    CANONICAL_FINANCING_CONTEXT,
    CANONICAL_INTERMEDIARIES_CONTEXT,
    CANONICAL_PROFILE,
    CANONICAL_RAG_CONTEXT,
    CANONICAL_SCORING_CONTEXT,
    CANONICAL_TIMEFRAME,
)


GOLDEN_DIR: Path = Path(__file__).parent / "golden"


def capture_all() -> dict[str, str]:
    """Retourne un mapping module_name -> prompt genere."""
    snapshots: dict[str, str] = {
        "system": build_system_prompt(user_profile=CANONICAL_PROFILE),
        "esg_scoring": build_esg_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            document_context=CANONICAL_DOCUMENT_CONTEXT,
        ),
        "carbon": build_carbon_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            applicable_categories=CANONICAL_APPLICABLE_CATEGORIES,
        ),
        "financing": build_financing_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            rag_context=CANONICAL_RAG_CONTEXT,
        ),
        "application": build_application_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            application_context=CANONICAL_APPLICATION_CONTEXT,
        ),
        "credit": build_credit_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            scoring_context=CANONICAL_SCORING_CONTEXT,
        ),
        "action_plan": build_action_plan_prompt(
            company_context=CANONICAL_COMPANY_CONTEXT,
            esg_context=CANONICAL_ESG_CONTEXT,
            carbon_context=CANONICAL_CARBON_CONTEXT,
            financing_context=CANONICAL_FINANCING_CONTEXT,
            intermediaries_context=CANONICAL_INTERMEDIARIES_CONTEXT,
            timeframe=CANONICAL_TIMEFRAME,
        ),
    }
    return snapshots


def write_all(force: bool = False) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    if not force and any(GOLDEN_DIR.glob("*.txt")):
        raise SystemExit(
            "Golden snapshots existent deja. Utiliser --force pour ecraser, "
            "ou les supprimer manuellement avec un commit explicite documentant "
            "le drift semantique attendu."
        )
    for name, content in capture_all().items():
        (GOLDEN_DIR / f"{name}.txt").write_text(content, encoding="utf-8")
        print(f"[ok] wrote {name}.txt ({len(content)} chars)")


if __name__ == "__main__":
    import sys
    write_all(force="--force" in sys.argv)
