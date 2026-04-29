"""Tests unitaires pour le service carbon_mapping (V8-AXE4).

Couvre la matrice I/O complete de resolve_subcategory + l'invariant cle :
tous les codes canoniques references par SUBCATEGORY_SYNONYMS doivent
exister dans EMISSION_FACTORS, sinon le mapping resout vers un code inutilisable.
"""

from __future__ import annotations

import pytest

from app.modules.carbon.emission_factors import EMISSION_FACTORS
from app.services.carbon_mapping import (
    SUBCATEGORY_SYNONYMS,
    _normalize,
    resolve_subcategory,
)


# ---------- _normalize ----------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Riz Pluvial", "riz pluvial"),
        ("  Diesel  ", "diesel"),
        ("Électricité", "electricite"),
        ("Compostage Déchets", "compostage dechets"),
        ("MAÏS", "mais"),
        ("", ""),
    ],
)
def test_normalize_lowercases_strips_and_removes_accents(raw: str, expected: str) -> None:
    assert _normalize(raw) == expected


# ---------- Matrice de resolution ----------


@pytest.mark.parametrize(
    "category, raw_text, expected_canonical",
    [
        # Match exact normalise (insensible a la casse + accents)
        ("agriculture", "riz pluvial", "rice_rainfed"),
        ("agriculture", "Riz Pluvial", "rice_rainfed"),
        ("agriculture", "RIZ PLUVIAL", "rice_rainfed"),
        ("agriculture", "blé", "wheat"),
        ("agriculture", "BLE", "wheat"),
        ("energy", "diesel", "diesel"),
        ("energy", "gasoil", "diesel"),
        ("energy", "essence", "gasoline"),
        ("energy", "électricité", "grid_electricity"),
        ("energy", "Electricite", "grid_electricity"),
        ("energy", "groupe électrogène", "diesel_generator"),
        ("waste", "compostage", "waste_compost"),
        ("waste", "décharge", "waste_landfill"),
        ("waste", "incinération", "waste_incineration"),
        ("transport", "camion", "truck"),
        ("transport", "moto", "motorcycle"),
        ("transport", "avion", "flight"),
        ("industrial", "ciment", "cement"),
        ("industrial", "acier", "steel"),
    ],
)
def test_resolve_subcategory_exact_match(
    category: str, raw_text: str, expected_canonical: str,
) -> None:
    """Match exact apres normalisation (lowercase + accents) doit retourner le code canonique."""
    canonical, alternatives = resolve_subcategory(category, raw_text)
    assert canonical == expected_canonical
    assert alternatives == []


@pytest.mark.parametrize(
    "category, raw_text, expected_canonical",
    [
        # Substring match : synonym contenu dans une phrase plus longue.
        # L'ordre d'insertion du dict prime — synonymes plus generiques
        # listes en premier gagnent (ex: "diesel" avant "groupe electrogene").
        ("energy", "panneaux solaires de toiture installes en 2024", "solar_pv"),
        ("agriculture", "production de riz pluvial dans le delta", "rice_rainfed"),
        ("waste", "compostage des déchets organiques", "waste_compost"),
        ("transport", "flotte de camions diesel", "truck"),
    ],
)
def test_resolve_subcategory_substring_match(
    category: str, raw_text: str, expected_canonical: str,
) -> None:
    canonical, alternatives = resolve_subcategory(category, raw_text)
    assert canonical == expected_canonical
    assert alternatives == []


@pytest.mark.parametrize(
    "category, raw_text, expected_canonical",
    [
        # Fuzzy : typos legers tolerees (cutoff 0.75)
        ("waste", "compostag", "waste_compost"),
        ("energy", "diesell", "diesel"),
        ("agriculture", "rizpluvial", "rice_rainfed"),
    ],
)
def test_resolve_subcategory_fuzzy_match(
    category: str, raw_text: str, expected_canonical: str,
) -> None:
    canonical, alternatives = resolve_subcategory(category, raw_text)
    assert canonical == expected_canonical
    assert alternatives == []


def test_resolve_subcategory_unknown_category_returns_none_and_empty_alternatives() -> None:
    """Categorie absente du mapping → (None, [])."""
    canonical, alternatives = resolve_subcategory("finance", "prêt vert")
    assert canonical is None
    assert alternatives == []


def test_resolve_subcategory_empty_raw_text_returns_alternatives() -> None:
    """raw_text vide → (None, alternatives = codes canoniques de la categorie)."""
    canonical, alternatives = resolve_subcategory("energy", "")
    assert canonical is None
    assert "diesel" in alternatives
    assert "gasoline" in alternatives
    assert "grid_electricity" in alternatives


def test_resolve_subcategory_none_raw_text_returns_alternatives() -> None:
    """raw_text=None → (None, alternatives)."""
    canonical, alternatives = resolve_subcategory("waste", None)
    assert canonical is None
    assert "waste_compost" in alternatives
    assert "waste_landfill" in alternatives


def test_resolve_subcategory_no_match_returns_alternatives() -> None:
    """raw_text non resolvable → (None, alternatives)."""
    canonical, alternatives = resolve_subcategory("energy", "cheval-vapeur")
    assert canonical is None
    assert len(alternatives) > 0
    # On doit retrouver des codes canoniques connus.
    assert "diesel" in alternatives


# ---------- BUG-V7.1-007 : disambiguisation diesel / essence ----------


def test_resolve_subcategory_diesel_does_not_collide_with_gasoline() -> None:
    """BUG-V7.1-007 : 'diesel' ne doit JAMAIS resoudre vers 'gasoline'."""
    canonical, _ = resolve_subcategory("energy", "diesel")
    assert canonical == "diesel"
    assert canonical != "gasoline"


def test_resolve_subcategory_compostage_does_not_collide_with_landfill() -> None:
    """BUG-V7.1-007 : 'compostage' ne doit JAMAIS resoudre vers 'waste_landfill'."""
    canonical, _ = resolve_subcategory("waste", "compostage")
    assert canonical == "waste_compost"
    assert canonical != "waste_landfill"


# ---------- Invariant : tous les codes canoniques existent dans EMISSION_FACTORS ----------


def test_invariant_all_canonical_codes_have_emission_factor() -> None:
    """Tous les codes canoniques references par SUBCATEGORY_SYNONYMS doivent
    exister dans EMISSION_FACTORS, sinon save_emission_entry rejettera des
    entrees pourtant resolues par le mapping.

    NB : on n'exige PAS que la category du code canonique dans EMISSION_FACTORS
    soit identique a la category du mapping. Certains combustibles (gasoline,
    diesel) sont cross-categorical : utilisables en energie statique ou en
    transport. La category de l'entree saisie par l'utilisateur est celle
    fournie par le LLM via le tool, pas celle attachee au code canonique.
    """
    missing: list[tuple[str, str]] = []
    for category, synonyms in SUBCATEGORY_SYNONYMS.items():
        for _synonym, canonical in synonyms.items():
            if canonical not in EMISSION_FACTORS:
                missing.append((category, canonical))
    assert not missing, (
        "Codes canoniques references dans SUBCATEGORY_SYNONYMS mais absents "
        f"d'EMISSION_FACTORS : {missing}"
    )
