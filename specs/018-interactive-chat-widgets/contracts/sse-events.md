# SSE Events Contract — Interactive Chat Widgets

**Feature**: 018-interactive-chat-widgets
**Transport** : Server-Sent Events existant (`astream_events(version="v2")`)
**Emplacement** : `backend/app/api/chat.py::stream_graph_events`
**Format** : `data: {"type": "<event_type>", ...}\n\n`

## Vue d'ensemble

Cette feature ajoute **2 nouveaux types d'événements SSE** au flux chat :

1. `interactive_question` — émis quand le LLM appelle `ask_interactive_question`
2. `interactive_question_resolved` — émis quand la question bascule en
   `answered` / `abandoned` / `expired`

Les événements existants (`token`, `tool_call_start`, `tool_call_end`,
`profile_update`, `done`, etc.) ne sont **pas modifiés**.

## Événement 1 : `interactive_question`

### Source

Émis par la fonction `stream_graph_events` quand elle détecte un marker
`<!--SSE:{"event":"interactive_question",…}-->` dans le retour du tool
`ask_interactive_question` (pattern déjà utilisé pour `profile_update`).

### Payload

```typescript
interface InteractiveQuestionEvent {
  type: "interactive_question"
  id: string              // UUID de la ligne interactive_questions
  conversation_id: string // UUID conversation
  question_type: "qcu" | "qcm" | "qcu_justification" | "qcm_justification"
  prompt: string          // 1-500 caractères
  options: Array<{
    id: string            // slug [a-z0-9_]
    label: string
    emoji?: string
    description?: string
  }>
  min_selections: number  // 1-8
  max_selections: number  // 1-8, >= min_selections
  requires_justification: boolean
  justification_prompt: string | null  // libellé fun
  module: string          // module émetteur (esg_scoring, carbon, …)
  created_at: string      // ISO 8601
}
```

### Exemple sur la ligne SSE

```text
data: {"type":"interactive_question","id":"7c3f…","conversation_id":"a1b2…","question_type":"qcu","prompt":"Quel est ton secteur principal ?","options":[{"id":"agri","label":"Agriculture","emoji":"🌾"},{"id":"energy","label":"Énergie","emoji":"⚡"}],"min_selections":1,"max_selections":1,"requires_justification":false,"justification_prompt":null,"module":"profiling","created_at":"2026-04-11T13:52:10.123Z"}

```

### Ordre garanti

L'événement `interactive_question` est émis **après** le `tool_call_end`
correspondant et **avant** le `done` final du tour. Le frontend l'intercale
dans la conversation à la position du message assistant en cours.

### Côté frontend

- Le composable `useChat.ts` (feature 012) ajoute un handler :
  ```ts
  case "interactive_question":
    currentInteractiveQuestion.value = event
    // injecté dans le dernier message assistant via composant MessageParser
    break
  ```
- Le rendu se fait dans `InteractiveQuestionHost.vue` (voir R7 research.md).

## Événement 2 : `interactive_question_resolved`

### Source

Émis depuis deux points :

1. `POST /api/chat/interactive-questions/{id}/abandon` (état → `abandoned`)
2. Prochain tour LLM qui relit la question en `active_module_data.widget_response`
   (état → `answered`). L'event est émis par `stream_graph_events` en tout
   début du tour suivant, avant le premier `token`.

### Payload

```typescript
interface InteractiveQuestionResolvedEvent {
  type: "interactive_question_resolved"
  id: string              // UUID de la question
  state: "answered" | "abandoned" | "expired"
  response_values: string[] | null       // null si state != 'answered'
  response_justification: string | null  // max 400 car
  answered_at: string     // ISO 8601
}
```

### Exemple

```text
data: {"type":"interactive_question_resolved","id":"7c3f…","state":"answered","response_values":["partial"],"response_justification":"On trie le plastique et le verre mais pas les déchets organiques","answered_at":"2026-04-11T13:52:45.678Z"}

```

### Usage frontend

- Permet de figer le widget dans l'historique (pas cliquable après réponse).
- Transforme le widget en « résumé answered » avec les choix surlignés et la
  justification affichée en italique.

## Événement 3 (déjà existant, non modifié) : `done`

Le `done` final du tour continue d'être émis une seule fois, à la fin de la
génération LLM. Quand une question interactive `pending` subsiste, le
frontend bascule le chat en « mode attente widget » : input texte désactivé
(mais le bouton « Répondre autrement » reste cliquable, clarification Q3).

## Invariants SSE

1. `interactive_question` arrive **toujours avant** `done` dans le même tour.
2. Au plus **1** `interactive_question` par tour (pas d'enchaînement).
3. `interactive_question_resolved` pour `answered` arrive **au début** du
   tour suivant (pas du tour courant).
4. `interactive_question_resolved` pour `abandoned` est émis **immédiatement**
   par l'endpoint REST (diffusion via le flux SSE actif si présent, sinon
   rejoué via la réponse JSON de l'endpoint).

## Tests de contrat

Implémentés dans `backend/tests/integration/test_chat_interactive_sse.py` :

1. Tour avec tool `ask_interactive_question` → séquence
   `tool_call_start` → `tool_call_end` → `interactive_question` → `done`.
2. Tour suivant avec widget_response injectée → séquence
   `interactive_question_resolved(state=answered)` → `token*` → `done`.
3. Abandon via endpoint → `interactive_question_resolved(state=abandoned)`.
4. Nouvelle question émise alors qu'une ancienne est pending → ancienne
   passe à `expired`, nouvelle `interactive_question` émise.
5. Marker SSE `<!--SSE:-->` absent → aucun event `interactive_question`
   (le tool a échoué, comportement dégradé = texte libre).
