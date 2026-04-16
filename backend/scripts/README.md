# `backend/scripts/` — utilitaires CLI

Scripts Python a executer **a la main** depuis l'environnement virtuel du
backend. Ces scripts ne sont **pas** importes par l'application FastAPI ; ils
servent uniquement a l'amorcage de la base de developpement local et aux taches
ponctuelles d'administration (analogue a `backend/alembic/`).

## Pre-requis

```bash
cd backend
source venv/bin/activate
```

`which python` doit pointer vers `backend/venv/bin/python`. Les scripts utilisent
`app.core.database.async_session_factory` et appliquent les memes hypotheses que
l'application (variables `.env`, base Postgres locale, etc.).

## Scripts disponibles

### `seed_aminata.py` — Story 8.3 (parcours Aminata)

Cree l'utilisateur de test E2E live `aminata1@gmail.com` avec :

- Profil entreprise « Recyclage Plus Senegal » (secteur `recyclage`, Senegal).
- Une evaluation ESG `completed` avec les 30 criteres notes (score global ~70/100,
  >= 3 forces, >= 3 recommandations).

Idempotent : si l'utilisateur existe deja, le script affiche un message et exit 0.

```bash
# Premiere execution (cree)
python scripts/seed_aminata.py

# Seconde execution (skip)
python scripts/seed_aminata.py
```

Codes de retour :

| Code | Signification |
|------|---------------|
| `0`  | Succes (seed cree ou deja present) |
| `1`  | Echec (exception ou garde-fou metier viole) |

Les credentials Aminata sont documentes en commentaire dans le `.env` racine
(voir le bloc `# Email : aminata1@gmail.com`). **Ne jamais** les committer en
clair ailleurs ; le `.env` est dans `.gitignore`.
