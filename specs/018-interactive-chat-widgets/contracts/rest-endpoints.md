# REST Endpoints Contract — Interactive Chat Widgets

**Feature**: 018-interactive-chat-widgets
**Base** : `backend/app/api/chat.py` (routeur chat existant)
**Auth** : `Depends(get_current_user)` pour tous les endpoints

## Vue d'ensemble

La feature ajoute **2 endpoints** et **étend 1 endpoint existant**. Aucune
régression sur les endpoints existants (`POST /api/chat/messages`,
`GET /api/chat/conversations`, etc.).

## 1. `POST /api/chat/messages` (existant, étendu)

L'endpoint `send_message` accepte désormais un champ optionnel
`interactive_question_response` dans le `multipart/form-data` (ou JSON
selon la variante actuelle).

### Paramètres ajoutés

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `interactive_question_id` | `UUID` string | non | ID de la question à résoudre |
| `interactive_question_values` | JSON string (list[str]) | non | Options choisies |
| `interactive_question_justification` | string | non | Texte libre (≤ 400 car) |

### Règles

- Si `interactive_question_id` est présent, les 2 autres champs sont obligatoires
  (`justification` reste optionnel si la question ne l'exige pas).
- Le champ `content` peut être vide si `interactive_question_id` est présent
  (la « réponse utilisateur » est alors synthétisée à partir des options
  choisies et de la justification).
- Validation :
  - `interactive_question_id` doit correspondre à une question `state=pending`
    liée à la conversation courante du user.
  - `interactive_question_values` : 1 à `max_selections` éléments, chacun
    doit appartenir à `options[*].id`.
  - Si `requires_justification=true`, `interactive_question_justification`
    est obligatoire et ≤ 400 caractères.

### Comportement

1. Charge la question par `id`, vérifie `state=pending` et ownership.
2. Valide `values` (cardinalité + appartenance aux options).
3. Construit le texte utilisateur visible :
   ```text
   {option1.label}, {option2.label}
   {justification optionnelle en italique}
   ```
4. Crée le `Message` utilisateur (role=`user`, content = texte synthétisé).
5. Met à jour la question : `state='answered'`, `response_values`,
   `response_justification`, `response_message_id`, `answered_at=now()`.
6. Injecte dans `ConversationState.active_module_data["widget_response"]` le dict
   `{question_id, values, justification, module}`.
7. Lance le flux LangGraph normal (SSE).

### Erreurs

| HTTP | Code | Condition |
|------|------|-----------|
| 400 | `INVALID_VALUES` | valeur non trouvée dans options ou cardinalité hors bornes |
| 400 | `JUSTIFICATION_REQUIRED` | requires_justification=true mais texte absent |
| 400 | `JUSTIFICATION_TOO_LONG` | justification > 400 caractères |
| 404 | `QUESTION_NOT_FOUND` | id inconnu |
| 409 | `QUESTION_NOT_PENDING` | state ∈ {answered, abandoned, expired} |
| 403 | `FORBIDDEN` | question liée à une conversation d'un autre user |

## 2. `POST /api/chat/interactive-questions/{question_id}/abandon` (nouveau)

Permet au frontend de matérialiser le clic sur « Répondre autrement »
(clarification Q3).

### Requête

```http
POST /api/chat/interactive-questions/7c3f…/abandon
Authorization: Bearer <token>
Content-Type: application/json

{}
```

### Réponse 200

```json
{
  "success": true,
  "data": {
    "id": "7c3f…",
    "state": "abandoned",
    "answered_at": "2026-04-11T13:55:12.000Z"
  }
}
```

### Comportement

1. Charge la question par `id`, vérifie ownership et `state=pending`.
2. Met à jour : `state='abandoned'`, `answered_at=now()`.
3. Émet un event `interactive_question_resolved(state=abandoned)` sur le
   flux SSE actif de la conversation si présent (best effort).
4. Le frontend débloque l'input texte classique et l'utilisateur peut écrire
   librement — le LLM verra le prochain message comme une réponse alternative.

### Erreurs

| HTTP | Code | Condition |
|------|------|-----------|
| 404 | `QUESTION_NOT_FOUND` | id inconnu |
| 409 | `QUESTION_NOT_PENDING` | déjà answered/abandoned/expired |
| 403 | `FORBIDDEN` | question d'un autre user |

## 3. `GET /api/chat/conversations/{conversation_id}/interactive-questions` (nouveau)

Endpoint de lecture pour l'hydratation de l'historique côté frontend (quand
l'utilisateur rouvre une conversation existante, il faut ré-afficher les
widgets déjà posés, avec leur état et réponses).

### Requête

```http
GET /api/chat/conversations/a1b2…/interactive-questions?state=all&limit=50
Authorization: Bearer <token>
```

### Paramètres query

| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| `state` | `all` \| `pending` \| `answered` \| `abandoned` \| `expired` | `all` | Filtre par état |
| `limit` | int | `50` | 1 ≤ n ≤ 200 |

### Réponse 200

```json
{
  "success": true,
  "data": [
    {
      "id": "7c3f…",
      "conversation_id": "a1b2…",
      "assistant_message_id": "m1…",
      "response_message_id": "m2…",
      "module": "esg_scoring",
      "question_type": "qcu_justification",
      "prompt": "…",
      "options": [{"id": "none", "label": "…"}, …],
      "min_selections": 1,
      "max_selections": 1,
      "requires_justification": true,
      "justification_prompt": "Raconte-nous pourquoi !",
      "state": "answered",
      "response_values": ["partial"],
      "response_justification": "On trie le plastique uniquement.",
      "created_at": "2026-04-11T13:52:10.123Z",
      "answered_at": "2026-04-11T13:52:45.678Z"
    }
  ],
  "meta": {"total": 4, "limit": 50}
}
```

### Erreurs

| HTTP | Code | Condition |
|------|------|-----------|
| 404 | `CONVERSATION_NOT_FOUND` | conversation inconnue |
| 403 | `FORBIDDEN` | conversation d'un autre user |

## Schémas Pydantic

```python
# backend/app/schemas/interactive_question.py

class InteractiveOption(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_]+$", min_length=1, max_length=32)
    label: str = Field(..., min_length=1, max_length=120)
    emoji: str | None = Field(None, max_length=8)
    description: str | None = Field(None, max_length=200)


class InteractiveQuestionResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    assistant_message_id: UUID | None
    response_message_id: UUID | None
    module: str
    question_type: InteractiveQuestionType
    prompt: str
    options: list[InteractiveOption]
    min_selections: int
    max_selections: int
    requires_justification: bool
    justification_prompt: str | None
    state: InteractiveQuestionState
    response_values: list[str] | None
    response_justification: str | None
    created_at: datetime
    answered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class InteractiveQuestionAnswerInput(BaseModel):
    question_id: UUID
    values: list[str] = Field(..., min_length=1, max_length=8)
    justification: str | None = Field(None, max_length=400)
```

## Tests de contrat

Implémentés dans `backend/tests/integration/test_interactive_question_api.py` :

### `POST /api/chat/messages` (extension)

1. Réponse QCU valide → 200, question passe en `answered`, nouveau message user créé.
2. Réponse QCM avec 2 values valides → 200, `response_values` contient les 2.
3. Values avec un id inconnu → 400 `INVALID_VALUES`.
4. QCM avec 0 value → 422 Pydantic.
5. `requires_justification=true` sans `justification` → 400 `JUSTIFICATION_REQUIRED`.
6. Justification de 401 caractères → 400 `JUSTIFICATION_TOO_LONG`.
7. Question `state=answered` → 409 `QUESTION_NOT_PENDING`.
8. Question d'un autre user → 403 `FORBIDDEN`.

### `POST /api/chat/interactive-questions/{id}/abandon`

9. Abandon valide d'une question pending → 200, `state=abandoned`.
10. Abandon d'une question answered → 409.
11. Abandon d'une question d'un autre user → 403.

### `GET /api/chat/conversations/{id}/interactive-questions`

12. Liste complète d'une conversation → 200, ordre chronologique.
13. Filtre `state=answered` → ne renvoie que les answered.
14. Conversation d'un autre user → 403.
15. `limit=201` → 422 Pydantic.
