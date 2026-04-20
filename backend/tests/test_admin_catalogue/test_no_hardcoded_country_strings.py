"""Scan NFR66 exhaustif sur les 9 fichiers du module admin_catalogue.

Story 10.4 AC7 + AC8 #15 — lecon MEDIUM-10.3-1 : iteration sur tous les `.py`
du module via `glob("*.py")`, pas une liste statique de 2 fichiers.
"""

from __future__ import annotations

from pathlib import Path


_ADMIN_CATALOGUE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "app"
    / "modules"
    / "admin_catalogue"
)


_BANNED_COUNTRY_STRINGS = [
    "Sénégal", "Senegal",
    "Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast",
    "Mali", "Burkina Faso", "Niger", "Togo", "Bénin", "Benin",
    "Guinée", "Guinee", "Guinea",
]


def test_no_hardcoded_country_strings_in_admin_catalogue_module():
    """Test 15 — NFR66 scan exhaustif des fichiers .py du module (lecon 10.3 M1)."""
    assert _ADMIN_CATALOGUE_DIR.is_dir(), (
        f"repertoire introuvable : {_ADMIN_CATALOGUE_DIR}"
    )
    targets = sorted(_ADMIN_CATALOGUE_DIR.glob("*.py"))
    assert len(targets) >= 9, (
        f"Attendu >= 9 fichiers, trouve {len(targets)} : {[p.name for p in targets]}"
    )
    for path in targets:
        content = path.read_text(encoding="utf-8")
        for banned in _BANNED_COUNTRY_STRINGS:
            assert banned not in content, (
                f"{path.name} contient le string pays banni '{banned}' "
                f"(NFR66 country-data-driven). Deplacer vers table BDD "
                f"(Criterion/Referential source_url) ou parametre `country`."
            )
