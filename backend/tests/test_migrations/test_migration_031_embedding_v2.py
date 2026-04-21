"""Story 10.13 — tests migration 031 embedding_vec_v2 (@pytest.mark.postgres).

AC4 : upgrade ajoute colonne + index HNSW v2 sans toucher v1, downgrade
supprime v2 uniquement. Round-trip reversible.
"""

from __future__ import annotations

import pytest
from alembic import command
from sqlalchemy import text

pytestmark = pytest.mark.postgres


def test_migration_031_upgrade_adds_column_and_index_v2(
    alembic_config, sync_engine
):
    """AC4 — upgrade 031 ajoute embedding_vec_v2 Vector(1024) + index HNSW v2."""
    command.upgrade(alembic_config, "031_add_embedding_vec_v2_voyage")

    with sync_engine.connect() as conn:
        # Colonne v2 présente ?
        columns = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'document_chunks' "
                "AND column_name IN ('embedding', 'embedding_vec_v2')"
            )
        ).fetchall()
        names = {r[0] for r in columns}
        assert "embedding" in names, "v1 devrait être conservée (Q2 parallel)"
        assert "embedding_vec_v2" in names, "v2 devrait être ajoutée"

        # Index HNSW v2 présent ?
        indexes = conn.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'document_chunks'"
            )
        ).fetchall()
        idx_names = {r[0] for r in indexes}
        assert "ix_document_chunks_embedding_hnsw" in idx_names, "v1 index"
        assert "ix_document_chunks_embedding_v2_hnsw" in idx_names, "v2 index"


def test_migration_031_downgrade_removes_v2_only(alembic_config, sync_engine):
    """AC4 — downgrade 031 drop v2, conserve v1 intact (rollback garanti)."""
    command.upgrade(alembic_config, "031_add_embedding_vec_v2_voyage")
    command.downgrade(alembic_config, "030_seed_sources_annexe_f")

    with sync_engine.connect() as conn:
        columns = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'document_chunks' "
                "AND column_name IN ('embedding', 'embedding_vec_v2')"
            )
        ).fetchall()
        names = {r[0] for r in columns}
        assert "embedding" in names, "v1 doit être conservée au downgrade"
        assert "embedding_vec_v2" not in names, "v2 doit être droppée"


def test_migration_031_roundtrip_upgrade_downgrade_upgrade(
    alembic_config, sync_engine
):
    """AC4 — round-trip complet (NFR50 testabilité migrations)."""
    command.upgrade(alembic_config, "031_add_embedding_vec_v2_voyage")
    command.downgrade(alembic_config, "030_seed_sources_annexe_f")
    command.upgrade(alembic_config, "031_add_embedding_vec_v2_voyage")

    with sync_engine.connect() as conn:
        columns = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'document_chunks' "
                "AND column_name = 'embedding_vec_v2'"
            )
        ).fetchall()
        assert len(columns) == 1
