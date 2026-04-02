# Research: 013-fix-multiturn-routing-timeline

**Date**: 2026-04-01

## Decision 1: Mecanisme de module actif dans le state

**Decision**: Ajouter deux champs `active_module: str | None` et `active_module_data: dict | None` au `ConversationState` TypedDict existant.

**Rationale**: Le state actuel utilise des flags booleens individuels (`_route_esg`, `_route_carbon`, etc.) recalcules a chaque tour par le routeur. Ces flags sont ephemeres et ne persistent pas entre les tours de conversation. Un champ unique `active_module` agit comme "memoire" du routeur, permettant au message suivant d'etre route vers le meme noeud sans re-detection par mots-cles.

**Alternatives considerees**:
- Stocker le module actif en base de donnees : rejet car ajoute latence I/O a chaque message et complexifie le code. Le state LangGraph est deja persiste via MemorySaver/checkpointer.
- Utiliser l'historique des messages pour inferer le module : rejet car fragile (necessite parsing des messages precedents) et couteux en tokens.
- Ajouter un champ par module (is_esg_active, is_carbon_active) : rejet car redondant avec les flags existants et ne resout pas le probleme de priorite.

## Decision 2: Detection de changement de sujet

**Decision**: Utiliser un appel LLM rapide (classification binaire) uniquement quand `active_module` est defini, avec defaut "rester dans le module" en cas d'erreur.

**Rationale**: Les heuristiques de mots-cles ne suffisent pas pour distinguer "Oui le SUNREF m'interesse" (continuation financement) de "Parlons de financement" (changement depuis un autre module). Un appel LLM court (prompt minimaliste, ~100 tokens) offre la fiabilite necessaire. Le cout est acceptable car il ne se declenche que quand un module est actif (~30% des messages).

**Alternatives considerees**:
- Heuristiques de mots-cles pour la detection de changement : rejet car trop de faux positifs ("stop" peut etre une reponse a une question, pas un changement de sujet).
- Toujours router vers le module actif sans detection de sortie : rejet car l'utilisateur serait "piege" dans un module.
- Classification multi-classe (quel module ?) : rejet car surdimensionne, une classification binaire (rester/quitter) suffit.

## Decision 3: Format timeline canonique

**Decision**: Standardiser tous les prompts sur le format `{"events": [...]}` et rendre le composant frontend tolerant aux variantes.

**Rationale**: 3 formats differents existent actuellement dans les prompts (events dans system.py, phases dans action_plan.py, items dans carbon.py et financing.py). La double correction (prompts + frontend) assure la robustesse : les prompts genereront le bon format, et le frontend acceptera les variantes en fallback.

**Alternatives considerees**:
- Corriger uniquement les prompts : rejet car le LLM ne suit pas toujours les instructions de format a 100%.
- Corriger uniquement le frontend : rejet car ne resout pas le probleme a la source et accumule de la dette technique dans le composant.
- Ajouter un middleware de normalisation cote backend : rejet car complexite inutile, le frontend peut gerer la normalisation.

## Decision 4: Gestion de la reprise de session

**Decision**: La reprise se fait via le routeur qui detecte l'intention ("continuons l'ESG") et le noeud specialiste qui requete la base pour trouver la session in_progress.

**Rationale**: Le `active_module` est remis a null quand l'utilisateur quitte un module. La reprise ne peut pas s'appuyer sur le state seul car il peut avoir ete reinitialise (nouvelle conversation). La base de donnees reste la source de verite pour les sessions in_progress.

**Alternatives considerees**:
- Garder `active_module` indefiniment jusqu'a finalisation : rejet car empecherait l'utilisateur de changer de sujet librement.
- Stocker la progression complete dans le state : rejet car le state deviendrait trop volumineux et fragile.

## Decision 5: Prompts a modifier pour le format timeline

**Decision**: Modifier 3 fichiers de prompts backend pour standardiser le format timeline.

**Fichiers identifies**:
- `backend/app/prompts/action_plan.py` : utilise `{"phases": [...]}` avec `name` au lieu de `title` → changer en `{"events": [...]}`
- `backend/app/prompts/carbon.py` : utilise `{"items": [...]}` → changer en `{"events": [...]}`
- `backend/app/prompts/financing.py` : utilise `{"items": [...]}` → changer en `{"events": [...]}`
- `backend/app/prompts/system.py` : deja correct avec `{"events": [...]}`

**Rationale**: Alignement sur le format canonique deja defini dans system.py. Les champs `date`, `title`, `status`, `description` sont le standard.
