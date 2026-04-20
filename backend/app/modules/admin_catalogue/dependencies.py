"""Dependances FastAPI du module admin_catalogue.

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].

Expose `require_admin_mefali` : dependance FastAPI stub qui enforce l'acces
admin Mefali tant que FR61 (Epic 18 — colonne User.role + MFA) n'est pas
livree. Fail-closed par defaut : si la variable d'env `ADMIN_MEFALI_EMAILS`
est absente ou vide, tous les utilisateurs recoivent 403.
"""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User


def _is_admin_mefali_email(email: str) -> bool:
    """Check whitelist email via env var `ADMIN_MEFALI_EMAILS` (comma-separated).

    Lecture dans le corps de la fonction (pas a l'import-time) pour
    permettre `monkeypatch.setenv` en tests.
    """
    allowed_raw = os.environ.get("ADMIN_MEFALI_EMAILS", "")
    allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
    return email.strip().lower() in allowed


async def require_admin_mefali(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce admin_mefali role (stub whitelist email MVP, remplacement Epic 18).

    MVP : whitelist d'emails via env var `ADMIN_MEFALI_EMAILS` (comma-separated).
    Epic 18 remplacera cette logique par
    `if current_user.role not in {"admin_mefali","admin_super"}: raise 403`.

    Ordre des statuts :
        - 401 : `get_current_user` leve si token absent/invalide (prime).
        - 403 : ici, si email non-whiteliste.
    """
    if not _is_admin_mefali_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces reserve au role admin_mefali (FR61 livre en Epic 18).",
        )
    return current_user
