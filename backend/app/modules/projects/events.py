"""Domain events emis par le module projects (D11 micro-Outbox).

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].

Les events listes ici seront inseres dans `domain_events` par Epic 11.
Story 10.10 livrera le worker APScheduler qui les consomme.

Payloads attendus (documentation uniquement MVP) :
- project.created : {project_id: UUID, company_id: UUID, name: str}
- project.status_changed : {project_id: UUID, from: str, to: str}
"""

from __future__ import annotations

from typing import Final, Literal

PROJECT_CREATED_EVENT_TYPE: Final[Literal["project.created"]] = "project.created"
PROJECT_STATUS_CHANGED_EVENT_TYPE: Final[Literal["project.status_changed"]] = (
    "project.status_changed"
)
