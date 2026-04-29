#!/usr/bin/env bash
# ===========================================
# ESG Mefali — Bootstrap local (macOS / Linux)
# ===========================================
# BUG-V7.1-012 : automatise les pre-requis systeme WeasyPrint
# (libgobject, pango, cairo, gdk-pixbuf, libffi) qui manquaient
# sur macOS et bloquaient la generation des rapports ESG PDF.
#
# Usage : bash setup.sh
# Idempotent : peut etre relance sans danger.

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== ESG Mefali — Bootstrap local ===${NC}"
echo -e "Repertoire : ${BLUE}${SCRIPT_DIR}${NC}"

# ========================================
# 1/4 — Dependances systeme (WeasyPrint)
# ========================================
echo -e "\n${GREEN}[1/4] Dependances systeme (WeasyPrint)${NC}"

case "$(uname -s)" in
  Darwin)
    if ! command -v brew >/dev/null 2>&1; then
      echo -e "${RED}Homebrew est requis sur macOS.${NC}"
      echo -e "Installer : https://brew.sh"
      exit 1
    fi
    echo -e "${BLUE}macOS detecte — installation via Homebrew (idempotent)${NC}"
    # V8-AXE5 review : install formule par formule pour ne pas casser
    # le bootstrap si une formule unique echoue ou est deja a jour.
    for formula in pango cairo glib gdk-pixbuf libffi; do
      if brew list "$formula" >/dev/null 2>&1; then
        echo -e "  ${BLUE}✓ $formula deja installe${NC}"
      else
        echo -e "  ${BLUE}→ Installation $formula${NC}"
        brew install "$formula" || echo -e "  ${YELLOW}⚠️  $formula : echec install (verifier manuellement)${NC}"
      fi
    done
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      echo -e "${BLUE}Debian/Ubuntu detecte — installation via apt-get${NC}"
      sudo apt-get update
      sudo apt-get install -y \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info
    else
      echo -e "${YELLOW}⚠️  Distribution Linux non Debian — installer manuellement :${NC}"
      echo -e "    pango, cairo, gdk-pixbuf, libffi-dev"
    fi
    ;;
  *)
    echo -e "${YELLOW}⚠️  OS $(uname -s) non supporte automatiquement — installer manuellement les dependances WeasyPrint.${NC}"
    ;;
esac

# ========================================
# 2/4 — Backend Python (venv + deps)
# ========================================
echo -e "\n${GREEN}[2/4] Backend Python (venv + deps)${NC}"

if [ ! -f "backend/requirements.txt" ]; then
  echo -e "${RED}Erreur : backend/requirements.txt introuvable.${NC}"
  exit 1
fi

if [ ! -d "backend/venv" ]; then
  echo -e "${BLUE}Creation du venv backend/venv${NC}"
  python3 -m venv backend/venv
else
  echo -e "${BLUE}Venv backend/venv deja present${NC}"
fi

# shellcheck disable=SC1091
source backend/venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet
deactivate

# ========================================
# 3/4 — Frontend (npm install)
# ========================================
echo -e "\n${GREEN}[3/4] Frontend (npm install)${NC}"

if [ ! -f "frontend/package.json" ]; then
  echo -e "${YELLOW}⚠️  frontend/package.json introuvable — etape ignoree.${NC}"
else
  if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}npm requis pour installer le frontend.${NC}"
    exit 1
  fi
  (cd frontend && npm install)
fi

# ========================================
# 4/4 — Fichiers .env
# ========================================
echo -e "\n${GREEN}[4/4] Fichiers .env${NC}"

if [ -f "backend/.env" ]; then
  echo -e "${BLUE}backend/.env existe deja — non ecrase.${NC}"
elif [ -f "backend/.env.example" ]; then
  cp backend/.env.example backend/.env
  echo -e "${BLUE}backend/.env cree depuis .env.example${NC}"
else
  echo -e "${YELLOW}⚠️  Aucun backend/.env.example trouve.${NC}"
fi

if [ -f ".env" ]; then
  echo -e "${BLUE}.env (racine) existe deja — non ecrase.${NC}"
elif [ -f ".env.example" ]; then
  cp .env.example .env
  echo -e "${BLUE}.env cree depuis .env.example${NC}"
fi

# ========================================
# Verification finale
# ========================================
echo -e "\n${GREEN}=== Verification ===${NC}"

# shellcheck disable=SC1091
source backend/venv/bin/activate
python - <<'PY' || echo -e "${YELLOW}⚠️  WeasyPrint non operationnel — verifier les dependances systeme.${NC}"
try:
    import weasyprint
    weasyprint.HTML(string="<p>setup test</p>").write_pdf("/tmp/_setup_smoke.pdf")
    print("\033[0;32m✓ WeasyPrint operationnel (smoke PDF /tmp/_setup_smoke.pdf)\033[0m")
except Exception as exc:
    print(f"\033[1;33m⚠️  WeasyPrint smoke test echoue : {exc}\033[0m")
    raise
PY
deactivate

echo -e "\n${GREEN}=== Bootstrap termine ===${NC}"
echo -e "Pour lancer le backend : ${BLUE}source backend/venv/bin/activate && uvicorn app.main:app --reload${NC}"
echo -e "Pour lancer le frontend : ${BLUE}cd frontend && npm run dev${NC}"
