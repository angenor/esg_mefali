"""Ponderations sectorielles et benchmarks ESG pour la zone UEMOA.

Les poids par defaut sont 1.0. Les secteurs specifiques ajustent les poids
des criteres les plus pertinents (ex: E6 Gestion eau critique pour agriculture).

Score par pilier = (somme des score_critere * poids_critere) / (somme des poids * 10) * 100
Score global = moyenne des 3 piliers (ponderation egale E/S/G).
"""

# Ponderations par secteur : dictionnaire de code_critere -> poids
# Les criteres absents ont un poids de 1.0 par defaut
SECTOR_WEIGHTS: dict[str, dict[str, float]] = {
    "agriculture": {
        "E1": 1.3, "E4": 1.5, "E5": 1.4, "E6": 1.5, "E8": 1.2, "E10": 1.3,
        "S1": 1.2, "S4": 1.3, "S5": 1.3, "S6": 1.2, "S9": 1.4,
        "G4": 1.2, "G6": 1.3,
    },
    "energie": {
        "E2": 1.5, "E3": 1.5, "E7": 1.3, "E8": 1.5, "E9": 1.2,
        "S5": 1.4, "S1": 1.3,
        "G4": 1.4, "G6": 1.4,
    },
    "recyclage": {
        "E1": 1.5, "E4": 1.4, "E10": 1.5, "E3": 1.3,
        "S1": 1.3, "S5": 1.4, "S4": 1.2,
        "G4": 1.3,
    },
    "transport": {
        "E3": 1.5, "E9": 1.5, "E2": 1.3, "E8": 1.2,
        "S1": 1.3, "S5": 1.4,
        "G4": 1.3, "G6": 1.2,
    },
    "construction": {
        "E1": 1.3, "E2": 1.3, "E3": 1.2, "E4": 1.4, "E5": 1.3, "E6": 1.2,
        "S1": 1.4, "S5": 1.5,
        "G4": 1.4, "G6": 1.3,
    },
    "textile": {
        "E1": 1.3, "E2": 1.2, "E4": 1.3, "E6": 1.4, "E10": 1.3,
        "S1": 1.4, "S2": 1.3, "S6": 1.3,
        "G3": 1.2, "G4": 1.2,
    },
    "agroalimentaire": {
        "E1": 1.4, "E4": 1.3, "E5": 1.2, "E6": 1.4, "E10": 1.2,
        "S1": 1.3, "S5": 1.4, "S9": 1.3,
        "G4": 1.3,
    },
    "services": {
        "E2": 1.2, "E7": 1.2,
        "S1": 1.2, "S2": 1.3, "S3": 1.4, "S6": 1.2, "S7": 1.3, "S10": 1.3,
        "G1": 1.3, "G8": 1.3, "G9": 1.4,
    },
    "commerce": {
        "E1": 1.2, "E9": 1.3, "E10": 1.2,
        "S1": 1.2, "S4": 1.3, "S6": 1.2, "S9": 1.4,
        "G1": 1.3, "G3": 1.3, "G4": 1.2,
    },
    "artisanat": {
        "E1": 1.2, "E4": 1.3, "E10": 1.4,
        "S1": 1.3, "S3": 1.3, "S4": 1.3, "S9": 1.3,
        "G1": 1.2, "G7": 1.3,
    },
}

DEFAULT_WEIGHT: float = 1.0


def get_criterion_weight(sector: str, criterion_code: str) -> float:
    """Obtenir le poids d'un critere pour un secteur donne."""
    sector_weights = SECTOR_WEIGHTS.get(sector, {})
    return sector_weights.get(criterion_code, DEFAULT_WEIGHT)


# Benchmarks sectoriels : moyennes estimees pour la zone UEMOA
# Basees sur des estimations contextuelles, affinables avec les donnees reelles
SECTOR_BENCHMARKS: dict[str, dict[str, object]] = {
    "agriculture": {
        "sector_label": "Agriculture",
        "averages": {"environment": 52, "social": 48, "governance": 45, "overall": 48},
        "top_criteria": ["E6", "E1", "S4"],
        "weak_criteria": ["G3", "G5", "G10"],
    },
    "energie": {
        "sector_label": "Energie",
        "averages": {"environment": 45, "social": 50, "governance": 48, "overall": 48},
        "top_criteria": ["E8", "S5", "G4"],
        "weak_criteria": ["E3", "G5", "G10"],
    },
    "recyclage": {
        "sector_label": "Recyclage",
        "averages": {"environment": 60, "social": 45, "governance": 42, "overall": 49},
        "top_criteria": ["E1", "E10", "E4"],
        "weak_criteria": ["S6", "G1", "G10"],
    },
    "transport": {
        "sector_label": "Transport",
        "averages": {"environment": 38, "social": 46, "governance": 44, "overall": 43},
        "top_criteria": ["S1", "G4", "E9"],
        "weak_criteria": ["E3", "E8", "G5"],
    },
    "construction": {
        "sector_label": "Construction",
        "averages": {"environment": 42, "social": 44, "governance": 43, "overall": 43},
        "top_criteria": ["S5", "E4", "G4"],
        "weak_criteria": ["E3", "G5", "S2"],
    },
    "textile": {
        "sector_label": "Textile",
        "averages": {"environment": 44, "social": 42, "governance": 40, "overall": 42},
        "top_criteria": ["E10", "S9", "E4"],
        "weak_criteria": ["S6", "G5", "G10"],
    },
    "agroalimentaire": {
        "sector_label": "Agroalimentaire",
        "averages": {"environment": 50, "social": 47, "governance": 44, "overall": 47},
        "top_criteria": ["E6", "S5", "S9"],
        "weak_criteria": ["G5", "G10", "E3"],
    },
    "services": {
        "sector_label": "Services",
        "averages": {"environment": 55, "social": 52, "governance": 50, "overall": 52},
        "top_criteria": ["S3", "G9", "S10"],
        "weak_criteria": ["E8", "E5", "G5"],
    },
    "commerce": {
        "sector_label": "Commerce",
        "averages": {"environment": 46, "social": 48, "governance": 46, "overall": 47},
        "top_criteria": ["S9", "S4", "G1"],
        "weak_criteria": ["E3", "G5", "E8"],
    },
    "artisanat": {
        "sector_label": "Artisanat",
        "averages": {"environment": 48, "social": 50, "governance": 42, "overall": 47},
        "top_criteria": ["E10", "S4", "S9"],
        "weak_criteria": ["G1", "G5", "G10"],
    },
}


def get_sector_benchmark(sector: str) -> dict | None:
    """Obtenir le benchmark sectoriel pour un secteur donne.

    Retourne None si le secteur n'est pas connu.
    """
    benchmark = SECTOR_BENCHMARKS.get(sector)
    if benchmark is None:
        return None
    return {"sector": sector, **benchmark}
