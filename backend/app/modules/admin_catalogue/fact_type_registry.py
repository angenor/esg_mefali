"""Registry des fact_type autorises (FR17 — Story 10.4 squelette).

Country-agnostic par construction — aucun pays liste ici. Les referentiels
specifiques (ex. UEMOA, BCEAO) sont charges en base via `AdminMaturityRequirement`
et `Referential`, pas dans ce registry.

Epic 13 Story 13.1 pourra etendre cette liste OU basculer vers une table BDD
`admin_fact_types` (decision deferee). Story 10.4 fige le contrat : tuple
immutable de strings (protection contre mutation accidentelle).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [FR17] (registry), NFR covered: [NFR27, NFR62, NFR66].
"""

from __future__ import annotations

from typing import Final

FACT_TYPE_CATALOGUE: Final[tuple[str, ...]] = (
    "energy_consumption_kwh",
    "water_consumption_m3",
    "waste_tonnes",
    "co2_scope1_tonnes",
    "co2_scope2_tonnes",
    "co2_scope3_tonnes",
    "employees_count",
    "female_employees_ratio",
    "training_hours_per_employee",
    "governance_board_independence_ratio",
    "financial_revenue_xof",
    "informal_activity_share_pct",
)
