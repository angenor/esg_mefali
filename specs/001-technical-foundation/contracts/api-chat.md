# API Contract: Chat / Conversation IA

**Base path**: `/api/chat`
**Authentification** : Tous les endpoints requierent `Authorization: Bearer <access_token>`

## POST /api/chat/conversations

Creer une nouvelle conversation.

**Request body** (optionnel) :
```json
{
  "title": "Ma premiere conversation"
}
```

**Reponse 201** :
```json
{
  "id": "uuid",
  "title": "Nouvelle conversation",
  "current_module": "chat",
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:00:00Z"
}
```

---

## GET /api/chat/conversations

Lister les conversations de l'utilisateur connecte.

**Query params** :
- `page` (int, default 1) : Numero de page
- `limit` (int, default 20, max 50) : Nombre par page

**Reponse 200** :
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Discussion ESG",
      "current_module": "chat",
      "created_at": "2026-03-30T10:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20
}
```

---

## GET /api/chat/conversations/{conversation_id}/messages

Recuperer les messages d'une conversation.

**Path params** : `conversation_id` (UUID)

**Query params** :
- `page` (int, default 1)
- `limit` (int, default 50, max 100)

**Reponse 200** :
```json
{
  "items": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Bonjour, je cherche des fonds verts",
      "created_at": "2026-03-30T10:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Bonjour ! Je suis ravi de vous aider...",
      "created_at": "2026-03-30T10:00:01Z"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 50
}
```

**Erreurs** :
- `404` : Conversation introuvable ou n'appartient pas a l'utilisateur

---

## POST /api/chat/conversations/{conversation_id}/messages

Envoyer un message et recevoir la reponse en streaming (SSE).

**Path params** : `conversation_id` (UUID)

**Request body** :
```json
{
  "content": "Bonjour, pouvez-vous m'aider avec mon bilan ESG ?"
}
```

**Validation** :
- `content` : requis, 1-5000 caracteres

**Reponse 200** (SSE stream, `Content-Type: text/event-stream`) :
```
data: {"type": "token", "content": "Bonjour"}

data: {"type": "token", "content": " !"}

data: {"type": "token", "content": " Je"}

data: {"type": "done", "message_id": "uuid"}

```

**Types d'evenements SSE** :
- `token` : Fragment de la reponse de l'assistant
- `done` : Fin du streaming, contient l'id du message complet sauvegarde
- `error` : Erreur en cours de streaming

**Erreurs** :
- `400` : Message vide ou trop long
- `404` : Conversation introuvable
- `503` : Service IA indisponible (timeout ou erreur OpenRouter)

---

## PATCH /api/chat/conversations/{conversation_id}

Modifier le titre d'une conversation.

**Request body** :
```json
{
  "title": "Discussion financement vert"
}
```

**Reponse 200** :
```json
{
  "id": "uuid",
  "title": "Discussion financement vert",
  "current_module": "chat",
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T14:00:00Z"
}
```

---

## DELETE /api/chat/conversations/{conversation_id}

Supprimer une conversation et ses messages.

**Reponse 204** : No content

**Erreurs** :
- `404` : Conversation introuvable ou n'appartient pas a l'utilisateur
