"""Feature flags de l'application (lecture env var, sans cache).

Story 10.2 : helper `is_project_model_enabled()` pose le socle consomme
par le router `/api/projects`. Story 10.9 : formalisation — consolidation
de la dependance FastAPI `check_project_model_enabled()` ici (source
unique, reutilisable multi-router) + marker cleanup Story 20.1.

Clarification 5 (Story 10.1) : aucune librairie externe (flipper,
unleash, launchdarkly) — simple lecture `os.environ` avec truthy values
case-insensitive.
"""

# CLEANUP: Story 20.1 — retirer ce fichier post-bascule Phase 1 (migration 027).
# Aucun caller ne doit subsister dans backend/app/ au moment du retrait.

from __future__ import annotations

import os

from fastapi import HTTPException

_TRUTHY_VALUES = frozenset({"true", "1", "yes"})

_FLAG_DISABLED_DETAIL = "Feature not available: ENABLE_PROJECT_MODEL is disabled"


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


def check_project_model_enabled() -> None:
    """Dependance FastAPI : leve `HTTPException(404)` si le flag est OFF.

    Reutilisable par tous les routers Phase 1 qui gatent le modele Project
    (consolidation Story 10.9 AC3, source unique). Preserve l'invariant
    comportemental 401 -> 404 -> 501 defini par Story 10.2 AC3.

    Raises
    ------
    HTTPException
        Status 404 si `is_project_model_enabled()` retourne `False`.
    """
    if not is_project_model_enabled():
        raise HTTPException(status_code=404, detail=_FLAG_DISABLED_DETAIL)
