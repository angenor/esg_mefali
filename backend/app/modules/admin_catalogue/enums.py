"""Enumerations du module admin_catalogue (source unique models + schemas + service).

Story 10.4 — module `admin_catalogue/` squelette (UI-only).
FR covered: [] (infra FR17-FR26 + FR64), NFR covered: [NFR27, NFR28, NFR62, NFR64, NFR66].
"""

from __future__ import annotations

import enum


class NodeStateEnum(str, enum.Enum):
    """Etat workflow admin N1/N2/N3 complet (Decision 6).

    Figee a 5 valeurs des Story 10.4 pour eviter un refactor invariant
    lorsque Epic 13.8b/c livrera les transitions peer-review -> publish.
    Valeurs stockees en String(16) cote BDD (workflow_state colonne des
    tables `criteria`, `referentials`, `packs`). L'enum Python est
    l'invariant cote code.

    Transitions legales :
        draft -> review_requested -> reviewed -> published -> archived
    """

    draft = "draft"
    review_requested = "review_requested"
    reviewed = "reviewed"
    published = "published"
    archived = "archived"


class CatalogueActionEnum(str, enum.Enum):
    """Miroir de l'enum PostgreSQL `catalogue_action_enum` (migration 026)."""

    create = "create"
    update = "update"
    delete = "delete"
    publish = "publish"
    retire = "retire"


class WorkflowLevelEnum(str, enum.Enum):
    """Miroir de l'enum PostgreSQL `workflow_level_enum` (migration 026)."""

    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
