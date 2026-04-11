# Data Model — Interactive Chat Widgets

**Feature**: 018-interactive-chat-widgets
**Date**: 2026-04-11
**Phase**: 1 (Design & Contracts)

## Vue d'ensemble

Cette fonctionnalité introduit **une seule nouvelle entité** : `InteractiveQuestion`.
Elle matérialise une question interactive (QCU/QCM avec ou sans justification)
posée par le LLM via le tool `ask_interactive_question`, puis consommée par le
frontend pour afficher un widget cliquable et tracer la réponse utilisateur.

Principe YAGNI : pas de tables satellites (options, responses). Les options et
la réponse vivent en JSONB sur la ligne principale — une question = une ligne.

## Entité : InteractiveQuestion

### Table PostgreSQL : `interactive_questions`

| Colonne | Type SQL | Nullable | Défaut | Description |
|---------|----------|----------|--------|-------------|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Clé primaire, générée côté BDD |
| `conversation_id` | `UUID` | NOT NULL | — | FK → `conversations.id`, `ON DELETE CASCADE` |
| `assistant_message_id` | `UUID` | NULL | — | FK → `messages.id`, `ON DELETE SET NULL`. Lie la question au message assistant qui l'a générée (NULL transitoirement pendant le streaming) |
| `response_message_id` | `UUID` | NULL | — | FK → `messages.id`, `ON DELETE SET NULL`. Lie la question au message utilisateur qui matérialise sa réponse |
| `module` | `VARCHAR(32)` | NOT NULL | — | Identifiant du module métier émetteur (`esg_scoring`, `carbon`, `financing`, `application`, `credit`, `action_plan`, `profiling`, `chat`). Permet le filtrage analytique |
| `question_type` | `VARCHAR(24)` | NOT NULL | — | Enum applicatif : `qcu`, `qcm`, `qcu_justification`, `qcm_justification` |
| `prompt` | `TEXT` | NOT NULL | — | Énoncé de la question, max 500 caractères (validation Pydantic) |
| `options` | `JSONB` | NOT NULL | — | Liste d'options `[{id: str, label: str, emoji?: str, description?: str}]`, 2 à 8 éléments |
| `min_selections` | `SMALLINT` | NOT NULL | `1` | Nombre minimal de sélections (QCU=1, QCM≥1) |
| `max_selections` | `SMALLINT` | NOT NULL | `1` | Nombre maximal (QCU=1, QCM = cardinal options) |
| `requires_justification` | `BOOLEAN` | NOT NULL | `false` | Indique si l'utilisateur doit fournir un texte libre |
| `justification_prompt` | `TEXT` | NULL | — | Libellé fun du champ justification (ex. « Raconte-nous pourquoi ! ») ; max 200 car |
| `state` | `VARCHAR(16)` | NOT NULL | `'pending'` | Enum applicatif : `pending`, `answered`, `abandoned`, `expired` |
| `response_values` | `JSONB` | NULL | — | Liste des `option.id` choisis par l'utilisateur (NULL tant que `state != 'answered'`) |
| `response_justification` | `VARCHAR(400)` | NULL | — | Texte libre saisi par l'utilisateur, max 400 caractères (clarification Q5) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | Date d'émission |
| `answered_at` | `TIMESTAMPTZ` | NULL | — | Date de la réponse ou de l'abandon explicite |

### Contraintes d'intégrité

```sql
-- Clé primaire
PRIMARY KEY (id)

-- Clés étrangères
FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
FOREIGN KEY (assistant_message_id) REFERENCES messages(id) ON DELETE SET NULL
FOREIGN KEY (response_message_id) REFERENCES messages(id) ON DELETE SET NULL

-- Cohérence sélections
CHECK (min_selections >= 1)
CHECK (max_selections >= min_selections)
CHECK (max_selections <= 8)

-- Cohérence type / sélections
CHECK (
  (question_type IN ('qcu', 'qcu_justification') AND min_selections = 1 AND max_selections = 1)
  OR
  (question_type IN ('qcm', 'qcm_justification'))
)

-- Cohérence justification
CHECK (
  (question_type IN ('qcu_justification', 'qcm_justification') AND requires_justification = true)
  OR
  (question_type IN ('qcu', 'qcm') AND requires_justification = false)
)

-- Cohérence état <-> réponse
CHECK (
  (state = 'pending' AND response_values IS NULL AND answered_at IS NULL)
  OR
  (state = 'answered' AND response_values IS NOT NULL AND answered_at IS NOT NULL)
  OR
  (state IN ('abandoned', 'expired') AND answered_at IS NOT NULL)
)

-- Longueurs textuelles
CHECK (char_length(prompt) BETWEEN 1 AND 500)
CHECK (justification_prompt IS NULL OR char_length(justification_prompt) <= 200)
```

### Index

```sql
-- Accès principal : récupérer la question en attente d'une conversation
CREATE INDEX ix_interactive_questions_conversation_pending
  ON interactive_questions (conversation_id, state)
  WHERE state = 'pending';

-- Jointure avec message assistant (affichage dans le flux)
CREATE INDEX ix_interactive_questions_assistant_message
  ON interactive_questions (assistant_message_id)
  WHERE assistant_message_id IS NOT NULL;

-- Analytics par module
CREATE INDEX ix_interactive_questions_module_state
  ON interactive_questions (module, state);
```

### Enums applicatifs (non PostgreSQL)

Les enums `question_type` et `state` sont encodés en `VARCHAR` plutôt qu'en
`CREATE TYPE` PostgreSQL. Raison : la constitution recommande la simplicité
(YAGNI) et l'ajout futur d'un nouveau type ne nécessite pas de migration
destructive.

**Python (`app/models/interactive_question.py`)** :

```python
class InteractiveQuestionType(str, Enum):
    QCU = "qcu"
    QCM = "qcm"
    QCU_JUSTIFICATION = "qcu_justification"
    QCM_JUSTIFICATION = "qcm_justification"


class InteractiveQuestionState(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    ABANDONED = "abandoned"
    EXPIRED = "expired"
```

## Forme du champ `options` (JSONB)

Schéma applicatif validé côté Pydantic :

```python
class InteractiveOption(BaseModel):
    id: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-z0-9_]+$")
    label: str = Field(..., min_length=1, max_length=120)
    emoji: str | None = Field(None, max_length=8)
    description: str | None = Field(None, max_length=200)
```

Exemple concret (module ESG, critère « Gestion des déchets ») :

```json
[
  {"id": "none", "label": "Aucune gestion formalisée", "emoji": "❌"},
  {"id": "partial", "label": "Tri partiel des déchets recyclables", "emoji": "♻️"},
  {"id": "full", "label": "Politique complète avec suivi mensuel", "emoji": "✅"}
]
```

## Forme du champ `response_values` (JSONB)

Toujours une **liste** de chaînes (même pour QCU → liste à 1 élément) afin
d'uniformiser la lecture côté LLM et côté analytics.

```json
["partial"]
```

## Machine à états

```text
        ask_interactive_question tool
                    │
                    ▼
               ┌─────────┐
               │ pending │
               └────┬────┘
           user      │      user clique
           clique    │      « Répondre autrement »
           widget    │      (clarification Q3)
            ┌────────┴─────────┐
            ▼                  ▼
       ┌──────────┐      ┌───────────┐
       │ answered │      │ abandoned │
       └──────────┘      └───────────┘

     (nouveau message assistant émis dans la conversation
      avec une question active pending → marque expired)
               ┌─────────┐
               │ pending │──────────► ┌─────────┐
               └─────────┘            │ expired │
                                      └─────────┘
```

### Règles de transition

| Transition | Déclencheur | Côté | Garanties |
|------------|-------------|------|-----------|
| `∅ → pending` | Tool `ask_interactive_question` exécuté | Backend | 1 seule question `pending` par conversation à la fois (invariant validé dans le tool) |
| `pending → answered` | `POST /api/chat/messages` avec `interactive_question_response` | Backend | `response_values` et `response_justification` (si requis) validés ; `response_message_id` renseigné ; `answered_at = now()` |
| `pending → abandoned` | `POST /api/chat/interactive-questions/{id}/abandon` | Backend | `answered_at = now()` ; déclenche ensuite un nouveau tour de conversation classique |
| `pending → expired` | Un nouveau message assistant arrive alors qu'une question est encore pending (clarification Q4 : « Expire + regenerate ») | Backend (hook dans chat send) | `answered_at = now()` ; LLM peut re-poser la question via un nouveau tool call |

### Invariant central

> Pour toute conversation, il existe **au plus une** `interactive_question`
> dans l'état `pending` à un instant donné.

Vérification applicative dans le tool `ask_interactive_question` : avant
insertion, marquer toute question `pending` existante comme `expired`.

## Relations

```text
conversations (1) ───────── (N) interactive_questions
                              │
                              ├── (0..1) assistant_message_id → messages
                              └── (0..1) response_message_id  → messages
```

- **Pas** de FK vers `users` : la question n'a pas de notion d'utilisateur
  (elle appartient à la conversation, qui elle porte l'utilisateur).
- **Pas** de table satellite pour les options ni pour les réponses :
  tout vit dans le JSONB de la ligne principale.

## Validation Pydantic (aperçu)

Schémas exposés dans `backend/app/schemas/interactive_question.py`
(détails complets dans `contracts/` Phase 1) :

```python
class InteractiveQuestionCreate(BaseModel):
    question_type: InteractiveQuestionType
    prompt: str = Field(..., min_length=1, max_length=500)
    options: list[InteractiveOption] = Field(..., min_length=2, max_length=8)
    min_selections: int = Field(1, ge=1, le=8)
    max_selections: int = Field(1, ge=1, le=8)
    requires_justification: bool = False
    justification_prompt: str | None = Field(None, max_length=200)
    module: str = Field(..., max_length=32)


class InteractiveQuestionResponseInput(BaseModel):
    question_id: UUID
    values: list[str] = Field(..., min_length=1, max_length=8)
    justification: str | None = Field(None, max_length=400)
```

## Impact migration

- **1 seule migration Alembic additive** : création de la table
  `interactive_questions` + 3 index.
- **Aucune** colonne ajoutée aux tables existantes (`messages`,
  `conversations`) → aucun risque de régression sur les features 001 à 017.
- Rollback trivial : `DROP TABLE interactive_questions`.

## Alignement avec l'existant

- Réutilise le pattern `VARCHAR + Enum Python` déjà employé pour les états
  (`esg_assessments.state`, `carbon_calculations.state`, etc.).
- Réutilise les FK `ON DELETE CASCADE` / `SET NULL` cohérentes avec
  `messages`, `conversations`.
- Respecte la convention de nommage : table en snake_case pluriel,
  colonnes en snake_case.
