"""Formatte le rapport JSON en corps d'issue GitHub Markdown.

Usage :

    python scripts/format_issue_body.py report.json > issue_body.md

Appelé par `.github/workflows/check-sources.yml` (Story 10.11, AC5).

Contraintes :
    - Le body GitHub est limité à ~65 536 chars. On liste seulement le
      top 10 des sources KO + un lien vers l'artifact complet
      (14 j de rétention).
    - Format Markdown GFM (table + code fence pour summary counts).
    - MEDIUM-10.11-11 : échappement strict des cellules Markdown.
    - LOW-10.11-18 : les query params d'URL sont supprimés à l'affichage
      (risque de fuite token `?apikey=...` si admin N3 colle une URL
      signée par erreur — l'artifact complet conserve l'URL brute pour
      l'audit, mais le body de l'issue ne l'expose pas).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

TOP_N: int = 10


def _md_cell(raw: object) -> str:
    """Échappe un littéral destiné à une cellule de table Markdown.

    Neutralise les pipes (qui casseraient la table), les backticks (qui
    sortiraient du code span et permettraient l'injection HTML), les
    backslashes et les newlines.
    """

    text = str(raw)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("`", "\\`")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def _redact_url(url: str, max_len: int = 80) -> str:
    """Supprime les query params et le fragment, puis tronque.

    Les query params peuvent contenir des secrets (tokens d'API, session
    IDs) qu'un admin N3 pourrait insérer par inadvertance. L'artifact
    conserve l'URL brute — ici on ne l'affiche pas en clair dans l'issue.
    """

    try:
        parsed = urlparse(url)
        clean = urlunparse(parsed._replace(query="", fragment=""))
    except ValueError:
        clean = url
    if parsed.query or parsed.fragment:
        clean = clean + " (?redacted)"
    if len(clean) > max_len:
        return clean[: max_len - 3] + "..."
    return clean


def _artifact_link() -> str:
    """Construit un lien vers l'artifact GitHub Actions si le run tourne en CI.

    Le lien pointe vers la page run + ancre `#artifacts` (LOW-10.11-13 :
    l'utilisateur atterrit directement sur la section artifacts).
    """

    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "<repo>")
    run_id = os.environ.get("GITHUB_RUN_ID", "<run-id>")
    return f"{server}/{repo}/actions/runs/{run_id}#artifacts"


def format_body(report: dict) -> str:
    """Transforme un rapport en Markdown lisible par un admin.

    Retourne une string — écrire via `sys.stdout.write(...)` pour
    rediriger vers un fichier `> issue_body.md` en shell.
    """

    counts = report["counts"]
    failures = report["total_sources_checked"] - counts["ok"]
    ko_sources = [s for s in report["sources"] if s["status"] != "ok"]
    ko_sources.sort(key=lambda s: s["status"])
    top = ko_sources[:TOP_N]

    lines: list[str] = []
    lines.append(
        f"## Résumé — {failures} source(s) KO "
        f"sur {report['total_sources_checked']}"
    )
    lines.append("")
    lines.append(f"- Généré : `{_md_cell(report['generated_at'])}`")
    lines.append(
        "- Compteurs : "
        + ", ".join(f"`{k}={v}`" for k, v in counts.items())
    )
    lines.append(
        f"- [Artifact `source-url-report` (JSON complet, 14 j)]"
        f"({_artifact_link()})"
    )
    lines.append("")
    lines.append(f"## Top {len(top)} KO")
    lines.append("")
    lines.append("| URL | Table | Status | HTTP | Action |")
    lines.append("|-----|-------|--------|------|--------|")
    for src in top:
        action = src.get("suggested_action") or "—"
        http = src["http_code"] if src["http_code"] is not None else "—"
        short_url = _redact_url(src["source_url"])
        lines.append(
            f"| `{_md_cell(short_url)}` | `{_md_cell(src['table'])}` | "
            f"`{_md_cell(src['status'])}` | `{_md_cell(http)}` | "
            f"`{_md_cell(action)}` |"
        )

    if len(ko_sources) > TOP_N:
        lines.append("")
        lines.append(
            f"*... et {len(ko_sources) - TOP_N} autre(s). Voir l'artifact "
            "pour la liste complète.*"
        )

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write(
            "Usage: python scripts/format_issue_body.py <report.json>\n"
        )
        return 2
    path = Path(argv[1])
    report = json.loads(path.read_text(encoding="utf-8"))
    sys.stdout.write(format_body(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
