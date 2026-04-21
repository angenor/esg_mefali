"""Test zero duplication STYLE/WIDGET/GUIDED_TOUR (AC4 Story 10.8 + patch HIGH-10.8-2).

Scan purement Python (pas de dependance a rg en PATH — plus portable en CI).

Deux scans :
  1. `test_no_duplicate_instruction_imports_in_business_modules` (AC4 original) :
     scope `backend/app/prompts/*.py`, exclut 4 fichiers legitimes.
  2. `test_no_duplicate_instruction_imports_anywhere_in_app` (HIGH-10.8-2) :
     scope `backend/app/**/*.py`, exclut les fichiers legitimes ET une liste
     d'exemptions DOCUMENTEES (dette tracee). Toute nouvelle duplication hors
     exemption fera echouer le test.

Toute mention des 3 constantes hors des fichiers autorises indique une
duplication residuelle non absorbee par CCC-9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROMPTS_DIR = BACKEND_ROOT / "app" / "prompts"
APP_DIR = BACKEND_ROOT / "app"

# 4 fichiers legitimes a exclure :
# - registry.py : nouveau, consomme les 3 constantes en import
# - system.py : exporte STYLE_INSTRUCTION, l'utilise localement (conditionnel)
# - widget.py : exporte WIDGET_INSTRUCTION
# - guided_tour.py : exporte GUIDED_TOUR_INSTRUCTION
ALLOWED_FILES = {"registry.py", "system.py", "widget.py", "guided_tour.py"}
ALLOWED_PATHS = {PROMPTS_DIR / name for name in ALLOWED_FILES}

# Exemptions DOCUMENTEES (dette ouverte — a justifier dans deferred-work.md).
# Vide depuis le patch HIGH-10.8-1 (2026-04-21) : build_system_prompt passe
# desormais par build_prompt(module="chat", exclude_names=...) et nodes.py
# n'injecte plus WIDGET_INSTRUCTION manuellement.
DOCUMENTED_DEBT_EXEMPTIONS: set[Path] = set()

FORBIDDEN_PATTERN = re.compile(
    r"STYLE_INSTRUCTION|WIDGET_INSTRUCTION|GUIDED_TOUR_INSTRUCTION"
)


def _scan_violations(py_file: Path) -> list[int]:
    """Retourne les numeros de ligne contenant les constantes interdites,
    en ignorant les lignes de commentaire (qui peuvent legitimement les
    mentionner sans causer de duplication reelle)."""
    matches: list[int] = []
    for lineno, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if FORBIDDEN_PATTERN.search(line):
            matches.append(lineno)
    return matches


@pytest.mark.unit
def test_no_duplicate_instruction_imports_in_business_modules() -> None:
    """Aucun module metier (6) ne doit importer ou concatener directement les
    3 constantes transverses — tout passe via le registre (AC4)."""
    offenders: dict[str, list[int]] = {}
    for py_file in PROMPTS_DIR.glob("*.py"):
        if py_file.name in ALLOWED_FILES:
            continue
        matches = _scan_violations(py_file)
        if matches:
            offenders[py_file.name] = matches

    assert not offenders, (
        f"Duplication residuelle : {offenders} importent STYLE/WIDGET/GUIDED_TOUR "
        f"alors qu'ils devraient passer par le registre (CCC-9)."
    )


@pytest.mark.unit
def test_no_duplicate_instruction_imports_anywhere_in_app() -> None:
    """HIGH-10.8-2 — scan elargi : aucun fichier hors ALLOWED_PATHS et hors
    DOCUMENTED_DEBT_EXEMPTIONS ne doit importer les 3 constantes transverses.

    La liste DOCUMENTED_DEBT_EXEMPTIONS doit rester vide ou se reduire au fil
    des patches — toute addition est une dette consciente a justifier dans
    deferred-work.md.
    """
    allowed = ALLOWED_PATHS | DOCUMENTED_DEBT_EXEMPTIONS
    offenders: dict[str, list[int]] = {}
    for py_file in APP_DIR.rglob("*.py"):
        if py_file in allowed:
            continue
        matches = _scan_violations(py_file)
        if matches:
            offenders[str(py_file.relative_to(APP_DIR))] = matches

    assert not offenders, (
        f"Duplication CCC-9 hors prompts/ : {offenders}. "
        f"Si intentionnel, ajouter le path dans DOCUMENTED_DEBT_EXEMPTIONS "
        f"avec entree correspondante dans deferred-work.md."
    )


@pytest.mark.unit
def test_documented_debt_exemptions_still_have_violations() -> None:
    """Anti-rot : chaque path dans DOCUMENTED_DEBT_EXEMPTIONS doit reellement
    contenir une violation. Sinon il est candidat au retrait — la dette est
    resolue, l'exemption est obsolete."""
    stale_exemptions: list[str] = []
    for exempt_path in DOCUMENTED_DEBT_EXEMPTIONS:
        if not exempt_path.exists():
            stale_exemptions.append(f"{exempt_path} (n'existe plus)")
            continue
        content = exempt_path.read_text(encoding="utf-8")
        if not FORBIDDEN_PATTERN.search(content):
            stale_exemptions.append(
                f"{exempt_path} (plus de violation — retirer de DOCUMENTED_DEBT_EXEMPTIONS)"
            )

    assert not stale_exemptions, (
        f"Exemptions obsoletes : {stale_exemptions}. "
        f"Retirer du set DOCUMENTED_DEBT_EXEMPTIONS (la dette est resolue)."
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
