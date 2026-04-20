"""Stub du generateur de plan de formalisation pays-specifique (FR13).

Story 10.3 - module `maturity/` squelette (AC7).
FR covered: [] (infra FR11-FR16), NFR covered: [NFR49, NFR62, NFR64, NFR66].

Le point d'extension Epic 12 Story 12.3 (FR13). Epic 12 livrera l'implementation
complete qui copie les etapes depuis `AdminMaturityRequirement.requirements_json`
du pays au moment de la generation (zero hardcoding Python).

**NFR66 country-data-driven** : aucun nom de pays UEMOA/CEDEAO
francophone ne doit apparaitre en string literal dans ce fichier. Le
test `test_country_data_driven_no_hardcoded_country_strings` scan ce
fichier pour l'enforcement.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.maturity.models import FormalizationPlan


class FormalizationPlanCalculator:
    """Generateur data-driven de plans de formalisation (stub Epic 12.3)."""

    def __init__(self) -> None:
        """Constructeur vide — Epic 12 decidera DI service."""

    async def generate(
        self,
        db: AsyncSession,
        *,
        company_id: uuid.UUID,
        current_level_id: uuid.UUID,
        target_level_id: uuid.UUID,
        country: str,
    ) -> FormalizationPlan:
        """Generer un plan de formalisation pays-specifique (FR13).

        Les etapes sont **copiees depuis `AdminMaturityRequirement.requirements_json`
        du pays** au moment de la generation (zero hardcoding Python).
        Epic 12 Story 12.3 livrera l'implementation.

        Args:
            db: session SQLAlchemy asynchrone.
            company_id: UUID de l'entreprise cible.
            current_level_id: UUID du niveau actuel (`AdminMaturityLevel.id`).
            target_level_id: UUID du niveau cible (`AdminMaturityLevel.id`).
            country: code ou libelle pays (string variable, **pas litterale**
                     hardcodee dans le code) — consomme via
                     `service.get_requirements_for_country_level`.

        Raises:
            NotImplementedError: toujours — squelette Story 10.3.
        """
        raise NotImplementedError(
            "Story 10.3 skeleton — FormalizationPlanCalculator.generate "
            "delivered in Epic 12 story 12.3"
        )
