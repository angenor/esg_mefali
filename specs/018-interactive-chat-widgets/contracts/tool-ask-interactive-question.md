# Tool Contract — `ask_interactive_question`

**Feature**: 018-interactive-chat-widgets
**Type** : LangChain `@tool` async
**Emplacement** : `backend/app/graph/tools/interactive_tools.py` (nouveau module)
**Exposition** : injecté dans les 7 nœuds LangGraph (chat, esg_scoring, carbon,
financing, application, credit, profiling) via `tools_by_module`.

## Rôle

Permet au LLM de poser une question interactive (QCU, QCM, avec ou sans
justification) qui sera matérialisée côté frontend sous forme d'un widget
cliquable. Le tool persiste la question en base et déclenche l'émission d'un
événement SSE via le marker `<!--SSE:{…}-->`.

## Signature Python

```python
from typing import Literal
from uuid import UUID
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool
async def ask_interactive_question(
    question_type: Literal["qcu", "qcm", "qcu_justification", "qcm_justification"],
    prompt: str,
    options: list[dict],
    min_selections: int = 1,
    max_selections: int = 1,
    requires_justification: bool = False,
    justification_prompt: str | None = None,
    config: RunnableConfig = None,
) -> str:
    """
    Pose une question interactive à l'utilisateur sous forme de widget cliquable.

    À utiliser quand la question attend :
    - un choix unique (question_type='qcu')
    - plusieurs choix (question_type='qcm')
    - un choix + justification texte libre amusante ('qcu_justification' ou 'qcm_justification')

    Args:
        question_type: Type de widget ('qcu' | 'qcm' | 'qcu_justification' | 'qcm_justification').
        prompt: Énoncé de la question (1-500 caractères, français avec accents).
        options: Liste de 2 à 8 options [{"id": "slug", "label": "Texte affiché", "emoji": "🎯", "description": "Aide optionnelle"}].
        min_selections: Nombre minimum de sélections (ignoré pour QCU, défaut 1).
        max_selections: Nombre maximum de sélections (ignoré pour QCU, défaut 1).
        requires_justification: True uniquement pour les variantes '_justification'.
        justification_prompt: Libellé fun du champ justification (ex. "Raconte-nous pourquoi !"), 200 car max.

    Returns:
        Confirmation textuelle avec marker SSE embarqué. Le LLM ne doit PAS
        continuer à générer du texte après ce tool call : le frontend affiche
        le widget, l'utilisateur répond, et un nouveau tour de conversation
        démarre avec la réponse injectée dans le prochain tour.
    """
```

## Contrat d'entrée

| Paramètre | Type | Contraintes |
|-----------|------|-------------|
| `question_type` | enum string | doit ∈ `{qcu, qcm, qcu_justification, qcm_justification}` |
| `prompt` | string | 1 ≤ len ≤ 500 |
| `options` | list[dict] | 2 ≤ len ≤ 8 ; chaque élément valide `InteractiveOption` |
| `options[i].id` | string | `^[a-z0-9_]+$`, 1-32 car, unique dans la liste |
| `options[i].label` | string | 1-120 car |
| `options[i].emoji` | string? | 0-8 car (1-2 grapheme clusters attendus) |
| `options[i].description` | string? | 0-200 car |
| `min_selections` | int | 1 ≤ n ≤ len(options) |
| `max_selections` | int | min_selections ≤ n ≤ len(options) ; forcé à 1 pour QCU* |
| `requires_justification` | bool | doit correspondre au suffixe `_justification` du type |
| `justification_prompt` | string? | requis ssi `requires_justification=true` ; 1-200 car |

### Règles croisées

1. `question_type=qcu` OU `qcu_justification` ⇒ `min_selections=1` et `max_selections=1`.
2. `question_type=qcm` OU `qcm_justification` ⇒ `max_selections ≥ min_selections ≥ 1`.
3. `question_type` suffixé `_justification` ⇒ `requires_justification=true` et
   `justification_prompt` non vide.
4. Les `options[i].id` doivent être uniques.
5. Le `prompt` ne doit pas être une simple reformulation d'une question déjà
   `pending` (vérifié uniquement via invariant état).

## Comportement

1. Récupère `db`, `user`, `conversation_id` via `get_db_and_user(config)`.
2. **Invariant** : marque toute `interactive_question` `pending` existante pour
   cette conversation comme `expired` (`answered_at=now()`).
3. Valide les paramètres avec `InteractiveQuestionCreate` (Pydantic).
4. Insère la nouvelle ligne avec `state='pending'`, `module = active_module`
   courant (ou `chat` par défaut).
5. Construit le payload SSE (voir `sse-events.md`) et retourne une chaîne
   contenant le marker `<!--SSE:{…}-->` suivi d'un court texte informatif.
6. Journalise l'appel via `log_tool_call(tool_name="ask_interactive_question", ...)`.

## Sortie attendue (string)

Format strict — le frontend se base sur la présence du marker SSE pour
afficher le widget :

```text
<!--SSE:{"event":"interactive_question","data":{"id":"<uuid>","question_type":"qcu","prompt":"…","options":[…],"min_selections":1,"max_selections":1,"requires_justification":false,"justification_prompt":null}}-->
Question posée à l'utilisateur.
```

Le texte humain (« Question posée à l'utilisateur. ») sert uniquement à
renseigner l'historique tool_calls — il n'est **pas** rendu au user.

## Erreurs

| Code | Condition | Message LLM (retour tool) |
|------|-----------|---------------------------|
| `VALIDATION_ERROR` | Pydantic lève `ValidationError` | `Impossible de poser la question : {détails}. Reformule avec des paramètres valides.` |
| `DUPLICATE_OPTION_ID` | 2 options partagent un `id` | `Les identifiants d'options doivent être uniques.` |
| `INCONSISTENT_JUSTIFICATION` | type vs requires_justification incohérent | `Incohérence entre question_type et requires_justification.` |
| `CONFIG_MISSING` | `db` ou `user` introuvables dans config | `Contexte technique indisponible, retente.` |

Les erreurs sont retournées **sans** marker SSE — le LLM est libre de retenter
ou de poser la question en texte libre.

## Exemple d'invocation LLM

```json
{
  "name": "ask_interactive_question",
  "args": {
    "question_type": "qcu_justification",
    "prompt": "Ton entreprise dispose-t-elle d'une politique formelle de gestion des déchets ?",
    "options": [
      {"id": "none", "label": "Aucune politique", "emoji": "❌"},
      {"id": "partial", "label": "Tri partiel", "emoji": "♻️"},
      {"id": "full", "label": "Politique formalisée et suivie", "emoji": "✅"}
    ],
    "min_selections": 1,
    "max_selections": 1,
    "requires_justification": true,
    "justification_prompt": "Parle-nous de ton quotidien avec les déchets ! 🌍"
  }
}
```

## Contraintes d'usage (prompt engineering)

Les 7 prompts modules (R5 de research.md) ajoutent une section **OUTIL INTERACTIF** :

- « Quand une question attend un choix parmi ≤ 8 options courtes, APPELLE
  `ask_interactive_question` au lieu de rédiger un texte. »
- « N'appelle jamais ce tool deux fois dans le même tour. »
- « Après l'appel, ne génère PAS de texte supplémentaire : le frontend affiche
  le widget, attends la réponse utilisateur. »
- « Si la question est ouverte (ex. `Décrivez votre activité`), NE l'utilise pas. »

## Tests de contrat

Implémentés dans `backend/tests/unit/test_ask_interactive_question_tool.py` :

1. QCU valide → ligne insérée `state=pending`, marker SSE présent.
2. QCM valide → `min_selections=1`, `max_selections=3`.
3. QCU_JUSTIFICATION valide → `requires_justification=true`.
4. Deux options avec même `id` → `DUPLICATE_OPTION_ID`.
5. `qcu` + `requires_justification=true` → `INCONSISTENT_JUSTIFICATION`.
6. Appel avec une question `pending` existante → l'ancienne passe à `expired`.
7. `prompt` de 501 caractères → `VALIDATION_ERROR`.
8. 9 options → `VALIDATION_ERROR` (max 8).
9. `config` sans `db` → `CONFIG_MISSING`.
10. `module` propagé depuis `active_module_data` si disponible.
