#!/usr/bin/env bash
# lib/env.sh — Source ce fichier pour exporter les credentials E2E live.
#
# Ce helper extrait `E2E_AMINATA_EMAIL` et `E2E_AMINATA_PASSWORD` depuis le
# `.env` racine du repo. Il privilegie les variables nommees (pattern
# `E2E_AMINATA_*=...`) et tombe en repli sur les commentaires humains
# (`# Email : aminata1@gmail.com` / `# Mot de passe : Aminata2026!`).
#
# Usage :
#   # depuis n'importe ou
#   source frontend/tests/e2e-live/lib/env.sh
#   echo "$AMINATA_EMAIL"
#
# Exit 1 si les credentials ne peuvent pas etre resolus.

set -u

_E2E_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
_E2E_ENV_FILE="${_E2E_REPO_ROOT}/.env"

if [[ ! -f "${_E2E_ENV_FILE}" ]]; then
  echo "✗ env.sh : fichier .env introuvable a ${_E2E_ENV_FILE}" >&2
  return 1 2>/dev/null || exit 1
fi

# 1) Variables nommees (preferees, scriptable-friendly)
_AMINATA_EMAIL_LINE="$(grep -E '^E2E_AMINATA_EMAIL=' "${_E2E_ENV_FILE}" | tail -n1)"
_AMINATA_PASSWORD_LINE="$(grep -E '^E2E_AMINATA_PASSWORD=' "${_E2E_ENV_FILE}" | tail -n1)"

if [[ -n "${_AMINATA_EMAIL_LINE}" && -n "${_AMINATA_PASSWORD_LINE}" ]]; then
  export AMINATA_EMAIL="${_AMINATA_EMAIL_LINE#E2E_AMINATA_EMAIL=}"
  export AMINATA_PASSWORD="${_AMINATA_PASSWORD_LINE#E2E_AMINATA_PASSWORD=}"
else
  # 2) Repli : extraction depuis les commentaires humains
  export AMINATA_EMAIL="$(grep -E '^# Email : aminata1@gmail.com' "${_E2E_ENV_FILE}" | head -n1 | sed -E 's/^# Email : //')"
  export AMINATA_PASSWORD="$(grep -A1 '^# Email : aminata1@gmail.com' "${_E2E_ENV_FILE}" | grep '^# Mot de passe' | head -n1 | sed -E 's/^# Mot de passe : //')"
fi

# Trim espaces eventuels
AMINATA_EMAIL="$(echo -n "${AMINATA_EMAIL}" | tr -d '[:space:]')"
AMINATA_PASSWORD="$(echo -n "${AMINATA_PASSWORD}" | tr -d '[:space:]')"

if [[ -z "${AMINATA_EMAIL:-}" || -z "${AMINATA_PASSWORD:-}" ]]; then
  echo "✗ env.sh : impossible d'extraire les credentials Aminata depuis ${_E2E_ENV_FILE}" >&2
  echo "  Verifier que les lignes E2E_AMINATA_EMAIL=... et E2E_AMINATA_PASSWORD=... existent." >&2
  return 1 2>/dev/null || exit 1
fi

# Session agent-browser dediee (pas d'option CLI --session, on utilise l'env var)
export AGENT_BROWSER_SESSION="${AGENT_BROWSER_SESSION:-aminata-e2e}"
