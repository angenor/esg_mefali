# `frontend/tests/e2e-live/` — Tests E2E live (agent-browser)

Cette suite execute des **scenarios E2E reels** contre un backend FastAPI
demarre + un LLM Claude **reel** via OpenRouter, en pilotant un navigateur
Chromium **visible** (`agent-browser --headed`).

Elle est **complementaire** (et non substituable) a `frontend/tests/e2e/`
(Playwright + backend mocke), qui assure la regression rapide en CI. La suite
live sert au **smoke manuel observable** avant release et a la validation des
chaines complexes (ex. tool calling LLM + SSE + Driver.js).

## Pre-requis

| Composant | Etat attendu | Verification |
|---|---|---|
| `agent-browser` | installe globalement (`/usr/local/lib/agent-browser`) | `agent-browser --version` |
| Backend FastAPI | demarre sur `:8000` | `curl -sSf http://localhost:8000/docs` |
| Frontend Nuxt | demarre sur `:3000` | `curl -sSf http://localhost:3000` |
| Postgres local | base `esg_mefali` accessible | `psql ...` ou backend up |
| `OPENROUTER_API_KEY` (`.env`) | valide + credit | tester un message dans le chat |
| User de test seed | present en base | voir tableau ci-dessous |

### Demarrage des serveurs

```bash
# Terminal 1 — backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

### Seed des utilisateurs de test

```bash
# Aminata (story 8.3)
cd backend && source venv/bin/activate
python scripts/seed_aminata.py
```

## Conventions

- **Un fichier par parcours** : `{epic}-{num}-parcours-{prenom}.sh`
  (ex. `8-3-parcours-aminata.sh`, `8-4-parcours-ibrahim.sh`).
- **Bash** (`set -euo pipefail`), executable (`chmod +x`).
- **Helpers partages** dans `lib/` :
  - `env.sh` — lit les credentials depuis `.env`.
  - `login.sh` — login UI reutilisable.
  - `assertions.sh` — `assert_visible`, `assert_count`, `assert_contains`,
    `assert_url_contains`, `assert_no_driver_popover`, `wait_for_count`,
    `wait_for_url`, `log_step`, `log_warn`, `log_fail`.
- **Session agent-browser dediee** : variable env `AGENT_BROWSER_SESSION`
  (ex. `aminata-e2e`, `ibrahim-e2e`) pour ne pas polluer d'autres parcours.
- **`--headed` toujours** (observabilite humaine + diagnostic visuel).
- **Captures** : `screenshots/failure-{timestamp}.png` (gitignore par defaut,
  cf. `.gitignore` racine).

## Parcours disponibles

| Story | Script | User | Verbe metier |
|---|---|---|---|
| 8.3 | `8-3-parcours-aminata.sh` | `aminata1@gmail.com` | demande EXPLICITE de guidage ESG |

## Lancement

```bash
# Depuis la racine du repo
bash frontend/tests/e2e-live/8-3-parcours-aminata.sh

# Mode debug (verbose agent-browser + temporisation)
AGENT_BROWSER_DEBUG=1 bash frontend/tests/e2e-live/8-3-parcours-aminata.sh

# Avec timeout global (5 min)
timeout 300 bash frontend/tests/e2e-live/8-3-parcours-aminata.sh
```

Codes de retour :

| Code | Signification |
|---|---|
| `0` | Succes complet |
| `1` | Echec d'assertion ou pre-flight |
| `124` | Timeout global atteint |

## Troubleshooting

- **`✗ env.sh : impossible d'extraire les credentials Aminata`**  
  → verifier que `.env` racine contient `E2E_AMINATA_EMAIL=...` et
    `E2E_AMINATA_PASSWORD=...` ou les commentaires equivalents.
- **`pre-flight: frontend down`** → demarrer `npm run dev` dans `frontend/`.
- **`pre-flight: backend down`** → demarrer `uvicorn app.main:app --reload`.
- **`AC4 : aucun overlay Driver.js apres 60s`** → le LLM n'a pas appele
  `trigger_guided_tour`. Verifier :
  1. `OPENROUTER_API_KEY` est valide et a du credit.
  2. Les logs backend (le tool a-t-il ete invoque ?).
  3. Le prompt `backend/app/prompts/guided_tour.py` (regle 2 declenchement
     direct).  
  Le script retry **1x** automatiquement avec une reformulation.
- **Session agent-browser bloquee** → `agent-browser session list` puis
  `agent-browser close` pour terminer la session active.
- **Captures `screenshots/failure-*.png`** → ouvertes localement, jamais
  committees (gitignore).
