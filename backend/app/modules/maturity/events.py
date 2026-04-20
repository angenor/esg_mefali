"""Domain events emis par le module maturity (D11 micro-Outbox).

Story 10.3 - module `maturity/` squelette (AC1 — preparation CCC-14).
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Les events listes ici seront inseres dans `domain_events` par Epic 12.
Story 10.10 livrera le worker APScheduler qui les consomme.

Payloads attendus (documentation uniquement MVP) :
- maturity.level_upgraded : {company_id, from_level_code, to_level_code, actor_id, reason}
- maturity.level_downgraded : {company_id, from_level_code, to_level_code, actor_id, reason, justification_text}
- maturity.formalization_plan_generated : {company_id, plan_id, current_level_id, target_level_id, step_count}
"""

from __future__ import annotations

from typing import Final, Literal

MATURITY_LEVEL_UPGRADED_EVENT_TYPE: Final[Literal["maturity.level_upgraded"]] = (
    "maturity.level_upgraded"
)
MATURITY_LEVEL_DOWNGRADED_EVENT_TYPE: Final[Literal["maturity.level_downgraded"]] = (
    "maturity.level_downgraded"
)
FORMALIZATION_PLAN_GENERATED_EVENT_TYPE: Final[
    Literal["maturity.formalization_plan_generated"]
] = "maturity.formalization_plan_generated"
