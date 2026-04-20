"""AC1 + Q2 arbitrage — backfill piloté fund_applications.project_id.

Vérifie que le backfill crée bien un project "legacy" par user distinct
de fund_applications et remplit project_id (NOT NULL + FK) lors de
l'upgrade 020.
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import text


pytestmark = pytest.mark.postgres


def test_backfill_project_id_for_legacy_fund_applications(
    alembic_config, sync_engine
):
    """Legacy fund_applications (pré-020) reçoit project_id backfillé."""
    # 1. Monter d'abord jusqu'à 019 (DB vide après reset fixture)
    command.upgrade(alembic_config, "019_manual_edits")

    user_id = uuid.uuid4()
    fund_id = uuid.uuid4()
    fa_id = uuid.uuid4()

    # 2. Insérer user + fund + fund_application legacy (état 019)
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, full_name, "
                "company_name, is_active) VALUES "
                "(:id, :em, 'h', 'U', 'C', true)"
            ),
            {"id": user_id, "em": f"u-{user_id.hex[:6]}@x.com"},
        )
        conn.execute(
            text(
                "INSERT INTO funds (id, name, organization, fund_type, "
                "description, access_type) VALUES "
                "(:id, 'F', 'Org', 'international', 'D', 'direct')"
            ),
            {"id": fund_id},
        )
        conn.execute(
            text(
                "INSERT INTO fund_applications (id, user_id, fund_id, "
                "target_type, status) VALUES "
                "(:id, :u, :f, 'fund_direct', 'draft')"
            ),
            {"id": fa_id, "u": user_id, "f": fund_id},
        )

    # 3. Upgrade à 020 : backfill doit remplir project_id
    command.upgrade(alembic_config, "020_projects")

    with sync_engine.connect() as conn:
        project_id = conn.execute(
            text("SELECT project_id FROM fund_applications WHERE id = :id"),
            {"id": fa_id},
        ).scalar()
    assert project_id is not None, (
        "project_id non backfillé — Q2 arbitrage : NOT NULL avec backfill piloté"
    )

    # 4. Nettoyage : remonter à head et supprimer user (CASCADE)
    command.upgrade(alembic_config, "head")
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
