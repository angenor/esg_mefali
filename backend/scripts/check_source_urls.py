"""CLI nightly — vérifie les `source_url` catalogue (Story 10.11, FR63, CCC-6).

Scanne deux sources en BDD :

1. Table centralisée `sources` (seed Annexe F + additions admin N3).
2. Colonnes `source_url` éparses sur 9 tables (migration 025).

Pour chaque URL distincte : HTTP HEAD → si `405 Method Not Allowed`
→ retombe sur GET avec `Range: bytes=0-1023` (1 Ko max, évite les PDF
lourds). Catégorise en 7 statuts, produit un rapport JSON structuré.

Le script **ne bloque jamais** la CI : il retourne toujours `0`. Le
workflow `.github/workflows/check-sources.yml` ouvre une issue GitHub
si le rapport contient ≥ 1 source KO.

Usage :

    python scripts/check_source_urls.py --output report.json
    python scripts/check_source_urls.py --dry-run --output /tmp/r.json
    python scripts/check_source_urls.py --timeout 30 --max-redirects 3

Story 10.11 — choix verrouillés pré-dev (Q1 httpx, Q2 HEAD+GET Range,
Q3 timeout CLI bornes [5, 60], Q4 issue GitHub seule — pas de Mailgun MVP).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import httpx

# --- Constantes transverses (importées aussi par les tests) ---

USER_AGENT: Final[str] = "MefaliSourceChecker/1.0 (+https://mefali.com)"
SENTINEL_LEGACY_PREFIX: Final[str] = "legacy://"

# 9 tables portant une colonne `source_url` (migration 025).
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

_ALL_TABLES: Final[tuple[str, ...]] = ("sources", *SCAN_TABLES)

_STATUS_TO_ACTION: Final[dict[str, str | None]] = {
    "ok": "no_action",
    "not_found": "admin_update_url",
    "ssl_error": "admin_verify_ssl",
    "server_error": "admin_check_mirror",
    "timeout": "admin_check_mirror",
    "redirect_excess": "admin_update_url",
    "other_error": "admin_check_mirror",
}

_COUNT_KEYS: Final[tuple[str, ...]] = (
    "ok",
    "not_found",
    "timeout",
    "redirect_excess",
    "ssl_error",
    "server_error",
    "other_error",
)


logger = logging.getLogger("source_check")


# --- Catégorisation ---


def _categorize(status_code: int) -> str:
    """Convertit un code HTTP en catégorie métier.

    Note : 200-299 → ok, 404 → not_found, 5xx → server_error,
    tout le reste → other_error.
    """

    if 200 <= status_code < 300:
        return "ok"
    if status_code == 404:
        return "not_found"
    if 500 <= status_code < 600:
        return "server_error"
    return "other_error"


# --- Vérification d'une URL unique ---


async def check_one(
    client: httpx.AsyncClient, url: str, table: str
) -> dict:
    """Vérifie une URL : HEAD puis fallback GET Range si 405.

    Retourne un dict conforme à `REPORT_SCHEMA.sources.items`.

    Pas de `except Exception:` catch-all (règle C1 9.7) — 5 classes httpx
    catchées explicitement.
    """

    start = datetime.now(timezone.utc)
    status: str
    http_code: int | None = None

    try:
        response = await client.head(url)
        if response.status_code == 405:
            response = await client.get(
                url, headers={"Range": "bytes=0-1023"}
            )
        status = _categorize(response.status_code)
        http_code = response.status_code
    except httpx.TimeoutException:
        status = "timeout"
    except httpx.TooManyRedirects:
        status = "redirect_excess"
    except httpx.ConnectError as exc:
        status = "ssl_error" if "SSL" in str(exc) else "other_error"
    except httpx.HTTPStatusError as exc:
        http_code = exc.response.status_code
        status = _categorize(http_code)
    except httpx.RequestError:
        status = "other_error"

    now = datetime.now(timezone.utc)
    duration_ms = int((now - start).total_seconds() * 1000)

    return {
        "source_url": url,
        "table": table,
        "status": status,
        "http_code": http_code,
        "detected_at": _iso_utc(start),
        "last_valid_at": _iso_utc(start) if status == "ok" else None,
        "suggested_action": _STATUS_TO_ACTION.get(status),
        "duration_ms": duration_ms,
    }


def _iso_utc(moment: datetime) -> str:
    """Retourne une datetime au format ISO 8601 UTC Z-suffixed."""

    return moment.astimezone(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


# --- Collecte des URLs ---


async def collect_urls_from_db(db_url: str) -> dict[str, str]:
    """Interroge la BDD et retourne `{url: table_of_origin}`.

    - UNION SELECT url FROM sources (centralisée) + 9 SELECT DISTINCT
      source_url FROM <table> WHERE source_url IS NOT NULL AND
      source_url NOT LIKE 'legacy://%'.
    - Dédoublonnage : si une URL apparaît dans `sources` ET dans une
      table éparse, la table `sources` gagne (centralisation priorisée).

    Import différé de sqlalchemy pour garder les tests unit purs (pas de
    BDD).
    """

    # Import différé — sqlalchemy est lourd, pas utile en mode --dry-run.
    from sqlalchemy import text as sql_text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(db_url)
    try:
        result: dict[str, str] = {}
        async with engine.connect() as conn:
            rows = await conn.execute(
                sql_text(
                    "SELECT url FROM sources "
                    "WHERE url NOT LIKE 'legacy://%'"
                )
            )
            for (url,) in rows:
                result[url] = "sources"

            for table in SCAN_TABLES:
                rows = await conn.execute(
                    sql_text(
                        f"SELECT DISTINCT source_url FROM {table} "
                        "WHERE source_url IS NOT NULL "
                        "AND source_url NOT LIKE 'legacy://%'"
                    )
                )
                for (url,) in rows:
                    # `sources` gagne en cas de duplication.
                    result.setdefault(url, table)
        return result
    finally:
        await engine.dispose()


def load_dry_run_fixture(fixture_path: Path) -> dict[str, str]:
    """Charge une fixture JSON `{"urls": [{"url": ..., "table": ...}, ...]}`.

    Pattern règle d'or 10.5 : le test dry-run lit un vrai fichier sur
    disque, pas un mock `json.load`.
    """

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return {entry["url"]: entry["table"] for entry in payload["urls"]}


# --- Construction du rapport ---


def build_report(results: list[dict]) -> dict:
    """Assemble le rapport final (conforme `REPORT_SCHEMA`)."""

    counts = {key: 0 for key in _COUNT_KEYS}
    for item in results:
        counts[item["status"]] += 1
    return {
        "generated_at": _iso_utc(datetime.now(timezone.utc)),
        "total_sources_checked": len(results),
        "counts": counts,
        "sources": results,
    }


# --- Entry point ---


async def run(args: argparse.Namespace) -> int:
    """Pipeline complet : collecte → vérification → rapport JSON.

    Retourne toujours 0 (rapport-only, AC5 : la CI ne doit pas bloquer).
    """

    if args.dry_run:
        urls = load_dry_run_fixture(Path(args.dry_run_fixture))
    else:
        from app.core.config import settings

        urls = await collect_urls_from_db(settings.database_url)

    if args.only_table is not None:
        urls = {u: t for u, t in urls.items() if t == args.only_table}

    async with httpx.AsyncClient(
        timeout=float(args.timeout),
        follow_redirects=True,
        max_redirects=args.max_redirects,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        tasks = [check_one(client, url, table) for url, table in urls.items()]
        results = await asyncio.gather(*tasks) if tasks else []

    report = build_report(results)
    Path(args.output).write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )

    counts = report["counts"]
    failures = report["total_sources_checked"] - counts["ok"]
    logger.info(
        json.dumps(
            {
                "level": "INFO",
                "metric": "source_url_check",
                "total": report["total_sources_checked"],
                "ok": counts["ok"],
                "failures": failures,
            }
        )
    )
    return 0


def _timeout_range(raw: str) -> int:
    """argparse type validator — borne [5, 60] (Q3 verrouillée)."""

    value = int(raw)
    if value < 5 or value > 60:
        raise argparse.ArgumentTypeError(
            f"timeout hors plage : {value} (attendu entre 5 et 60)"
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser argparse (exposé pour tests)."""

    parser = argparse.ArgumentParser(
        prog="check_source_urls",
        description=(
            "Vérifie l'état HTTP (HEAD+fallback GET) des source_url "
            "catalogue. Produit un rapport JSON."
        ),
    )
    parser.add_argument(
        "--output",
        default="/tmp/source_urls_report.json",
        help="Chemin du rapport JSON (défaut /tmp/source_urls_report.json).",
    )
    parser.add_argument(
        "--timeout",
        type=_timeout_range,
        default=10,
        help="Timeout par requête, secondes (défaut 10, bornes [5, 60]).",
    )
    parser.add_argument(
        "--max-redirects",
        type=int,
        default=3,
        help="Nombre max de redirections suivies (défaut 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="N'accède pas à la BDD — lit la fixture JSON (--dry-run-fixture).",
    )
    parser.add_argument(
        "--dry-run-fixture",
        default="backend/tests/test_scripts/fixtures/dry_run_fixture.json",
        help="Fixture utilisée par --dry-run (chemin relatif accepté).",
    )
    parser.add_argument(
        "--only-table",
        choices=list(_ALL_TABLES),
        default=None,
        help="Filtre le scan sur une seule table (debug).",
    )
    return parser


def main() -> int:
    """Entry point synchrone pour `python -m` / `sys.exit`."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
