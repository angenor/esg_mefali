# Contrat API: Chat Endpoints

**Date**: 2026-03-30
**Base URL**: `/api/chat`

## Endpoints existants (pas de changement de contrat)

### POST /conversations
Creer une nouvelle conversation.

**Request Body** (optionnel):
```json
{ "title": "string (optionnel)" }
```

**Response** (201):
```json
{
  "id": "uuid",
  "title": "Nouvelle conversation",
  "current_module": "chat",
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:00:00Z"
}
```

### GET /conversations
Lister les conversations de l'utilisateur (paginee).

**Query params**: `page` (default 1), `limit` (default 20)

**Response** (200):
```json
{
  "items": [Conversation],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

### GET /conversations/{id}/messages
Recuperer les messages d'une conversation (pagines).

**Query params**: `page` (default 1), `limit` (default 50)

**Response** (200):
```json
{
  "items": [Message],
  "total": 15,
  "page": 1,
  "limit": 50
}
```

### POST /conversations/{id}/messages
Envoyer un message. Retourne un flux SSE.

**Request Body**:
```json
{ "content": "string" }
```

**Response** (200, SSE stream):
```
data: {"type": "token", "content": "Bonjour"}
data: {"type": "token", "content": ", voici"}
data: {"type": "token", "content": " mon analyse..."}
data: {"type": "done", "message_id": "uuid"}
```

**Erreurs**:
- 429: Rate limit depasse (30 msg/min)
- 404: Conversation non trouvee
- 403: Conversation n'appartient pas a l'utilisateur

### PATCH /conversations/{id}
Renommer une conversation.

**Request Body**:
```json
{ "title": "Nouveau titre" }
```

**Response** (200):
```json
{
  "id": "uuid",
  "title": "Nouveau titre",
  "current_module": "chat",
  "created_at": "...",
  "updated_at": "..."
}
```

### DELETE /conversations/{id}
Supprimer une conversation et ses messages.

**Response** (204): No content.

## Comportements specifiques a cette feature

### Titre auto-genere
Apres le premier echange (POST /messages), le backend genere automatiquement un titre pour la conversation si elle n'en a pas. Le titre est mis a jour en base et sera visible lors du prochain GET /conversations.

### Streaming des Rich Blocks
Les blocs visuels sont streames comme du texte normal dans les tokens SSE. Exemple :

```
data: {"type": "token", "content": "Voici le score :\n\n```chart\n"}
data: {"type": "token", "content": "{\"type\":\"radar\",\"data\":{\"labels\":"}
data: {"type": "token", "content": "[\"E\",\"S\",\"G\"],\"datasets\":[{\"data\":[65,72,58]}]}}"}
data: {"type": "token", "content": "\n```\n\nComme vous pouvez le voir..."}
data: {"type": "done", "message_id": "uuid"}
```

Le frontend est responsable de parser et rendre les blocs visuels.

### Mode guide
Le message d'accueil (mode guide) est gere cote frontend. Ce n'est PAS un message persiste en base. Il est affiche par le composant WelcomeMessage.vue quand une conversation n'a aucun message.
