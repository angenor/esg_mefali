"""Extraction déterministe regex/dict des champs profil entreprise depuis langage naturel.

Spec V8-AXE1 (BUG-V7-001 + BUG-V7.1-001) — fallback déterministe au tool LLM
``update_company_profile`` quand le LLM laisse ≥2 champs ``null`` malgré un
texte utilisateur structuré (ex. « AgriVert Sarl, Agriculture, 15 employés,
Sénégal »).

Règles :
    - Le LLM reste prioritaire ; ce module ne couvre QUE les 5 champs cibles
      (``company_name``, ``sector``, ``employee_count``, ``country``, ``city``).
    - Tolérance accents et casse (normalisation NFD lower côté detection).
    - Premier match canonique en cas d'ambiguïté multi-sector ; warning loggé.
    - Aucune dépendance externe — regex + str natif uniquement.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import TypedDict

logger = logging.getLogger(__name__)


# Mapping synonymes FR -> valeur canonique alignee sur app.modules.company.schemas.SectorEnum.
# Toute valeur retournee DOIT etre membre de SectorEnum, sinon Pydantic leve
# ValidationError sur CompanyProfileUpdate (review V8-AXE1 CRITIQUE-1).
# Les libelles « industrie », « industriel », « tourisme », « hotellerie »
# pointent vers `autre`/`services` faute d'enum dedie.
SECTORS_FR: dict[str, list[str]] = {
    "agriculture": ["agriculture", "agricole", "agro", "elevage", "culture"],
    "energie": ["energie", "solaire", "eolien", "hydro", "biomasse"],
    "textile": ["textile", "habillement", "couture"],
    "transport": ["transport", "logistique", "fret"],
    "construction": ["construction", "btp", "batiment"],
    "agroalimentaire": ["agroalimentaire", "alimentaire"],
    "recyclage": ["recyclage", "dechets", "valorisation"],
    "artisanat": ["artisanat", "artisanal", "artisan"],
    "services": ["services", "consulting", "conseil", "tourisme", "hotellerie", "restaurant"],
    "commerce": ["commerce", "vente", "distribution"],
    "autre": ["industrie", "industriel", "manufacture"],
}

COUNTRIES_UEMOA: dict[str, list[str]] = {
    "Sénégal": ["senegal"],
    "Côte d'Ivoire": ["cote d'ivoire", "cote divoire", "ivoire"],
    "Mali": ["mali"],
    "Burkina Faso": ["burkina faso", "burkina", "burkinabe"],
    "Bénin": ["benin"],
    "Togo": ["togo"],
    "Niger": ["niger"],
    "Guinée-Bissau": ["guinee-bissau", "guinee bissau"],
}

# Pattern entreprise : 1 ou 2 mots capitalises consecutifs + forme juridique.
# Limiter a 2 mots avant la forme juridique evite de capter les prefixes
# phrastiques (« Mon Entreprise AgriVert Sarl » → AgriVert Sarl, pas la phrase
# entiere — review V8-AXE1 CRITIQUE-2). Formes longues listees en premier pour
# privilegier le match le plus complet. Lookahead inclut chiffres pour eviter
# de capter "SAS" dans "SAS123" (review V8-AXE1 ÉLEVÉ-2).
_COMPANY_NAME_RE = re.compile(
    r"\b([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇ][A-Za-zÀ-ÿ0-9'\-]+"
    r"(?:\s+[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇ][A-Za-zÀ-ÿ0-9'\-]+)?)\s+"
    r"(S\.A\.R\.L\.|S\.A\.S\.|S\.A\.|SARL|Sarl|SAS|SA)"
    r"(?![A-Za-zÀ-ÿ0-9])"
)

# Borner a 5 chiffres : Pydantic CompanyProfileUpdate limite employee_count a
# le=100_000, donc 6 chiffres provoqueraient ValidationError 422 (review
# V8-AXE1 ÉLEVÉ-4). Lookbehind/lookahead negatifs sur \\d evitent de capter
# un sous-bloc « 00000 » dans « 500000 employes » (faux positif a 0).
_EMPLOYEE_COUNT_RE = re.compile(
    r"(?<!\d)(\d{1,5})(?!\d)\s*(?:employes?|personnes?|salaries?|staff|collaborateurs?)",
    re.IGNORECASE,
)

# Cap defensif sur la longueur du texte d'entree pour eviter ReDoS / DoS
# (review V8-AXE1 ÉLEVÉ-1). 5000 caracteres couvrent largement un message
# utilisateur structure ; au-dela, on tronque silencieusement.
_MAX_INPUT_LENGTH = 5000


class ExtractedProfile(TypedDict, total=False):
    """Sous-ensemble strict des 5 champs ciblés par l'extraction déterministe."""

    company_name: str
    sector: str
    employee_count: int
    country: str
    city: str


def _normalize(text: str) -> str:
    """Lower + suppression accents (NFD) pour matching robuste."""
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _extract_company_name(text: str) -> str | None:
    """Capturer un nom propre suivi d'une forme juridique (Sarl/SA/SAS)."""
    match = _COMPANY_NAME_RE.search(text)
    if not match:
        return None
    name_part = match.group(1).strip()
    legal_form = match.group(2).strip()
    return f"{name_part} {legal_form}"


def _extract_employee_count(text: str) -> int | None:
    """Capturer le nombre d'employés via patterns FR (employé, personne, salarié)."""
    match = _EMPLOYEE_COUNT_RE.search(_normalize(text))
    if not match:
        return None
    try:
        return int(match.group(1))
    except (ValueError, TypeError):
        return None


def _extract_sector(normalized: str) -> str | None:
    """Premier match canonique parmi SECTORS_FR. Warning si multi-match."""
    matched: list[str] = []
    for canonical, synonyms in SECTORS_FR.items():
        if any(re.search(rf"\b{re.escape(syn)}\b", normalized) for syn in synonyms):
            matched.append(canonical)
    if not matched:
        return None
    if len(matched) > 1:
        logger.warning(
            "Multi-sector match in profile extraction: %s — picking first canonical",
            matched,
            extra={"metric": "profile_extraction_multi_sector", "candidates": matched},
        )
    return matched[0]


def _extract_country(normalized: str) -> str | None:
    """Premier match canonique parmi COUNTRIES_UEMOA. Word-boundary stricte."""
    for canonical, synonyms in COUNTRIES_UEMOA.items():
        for syn in synonyms:
            if re.search(rf"\b{re.escape(syn)}\b", normalized):
                return canonical
    return None


def extract_profile_from_text(text: str) -> ExtractedProfile:
    """Extraire les champs profil détectables depuis ``text``.

    Retourne un dict avec uniquement les clés effectivement matchées (pas de
    ``None`` explicites). Champ ``city`` non couvert par cette V8-AXE1
    (réservé au LLM ; trop de faux positifs avec un dict statique).

    Args:
        text: Message utilisateur brut (peut être vide / None-like → {}).

    Returns:
        ExtractedProfile contenant 0 à 4 clés.
    """
    if not isinstance(text, str) or not text:
        return {}

    # Cap defensif anti-DoS / ReDoS (review V8-AXE1 ÉLEVÉ-1).
    if len(text) > _MAX_INPUT_LENGTH:
        text = text[:_MAX_INPUT_LENGTH]

    result: ExtractedProfile = {}
    normalized = _normalize(text)

    name = _extract_company_name(text)
    if name:
        result["company_name"] = name

    employees = _extract_employee_count(text)
    if employees is not None:
        result["employee_count"] = employees

    sector = _extract_sector(normalized)
    if sector:
        result["sector"] = sector

    country = _extract_country(normalized)
    if country:
        result["country"] = country

    return result
