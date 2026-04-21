"""Scans post-dev : unicite writer + no generic except (Story 10.12 AC8 / lecons 9.7+10.5).

Tests grep Python natif (pattern 10.9/10.11) — scan les fichiers sources sans
subprocess rg. Enforce les regles :
- Aucune `INSERT INTO admin_catalogue_audit_trail` en dehors de
  `service.record_audit_event` (anti-God NFR64 + NFR28 unicite writer).
- Aucun `except Exception` catch-all dans les nouveaux fichiers 10.12.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR = _BACKEND_ROOT / "app"
_STORY_1012_FILES = (
    _APP_DIR / "modules" / "admin_catalogue" / "audit_constants.py",
    _APP_DIR / "modules" / "admin_catalogue" / "router.py",
    _APP_DIR / "modules" / "admin_catalogue" / "service.py",
)


def test_no_raw_insert_into_admin_catalogue_audit_trail():
    """Scan : aucune `INSERT INTO admin_catalogue_audit_trail` en raw SQL.

    Le body `record_audit_event` utilise l'ORM (`db.add(entity)`), donc zero
    `INSERT INTO admin_catalogue_audit_trail` raw doit apparaitre dans
    `backend/app/`. Les tests tamper-proof (`test_audit_trail_tamper_proof.py`)
    sont explicitement exclus car ils font un INSERT raw de setup.
    """
    # Regex stricte : INSERT INTO + table (case-sensitive uppercase) sans
    # backticks / guillemets inverses (pour exclure les mentions dans les
    # docstrings/commentaires qui citent la regle).
    pattern = re.compile(r"INSERT\s+INTO\s+admin_catalogue_audit_trail")
    hits: list[tuple[Path, int, str]] = []
    for py_file in _APP_DIR.rglob("*.py"):
        try:
            for lineno, line in enumerate(
                py_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if pattern.search(line) and "`" not in line:
                    hits.append((py_file, lineno, line.strip()))
        except UnicodeDecodeError:
            continue

    assert hits == [], (
        "Hits `INSERT INTO admin_catalogue_audit_trail` raw trouves hors "
        f"`service.record_audit_event` (viole NFR64 / regle 10.5) : {hits}"
    )


def test_no_generic_except_exception_in_story_1012_files():
    """Scan : aucun `except Exception` catch-all dans les fichiers livres 10.12.

    Lecon 9.7 C1 — fail-fast explicite, pas d'avalement silencieux.
    Les `except ValueError` / `except ... as exc` qui remontent via
    `raise ... from exc` sont autorises et recommandes.
    """
    # Regex : `except Exception` en debut de ligne (whitespaces ok) suivi
    # d'un `:` ou ` as`. Exclu `except (Exception,)` explicite (rare mais
    # legitime pour un handler racine — n'arrive pas en Story 10.12).
    pattern = re.compile(r"^\s*except\s+Exception\b")
    hits: list[tuple[Path, int, str]] = []
    for py_file in _STORY_1012_FILES:
        for lineno, line in enumerate(
            py_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if pattern.match(line):
                hits.append((py_file, lineno, line.strip()))

    assert hits == [], (
        f"`except Exception` catch-all trouve dans fichiers Story 10.12 : {hits}"
    )
