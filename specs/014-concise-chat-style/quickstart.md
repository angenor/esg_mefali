# Quickstart: 014-concise-chat-style

## Objectif

Ajouter une instruction de style concis (`STYLE_INSTRUCTION`) dans le prompt systeme de tous les noeuds LangGraph pour que l'assistant IA ne repete pas en texte ce que les blocs visuels montrent deja.

## Fichiers a modifier

1. `backend/app/prompts/system.py` — Definir `STYLE_INSTRUCTION`, l'injecter dans `build_system_prompt()` (conditionnel onboarding)
2. `backend/app/prompts/esg_scoring.py` — Importer et ajouter `STYLE_INSTRUCTION` dans `build_esg_prompt()`
3. `backend/app/prompts/carbon.py` — Idem dans `build_carbon_prompt()`
4. `backend/app/prompts/financing.py` — Idem dans `build_financing_prompt()`
5. `backend/app/prompts/credit.py` — Idem dans `build_credit_prompt()`
6. `backend/app/prompts/application.py` — Idem dans `build_application_prompt()`
7. `backend/app/prompts/action_plan.py` — Idem dans `build_action_plan_prompt()`

## Verification rapide

```bash
# Activer le venv
source backend/venv/bin/activate

# Lancer les tests existants
pytest backend/tests/ -x -q

# Verifier que STYLE_INSTRUCTION est present dans tous les prompts
python -c "
from app.prompts.system import STYLE_INSTRUCTION, build_system_prompt
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.carbon import build_carbon_prompt

# Chat avec profil (style concis actif)
p = build_system_prompt(user_profile={'sector': 'recyclage', 'city': 'Abidjan'})
assert 'CONCIS' in p or 'concis' in p

# Chat sans profil (onboarding, style concis inactif)
p2 = build_system_prompt()
assert 'CONCIS' not in p2

# Modules specialises (toujours actif)
assert 'concis' in build_esg_prompt().lower()
assert 'concis' in build_carbon_prompt().lower()

print('OK')
"
```
