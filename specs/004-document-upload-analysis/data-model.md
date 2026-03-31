# Data Model: Upload et Analyse Intelligente de Documents

**Date**: 2026-03-30
**Feature**: 004-document-upload-analysis

## Entites

### Document

Represente un fichier uploade par un utilisateur.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL | Proprietaire du document |
| conversation_id | UUID | FK → conversations.id, NULLABLE | Conversation associee (si upload chat) |
| filename | string(255) | NOT NULL | Nom de fichier stocke (sanitise) |
| original_filename | string(255) | NOT NULL | Nom original du fichier uploade |
| mime_type | string(100) | NOT NULL | Type MIME valide |
| file_size | integer | NOT NULL, > 0, <= 10485760 | Taille en octets |
| storage_path | string(500) | NOT NULL | Chemin relatif du fichier stocke |
| status | enum | NOT NULL, default: 'uploaded' | Statut de traitement |
| document_type | enum | NULLABLE | Type de document identifie |
| created_at | timestamp | auto | Date de creation |
| updated_at | timestamp | auto | Date de derniere modification |

**Status enum** : `uploaded`, `processing`, `analyzed`, `error`

**Document type enum** : `statuts_juridiques`, `rapport_activite`, `facture`, `contrat`, `politique_interne`, `bilan_financier`, `autre`

**Relations** :
- Appartient a un User (N:1)
- Optionnellement lie a une Conversation (N:1)
- Possede une DocumentAnalysis (1:1, optionnelle)
- Possede plusieurs DocumentChunk (1:N)

**Index** :
- `ix_documents_user_id` sur user_id (requetes de liste)
- `ix_documents_conversation_id` sur conversation_id (requetes chat)
- `ix_documents_status` sur status (filtrage par statut)

---

### DocumentAnalysis

Resultat de l'analyse IA d'un document.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identifiant unique |
| document_id | UUID | FK → documents.id, UNIQUE, NOT NULL | Document analyse |
| raw_text | text | NULLABLE | Texte brut extrait |
| structured_data | jsonb | NULLABLE | Informations structurees extraites |
| summary | text | NULLABLE | Resume en francais |
| key_findings | jsonb | NULLABLE | Liste de points cles |
| esg_relevant_info | jsonb | NULLABLE | Informations pertinentes ESG |
| analyzed_at | timestamp | NULLABLE | Date de l'analyse |
| created_at | timestamp | auto | Date de creation |
| updated_at | timestamp | auto | Date de derniere modification |

**Relations** :
- Appartient a un Document (1:1)

**Structured data format** (exemple bilan financier) :
```json
{
  "chiffre_affaires": 500000000,
  "resultat_net": 25000000,
  "total_actif": 300000000,
  "effectif": 45,
  "exercice": "2024",
  "devise": "XOF"
}
```

**Key findings format** :
```json
[
  "Chiffre d'affaires en hausse de 15% par rapport a l'exercice precedent",
  "Investissement de 50M XOF dans les energies renouvelables",
  "45 employes dont 40% de femmes"
]
```

**ESG relevant info format** :
```json
{
  "environmental": ["Investissement energies renouvelables", "Pas de politique dechets formalisee"],
  "social": ["40% femmes dans l'effectif", "Programme de formation continue"],
  "governance": ["Rapports financiers annuels publies", "Pas de comite ESG formel"]
}
```

---

### DocumentChunk

Segment de texte avec embedding vectoriel pour le RAG.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identifiant unique |
| document_id | UUID | FK → documents.id, NOT NULL | Document source |
| chunk_index | integer | NOT NULL | Position du segment dans le document |
| content | text | NOT NULL | Contenu textuel du segment |
| embedding | vector(1536) | NULLABLE | Vecteur d'embedding |
| metadata | jsonb | NULLABLE | Metadonnees (page, section, etc.) |
| created_at | timestamp | auto | Date de creation |

**Relations** :
- Appartient a un Document (N:1)

**Index** :
- Index HNSW sur embedding pour recherche vectorielle rapide
- `ix_document_chunks_document_id` sur document_id

---

## Transitions d'etat

### Document.status

```
uploaded → processing → analyzed
                     → error → processing (reanalyze)
```

| Transition | Declencheur | Action |
|-----------|-------------|--------|
| uploaded → processing | Debut de l'extraction texte | Lancement du pipeline d'analyse |
| processing → analyzed | Analyse IA terminee | Sauvegarde DocumentAnalysis + embeddings |
| processing → error | Echec extraction ou analyse | Message d'erreur stocke |
| error → processing | Utilisateur clique "Relancer" | Reprise du pipeline |

---

## Regles de validation

### Upload
- Types MIME acceptes : `application/pdf`, `image/png`, `image/jpeg`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Taille maximale : 10MB (10 485 760 octets)
- Nom de fichier : sanitise (caracteres speciaux remplaces, longueur max 255)

### Acces
- Un document est accessible uniquement par son user_id
- Les requetes de liste filtrent toujours par user_id du token JWT
- La suppression supprime le fichier physique ET les enregistrements BDD (cascade)
