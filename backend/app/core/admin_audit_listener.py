"""Event listener SQLAlchemy : log les bypass admin dans ``admin_access_audit``.

Story 10.5 — pattern ``before_flush`` sur ``AsyncSession`` (architecture.md
§D7 ligne 647-654). À chaque flush, inspecte ``session.new | session.dirty
| session.deleted`` et, si la session courante est en contexte admin
(``app.user_role IN ('admin_mefali','admin_super')``), insère une ligne
``admin_access_audit`` par objet concerné parmi les 4 tables sensibles.

Limitations MVP (documentées) :
- **SELECT non capturables** via ``before_flush`` — ``before_flush`` ne se
  déclenche que sur les mutations. L'extension aux SELECT via un
  intercepteur ``Query.execute`` est déférée à Story 18.x quand le besoin
  concret émergera (audit interne/externe). En l'état MVP, le risque est
  mitigé : un admin qui veut exfiltrer des données devra nécessairement
  faire un INSERT dans son propre environnement pour les persister (donc
  capturé).
- **Atomicité** : insertion dans la **même session** que la mutation
  métier — si la transaction métier rollback, l'audit rollback aussi.
  Comportement voulu (pas de log orphelin sans modification effective).
- **Anti-récursion** : les mutations sur ``admin_access_audit`` et
  ``admin_catalogue_audit_trail`` sont ignorées pour éviter une boucle
  infinie (le listener auditerait l'audit qu'il vient d'insérer).

Enregistrement :
- Appel unique au startup dans ``app.main`` via
  ``register_admin_access_listener(engine)``.
- Pattern standard : ``event.listens_for(AsyncSession, "before_flush")``.
  Le listener est attaché au ``AsyncSession`` global ; tous les
  ``async_session_factory()`` l'héritent.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.rls import ADMIN_ROLES


RLS_TABLE_NAMES = frozenset({"companies", "fund_applications", "facts", "documents"})
AUDIT_TABLE_NAMES = frozenset({"admin_access_audit", "admin_catalogue_audit_trail"})

# Flag de session pour anti-récursion : si positionné, le listener skip
# (évite qu'un INSERT admin_access_audit généré par le listener ne
# redéclenche un nouveau flush qui re-déclencherait le listener).
_SESSION_AUDIT_FLAG = "admin_audit_listener_active"


def _collect_mutations(
    session: AsyncSession,
) -> list[tuple[str, str, Any]]:
    """Collecte les (operation, tablename, obj) à auditer.

    Filtre :
    - Tables RLS uniquement (companies, fund_applications, facts, documents).
    - Ignore les objets des tables audit elles-mêmes (anti-récursion).
    """
    mutations: list[tuple[str, str, Any]] = []
    for obj in session.new:
        tablename = getattr(type(obj), "__tablename__", None)
        if tablename in RLS_TABLE_NAMES:
            mutations.append(("INSERT", tablename, obj))
    for obj in session.dirty:
        tablename = getattr(type(obj), "__tablename__", None)
        if tablename in RLS_TABLE_NAMES:
            mutations.append(("UPDATE", tablename, obj))
    for obj in session.deleted:
        tablename = getattr(type(obj), "__tablename__", None)
        if tablename in RLS_TABLE_NAMES:
            mutations.append(("DELETE", tablename, obj))
    return mutations


def _build_audit_insert_sql() -> str:
    """SQL paramétré pour insérer une ligne dans admin_access_audit.

    Note : ``record_ids`` est JSONB côté PG / JSON côté SQLite via le
    cast applicatif dans la migration 024.
    """
    return (
        "INSERT INTO admin_access_audit "
        "(id, admin_user_id, admin_role, table_accessed, operation, "
        " record_ids, accessed_at) "
        "VALUES (:id, :admin_user_id, :admin_role, :table_accessed, "
        " :operation, CAST(:record_ids AS JSONB), now())"
    )


def register_admin_access_listener(engine: AsyncEngine | Engine) -> None:
    """Attache le listener ``before_flush`` au ``AsyncSession`` global.

    Args:
        engine: L'engine applicatif (AsyncEngine en prod, Engine pour
            tests sync). Le paramètre est gardé pour cohérence avec
            l'API architecture.md §D7 mais le listener est attaché sur
            la classe ``AsyncSession``, pas sur l'engine — un seul
            appel suffit au startup.

    Idempotence : SQLAlchemy déduplique automatiquement un même
    listener attaché deux fois sur le même event (pas de doublons).
    """
    del engine  # Paramètre conservé pour l'API publique ; non consommé ici.

    @event.listens_for(AsyncSession.sync_session_class, "before_flush")
    def _audit_admin_mutations(session, flush_context, instances):
        """Listener before_flush — inspecte les mutations admin.

        Note : attaché sur ``AsyncSession.sync_session_class`` (la
        ``Session`` sous-jacente), car SQLAlchemy déclenche les events
        sur la session synchrone wrappée par ``AsyncSession``.
        """
        del flush_context, instances

        # PostgreSQL only : RLS + current_setting n'existent pas sur SQLite.
        bind = session.get_bind()
        if bind is None or bind.dialect.name != "postgresql":
            return

        # Anti-récursion : si le listener est déjà actif pour cette
        # session (insertion d'audit en cours), skip pour éviter boucle.
        if session.info.get(_SESSION_AUDIT_FLAG):
            return

        mutations = _collect_mutations(session)
        if not mutations:
            return

        # Lire le contexte RLS de la session courante (même connexion
        # que les mutations — garantit la cohérence avec apply_rls_context).
        role_row = session.execute(
            text("SELECT current_setting('app.user_role', true)")
        ).fetchone()
        role = (role_row[0] if role_row else "") or ""

        if role not in ADMIN_ROLES:
            return

        uid_row = session.execute(
            text("SELECT current_setting('app.current_user_id', true)")
        ).fetchone()
        uid_raw = (uid_row[0] if uid_row else "") or ""
        if not uid_raw:
            # Admin sans user_id positionné : état incohérent — on ne log
            # pas (défense en profondeur, évite FK violation).
            return

        admin_uuid = uuid.UUID(uid_raw)
        insert_sql = text(_build_audit_insert_sql())

        # Positionner le flag anti-récursion avant d'exécuter les inserts
        # d'audit : le flush implicite ne se déclenche pas pour des
        # execute() directs (pas d'ORM), donc en pratique il n'y a pas
        # de récursion, mais la ceinture-bretelle est gratuite.
        session.info[_SESSION_AUDIT_FLAG] = True
        try:
            for operation, tablename, obj in mutations:
                record_id_raw = getattr(obj, "id", None)
                # Story 10.5 review fix (MEDIUM-10.5-1) : utiliser json.dumps
                # pour le quoting JSON natif au lieu d'une f-string. Garde
                # la cohérence bind-params avec rls.py et protège contre
                # toute injection JSON future si l'ID devenait non-UUID
                # (ex. clé business user-contrôlable). Conservé en bind via
                # CAST(:record_ids AS JSONB) — défense en profondeur.
                record_ids_json = (
                    json.dumps([str(record_id_raw)])
                    if record_id_raw is not None
                    else "[]"
                )
                session.execute(
                    insert_sql,
                    {
                        "id": str(uuid.uuid4()),
                        "admin_user_id": str(admin_uuid),
                        "admin_role": role,
                        "table_accessed": tablename,
                        "operation": operation,
                        "record_ids": record_ids_json,
                    },
                )
        finally:
            session.info[_SESSION_AUDIT_FLAG] = False
