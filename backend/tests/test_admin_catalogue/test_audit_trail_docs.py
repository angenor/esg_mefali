"""Tests grep natif de la documentation `docs/CODEMAPS/audit-trail.md` (Story 10.12 AC7).

Valide la presence des 5 sections H2 exactes et l'inscription dans
`docs/CODEMAPS/index.md`. Pattern Python natif sans subprocess rg
(lecon 10.9).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_DOCS_DIR = Path(__file__).resolve().parents[3] / "docs" / "CODEMAPS"
_AUDIT_TRAIL_MD = _DOCS_DIR / "audit-trail.md"
_INDEX_MD = _DOCS_DIR / "index.md"


def test_codemap_audit_trail_exists():
    """Le fichier `docs/CODEMAPS/audit-trail.md` existe."""
    assert _AUDIT_TRAIL_MD.exists(), f"Fichier absent : {_AUDIT_TRAIL_MD}"


def test_codemap_audit_trail_has_5_sections_h2():
    """Les 5 sections H2 canoniques sont presentes (ordre preserve)."""
    text = _AUDIT_TRAIL_MD.read_text(encoding="utf-8")
    expected_headings = [
        "## 1. Pattern D6 audit immuable",
        "## 2. Écriture (producer)",
        "## 3. Consultation (consumer)",
        "## 4. Export CSV",
        "## 5. Pièges",
    ]
    for heading in expected_headings:
        assert heading in text, f"Heading manquant : {heading!r}"

    # Ordre preserve (chaque heading suivant apparait apres le precedent)
    positions = [text.find(h) for h in expected_headings]
    assert positions == sorted(positions), (
        f"Les H2 ne sont pas dans l'ordre attendu : positions={positions}"
    )


def test_codemap_audit_trail_has_mermaid_diagrams():
    """Au moins 2 diagrammes Mermaid `sequenceDiagram` (producer + consumer)."""
    text = _AUDIT_TRAIL_MD.read_text(encoding="utf-8")
    mermaid_blocks = re.findall(
        r"```mermaid\s*\n\s*sequenceDiagram", text
    )
    assert len(mermaid_blocks) >= 2, (
        f"Attendu >= 2 sequenceDiagram Mermaid, trouve : {len(mermaid_blocks)}"
    )


def test_codemap_audit_trail_has_extension_and_retention_sections():
    """Sections Extension et Rétention 5 ans presentes."""
    text = _AUDIT_TRAIL_MD.read_text(encoding="utf-8")
    assert "## Extension" in text
    assert "## Rétention 5 ans" in text


def test_codemap_index_lists_audit_trail():
    """`docs/CODEMAPS/index.md` contient la ligne audit-trail.md."""
    text = _INDEX_MD.read_text(encoding="utf-8")
    assert "[audit-trail.md](./audit-trail.md)" in text, (
        "index.md doit referencer audit-trail.md"
    )
