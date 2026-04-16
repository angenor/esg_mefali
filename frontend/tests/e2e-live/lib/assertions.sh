#!/usr/bin/env bash
# lib/assertions.sh — Wrappers d'assertions au-dessus de `agent-browser`.
#
# Toutes les fonctions retournent 0 si l'assertion passe, 1 sinon (avec un
# message d'erreur sur stderr). Combinables avec `set -euo pipefail` du script
# appelant — un echec stoppe automatiquement le script (et declenche le trap
# EXIT pour la capture d'ecran).
#
# Pre-requis : `lib/env.sh` source (pour AGENT_BROWSER_SESSION).

set -u

# Couleurs ANSI partagees avec le script principal
_COLOR_GREEN="$(printf '\033[0;32m')"
_COLOR_RED="$(printf '\033[0;31m')"
_COLOR_YELLOW="$(printf '\033[0;33m')"
_COLOR_RESET="$(printf '\033[0m')"

_AB() { agent-browser --headed "$@"; }

# log_step "AC4.step2" "Description"
log_step() {
  local id="$1"
  local msg="$2"
  echo "${_COLOR_GREEN}==>${_COLOR_RESET} [${id}] ${msg}"
}

log_warn() {
  local msg="$1"
  echo "${_COLOR_YELLOW}!${_COLOR_RESET} ${msg}" >&2
}

log_fail() {
  local id="$1"
  local msg="$2"
  echo "${_COLOR_RED}✗${_COLOR_RESET} [${id}] ${msg}" >&2
}

# assert_visible <id> <selector>
assert_visible() {
  local id="$1"
  local sel="$2"
  if _AB is visible "${sel}" 2>/dev/null | grep -qi 'true'; then
    log_step "${id}" "visible OK : ${sel}"
    return 0
  fi
  log_fail "${id}" "non visible : ${sel}"
  return 1
}

# assert_count <id> <selector> <comparator> <expected>
# comparator : '==' | '>=' | '<=' | '>' | '<'
assert_count() {
  local id="$1"
  local sel="$2"
  local cmp="$3"
  local expected="$4"
  local actual
  actual="$(_AB get count "${sel}" 2>/dev/null | tr -d '[:space:]')"
  actual="${actual:-0}"
  case "${cmp}" in
    '==') [[ "${actual}" -eq "${expected}" ]] ;;
    '>=') [[ "${actual}" -ge "${expected}" ]] ;;
    '<=') [[ "${actual}" -le "${expected}" ]] ;;
    '>')  [[ "${actual}" -gt "${expected}" ]] ;;
    '<')  [[ "${actual}" -lt "${expected}" ]] ;;
    *) log_fail "${id}" "comparateur invalide : ${cmp}" ; return 1 ;;
  esac
  if [[ $? -eq 0 ]]; then
    log_step "${id}" "count(${sel}) ${cmp} ${expected} (actual=${actual})"
    return 0
  fi
  log_fail "${id}" "count(${sel}) ${cmp} ${expected} VIOLE (actual=${actual})"
  return 1
}

# assert_contains <id> <selector> <regex>
assert_contains() {
  local id="$1"
  local sel="$2"
  local regex="$3"
  local text
  text="$(_AB get text "${sel}" 2>/dev/null || true)"
  if echo "${text}" | grep -Eqi -- "${regex}"; then
    log_step "${id}" "text(${sel}) ~ /${regex}/i"
    return 0
  fi
  log_fail "${id}" "text(${sel}) ne matche pas /${regex}/i (texte=${text:0:120}...)"
  return 1
}

# assert_url_contains <id> <substring>
assert_url_contains() {
  local id="$1"
  local needle="$2"
  local url
  url="$(_AB get url 2>/dev/null || true)"
  if [[ "${url}" == *"${needle}"* ]]; then
    log_step "${id}" "url contient ${needle} (${url})"
    return 0
  fi
  log_fail "${id}" "url=${url} ne contient pas ${needle}"
  return 1
}

# assert_no_driver_popover <id>
assert_no_driver_popover() {
  local id="$1"
  assert_count "${id}" ".driver-popover" '==' 0
}

# wait_for_count <selector> <comparator> <expected> <timeout_ms>
# Boucle jusqu'a ce que la condition soit vraie ou expiration.
wait_for_count() {
  local sel="$1"
  local cmp="$2"
  local expected="$3"
  local timeout_ms="$4"
  local interval_ms=500
  local elapsed=0
  while (( elapsed < timeout_ms )); do
    local actual
    actual="$(_AB get count "${sel}" 2>/dev/null | tr -d '[:space:]')"
    actual="${actual:-0}"
    case "${cmp}" in
      '==') [[ "${actual}" -eq "${expected}" ]] && return 0 ;;
      '>=') [[ "${actual}" -ge "${expected}" ]] && return 0 ;;
      '<=') [[ "${actual}" -le "${expected}" ]] && return 0 ;;
      '>')  [[ "${actual}" -gt "${expected}" ]] && return 0 ;;
      '<')  [[ "${actual}" -lt "${expected}" ]] && return 0 ;;
    esac
    sleep "$(awk -v ms="${interval_ms}" 'BEGIN { print ms/1000 }')"
    elapsed=$(( elapsed + interval_ms ))
  done
  return 1
}

# wait_for_url <substring> <timeout_ms>
wait_for_url() {
  local needle="$1"
  local timeout_ms="$2"
  local interval_ms=500
  local elapsed=0
  while (( elapsed < timeout_ms )); do
    local url
    url="$(_AB get url 2>/dev/null || true)"
    [[ "${url}" == *"${needle}"* ]] && return 0
    sleep "$(awk -v ms="${interval_ms}" 'BEGIN { print ms/1000 }')"
    elapsed=$(( elapsed + interval_ms ))
  done
  return 1
}
