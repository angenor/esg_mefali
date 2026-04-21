"""Add financing_chunks.embedding_vec_v2 Voyage column — Story 10.13 HIGH-3 patch

Revision ID: 032_add_financing_chunks_embedding_v2_voyage
Revises: 031_add_embedding_vec_v2_voyage
Create Date: 2026-04-21

Story 10.13 post-review HIGH-3 : la colonne ``financing_chunks.embedding`` est
figée ``Vector(1536)`` (OpenAI text-embedding-3-small legacy). Pour homogénéiser
le corpus RAG avec ``document_chunks.embedding_vec_v2`` (Voyage 1024 dim),
on ajoute ``embedding_vec_v2 Vector(1024)`` en parallèle (Q2 strategy byte-
identique migration 031).

Pas de DROP v1 ici — la coexistence garantit le rollback. Drop programmé dans
la même Story 20.X cleanup que 031 (post-validation qualité prod ≥ 3 mois).

Les consommateurs ``financing/service.py::search_financing_chunks`` et
``financing/seed.py`` consomment désormais ``get_embedding_provider()`` +
écrivent dans ``embedding_vec_v2``.
"""

from __future__ import annotations

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "032_add_financing_chunks_embedding_v2_voyage"
down_revision = "031_add_embedding_vec_v2_voyage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajout additif : colonne v2 + index HNSW v2. v1 intact."""
    op.add_column(
        "financing_chunks",
        sa.Column(
            "embedding_vec_v2",
            pgvector.sqlalchemy.vector.VECTOR(dim=1024),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_financing_chunks_embedding_v2_hnsw",
        "financing_chunks",
        ["embedding_vec_v2"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding_vec_v2": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Rollback trivial : drop uniquement v2. v1 reste opérationnel."""
    op.drop_index(
        "ix_financing_chunks_embedding_v2_hnsw",
        table_name="financing_chunks",
        postgresql_using="hnsw",
    )
    op.drop_column("financing_chunks", "embedding_vec_v2")
