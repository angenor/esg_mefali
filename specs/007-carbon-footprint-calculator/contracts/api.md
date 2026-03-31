# API Contracts: Module Carbon

**Prefix**: `/api/carbon`

## Endpoints

### POST /api/carbon/assessments

Cree un nouveau bilan carbone pour l'annee en cours.

**Request**:
```json
{
  "year": 2026,
  "conversation_id": "uuid-optional"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "conversation_id": "uuid|null",
  "year": 2026,
  "status": "in_progress",
  "total_emissions_tco2e": null,
  "completed_categories": [],
  "created_at": "2026-03-31T10:00:00Z"
}
```

**Response 409** (doublon annee):
```json
{
  "detail": "Un bilan carbone existe deja pour l'annee 2026"
}
```

---

### GET /api/carbon/assessments

Liste les bilans carbone de l'utilisateur connecte.

**Query params**: `page` (default 1), `limit` (default 10), `status` (optional: in_progress|completed)

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "year": 2026,
      "status": "completed",
      "total_emissions_tco2e": 12.5,
      "completed_categories": ["energy", "transport", "waste"],
      "created_at": "2026-03-31T10:00:00Z",
      "updated_at": "2026-03-31T11:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

### GET /api/carbon/assessments/{id}

Recupere un bilan carbone avec ses entrees d'emissions.

**Response 200**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "year": 2026,
  "status": "completed",
  "sector": "agriculture",
  "total_emissions_tco2e": 12.5,
  "completed_categories": ["energy", "transport", "waste"],
  "reduction_plan": {
    "quick_wins": [
      {"action": "...", "reduction_tco2e": 1.2, "savings_fcfa": 500000, "timeline": "3 mois"}
    ],
    "long_term": [
      {"action": "...", "reduction_tco2e": 3.5, "savings_fcfa": 2000000, "timeline": "12 mois"}
    ]
  },
  "entries": [
    {
      "id": "uuid",
      "category": "energy",
      "subcategory": "electricity",
      "quantity": 5000,
      "unit": "kWh",
      "emission_factor": 0.41,
      "emissions_tco2e": 2.05,
      "source_description": "Consommation electrique mensuelle bureau"
    }
  ],
  "created_at": "2026-03-31T10:00:00Z",
  "updated_at": "2026-03-31T11:00:00Z"
}
```

---

### POST /api/carbon/assessments/{id}/entries

Ajoute une ou plusieurs entrees d'emissions a un bilan en cours.

**Request**:
```json
{
  "entries": [
    {
      "category": "energy",
      "subcategory": "electricity",
      "quantity": 5000,
      "unit": "kWh",
      "emission_factor": 0.41,
      "emissions_tco2e": 2.05,
      "source_description": "Consommation electrique mensuelle bureau"
    }
  ],
  "mark_category_complete": "energy"
}
```

**Response 201**:
```json
{
  "entries_added": 1,
  "total_emissions_tco2e": 2.05,
  "completed_categories": ["energy"]
}
```

**Response 400** (bilan deja complete):
```json
{
  "detail": "Ce bilan est deja finalise"
}
```

---

### GET /api/carbon/assessments/{id}/summary

Recupere le resume complet d'un bilan (pour la page resultats).

**Response 200**:
```json
{
  "assessment_id": "uuid",
  "year": 2026,
  "status": "completed",
  "total_emissions_tco2e": 12.5,
  "by_category": {
    "energy": {"emissions_tco2e": 5.2, "percentage": 41.6, "entries_count": 2},
    "transport": {"emissions_tco2e": 4.8, "percentage": 38.4, "entries_count": 3},
    "waste": {"emissions_tco2e": 2.5, "percentage": 20.0, "entries_count": 1}
  },
  "equivalences": [
    {"label": "vols Paris-Dakar", "value": 10.4},
    {"label": "annees de conduite moyenne", "value": 5.2},
    {"label": "arbres necessaires pour compenser (1 an)", "value": 500}
  ],
  "reduction_plan": {
    "quick_wins": [...],
    "long_term": [...]
  },
  "sector_benchmark": {
    "sector": "agriculture",
    "sector_average_tco2e": 18.0,
    "position": "below_average",
    "percentile": 35
  }
}
```

---

### GET /api/carbon/benchmarks/{sector}

Recupere les benchmarks carbone pour un secteur donne.

**Response 200**:
```json
{
  "sector": "agriculture",
  "average_emissions_tco2e": 18.0,
  "median_emissions_tco2e": 15.0,
  "by_category": {
    "energy": 7.5,
    "transport": 5.0,
    "waste": 3.0,
    "agriculture": 2.5
  },
  "sample_size": "estimation",
  "source": "Estimations basees sur moyennes regionales Afrique de l'Ouest"
}
```

**Response 404** (secteur inconnu):
```json
{
  "detail": "Donnees de benchmark non disponibles pour ce secteur",
  "fallback_sector": "services"
}
```
