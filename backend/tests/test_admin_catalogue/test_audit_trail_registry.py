"""Tests du registre CCC-9 `audit_constants` (Story 10.12 AC2).

Pattern byte-identique 10.8 `INSTRUCTION_REGISTRY`, 10.10 `HandlerEntry`,
10.11 `ANNEXE_F_SOURCES` : tuple frozen + validation import-time.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.modules.admin_catalogue import audit_constants
from app.modules.admin_catalogue.audit_constants import (
    ACTION_TYPES,
    ENTITY_TYPES,
    EXPORT_ROW_HARD_CAP,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MAX,
    RATE_LIMIT_AUDIT_EXPORT,
    RATE_LIMIT_AUDIT_TRAIL,
    WORKFLOW_LEVELS,
)


def test_action_types_is_frozen_tuple() -> None:
    """`ACTION_TYPES` doit etre un `tuple[str, ...]` immutable (CCC-9)."""
    assert isinstance(ACTION_TYPES, tuple)
    with pytest.raises(TypeError):
        ACTION_TYPES[0] = "hacked"  # type: ignore[index]


def test_action_types_matches_db_enum_source_of_truth() -> None:
    """`ACTION_TYPES` Python == enum DB `catalogue_action_enum` migration 026.

    Si un developpeur ajoute une valeur cote DB sans mettre a jour le tuple
    Python (ou inversement), le test doit echouer immediatement. Le parser
    migration utilise la meme regex que `_validate_registry_matches_db_enum`.
    """
    migration_path = (
        Path(audit_constants.__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "026_create_admin_catalogue_audit_trail.py"
    )
    text = migration_path.read_text(encoding="utf-8")
    db_values = audit_constants._parse_enum_values(text, "catalogue_action_enum")
    assert set(ACTION_TYPES) == db_values


def test_workflow_levels_matches_db_enum() -> None:
    """`WORKFLOW_LEVELS` == enum DB `workflow_level_enum` migration 026."""
    migration_path = (
        Path(audit_constants.__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "026_create_admin_catalogue_audit_trail.py"
    )
    text = migration_path.read_text(encoding="utf-8")
    db_values = audit_constants._parse_enum_values(text, "workflow_level_enum")
    assert set(WORKFLOW_LEVELS) == db_values


def test_entity_types_non_empty_tuple_minimum_six() -> None:
    """`ENTITY_TYPES` doit couvrir les 6 entites catalogue MVP minimum.

    fund, intermediary, referential, criterion, pack, derivation_rule.
    Extensible sans migration DB (colonne `entity_type` VARCHAR libre).
    """
    assert isinstance(ENTITY_TYPES, tuple)
    assert len(ENTITY_TYPES) >= 6
    for value in ENTITY_TYPES:
        assert isinstance(value, str)
        assert value == value.lower()


def test_pagination_and_export_constants_sane() -> None:
    """Bornes pagination + export conformes a la spec AC2/AC3."""
    assert PAGE_SIZE_DEFAULT == 50
    assert PAGE_SIZE_MAX == 200
    assert PAGE_SIZE_DEFAULT <= PAGE_SIZE_MAX
    assert EXPORT_ROW_HARD_CAP == 50_000


def test_rate_limit_strings_parse_slowapi_format() -> None:
    """Les rate limits suivent le format SlowAPI `N/period` (Story 9.1)."""
    assert re.match(r"^\d+/(second|minute|hour|day)$", RATE_LIMIT_AUDIT_TRAIL)
    assert re.match(r"^\d+/(second|minute|hour|day)$", RATE_LIMIT_AUDIT_EXPORT)
    assert RATE_LIMIT_AUDIT_TRAIL == "60/minute"
    assert RATE_LIMIT_AUDIT_EXPORT == "10/hour"


def test_validate_registry_import_time_has_run() -> None:
    """L'appel `_validate_registry_matches_db_enum()` a l'import a reussi.

    Si l'import du module a echoue (desynchro Python/DB), le test fixture
    aurait leve avant meme ce test. On valide qu'un appel explicite re-run
    reste vert (idempotent).
    """
    audit_constants._validate_registry_matches_db_enum()  # ne leve pas


def test_validate_registry_fails_when_enum_missing(tmp_path, monkeypatch) -> None:
    """Si la migration 026 ne contient plus `catalogue_action_enum`, RuntimeError.

    Pointe `_MIGRATION_PATH` vers un faux fichier ne contenant pas l'enum
    attendu et verifie que `RuntimeError` est leve (pas `AssertionError` —
    robuste au mode `python -O`).
    """
    fake_migration = tmp_path / "fake_026.py"
    fake_migration.write_text("# migration sans enum\n", encoding="utf-8")
    monkeypatch.setattr(audit_constants, "_MIGRATION_PATH", fake_migration)
    with pytest.raises(RuntimeError):
        audit_constants._validate_registry_matches_db_enum()
