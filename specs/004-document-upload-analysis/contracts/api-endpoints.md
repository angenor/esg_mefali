# API Contracts: Documents Module

**Date**: 2026-03-30
**Feature**: 004-document-upload-analysis
**Base URL**: `/api/documents`

---

## POST /api/documents/upload

Upload d'un ou plusieurs fichiers.

**Auth**: Required (JWT Bearer)
**Content-Type**: `multipart/form-data`

**Request**:
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| files | File[] | Oui | Fichiers a uploader (max 5 simultanes) |
| conversation_id | string (UUID) | Non | Conversation associee (pour upload chat) |

**Response 201**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "original_filename": "bilan_2024.pdf",
      "mime_type": "application/pdf",
      "file_size": 2048576,
      "status": "uploaded",
      "document_type": null,
      "created_at": "2026-03-30T14:00:00Z"
    }
  ]
}
```

**Response 400** (fichier invalide):
```json
{
  "detail": "Type de fichier non accepte. Types autorises : PDF, PNG, JPG, JPEG, DOCX, XLSX"
}
```

**Response 413** (taille depassee):
```json
{
  "detail": "Le fichier depasse la taille maximale autorisee (10 MB)"
}
```

---

## GET /api/documents/

Liste des documents de l'utilisateur.

**Auth**: Required (JWT Bearer)

**Query params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| document_type | string | null | Filtrer par type de document |
| status | string | null | Filtrer par statut |
| page | integer | 1 | Page courante |
| limit | integer | 20 | Documents par page |

**Response 200**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "original_filename": "bilan_2024.pdf",
      "mime_type": "application/pdf",
      "file_size": 2048576,
      "status": "analyzed",
      "document_type": "bilan_financier",
      "has_analysis": true,
      "created_at": "2026-03-30T14:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 20
}
```

---

## GET /api/documents/{id}

Detail d'un document avec son analyse.

**Auth**: Required (JWT Bearer)

**Response 200**:
```json
{
  "id": "uuid",
  "original_filename": "bilan_2024.pdf",
  "mime_type": "application/pdf",
  "file_size": 2048576,
  "status": "analyzed",
  "document_type": "bilan_financier",
  "created_at": "2026-03-30T14:00:00Z",
  "analysis": {
    "summary": "Bilan financier de l'exercice 2024 de la societe XYZ...",
    "key_findings": [
      "Chiffre d'affaires de 500M XOF (+15%)",
      "Resultat net de 25M XOF",
      "45 employes dont 40% de femmes"
    ],
    "structured_data": {
      "chiffre_affaires": 500000000,
      "resultat_net": 25000000,
      "total_actif": 300000000
    },
    "esg_relevant_info": {
      "environmental": ["Investissement energies renouvelables"],
      "social": ["40% femmes dans l'effectif"],
      "governance": ["Rapports financiers annuels publies"]
    },
    "analyzed_at": "2026-03-30T14:02:00Z"
  }
}
```

**Response 403** (document d'un autre utilisateur):
```json
{
  "detail": "Acces non autorise"
}
```

**Response 404**:
```json
{
  "detail": "Document non trouve"
}
```

---

## DELETE /api/documents/{id}

Supprime un document, son fichier physique et son analyse.

**Auth**: Required (JWT Bearer)

**Response 204**: No Content

**Response 403**: Acces non autorise
**Response 404**: Document non trouve

---

## POST /api/documents/{id}/reanalyze

Relance l'analyse d'un document (utile apres une erreur).

**Auth**: Required (JWT Bearer)

**Response 200**:
```json
{
  "id": "uuid",
  "status": "processing",
  "message": "Analyse relancee avec succes"
}
```

**Response 403**: Acces non autorise
**Response 404**: Document non trouve

---

## GET /api/documents/{id}/preview

Sert le fichier pour previsualisation (images et PDFs).

**Auth**: Required (JWT Bearer)

**Response 200**: FileResponse avec le bon Content-Type
**Response 403**: Acces non autorise
**Response 404**: Document non trouve

---

## SSE Events (Chat Upload Integration)

Lors de l'upload d'un document dans le chat (via POST `/api/chat/conversations/{id}/messages` avec fichier joint), les evenements SSE suivants sont emis en plus des evenements existants :

| Event Type | Payload | Description |
|-----------|---------|-------------|
| `document_upload` | `{document_id, filename, status: "uploaded"}` | Fichier recu |
| `document_status` | `{document_id, status: "extracting"}` | Extraction texte en cours |
| `document_status` | `{document_id, status: "analyzing"}` | Analyse IA en cours |
| `document_analysis` | `{document_id, summary, document_type}` | Analyse terminee |

Apres `document_analysis`, le flux reprend normalement avec les evenements `token` et `done` habituels (Claude repond avec les blocs visuels).
