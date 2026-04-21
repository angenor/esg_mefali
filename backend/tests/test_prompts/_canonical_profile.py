"""Profil canonique partage pour les golden snapshots (Story 10.8).

Utilise par test_golden_snapshots.py pour generer et comparer les prompts
canoniques des 7 modules metier. Defini ici pour qu'une modification du profil
soit visible dans le diff des golden snapshots (fail-fast sur drift).
"""

from __future__ import annotations

from typing import Any, Final

# Profil minimal (>= 2 champs pour activer _has_minimum_profile dans system.py
# et declencher l'injection de STYLE_INSTRUCTION post-onboarding).
CANONICAL_PROFILE: Final[dict[str, Any]] = {
    "company_name": "Mefali Test SARL",
    "sector": "recyclage",
    "country": "Côte d'Ivoire",
    "employee_count": 25,
}


CANONICAL_COMPANY_CONTEXT: Final[str] = (
    "Profil: Mefali Test SARL, secteur recyclage, Côte d'Ivoire, 25 employés."
)

CANONICAL_DOCUMENT_CONTEXT: Final[str] = "Aucun document analyse."

CANONICAL_RAG_CONTEXT: Final[str] = "Aucune information supplementaire disponible."

CANONICAL_APPLICATION_CONTEXT: Final[str] = "Aucun dossier en cours."

CANONICAL_SCORING_CONTEXT: Final[str] = "Aucun score genere."

CANONICAL_APPLICABLE_CATEGORIES: Final[str] = "energy, transport, waste"

CANONICAL_ESG_CONTEXT: Final[str] = "Aucune évaluation ESG disponible."

CANONICAL_CARBON_CONTEXT: Final[str] = "Aucun bilan carbone disponible."

CANONICAL_FINANCING_CONTEXT: Final[str] = "Aucun matching financement disponible."

CANONICAL_INTERMEDIARIES_CONTEXT: Final[str] = "Aucun intermédiaire identifié."

CANONICAL_TIMEFRAME: Final[int] = 12
