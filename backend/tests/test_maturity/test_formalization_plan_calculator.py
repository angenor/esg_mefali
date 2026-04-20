"""Tests pour FormalizationPlanCalculator stub + scan NFR66 country-data-driven (Story 10.3 AC7, AC8)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.modules.maturity.formalization_plan_calculator import (
    FormalizationPlanCalculator,
)

# NFR66 country-data-driven : toute lecture de requirements doit passer par
# `AdminMaturityRequirement.requirements_json` en base — zero string pays
# hardcode cote Python. Le test ci-dessous scan les fichiers sensibles pour
# detecter toute occurrence de noms de pays UEMOA/CEDEAO francophones.
_BANNED_COUNTRY_STRINGS = [
    "Sénégal",
    "Senegal",
    "Côte d'Ivoire",
    "Cote d'Ivoire",
    "Ivory Coast",
    "Mali",
    "Burkina Faso",
    "Niger",
    "Togo",
    "Bénin",
    "Benin",
    "Guinée",
    "Guinee",
    "Guinea",
]

_MATURITY_MODULE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "app"
    / "modules"
    / "maturity"
)


def test_country_data_driven_no_hardcoded_country_strings():
    """Test 15 — NFR66 : scan de TOUS les fichiers Python du module maturity.

    Toute occurrence de « Sénégal », « Côte d'Ivoire », etc. en string literal
    echoue le test. Le parametre `country` (variable) est autorise, les
    literals non. La lecture est faite via `read_text()` et la verification
    scan le fichier entier (le nom des pays dans une docstring est tout
    aussi interdit : Epic 12 Story 12.3 doit rester strictement data-driven).

    MEDIUM-10.3-1 (code review 2026-04-20) — le scan couvre desormais
    l'ensemble du module (8 fichiers) plutot que 2 : un contributeur Epic 12
    pourrait glisser un pays hardcode dans `schemas.py`, `enums.py`,
    `router.py` ou `events.py` sans que le test initial (limite a
    `service.py` + `formalization_plan_calculator.py`) ne le detecte.
    """
    targets = sorted(_MATURITY_MODULE_DIR.glob("*.py"))
    assert targets, (
        f"aucun fichier Python trouve dans {_MATURITY_MODULE_DIR} — "
        f"scan NFR66 vide, defense desactivee"
    )

    for target in targets:
        content = target.read_text(encoding="utf-8")
        for banned in _BANNED_COUNTRY_STRINGS:
            assert banned not in content, (
                f"{target.relative_to(_MATURITY_MODULE_DIR.parent.parent.parent)} "
                f"contient la chaine de pays interdite '{banned}' "
                f"(NFR66 country-data-driven). Les requirements doivent etre "
                f"lus depuis `AdminMaturityRequirement.requirements_json` "
                f"en base, jamais hardcodes en Python."
            )


@pytest.mark.asyncio
async def test_generate_raises_not_implemented(db_session):
    """Test 16 — FormalizationPlanCalculator.generate() leve NotImplementedError."""
    calc = FormalizationPlanCalculator()
    with pytest.raises(
        NotImplementedError, match=r"Story 10\.3 skeleton"
    ) as excinfo:
        await calc.generate(
            db_session,
            company_id=uuid.uuid4(),
            current_level_id=uuid.uuid4(),
            target_level_id=uuid.uuid4(),
            country="country-variable",
        )
    assert "Epic 12 story 12.3" in str(excinfo.value)
