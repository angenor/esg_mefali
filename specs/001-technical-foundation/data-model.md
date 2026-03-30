# Data Model: Foundation Technique ESG Mefali

**Date**: 2026-03-30 | **Branch**: `001-technical-foundation`

## Entites

### users

Represente un utilisateur inscrit sur la plateforme.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-genere | Identifiant unique |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Adresse email |
| hashed_password | VARCHAR(255) | NOT NULL | Mot de passe hashe (bcrypt) |
| full_name | VARCHAR(255) | NOT NULL | Nom complet |
| company_name | VARCHAR(255) | NOT NULL | Nom de l'entreprise |
| is_active | BOOLEAN | DEFAULT true | Compte actif |
| created_at | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | Date de creation |
| updated_at | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | Derniere modification |

**Index** : `idx_users_email` UNIQUE sur `email`

### conversations

Represente un fil de conversation entre un utilisateur et l'assistant IA.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-genere | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL | Proprietaire |
| title | VARCHAR(255) | DEFAULT 'Nouvelle conversation' | Titre (auto-genere ou editable) |
| current_module | VARCHAR(50) | DEFAULT 'chat' | Module actif (chat, esg, finance...) |
| created_at | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | Date de creation |
| updated_at | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | Derniere activite |

**Index** : `idx_conversations_user_id` sur `user_id`
**Relation** : Un utilisateur peut avoir plusieurs conversations (1:N)

### messages

Unite d'echange dans une conversation.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-genere | Identifiant unique |
| conversation_id | UUID | FK → conversations.id, NOT NULL | Conversation parente |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('user', 'assistant') | Auteur du message |
| content | TEXT | NOT NULL | Contenu textuel |
| created_at | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | Date d'envoi |

**Index** : `idx_messages_conversation_id` sur `conversation_id`
**Relation** : Une conversation contient plusieurs messages (1:N), ordonnes par `created_at`

## Relations

```
users (1) ──── (N) conversations (1) ──── (N) messages
```

## Notes

- **pgvector** : L'extension est installee et configuree mais aucune colonne vector n'est ajoutee dans cette feature. Elle sera utilisee pour les embeddings de documents dans les modules ESG/RAG futurs.
- **LangGraph checkpointer** : Le `PostgresSaver` de LangGraph cree ses propres tables internes (`checkpoints`, `checkpoint_writes`, etc.) pour persister l'etat du graphe. Ces tables sont distinctes de notre table `messages` et sont gerees automatiquement par LangGraph.
- **Coherence messages/checkpointer** : La table `messages` sert de log lisible et requetable. Le checkpointer LangGraph sert a restaurer l'etat du graphe. Les deux sont maintenus en parallele : le noeud chat sauvegarde dans `messages` apres chaque echange.

## Regles de validation

- **Email** : Format valide (regex standard), unique dans la table users
- **Mot de passe** : Minimum 8 caracteres (valide a l'inscription, stocke hashe)
- **Message content** : 1 a 5000 caracteres
- **Conversation title** : 1 a 255 caracteres

## Migrations Alembic

1. **001_create_users** : Table `users` + index email + extension pgvector
2. **002_create_conversations** : Table `conversations` + FK user_id + index
3. **003_create_messages** : Table `messages` + FK conversation_id + index
