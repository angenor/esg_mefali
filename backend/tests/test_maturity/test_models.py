"""Tests CRUD pour les modeles SQLAlchemy du module maturity (Story 10.3 AC2, AC8)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.maturity.enums import (
    MaturityChangeDirectionEnum,
    MaturityWorkflowStateEnum,
)
from app.modules.maturity.models import (
    AdminMaturityLevel,
    AdminMaturityRequirement,
    FormalizationPlan,
)


@pytest.mark.asyncio
async def test_admin_maturity_level_crud_sqlite(db_session):
    """Test 1 — INSERT -> SELECT -> UPDATE is_published -> DELETE (SQLite)."""
    level = AdminMaturityLevel(
        id=uuid.uuid4(),
        level=1,
        code="informel",
        label_fr="Informel",
        workflow_state="draft",
        is_published=False,
    )
    db_session.add(level)
    await db_session.flush()

    fetched = (
        await db_session.execute(
            select(AdminMaturityLevel).where(AdminMaturityLevel.id == level.id)
        )
    ).scalar_one()
    assert fetched.code == "informel"
    assert fetched.level == 1

    fetched.is_published = True
    await db_session.flush()
    refetched = (
        await db_session.execute(
            select(AdminMaturityLevel).where(AdminMaturityLevel.id == level.id)
        )
    ).scalar_one()
    assert refetched.is_published is True

    await db_session.delete(refetched)
    await db_session.flush()
    gone = (
        await db_session.execute(
            select(AdminMaturityLevel).where(AdminMaturityLevel.id == level.id)
        )
    ).scalar_one_or_none()
    assert gone is None


@pytest.mark.asyncio
async def test_admin_maturity_level_unique_code(db_session):
    """Test 2a — UNIQUE `code` (uq_maturity_code) -> IntegrityError."""
    db_session.add(
        AdminMaturityLevel(
            id=uuid.uuid4(),
            level=1,
            code="shared-code",
            label_fr="L1",
            workflow_state="draft",
            is_published=False,
        )
    )
    await db_session.flush()

    db_session.add(
        AdminMaturityLevel(
            id=uuid.uuid4(),
            level=2,
            code="shared-code",
            label_fr="L2",
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_admin_maturity_level_unique_level(db_session):
    """Test 2b — UNIQUE `level` (uq_maturity_level) -> IntegrityError."""
    db_session.add(
        AdminMaturityLevel(
            id=uuid.uuid4(),
            level=3,
            code="code-a",
            label_fr="La",
            workflow_state="draft",
            is_published=False,
        )
    )
    await db_session.flush()

    db_session.add(
        AdminMaturityLevel(
            id=uuid.uuid4(),
            level=3,
            code="code-b",
            label_fr="Lb",
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_admin_maturity_level_check_level_between_1_and_5(db_session):
    """Test 3 — CHECK `level BETWEEN 1 AND 5` (Postgres only).

    SQLite ne gere pas les CHECK au niveau colonne -> skip en environnement
    SQLite (marker `@pytest.mark.postgres`, lecon 10.1).
    """
    db_session.add(
        AdminMaturityLevel(
            id=uuid.uuid4(),
            level=0,
            code="zero",
            label_fr="Zero",
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_formalization_plan_fk_cascade_on_company_delete():
    """Test 4 — FormalizationPlan.company_id declare ON DELETE CASCADE.

    Valide la DDL (SQLite ignore les FK sauf PRAGMA foreign_keys=ON ;
    Story 10.5 RLS + Epic 12 valideront en PostgreSQL reel).
    """
    fk_to_companies = [
        fk
        for col in FormalizationPlan.__table__.columns
        for fk in col.foreign_keys
        if fk.column.table.name == "companies"
    ]
    assert fk_to_companies, (
        "formalization_plans.company_id doit referencer companies"
    )
    assert all(fk.ondelete == "CASCADE" for fk in fk_to_companies), (
        "FK formalization_plans.company_id doit etre ON DELETE CASCADE"
    )


@pytest.mark.asyncio
async def test_admin_maturity_requirement_unique_country_level(
    db_session, level_factory
):
    """Test 5 — UNIQUE (country, level_id) -> IntegrityError."""
    level = await level_factory(level=1, code="informel")

    db_session.add(
        AdminMaturityRequirement(
            id=uuid.uuid4(),
            country="CountryA",
            level_id=level.id,
            requirements_json={"steps": []},
            workflow_state="draft",
            is_published=False,
        )
    )
    await db_session.flush()

    db_session.add(
        AdminMaturityRequirement(
            id=uuid.uuid4(),
            country="CountryA",
            level_id=level.id,
            requirements_json={"steps": [1]},
            workflow_state="draft",
            is_published=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_maturity_workflow_state_enum_values():
    """Test 6 — MaturityWorkflowStateEnum a exactement 3 valeurs."""
    values = {m.value for m in MaturityWorkflowStateEnum}
    assert values == {"draft", "review_requested", "published"}
    assert len(values) == 3


def test_maturity_change_direction_enum_values():
    """Test 7 — MaturityChangeDirectionEnum a exactement 2 valeurs."""
    values = {m.value for m in MaturityChangeDirectionEnum}
    assert values == {"upgrade", "downgrade"}
    assert len(values) == 2
