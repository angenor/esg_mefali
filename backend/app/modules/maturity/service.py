"""Service du module maturity (surface API consommee par Epic 12).

Story 10.3 - module `maturity/` squelette.
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Les 5 fonctions ci-dessous sont des stubs `NotImplementedError`. Epic 12
livrera la logique metier reelle (self-declaration, OCR validation,
FormalizationPlan pays-specifique, auto-reclassement).

**Anti-pattern God service (NFR64)** : toute lecture/ecriture sur les tables
`admin_maturity_levels`/`formalization_plans`/`admin_maturity_requirements`
doit passer par ces 5 fonctions — aucun `select(AdminMaturityLevel)` inline
dans les consommateurs externes (`formalization_plan_calculator`, OCR
validator, auto-reclassement handler, router Epic 12).

**NFR66 country-data-driven** : `get_requirements_for_country_level` est le
point d'entree data-driven FR13 — zero string pays hardcode cote Python.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.maturity.models import (
    AdminMaturityLevel,
    AdminMaturityRequirement,
    FormalizationPlan,
)

_SKELETON_MSG = "Story 10.3 skeleton — implemented in Epic 12 story 12-X"


# AC6 — surface d'API consommee par Epic 12.


async def declare_maturity_level(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    level_code: str,
    actor_user_id: uuid.UUID,
) -> FormalizationPlan | None:
    """Self-declarer le niveau de maturite d'une entreprise (stub Epic 12.1).

    Epic 12 Story 12.1 implementera : validation `level_code` contre
    `AdminMaturityLevel.code`, creation/mise a jour de `FormalizationPlan`,
    emission event `maturity.level_upgraded` ou `maturity.level_downgraded`
    via `domain_events` (CCC-14 D11 micro-Outbox).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def get_formalization_plan(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
) -> FormalizationPlan | None:
    """Recuperer le plan de formalisation d'une entreprise (stub Epic 12.3)."""
    raise NotImplementedError(_SKELETON_MSG)


async def list_published_levels(
    db: AsyncSession,
) -> list[AdminMaturityLevel]:
    """Lister les AdminMaturityLevel publies (stub Epic 12).

    Filtre `is_published = True` (admin workflow Story 10.4 + 10.12).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def get_requirements_for_country_level(
    db: AsyncSession,
    *,
    country: str,
    level_id: uuid.UUID,
) -> AdminMaturityRequirement | None:
    """Point d'entree data-driven FR13 — zero string pays hardcode cote Python.

    Epic 12.3 `FormalizationPlanCalculator.generate` appellera **exclusivement**
    cette fonction pour lire les requirements pays-specifiques. Tout
    hardcoding pays (e.g. `if country == "<pays>"`) en dur dans le code
    echoue le test NFR66
    (`test_country_data_driven_no_hardcoded_country_strings`) — feedback
    CI immediat.
    """
    raise NotImplementedError(_SKELETON_MSG)


async def create_formalization_plan(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    current_level_id: uuid.UUID,
    target_level_id: uuid.UUID,
    actions: list[dict],
) -> FormalizationPlan:
    """Creer un FormalizationPlan (stub Epic 12.3 — invoque par le Calculator)."""
    raise NotImplementedError(_SKELETON_MSG)
