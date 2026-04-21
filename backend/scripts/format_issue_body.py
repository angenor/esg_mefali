"""Formatte le rapport JSON en corps d'issue GitHub Markdown.

Usage :

    python scripts/format_issue_body.py report.json > issue_body.md

Appelé par `.github/workflows/check-sources.yml` (Story 10.11, AC5).

Contraintes :
    - Le body GitHub est limité à ~65 536 chars. On liste seulement le
      top 10 des sources KO + un lien vers l'artifact complet
      (14 j de rétention).
    - Format Markdown GFM (table + code fence pour summary counts).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TOP_N: int = 10


def _artifact_link() -> str:
    """Construit un lien vers l'artifact GitHub Actions si le run tourne en CI.

    Utilise les variables d'env auto-exposées par GitHub Actions. Si
    absentes (exécution locale), retourne un placeholder informatif.
    """

    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "<repo>")
    run_id = os.environ.get("GITHUB_RUN_ID", "<run-id>")
    return f"{server}/{repo}/actions/runs/{run_id}"


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
    lines.append(
        f"- Généré : `{report['generated_at']}`"
    )
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
    lines.append(
        "| URL | Table | Status | HTTP | Action |"
    )
    lines.append(
        "|-----|-------|--------|------|--------|"
    )
    for src in top:
        action = src.get("suggested_action") or "—"
        http = src["http_code"] if src["http_code"] is not None else "—"
        # Troncature de l'URL à 80 chars pour éviter les lignes illisibles.
        url = src["source_url"]
        short_url = (url[:77] + "...") if len(url) > 80 else url
        lines.append(
            f"| `{short_url}` | `{src['table']}` | "
            f"`{src['status']}` | `{http}` | `{action}` |"
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
