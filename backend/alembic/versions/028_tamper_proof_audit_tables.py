"""tamper-proof admin_access_audit + admin_catalogue_audit_trail (D6/D7)

Revision ID: 028_audit_tamper
Revises: 027_outbox_prefill
Create Date: 2026-04-20

Story 10.5 — résolution HIGH-10.1-11 (déféré par Story 10.1).

Rend les 2 tables d'audit **immutables au niveau SQL** (défense en
profondeur indépendante de tout bug applicatif) :
- ``REVOKE UPDATE, DELETE ON ... FROM PUBLIC`` : retire le privilège
  mutatif même à admin_super.
- Trigger ``BEFORE UPDATE OR DELETE`` qui ``RAISE EXCEPTION`` avec
  ERRCODE 42501 (insufficient_privilege).

INSERT reste autorisé (nécessaire pour l'event listener Story 10.5).

FR covered: [] (NFR12, NFR27 défense en profondeur — immutabilité audit)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

from alembic import op


revision: str = "028_audit_tamper"
down_revision: Union[str, None] = "027_outbox_prefill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AUDIT_TABLES = ("admin_access_audit", "admin_catalogue_audit_trail")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # Les triggers PL/pgSQL et REVOKE ... FROM PUBLIC n'ont pas
        # d'équivalent SQLite. Immutabilité applicative seule.
        return

    # REVOKE mutatif (écriture mutative uniquement — SELECT et INSERT restent).
    for table in AUDIT_TABLES:
        op.execute(f"REVOKE UPDATE, DELETE ON {table} FROM PUBLIC")

    # Fonction trigger partagée (idempotente via CREATE OR REPLACE).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_table_is_immutable()
        RETURNS trigger LANGUAGE plpgsql AS $fn$
        BEGIN
          RAISE EXCEPTION 'audit table is immutable (D6/D7)'
            USING ERRCODE = '42501';
        END;
        $fn$;
        """
    )

    # Triggers BEFORE UPDATE OR DELETE sur chaque table — idempotents via
    # bloc DO $$ ... IF NOT EXISTS ... (pattern robuste rerun).
    for table in AUDIT_TABLES:
        trigger_name = f"trg_{table}_immutable"
        op.execute(
            f"""
            DO $blk$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}'
              ) THEN
                CREATE TRIGGER {trigger_name}
                  BEFORE UPDATE OR DELETE ON {table}
                  FOR EACH ROW EXECUTE FUNCTION audit_table_is_immutable();
              END IF;
            END
            $blk$;
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in AUDIT_TABLES:
        trigger_name = f"trg_{table}_immutable"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table}")

    op.execute("DROP FUNCTION IF EXISTS audit_table_is_immutable()")

    for table in AUDIT_TABLES:
        op.execute(f"GRANT UPDATE, DELETE ON {table} TO PUBLIC")
