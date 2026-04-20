"""CLI d'anonymisation dump PROD → STAGING (Story 10.7 AC5).

Usage :
    python -m scripts.anonymize_prod_to_staging \\
        --source /tmp/prod_dump.sql \\
        --output /tmp/staging_dump.sql

Prérequis env :
    ANONYMIZATION_SALT=<secret-32+chars>   # AWS Secrets Manager mefali/ops

Flow (fail-fast D8.2) :
    1. Lecture streaming ligne par ligne (pas de load RAM 500MB).
    2. Substitution des 15 PII_PATTERNS par mapping déterministe SHA256.
    3. Re-scan post-anonymisation → AnonymizationPatternViolation si résiduel.
    4. Écriture dump anonymisé + log INFO substitutions par pattern.

Exit codes :
    0 — Succès (zéro PII résiduel).
    1 — Erreur I/O (AnonymizationDumpError).
    2 — Pattern violation (AnonymizationPatternViolation — fail-fast).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

from app.core.anonymization import (
    ANONYMIZATION_SALT_ENV,
    AnonymizationDumpError,
    AnonymizationPatternViolation,
    anonymize_text,
    scan_for_pii,
)

logger = logging.getLogger("anonymize_prod_to_staging")


def _require_salt() -> str:
    """Fail-fast si `ANONYMIZATION_SALT` absent — préserve le déterminisme
    des mappings (sans salt fixe, un refresh STAGING mensuel casserait les
    jointures post-anonymisation)."""
    salt = os.environ.get(ANONYMIZATION_SALT_ENV, "")
    if not salt:
        raise SystemExit(
            f"{ANONYMIZATION_SALT_ENV} env var required for deterministic "
            f"mapping. Read from AWS Secrets Manager mefali/ops."
        )
    if len(salt) < 16:
        raise SystemExit(
            f"{ANONYMIZATION_SALT_ENV} must be at least 16 chars (got {len(salt)})."
        )
    return salt


def anonymize_dump(source: Path, output: Path, salt: str) -> dict[str, int]:
    """Anonymise un dump SQL et vérifie fail-fast post-anonymisation.

    Args:
        source: dump SQL PROD filtré (tables BLOB exclues en amont).
        output: chemin de sortie pour le dump anonymisé.
        salt: secret déterministe.

    Returns:
        compteur {pattern_name: nombre_substitutions}.

    Raises:
        AnonymizationDumpError: I/O échec.
        AnonymizationPatternViolation: ≥ 1 PII résiduel post-anonymisation.
    """
    if not source.is_file():
        raise AnonymizationDumpError(f"Source dump not found: {source}")

    substitution_counts: Counter[str] = Counter()

    # Streaming ligne-par-ligne pour dumps multi-MB
    try:
        with source.open("r", encoding="utf-8") as src, output.open(
            "w", encoding="utf-8"
        ) as dst:
            for line in src:
                anonymized_line, results = anonymize_text(line, salt)
                for result in results:
                    substitution_counts[result.pattern_name] += 1
                dst.write(anonymized_line)
    except OSError as exc:
        raise AnonymizationDumpError(
            f"I/O error during anonymization: {exc}"
        ) from exc

    # Re-scan fail-fast (règle d'or 10.5 : effet observable sur fichier réel)
    try:
        content = output.read_text(encoding="utf-8")
    except OSError as exc:
        raise AnonymizationDumpError(
            f"Cannot re-read anonymized dump for validation: {exc}"
        ) from exc

    residual = scan_for_pii(content)
    if residual:
        preview = residual[:5]
        raise AnonymizationPatternViolation(
            f"Residual PII detected after anonymization "
            f"({len(residual)} violations, first 5: {preview}). "
            f"Enrich PII_PATTERNS or fix upstream filtering before retry."
        )

    return dict(substitution_counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="anonymize_prod_to_staging",
        description="Anonymise un dump PROD pour refresh STAGING (D8.2).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Chemin du dump SQL PROD (filtré tables BLOB exclues).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Chemin de sortie du dump anonymisé.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log niveau DEBUG (INFO par défaut).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        stream=sys.stderr,
    )

    salt = _require_salt()

    try:
        counts = anonymize_dump(args.source, args.output, salt)
    except AnonymizationPatternViolation as exc:
        logger.critical("Anonymization FAILED (fail-fast D8.2): %s", exc)
        # Audit log JSON sur stdout pour ingestion observability
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": "pattern_violation",
                    "message": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2
    except AnonymizationDumpError as exc:
        logger.error("Anonymization I/O error: %s", exc)
        print(
            json.dumps({"status": "failed", "reason": "io_error", "message": str(exc)}),
            file=sys.stderr,
        )
        return 1

    total_substitutions = sum(counts.values())
    logger.info(
        "Anonymization SUCCEEDED — %d substitutions, zero residual PII",
        total_substitutions,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "total_substitutions": total_substitutions,
                "counts_by_pattern": counts,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
