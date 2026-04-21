"""Worker Outbox APScheduler + FOR UPDATE SKIP LOCKED (Story 10.10 AC2/AC4/AC5).

Pattern architecture.md §D11 :
    - ``AsyncIOScheduler`` démarré au lifespan startup, arrêté au shutdown
      (``scheduler.shutdown(wait=True)`` avant ``engine.dispose()``).
    - Job ``process_outbox_batch`` : intervalle configurable (Settings,
      défaut 30 s), ``max_instances=1`` anti-overlap, ``coalesce=True``,
      ``timezone="UTC"`` explicite (NFR37 anti-drift).
    - Query verrou row-level ``SELECT ... FOR UPDATE SKIP LOCKED`` via
      SQLAlchemy ``.with_for_update(skip_locked=True)`` — multi-process
      safe sans Redis.
    - Retry exponentiel ``BACKOFF_SCHEDULE = (30, 120, 600)`` secondes.
      ``next_retry_at`` fixé côté applicatif (``now() + delta``).
    - Cap applicatif ``MAX_RETRIES = 3`` (défense en profondeur vs
      contrainte DB ``retry_count <= 5``).
    - Fail-fast ``unknown_handler`` : pas de retry (AC5 Epic).

Anti-patterns (voir ``docs/CODEMAPS/outbox.md §5 Pièges``) :
    - ``try/except Exception`` autour du batch entier (C1 9.7) : **interdit**.
      Le try/except est local dans ``dispatch_event``, isolé à l'appel handler.
    - ``payload`` entier dans les logs : **interdit** (NFR18). Seul
      ``payload_keys`` est loggué.
    - ``now()`` dans un index partiel PostgreSQL : non-IMMUTABLE refusé.
      Le filtre vit dans la query worker, pas dans le DDL.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Final

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import settings
from app.core.outbox.handlers import dispatch_event
from app.models.domain_event import DomainEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


#: Retry schedule architecture.md §D11 (30 s, 2 min, 10 min).
#: Distinct du pattern ``with_retry`` LLM (``[1, 3, 9]``, NFR75) : les handlers
#: Outbox retry des erreurs BDD transientes (connection drop, deadlock) sur
#: fenêtres 30-600 s, pas des retries synchrones courts < 10 s.
BACKOFF_SCHEDULE: Final[tuple[int, ...]] = (30, 120, 600)

#: Cap applicatif — après ``MAX_RETRIES``, l'event est marqué ``failed``.
#: Défense en profondeur vs contrainte DB ``retry_count <= 5``.
MAX_RETRIES: Final[int] = 3

#: Taille maximale d'un batch (protège mémoire + verrous row-level).
BATCH_SIZE: Final[int] = 100

#: Intervalle purge ``prefill_drafts`` (MEDIUM-10.1-5 absorbé).
PREFILL_PURGE_INTERVAL_S: Final[int] = 3600

#: Batch size purge ``prefill_drafts``.
PREFILL_PURGE_BATCH_SIZE: Final[int] = 500


def _utcnow() -> datetime:
    """Timestamp UTC timezone-aware (NFR37 anti-drift)."""
    return datetime.now(timezone.utc)


def _truncate_error(message: str, limit: int = 500) -> str:
    """Tronque un message d'erreur à ``limit`` chars (colonne ``error_message``)."""
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


# ---------------------------------------------------------------------------
# Batch processing (AC2 + AC4 + AC5)
# ---------------------------------------------------------------------------


async def process_outbox_batch(engine: AsyncEngine) -> None:
    """Consomme un batch d'events ``pending`` éligibles.

    Flow :
        1. Ouvre une session dédiée (session pool released en ``finally``
           via ``async with``).
        2. ``SELECT ... FOR UPDATE SKIP LOCKED`` sur les events :
           - ``processed_at IS NULL``
           - ``retry_count < MAX_RETRIES``
           - ``status IN ('pending',)``
           - ``next_retry_at IS NULL OR next_retry_at <= now()``
        3. Pour chaque event : dispatch handler → update status/retry_count/
           next_retry_at selon le résultat + log structuré JSON.
        4. Commit (release des verrous row-level).

    C1 9.7 : **pas de ``try/except Exception`` autour du batch**. Une erreur
    BDD doit remonter au scheduler → restart propre par l'orchestrateur.
    """
    async with AsyncSession(engine, expire_on_commit=False) as db:
        stmt = (
            select(DomainEvent)
            .where(
                DomainEvent.processed_at.is_(None),
                DomainEvent.retry_count < MAX_RETRIES,
                DomainEvent.status == "pending",
                or_(
                    DomainEvent.next_retry_at.is_(None),
                    DomainEvent.next_retry_at <= func.now(),
                ),
            )
            .order_by(DomainEvent.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        result = await db.execute(stmt)
        events = list(result.scalars().all())

        if not events:
            await db.commit()
            return

        for event in events:
            await _process_single_event(db, event)

        await db.commit()


async def _process_single_event(db: AsyncSession, event: DomainEvent) -> None:
    """Dispatche un event + update sa ligne + log structuré."""
    start_monotonic = time.monotonic()
    result = await dispatch_event(event, db)
    duration_ms = int((time.monotonic() - start_monotonic) * 1000)

    attempt = event.retry_count + 1

    # Payload keys uniquement (NFR18 anti-PII).
    payload_keys = sorted(event.payload.keys()) if isinstance(event.payload, dict) else []

    log_extra_base = {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": str(event.aggregate_id),
        "attempt": attempt,
        "duration_ms": duration_ms,
        "payload_keys": payload_keys,
    }

    if result.status == "processed":
        event.status = "processed"
        event.processed_at = _utcnow()
        event.error_message = None
        logger.info(
            "outbox event processed",
            extra={
                **log_extra_base,
                "metric": "outbox_event_processed",
                "status": "processed",
                "error_message": None,
            },
        )
        return

    if result.status == "unknown_handler":
        # Fail-fast (AC5 Epic) — pas de retry, l'event sort de l'index partiel.
        event.status = "unknown_handler"
        event.processed_at = _utcnow()
        event.error_message = _truncate_error(result.error_message or "")
        logger.error(
            "outbox event unknown_handler",
            extra={
                **log_extra_base,
                "metric": "outbox_event_unknown_handler",
                "status": "unknown_handler",
                "error_message": event.error_message,
            },
        )
        return

    # result.status == "retry" — handler a raise Exception.
    event.retry_count = event.retry_count + 1
    event.error_message = _truncate_error(result.error_message or "")

    if event.retry_count >= MAX_RETRIES:
        event.status = "failed"
        event.processed_at = _utcnow()
        logger.error(
            "outbox event failed (max retries exhausted)",
            extra={
                **log_extra_base,
                "metric": "outbox_event_failed",
                "status": "failed",
                "attempt": event.retry_count,
                "error_message": event.error_message,
            },
        )
        return

    # Retry scheduled : calcul next_retry_at selon BACKOFF_SCHEDULE.
    backoff_index = event.retry_count - 1
    backoff_index = min(backoff_index, len(BACKOFF_SCHEDULE) - 1)
    delta_s = BACKOFF_SCHEDULE[backoff_index]
    event.next_retry_at = _utcnow() + timedelta(seconds=delta_s)
    logger.warning(
        "outbox event retry scheduled",
        extra={
            **log_extra_base,
            "metric": "outbox_event_retry",
            "status": "retry",
            "attempt": event.retry_count,
            "next_retry_at": event.next_retry_at.isoformat(),
            "error_message": event.error_message,
        },
    )


# ---------------------------------------------------------------------------
# Purge prefill_drafts (MEDIUM-10.1-5 absorbé — AC9 bonus)
# ---------------------------------------------------------------------------


async def purge_expired_prefill_drafts(engine: AsyncEngine) -> None:
    """Supprime les ``prefill_drafts`` expirés (batch ``PREFILL_PURGE_BATCH_SIZE``).

    Co-localisé avec le scheduler Outbox pour éviter 2 schedulers concurrents
    dans le même process (anti-race, NFR37).
    """
    async with AsyncSession(engine, expire_on_commit=False) as db:
        # On utilise une sous-requête LIMIT pour borner la taille du batch
        # (sinon une purge géante bloquerait la boucle).
        subquery = text(
            """
            DELETE FROM prefill_drafts
            WHERE id IN (
                SELECT id FROM prefill_drafts
                WHERE expires_at < now()
                LIMIT :batch_size
            )
            """
        )
        result = await db.execute(subquery, {"batch_size": PREFILL_PURGE_BATCH_SIZE})
        await db.commit()

        count = result.rowcount if result.rowcount is not None else 0
        if count > 0:
            logger.info(
                "prefill_drafts purged",
                extra={"metric": "prefill_drafts_purged", "count": count},
            )


# ---------------------------------------------------------------------------
# Scheduler lifecycle (AC2 + AC6)
# ---------------------------------------------------------------------------


def start_outbox_scheduler(engine: AsyncEngine) -> AsyncIOScheduler | None:
    """Instancie et démarre l'``AsyncIOScheduler`` avec 2 jobs.

    Returns:
        Le scheduler démarré, ou ``None`` si ``DOMAIN_EVENTS_WORKER_ENABLED=false``.
    """
    if not settings.domain_events_worker_enabled:
        logger.warning(
            "Worker Outbox désactivé (DOMAIN_EVENTS_WORKER_ENABLED=false) — "
            "events s'accumulent en 'pending' (debug DEV)."
        )
        return None

    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        process_outbox_batch,
        trigger=IntervalTrigger(seconds=settings.domain_events_worker_interval_s),
        args=[engine],
        id="outbox_batch_worker",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        purge_expired_prefill_drafts,
        trigger=IntervalTrigger(seconds=PREFILL_PURGE_INTERVAL_S),
        args=[engine],
        id="prefill_drafts_purge",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Outbox scheduler started",
        extra={
            "metric": "outbox_scheduler_started",
            "outbox_interval_s": settings.domain_events_worker_interval_s,
            "purge_interval_s": PREFILL_PURGE_INTERVAL_S,
        },
    )
    return scheduler


async def stop_outbox_scheduler(scheduler: AsyncIOScheduler | None) -> None:
    """Arrêt propre du scheduler (``shutdown(wait=True)`` — jobs en cours finalisés)."""
    if scheduler is None:
        return
    scheduler.shutdown(wait=True)
    logger.info("Outbox scheduler stopped", extra={"metric": "outbox_scheduler_stopped"})
