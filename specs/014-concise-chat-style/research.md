# Research: 014-concise-chat-style

**Date**: 2026-04-02

## R1: Strategie d'injection du STYLE_INSTRUCTION dans les prompts

### Decision

Definir `STYLE_INSTRUCTION` comme constante dans `backend/app/prompts/system.py`, puis l'injecter a deux niveaux :

1. **build_system_prompt()** (chat_node) : injection conditionnelle — uniquement quand `user_profile` est renseigne (post-onboarding). Si `user_profile` est None ou vide, l'instruction n'est pas ajoutee (mode onboarding pedagogique).
2. **build_*_prompt()** specialises (6 fonctions : esg, carbon, financing, credit, application, action_plan) : injection systematique car ces modules ne sont declenches qu'apres profilage.

### Rationale

- Centralise la constante en un seul endroit (`system.py`) pour faciliter la maintenance.
- Les 6 prompts specialises ne partagent pas le BASE_PROMPT — ils ont chacun leur propre constante `*_PROMPT` et retournent `*_PROMPT.format(...)`. L'injection doit donc se faire dans chaque `build_*_prompt()`.
- L'import depuis `system.py` evite la duplication du texte.

### Alternatives considerees

| Alternative | Raison du rejet |
|-------------|-----------------|
| Ajouter directement dans chaque `*_PROMPT` | Duplication du texte, maintenance difficile |
| Post-processing des reponses LLM | Complexe, fragile, ne resout pas le probleme a la source |
| Middleware de prompt | Sur-ingenierie pour un ajout de texte statique |

## R2: Condition d'onboarding pour FR-010

### Decision

L'onboarding est detecte par l'absence de `user_profile` ou un profil avec moins de 2 champs renseignes dans `build_system_prompt()`. Ce seuil correspond au fait que le profilage initial collecte au minimum secteur + ville.

### Rationale

- `build_system_prompt()` recoit deja `user_profile: dict | None` — condition naturelle.
- Les prompts specialises (ESG, carbone...) ne sont jamais appeles sans profil — le router ne les active qu'apres profilage. Pas de condition necessaire la.

### Alternatives considerees

| Alternative | Raison du rejet |
|-------------|-----------------|
| Flag booleen `is_onboarding` dans le state | Ajout de complexite inutile alors que le profil vide suffit |
| Compteur de messages | Non fiable — un utilisateur peut revenir sans profil |

## R3: Placement du STYLE_INSTRUCTION dans le prompt

### Decision

Placer `STYLE_INSTRUCTION` APRES les instructions visuelles et AVANT le profil entreprise dans `BASE_PROMPT`. Pour les prompts specialises, l'ajouter en fin de prompt (apres le `.format()` du contexte).

### Rationale

- Position apres les visuels = le LLM lit d'abord comment creer les blocs, puis comment les accompagner de texte. Ordre logique.
- L'utilisateur a explicitement demande "APRES les instructions de visualisation".
- Pour les specialises, l'ajout en fin via `build_*_prompt()` evite de modifier les templates `*_PROMPT` qui contiennent des `{placeholders}`.
