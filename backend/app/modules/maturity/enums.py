"""Enumerations du module maturity (source unique pour models + schemas + service).

Story 10.3 - module `maturity/` squelette.
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].
"""

from __future__ import annotations

import enum


class MaturityWorkflowStateEnum(str, enum.Enum):
    """Etat workflow admin N1/N2/N3 simplifie MVP (Decision 6).

    Valeurs stockees en String(16) cote BDD (workflow_state colonne des
    tables `admin_maturity_levels` et `admin_maturity_requirements`).
    L'enum Python est l'invariant cote code.
    """

    draft = "draft"
    review_requested = "review_requested"
    published = "published"


class MaturityChangeDirectionEnum(str, enum.Enum):
    """Direction d'un changement de niveau de maturite (Epic 12 Story 12.5).

    Cohorence avec `MaturityChangeLog.direction` (Cluster A' audit trail).
    """

    upgrade = "upgrade"
    downgrade = "downgrade"
