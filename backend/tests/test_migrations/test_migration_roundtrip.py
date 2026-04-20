"""AC1 + AC2 + AC10 — round-trip upgrade/downgrade/upgrade sur PostgreSQL.

Story 10.1 migrations 020-027. Ces tests nécessitent un PostgreSQL de
test (TEST_ALEMBIC_URL). Skip auto si non disponible.
"""
from __future__ import annotations

import pytest
from alembic import command
from alembic.script import ScriptDirectory


pytestmark = pytest.mark.postgres


def _heads(cfg):
    return ScriptDirectory.from_config(cfg).get_heads()


def test_alembic_chain_linear_single_head(alembic_config):
    """AC1 — chaîne linéaire, un seul head = 027_outbox_prefill."""
    heads = tuple(_heads(alembic_config))
    assert heads == ("027_outbox_prefill",), f"heads multiples ou head inattendu: {heads}"


def test_upgrade_head_from_base(alembic_config):
    """AC1 — upgrade base → head applique toute la chaîne sans erreur."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_round_trip_all_migrations(alembic_config):
    """AC2 — downgrade base / upgrade head / downgrade 019 / upgrade head."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "019_manual_edits")
    command.upgrade(alembic_config, "head")


def test_downgrade_each_new_migration_individually(alembic_config):
    """AC2 — reversibilité fine : downgrade -1 pour chaque migration 020-027."""
    command.upgrade(alembic_config, "head")
    for target in (
        "026_catalogue_audit",
        "025_source_tracking",
        "024_rls_audit",
        "023_deliverables",
        "022_esg_3layers",
        "021_maturity",
        "020_projects",
        "019_manual_edits",
    ):
        command.downgrade(alembic_config, target)
    # Remonter
    command.upgrade(alembic_config, "head")
