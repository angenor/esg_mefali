#!/usr/bin/env bash
# lib/login.sh — Login UI reutilisable pour les scripts E2E live.
#
# Necessite que `lib/env.sh` et `lib/assertions.sh` soient sourced AVANT.
#
# Usage :
#   source frontend/tests/e2e-live/lib/env.sh
#   source frontend/tests/e2e-live/lib/assertions.sh
#   source frontend/tests/e2e-live/lib/login.sh
#   login_via_ui "$AMINATA_EMAIL" "$AMINATA_PASSWORD"
#
# Exit 1 si le login echoue (timeout 15s sur la redirection).

set -u

_LOGIN_FRONTEND_URL="${E2E_FRONTEND_URL:-http://localhost:3000}"

# login_via_ui <email> <password>
login_via_ui() {
  local email="$1"
  local password="$2"

  log_step "LOGIN.open" "Ouverture de ${_LOGIN_FRONTEND_URL}/login"
  agent-browser --headed open "${_LOGIN_FRONTEND_URL}/login" >/dev/null

  # Purge cookies/storage pour isolation totale
  agent-browser --headed eval "localStorage.clear(); sessionStorage.clear();" >/dev/null 2>&1 || true

  # Re-charger pour repartir de zero apres clear
  agent-browser --headed open "${_LOGIN_FRONTEND_URL}/login" >/dev/null

  log_step "LOGIN.wait_form" "Attente du formulaire de login"
  agent-browser --headed wait '[data-testid="login-email"]' 10000 >/dev/null

  log_step "LOGIN.fill_email" "Saisie email=${email}"
  agent-browser --headed fill '[data-testid="login-email"]' "${email}" >/dev/null

  log_step "LOGIN.fill_password" "Saisie mot de passe (***)"
  agent-browser --headed fill '[data-testid="login-password"]' "${password}" >/dev/null

  log_step "LOGIN.submit" "Clic sur le bouton Se connecter"
  agent-browser --headed click '[data-testid="login-submit"]' >/dev/null

  log_step "LOGIN.wait_dashboard" "Attente redirection vers /dashboard (15s max)"
  if ! wait_for_url "/dashboard" 15000; then
    log_fail "LOGIN.wait_dashboard" "Pas de redirection vers /dashboard apres 15s"
    return 1
  fi

  log_step "LOGIN.done" "Login reussi : utilisateur sur /dashboard"
}
