"""create projects schema (Cluster A N:N avec cumul de rôles)

Revision ID: 020_projects
Revises: 019_manual_edits
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 020/8.
Support Décision 1 (Company × Project N:N + cumul de rôles) de architecture.md.

Tables créées : companies, projects, project_memberships,
project_role_permissions, project_snapshots, company_projections,
beneficiary_profiles.

ALTER fund_applications : +project_id (FK NOT NULL avec backfill piloté),
+version_number (optimistic locking D11), +snapshot_id (FK snapshots),
+submitted_hash (SHA-256 FR40).

Backfill piloté Q2 (arbitrage 2026-04-20) : pour chaque user avec
fund_applications legacy, un triplet company + project "legacy" est créé
AVANT ALTER SET NOT NULL. Rollback supporté dans downgrade().

Déterminisme : si un user possède plusieurs projects legacy (cas hors-MVP),
toutes ses fund_applications sont rattachées au project le plus ancien
(ORDER BY projects.created_at ASC) pour garantir la reproductibilité.

FR covered: [] (infra FR1-FR10)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "020_projects"
down_revision: Union[str, None] = "019_manual_edits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _jsonb_variant() -> sa.types.TypeEngine:
    """JSONB cross-dialecte (Postgres + SQLite)."""
    return sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    # ---------- 1. companies (nouvelle table, socle Cluster A) ----------
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", _jsonb_variant(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_owner_user_id", "companies", ["owner_user_id"])

    # ---------- 2. projects (Cluster A) ----------
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "idea",
                "planning",
                "in_progress",
                "operational",
                "archived",
                name="project_status_enum",
                create_constraint=True,
            ),
            nullable=False,
            server_default="idea",
        ),
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", _jsonb_variant(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_projects_company_status", "projects", ["company_id", "status"]
    )

    # ---------- 3. project_memberships (cumul rôles D1) ----------
    op.create_table(
        "project_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "porteur_principal",
                "beneficiaire",
                "partenaire",
                "observateur",
                name="project_role_enum",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "company_id",
            "role",
            name="uq_project_memberships_triplet",
        ),
    )

    # ---------- 4. project_role_permissions (catalogue permissions) ----------
    op.create_table(
        "project_role_permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("permission", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role", "permission", name="uq_project_role_permission"
        ),
    )

    # ---------- 5. project_snapshots (gel hash FR40) ----------
    op.create_table(
        "project_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("payload", _jsonb_variant(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_snapshots_project_id",
        "project_snapshots",
        ["project_id"],
    )

    # ---------- 6. company_projections (cache lecture) ----------
    op.create_table(
        "company_projections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("projection_type", sa.String(length=64), nullable=False),
        sa.Column("payload", _jsonb_variant(), nullable=False),
        sa.Column(
            "refreshed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "projection_type",
            name="uq_company_projection_type",
        ),
    )

    # ---------- 7. beneficiary_profiles (Cluster A') ----------
    op.create_table(
        "beneficiary_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("survey_data", _jsonb_variant(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_beneficiary_profiles_company_id",
        "beneficiary_profiles",
        ["company_id"],
    )

    # ---------- 8. ALTER fund_applications : colonnes Cluster A ----------
    op.add_column(
        "fund_applications",
        sa.Column("project_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "fund_applications",
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "fund_applications",
        sa.Column("snapshot_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "fund_applications",
        sa.Column("submitted_hash", sa.String(length=64), nullable=True),
    )

    # ---------- 9. Backfill piloté Q2 : project legacy par user ----------
    # Pré-MVP : aucune donnée prod legacy attendue. Si des lignes existent,
    # on crée companies/projects « legacy » pour chaque user distinct afin
    # de satisfaire la contrainte NOT NULL + FK.
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(
            sa.text(
                """
                INSERT INTO companies (id, owner_user_id, name, created_at, updated_at)
                SELECT gen_random_uuid(), fa.user_id,
                       'Legacy Company (user ' || fa.user_id || ')',
                       now(), now()
                FROM (SELECT DISTINCT user_id FROM fund_applications) fa
                WHERE NOT EXISTS (
                    SELECT 1 FROM companies c WHERE c.owner_user_id = fa.user_id
                )
                """
            )
        )
        op.execute(
            sa.text(
                """
                INSERT INTO projects (id, company_id, name, status, version_number, created_at, updated_at)
                SELECT gen_random_uuid(), c.id, 'Legacy Project', 'archived', 1, now(), now()
                FROM companies c
                WHERE NOT EXISTS (
                    SELECT 1 FROM projects p WHERE p.company_id = c.id
                )
                """
            )
        )
        op.execute(
            sa.text(
                """
                UPDATE fund_applications fa
                SET project_id = (
                    SELECT p.id
                    FROM projects p
                    JOIN companies c ON p.company_id = c.id
                    WHERE c.owner_user_id = fa.user_id
                    ORDER BY p.created_at ASC
                    LIMIT 1
                )
                WHERE fa.project_id IS NULL
                """
            )
        )
    # SQLite : pas de backfill auto (tests utilisent data vierge).

    # ---------- 10. FK + NOT NULL sur project_id (Postgres only) ----------
    if dialect == "postgresql":
        op.execute(
            sa.text(
                "ALTER TABLE fund_applications "
                "ALTER COLUMN project_id SET NOT NULL"
            )
        )
    op.create_foreign_key(
        "fk_fund_applications_project_id",
        "fund_applications",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_fund_applications_snapshot_id",
        "fund_applications",
        "project_snapshots",
        ["snapshot_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_fund_applications_project_id",
        "fund_applications",
        ["project_id"],
    )


def downgrade() -> None:
    # Rollback : retire colonnes + FK ajoutées à fund_applications puis
    # DROP tables Cluster A en ordre inverse FK.
    op.drop_index(
        "ix_fund_applications_project_id", table_name="fund_applications"
    )
    op.drop_constraint(
        "fk_fund_applications_snapshot_id",
        "fund_applications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_fund_applications_project_id",
        "fund_applications",
        type_="foreignkey",
    )
    op.drop_column("fund_applications", "submitted_hash")
    op.drop_column("fund_applications", "snapshot_id")
    op.drop_column("fund_applications", "version_number")
    op.drop_column("fund_applications", "project_id")

    op.drop_index(
        "ix_beneficiary_profiles_company_id",
        table_name="beneficiary_profiles",
    )
    op.drop_table("beneficiary_profiles")

    op.drop_table("company_projections")

    op.drop_index(
        "ix_project_snapshots_project_id", table_name="project_snapshots"
    )
    op.drop_table("project_snapshots")

    op.drop_table("project_role_permissions")
    op.drop_table("project_memberships")

    op.drop_index("ix_projects_company_status", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_companies_owner_user_id", table_name="companies")
    op.drop_table("companies")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS project_role_enum"))
        op.execute(sa.text("DROP TYPE IF EXISTS project_status_enum"))
