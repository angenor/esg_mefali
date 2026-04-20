"""enable RLS on 4 sensitive tables + admin_access_audit (D7)

Revision ID: 024_rls_audit
Revises: 023_deliverables
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 024/8.
Support Décision 7 (multi-tenancy RLS + log admin escape).

Active RLS sur companies, fund_applications, facts, documents (PostgreSQL
uniquement — skip SQLite). Crée la table admin_access_audit pour
journaliser les accès admin_mefali/admin_super (event listener livré
Story 10.5).

Bypass admin via current_setting('app.user_role') IN ('admin_mefali',
'admin_super') — pas de policy séparée pour éviter confusion.

FR covered: [] (NFR12 défense en profondeur)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "024_rls_audit"
down_revision: Union[str, None] = "023_deliverables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


RLS_TABLES = ("companies", "fund_applications", "facts", "documents")

# Policy USING clause par table : chaque table expose un accès via FK.
# companies.owner_user_id, fund_applications.user_id, facts.company_id
# (via jointure implicite app-niveau), documents.user_id.
POLICY_USING = {
    "companies": (
        "owner_user_id = current_setting('app.current_user_id', true)::uuid "
        "OR current_setting('app.user_role', true) IN ('admin_mefali','admin_super')"
    ),
    "fund_applications": (
        "user_id = current_setting('app.current_user_id', true)::uuid "
        "OR current_setting('app.user_role', true) IN ('admin_mefali','admin_super')"
    ),
    "facts": (
        "company_id IN (SELECT id FROM companies WHERE owner_user_id = "
        "current_setting('app.current_user_id', true)::uuid) "
        "OR current_setting('app.user_role', true) IN ('admin_mefali','admin_super')"
    ),
    "documents": (
        "user_id = current_setting('app.current_user_id', true)::uuid "
        "OR current_setting('app.user_role', true) IN ('admin_mefali','admin_super')"
    ),
}


def upgrade() -> None:
    # ---------- admin_access_audit (D7) ----------
    op.create_table(
        "admin_access_audit",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("admin_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "admin_role",
            sa.Enum(
                "admin_mefali",
                "admin_super",
                name="admin_role_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("table_accessed", sa.String(length=64), nullable=False),
        sa.Column(
            "operation",
            sa.Enum(
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                name="rls_operation_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("record_ids", _jsonb_variant(), nullable=True),
        sa.Column("request_id", sa.UUID(), nullable=True),
        sa.Column("query_excerpt", sa.Text(), nullable=True),
        sa.Column(
            "accessed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["admin_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_access_audit_admin_ts",
        "admin_access_audit",
        ["admin_user_id", "accessed_at"],
    )
    op.create_index(
        "ix_admin_access_audit_table_ts",
        "admin_access_audit",
        ["table_accessed", "accessed_at"],
    )

    # RLS uniquement sur PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        using = POLICY_USING[table]
        # WITH CHECK explicite : bloque aussi INSERT/UPDATE d'une ligne
        # appartenant à un autre tenant (défense en profondeur — sans cet
        # ajout, Postgres applique USING comme WITH CHECK implicitement,
        # comportement non-évident pour un reviewer futur).
        op.execute(
            sa.text(
                f"CREATE POLICY tenant_isolation ON {table} "
                f"FOR ALL USING ({using}) WITH CHECK ({using})"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in RLS_TABLES:
            op.execute(
                sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
            )
            op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    op.drop_index(
        "ix_admin_access_audit_table_ts", table_name="admin_access_audit"
    )
    op.drop_index(
        "ix_admin_access_audit_admin_ts", table_name="admin_access_audit"
    )
    op.drop_table("admin_access_audit")

    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS rls_operation_enum"))
        op.execute(sa.text("DROP TYPE IF EXISTS admin_role_enum"))
