"""Tests du seed Annexe F (Story 10.11, AC6 + AC8).

Couvre :
    - Unicité des URLs (pattern CCC-9 Story 10.8).
    - Nombre minimum de sources (≥ 22).
    - Source unique de vérité (grep anti-duplication).
    - Migration 030 chaînée sur la bonne `down_revision`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from app.core.sources.annexe_f_seed import (
    ANNEXE_F_SOURCES,
    _validate_unique_urls,
)
from app.core.sources.types import SourceSeed

REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.unit
def test_seed_no_duplicate_urls() -> None:
    """Aucune URL ne doit apparaître deux fois (fail-fast import-time)."""

    urls = [seed.url for seed in ANNEXE_F_SOURCES]
    assert len(urls) == len(set(urls)), "URLs dupliquées dans ANNEXE_F_SOURCES"


@pytest.mark.unit
def test_seed_validation_raises_on_duplicate() -> None:
    """Le helper lève ValueError dès qu'une URL est dupliquée."""

    duplicates = (
        SourceSeed(url="https://a.test/x", source_type="web", description="a"),
        SourceSeed(url="https://a.test/x", source_type="web", description="b"),
    )
    with pytest.raises(ValueError, match="duplicate URL"):
        _validate_unique_urls(duplicates)


@pytest.mark.unit
def test_seed_min_22_entries() -> None:
    """L'Annexe F PRD exige ≥ 22 sources seedées en Phase 0."""

    assert len(ANNEXE_F_SOURCES) >= 22, (
        f"Annexe F exige ≥ 22 sources, trouvé {len(ANNEXE_F_SOURCES)}"
    )


@pytest.mark.unit
def test_seed_all_source_types_valid() -> None:
    """Chaque entrée doit respecter l'enum `source_type_enum` (BDD)."""

    allowed = {"pdf", "web", "regulation", "peer_reviewed"}
    for seed in ANNEXE_F_SOURCES:
        assert seed.source_type in allowed, (
            f"source_type invalide : {seed.source_type}"
        )


@pytest.mark.unit
def test_seed_no_legacy_sentinel_url() -> None:
    """Les sentinelles `legacy://` sont exclues du seed (exclusion scan)."""

    for seed in ANNEXE_F_SOURCES:
        assert not seed.url.startswith("legacy://"), (
            f"Le seed Annexe F ne doit pas contenir de sentinelle legacy:// "
            f"(trouvé {seed.url})"
        )


@pytest.mark.unit
def test_seed_single_source_of_truth_no_duplication() -> None:
    """Chaque URL Annexe F n'apparaît qu'à un seul endroit du code.

    Règle 10.5 : `ANNEXE_F_SOURCES` est l'unique source. La migration 030
    l'importe sans dupliquer les littéraux.
    """

    # On vérifie sur une URL suffisamment spécifique au seed Annexe F.
    needle = "greenclimate.fund/projects"
    search_dirs = [
        REPO_ROOT / "backend" / "app",
        REPO_ROOT / "backend" / "alembic",
        REPO_ROOT / "scripts",
    ]
    hits: list[Path] = []
    for base in search_dirs:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                if needle in path.read_text(encoding="utf-8"):
                    hits.append(path)
            except OSError:
                continue

    assert len(hits) == 1, (
        f"URL {needle!r} doit apparaître dans exactement 1 fichier "
        f"(annexe_f_seed.py) ; trouvé {len(hits)} : {hits}"
    )
    assert hits[0].name == "annexe_f_seed.py"


@pytest.mark.unit
def test_migration_030_down_revision_is_029() -> None:
    """La migration 030 chaîne sur `029_outbox_next_retry_at` (Story 10.10)."""

    migration_path = (
        REPO_ROOT / "backend" / "alembic" / "versions"
        / "030_seed_sources_annexe_f.py"
    )
    content = migration_path.read_text(encoding="utf-8")
    match = re.search(r'^down_revision\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "down_revision manquante dans la migration 030"
    assert match.group(1) == "029_outbox_next_retry_at", (
        f"Chaîne migration cassée : attendu 029_outbox_next_retry_at, "
        f"trouvé {match.group(1)}"
    )
