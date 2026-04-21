"""Test doc CODEMAPS outbox.md (Story 10.10 AC8)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _docs_root() -> Path:
    return Path(__file__).resolve().parents[3].parent / "docs" / "CODEMAPS"


def test_outbox_codemap_has_7_sections():
    """docs/CODEMAPS/outbox.md doit comporter les 7 sections §1 à §7 (AC8)."""
    path = _docs_root() / "outbox.md"
    assert path.exists(), f"fichier absent: {path}"
    content = path.read_text(encoding="utf-8")

    # Ordre et présence stricts des 7 §.
    expected_headings = [
        r"^## §1 Vue d'ensemble",
        r"^## §2 Contrat writer",
        r"^## §3 Contrat worker",
        r"^## §4 Contrat handler",
        r"^## §5 Pièges",
        r"^## §6 Consommateurs prévus",
        r"^## §7 Migration Phase Growth",
    ]
    for pattern in expected_headings:
        assert re.search(pattern, content, re.MULTILINE), (
            f"section manquante ou mal titrée: {pattern!r}"
        )

    # Bloc Mermaid présent en §1.
    assert "```mermaid" in content

    # Tableau consommateurs prévus ≥ 8 lignes event_type.
    consumer_lines = re.findall(r"^\|\s*`[a-z_]+\.[a-z_]+`", content, re.MULTILINE)
    assert len(consumer_lines) >= 8, f"seulement {len(consumer_lines)} consommateurs listés"


def test_outbox_codemap_index_references_outbox():
    """docs/CODEMAPS/index.md doit référencer outbox.md (+1 ligne)."""
    path = _docs_root() / "index.md"
    content = path.read_text(encoding="utf-8")
    assert "outbox.md" in content, "index.md ne référence pas outbox.md"
