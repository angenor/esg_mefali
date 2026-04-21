"""Test CCC-14 : atomicite transaction `record_audit_event` (Story 10.12 AC6).

Verifie que l'insert audit trail et la mutation metier partagent la meme
transaction ORM — rollback caller supprime la row audit (pas d'orphelin).
Round-trip observable (regle d'or 10.5) : post-flush meme session = row
visible ; post-rollback session fraiche = 0 row.

PostgreSQL-only car l'isolation MVCC + la consistence de `ts` server-default
micro-precision sont indispensables pour verifier le comportement attendu.
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import select

from app.modules.admin_catalogue.enums import (
    CatalogueActionEnum,
    WorkflowLevelEnum,
)
from app.modules.admin_catalogue.models import AdminCatalogueAuditTrail
from app.modules.admin_catalogue.service import record_audit_event


pytestmark = [
    pytest.mark.postgres,
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"),
        reason="Requires PostgreSQL (tx isolation MVCC + micro-precision ts)",
    ),
]


async def test_record_audit_event_inserts_row_same_transaction_rolled_back(
    db_session, seed_admin_user
):
    """Round-trip : post-flush meme session = row visible ; post-rollback = 0 row.

    Invariant CCC-14 : `record_audit_event` n'emet PAS `commit`. Il utilise
    la transaction en cours (boundary au caller). Si le caller rollback, la
    row audit disparait (pas d'audit orphelin).
    """
    actor_id = seed_admin_user.id
    entity_id = uuid.uuid4()

    # Phase 1 : INSERT dans la transaction courante (pas commit)
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
        changes_after={"init": True},
        correlation_id=uuid.uuid4(),
    )
    assert entity.id is not None

    # Observabilite : meme session, post-flush pre-commit, retourne la row
    stmt = select(AdminCatalogueAuditTrail).where(
        AdminCatalogueAuditTrail.entity_id == entity_id
    )
    result = await db_session.execute(stmt)
    assert len(result.scalars().all()) == 1

    # Phase 2 : rollback caller
    await db_session.rollback()

    # Phase 3 : session fraiche -> 0 row (transaction rolled back)
    # On ne peut pas creer de session ici sans factory partagee. A defaut, on
    # reutilise la session apres rollback : PostgreSQL isole les tx donc la
    # meme session post-rollback ne voit plus la row (la tx a ete annulee).
    result = await db_session.execute(stmt)
    assert len(result.scalars().all()) == 0
