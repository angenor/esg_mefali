"""Helper de reparation JSON tolerant pour sorties LLM imparfaites.

Pattern §4decies (Lecon 40) : sur les tools de generation creative
(plan d'action, recommandations), les LLM produisent parfois du JSON
quasi-valide (trailing comma, single quotes, cles non quotees). Au
lieu de rejeter immediatement et declencher un retry coute en
tokens, on tente une reparation deterministe avant rejet.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _try_parse(text: str) -> Any | None:
    """Tenter `json.loads`. Retourne le payload parse ou None."""
    try:
        return json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return None


def _strip_trailing_commas(text: str) -> str:
    """Supprimer les virgules trainantes avant `}` ou `]`."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _quote_unquoted_keys(text: str) -> str:
    """Quoter les cles non quotees apres `{` ou `,`.

    Heuristique : `key:` -> `"key":` quand la cle est un identifiant
    Python valide. Ne touche pas aux valeurs.
    """
    return re.sub(
        r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:",
        r'\1"\2":',
        text,
    )


def _convert_top_level_single_quotes(text: str) -> str:
    """Conversion safe single -> double quotes pour des JSON dont AUCUNE
    valeur ne contient de double quote.

    Heuristique conservative pour le francais : on ne tente la conversion
    que si `text` ne contient AUCUN double quote (sinon le risque de
    casser des apostrophes francaises dans les valeurs deja quotees est
    trop eleve, ex: `"d'action"` -> `"d"action"`). Si la condition n'est
    pas remplie, on retourne le texte inchange.
    """
    if '"' in text:
        return text
    return text.replace("'", '"')


def repair_json(text: str) -> Any | None:
    """Reparer un JSON malforme produit par un LLM.

    Ordre des passes (cumulatives, on parse a chaque etape) :
    1. parse direct
    2. trailing comma removal
    3. unquoted keys -> quoted
    4. single quotes -> double quotes (uniquement si aucun double
       quote dans le texte ; sinon trop de risques de corruption en
       francais — review V8-AXE2 finding #2).

    Retourne le payload parse (dict ou list) ou None si aucune
    passe ne reussit.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    # 1. Parse direct
    parsed = _try_parse(text)
    if parsed is not None:
        return parsed

    # 2. Trailing comma
    cleaned = _strip_trailing_commas(text)
    parsed = _try_parse(cleaned)
    if parsed is not None:
        return parsed

    # 3. Unquoted keys
    cleaned = _quote_unquoted_keys(cleaned)
    parsed = _try_parse(cleaned)
    if parsed is not None:
        return parsed

    # 4. Single -> double quotes (passe conservative : seulement si
    # aucun double quote present — voir docstring helper).
    cleaned_quotes = _convert_top_level_single_quotes(cleaned)
    if cleaned_quotes is not cleaned:
        parsed = _try_parse(cleaned_quotes)
        if parsed is not None:
            return parsed

    return None
