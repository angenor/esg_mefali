"""Tests du script `scripts/check_source_urls.py` (Story 10.11, AC3/AC4/AC8).

Couverture :

- 6 tests unit `respx` mock HTTP (statuts : ok, 404, redirect>3, timeout,
  ssl, fallback HEAD 405 → GET Range 1 Ko).
- 1 test scan anti-`except Exception` (règle C1 9.7).
- 1 test `jsonschema.validate` sur un rapport produit via `--dry-run`
  (règle d'or 10.5 : effet observable = fichier sur disque).
- 2 tests `@pytest.mark.integration` env-gated (`SOURCE_URL_CHECK=1`,
  règle C2 9.7) : smoke httpbin.org + dry-run E2E sur disque.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import httpx
import jsonschema
import pytest
import respx  # noqa: F401

from scripts import check_source_urls
from scripts.check_source_urls import (
    USER_AGENT,
    build_parser,
    build_report,
    check_one,
    load_dry_run_fixture,
)

from app.core.sources.types import REPORT_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "check_source_urls.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dry_run_fixture.json"


# =====================================================================
# Helpers
# =====================================================================


def _run(coro):
    """Exécute une coroutine dans un event loop dédié."""

    return asyncio.run(coro)


async def _call_check_one(url: str) -> dict:
    async with httpx.AsyncClient(
        timeout=2.0,
        follow_redirects=True,
        max_redirects=3,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        return await check_one(client, url, "sources")


# =====================================================================
# Unit tests (respx mock — AC3)
# =====================================================================


@pytest.mark.unit
@respx.mock
def test_head_200_returns_status_ok() -> None:
    """HEAD 200 → status `ok`, http_code=200, suggested_action=no_action."""

    url = "https://example.test/ok"
    respx.head(url).mock(return_value=httpx.Response(200))

    result = _run(_call_check_one(url))

    assert result["status"] == "ok"
    assert result["http_code"] == 200
    assert result["suggested_action"] == "no_action"
    assert result["last_valid_at"] is not None
    assert result["duration_ms"] >= 0


@pytest.mark.unit
@respx.mock
def test_head_404_returns_status_not_found() -> None:
    """HEAD 404 → status `not_found`, suggested_action=admin_update_url."""

    url = "https://example.test/missing"
    respx.head(url).mock(return_value=httpx.Response(404))

    result = _run(_call_check_one(url))

    assert result["status"] == "not_found"
    assert result["http_code"] == 404
    assert result["suggested_action"] == "admin_update_url"
    assert result["last_valid_at"] is None


@pytest.mark.unit
@respx.mock
def test_redirect_chain_gt_3_returns_redirect_excess() -> None:
    """Une chaîne de > 3 redirects → status `redirect_excess`."""

    # 4 redirects consécutifs → httpx lève TooManyRedirects avec max=3.
    respx.head("https://a.test/1").mock(
        return_value=httpx.Response(301, headers={"Location": "https://a.test/2"})
    )
    respx.head("https://a.test/2").mock(
        return_value=httpx.Response(301, headers={"Location": "https://a.test/3"})
    )
    respx.head("https://a.test/3").mock(
        return_value=httpx.Response(301, headers={"Location": "https://a.test/4"})
    )
    respx.head("https://a.test/4").mock(
        return_value=httpx.Response(301, headers={"Location": "https://a.test/5"})
    )
    respx.head("https://a.test/5").mock(return_value=httpx.Response(200))

    result = _run(_call_check_one("https://a.test/1"))

    assert result["status"] == "redirect_excess"
    assert result["http_code"] is None


@pytest.mark.unit
@respx.mock
def test_timeout_exception_returns_status_timeout() -> None:
    """httpx.TimeoutException → status `timeout`."""

    url = "https://slow.test/resource"
    respx.head(url).mock(side_effect=httpx.TimeoutException("read timeout"))

    result = _run(_call_check_one(url))

    assert result["status"] == "timeout"
    assert result["http_code"] is None
    assert result["suggested_action"] == "admin_check_mirror"


@pytest.mark.unit
@respx.mock
def test_ssl_error_returns_status_ssl_error() -> None:
    """ConnectError contenant 'SSL' → status `ssl_error`."""

    url = "https://bad-ssl.test/"
    respx.head(url).mock(
        side_effect=httpx.ConnectError("SSL: certificate has expired")
    )

    result = _run(_call_check_one(url))

    assert result["status"] == "ssl_error"
    assert result["suggested_action"] == "admin_verify_ssl"
    assert result["http_code"] is None


@pytest.mark.unit
@respx.mock
def test_rate_limit_429_mapped_to_server_error() -> None:
    """HTTP 429 (rate-limit) → status `server_error` (mapping CODEMAPS §2).

    MEDIUM-10.11-5 : 429 doit être catégorisé `server_error` pour que
    `suggested_action = admin_check_mirror` soit cohérent.
    """

    url = "https://ratelimited.test/"
    respx.head(url).mock(return_value=httpx.Response(429))

    result = _run(_call_check_one(url))

    assert result["status"] == "server_error"
    assert result["http_code"] == 429
    assert result["suggested_action"] == "admin_check_mirror"


@pytest.mark.unit
@respx.mock
def test_auth_401_mapped_to_server_error() -> None:
    """HTTP 401 → status `server_error` (Sedex/EcoVadis-like portails auth).

    MEDIUM-10.11-1 : 401/403 mappés comme auth-required (server_error +
    admin_check_mirror) au lieu de tomber en `other_error`.
    """

    url = "https://auth.test/"
    respx.head(url).mock(return_value=httpx.Response(401))

    result = _run(_call_check_one(url))

    assert result["status"] == "server_error"
    assert result["http_code"] == 401


@pytest.mark.unit
@respx.mock
def test_request_error_categorized_as_other_error() -> None:
    """httpx.RequestError (parent class) → status `other_error`."""

    url = "https://example.test/request-err"
    respx.head(url).mock(side_effect=httpx.RequestError("dns failure"))

    result = _run(_call_check_one(url))
    assert result["status"] == "other_error"
    assert result["http_code"] is None


@pytest.mark.unit
@respx.mock
def test_connect_error_without_ssl_is_other_error() -> None:
    """ConnectError sans mention 'SSL' → status `other_error`."""

    url = "https://example.test/conn"
    respx.head(url).mock(side_effect=httpx.ConnectError("DNS resolution failed"))

    result = _run(_call_check_one(url))
    assert result["status"] == "other_error"


@pytest.mark.unit
@respx.mock
def test_head_405_falls_back_to_get_range_1kb() -> None:
    """HEAD 405 → fallback GET avec `Range: bytes=0-1023` → status final ok."""

    url = "https://strict.test/resource"
    respx.head(url).mock(return_value=httpx.Response(405))
    get_route = respx.get(url).mock(return_value=httpx.Response(206))

    result = _run(_call_check_one(url))

    assert get_route.called
    # Vérifie que le fallback envoie bien le header Range.
    called = get_route.calls[0].request
    assert called.headers.get("Range") == "bytes=0-1023"
    assert result["status"] == "ok"
    assert result["http_code"] == 206


# =====================================================================
# Script-level tests (AC3 bullet scan + AC4 schema)
# =====================================================================


@pytest.mark.unit
def test_no_generic_except_in_script() -> None:
    """Scan `scripts/check_source_urls.py` — aucun `except Exception:` autorisé.

    Règle C1 9.7 : exceptions narrowly scoped (5 classes httpx explicites).
    """

    content = SCRIPT_PATH.read_text(encoding="utf-8")
    # Code only — autorise "except Exception" dans les docstrings/commentaires.
    code_lines = [
        line
        for line in content.splitlines()
        if not line.lstrip().startswith("#")
    ]
    code = "\n".join(code_lines)
    matches = re.findall(r"^\s*except\s+Exception\b", code, flags=re.MULTILINE)
    assert matches == [], (
        f"`except Exception:` interdit dans le script ; trouvé {len(matches)} hit(s)"
    )


@pytest.mark.unit
def test_build_parser_exposes_five_flags() -> None:
    """AC1 : argparse doit exposer les 5 flags documentés."""

    parser = build_parser()
    help_text = parser.format_help()
    for flag in [
        "--output",
        "--timeout",
        "--max-redirects",
        "--dry-run",
        "--only-table",
    ]:
        assert flag in help_text, f"Flag manquant : {flag}"


@pytest.mark.unit
def test_timeout_rejects_out_of_range(capsys: pytest.CaptureFixture) -> None:
    """Bornes Q3 verrouillées : timeout ∉ [5, 60] → argparse error."""

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--timeout", "3"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--timeout", "120"])


@pytest.mark.unit
def test_report_schema_validates_dry_run(tmp_path: Path) -> None:
    """AC4 : `--dry-run` produit un rapport validant `REPORT_SCHEMA`.

    Règle d'or 10.5 : on compare le fichier JSON **écrit sur disque**
    (effet observable), pas un objet mocké.
    """

    output = tmp_path / "report.json"
    parser = build_parser()
    args = parser.parse_args(
        [
            "--dry-run",
            "--dry-run-fixture",
            str(FIXTURE_PATH),
            "--output",
            str(output),
        ]
    )

    # Mock respx pour que les 3 URLs renvoient différents statuts.
    with respx.mock() as mock:
        mock.head("https://example.test/ok").mock(
            return_value=httpx.Response(200)
        )
        mock.head("https://example.test/missing").mock(
            return_value=httpx.Response(404)
        )
        mock.head("https://example.test/slow").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        exit_code = asyncio.run(check_source_urls.run(args))

    assert exit_code == 0
    assert output.exists()
    report = json.loads(output.read_text(encoding="utf-8"))
    jsonschema.validate(report, REPORT_SCHEMA)

    # Sanity checks supplémentaires.
    assert report["total_sources_checked"] == 3
    counts = report["counts"]
    assert counts["ok"] + counts["not_found"] + counts["timeout"] == 3


@pytest.mark.unit
def test_load_dry_run_fixture_returns_url_to_table_mapping() -> None:
    """Le loader fixture doit retourner `{url: table}` conforme."""

    urls = load_dry_run_fixture(FIXTURE_PATH)
    assert len(urls) == 3
    assert urls["https://example.test/ok"] == "sources"
    assert urls["https://example.test/missing"] == "funds"


@pytest.mark.unit
def test_main_invokes_run_via_asyncio(tmp_path, monkeypatch) -> None:
    """Le point d'entrée `main()` appelle `asyncio.run(run(args))`.

    Couvre les branches `main()` + `if __name__ == "__main__"` (branche
    skippée sous pytest mais la fonction `main` est exécutable directement).
    """

    output = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_source_urls.py",
            "--dry-run",
            "--dry-run-fixture",
            str(FIXTURE_PATH),
            "--output",
            str(output),
        ],
    )
    with respx.mock() as mock:
        mock.head("https://example.test/ok").mock(return_value=httpx.Response(200))
        mock.head("https://example.test/missing").mock(return_value=httpx.Response(404))
        mock.head("https://example.test/slow").mock(
            side_effect=httpx.TimeoutException("slow")
        )
        exit_code = check_source_urls.main()
    assert exit_code == 0
    assert output.exists()


@pytest.mark.unit
def test_only_table_filter_restricts_scan(tmp_path) -> None:
    """`--only-table funds` ne scanne que les URLs de la table `funds`."""

    output = tmp_path / "report.json"
    parser = build_parser()
    args = parser.parse_args(
        [
            "--dry-run",
            "--dry-run-fixture",
            str(FIXTURE_PATH),
            "--output",
            str(output),
            "--only-table",
            "funds",
        ]
    )
    with respx.mock() as mock:
        mock.head("https://example.test/missing").mock(
            return_value=httpx.Response(404)
        )
        exit_code = asyncio.run(check_source_urls.run(args))
    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    # Seule la source `funds` (missing) est retenue — les 2 autres filtrées.
    assert report["total_sources_checked"] == 1
    assert report["sources"][0]["table"] == "funds"


@pytest.mark.unit
def test_collect_urls_from_db_returns_dedup_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`collect_urls_from_db` doit dédoublonner centralisé > éparse."""

    # Mock léger de l'engine/connection — on ne teste pas SQLAlchemy,
    # juste la logique de merge `sources` > `SCAN_TABLES`.
    import types

    fake_rows: dict[str, list[tuple[str]]] = {
        "sources": [("https://dup.test/a",), ("https://only-sources.test/b",)],
    }
    # Ajoute 1 URL dupliquée (doit rester `sources`) + 1 URL exclusive funds.
    for table in check_source_urls.SCAN_TABLES:
        if table == "funds":
            fake_rows[table] = [
                ("https://dup.test/a",),
                ("https://only-funds.test/c",),
            ]
        else:
            fake_rows[table] = []

    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def __iter__(self):
            return iter(self._rows)

    class _FakeConn:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def execute(self, stmt):
            text = str(stmt)
            if "FROM sources" in text:
                return _FakeResult(fake_rows["sources"])
            for table in check_source_urls.SCAN_TABLES:
                if f"FROM {table}" in text:
                    return _FakeResult(fake_rows[table])
            return _FakeResult([])

    class _FakeEngine:
        def connect(self):
            return _FakeConn()

        async def dispose(self):
            return None

    def fake_create(db_url):
        return _FakeEngine()

    import sqlalchemy.ext.asyncio as sa_async

    monkeypatch.setattr(sa_async, "create_async_engine", fake_create)

    result = asyncio.run(
        check_source_urls.collect_urls_from_db("postgresql://fake")
    )
    # Centralisé gagne sur dup.test/a.
    assert result["https://dup.test/a"] == "sources"
    assert result["https://only-sources.test/b"] == "sources"
    assert result["https://only-funds.test/c"] == "funds"


@pytest.mark.unit
def test_build_report_aggregates_counts_correctly() -> None:
    """`build_report` doit agréger les statuts dans `counts` (7 clés fixes)."""

    fake_results = [
        {
            "source_url": "https://a",
            "table": "sources",
            "status": "ok",
            "http_code": 200,
            "detected_at": "2026-04-21T00:00:00Z",
            "last_valid_at": "2026-04-21T00:00:00Z",
            "suggested_action": "no_action",
            "duration_ms": 10,
        },
        {
            "source_url": "https://b",
            "table": "funds",
            "status": "not_found",
            "http_code": 404,
            "detected_at": "2026-04-21T00:00:00Z",
            "last_valid_at": None,
            "suggested_action": "admin_update_url",
            "duration_ms": 20,
        },
    ]
    report = build_report(fake_results)
    assert report["total_sources_checked"] == 2
    assert report["counts"]["ok"] == 1
    assert report["counts"]["not_found"] == 1
    assert report["counts"]["timeout"] == 0


# =====================================================================
# Integration tests (env-gated SOURCE_URL_CHECK=1 — règle C2 9.7)
# =====================================================================


_INTEGRATION_SKIP_REASON = (
    "Integration test — set SOURCE_URL_CHECK=1 to enable network access"
)


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SOURCE_URL_CHECK") != "1",
    reason=_INTEGRATION_SKIP_REASON,
)
def test_httpbin_smoke_200_404_500() -> None:
    """E2E : httpbin.org renvoie 200/404/500 → catégorisation correcte.

    Skippé sans SOURCE_URL_CHECK=1 (pas d'appel réseau en CI par défaut).
    """

    async def run() -> list[dict]:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            max_redirects=3,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            try:
                await client.head("https://httpbin.org/status/200")
            except httpx.ConnectError:
                pytest.skip("httpbin.org unavailable")
            return [
                await check_one(client, f"https://httpbin.org/status/{code}", "sources")
                for code in (200, 404, 500)
            ]

    results = asyncio.run(run())
    statuses = {r["status"] for r in results}
    assert "ok" in statuses
    assert "not_found" in statuses
    assert "server_error" in statuses


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SOURCE_URL_CHECK") != "1",
    reason=_INTEGRATION_SKIP_REASON,
)
def test_subprocess_dry_run_produces_valid_report(tmp_path: Path) -> None:
    """E2E : `python scripts/check_source_urls.py --dry-run` via subprocess
    écrit un rapport validant REPORT_SCHEMA sur le vrai FS."""

    output = tmp_path / "report.json"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--dry-run-fixture",
            str(FIXTURE_PATH),
            "--output",
            str(output),
            "--timeout",
            "5",
        ],
        check=True,
        cwd=str(BACKEND_ROOT),
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    jsonschema.validate(report, REPORT_SCHEMA)
