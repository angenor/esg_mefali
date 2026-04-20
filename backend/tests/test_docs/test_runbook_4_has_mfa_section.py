"""Gate CI documentaire (Story 10.7 AC7).

Vérifie que `docs/runbooks/README.md` conserve les sections critiques sur :
    - Versioning
    - MFA Delete
    - Object Lock

Prévient la suppression accidentelle lors d'une future PR refactor docs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

RUNBOOK_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "runbooks" / "README.md"


def test_runbook_exists():
    """Sanity : le runbook doit exister."""
    assert RUNBOOK_PATH.is_file(), f"Runbook missing at {RUNBOOK_PATH}"


@pytest.mark.parametrize(
    "required_phrase",
    [
        "MFA Delete",       # §6.2 procedure root-only
        "Object Lock",      # §6.3 differe Phase Growth
        "Versioning",       # §6.1 prerequis CRR
        "CRR",              # AC6 - replication cross-region
        "ANONYMIZATION_SALT",  # AC5 - salt deterministe
    ],
)
def test_runbook_contains_required_sections(required_phrase: str):
    """Gate CI : toute suppression d'une de ces chaines critiques fail le build."""
    content = RUNBOOK_PATH.read_text(encoding="utf-8")
    assert required_phrase in content, (
        f"Runbook 4 missing required phrase '{required_phrase}' — "
        f"check docs/runbooks/README.md §4 or §6 Propriétés bucket"
    )
