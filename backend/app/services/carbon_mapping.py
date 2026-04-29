"""Mapping subcategory carbone — synonymes francais → codes canoniques.

Service deterministe pur (aucune dependance DB, aucun appel LLM) qui resout
un libelle francais saisi par l'utilisateur ou produit par le LLM vers un code
canonique d'EMISSION_FACTORS. Trois strategies de match dans cet ordre :

1. Exact (lowercase + strip + sans accents)
2. Substring (synonym contenu dans input)
3. Fuzzy via difflib (cutoff 0.75)

Si aucune strategie ne resout, retourne (None, alternatives) ou alternatives
liste les codes canoniques de la categorie pour permettre un fallback informe.

Regression V8-AXE4 : BUG-V7-005, BUG-V7.1-006, BUG-V7.1-007.
"""

from __future__ import annotations

import unicodedata
from difflib import get_close_matches

SUBCATEGORY_SYNONYMS: dict[str, dict[str, str]] = {
    "agriculture": {
        "riz pluvial": "rice_rainfed",
        "riz irrigué": "rice_irrigated",
        "riz": "rice_rainfed",
        "blé": "wheat",
        "ble": "wheat",
        "maïs": "maize",
        "mais": "maize",
        "élevage bovin": "cattle",
        "elevage bovin": "cattle",
        "vaches": "cattle",
        "élevage caprin": "goats",
        "chèvres": "goats",
        "compostage": "compost",
        "compost": "compost",
        "fertilisant azoté": "nitrogen_fertilizer",
        "fertilisant": "nitrogen_fertilizer",
        "engrais": "nitrogen_fertilizer",
    },
    "energy": {
        "diesel": "diesel",
        "gasoil": "diesel",
        "essence": "gasoline",
        "gpl": "lpg",
        "butane": "lpg",
        "propane": "lpg",
        "électricité": "grid_electricity",
        "electricite": "grid_electricity",
        "électricité réseau": "grid_electricity",
        "panneaux solaires": "solar_pv",
        "solaire": "solar_pv",
        "groupe électrogène": "diesel_generator",
        "groupe diesel": "diesel_generator",
        "charbon": "coal",
        "bois": "biomass",
        "biomasse": "biomass",
    },
    "transport": {
        "camion": "truck",
        "camionnette": "truck",
        "voiture": "car",
        "véhicule personnel": "car",
        "moto": "motorcycle",
        "scooter": "motorcycle",
        "avion": "flight",
        "vol": "flight",
        "bateau": "ship",
        "ferry": "ship",
        "train": "train",
        "bus": "bus",
    },
    "waste": {
        "compostage": "waste_compost",
        "compost": "waste_compost",
        "compostage déchets": "waste_compost",
        "décharge": "waste_landfill",
        "decharge": "waste_landfill",
        "enfouissement": "waste_landfill",
        "incinération": "waste_incineration",
        "incineration": "waste_incineration",
        "brûlage": "waste_incineration",
        "recyclage": "waste_recycling",
        "récupération": "waste_recycling",
    },
    "industrial": {
        "ciment": "cement",
        "acier": "steel",
        "fer": "steel",
        "aluminium": "aluminum",
        "verre": "glass",
        "papier": "paper",
        "plastique": "plastic",
    },
}


def _normalize(text: str) -> str:
    """Lowercase + strip + remove accents pour match permissif."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def resolve_subcategory(
    category: str,
    raw_text: str | None,
) -> tuple[str | None, list[str]]:
    """Mapper raw_text francais vers subcategory canonique.

    Args:
        category: Categorie d'emission (energy, transport, waste, industrial, agriculture).
        raw_text: Libelle libre fourni par l'utilisateur ou le LLM (ex: "riz pluvial").

    Returns:
        (canonical_subcategory, alternatives)
        - canonical_subcategory : code canonique resolu, ou None si non resolu.
        - alternatives : liste de codes canoniques possibles pour la categorie
          (vide si match trouve, ou si la categorie est inconnue).
    """
    if category not in SUBCATEGORY_SYNONYMS:
        return None, []

    synonyms_dict = SUBCATEGORY_SYNONYMS[category]
    canonical_codes = sorted(set(synonyms_dict.values()))

    if not raw_text:
        return None, canonical_codes

    normalized_input = _normalize(raw_text)

    # 1. Match exact lowercase + sans accents
    for synonym, canonical in synonyms_dict.items():
        if _normalize(synonym) == normalized_input:
            return canonical, []

    # 2. Match substring (synonym contenu dans input)
    for synonym, canonical in synonyms_dict.items():
        if _normalize(synonym) in normalized_input:
            return canonical, []

    # 3. Match fuzzy (Levenshtein via difflib)
    normalized_synonyms = {_normalize(syn): canonical for syn, canonical in synonyms_dict.items()}
    matches = get_close_matches(
        normalized_input, list(normalized_synonyms.keys()), n=1, cutoff=0.75,
    )
    if matches:
        return normalized_synonyms[matches[0]], []

    return None, canonical_codes
