"""Domain events emis par le module admin_catalogue (D11 micro-Outbox).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].

Les events listes ici seront inseres dans `domain_events` par Epic 13.
Story 10.10 livrera le worker APScheduler qui les consomme.

Payloads attendus (documentation uniquement MVP) :
- catalogue.criterion_published : {criterion_id, actor_id, workflow_level, ts}
- catalogue.referential_published : {referential_id, actor_id, workflow_level, ts}
- catalogue.pack_published : {pack_id, actor_id, workflow_level, ts}
- catalogue.rule_published : {rule_id, criterion_id, actor_id, ts}
- catalogue.entity_retired : {entity_type, entity_id, actor_id, reason, ts}
"""

from __future__ import annotations

from typing import Final, Literal

CATALOGUE_CRITERION_PUBLISHED_EVENT_TYPE: Final[
    Literal["catalogue.criterion_published"]
] = "catalogue.criterion_published"
CATALOGUE_REFERENTIAL_PUBLISHED_EVENT_TYPE: Final[
    Literal["catalogue.referential_published"]
] = "catalogue.referential_published"
CATALOGUE_PACK_PUBLISHED_EVENT_TYPE: Final[
    Literal["catalogue.pack_published"]
] = "catalogue.pack_published"
CATALOGUE_RULE_PUBLISHED_EVENT_TYPE: Final[
    Literal["catalogue.rule_published"]
] = "catalogue.rule_published"
CATALOGUE_ENTITY_RETIRED_EVENT_TYPE: Final[
    Literal["catalogue.entity_retired"]
] = "catalogue.entity_retired"
