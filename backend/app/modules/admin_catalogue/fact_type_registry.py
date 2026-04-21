"""Registry des fact_type autorises (FR17 — Story 10.4 squelette).

Country-agnostic par construction — aucun pays liste ici. Les referentiels
specifiques (ex. UEMOA, BCEAO) sont charges en base via `AdminMaturityRequirement`
et `Referential`, pas dans ce registry.

Epic 13 Story 13.1 pourra etendre cette liste OU basculer vers une table BDD
`admin_fact_types` (decision deferee). Story 10.4 fige le contrat : tuple
immutable de strings (protection contre mutation accidentelle).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [FR17] (registry), NFR covered: [NFR27, NFR62, NFR66].

Note CCC-6 (NFR-SOURCE-TRACKING) — **non applicable** : ce registre est
du code interne (tuple Python), pas une entite catalogue BDD. Les
`fact_type` sont des cles enum (identifiants de type de fait), pas des
references a des documents sources. Les `source_url` sont portees par
les entites BDD qui **utilisent** ces cles (`criteria`, `referentials`,
`admin_maturity_requirements`, ...). Story 10.11.
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
