"""AC9 Story 10.1 — documentation docs/CODEMAPS/data-model-extension.md."""
from __future__ import annotations

from pathlib import Path


DOC_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "CODEMAPS"
    / "data-model-extension.md"
)


def test_data_model_extension_doc_exists():
    """AC9 — le fichier docs/CODEMAPS/data-model-extension.md existe."""
    assert DOC_PATH.is_file(), f"Documentation manquante : {DOC_PATH}"


def test_doc_contains_mermaid_diagram():
    """AC9 — diagramme Mermaid erDiagram présent."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "```mermaid" in content, "aucun bloc Mermaid"
    assert "erDiagram" in content, "pas de erDiagram"


def test_doc_lists_all_new_tables():
    """AC9 — toutes les nouvelles tables 020-027 sont citées."""
    content = DOC_PATH.read_text(encoding="utf-8")
    expected = [
        "companies", "projects", "project_memberships",
        "admin_maturity_levels", "formalization_plans",
        "facts", "criteria", "referential_verdicts",
        "document_templates", "reusable_sections",
        "admin_access_audit", "sources",
        "admin_catalogue_audit_trail",
        "domain_events", "prefill_drafts",
    ]
    missing = [t for t in expected if t not in content]
    assert not missing, f"tables non documentées : {missing}"


def test_doc_mentions_architectural_decisions():
    """AC9 CQ-8 — liens vers décisions architecturales D1/D3/D4/D5/D6/D7/D11."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for marker in ("D1", "D3", "D4", "D5", "D6", "D7", "D11"):
        assert marker in content, f"Décision {marker} non mentionnée"


def test_doc_mentions_migration_chain():
    """AC9 — chaîne 020→027 décrite."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for migration in ("020", "021", "022", "023", "024", "025", "026", "027"):
        assert migration in content, f"migration {migration} non mentionnée"
