"""CLI batch re-embedding — Story 10.13 AC5.

Remplit ``document_chunks.embedding_vec_v2`` (Voyage voyage-3 1024 dim)
par batch depuis les chunks existants dont la colonne v2 est NULL.

Idempotent : ``WHERE embedding_vec_v2 IS NULL`` reprend au point d'arrêt.
Sync CLI one-shot (Q3 tranchée pas Outbox async overkill MVP).

Usage::

    python backend/scripts/rembed_voyage_corpus.py --batch-size 100
    python backend/scripts/rembed_voyage_corpus.py --dry-run --limit 10
    python backend/scripts/rembed_voyage_corpus.py --resume-from <chunk_uuid>

Exit codes :
    0 : succès (zéro chunk restant NULL).
    1 : erreur non-récupérable (provider fatal, DB down).
    2 : interrompu par l'utilisateur (Ctrl+C).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
import uuid
from typing import Final

logger = logging.getLogger("rembed_voyage_corpus")

DEFAULT_BATCH_SIZE: Final[int] = 100
BATCH_SIZE_MIN: Final[int] = 1
BATCH_SIZE_MAX: Final[int] = 500


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-embed document_chunks via Voyage API (Story 10.13)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Chunks par batch (défaut {DEFAULT_BATCH_SIZE}, bornes [{BATCH_SIZE_MIN}, {BATCH_SIZE_MAX}])",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Plafond total de chunks à traiter (dev-only).",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="UUID de chunk à partir duquel reprendre (trié par id ASC).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ne fait aucun UPDATE — affiche seulement les chunks candidats.",
    )
    return parser.parse_args(argv)


def _validate_args(args: argparse.Namespace) -> None:
    if not (BATCH_SIZE_MIN <= args.batch_size <= BATCH_SIZE_MAX):
        raise SystemExit(
            f"--batch-size hors bornes [{BATCH_SIZE_MIN}, {BATCH_SIZE_MAX}]"
        )
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit doit être > 0")
    if args.resume_from is not None:
        try:
            uuid.UUID(args.resume_from)
        except ValueError as exc:
            raise SystemExit(f"--resume-from invalide: {exc}") from exc


async def _fetch_batch(db, *, batch_size: int, resume_from: uuid.UUID | None):
    """Sélectionne les prochains chunks v2-NULL (ordre id ASC)."""
    from sqlalchemy import select

    from app.models.document import DocumentChunk

    stmt = (
        select(DocumentChunk.id, DocumentChunk.content)
        .where(DocumentChunk.embedding_vec_v2.is_(None))
        .order_by(DocumentChunk.id)
        .limit(batch_size)
    )
    if resume_from is not None:
        stmt = stmt.where(DocumentChunk.id > resume_from)
    result = await db.execute(stmt)
    return list(result.all())


async def _update_chunk_embedding(db, *, chunk_id: uuid.UUID, vector: list[float]) -> None:
    """UPDATE unitaire — une ligne par chunk pour éviter la rétention en RAM."""
    from sqlalchemy import update

    from app.models.document import DocumentChunk

    stmt = (
        update(DocumentChunk)
        .where(DocumentChunk.id == chunk_id)
        .values(embedding_vec_v2=vector)
    )
    await db.execute(stmt)


def _emit_progress(event: dict) -> None:
    """Log JSON structuré (pattern 10.10 — logger avec extra="metric")."""
    logger.info(json.dumps(event, default=str), extra={"metric": event.get("event", "rembed")})


async def _run(args: argparse.Namespace) -> int:
    from app.core.database import async_session
    from app.core.embeddings import EmbeddingError, get_embedding_provider

    provider = get_embedding_provider()
    processed = 0
    resume_from = uuid.UUID(args.resume_from) if args.resume_from else None

    async with async_session() as db:
        while True:
            if args.limit is not None and processed >= args.limit:
                break

            remaining = args.batch_size
            if args.limit is not None:
                remaining = min(remaining, args.limit - processed)

            batch = await _fetch_batch(
                db,
                batch_size=remaining,
                resume_from=resume_from,
            )
            if not batch:
                break

            if args.dry_run:
                _emit_progress({
                    "event": "embedding_batch_dry_run",
                    "batch_size": len(batch),
                    "first_chunk_id": str(batch[0][0]),
                })
                processed += len(batch)
                resume_from = batch[-1][0]
                continue

            texts = [row[1] for row in batch]
            chunk_ids = [row[0] for row in batch]
            started = time.perf_counter()
            try:
                vectors = await provider.embed(texts)
            except EmbeddingError as exc:
                logger.error(
                    "Erreur provider embedding (provider=%s): %s",
                    provider.name,
                    exc,
                )
                return 1

            for chunk_id, vector in zip(chunk_ids, vectors):
                await _update_chunk_embedding(
                    db, chunk_id=chunk_id, vector=vector
                )

            await db.commit()

            elapsed_ms = int((time.perf_counter() - started) * 1000)
            _emit_progress({
                "event": "embedding_batch_progress",
                "processed": len(batch),
                "total_processed": processed + len(batch),
                "batch_duration_ms": elapsed_ms,
                "provider": provider.name,
                "model": provider.model,
            })
            processed += len(batch)
            resume_from = chunk_ids[-1]

    _emit_progress({
        "event": "embedding_corpus_complete",
        "total_processed": processed,
        "provider": provider.name,
    })
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args(argv)
    _validate_args(args)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.warning("Interrompu par l'utilisateur (SIGINT)")
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
