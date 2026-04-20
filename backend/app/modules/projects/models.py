"""Modeles SQLAlchemy 2.0 pour le module projects.

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].

Mappe strictement sur les 6 tables creees par migration
`backend/alembic/versions/020_create_projects_schema.py` (Story 10.1 done).

Tables couvertes :
- projects
- project_memberships (UNIQUE (project_id, company_id, role))
- project_role_permissions
- project_snapshots
- company_projections
- beneficiary_profiles

Note : un modele `Company` minimal est ajoute ici (7e modele) pour satisfaire
les ForeignKey `company_id -> companies.id` lors des tests SQLite (Story 10.2).
Epic 11 Story 11-1 enrichira ce modele avec la logique metier (owner_user_id,
sector, ...). Cf. migration 020 colonnes `companies`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.modules.projects.enums import ProjectRoleEnum, ProjectStatusEnum


def _jsonb() -> "JSONB":
    """JSONB cross-dialecte (Postgres natif, SQLite fallback JSON)."""
    return JSONB().with_variant(JSON(), "sqlite")


class Company(UUIDMixin, TimestampMixin, Base):
    """Company (socle Cluster A — migration 020 table `companies`).

    Modele minimal fournissant la cible des ForeignKey `company_id`. Epic 11
    Story 11-1 enrichira ce modele avec la logique metier complete
    (relations, services, validations). Cf. migration 020.

    .. note::
       Coexiste temporairement avec ``app.models.company.CompanyProfile``
       (table ``company_profiles``, spec 003 MVP). Story 11-1 migrera les
       usages metier MVP vers ``Company`` et Story 20.1 depreciera
       ``CompanyProfile``. Cf. deferred-work.md §« Migration Cluster A :
       CompanyProfile → Company » pour le plan de coexistence.
    """

    __tablename__ = "companies"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)


class Project(UUIDMixin, TimestampMixin, Base):
    """Projet porte par une company (D1 Cluster A)."""

    __tablename__ = "projects"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatusEnum] = mapped_column(
        Enum(
            ProjectStatusEnum,
            name="project_status_enum",
            create_constraint=True,
            native_enum=True,
        ),
        nullable=False,
        default=ProjectStatusEnum.idea,
    )
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)


class ProjectMembership(UUIDMixin, Base):
    """Membership Company x Project x Role (cumul de roles D1)."""

    __tablename__ = "project_memberships"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "company_id",
            "role",
            name="uq_project_memberships_triplet",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ProjectRoleEnum] = mapped_column(
        Enum(
            ProjectRoleEnum,
            name="project_role_enum",
            create_constraint=True,
            native_enum=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ProjectRolePermission(UUIDMixin, Base):
    """Catalogue des permissions par role projet."""

    __tablename__ = "project_role_permissions"
    __table_args__ = (
        UniqueConstraint("role", "permission", name="uq_project_role_permission"),
    )

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    permission: Mapped[str] = mapped_column(String(64), nullable=False)


class ProjectSnapshot(UUIDMixin, Base):
    """Gel immuable d'un projet au moment d'une soumission (FR40 hash)."""

    __tablename__ = "project_snapshots"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(_jsonb(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class CompanyProjection(UUIDMixin, Base):
    """Cache de lecture (projection) par company + type."""

    __tablename__ = "company_projections"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "projection_type",
            name="uq_company_projection_type",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    projection_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(_jsonb(), nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BeneficiaryProfile(UUIDMixin, TimestampMixin, Base):
    """Profil beneficiaire (Cluster A') attache a une company (+ optionnel projet)."""

    __tablename__ = "beneficiary_profiles"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    survey_data: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)
