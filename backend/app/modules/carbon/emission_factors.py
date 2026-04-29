"""Facteurs d'emission et constantes pour le calcul carbone.

Sources : grilles ADEME adaptees Afrique de l'Ouest.
"""

# Facteurs d'emission par source (kgCO2e par unite)
# Sources : ADEME Base Carbone, IPCC AR6, GHG Protocol — adaptes Afrique de l'Ouest.
EMISSION_FACTORS: dict[str, dict] = {
    # Energie
    "electricity_ci": {
        "factor": 0.41,
        "unit": "kgCO2e/kWh",
        "label": "Electricite (reseau CI)",
        "category": "energy",
    },
    "grid_electricity": {
        "factor": 0.41,
        "unit": "kgCO2e/kWh",
        "label": "Electricite reseau",
        "category": "energy",
    },
    "diesel_generator": {
        "factor": 2.68,
        "unit": "kgCO2e/L",
        "label": "Generateur diesel",
        "category": "energy",
    },
    "diesel": {
        "factor": 2.68,
        "unit": "kgCO2e/L",
        "label": "Diesel (gasoil)",
        "category": "energy",
    },
    "butane_gas": {
        "factor": 2.98,
        "unit": "kgCO2e/kg",
        "label": "Gaz butane",
        "category": "energy",
    },
    "lpg": {
        "factor": 3.0,
        "unit": "kgCO2e/kg",
        "label": "GPL (butane / propane)",
        "category": "energy",
    },
    "solar_pv": {
        "factor": 0.041,
        "unit": "kgCO2e/kWh",
        "label": "Electricite solaire photovoltaique",
        "category": "energy",
    },
    "coal": {
        "factor": 2.42,
        "unit": "kgCO2e/kg",
        "label": "Charbon",
        "category": "energy",
    },
    "biomass": {
        "factor": 0.39,
        "unit": "kgCO2e/kg",
        "label": "Biomasse / bois",
        "category": "energy",
    },
    # Transport
    "gasoline": {
        "factor": 2.31,
        "unit": "kgCO2e/L",
        "label": "Essence",
        "category": "transport",
    },
    "diesel_transport": {
        "factor": 2.68,
        "unit": "kgCO2e/L",
        "label": "Gasoil",
        "category": "transport",
    },
    "truck": {
        "factor": 0.92,
        "unit": "kgCO2e/km",
        "label": "Camion / camionnette",
        "category": "transport",
    },
    "car": {
        "factor": 0.18,
        "unit": "kgCO2e/km",
        "label": "Voiture particuliere",
        "category": "transport",
    },
    "motorcycle": {
        "factor": 0.07,
        "unit": "kgCO2e/km",
        "label": "Moto / scooter",
        "category": "transport",
    },
    "flight": {
        "factor": 0.255,
        "unit": "kgCO2e/km",
        "label": "Avion (vol passager)",
        "category": "transport",
    },
    "ship": {
        "factor": 0.04,
        "unit": "kgCO2e/km",
        "label": "Bateau / ferry",
        "category": "transport",
    },
    "train": {
        "factor": 0.06,
        "unit": "kgCO2e/km",
        "label": "Train",
        "category": "transport",
    },
    "bus": {
        "factor": 0.10,
        "unit": "kgCO2e/km",
        "label": "Bus",
        "category": "transport",
    },
    # Dechets
    "waste_landfill": {
        "factor": 0.5,
        "unit": "kgCO2e/kg",
        "label": "Dechets (enfouissement)",
        "category": "waste",
    },
    "waste_incineration": {
        "factor": 1.1,
        "unit": "kgCO2e/kg",
        "label": "Dechets (incineration)",
        "category": "waste",
    },
    "waste_compost": {
        "factor": 0.05,
        "unit": "kgCO2e/kg",
        "label": "Dechets (compostage)",
        "category": "waste",
    },
    "waste_recycling": {
        "factor": 0.02,
        "unit": "kgCO2e/kg",
        "label": "Dechets (recyclage)",
        "category": "waste",
    },
    # Agriculture
    "rice_rainfed": {
        "factor": 1.45,
        "unit": "kgCO2e/kg",
        "label": "Riz pluvial",
        "category": "agriculture",
    },
    "rice_irrigated": {
        "factor": 3.0,
        "unit": "kgCO2e/kg",
        "label": "Riz irrigue",
        "category": "agriculture",
    },
    "wheat": {
        "factor": 0.8,
        "unit": "kgCO2e/kg",
        "label": "Ble",
        "category": "agriculture",
    },
    "maize": {
        "factor": 0.6,
        "unit": "kgCO2e/kg",
        "label": "Mais",
        "category": "agriculture",
    },
    "cattle": {
        "factor": 15.0,
        "unit": "kgCO2e/animal/an",
        "label": "Elevage bovin",
        "category": "agriculture",
    },
    "goats": {
        "factor": 1.8,
        "unit": "kgCO2e/animal/an",
        "label": "Elevage caprin",
        "category": "agriculture",
    },
    "compost": {
        "factor": 0.05,
        "unit": "kgCO2e/kg",
        "label": "Compostage agricole",
        "category": "agriculture",
    },
    "nitrogen_fertilizer": {
        "factor": 5.4,
        "unit": "kgCO2e/kg",
        "label": "Fertilisant azote",
        "category": "agriculture",
    },
    # Processus industriels
    "cement": {
        "factor": 0.93,
        "unit": "kgCO2e/kg",
        "label": "Ciment",
        "category": "industrial",
    },
    "steel": {
        "factor": 1.85,
        "unit": "kgCO2e/kg",
        "label": "Acier",
        "category": "industrial",
    },
    "aluminum": {
        "factor": 8.14,
        "unit": "kgCO2e/kg",
        "label": "Aluminium",
        "category": "industrial",
    },
    "glass": {
        "factor": 0.85,
        "unit": "kgCO2e/kg",
        "label": "Verre",
        "category": "industrial",
    },
    "paper": {
        "factor": 1.1,
        "unit": "kgCO2e/kg",
        "label": "Papier",
        "category": "industrial",
    },
    "plastic": {
        "factor": 2.5,
        "unit": "kgCO2e/kg",
        "label": "Plastique",
        "category": "industrial",
    },
}

# Equivalences parlantes contextualisees Afrique de l'Ouest
EQUIVALENCES: dict[str, dict] = {
    "flight_paris_dakar": {
        "value": 1.2,
        "unit": "tCO2e",
        "label": "vols Paris-Dakar",
    },
    "car_year_avg": {
        "value": 2.4,
        "unit": "tCO2e",
        "label": "annees de conduite moyenne",
    },
    "tree_year_absorption": {
        "value": 0.025,
        "unit": "tCO2e",
        "label": "arbres necessaires pour compenser (1 an)",
    },
}

# Tarifs moyens pour conversion FCFA → unites physiques
PRICE_REFERENCES_FCFA: dict[str, dict] = {
    "electricity_kwh": {
        "price": 100,
        "unit": "FCFA/kWh",
        "label": "Electricite CIE (tranche moyenne)",
    },
    "diesel_liter": {
        "price": 700,
        "unit": "FCFA/L",
        "label": "Diesel",
    },
    "gasoline_liter": {
        "price": 615,
        "unit": "FCFA/L",
        "label": "Essence",
    },
    "butane_12kg": {
        "price": 6000,
        "unit": "FCFA/12.5kg",
        "label": "Gaz butane (bouteille 12.5 kg)",
    },
}

# Categories d'emissions et leur ordre de progression
EMISSION_CATEGORIES: list[dict] = [
    {
        "key": "energy",
        "label": "Energie",
        "required": True,
        "subcategories": ["electricity_ci", "diesel_generator", "butane_gas"],
    },
    {
        "key": "transport",
        "label": "Transport",
        "required": True,
        "subcategories": ["gasoline", "diesel_transport"],
    },
    {
        "key": "waste",
        "label": "Dechets",
        "required": True,
        "subcategories": ["waste_landfill", "waste_incineration"],
    },
    {
        "key": "industrial",
        "label": "Processus industriels",
        "required": False,
        "applicable_sectors": ["manufacturing", "construction", "mining"],
        "subcategories": ["cement", "steel", "aluminum", "glass", "paper", "plastic"],
    },
    {
        "key": "agriculture",
        "label": "Agriculture",
        "required": False,
        "applicable_sectors": ["agriculture", "agroalimentaire"],
        "subcategories": [
            "rice_rainfed",
            "rice_irrigated",
            "wheat",
            "maize",
            "cattle",
            "goats",
            "compost",
            "nitrogen_fertilizer",
        ],
    },
]


def get_emission_factor(subcategory: str) -> float:
    """Retourne le facteur d'emission pour une sous-categorie donnee."""
    factor_info = EMISSION_FACTORS.get(subcategory)
    if factor_info is None:
        raise ValueError(f"Facteur d'emission inconnu: {subcategory}")
    return factor_info["factor"]


def compute_emissions_tco2e(quantity: float, emission_factor: float) -> float:
    """Calcule les emissions en tCO2e a partir de la quantite et du facteur."""
    return round((quantity * emission_factor) / 1000, 4)


def compute_equivalences(total_tco2e: float) -> list[dict]:
    """Calcule les equivalences parlantes pour un total d'emissions."""
    results: list[dict] = []
    for _key, equiv in EQUIVALENCES.items():
        if equiv["value"] > 0:
            count = round(total_tco2e / equiv["value"], 1)
            results.append({
                "label": equiv["label"],
                "value": count,
            })
    return results


def get_applicable_categories(sector: str | None) -> list[str]:
    """Retourne les categories applicables pour un secteur donne."""
    categories: list[str] = []
    for cat in EMISSION_CATEGORIES:
        if cat["required"]:
            categories.append(cat["key"])
        elif sector and sector.lower() in cat.get("applicable_sectors", []):
            categories.append(cat["key"])
    return categories
