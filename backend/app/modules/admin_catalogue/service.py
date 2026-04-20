"""Service du module admin_catalogue (surface API Epic 13 + Story 10.12).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].

**7 fonctions exposees** (1 effective + 6 stubs `NotImplementedError`) :
- `list_fact_types` (effective — retourne le registry FR17).
- `create_criterion` (stub Epic 13.1).
- `create_referential` (stub Epic 13.2).
- `create_pack` (stub Epic 13.3).
- `create_derivation_rule` (stub Epic 13.1bis).
- `record_audit_event` (stub Story 10.12 — point d'entree unique audit trail).
- `transition_workflow_state` (stub Epic 13.8b/c — state machine peer review).

**Anti-pattern God service (NFR64)** : toute lecture/ecriture sur les tables
`criteria`/`referentials`/`packs`/`criterion_derivation_rules`/
`admin_catalogue_audit_trail` doit passer par ces 7 fonctions — aucun
`select(Criterion)` inline dans les consommateurs externes (router Epic 13,
handler audit Story 10.12, workflow state machine 13.8b/c).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin_catalogue.enums import (
    CatalogueActionEnum,
    NodeStateEnum,
    WorkflowLevelEnum,
)
from app.modules.admin_catalogue.fact_type_registry import (
    FACT_TYPE_CATALOGUE,
)
from app.modules.admin_catalogue.models import (
    AdminCatalogueAuditTrail,
    Criterion,
    CriterionDerivationRule,
    Pack,
    Referential,
)

_SKELETON_MSG = (
    "Story 10.4 skeleton — implemented in Epic 13 story 13-X / Story 10.12"
)


async def list_fact_types() -> list[str]:
    """Retourner la liste des fact_type autorises (FR17 — **effective**).

    Seule fonction non-stub du service MVP. Lecture du registry immutable
    `FACT_TYPE_CATALOGUE` (tuple) converti en `list` pour serialisation
    Pydantic.
    """
    return list(FACT_TYPE_CATALOGUE)


async def create_criterion(
    db: AsyncSession,
    *,
    code: str,
    label_fr: str,
    dimension: str,
    description: str | None,
    actor_user_id: uuid.UUID,
) -> Criterion:
    """Creer un Criterion draft (stub Epic 13.1).

    Epic 13 Story 13.1 livrera : validation code unique, insertion en
    workflow_state='draft', emission event `catalogue.criterion_created`
    via `record_audit_event` (memes transaction DB).
    """
    raise NotImplementedError(_SKELETON_MSG)


async def create_referential(
    db: AsyncSession,
    *,
    code: str,
    label_fr: str,
    description: str | None,
    actor_user_id: uuid.UUID,
) -> Referential:
    """Creer un Referential draft (stub Epic 13.2)."""
    raise NotImplementedError(_SKELETON_MSG)


async def create_pack(
    db: AsyncSession,
    *,
    code: str,
    label_fr: str,
    actor_user_id: uuid.UUID,
) -> Pack:
    """Creer un Pack draft (stub Epic 13.3)."""
    raise NotImplementedError(_SKELETON_MSG)


async def create_derivation_rule(
    db: AsyncSession,
    *,
    criterion_id: uuid.UUID,
    rule_type: str,
    rule_json: dict,
    actor_user_id: uuid.UUID,
) -> CriterionDerivationRule:
    """Creer une regle de derivation pour un critere (stub Epic 13.1bis)."""
    raise NotImplementedError(_SKELETON_MSG)


async def record_audit_event(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    action: CatalogueActionEnum,
    workflow_level: WorkflowLevelEnum,
    workflow_state_before: str | None,
    workflow_state_after: str | None,
    changes_before: dict | None,
    changes_after: dict | None,
    correlation_id: uuid.UUID | None,
) -> AdminCatalogueAuditTrail:
    """Point d'entree **UNIQUE** pour toute ecriture dans admin_catalogue_audit_trail.

    **NFR64 anti-God service** : Epic 13 + Story 10.12 consomment cette
    fonction ; aucun `INSERT INTO admin_catalogue_audit_trail` inline dans
    les routers/handlers. Appelee dans la **meme transaction DB** que la
    mutation qui declenche l'event — garantit la coherence atomique.

    **NFR37 tracability** : `correlation_id` recoit le `request_id` du
    middleware HTTP pour tracer l'event jusqu'au log. Story 10.10 livrera
    le wiring complet.
    """
    raise NotImplementedError(_SKELETON_MSG)


async def transition_workflow_state(
    db: AsyncSession,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    from_state: NodeStateEnum,
    to_state: NodeStateEnum,
    actor_user_id: uuid.UUID,
) -> None:
    """Transitionner l'etat workflow d'une entite catalogue (stub 13.8b/c).

    Invariant transitions legales :
        draft -> review_requested -> reviewed -> published -> archived

    Toute transition non listee leve (Epic 13.8b/c livrera la validation).
    `record_audit_event` sera appele dans la meme transaction avec
    `workflow_state_before`/`workflow_state_after` remplis.
    """
    raise NotImplementedError(_SKELETON_MSG)
