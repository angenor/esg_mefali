"""Constantes + registre CCC-9 pour l'audit trail catalogue (Story 10.12).

Pattern **CCC-9 byte-identique** aux stories 10.8 (`INSTRUCTION_REGISTRY`),
10.10 (`HandlerEntry`) et 10.11 (`ANNEXE_F_SOURCES`) : tuple frozen + fonction
`_validate_registry_matches_db_enum()` appelee a l'import-time (fail-fast au
boot applicatif si la synchro Python <-> migration DB derive).

Fichiers source de verite :
- DB enum `catalogue_action_enum` defini dans
  `alembic/versions/026_create_admin_catalogue_audit_trail.py` (sa.Enum).
- DB enum `workflow_level_enum` idem migration 026.
- La migration 026 est parsee via regex `re.DOTALL` a l'import : si un
  developpeur ajoute `"archive"` cote DB sans mettre a jour le tuple ici,
  `RuntimeError` leve au boot applicatif (et import-time en tests).

Constantes rate limiting : reutilisent le pattern SlowAPI
`app.core.rate_limit.limiter` de la story 9.1 (FR-013 — cle = admin_user_id).

Constantes pagination : keyset `(ts DESC, id DESC)` opaque base64 (voir
audit-trail.md §Consultation), pas d'offset.

Constantes export CSV : hard cap 50 000 lignes (defense admin malveillant),
rate limit stricte 10/hour (export plus couteux que consultation).

Non-applicable ici : CCC-6 source tracking (les constantes enum sont du
code interne, pas une entite catalogue BDD avec source_url).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final


# ---------------------------------------------------------------------------
# Registres frozen tuple — source de verite Python (miroirs des enum DB 026).
# ---------------------------------------------------------------------------

ACTION_TYPES: Final[tuple[str, ...]] = (
    "create",
    "update",
    "delete",
    "publish",
    "retire",
)

WORKFLOW_LEVELS: Final[tuple[str, ...]] = ("N1", "N2", "N3")

# Types d'entites catalogue auditables. Extensible sans migration DB (colonne
# `entity_type` est un `VARCHAR(64)` libre — voir `models.py`). Ajouter une
# valeur ici suffit pour que le filtre endpoint `?entity_type=...` soit
# accepte.
ENTITY_TYPES: Final[tuple[str, ...]] = (
    "fund",
    "intermediary",
    "referential",
    "criterion",
    "pack",
    "derivation_rule",
)


# ---------------------------------------------------------------------------
# Pagination & export — bornes dures (defense admin malveillant).
# ---------------------------------------------------------------------------

PAGE_SIZE_DEFAULT: Final[int] = 50
PAGE_SIZE_MAX: Final[int] = 200

# Nombre maximum de lignes emises par un export CSV unitaire. Au-dela, la
# reponse est tronquee avec une ligne sentinelle + header HTTP
# `X-Export-Truncated: true`. Borne choisie pour que 50 000 lignes x 9
# colonnes JSONB ~= 10 Mo soient streamees en < 30 s via `yield_per=500`
# sans OOM server-side.
EXPORT_ROW_HARD_CAP: Final[int] = 50_000

# Sentinelle inseree comme derniere ligne CSV si la query matche plus de
# `EXPORT_ROW_HARD_CAP` rows. Permet au client de detecter la troncature
# sans parser le header HTTP.
EXPORT_TRUNCATED_SENTINEL: Final[str] = (
    "# TRUNCATED_AT_50000_ROWS — refine filters or paginate"
)


# ---------------------------------------------------------------------------
# Rate limiting SlowAPI (pattern FR-013 Story 9.1, cle = admin_user_id).
# ---------------------------------------------------------------------------

RATE_LIMIT_AUDIT_TRAIL: Final[str] = "60/minute"
RATE_LIMIT_AUDIT_EXPORT: Final[str] = "10/hour"


# CLEANUP Phase Growth (Story 20.2) : SlowAPI in-memory mono-worker MVP.
# Multi-worker uvicorn necessitera Redis backend partage sous peine de
# voir la limite effective x N workers. Deferred-work.md ligne LOW-10.12-1.
_RATE_LIMIT_BACKEND_PHASE_GROWTH_TODO: Final[str] = (
    "LOW-10.12-1 — migrate SlowAPI backend to Redis if multi-worker"
)


# ---------------------------------------------------------------------------
# Validator import-time : synchro Python <-> migration Alembic 026.
# ---------------------------------------------------------------------------

_MIGRATION_PATH: Final[Path] = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "026_create_admin_catalogue_audit_trail.py"
)


def _parse_enum_values(migration_text: str, enum_name: str) -> frozenset[str]:
    """Extraire les valeurs d'un `sa.Enum(...)` nomme depuis un fichier migration.

    Le bloc `sa.Enum("a", "b", ..., name="<enum_name>", ...)` est detecte par
    regex `re.DOTALL` tolerant le formatage black multi-ligne. Les valeurs
    sont extraites via un second pass (double-quoted strings) — robuste a
    l'ordre et aux whitespaces variables.

    Retour : `frozenset[str]` des valeurs (set pour comparaison unordered).
    Leve `ValueError` si le bloc enum recherche est absent (fail-fast).
    """
    # Pattern strict : le corps de `sa.Enum(...)` ne doit contenir que des
    # chaines quotees separees par virgules + whitespaces jusqu'au `name=`.
    # Interdit le crossing d'un autre `sa.Enum(` (evite false-match sur un
    # bloc precedent en mode DOTALL).
    pattern = re.compile(
        r"sa\.Enum\(\s*((?:[\"'][^\"']+[\"']\s*,\s*)+)"
        r"name\s*=\s*[\"']" + re.escape(enum_name) + r"[\"']",
        re.DOTALL,
    )
    match = pattern.search(migration_text)
    if match is None:
        raise ValueError(
            f"Enum DB `{enum_name}` introuvable dans la migration 026 — "
            f"synchro Python <-> DB impossible a valider."
        )
    body = match.group(1)
    values = re.findall(r"[\"']([^\"']+)[\"']", body)
    return frozenset(values)


def _validate_registry_matches_db_enum() -> None:
    """Fail-fast au boot si le tuple Python derive de l'enum DB migration 026.

    Invariant : `set(ACTION_TYPES) == {valeurs sa.Enum catalogue_action_enum}`.
    Idem pour `WORKFLOW_LEVELS` <-> `workflow_level_enum`.

    Leve `RuntimeError` si divergence (pas `AssertionError` — l'erreur doit
    remonter meme en mode `python -O`). Pattern byte-identique 10.8
    `_validate_instruction_registry_startup`.
    """
    try:
        migration_text = _MIGRATION_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Migration 026 introuvable pour validation registry : "
            f"{_MIGRATION_PATH}"
        ) from exc

    try:
        db_actions = _parse_enum_values(migration_text, "catalogue_action_enum")
        db_levels = _parse_enum_values(migration_text, "workflow_level_enum")
    except ValueError as exc:
        raise RuntimeError(
            f"Parsing enum DB migration 026 a echoue : {exc}"
        ) from exc

    if set(ACTION_TYPES) != db_actions:
        raise RuntimeError(
            "Registry `ACTION_TYPES` desynchronise avec l'enum DB "
            "`catalogue_action_enum` (migration 026). "
            f"Python={set(ACTION_TYPES)!r}, DB={db_actions!r}. "
            "Ajouter la valeur manquante dans ACTION_TYPES ou migrer la DB."
        )

    if set(WORKFLOW_LEVELS) != db_levels:
        raise RuntimeError(
            "Registry `WORKFLOW_LEVELS` desynchronise avec l'enum DB "
            "`workflow_level_enum` (migration 026). "
            f"Python={set(WORKFLOW_LEVELS)!r}, DB={db_levels!r}."
        )


# Invocation import-time (fail-fast au boot applicatif + a chaque import test).
_validate_registry_matches_db_enum()
