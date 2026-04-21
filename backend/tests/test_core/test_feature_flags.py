"""Tests pour les feature flags (Story 10.2 AC4, AC8 + Story 10.9 AC1-AC6)."""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.feature_flags import (
    check_project_model_enabled,
    is_project_model_enabled,
)


def test_is_project_model_enabled_defaults_false(monkeypatch):
    """Test 10 — sans env var -> False (défaut MVP sûr)."""
    monkeypatch.delenv("ENABLE_PROJECT_MODEL", raising=False)
    assert is_project_model_enabled() is False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("YES", True),
        ("Yes", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("", False),
        ("no", False),
        ("disabled", False),
        ("2", False),
        ("random", False),
    ],
)
def test_is_project_model_enabled_truthy_values(monkeypatch, value, expected):
    """Test 11 — valeurs truthy/falsy case-insensitive (table-driven)."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", value)
    assert is_project_model_enabled() is expected


# --- Story 10.9 AC2 : champ Settings Pydantic informationnel ---


@pytest.mark.unit
def test_settings_declares_enable_project_model_field():
    """Story 10.9 AC2 — le champ est déclaré avec default=False."""
    from app.core.config import Settings

    assert "enable_project_model" in Settings.model_fields
    field = Settings.model_fields["enable_project_model"]
    assert field.default is False
    assert field.annotation is bool


@pytest.mark.unit
def test_settings_boot_value_matches_env_at_init(monkeypatch):
    """Story 10.9 AC2 — fresh `Settings()` honore ENABLE_PROJECT_MODEL au boot.

    Le champ informationnel reflète bien l'env au moment de l'instanciation.
    NB : le runtime applicatif n'utilise PAS ce champ (Q1 tranché, cf. test
    dédié `test_no_applicative_caller_reads_settings_enable_project_model`).
    """
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")

    from app.core.config import Settings

    assert Settings().enable_project_model is True

    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "false")
    assert Settings().enable_project_model is False


@pytest.mark.unit
def test_no_applicative_caller_reads_settings_enable_project_model():
    """Story 10.9 Q1 — aucun code applicatif ne lit `settings.enable_project_model`.

    Le runtime passe toujours par `is_project_model_enabled()` qui lit
    `os.environ` dynamiquement. Les tests peuvent lire le champ, mais pas
    le code sous `backend/app/`.
    """
    backend_app = Path(__file__).resolve().parents[2] / "app"
    assert backend_app.is_dir(), f"backend/app/ introuvable: {backend_app}"

    pattern = re.compile(r"settings\.enable_project_model")
    hits: list[str] = []
    for py_file in backend_app.rglob("*.py"):
        for line_no, line in enumerate(
            py_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if pattern.search(line):
                hits.append(f"{py_file}:{line_no}: {line.strip()}")

    assert not hits, (
        f"Aucun caller applicatif ne doit lire settings.enable_project_model "
        f"(Q1 Story 10.9). Hits trouvés :\n" + "\n".join(hits)
    )


# --- Story 10.9 AC4 : absence librairie externe (Clarification 5) ---


@pytest.mark.unit
def test_no_external_feature_flag_library_installed():
    """Story 10.9 AC4 — Clarification 5 : aucune lib externe feature-flag.

    Scanne `importlib.metadata.distributions()` (API stdlib réelle, pas de
    mock de `pip list`). Défense en profondeur contre `pip install`
    opportuniste qui dériverait du wrapper simple vers un SDK lourd.
    """
    forbidden = frozenset(
        {
            "flipper-client",
            "flipper",
            "unleash-client",
            "unleash",
            "launchdarkly-server-sdk",
            "launchdarkly-api",
            "gitlab-feature-flag",
            "configcat-client",
        }
    )
    installed = set()
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if name:
            installed.add(name.lower())

    leaked = installed & forbidden
    assert not leaked, (
        f"Clarification 5 (Story 10.1) violée : librairies externes "
        f"feature-flag installées : {sorted(leaked)}. Utiliser le helper "
        f"`is_project_model_enabled()` simple à la place."
    )


# --- Story 10.9 AC5 : marker cleanup Story 20.1 ---


@pytest.mark.unit
def test_feature_flags_has_cleanup_marker():
    """Story 10.9 AC5 — le marker cleanup Story 20.1 est présent.

    Fail-fast contre suppression accidentelle avant Story 20.1
    (migration 027). Le marker doit apparaître textuellement dans
    `backend/app/core/feature_flags.py`.
    """
    feature_flags_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "core"
        / "feature_flags.py"
    )
    assert feature_flags_path.is_file(), f"Fichier introuvable: {feature_flags_path}"

    content = feature_flags_path.read_text(encoding="utf-8")
    assert "CLEANUP: Story 20.1" in content, (
        "Marker `# CLEANUP: Story 20.1` manquant dans feature_flags.py."
    )
    assert "migration 027" in content, (
        "Marker doit mentionner `migration 027` (référence Story 20.1)."
    )


# --- Story 10.9 AC1/AC3 : `check_project_model_enabled` source unique ---


@pytest.mark.unit
def test_check_project_model_enabled_raises_404_when_disabled(monkeypatch):
    """Story 10.9 AC1/AC3 — dépendance FastAPI lève 404 si flag OFF."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "false")

    with pytest.raises(HTTPException) as exc_info:
        check_project_model_enabled()

    assert exc_info.value.status_code == 404
    assert "ENABLE_PROJECT_MODEL" in exc_info.value.detail


@pytest.mark.unit
def test_check_project_model_enabled_returns_none_when_enabled(monkeypatch):
    """Story 10.9 AC1/AC3 — dépendance FastAPI passe (None) si flag ON."""
    monkeypatch.setenv("ENABLE_PROJECT_MODEL", "true")

    assert check_project_model_enabled() is None


@pytest.mark.unit
def test_no_duplicate_check_project_model_enabled_definition():
    """Story 10.9 AC3 — 1 seule définition dans backend/app/.

    Fail-fast régression duplication (leçon 10.5) : si un dev
    redéfinit `check_project_model_enabled` dans un router local au lieu
    d'importer depuis `core/feature_flags.py`, ce test casse.
    """
    backend_app = Path(__file__).resolve().parents[2] / "app"
    assert backend_app.is_dir(), f"backend/app/ introuvable: {backend_app}"

    pattern = re.compile(r"^def check_project_model_enabled\b")
    hits: list[Path] = []
    for py_file in backend_app.rglob("*.py"):
        for line in py_file.read_text(encoding="utf-8").splitlines():
            if pattern.search(line):
                hits.append(py_file)
                break

    assert len(hits) == 1, (
        f"Définitions multiples de check_project_model_enabled détectées "
        f"(attendu 1 dans core/feature_flags.py). Trouvé(es) : {hits}"
    )
    assert hits[0].name == "feature_flags.py" and "core" in hits[0].parts, (
        f"Définition unique attendue dans core/feature_flags.py, "
        f"trouvée ailleurs : {hits[0]}"
    )
