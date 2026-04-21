"""CLI nightly — vérifie les `source_url` catalogue (Story 10.11, FR63, CCC-6).

Scanne deux sources en BDD :

1. Table centralisée `sources` (seed Annexe F + additions admin N3).
2. Colonnes `source_url` éparses sur 9 tables (migration 025).

Pour chaque URL distincte : HTTP HEAD → si `405 Method Not Allowed`
→ retombe sur GET avec `Range: bytes=0-1023` (1 Ko max, évite les PDF
lourds). Catégorise en 8 statuts, produit un rapport JSON structuré.

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
import os
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import httpx

from app.core.sources.types import (
    SCAN_TABLES,
    SENTINEL_LEGACY_PREFIX,
    USER_AGENT,
)

# --- Constantes transverses (règle 10.5 : importées depuis `types.py`) ---

_ALL_TABLES: Final[tuple[str, ...]] = ("sources", *SCAN_TABLES)

DEFAULT_TIMEOUT: Final[int] = 10
TIMEOUT_MIN: Final[int] = 5
TIMEOUT_MAX: Final[int] = 60
DEFAULT_MAX_REDIRECTS: Final[int] = 3
DEFAULT_CONCURRENCY: Final[int] = 10

# Validation module-level du default timeout (LOW-10.11-2) : si le default est
# un jour modifié hors bornes, le module ne s'importe plus.
assert TIMEOUT_MIN <= DEFAULT_TIMEOUT <= TIMEOUT_MAX, (
    f"DEFAULT_TIMEOUT={DEFAULT_TIMEOUT} hors bornes [{TIMEOUT_MIN}, {TIMEOUT_MAX}]"
)

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

# Tokens SSL-likely dans les messages d'exception httpx.ConnectError
# (MEDIUM-10.11-2 : détection robuste via `exc.__cause__` isinstance SSLError +
# fallback scan tokens case-insensitive couvrant X509, TLS, certificate).
_SSL_TOKENS: Final[tuple[str, ...]] = (
    "SSL",
    "TLS",
    "X509",
    "CERTIFICATE",
)


logger = logging.getLogger("source_check")


# --- Catégorisation ---


def _categorize(status_code: int) -> str:
    """Convertit un code HTTP en catégorie métier.

    Note : 200-299 → ok, 404 → not_found, 401/403/429/5xx → server_error,
    tout le reste → other_error.

    MEDIUM-10.11-5 : 429 mappé vers `server_error` (action admin_check_mirror
    conforme au mapping documenté CODEMAPS §2).
    """

    if 200 <= status_code < 300:
        return "ok"
    if status_code == 404:
        return "not_found"
    if status_code in (401, 403, 429):
        # MEDIUM-10.11-1 & 5 : auth_required-like et rate-limit → server_error.
        return "server_error"
    if 500 <= status_code < 600:
        return "server_error"
    return "other_error"


def _is_ssl_error(exc: BaseException) -> bool:
    """Détection robuste d'une erreur SSL (MEDIUM-10.11-2).

    Vérifie d'abord si la cause sous-jacente est `ssl.SSLError` (la manière
    canonique), puis tombe sur un scan case-insensitive des tokens SSL/TLS/
    X509/CERTIFICATE dans le message de l'exception.
    """

    cause = exc.__cause__ or exc.__context__
    if isinstance(cause, ssl.SSLError):
        return True
    message = str(exc).upper()
    return any(token in message for token in _SSL_TOKENS)


# --- Vérification d'une URL unique ---


async def check_one(
    client: httpx.AsyncClient, url: str, table: str
) -> dict:
    """Vérifie une URL : HEAD puis fallback GET Range si 405.

    Retourne un dict conforme à `REPORT_SCHEMA.sources.items`.

    Pas de `except Exception:` catch-all (règle C1 9.7) — 4 classes httpx
    catchées explicitement (`HTTPStatusError` retirée — branche morte
    LOW-10.11-1, `raise_for_status()` n'est jamais appelé).
    """

    start = datetime.now(timezone.utc)
    status: str
    http_code: int | None = None

    try:
        response = await client.head(url)
        if response.status_code == 405:
            # MEDIUM-10.11-6 : utiliser l'URL finale post-redirect, pas l'URL
            # d'origine (évite de re-suivre les redirects + dépasser max=3).
            # MEDIUM-10.11-13 : `stream=True` évite de télécharger le body
            # complet si le serveur ignore `Range`.
            async with client.stream(
                "GET",
                str(response.url),
                headers={"Range": "bytes=0-1023"},
            ) as streamed:
                http_code = streamed.status_code
                status = _categorize(http_code)
        else:
            status = _categorize(response.status_code)
            http_code = response.status_code
    except httpx.TimeoutException:
        status = "timeout"
    except httpx.TooManyRedirects:
        status = "redirect_excess"
    except httpx.ConnectError as exc:
        status = "ssl_error" if _is_ssl_error(exc) else "other_error"
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


def _build_empty_report() -> dict:
    """Rapport squelette (counts = 0) utilisé par les chemins d'erreur."""

    return {
        "generated_at": _iso_utc(datetime.now(timezone.utc)),
        "total_sources_checked": 0,
        "counts": {key: 0 for key in _COUNT_KEYS},
        "sources": [],
    }


def _boot_error_report(reason: str, url: str = "<boot>") -> dict:
    """Rapport minimal déclenchant `has_failures=true` dans le workflow.

    HIGH-10.11-2 & MEDIUM-10.11-10 : garantit qu'une erreur avant l'exécution
    réelle (secret absent, crash script) ouvre quand même une issue GitHub
    plutôt que de disparaître silencieusement.
    """

    now = _iso_utc(datetime.now(timezone.utc))
    counts = {key: 0 for key in _COUNT_KEYS}
    counts["other_error"] = 1
    return {
        "generated_at": now,
        "total_sources_checked": 1,
        "counts": counts,
        "sources": [
            {
                "source_url": url,
                "table": "boot",
                "status": "other_error",
                "http_code": None,
                "detected_at": now,
                "last_valid_at": None,
                "suggested_action": "admin_check_mirror",
                "duration_ms": 0,
                "error": reason,
            }
        ],
    }


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
                    "WHERE url NOT LIKE :sentinel_prefix"
                ).bindparams(sentinel_prefix=f"{SENTINEL_LEGACY_PREFIX}%")
            )
            for (url,) in rows:
                result[url] = "sources"

            for table in SCAN_TABLES:
                # LOW-10.11-22 : assertion défensive — le table name est
                # interpolé en f-string (SQLAlchemy ne supporte pas le
                # paramétrage des identifiers), on whitelist explicitement.
                assert table in SCAN_TABLES, f"table inattendue : {table}"
                rows = await conn.execute(
                    sql_text(
                        f"SELECT DISTINCT source_url FROM {table} "
                        "WHERE source_url IS NOT NULL "
                        "AND source_url NOT LIKE :sentinel_prefix"
                    ).bindparams(sentinel_prefix=f"{SENTINEL_LEGACY_PREFIX}%")
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


async def _check_with_semaphore(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    table: str,
) -> dict:
    """Wrapper `check_one` sous Semaphore — MEDIUM-10.11-3."""

    async with semaphore:
        return await check_one(client, url, table)


async def run(args: argparse.Namespace) -> int:
    """Pipeline complet : collecte → vérification → rapport JSON.

    Retourne toujours 0 (rapport-only, AC5 : la CI ne doit pas bloquer).

    HIGH-10.11-2 : fail-fast si `DATABASE_URL` absent en mode non-dry-run —
    écrit un rapport minimal qui déclenche quand même l'issue GitHub.
    """

    if args.dry_run:
        urls = load_dry_run_fixture(Path(args.dry_run_fixture))
    else:
        if not os.environ.get("DATABASE_URL"):
            reason = (
                "DATABASE_URL env var manquante — secret GitHub "
                "STAGING_DATABASE_URL_READ_ONLY non provisionné ?"
            )
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "metric": "source_url_check",
                        "error": reason,
                    }
                )
            )
            Path(args.output).write_text(
                json.dumps(_boot_error_report(reason), indent=2),
                encoding="utf-8",
            )
            return 0

        from app.core.config import settings

        urls = await collect_urls_from_db(settings.database_url)

    if args.only_table is not None:
        urls = {u: t for u, t in urls.items() if t == args.only_table}

    # MEDIUM-10.11-3 : borner la concurrence pour éviter DDoS auto sur
    # domaines partagés (ifrs.org, ...) et ban IP du runner GitHub.
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(
        timeout=float(args.timeout),
        follow_redirects=True,
        max_redirects=args.max_redirects,
        headers={"User-Agent": USER_AGENT},
        limits=limits,
    ) as client:
        tasks = [
            _check_with_semaphore(client, semaphore, url, table)
            for url, table in urls.items()
        ]
        # MEDIUM-10.11-4 : return_exceptions=True — une exception non-httpx
        # ne doit pas tuer le batch (AC5 exit 0 inconditionnel).
        raw_results = (
            await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        )

    results: list[dict] = []
    for raw, (url, table) in zip(raw_results, urls.items()):
        if isinstance(raw, BaseException):
            logger.error(
                json.dumps(
                    {
                        "level": "ERROR",
                        "metric": "source_url_check",
                        "source_url": url,
                        "table": table,
                        "error": f"{type(raw).__name__}: {raw}",
                    }
                )
            )
            now = _iso_utc(datetime.now(timezone.utc))
            results.append(
                {
                    "source_url": url,
                    "table": table,
                    "status": "other_error",
                    "http_code": None,
                    "detected_at": now,
                    "last_valid_at": None,
                    "suggested_action": "admin_check_mirror",
                    "duration_ms": 0,
                }
            )
        else:
            results.append(raw)

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
    if value < TIMEOUT_MIN or value > TIMEOUT_MAX:
        raise argparse.ArgumentTypeError(
            f"timeout hors plage : {value} "
            f"(attendu entre {TIMEOUT_MIN} et {TIMEOUT_MAX})"
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
        default=DEFAULT_TIMEOUT,
        help=(
            f"Timeout par requête, secondes (défaut {DEFAULT_TIMEOUT}, "
            f"bornes [{TIMEOUT_MIN}, {TIMEOUT_MAX}])."
        ),
    )
    parser.add_argument(
        "--max-redirects",
        type=int,
        default=DEFAULT_MAX_REDIRECTS,
        help=f"Nombre max de redirections suivies (défaut {DEFAULT_MAX_REDIRECTS}).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=(
            f"Nombre max de requêtes HTTP concurrentes "
            f"(défaut {DEFAULT_CONCURRENCY})."
        ),
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
    """Entry point synchrone pour `python -m` / `sys.exit`.

    MEDIUM-10.11-10 : try/except dernier recours — toute exception non
    catchée dans `run()` est convertie en rapport minimal pour que le
    workflow ouvre quand même une issue (AC5 strict : exit 0).

    LOW-10.11-3 : `basicConfig` scope à `__main__` seul + `force=True`
    pour éviter de polluer la config globale des tests.
    """

    args = build_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except BaseException as exc:  # dernier recours, script-crash-safe
        logger.exception("source_url_check crashed")
        reason = f"{type(exc).__name__}: {exc}"
        try:
            Path(args.output).write_text(
                json.dumps(
                    _boot_error_report(reason, url="<script_crash>"),
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    sys.exit(main())
