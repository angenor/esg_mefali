"""Tests CRUD pour les modeles SQLAlchemy du module admin_catalogue (Story 10.4 AC2, AC8)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.admin_catalogue.enums import (
    CatalogueActionEnum,
    NodeStateEnum,
    WorkflowLevelEnum,
)
from app.modules.admin_catalogue.models import (
    AdminCatalogueAuditTrail,
    Criterion,
    CriterionDerivationRule,
    Pack,
    Referential,
)


@pytest.mark.asyncio
async def test_criterion_crud_sqlite(db_session):
    """Test 1 — INSERT -> SELECT -> UPDATE is_published -> DELETE sur Criterion."""
    crit = Criterion(
        id=uuid.uuid4(),
        code="c1",
        label_fr="Critere 1",
        dimension="E",
        workflow_state="draft",
        is_published=False,
    )
    db_session.add(crit)
    await db_session.flush()

    fetched = (
        await db_session.execute(
            select(Criterion).where(Criterion.id == crit.id)
        )
    ).scalar_one()
    assert fetched.code == "c1"
    assert fetched.dimension == "E"

    fetched.is_published = True
    await db_session.flush()
    refetched = (
        await db_session.execute(
            select(Criterion).where(Criterion.id == crit.id)
        )
    ).scalar_one()
    assert refetched.is_published is True

    await db_session.delete(refetched)
    await db_session.flush()
    gone = (
        await db_session.execute(
            select(Criterion).where(Criterion.id == crit.id)
        )
    ).scalar_one_or_none()
    assert gone is None


@pytest.mark.asyncio
async def test_referential_unique_code(db_session):
    """Test 2a — UNIQUE `code` (uq_referentials_code) -> IntegrityError."""
    db_session.add(
        Referential(
            id=uuid.uuid4(),
            code="shared-ref",
            label_fr="Ref A",
            workflow_state="draft",
            is_published=False,
        )
    )
    await db_session.flush()

    db_session.add(
        Referential(
            id=uuid.uuid4(),
            code="shared-ref",
            label_fr="Ref B",
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_pack_unique_code(db_session):
    """Test 2b — UNIQUE `code` (uq_packs_code) -> IntegrityError."""
    db_session.add(
        Pack(
            id=uuid.uuid4(),
            code="shared-pack",
            label_fr="Pack A",
            workflow_state="draft",
            is_published=False,
        )
    )
    await db_session.flush()

    db_session.add(
        Pack(
            id=uuid.uuid4(),
            code="shared-pack",
            label_fr="Pack B",
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_criterion_derivation_rule_fk_cascade_on_criterion_delete():
    """Test 3 — FK `criterion_id` declare ON DELETE CASCADE (valide DDL)."""
    fk_to_criteria = [
        fk
        for col in CriterionDerivationRule.__table__.columns
        for fk in col.foreign_keys
        if fk.column.table.name == "criteria"
    ]
    assert fk_to_criteria, (
        "criterion_derivation_rules.criterion_id doit referencer criteria"
    )
    assert all(fk.ondelete == "CASCADE" for fk in fk_to_criteria), (
        "FK criterion_id doit etre ON DELETE CASCADE"
    )


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_criterion_derivation_rule_check_rule_type(db_session):
    """Test 4 — CHECK `rule_type IN (...)` (Postgres only, SQLite ignore).

    Marker `@pytest.mark.postgres` — skip en env SQLite-only (lecon 10.1 + 10.3).
    """
    crit = Criterion(
        id=uuid.uuid4(),
        code="c-rule-check",
        label_fr="C",
        dimension="E",
        workflow_state="draft",
        is_published=False,
    )
    db_session.add(crit)
    await db_session.flush()

    db_session.add(
        CriterionDerivationRule(
            id=uuid.uuid4(),
            criterion_id=crit.id,
            rule_type="invalid",
            rule_json={},
            version=1,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_admin_catalogue_audit_trail_indexes_declared():
    """Test 5 — 3 index composite declares sur admin_catalogue_audit_trail."""
    index_names = {ix.name for ix in AdminCatalogueAuditTrail.__table__.indexes}
    assert "ix_catalogue_audit_entity_ts" in index_names
    assert "ix_catalogue_audit_actor_ts" in index_names
    assert "ix_catalogue_audit_level_ts" in index_names


def test_node_state_enum_has_exactly_5_values():
    """Test 6 — NodeStateEnum figee a 5 valeurs des 10.4 (invariant 13.8b/c)."""
    values = {m.value for m in NodeStateEnum}
    assert values == {
        "draft",
        "review_requested",
        "reviewed",
        "published",
        "archived",
    }
    assert len(values) == 5


def test_catalogue_action_and_workflow_level_enums():
    """Test 7 — CatalogueActionEnum (5 valeurs) + WorkflowLevelEnum (3 valeurs)."""
    action_values = {m.value for m in CatalogueActionEnum}
    assert action_values == {"create", "update", "delete", "publish", "retire"}
    assert len(action_values) == 5

    level_values = {m.value for m in WorkflowLevelEnum}
    assert level_values == {"N1", "N2", "N3"}
    assert len(level_values) == 3
