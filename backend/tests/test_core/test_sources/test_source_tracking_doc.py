"""Tests de structure de `docs/CODEMAPS/source-tracking.md` (Story 10.11, AC7).

Pattern identique Story 10.8+10.10 (ancrage structure CODEMAPS par doc grep).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
DOC_PATH = REPO_ROOT / "docs" / "CODEMAPS" / "source-tracking.md"
INDEX_PATH = REPO_ROOT / "docs" / "CODEMAPS" / "index.md"


@pytest.mark.unit
def test_codemap_has_5_sections() -> None:
    """Le doc doit contenir exactement 5 sections `## N. Title`."""

    content = DOC_PATH.read_text(encoding="utf-8")
    headings = re.findall(r"^## \d\. ", content, flags=re.MULTILINE)
    assert len(headings) == 5, (
        f"Attendu 5 sections, trouvé {len(headings)}"
    )


@pytest.mark.unit
def test_codemap_has_mermaid_sequence_diagram() -> None:
    """La section 2 doit inclure un bloc Mermaid `sequenceDiagram`."""

    content = DOC_PATH.read_text(encoding="utf-8")
    assert "```mermaid" in content, "Bloc ```mermaid manquant"
    assert "sequenceDiagram" in content, "Diagramme sequenceDiagram manquant"


@pytest.mark.unit
def test_codemap_lists_seven_status_values() -> None:
    """Le doc doit lister les 7 statuts finaux (AC4 + catégorisation)."""

    content = DOC_PATH.read_text(encoding="utf-8")
    for status in (
        "ok",
        "not_found",
        "timeout",
        "redirect_excess",
        "ssl_error",
        "server_error",
        "other_error",
    ):
        assert status in content, f"Statut manquant dans le doc : {status}"


@pytest.mark.unit
def test_index_references_source_tracking_page() -> None:
    """`index.md` hub doit référencer le nouveau doc."""

    content = INDEX_PATH.read_text(encoding="utf-8")
    assert "source-tracking.md" in content
    assert "NFR-SOURCE-TRACKING" in content
