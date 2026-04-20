"""Modeles SQLAlchemy 2.0 pour le module maturity.

Story 10.3 - module `maturity/` squelette.
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Mappe strictement sur les 3 tables creees par migration
`backend/alembic/versions/021_create_maturity_schema.py` (Story 10.1 done).

Tables couvertes :
- admin_maturity_levels (catalogue N1, 5 niveaux gradues, UNIQUE level, UNIQUE code)
- formalization_plans (plan par company, FK company_id CASCADE)
- admin_maturity_requirements (exigences par pays x niveau, UNIQUE (country, level_id))

Note : le modele `Company` necessaire pour la FK `company_id -> companies.id`
est deja expose par `app.modules.projects.models` (Story 10.2). On ne le
redefinit pas ici (MEDIUM-10.2-1 — un seul modele Company global).

Colonnes SOURCE-TRACKING `source_url/source_accessed_at/source_version` sont
nullable — Story 10.11 ajoutera les contraintes CHECK via migration 025.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


def _jsonb() -> "JSONB":
    """JSONB cross-dialecte (Postgres natif, SQLite fallback JSON)."""
    return JSONB().with_variant(JSON(), "sqlite")


class AdminMaturityLevel(UUIDMixin, TimestampMixin, Base):
    """Catalogue admin des niveaux de maturite gradues (5 niveaux 1-5).

    Source : migration 021 (Story 10.1). UNIQUE `level` + UNIQUE `code`,
    CHECK `level BETWEEN 1 AND 5` (valide uniquement en PostgreSQL, SQLite
    ignore les CHECK au niveau colonne — cf. test_maturity `@pytest.mark.postgres`).
    """

    __tablename__ = "admin_maturity_levels"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 5", name="ck_maturity_level_1_5"),
        UniqueConstraint("level", name="uq_maturity_level"),
        UniqueConstraint("code", name="uq_maturity_code"),
    )

    level: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    label_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft"
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_version: Mapped[str | None] = mapped_column(String(64), nullable=True)


class FormalizationPlan(UUIDMixin, TimestampMixin, Base):
    """Plan de formalisation pays-specifique (FR13 Epic 12.3).

    FK `company_id` ON DELETE CASCADE (plan supprime si company disparait).
    FK `current_level_id` / `target_level_id` ON DELETE SET NULL (nullable).
    `actions_json` : JSONB cross-dialecte, payload pays-specifique data-driven.
    """

    __tablename__ = "formalization_plans"
    __table_args__ = (
        Index("ix_formalization_plans_company_id", "company_id"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_maturity_levels.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_maturity_levels.id", ondelete="SET NULL"),
        nullable=True,
    )
    actions_json: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )


class AdminMaturityRequirement(UUIDMixin, TimestampMixin, Base):
    """Exigences admin par pays x niveau (FR13 country-data-driven).

    Point d'entree unique pour Epic 12.3 `FormalizationPlanCalculator` :
    toute lecture de requirements passe par le service qui lit cette table
    (zero hardcoding pays en Python — NFR66).

    FK `level_id` ON DELETE RESTRICT (un niveau reference ne peut etre supprime).
    UNIQUE (country, level_id) — uq_maturity_country_level.
    """

    __tablename__ = "admin_maturity_requirements"
    __table_args__ = (
        UniqueConstraint(
            "country", "level_id", name="uq_maturity_country_level"
        ),
    )

    country: Mapped[str] = mapped_column(String(64), nullable=False)
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_maturity_levels.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requirements_json: Mapped[dict] = mapped_column(_jsonb(), nullable=False)
    workflow_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft"
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
