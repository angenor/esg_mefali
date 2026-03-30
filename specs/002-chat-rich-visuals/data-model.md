# Data Model: 002-chat-rich-visuals

**Date**: 2026-03-30

## Entites existantes (pas de modification)

### Conversation

| Champ | Type | Contraintes | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | Genere automatiquement |
| user_id | UUID | FK → User, NOT NULL | Proprietaire |
| title | String | nullable | Auto-genere apres premier echange |
| current_module | String | default "chat" | Module actif |
| created_at | DateTime | NOT NULL | Timestamp creation |
| updated_at | DateTime | NOT NULL | Mis a jour a chaque message |

**Relations**: Un utilisateur possede N conversations. Une conversation contient N messages.

### Message

| Champ | Type | Contraintes | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | Genere automatiquement |
| conversation_id | UUID | FK → Conversation, NOT NULL, CASCADE | Conversation parente |
| role | String | 'user' \| 'assistant' | Auteur du message |
| content | Text | NOT NULL | Contenu brut (markdown + blocs visuels encodes) |
| created_at | DateTime | NOT NULL | Timestamp creation |

**Note importante** : Les blocs visuels (Rich Blocks) ne sont PAS des entites en base de donnees. Ils sont contenus dans le champ `content` du message sous forme de blocs de code markdown (` ```chart {...} ``` `). Le parsing et le rendu sont entierement geres cote frontend.

## Types Rich Blocks (frontend uniquement)

Ces types definissent la structure JSON attendue par chaque composant de rendu visuel. Ils ne sont pas persistes en base.

### ChartBlockData

```typescript
interface ChartBlockData {
  type: 'bar' | 'line' | 'pie' | 'doughnut' | 'radar' | 'polarArea'
  data: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      backgroundColor?: string | string[]
      borderColor?: string | string[]
      [key: string]: unknown
    }>
  }
  options?: Record<string, unknown>
}
```

**Validation** : `type`, `data.labels` et `data.datasets` requis. Si absent, fallback erreur.

### TableBlockData

```typescript
interface TableBlockData {
  headers: string[]
  rows: Array<Array<string | number>>
  highlightColumn?: number
  sortable?: boolean
}
```

### GaugeBlockData

```typescript
interface GaugeBlockData {
  value: number
  max: number
  label: string
  thresholds: Array<{ limit: number; color: string }>
  unit?: string
}
```

### ProgressBlockData

```typescript
interface ProgressBlockData {
  items: Array<{
    label: string
    value: number
    max: number
    color?: string
  }>
}
```

### TimelineBlockData

```typescript
interface TimelineBlockData {
  events: Array<{
    date: string
    title: string
    status: 'done' | 'in_progress' | 'todo'
    description?: string
  }>
}
```

### MermaidBlock

Le bloc Mermaid recoit du texte brut (pas du JSON), valide syntaxiquement par `mermaid.parse()` avant rendu.

## Transitions d'etat

### Conversation

```
CREATED → ACTIVE (premier message envoye)
ACTIVE → TITLED (titre auto-genere apres premier echange)
TITLED → ACTIVE (cycle continu de messages)
ANY → DELETED (suppression par l'utilisateur)
```

### Streaming d'un message

```
IDLE → SENDING (utilisateur envoie un message)
SENDING → STREAMING (premiers tokens recus)
STREAMING → COMPLETE (event 'done' recu)
STREAMING → ERROR (erreur reseau ou service)
```

### Rich Block (pendant le streaming)

```
NOT_STARTED → INCOMPLETE (ouverture ``` detectee)
INCOMPLETE → COMPLETE (fermeture ``` detectee)
COMPLETE → RENDERED (composant Vue monte avec succes)
COMPLETE → ERROR (JSON invalide ou echec rendu)
```
