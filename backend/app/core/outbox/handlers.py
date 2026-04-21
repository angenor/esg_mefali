"""Registre des handlers Outbox (Story 10.10 AC3 — pattern CCC-9 Story 10.8).

``EVENT_HANDLERS`` est un **tuple frozen** (byte-identique au pattern
``INSTRUCTION_REGISTRY`` de ``app.prompts.registry``) : append-only à
compile-time, pas de décorateur magique, pas de side-effect à l'import.

Ajouter un nouveau handler = 1 bloc ``HandlerEntry(...)`` dans le tuple.
Le worker y accède en lecture seule via ``dispatch_event``.

Contrat d'un handler :
    ``async def handler(event: DomainEvent, db: AsyncSession) -> None``

    - **Idempotent** : rejouer le même event = même résultat (pas d'effet
      de bord cumulatif) — le worker peut re-consommer après retry.
    - ``raise Exception`` → retry (retry_count += 1, next_retry_at fixé).
    - ``return`` (ou ``None``) → succès (status='processed').
    - ``raise BaseException`` (``SystemExit`` / ``KeyboardInterrupt``) →
      propage au scheduler (tue le process — documenté comme anti-pattern).

Consommateurs prévus (Epic 13-14) :
    - ``fact_updated`` → invalidation ``referential_verdicts`` AR-D3 (Epic 13).
    - ``criterion_rule_updated`` → idem.
    - ``fund_updated`` → REFRESH MATERIALIZED VIEW ``mv_fund_matching_cube``
      (Epic 14, MEDIUM-10.1-6).
    - ``fund_application_submitted`` → notification chat PDF (Story 9.12).
    - ``referential_version_published`` → FR34 notifications opt-in.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


HandlerFn = Callable[[DomainEvent, AsyncSession], Awaitable[None]]


@dataclass(frozen=True)
class HandlerEntry:
    """Entrée immutable du registre des handlers Outbox.

    Attributes:
        event_type: identifiant `<entity>.<verb_past>` (ex. `project.created`).
        handler: coroutine idempotente invoquée avec ``(event, db)``.
        description: documentation courte (audit + grep).
    """

    event_type: str
    handler: HandlerFn
    description: str


@dataclass(frozen=True)
class HandlerResult:
    """Résultat d'un dispatch — consommé par ``worker.process_outbox_batch``.

    ``status`` ∈ {``processed``, ``retry``, ``failed``, ``unknown_handler``}.
    """

    status: str
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Handlers concrets (dummy uniquement — les handlers métier arrivent Epic 13-14)
# ---------------------------------------------------------------------------


async def noop_handler(event: DomainEvent, db: AsyncSession) -> None:
    """Handler test-only : log + no-op. Idempotent par construction.

    Utilisé exclusivement par les tests E2E Story 10.10 (``noop.test``).
    Jamais référencé par du code métier.
    """
    logger.debug(
        "noop handler invoked",
        extra={
            "metric": "outbox_noop_handler",
            "event_id": str(event.id),
            "event_type": event.event_type,
        },
    )


# ---------------------------------------------------------------------------
# Registre frozen (pattern CCC-9 Story 10.8 — byte-identique INSTRUCTION_REGISTRY)
# ---------------------------------------------------------------------------


EVENT_HANDLERS: Final[tuple[HandlerEntry, ...]] = (
    HandlerEntry(
        event_type="noop.test",
        handler=noop_handler,
        description=(
            "Handler test idempotent — log + no-op. Utilisé par les tests "
            "E2E Story 10.10. Aucun handler métier ne doit utiliser ce type."
        ),
    ),
    # Epic 13 ajoutera ici :
    #   HandlerEntry(event_type="fact_updated", handler=..., description="...")
    #   HandlerEntry(event_type="criterion_rule_updated", handler=..., ...)
    # Epic 14 ajoutera :
    #   HandlerEntry(event_type="fund_updated", handler=..., ...)
    #   HandlerEntry(event_type="intermediary_updated", handler=..., ...)
)


def _validate_unique_event_types() -> None:
    """Fail-at-import si un ``event_type`` est dupliqué dans EVENT_HANDLERS.

    Garde-fou cohérence CCC-9 (pattern Story 10.8 `_validate_unique_names`).
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in EVENT_HANDLERS:
        if entry.event_type in seen:
            duplicates.append(entry.event_type)
        seen.add(entry.event_type)
    if duplicates:
        raise RuntimeError(
            f"Duplicate event_type(s) in EVENT_HANDLERS: {duplicates}. "
            f"Each event_type must map to exactly one handler."
        )


# Exécuté à l'import — fail-fast en cas de duplication.
_validate_unique_event_types()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


async def dispatch_event(event: DomainEvent, db: AsyncSession) -> HandlerResult:
    """Dispatche un event vers son handler via scan linéaire du tuple.

    O(n) avec n < 50 events prévus MVP — acceptable vs complexité dict
    mutable (sécurité > performance à cette échelle).

    Fail-fast :
        - ``event_type`` absent → ``HandlerResult(status='unknown_handler')``
          (pas de retry, AC5 Epic).
        - handler raise ``Exception`` → ``HandlerResult(status='retry')`` +
          ``error_message = str(exc) + ':' + type(exc).__name__`` (max 500
          chars tronqué par le worker).
        - handler raise ``BaseException`` (SystemExit, KeyboardInterrupt) →
          propage au scheduler (tue le process, documenté §Pièges).

    Note C1 9.7 : le ``try/except Exception`` est **local** (défense en
    profondeur isolée au handler individuel), jamais autour du batch entier.
    """
    for entry in EVENT_HANDLERS:
        if entry.event_type == event.event_type:
            try:
                await entry.handler(event, db)
            except Exception as exc:  # noqa: BLE001 — local handler isolation
                error_detail = f"{type(exc).__name__}: {exc}"
                return HandlerResult(
                    status="retry",
                    error_message=error_detail[:500],
                )
            return HandlerResult(status="processed")

    return HandlerResult(
        status="unknown_handler",
        error_message=f"Unknown event_type: {event.event_type!r}",
    )
