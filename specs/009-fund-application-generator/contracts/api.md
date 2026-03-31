# API Contracts — 009 Fund Application Generator

**Base Path**: `/api/applications`

## Endpoints

### POST /applications/

Creer un nouveau dossier de candidature.

**Request Body**:
```json
{
  "fund_id": "uuid",
  "match_id": "uuid | null",
  "intermediary_id": "uuid | null"
}
```

**Response 201**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "fund_id": "uuid",
    "fund_name": "SUNREF",
    "intermediary_id": "uuid | null",
    "intermediary_name": "SIB | null",
    "target_type": "intermediary_bank",
    "status": "draft",
    "sections": { "...cles initialisees a not_generated..." },
    "checklist": [ "...items adaptes au target_type..." ],
    "created_at": "datetime"
  }
}
```

**Logique**: Le target_type est determine automatiquement :
- Si intermediary_id est null → fund_direct
- Si intermediary.intermediary_type == partner_bank → intermediary_bank
- Si intermediary.intermediary_type == implementation_agency → intermediary_agency
- Si intermediary.intermediary_type == project_developer → intermediary_developer

---

### GET /applications/

Liste des dossiers de l'utilisateur.

**Query Params**: `status` (optionnel, filtre par statut)

**Response 200**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "fund_name": "SUNREF",
      "intermediary_name": "SIB",
      "target_type": "intermediary_bank",
      "status": "in_progress",
      "status_label": "Redaction en cours",
      "sections_progress": { "total": 6, "generated": 3, "validated": 1 },
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}
```

---

### GET /applications/{id}

Detail d'un dossier.

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "fund": { "id": "uuid", "name": "SUNREF", "organization": "AFD" },
    "intermediary": { "id": "uuid", "name": "SIB", "contact_email": "...", "contact_phone": "...", "physical_address": "..." } | null,
    "match": { "id": "uuid", "compatibility_score": 82 } | null,
    "target_type": "intermediary_bank",
    "status": "in_progress",
    "status_label": "Redaction en cours",
    "sections": {
      "company_banking_history": { "title": "...", "content": "...", "status": "generated", "updated_at": "..." },
      "...": "..."
    },
    "checklist": [ "..." ],
    "intermediary_prep": { "..." } | null,
    "simulation": { "..." } | null,
    "created_at": "datetime",
    "updated_at": "datetime",
    "submitted_at": "datetime | null"
  }
}
```

---

### POST /applications/{id}/generate-section

Generer ou regenerer une section via LLM + RAG.

**Request Body**:
```json
{
  "section_key": "detailed_financial_plan"
}
```

**Response 200**:
```json
{
  "success": true,
  "data": {
    "section_key": "detailed_financial_plan",
    "title": "Plan financier detaille",
    "content": "<html content genere>",
    "status": "generated",
    "updated_at": "datetime"
  }
}
```

---

### PATCH /applications/{id}/sections/{key}

Modifier manuellement le contenu d'une section.

**Request Body**:
```json
{
  "content": "<html content modifie>",
  "status": "validated"
}
```

**Response 200**:
```json
{
  "success": true,
  "data": {
    "section_key": "detailed_financial_plan",
    "content": "<html content>",
    "status": "validated",
    "updated_at": "datetime"
  }
}
```

---

### GET /applications/{id}/checklist

Checklist documentaire adaptee au destinataire.

**Response 200**:
```json
{
  "success": true,
  "data": [
    {
      "key": "financial_statements",
      "name": "Bilans comptables (3 derniers exercices)",
      "status": "missing",
      "document_id": null,
      "required_by": "intermediary_bank"
    }
  ]
}
```

---

### POST /applications/{id}/simulate

Lancer la simulation de financement.

**Response 200**:
```json
{
  "success": true,
  "data": {
    "eligible_amount_xof": 50000000,
    "roi_green": { "annual_savings_xof": 12000000, "payback_months": 50 },
    "timeline": [
      { "step": "Preparation du dossier", "duration_weeks": "2-4" },
      { "step": "Traitement par la banque", "duration_weeks": "2-4" },
      { "step": "Soumission au fonds", "duration_weeks": "1-2" },
      { "step": "Examen par le fonds", "duration_weeks": "8-16" }
    ],
    "carbon_impact_tco2e": 85,
    "intermediary_fees_xof": 2500000
  }
}
```

---

### POST /applications/{id}/export

Exporter le dossier en PDF ou Word.

**Request Body**:
```json
{
  "format": "pdf" | "docx"
}
```

**Response 200**: Fichier binaire (application/pdf ou application/vnd.openxmlformats-officedocument.wordprocessingml.document).

---

### POST /applications/{id}/prep-sheet

Generer la fiche de preparation intermediaire en PDF.

**Response 200**: Fichier PDF (application/pdf).

**Erreur 400**: Si le dossier n'a pas d'intermediaire (target_type == fund_direct).

---

### PATCH /applications/{id}/status

Mettre a jour le statut du dossier.

**Request Body**:
```json
{
  "status": "submitted_to_intermediary"
}
```

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "submitted_to_intermediary",
    "status_label": "Soumis a l'intermediaire",
    "updated_at": "datetime"
  }
}
```

**Validation**: Les transitions de statut invalides retournent 422 (ex: draft → accepted).
