"""Add embedding_vec_v2 Voyage column (parallel to OpenAI v1) — Story 10.13

Revision ID: 031_add_embedding_vec_v2_voyage
Revises: 030_seed_sources_annexe_f
Create Date: 2026-04-21

Story 10.13 — migration parallèle v1+v2 (Q2 tranchée) :
  * ADD ``document_chunks.embedding_vec_v2 vector(1024)`` (Voyage voyage-3).
  * CREATE INDEX HNSW ``ix_document_chunks_embedding_v2_hnsw``.
  * CONSERVE la colonne v1 ``embedding vector(1536)`` (rollback garanti).

Le drop de la colonne v1 est DÉFÉRÉ à la migration 032 séparée (Story 20.X
post-validation qualité prod ≥ 3 mois) — cette migration est strictement
additive et donc 100 % reversible.
"""

from __future__ import annotations

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "031_add_embedding_vec_v2_voyage"
down_revision = "030_seed_sources_annexe_f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajout additif : colonne v2 + index HNSW v2. v1 intact."""
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding_vec_v2",
            pgvector.sqlalchemy.vector.VECTOR(dim=1024),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_document_chunks_embedding_v2_hnsw",
        "document_chunks",
        ["embedding_vec_v2"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding_vec_v2": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Rollback trivial : drop uniquement v2. v1 reste opérationnel.

    Piège documenté Story 10.13 §11 : si ``rembed_voyage_corpus.py`` a
    peuplé ``embedding_vec_v2`` avant downgrade, ces données sont
    irrémédiablement perdues. ``pg_dump -t document_chunks`` recommandé
    en pré-rollback prod.
    """
    # Note (LOW-1 post-review 2026-04-21) : ``postgresql_using``/``_with``/``_ops``
    # sont ignorés par ``op.drop_index`` (alembic les tolère silencieusement).
    # On les passe ici uniquement pour la symétrie visuelle avec ``upgrade()``
    # — simplifiable en ``op.drop_index("ix_document_chunks_embedding_v2_hnsw",
    # table_name="document_chunks")`` sans perte de comportement.
    op.drop_index(
        "ix_document_chunks_embedding_v2_hnsw",
        table_name="document_chunks",
        postgresql_using="hnsw",
    )
    op.drop_column("document_chunks", "embedding_vec_v2")
