"""Types du module `sources` (Story 10.11).

Regroupe :
    - `SourceSeed` : entrée catalogue Annexe F (tuple frozen).
    - `SourceCheckResult` : résultat d'une vérification HEAD/GET.
    - `REPORT_SCHEMA` : JSON Schema validé par `jsonschema.validate`.
    - `SCAN_TABLES` : 9 tables portant une colonne `source_url`.
    - `USER_AGENT`, `SENTINEL_LEGACY_PREFIX` : constantes transverses.

Pattern CCC-9 (Story 10.8) : tuple frozen + dataclass(frozen=True) stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

SourceType = Literal["pdf", "web", "regulation", "peer_reviewed"]
StatusValue = Literal[
    "ok",
    "not_found",
    "timeout",
    "redirect_excess",
    "ssl_error",
    "server_error",
    "other_error",
]
SuggestedAction = Literal[
    "admin_update_url",
    "admin_verify_ssl",
    "admin_check_mirror",
    "no_action",
]


USER_AGENT: Final[str] = "MefaliSourceChecker/1.0 (+https://mefali.com)"
SENTINEL_LEGACY_PREFIX: Final[str] = "legacy://"

# 9 tables portant une colonne `source_url` (migration 025).
# L'ordre est stable pour faciliter la lecture des rapports.
SCAN_TABLES: Final[tuple[str, ...]] = (
    "funds",
    "intermediaries",
    "criteria",
    "referentials",
    "packs",
    "document_templates",
    "reusable_sections",
    "admin_maturity_requirements",
    "admin_maturity_levels",
)


@dataclass(frozen=True, slots=True)
class SourceSeed:
    """Entrée catalogue Annexe F.

    Attributs :
        url : URL canonique (unique au sein du tuple `ANNEXE_F_SOURCES`).
        source_type : type parmi les 4 valeurs de l'enum BDD `source_type_enum`.
        description : libellé court (≤ 120 chars) — usage debug/audit.
    """

    url: str
    source_type: SourceType
    description: str


@dataclass(frozen=True, slots=True)
class SourceCheckResult:
    """Résultat d'une vérification HTTP pour une URL donnée.

    Attributs :
        source_url : URL vérifiée.
        table : origine ("sources" ou nom de table pour colonnes éparses).
        status : catégorie finale (voir `StatusValue`).
        http_code : code HTTP (ou None si exception avant réponse).
        detected_at : ISO 8601 UTC Z-suffixed (début de la requête).
        last_valid_at : ISO 8601 UTC Z ou None si inconnu.
        suggested_action : action recommandée pour l'admin ou None.
        duration_ms : durée totale de la vérification (>= 0).
    """

    source_url: str
    table: str
    status: StatusValue
    http_code: int | None
    detected_at: str
    last_valid_at: str | None
    suggested_action: SuggestedAction | None
    duration_ms: int


# JSON Schema du rapport nightly (AC4).
# Usage : jsonschema.validate(report, REPORT_SCHEMA).
REPORT_SCHEMA: Final[dict] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["generated_at", "total_sources_checked", "counts", "sources"],
    "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "total_sources_checked": {"type": "integer", "minimum": 0},
        "counts": {
            "type": "object",
            "required": [
                "ok",
                "not_found",
                "timeout",
                "redirect_excess",
                "ssl_error",
                "server_error",
                "other_error",
            ],
            "additionalProperties": {"type": "integer", "minimum": 0},
        },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "source_url",
                    "table",
                    "status",
                    "http_code",
                    "detected_at",
                    "last_valid_at",
                    "suggested_action",
                    "duration_ms",
                ],
                "properties": {
                    "source_url": {"type": "string"},
                    "table": {"type": "string"},
                    "status": {
                        "enum": [
                            "ok",
                            "not_found",
                            "timeout",
                            "redirect_excess",
                            "ssl_error",
                            "server_error",
                            "other_error",
                        ]
                    },
                    "http_code": {"type": ["integer", "null"]},
                    "detected_at": {"type": "string", "format": "date-time"},
                    "last_valid_at": {"type": ["string", "null"]},
                    "suggested_action": {
                        "type": ["string", "null"],
                        "enum": [
                            "admin_update_url",
                            "admin_verify_ssl",
                            "admin_check_mirror",
                            "no_action",
                            None,
                        ],
                    },
                    "duration_ms": {"type": "integer", "minimum": 0},
                },
            },
        },
    },
}
