"""Feature flags de l'application (lecture env var, sans cache).

Story 10.2 : helper `is_project_model_enabled()` pose le socle consomme
par le router `/api/projects`. Story 10.9 livrera le wrapper complet et
les tests dedies (10.9 AC1-AC6). Story 20.1 (fin Phase 1) supprimera ce
fichier apres bascule complete Project Model.

Clarification 5 (Story 10.1) : aucune librairie externe (flipper,
unleash, launchdarkly) — simple lecture `os.environ` avec truthy values
case-insensitive.
"""

from __future__ import annotations

import os

_TRUTHY_VALUES = frozenset({"true", "1", "yes"})


def is_project_model_enabled() -> bool:
    """Retourne `True` si le feature flag `ENABLE_PROJECT_MODEL` est actif.

    Lu DYNAMIQUEMENT a chaque appel (pas de cache module-level) pour que
    le toggle live en DEV via `monkeypatch.setenv` fonctionne — exigence
    AC4 Story 10.2 + AC6 Story 10.9.

    Truthy : `"true"`, `"1"`, `"yes"` (case-insensitive).
    Defaut : `False` (feature masquee en MVP, arbitrage Q1 Story 10.1).
    """
    raw = os.environ.get("ENABLE_PROJECT_MODEL", "false")
    return raw.strip().lower() in _TRUTHY_VALUES
