"""Tests de la surface d'API du service projects (Story 10.2 AC7)."""

from __future__ import annotations

import uuid

import pytest

from app.modules.projects import service as projects_service
from app.modules.projects.enums import ProjectRoleEnum, ProjectStatusEnum


_SKELETON_MARKER = "Story 10.2 skeleton"


@pytest.mark.asyncio
async def test_create_project_raises_not_implemented(db_session):
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await projects_service.create_project(
            db_session,
            company_id=uuid.uuid4(),
            name="Test",
            status=ProjectStatusEnum.idea,
        )


@pytest.mark.asyncio
async def test_get_project_raises_not_implemented(db_session):
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await projects_service.get_project(
            db_session, project_id=uuid.uuid4(), owner_user_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_list_projects_by_owner_raises_not_implemented(db_session):
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await projects_service.list_projects_by_owner(
            db_session, owner_user_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_add_membership_raises_not_implemented(db_session):
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await projects_service.add_membership(
            db_session,
            project_id=uuid.uuid4(),
            company_id=uuid.uuid4(),
            role=ProjectRoleEnum.porteur_principal,
        )


@pytest.mark.asyncio
async def test_get_memberships_for_project_raises_not_implemented(db_session):
    with pytest.raises(NotImplementedError, match=_SKELETON_MARKER):
        await projects_service.get_memberships_for_project(
            db_session, project_id=uuid.uuid4()
        )


def test_events_module_exposes_event_types():
    """Vérifie events.py (préparation CCC-14 D11 micro-Outbox)."""
    from app.modules.projects import events

    assert events.PROJECT_CREATED_EVENT_TYPE == "project.created"
    assert events.PROJECT_STATUS_CHANGED_EVENT_TYPE == "project.status_changed"
