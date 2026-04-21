"""Module `sources` — sourcing documentaire + vérification HTTP nightly.

Story 10.11. CCC-6 NFR-SOURCE-TRACKING, FR63.

Exports :
    - ANNEXE_F_SOURCES : tuple frozen de `SourceSeed` (22+ sources Annexe F PRD)
    - SourceSeed : dataclass frozen d'une entrée catalogue
    - SourceCheckResult : dataclass résultat d'un HEAD
    - REPORT_SCHEMA : JSON Schema du rapport nightly
    - SCAN_TABLES : tuple des 9 tables scannées pour colonnes `source_url` éparses
"""

from app.core.sources.annexe_f_seed import ANNEXE_F_SOURCES
from app.core.sources.types import (
    REPORT_SCHEMA,
    SCAN_TABLES,
    SENTINEL_LEGACY_PREFIX,
    USER_AGENT,
    SourceCheckResult,
    SourceSeed,
)

__all__ = [
    "ANNEXE_F_SOURCES",
    "REPORT_SCHEMA",
    "SCAN_TABLES",
    "SENTINEL_LEGACY_PREFIX",
    "USER_AGENT",
    "SourceCheckResult",
    "SourceSeed",
]
