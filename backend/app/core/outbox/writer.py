"""Writer Outbox — insertion transactionnelle (Story 10.10 AC1).

Contrat CCC-14 :
    L'appel ``write_domain_event(db, ...)`` **ne commit pas**. La décision
    de commit appartient au caller (transaction métier). Si le caller
    `raise` après l'appel, la transaction rollback propage à l'event.

Validations fail-fast :
    - ``event_type`` : regex ``^[a-z_]+\\.[a-z_]+$`` (ex. ``project.created``).
    - ``payload`` : ``json.dumps(payload, default=str)`` dry-run pour détecter
      toute structure non JSON-sérialisable (datetimes naïves, sets, etc.).

Aucune écriture ``domain_events`` ailleurs que dans ce module
(règle d'or 10.5 — scan CI vérifie zéro duplication).
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent


_EVENT_TYPE_RE = re.compile(r"^[a-z_]+\.[a-z_]+$")


def _validate_event_type(event_type: str) -> None:
    """Valide le format ``<entity>.<verb_past>`` (architecture.md §D11)."""
    if not isinstance(event_type, str) or not _EVENT_TYPE_RE.match(event_type):
        raise ValueError(
            f"Invalid event_type {event_type!r}: must match "
            f"'^[a-z_]+\\.[a-z_]+$' (ex. 'project.created')."
        )


def _validate_payload_json_serializable(payload: dict[str, Any]) -> None:
    """Dry-run ``json.dumps`` pour fail-fast si payload non sérialisable.

    Les ``datetime`` naïves (sans timezone) sont rejetées : passer par
    ``dt.isoformat()`` côté caller pour garantir l'auditabilité des logs.
    """
    if not isinstance(payload, dict):
        raise ValueError(
            f"payload must be a dict (JSON object), got {type(payload).__name__}"
        )
    try:
        # default=str couvrirait accidentellement les datetime naïves :
        # on veut que le caller explicite le format (UTC isoformat).
        json.dumps(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"payload not JSON-serializable: {exc}. "
            f"Hint: convert datetimes to ISO strings, sets to lists."
        ) from exc


async def write_domain_event(
    db: AsyncSession,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any],
) -> DomainEvent:
    """Insère un event dans la transaction courante, sans commit interne.

    Args:
        db: session SQLAlchemy async **déjà dans une transaction** (ouverte
            par le caller ou auto-begin).
        event_type: format ``<entity>.<verb_past>`` (ex. ``project.created``).
        aggregate_type: type de l'agrégat source (ex. ``"project"``).
        aggregate_id: identifiant UUID de l'agrégat.
        payload: dict JSON-sérialisable (datetime → isoformat côté caller).

    Returns:
        L'instance ``DomainEvent`` flushée (``id`` UUID généré Python).

    Raises:
        ValueError: si ``event_type`` ou ``payload`` ne passent pas les
            validations fail-fast.

    Atomicité CCC-14 :
        Aucun ``db.commit()`` n'est appelé — la décision de commit appartient
        strictement au caller. Un rollback sur la transaction métier propage
        à la ligne insérée (atomicité byte-identique aux INSERT SQL directs).
    """
    _validate_event_type(event_type)
    _validate_payload_json_serializable(payload)

    event = DomainEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        status="pending",
        retry_count=0,
    )
    db.add(event)
    await db.flush()
    return event
