"""Golden snapshots post-refactor (AC5 Story 10.8).

Compare les 7 prompts canoniques generes par les builders (build_system_prompt,
build_esg_prompt, ..., build_action_plan_prompt) avec les golden snapshots
captures AVANT le refactor CCC-9 (commit chore(10.8): freeze golden snapshots).

La comparaison utilise `_normalize_whitespace` qui tolere uniquement :
  - trailing whitespace par ligne
  - lignes vides consecutives multiples (collapse → 1)
  - whitespace initial/final global (strip)

Toute difference SEMANTIQUE (texte different, marqueur manquant, ordre change)
fera echouer le test et documentera une regression du refactor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

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


def _normalize_whitespace(text: str) -> str:
    """Normalise le whitespace pour tolerer :
    - trailing whitespace par ligne
    - blank lines consecutives multiples → 1 seule blank line
    - leading/trailing whitespace global (strip)
    """
    lines = [line.rstrip() for line in text.splitlines()]
    result: list[str] = []
    prev_blank = False
    for line in lines:
        if line == "":
            if not prev_blank:
                result.append(line)
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    return "\n".join(result).strip()


def _load_golden(name: str) -> str:
    path = GOLDEN_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


# Callable sans argument qui genere le prompt canonique de chaque module.
_MODULE_BUILDERS: dict[str, Callable[[], str]] = {
    "system": lambda: build_system_prompt(user_profile=CANONICAL_PROFILE),
    "esg_scoring": lambda: build_esg_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        document_context=CANONICAL_DOCUMENT_CONTEXT,
    ),
    "carbon": lambda: build_carbon_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        applicable_categories=CANONICAL_APPLICABLE_CATEGORIES,
    ),
    "financing": lambda: build_financing_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        rag_context=CANONICAL_RAG_CONTEXT,
    ),
    "application": lambda: build_application_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        application_context=CANONICAL_APPLICATION_CONTEXT,
    ),
    "credit": lambda: build_credit_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        scoring_context=CANONICAL_SCORING_CONTEXT,
    ),
    "action_plan": lambda: build_action_plan_prompt(
        company_context=CANONICAL_COMPANY_CONTEXT,
        esg_context=CANONICAL_ESG_CONTEXT,
        carbon_context=CANONICAL_CARBON_CONTEXT,
        financing_context=CANONICAL_FINANCING_CONTEXT,
        intermediaries_context=CANONICAL_INTERMEDIARIES_CONTEXT,
        timeframe=CANONICAL_TIMEFRAME,
    ),
}


@pytest.mark.parametrize("module", sorted(_MODULE_BUILDERS.keys()))
@pytest.mark.unit
def test_golden_snapshot_matches_post_refactor(module: str) -> None:
    """Pour chacun des 7 modules : prompt genere ≡ golden snapshot (AC5).

    Tolerance whitespace uniquement. Toute difference semantique = regression.
    """
    generated = _MODULE_BUILDERS[module]()
    golden = _load_golden(module)

    norm_generated = _normalize_whitespace(generated)
    norm_golden = _normalize_whitespace(golden)

    assert norm_generated == norm_golden, (
        f"Regression semantique detectee sur module '{module}'.\n"
        f"Golden chars: {len(norm_golden)}, generated chars: {len(norm_generated)}.\n"
        f"Pour investiguer : diff <(echo \"$GOLDEN\" | python _normalize) <(echo \"$GEN\" | python _normalize)."
    )


_EXPECTED_MARKERS: dict[str, tuple[str, ...]] = {
    "system": ("## STYLE DE COMMUNICATION", "## OUTIL GUIDAGE VISUEL"),
    "esg_scoring": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
        "## OUTIL GUIDAGE VISUEL",
    ),
    "carbon": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
        "## OUTIL GUIDAGE VISUEL",
    ),
    "financing": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
        "## OUTIL GUIDAGE VISUEL",
    ),
    "application": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
    ),
    "credit": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
        "## OUTIL GUIDAGE VISUEL",
    ),
    "action_plan": (
        "## STYLE DE COMMUNICATION",
        "## OUTIL INTERACTIF",
        "## OUTIL GUIDAGE VISUEL",
    ),
}


@pytest.mark.unit
def test_golden_files_meta_markers_present() -> None:
    """Meta-test : defense en profondeur contre un golden vide ou tronque."""
    for module, markers in _EXPECTED_MARKERS.items():
        content = _load_golden(module)
        for marker in markers:
            assert marker in content, (
                f"Golden '{module}.txt' ne contient pas le marqueur '{marker}' "
                f"— golden probablement vide ou tronque."
            )

    # Verifie explicitement que les modules non-concernes n'ont pas d'instruction
    # qu'ils ne devraient pas avoir (parite historique).
    application_content = _load_golden("application")
    assert "## OUTIL GUIDAGE VISUEL" not in application_content
    assert "trigger_guided_tour" not in application_content

    system_content = _load_golden("system")
    assert "## OUTIL INTERACTIF" not in system_content
