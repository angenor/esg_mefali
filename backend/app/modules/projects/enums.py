"""Enumerations du module projects (source unique pour models + schemas).

Story 10.2 - module `projects/` squelette.
FR covered: [] (infra FR1-FR10), NFR covered: [NFR49, NFR62, NFR64].
"""

from __future__ import annotations

import enum


class ProjectStatusEnum(str, enum.Enum):
    """Statut d'un projet (aligne sur migration 020 `project_status_enum`)."""

    idea = "idea"
    planning = "planning"
    in_progress = "in_progress"
    operational = "operational"
    archived = "archived"


class ProjectRoleEnum(str, enum.Enum):
    """Role d'un membership (aligne sur migration 020 `project_role_enum`)."""

    porteur_principal = "porteur_principal"
    beneficiaire = "beneficiaire"
    partenaire = "partenaire"
    observateur = "observateur"
