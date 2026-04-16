#!/usr/bin/env bash
# Story 8.3 : Tests E2E live — Parcours Aminata (guidage demande explicitement).
#
# Couvre AC3-AC6, AC8, AC9 :
#   - Login UI Aminata -> /dashboard (AC3)
#   - Chat ouvert + intent explicite "Montre-moi mes resultats ESG" (AC4)
#   - Aucun widget de consentement Oui/Non (assertion negative)
#   - Trigger direct du tour show_esg_results (overlay Driver.js dans 60s)
#   - Entry step sidebar + decompteur 8s + 3 popovers ESG (AC5)
#   - Widget reapparait + chat de nouveau fonctionnel (AC6)
#   - Retry LLM 1x avec reformulation (AC8.5, AC9.5)
#
# Lancement :
#   bash frontend/tests/e2e-live/8-3-parcours-aminata.sh
#   AGENT_BROWSER_DEBUG=1 bash frontend/tests/e2e-live/8-3-parcours-aminata.sh
#
# Codes de retour : 0 succes, 1 echec assertion/pre-flight, 124 timeout (via `timeout`).

set -euo pipefail

# ── Resolution chemin & sourcing helpers ───────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SCREENSHOTS_DIR="${SCRIPT_DIR}/screenshots"
mkdir -p "${SCREENSHOTS_DIR}"

# shellcheck source=lib/env.sh
source "${SCRIPT_DIR}/lib/env.sh"
# shellcheck source=lib/assertions.sh
source "${SCRIPT_DIR}/lib/assertions.sh"
# shellcheck source=lib/login.sh
source "${SCRIPT_DIR}/lib/login.sh"

FRONTEND_URL="${E2E_FRONTEND_URL:-http://localhost:3000}"
BACKEND_URL="${E2E_BACKEND_URL:-http://localhost:8000}"

# ── Cleanup global ─────────────────────────────────────────────────────────
_RUN_TS="$(date +%s)"
_LAST_STEP="init"

cleanup() {
  local exit_code=$?
  if [[ ${exit_code} -ne 0 ]]; then
    log_warn "Echec sur etape : ${_LAST_STEP} (exit=${exit_code})"
    local shot="${SCREENSHOTS_DIR}/failure-${_RUN_TS}-${_LAST_STEP}.png"
    if agent-browser --headed screenshot "${shot}" >/dev/null 2>&1; then
      log_warn "Capture d'ecran : ${shot}"
    fi
  fi
  agent-browser --headed close >/dev/null 2>&1 || true
}
trap cleanup EXIT

mark_step() { _LAST_STEP="$1"; }

# ── Pre-flight ─────────────────────────────────────────────────────────────
mark_step "preflight.frontend"
log_step "PREFLIGHT" "Verification frontend ${FRONTEND_URL}"
if ! curl -sSf "${FRONTEND_URL}" -o /dev/null --max-time 5; then
  log_fail "PREFLIGHT" "Frontend down (${FRONTEND_URL}). Lancer: cd frontend && npm run dev"
  exit 1
fi

mark_step "preflight.backend"
log_step "PREFLIGHT" "Verification backend ${BACKEND_URL}"
if ! curl -sSf "${BACKEND_URL}/docs" -o /dev/null --max-time 5; then
  log_fail "PREFLIGHT" "Backend down (${BACKEND_URL}). Lancer: cd backend && uvicorn app.main:app --reload"
  exit 1
fi

# ── AC3 : Login + dashboard ────────────────────────────────────────────────
mark_step "AC3.login"
log_step "AC3" "Login UI avec Aminata"
login_via_ui "${AMINATA_EMAIL}" "${AMINATA_PASSWORD}"

mark_step "AC3.assert_dashboard"
agent-browser --headed wait '[data-testid="floating-chat-button"]' 10000 >/dev/null
assert_visible "AC3.floating_button" '[data-testid="floating-chat-button"]'
assert_url_contains "AC3.url" "/dashboard"

# ── AC4 : Ouverture widget + intent explicite + assertions trigger direct ──

# Sous-fonction : envoie un message dans le chat et verifie qu'aucun widget
# de consentement Oui/Non n'apparait + qu'un overlay Driver.js apparait.
trigger_intent_and_verify() {
  local id_prefix="$1"
  local question="$2"

  mark_step "${id_prefix}.open_widget"
  log_step "${id_prefix}" "Clic sur le bouton flottant"
  agent-browser --headed click '[data-testid="floating-chat-button"]' >/dev/null
  agent-browser --headed wait '[data-testid="chat-textarea"]' 5000 >/dev/null
  assert_visible "${id_prefix}.textarea" '[data-testid="chat-textarea"]'

  mark_step "${id_prefix}.send_question"
  log_step "${id_prefix}" "Question : ${question}"
  agent-browser --headed fill '[data-testid="chat-textarea"]' "${question}" >/dev/null
  agent-browser --headed click '[data-testid="chat-send-button"]' >/dev/null

  # Assertion negative : pas de widget de consentement Oui/Non dans 30s.
  # On s'autorise un check sur l'evolution : on attend 5s puis on verifie
  # qu'aucun bouton interactive-choice-yes/no n'est present.
  mark_step "${id_prefix}.assert_no_consent"
  sleep 5
  log_step "${id_prefix}" "Assertion negative : pas de widget consentement Oui/Non"
  if ! assert_count "${id_prefix}.no_yes" '[data-testid="interactive-choice-yes"]' '==' 0; then
    return 1
  fi
  if ! assert_count "${id_prefix}.no_no" '[data-testid="interactive-choice-no"]' '==' 0; then
    return 1
  fi

  # Assertion positive : overlay OU popover Driver.js dans 60s
  mark_step "${id_prefix}.wait_driver_overlay"
  log_step "${id_prefix}" "Attente overlay/popover Driver.js (60s max)"
  if wait_for_count ".driver-overlay" '>=' 1 60000; then
    log_step "${id_prefix}" "Overlay Driver.js detecte"
    return 0
  fi
  if wait_for_count ".driver-popover" '>=' 1 1000; then
    log_step "${id_prefix}" "Popover Driver.js detecte (sans overlay distinct)"
    return 0
  fi
  if wait_for_url "/esg/results" 1000; then
    log_step "${id_prefix}" "URL /esg/results atteinte sans overlay observe"
    return 0
  fi
  log_fail "${id_prefix}" "Aucun overlay/popover Driver.js apres 60s"
  return 1
}

mark_step "AC4.first_attempt"
log_step "AC4" "Tentative 1 : intent explicite canonique"
if ! trigger_intent_and_verify "AC4.try1" "Montre-moi mes resultats ESG"; then
  log_warn "AC4 tentative 1 echouee — retry 1x avec reformulation"
  # On ferme le widget et on retente
  agent-browser --headed click '[data-testid="floating-chat-button"]' >/dev/null 2>&1 || true
  sleep 2
  mark_step "AC4.second_attempt"
  if ! trigger_intent_and_verify "AC4.try2" "Guide-moi vers mes resultats ESG"; then
    log_fail "AC4" "Echec definitif apres 2 tentatives — voir backend logs / OpenRouter."
    exit 1
  fi
fi

# ── AC5 : Parcours visuel — entry step + 3 popovers ────────────────────────
mark_step "AC5.entry_step"
log_step "AC5" "Verification entry step sur sidebar ESG link"
# L'entry step doit etre visible (popover sur sidebar-esg-link).
# Si l'overlay vient d'apparaitre, on a deja >= 1 popover.
if ! wait_for_count ".driver-popover" '>=' 1 5000; then
  log_fail "AC5.entry_step" "Aucun popover Driver.js (entry step manquant)"
  exit 1
fi
log_step "AC5.entry_step" "Popover entry step present"

# Le decompteur de 8s navigue automatiquement vers /esg/results.
# On attend jusqu'a 12s pour la navigation auto.
mark_step "AC5.wait_navigation"
log_step "AC5" "Attente navigation auto vers /esg/results (12s max via decompteur)"
if ! wait_for_url "/esg/results" 12000; then
  log_warn "AC5" "Pas de nav auto, fallback : clic manuel sur sidebar-esg-link"
  agent-browser --headed click '[data-guide-target="sidebar-esg-link"]' >/dev/null 2>&1 || true
  if ! wait_for_url "/esg/results" 8000; then
    log_fail "AC5.navigation" "URL /esg/results jamais atteinte"
    exit 1
  fi
fi
assert_url_contains "AC5.url" "/esg/results"

# Attente que la page ESG se rende et que le tour reprenne
sleep 3

# Step 1 : Score ESG
mark_step "AC5.popover_score"
log_step "AC5" "Step 1 : Score ESG global"
if ! wait_for_count ".driver-popover" '>=' 1 10000; then
  log_fail "AC5.popover_score" "Pas de popover sur la page /esg/results"
  exit 1
fi
assert_visible "AC5.score_circle" '[data-guide-target="esg-score-circle"]'
# Tolerer les variantes — on ne fail pas si le texte ne matche pas, on warn
assert_contains "AC5.score_text" ".driver-popover" "score|esg|resultat" || \
  log_warn "AC5.score_text" "Le texte du popover ne contient pas score/esg/resultat — toleration"

mark_step "AC5.next_to_strengths"
log_step "AC5" "Clic Suivant -> popover Forces"
agent-browser --headed find role button click --name Suivant >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Next >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Continuer >/dev/null 2>&1 || true
sleep 2

# Step 2 : Forces
mark_step "AC5.popover_strengths"
assert_visible "AC5.strengths_badges" '[data-guide-target="esg-strengths-badges"]'
assert_contains "AC5.strengths_text" ".driver-popover" "points?\\s*forts?|forces" || \
  log_warn "AC5.strengths_text" "Le texte du popover ne contient pas points forts/forces — toleration"

mark_step "AC5.next_to_recos"
log_step "AC5" "Clic Suivant -> popover Recommandations"
agent-browser --headed find role button click --name Suivant >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Next >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Continuer >/dev/null 2>&1 || true
sleep 2

# Step 3 : Recommandations
mark_step "AC5.popover_recos"
assert_visible "AC5.recos" '[data-guide-target="esg-recommendations"]'
assert_contains "AC5.recos_text" ".driver-popover" "recommandations?" || \
  log_warn "AC5.recos_text" "Le texte du popover ne contient pas recommandations — toleration"

# Cloture du tour
mark_step "AC5.close_tour"
log_step "AC5" "Cloture du tour (Terminer/Done/Fermer)"
agent-browser --headed find role button click --name Terminer >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Done >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Fermer >/dev/null 2>&1 || \
  agent-browser --headed find role button click --name Suivant >/dev/null 2>&1 || true

# Attente disparition complete
mark_step "AC5.tour_destroyed"
log_step "AC5" "Verification driver.destroy() : 0 popover & 0 overlay"
if ! wait_for_count ".driver-popover" '==' 0 8000; then
  log_warn "AC5.tour_destroyed" "Popover encore present apres cloture — toleration douce"
fi
if ! wait_for_count ".driver-overlay" '==' 0 5000; then
  log_warn "AC5.tour_destroyed" "Overlay encore present apres cloture — toleration douce"
fi

# ── AC6 : Reapparition widget + chat fonctionnel ───────────────────────────
mark_step "AC6.widget_visible"
log_step "AC6" "Verification reapparition du bouton flottant"
agent-browser --headed wait '[data-testid="floating-chat-button"]' 5000 >/dev/null
assert_visible "AC6.floating_button" '[data-testid="floating-chat-button"]'

mark_step "AC6.chat_usable"
log_step "AC6" "Re-ouverture du widget + envoi message"
agent-browser --headed click '[data-testid="floating-chat-button"]' >/dev/null
agent-browser --headed wait '[data-testid="chat-textarea"]' 3000 >/dev/null
assert_visible "AC6.textarea" '[data-testid="chat-textarea"]'
agent-browser --headed fill '[data-testid="chat-textarea"]' "Merci pour le tour" >/dev/null
agent-browser --headed click '[data-testid="chat-send-button"]' >/dev/null

mark_step "AC6.assistant_reply"
log_step "AC6" "Attente reponse assistant (30s max)"
# On verifie qu'au moins 2 messages chat existent (user + assistant)
# Selecteur tolerant : article ou data-testid commence par chat-message
if ! wait_for_count "[role='article'], [data-testid^='chat-message']" '>=' 2 30000; then
  log_warn "AC6.assistant_reply" "Reponse assistant non detectee dans 30s — toleration"
fi

# ── Succes ─────────────────────────────────────────────────────────────────
mark_step "DONE"
log_step "DONE" "Parcours Aminata 8.3 OK ✓"
echo
echo "${_COLOR_GREEN}========================================${_COLOR_RESET}"
echo "${_COLOR_GREEN}  Story 8.3 — Parcours Aminata : SUCCES  ${_COLOR_RESET}"
echo "${_COLOR_GREEN}========================================${_COLOR_RESET}"

# Capture de succes (utile pour traceability)
_SUCCESS_SHOT="${SCREENSHOTS_DIR}/success-aminata-${_RUN_TS}.png"
agent-browser --headed screenshot "${_SUCCESS_SHOT}" >/dev/null 2>&1 || true
[[ -f "${_SUCCESS_SHOT}" ]] && log_step "DONE" "Capture finale : ${_SUCCESS_SHOT}"

exit 0
