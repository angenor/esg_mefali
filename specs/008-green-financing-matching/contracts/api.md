# API Contracts: 008-green-financing-matching

**Prefix**: `/api/financing`
**Auth**: Bearer JWT (get_current_user) sur tous les endpoints sauf mention contraire

---

## Fonds

### GET /funds

Liste des fonds avec filtres optionnels.

**Query Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| fund_type | string | null | Filtre par type (international, regional, national, carbon_market, local_bank_green_line) |
| sector | string | null | Filtre par secteur eligible |
| min_amount | int | null | Montant minimum en FCFA |
| max_amount | int | null | Montant maximum en FCFA |
| access_type | string | null | Filtre par mode d'acces (direct, intermediary_required, mixed) |
| status | string | active | Filtre par statut |
| page | int | 1 | Pagination |
| limit | int | 20 | Taille de page |

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "SUNREF (AFD/Proparco)",
      "organization": "AFD / Proparco",
      "fund_type": "regional",
      "status": "active",
      "access_type": "intermediary_required",
      "intermediary_type": "partner_bank",
      "min_amount_xof": 5000000,
      "max_amount_xof": 500000000,
      "sectors_eligible": ["energie", "agriculture", "industrie"],
      "typical_timeline_months": 6
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 20
}
```

### GET /funds/{fund_id}

Detail d'un fonds avec ses intermediaires.

**Response 200**:
```json
{
  "id": "uuid",
  "name": "SUNREF (AFD/Proparco)",
  "organization": "AFD / Proparco",
  "fund_type": "regional",
  "description": "Ligne de credit verte...",
  "website_url": "https://...",
  "contact_info": {},
  "eligibility_criteria": { "min_revenue": 10000000, "legal_status": ["SARL", "SA"] },
  "sectors_eligible": ["energie", "agriculture"],
  "min_amount_xof": 5000000,
  "max_amount_xof": 500000000,
  "application_deadline": null,
  "required_documents": ["business_plan", "financial_statements", "esg_report"],
  "esg_requirements": { "min_score": 40 },
  "status": "active",
  "access_type": "intermediary_required",
  "intermediary_type": "partner_bank",
  "application_process": [
    { "step": 1, "title": "Contact banque partenaire", "description": "..." },
    { "step": 2, "title": "Montage dossier", "description": "..." }
  ],
  "typical_timeline_months": 6,
  "success_tips": "...",
  "intermediaries": [
    {
      "id": "uuid",
      "name": "SIB",
      "intermediary_type": "partner_bank",
      "organization_type": "bank",
      "city": "Abidjan",
      "role": "Banque partenaire SUNREF",
      "is_primary": true,
      "services_offered": { "credit_evaluation": true, "technical_assistance": true },
      "typical_fees": "Taux d'interet bonifie..."
    }
  ]
}
```

### POST /funds (admin)

Ajouter un nouveau fonds.

**Request Body**: FundCreate schema (tous les champs sauf id, created_at, updated_at)
**Response 201**: FundResponse complet

---

## Intermediaires

### GET /intermediaries

Liste des intermediaires avec filtres.

**Query Params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| intermediary_type | string | null | accredited_entity, partner_bank, etc. |
| organization_type | string | null | bank, development_bank, etc. |
| country | string | null | Filtre par pays |
| city | string | null | Filtre par ville |
| fund_id | uuid | null | Intermediaires lies a un fonds specifique |
| page | int | 1 | Pagination |
| limit | int | 50 | Taille de page |

**Response 200**: Liste paginee d'IntermediaireSummary

### GET /intermediaries/{intermediary_id}

Detail d'un intermediaire avec les fonds couverts.

**Response 200**:
```json
{
  "id": "uuid",
  "name": "SIB (Societe Ivoirienne de Banque)",
  "intermediary_type": "partner_bank",
  "organization_type": "bank",
  "description": "...",
  "country": "Cote d'Ivoire",
  "city": "Abidjan",
  "website_url": "https://...",
  "contact_email": "...",
  "contact_phone": "+225...",
  "physical_address": "...",
  "accreditations": [...],
  "services_offered": { "credit_evaluation": true, "technical_assistance": true },
  "typical_fees": "...",
  "eligibility_for_sme": { "min_revenue": 5000000 },
  "is_active": true,
  "funds_covered": [
    { "id": "uuid", "name": "SUNREF", "role": "Banque partenaire", "is_primary": true }
  ]
}
```

### GET /intermediaries/nearby

Intermediaires proches pour un fonds donne.

**Query Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| city | string | oui | Ville de l'utilisateur |
| fund_id | uuid | non | Fonds specifique |

**Response 200**: Liste d'intermediaires filtres par ville, tries par pertinence

---

## Matching

### GET /matches

Fonds recommandes avec parcours d'acces, tries par compatibilite.

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "fund": { "id": "uuid", "name": "SUNREF", "access_type": "intermediary_required", ... },
      "compatibility_score": 78,
      "matching_criteria": { "sector": 90, "esg": 75, "size": 60, "location": 80, "documents": 70 },
      "missing_criteria": { "documents": ["esg_report"] },
      "recommended_intermediaries": [
        { "id": "uuid", "name": "SIB", "city": "Abidjan" }
      ],
      "estimated_timeline_months": 6,
      "status": "suggested"
    }
  ],
  "total": 8
}
```

### GET /matches/{fund_id}

Detail du matching pour un fonds specifique, incluant le parcours d'acces complet.

**Response 200**:
```json
{
  "id": "uuid",
  "fund": { ... },
  "compatibility_score": 78,
  "matching_criteria": { ... },
  "missing_criteria": { ... },
  "recommended_intermediaries": [ ... ],
  "access_pathway": {
    "steps": [
      { "step": 1, "phase": "preparation", "title": "...", "description": "...", "duration_weeks": 2 },
      { "step": 2, "phase": "contact", "title": "...", "description": "...", "duration_weeks": 1 }
    ],
    "total_duration_months": 6
  },
  "estimated_timeline_months": 6,
  "status": "suggested"
}
```

### PATCH /matches/{match_id}/status

Mettre a jour le statut d'un match.

**Request Body**:
```json
{ "status": "interested" }
```

**Response 200**: MatchResponse mis a jour

### PATCH /matches/{match_id}/intermediary

Enregistrer l'intermediaire choisi.

**Request Body**:
```json
{ "intermediary_id": "uuid" }
```

**Response 200**: MatchResponse mis a jour

---

## Fiche de preparation

### GET /matches/{match_id}/preparation-sheet

Generer et telecharger la fiche de preparation PDF.

**Response 200**: `application/pdf`
**Headers**: `Content-Disposition: attachment; filename="fiche-preparation-{fund_name}.pdf"`
