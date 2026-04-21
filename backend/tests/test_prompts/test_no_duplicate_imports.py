"""Test zero duplication STYLE/WIDGET/GUIDED_TOUR dans les modules metier (AC4 Story 10.8).

Scan purement Python (pas de dependance a rg en PATH — plus portable en CI)
sur backend/app/prompts/ en excluant les 4 fichiers legitimes (registry.py,
system.py, widget.py, guided_tour.py). Toute mention des 3 constantes dans les
6 autres modules (esg_scoring, carbon, financing, application, credit,
action_plan) indique une duplication residuelle non absorbee par CCC-9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROMPTS_DIR = BACKEND_ROOT / "app" / "prompts"

# 4 fichiers legitimes a exclure :
# - registry.py : nouveau, consomme les 3 constantes en import
# - system.py : exporte STYLE_INSTRUCTION, l'utilise localement (conditionnel)
# - widget.py : exporte WIDGET_INSTRUCTION
# - guided_tour.py : exporte GUIDED_TOUR_INSTRUCTION
ALLOWED_FILES = {"registry.py", "system.py", "widget.py", "guided_tour.py"}

FORBIDDEN_PATTERN = re.compile(
    r"STYLE_INSTRUCTION|WIDGET_INSTRUCTION|GUIDED_TOUR_INSTRUCTION"
)


@pytest.mark.unit
def test_no_duplicate_instruction_imports_in_business_modules() -> None:
    """Aucun module metier (6) ne doit importer ou concatener directement les
    3 constantes transverses — tout passe via le registre (AC4)."""
    offenders: dict[str, list[int]] = {}
    for py_file in PROMPTS_DIR.glob("*.py"):
        if py_file.name in ALLOWED_FILES:
            continue
        content = py_file.read_text(encoding="utf-8")
        matches: list[int] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            if FORBIDDEN_PATTERN.search(line):
                matches.append(lineno)
        if matches:
            offenders[py_file.name] = matches

    assert not offenders, (
        f"Duplication residuelle : {offenders} importent STYLE/WIDGET/GUIDED_TOUR "
        f"alors qu'ils devraient passer par le registre (CCC-9)."
    )


@pytest.mark.unit
def test_allowed_files_still_export_constants() -> None:
    """Les 3 constantes restent exportees depuis leurs fichiers d'origine
    pour retro-compatibilite des tests existants (test_guided_tour_instruction.py, etc.)."""
    # Import direct = verification que les constantes existent toujours
    from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION
    from app.prompts.system import STYLE_INSTRUCTION
    from app.prompts.widget import WIDGET_INSTRUCTION

    assert len(STYLE_INSTRUCTION) > 0
    assert len(WIDGET_INSTRUCTION) > 0
    assert len(GUIDED_TOUR_INSTRUCTION) > 0
    assert "STYLE DE COMMUNICATION" in STYLE_INSTRUCTION
    assert "OUTIL INTERACTIF" in WIDGET_INSTRUCTION
    assert "OUTIL GUIDAGE VISUEL" in GUIDED_TOUR_INSTRUCTION
