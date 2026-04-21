"""Tests unit du body `service.record_audit_event` (Story 10.12 AC6).

Tests SQLite-friendly (pas de trigger PG) — validation registre fail-fast et
signature byte-identique (pattern shims legacy 10.6). Les tests d'atomicite
CCC-14 vrais live sur PG sont dans `test_audit_trail_atomicity.py`.
"""

from __future__ import annotations

import inspect
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin_catalogue.enums import (
    CatalogueActionEnum,
    WorkflowLevelEnum,
)
from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail
from app.modules.admin_catalogue.service import record_audit_event


@pytest.mark.asyncio
async def test_record_audit_event_rejects_unknown_action(
    db_session: AsyncSession,
) -> None:
    """Action hors registre `ACTION_TYPES` -> ValueError fail-fast."""
    with pytest.raises(ValueError, match="Action `hacked` invalide"):
        await record_audit_event(
            db_session,
            actor_user_id=uuid.uuid4(),
            entity_type="fund",
            entity_id=uuid.uuid4(),
            action="hacked",  # type: ignore[arg-type]
            workflow_level="N1",  # type: ignore[arg-type]
            workflow_state_before=None,
            workflow_state_after=None,
            changes_before=None,
            changes_after=None,
            correlation_id=None,
        )


@pytest.mark.asyncio
async def test_record_audit_event_rejects_unknown_workflow_level(
    db_session: AsyncSession,
) -> None:
    """`workflow_level` hors `WORKFLOW_LEVELS` -> ValueError."""
    with pytest.raises(ValueError, match="Workflow level `N4` invalide"):
        await record_audit_event(
            db_session,
            actor_user_id=uuid.uuid4(),
            entity_type="fund",
            entity_id=uuid.uuid4(),
            action="create",  # type: ignore[arg-type]
            workflow_level="N4",  # type: ignore[arg-type]
            workflow_state_before=None,
            workflow_state_after=None,
            changes_before=None,
            changes_after=None,
            correlation_id=None,
        )


@pytest.mark.asyncio
async def test_record_audit_event_persists_row_via_orm(
    db_session: AsyncSession,
    seed_admin_user,
) -> None:
    """Appel nominal : row visible post-flush en meme session (avant commit)."""
    actor_id = seed_admin_user.id
    entity_id = uuid.uuid4()
    correlation_id = uuid.uuid4()

    entity = await record_audit_event(
        db_session,
        actor_user_id=actor_id,
        entity_type="fund",
        entity_id=entity_id,
        action=CatalogueActionEnum.create,
        workflow_level=WorkflowLevelEnum.N1,
        workflow_state_before=None,
        workflow_state_after="draft",
        changes_before=None,
        changes_after={"title": "Test Fund"},
        correlation_id=correlation_id,
    )

    # id + ts generes server-default — disponibles post-flush
    assert entity.id is not None
    assert entity.ts is not None
    assert entity.actor_user_id == actor_id
    assert entity.entity_id == entity_id
    assert entity.correlation_id == correlation_id
    assert entity.changes_after == {"title": "Test Fund"}

    # Effet observable round-trip : meme session voit la row
    stmt = select(AdminCatalogueAuditTrail).where(
        AdminCatalogueAuditTrail.entity_id == entity_id
    )
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].id == entity.id


@pytest.mark.asyncio
async def test_record_audit_event_correlation_id_nullable_roundtrip(
    db_session: AsyncSession,
    seed_admin_user,
) -> None:
    """`correlation_id=None` autorise (migration 026 declare colonne nullable)."""
    entity = await record_audit_event(
        db_session,
        actor_user_id=seed_admin_user.id,
        entity_type="referential",
        entity_id=uuid.uuid4(),
        action=CatalogueActionEnum.update,
        workflow_level=WorkflowLevelEnum.N2,
        workflow_state_before="draft",
        workflow_state_after="reviewed",
        changes_before={"label_fr": "Old"},
        changes_after={"label_fr": "New"},
        correlation_id=None,
    )
    assert entity.correlation_id is None
    assert entity.workflow_state_before == "draft"
    assert entity.workflow_state_after == "reviewed"


def test_record_audit_event_signature_byte_identical_to_stub() -> None:
    """Pattern shims legacy 10.6 : signature stub 10.4 preservee apres implementation.

    Parametres keyword-only + types preserves — zero breaking change pour
    les callers Epic 13 qui appelleront la fonction avec les memes kwargs
    que ceux documentes dans le stub 10.4 (`records_audit_event` service.py
    lignes 112-137).
    """
    sig = inspect.signature(record_audit_event)
    expected_params = {
        "db",
        "actor_user_id",
        "entity_type",
        "entity_id",
        "action",
        "workflow_level",
        "workflow_state_before",
        "workflow_state_after",
        "changes_before",
        "changes_after",
        "correlation_id",
    }
    assert set(sig.parameters.keys()) == expected_params
    # Tous sauf `db` doivent etre keyword-only (stub 10.4 utilise `*` separator)
    for name, param in sig.parameters.items():
        if name == "db":
            assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        else:
            assert param.kind == inspect.Parameter.KEYWORD_ONLY, (
                f"Parametre `{name}` doit rester KEYWORD_ONLY "
                f"(signature byte-identical stub 10.4)."
            )
