"""Tests CRUD pour les modèles SQLAlchemy du module projects (Story 10.2 AC2, AC8)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.projects.enums import ProjectRoleEnum, ProjectStatusEnum
from app.modules.projects.models import (
    Project,
    ProjectMembership,
)


@pytest.mark.asyncio
async def test_project_model_crud_sqlite(db_session, company_factory):
    """Test 1 — INSERT -> SELECT -> UPDATE -> DELETE sur Project (SQLite)."""
    company = await company_factory()

    # INSERT
    project = Project(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Ferme solaire 50 kW",
        status=ProjectStatusEnum.idea,
        version_number=1,
        description="Projet solaire PME",
    )
    db_session.add(project)
    await db_session.flush()

    # SELECT
    fetched = (
        await db_session.execute(select(Project).where(Project.id == project.id))
    ).scalar_one()
    assert fetched.name == "Ferme solaire 50 kW"
    assert fetched.status == ProjectStatusEnum.idea

    # UPDATE status
    fetched.status = ProjectStatusEnum.planning
    await db_session.flush()
    refetched = (
        await db_session.execute(select(Project).where(Project.id == project.id))
    ).scalar_one()
    assert refetched.status == ProjectStatusEnum.planning

    # DELETE
    await db_session.delete(refetched)
    await db_session.flush()
    gone = (
        await db_session.execute(select(Project).where(Project.id == project.id))
    ).scalar_one_or_none()
    assert gone is None


@pytest.mark.asyncio
async def test_project_membership_unique_triplet(db_session, company_factory):
    """Test 2 — UNIQUE(project_id, company_id, role) D1 cumul rôles."""
    company = await company_factory()
    project = Project(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Projet",
        status=ProjectStatusEnum.idea,
    )
    db_session.add(project)
    await db_session.flush()

    m1 = ProjectMembership(
        id=uuid.uuid4(),
        project_id=project.id,
        company_id=company.id,
        role=ProjectRoleEnum.porteur_principal,
    )
    db_session.add(m1)
    await db_session.flush()

    # Un autre role pour le même (project, company) est OK (cumul D1)
    m_other_role = ProjectMembership(
        id=uuid.uuid4(),
        project_id=project.id,
        company_id=company.id,
        role=ProjectRoleEnum.beneficiaire,
    )
    db_session.add(m_other_role)
    await db_session.flush()

    # Re-insertion du même triplet -> IntegrityError
    dup = ProjectMembership(
        id=uuid.uuid4(),
        project_id=project.id,
        company_id=company.id,
        role=ProjectRoleEnum.porteur_principal,
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_project_status_enum_values():
    """Test 3 — ProjectStatusEnum a exactement 5 valeurs alignées sur migration 020."""
    values = {m.value for m in ProjectStatusEnum}
    assert values == {"idea", "planning", "in_progress", "operational", "archived"}
    assert len(values) == 5


def test_project_role_enum_values():
    """Test 4 — ProjectRoleEnum a exactement 4 valeurs alignées sur migration 020."""
    values = {m.value for m in ProjectRoleEnum}
    assert values == {"porteur_principal", "beneficiaire", "partenaire", "observateur"}
    assert len(values) == 4


def test_fk_cascade_project_delete_membership():
    """Test 5 — la FK project_memberships.project_id déclare ON DELETE CASCADE.

    Vérifie la déclaration DDL de cascade sur la metadata. SQLite ignore
    silencieusement les FK sauf si PRAGMA foreign_keys=ON est actif au
    niveau de la connexion (non garanti par le fixture conftest). La
    validation runtime de la cascade sera faite via `@pytest.mark.postgres`
    en environnement PostgreSQL (Story 10.5 RLS tests + Epic 11 intégration).
    """
    fk_to_projects = [
        fk
        for col in ProjectMembership.__table__.columns
        for fk in col.foreign_keys
        if fk.column.table.name == "projects"
    ]
    assert fk_to_projects, "project_memberships.project_id doit référencer projects"
    assert all(fk.ondelete == "CASCADE" for fk in fk_to_projects), (
        "FK project_memberships.project_id doit être ON DELETE CASCADE"
    )
