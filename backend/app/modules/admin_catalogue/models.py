"""Modeles SQLAlchemy 2.0 pour le module admin_catalogue.

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].

Mappe strictement sur les tables creees par :
- migration 022 `create_esg_3_layers` (criteria, criterion_derivation_rules,
  referentials, packs)
- migration 026 `create_admin_catalogue_audit_trail` (admin_catalogue_audit_trail)

**5 modeles exposes** (source unique — les consommateurs Epic 13 + Story 10.12
ne doivent pas redefinir ces mappings) :
- Criterion
- Referential
- Pack
- CriterionDerivationRule
- AdminCatalogueAuditTrail

Colonnes SOURCE-TRACKING `source_url/source_accessed_at/source_version` sont
nullable — migration 025 applique les CHECK `is_published = false OR
source_url IS NOT NULL`. Epic 13 enforcera cote UI Story 10.11.

`AdminCatalogueAuditTrail` est append-only cote conception (Story 10.12
ajoutera les triggers PostgreSQL update/delete reject). Story 10.4 ne
declare aucune policy ORM update/delete.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
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
    """JSONB cross-dialecte (Postgres natif, SQLite fallback JSON).

    Duplique sciemment (auto-suffisance module) le helper de
    `app/modules/maturity/models.py` — choix architectural valide en 10.2.
    """
    return JSONB().with_variant(JSON(), "sqlite")


class Criterion(UUIDMixin, TimestampMixin, Base):
    """Critere ESG (couche 2 migration 022).

    Table `criteria` : cle UNIQUE `code`, workflow_state String(16) qui
    accepte les 5 valeurs de `NodeStateEnum` (draft/review_requested/
    reviewed/published/archived).
    """

    __tablename__ = "criteria"
    __table_args__ = (
        UniqueConstraint("code", name="uq_criteria_code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimension: Mapped[str] = mapped_column(String(32), nullable=False)
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
    source_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )


class Referential(UUIDMixin, TimestampMixin, Base):
    """Referentiel (couche 3 migration 022).

    Table `referentials` : cle UNIQUE `code`. Contrairement a `Criterion`,
    pas de colonne `dimension` (verdict global par referentiel).
    """

    __tablename__ = "referentials"
    __table_args__ = (
        UniqueConstraint("code", name="uq_referentials_code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
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
    source_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )


class Pack(UUIDMixin, TimestampMixin, Base):
    """Pack bailleur (couche 3 migration 022).

    Table `packs` : cle UNIQUE `code`. Divergence vs `Criterion`/`Referential` :
    pas de colonnes `dimension` ni `description` (la migration 022 ne les
    declare pas — respecter strict).
    """

    __tablename__ = "packs"
    __table_args__ = (
        UniqueConstraint("code", name="uq_packs_code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label_fr: Mapped[str] = mapped_column(String(255), nullable=False)
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
    source_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )


class CriterionDerivationRule(UUIDMixin, Base):
    """Regle de derivation d'un critere (couche 2 migration 022).

    Table `criterion_derivation_rules` : FK `criterion_id ON DELETE CASCADE`,
    CHECK `rule_type IN ('threshold','boolean_expression','aggregate',
    'qualitative_check')` (PostgreSQL uniquement ; SQLite ignore).

    **N'utilise PAS `TimestampMixin`** : la migration 022 ne declare que
    `created_at` (pas de `updated_at`). Respecter strict.
    """

    __tablename__ = "criterion_derivation_rules"
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('threshold','boolean_expression','aggregate','qualitative_check')",
            name="ck_rule_type_enum",
        ),
    )

    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_json: Mapped[dict] = mapped_column(_jsonb(), nullable=False)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AdminCatalogueAuditTrail(UUIDMixin, Base):
    """Audit trail immuable des mutations catalogue (FR64 migration 026).

    **Append-only** (Story 10.12 livrera les triggers PG update/delete reject).

    **N'utilise PAS `TimestampMixin`** : la migration 026 ne declare que `ts`
    (pas de `created_at`/`updated_at`). Respecter strict.

    3 index composite pour les requetes typiques :
    - `entity_type + entity_id + ts` : historique d'une entite
    - `actor_user_id + ts` : actions d'un admin
    - `workflow_level + ts` : transitions par niveau N1/N2/N3
    """

    __tablename__ = "admin_catalogue_audit_trail"
    __table_args__ = (
        Index(
            "ix_catalogue_audit_entity_ts",
            "entity_type",
            "entity_id",
            "ts",
        ),
        Index(
            "ix_catalogue_audit_actor_ts",
            "actor_user_id",
            "ts",
        ),
        Index(
            "ix_catalogue_audit_level_ts",
            "workflow_level",
            "ts",
        ),
    )

    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    action: Mapped[str] = mapped_column(
        SAEnum(
            "create",
            "update",
            "delete",
            "publish",
            "retire",
            name="catalogue_action_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    workflow_level: Mapped[str] = mapped_column(
        SAEnum(
            "N1",
            "N2",
            "N3",
            name="workflow_level_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    workflow_state_before: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    workflow_state_after: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    changes_before: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)
    changes_after: Mapped[dict | None] = mapped_column(_jsonb(), nullable=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
