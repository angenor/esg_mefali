"""Benchmarks sectoriels d'emissions carbone pour les PME d'Afrique de l'Ouest.

Estimations basees sur des moyennes regionales ajustees au contexte.
"""

# Benchmarks par secteur (tCO2e/an pour une PME typique)
SECTOR_BENCHMARKS: dict[str, dict] = {
    "agriculture": {
        "average_emissions_tco2e": 18.0,
        "median_emissions_tco2e": 15.0,
        "by_category": {
            "energy": 7.5,
            "transport": 5.0,
            "waste": 3.0,
            "agriculture": 2.5,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "agroalimentaire": {
        "average_emissions_tco2e": 22.0,
        "median_emissions_tco2e": 18.0,
        "by_category": {
            "energy": 10.0,
            "transport": 5.5,
            "waste": 4.0,
            "industrial": 2.5,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "energie": {
        "average_emissions_tco2e": 35.0,
        "median_emissions_tco2e": 28.0,
        "by_category": {
            "energy": 20.0,
            "transport": 8.0,
            "waste": 4.0,
            "industrial": 3.0,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "transport": {
        "average_emissions_tco2e": 30.0,
        "median_emissions_tco2e": 25.0,
        "by_category": {
            "energy": 5.0,
            "transport": 22.0,
            "waste": 3.0,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "construction": {
        "average_emissions_tco2e": 28.0,
        "median_emissions_tco2e": 22.0,
        "by_category": {
            "energy": 10.0,
            "transport": 8.0,
            "waste": 5.0,
            "industrial": 5.0,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "commerce": {
        "average_emissions_tco2e": 12.0,
        "median_emissions_tco2e": 10.0,
        "by_category": {
            "energy": 5.0,
            "transport": 4.5,
            "waste": 2.5,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "services": {
        "average_emissions_tco2e": 8.0,
        "median_emissions_tco2e": 6.5,
        "by_category": {
            "energy": 4.0,
            "transport": 2.5,
            "waste": 1.5,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "textile": {
        "average_emissions_tco2e": 20.0,
        "median_emissions_tco2e": 16.0,
        "by_category": {
            "energy": 9.0,
            "transport": 4.0,
            "waste": 4.0,
            "industrial": 3.0,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
    "recyclage": {
        "average_emissions_tco2e": 15.0,
        "median_emissions_tco2e": 12.0,
        "by_category": {
            "energy": 6.0,
            "transport": 5.0,
            "waste": 4.0,
        },
        "sample_size": "estimation",
        "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest",
    },
}

# Mapping de fallback vers des secteurs similaires
SECTOR_FALLBACK: dict[str, str] = {
    "mining": "construction",
    "manufacturing": "construction",
    "artisanat": "commerce",
    "education": "services",
    "sante": "services",
    "technologie": "services",
    "tourisme": "commerce",
    "immobilier": "construction",
}


def get_sector_benchmark(sector: str) -> dict | None:
    """Retourne le benchmark pour un secteur, avec fallback vers secteur similaire."""
    sector_lower = sector.lower()

    benchmark = SECTOR_BENCHMARKS.get(sector_lower)
    if benchmark is not None:
        return {**benchmark, "sector": sector_lower}

    # Essayer le fallback
    fallback = SECTOR_FALLBACK.get(sector_lower)
    if fallback is not None:
        benchmark = SECTOR_BENCHMARKS.get(fallback)
        if benchmark is not None:
            return {**benchmark, "sector": fallback, "fallback_from": sector_lower}

    return None


def compute_benchmark_position(
    total_tco2e: float, sector: str
) -> dict:
    """Compare les emissions au benchmark sectoriel et retourne la position."""
    benchmark = get_sector_benchmark(sector)
    if benchmark is None:
        return {
            "sector": sector,
            "position": "unknown",
            "sector_average_tco2e": None,
            "percentile": None,
        }

    avg = benchmark["average_emissions_tco2e"]
    median = benchmark["median_emissions_tco2e"]

    if total_tco2e <= median * 0.7:
        position = "well_below_average"
        percentile = 20
    elif total_tco2e <= median:
        position = "below_average"
        percentile = 35
    elif total_tco2e <= avg:
        position = "average"
        percentile = 50
    elif total_tco2e <= avg * 1.3:
        position = "above_average"
        percentile = 70
    else:
        position = "well_above_average"
        percentile = 85

    return {
        "sector": benchmark.get("sector", sector),
        "sector_average_tco2e": avg,
        "position": position,
        "percentile": percentile,
    }
