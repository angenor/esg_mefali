"""Injection du contexte RLS PostgreSQL (NFR12 défense en profondeur).

Story 10.5 — active la couche applicative qui consomme la migration 024
(policies tenant_isolation + table admin_access_audit) en positionnant
`app.current_user_id` et `app.user_role` sur chaque session authentifiée.

FR covered: [FR59] (RLS 4 tables)
NFR covered: [NFR12, NFR18, NFR27, NFR60]
Phase: 0 (Fondations)

Architecture références :
- _bmad-output/planning-artifacts/architecture.md §D7 (RLS + escape log)
- _bmad-output/planning-artifacts/architecture.md CCC-5 (multi-tenancy)
- backend/alembic/versions/024_enable_rls_on_sensitive_tables.py

Contrat d'API :
- ``apply_rls_context(db, user)`` : positionne ``app.current_user_id`` et
  ``app.user_role`` sur la session courante. ``user=None`` → état anonyme
  explicite (chaîne vide). Utilise ``set_config(..., is_local=false)`` —
  scope session PostgreSQL (pas transaction) pour survivre aux commits
  intermédiaires du même request cycle.
- ``reset_rls_context(db)`` : remet les 2 settings à ``''``. Appelé dans
  le ``finally`` de ``get_db`` pour éviter toute fuite cross-requête via
  pool asyncpg reuse (connexion checkin).
- ``resolve_user_role(user)`` : dérive le rôle à partir de la whitelist
  email (cohérence Story 10.4 ``_is_admin_mefali_email``) — pas de
  duplication de liste, source unique.
- ``ADMIN_ROLES`` : frozenset consommé par le listener d'audit (évite
  magic strings).

Sécurité :
- Bind params ``sqlalchemy.text("SELECT set_config(:k, :v, false)")`` —
  défense en profondeur contre toute injection future si ``user.id``
  devenait partiellement contrôlable (aujourd'hui UUID validé).
- Fail-closed sur ``ADMIN_SUPER_EMAILS`` : variable absente → aucun
  admin_super (cohérence pattern 10.4 ``ADMIN_MEFALI_EMAILS``).
"""

from __future__ import annotations

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


ADMIN_ROLES: frozenset[str] = frozenset({"admin_mefali", "admin_super"})


def _is_admin_super_email(email: str) -> bool:
    """Check whitelist email ``ADMIN_SUPER_EMAILS`` (comma-separated).

    Lecture dans le corps de la fonction (pas à l'import-time) pour
    permettre ``monkeypatch.setenv`` en tests. Fail-closed : variable
    absente ou vide → aucun admin_super.
    """
    allowed_raw = os.environ.get("ADMIN_SUPER_EMAILS", "")
    allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
    return email.strip().lower() in allowed


def resolve_user_role(user: User) -> str:
    """Dérive le rôle RLS d'un utilisateur à partir de la whitelist email.

    Retourne :
    - ``"admin_super"`` si email ∈ ``ADMIN_SUPER_EMAILS``
    - ``"admin_mefali"`` si email ∈ ``ADMIN_MEFALI_EMAILS``
    - ``"user"`` sinon

    La précédence admin_super > admin_mefali garantit que si un email
    figure dans les 2 listes (mauvaise config ops), le privilège le plus
    élevé l'emporte — comportement prévisible.

    Remplacé par FR61 (Epic 18 : colonne ``User.role`` + MFA step-up).
    """
    # Import tardif pour casser le cycle d'import
    # (admin_catalogue.dependencies → api.deps → core.database → core.rls).
    # Source unique : pas de duplication de la whitelist email.
    from app.modules.admin_catalogue.dependencies import _is_admin_mefali_email

    email = user.email or ""
    if _is_admin_super_email(email):
        return "admin_super"
    if _is_admin_mefali_email(email):
        return "admin_mefali"
    return "user"


def _is_postgres_session(db: AsyncSession) -> bool:
    """True si la session est bindée à PostgreSQL.

    RLS + ``set_config`` sont PostgreSQL-only. Sur SQLite (tests), les
    fonctions ``apply_rls_context`` / ``reset_rls_context`` sont no-op :
    RLS n'existe pas, la sécurité applicative repose exclusivement sur
    les filtres WHERE des requêtes (NFR12 défense en profondeur).
    """
    bind = db.get_bind()
    return bind.dialect.name == "postgresql"


async def apply_rls_context(db: AsyncSession, user: User | None) -> None:
    """Positionne ``app.current_user_id`` et ``app.user_role`` sur la session.

    Args:
        db: Session SQLAlchemy async.
        user: Utilisateur authentifié, ou None pour état anonyme explicite.

    Comportement :
    - ``user=None`` → ``('', '')`` (anonyme explicite, RLS filtre tout).
    - ``user`` normal → ``(str(user.id), 'user')``.
    - ``user`` admin (whitelist) → ``(str(user.id), 'admin_mefali|admin_super')``.

    Utilise ``is_local=false`` (3ᵉ param de ``set_config``) pour scope
    session PostgreSQL : survit aux commits intermédiaires du même
    request cycle. Le reset de sécurité est effectué dans ``get_db``.

    No-op sur SQLite (tests) : ``set_config`` n'existe pas, RLS non plus.
    """
    if not _is_postgres_session(db):
        return

    if user is None:
        user_id_value = ""
        role_value = ""
    else:
        user_id_value = str(user.id)
        role_value = resolve_user_role(user)

    await db.execute(
        text("SELECT set_config(:k, :v, false)"),
        {"k": "app.current_user_id", "v": user_id_value},
    )
    await db.execute(
        text("SELECT set_config(:k, :v, false)"),
        {"k": "app.user_role", "v": role_value},
    )


async def reset_rls_context(db: AsyncSession) -> None:
    """Remet ``app.current_user_id`` et ``app.user_role`` à ``''``.

    Appelé dans le ``finally`` de ``get_db`` pour éviter toute fuite
    cross-requête via pool asyncpg reuse : une connexion rendue au pool
    puis réutilisée par une autre requête hériterait sinon du contexte
    de la requête précédente (set_config is_local=false persiste jusqu'à
    fermeture physique de la connexion).

    No-op sur SQLite (tests).
    """
    if not _is_postgres_session(db):
        return

    await db.execute(
        text("SELECT set_config(:k, :v, false)"),
        {"k": "app.current_user_id", "v": ""},
    )
    await db.execute(
        text("SELECT set_config(:k, :v, false)"),
        {"k": "app.user_role", "v": ""},
    )
