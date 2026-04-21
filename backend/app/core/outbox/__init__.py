"""Micro-Outbox pattern (Story 10.10).

Module transversal livrant la plomberie événementielle D11 :

- ``writer.write_domain_event`` : insère un event dans la **transaction
  courante du caller** (atomicité CCC-14 garantie, pas de commit interne).
- ``worker.process_outbox_batch`` : consomme les events via
  ``SELECT ... FOR UPDATE SKIP LOCKED`` (multi-process safe, PostgreSQL).
- ``worker.purge_expired_prefill_drafts`` : 2ᵉ job APScheduler (1 h)
  co-localisé (MEDIUM-10.1-5 absorbé).
- ``handlers.EVENT_HANDLERS`` : registre ``tuple[HandlerEntry, ...]``
  frozen (pattern CCC-9, Story 10.8).

Voir ``docs/CODEMAPS/outbox.md`` pour le contrat complet.
"""

from app.core.outbox.handlers import (
    EVENT_HANDLERS,
    HandlerEntry,
    HandlerResult,
    dispatch_event,
)
from app.core.outbox.worker import (
    BACKOFF_SCHEDULE,
    MAX_RETRIES,
    process_outbox_batch,
    purge_expired_prefill_drafts,
    start_outbox_scheduler,
    stop_outbox_scheduler,
)
from app.core.outbox.writer import write_domain_event

__all__ = [
    "BACKOFF_SCHEDULE",
    "EVENT_HANDLERS",
    "HandlerEntry",
    "HandlerResult",
    "MAX_RETRIES",
    "dispatch_event",
    "process_outbox_batch",
    "purge_expired_prefill_drafts",
    "start_outbox_scheduler",
    "stop_outbox_scheduler",
    "write_domain_event",
]
