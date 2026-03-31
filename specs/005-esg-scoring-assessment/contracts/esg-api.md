# API Contract: ESG Assessment

**Base path**: `/api/esg`
**Auth**: Bearer JWT (toutes les routes)

---

## POST /assessments

Creer une nouvelle evaluation ESG.

**Request Body**:
```json
{
  "conversation_id": "uuid (optionnel)"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "conversation_id": "uuid | null",
  "version": 1,
  "status": "draft",
  "sector": "agriculture",
  "overall_score": null,
  "environment_score": null,
  "social_score": null,
  "governance_score": null,
  "current_pillar": null,
  "evaluated_criteria": [],
  "created_at": "2026-03-31T10:00:00Z",
  "updated_at": "2026-03-31T10:00:00Z"
}
```

**Errors**:
- `400` : Profil entreprise incomplet (secteur manquant)
- `401` : Non authentifie

---

## GET /assessments

Lister les evaluations de l'utilisateur.

**Query Parameters**:
- `status` (optionnel) : filtrer par statut (draft, in_progress, completed)
- `page` (default 1)
- `limit` (default 10, max 50)

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "version": 1,
      "status": "completed",
      "sector": "agriculture",
      "overall_score": 65.5,
      "environment_score": 72.0,
      "social_score": 68.0,
      "governance_score": 56.5,
      "created_at": "2026-03-31T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 10
}
```

---

## GET /assessments/{id}

Detail complet d'une evaluation.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "conversation_id": "uuid | null",
  "version": 1,
  "status": "completed",
  "sector": "agriculture",
  "overall_score": 65.5,
  "environment_score": 72.0,
  "social_score": 68.0,
  "governance_score": 56.5,
  "assessment_data": {
    "criteria_scores": {
      "E1": { "score": 7, "justification": "Bonne gestion des dechets organiques", "sources": [] },
      "E2": { "score": 5, "justification": "Consommation energetique elevee", "sources": ["doc_uuid"] }
    },
    "pillar_details": {
      "environment": { "raw_score": 65, "weighted_score": 72.0, "weights_applied": {} },
      "social": { "raw_score": 70, "weighted_score": 68.0, "weights_applied": {} },
      "governance": { "raw_score": 55, "weighted_score": 56.5, "weights_applied": {} }
    }
  },
  "recommendations": [
    {
      "priority": 1,
      "criteria_code": "G3",
      "pillar": "governance",
      "title": "Formaliser une politique anti-corruption",
      "description": "Rediger et diffuser un code d'ethique...",
      "impact": "high",
      "effort": "medium",
      "timeline": "3-6 mois"
    }
  ],
  "strengths": [
    {
      "criteria_code": "E7",
      "pillar": "environment",
      "title": "Politique environnementale solide",
      "description": "L'entreprise dispose d'une politique...",
      "score": 9
    }
  ],
  "gaps": [
    {
      "criteria_code": "G5",
      "pillar": "governance",
      "title": "Absence de politique anti-corruption formelle",
      "score": 2
    }
  ],
  "sector_benchmark": {
    "sector": "agriculture",
    "averages": { "environment": 52, "social": 48, "governance": 45, "overall": 48 },
    "position": "above_average",
    "percentile": 72
  },
  "created_at": "2026-03-31T10:00:00Z",
  "updated_at": "2026-03-31T12:00:00Z"
}
```

**Errors**:
- `404` : Evaluation non trouvee
- `403` : Evaluation appartient a un autre utilisateur

---

## POST /assessments/{id}/evaluate

Lancer ou continuer l'evaluation conversationnelle. Cette route est appelee via le flux de chat normal (le `esg_scoring_node` LangGraph gere l'evaluation). Cet endpoint met a jour l'etat de l'evaluation apres chaque interaction.

**Request Body**:
```json
{
  "message": "Nous avons un programme de tri des dechets depuis 2 ans..."
}
```

**Response** `200 OK`:
```json
{
  "assessment_id": "uuid",
  "status": "in_progress",
  "current_pillar": "environment",
  "evaluated_criteria": ["E1", "E2", "E3"],
  "progress_percent": 10,
  "total_criteria": 30
}
```

**Note**: L'evaluation se fait principalement via le flux de chat LangGraph. Cet endpoint est une API de suivi/mise a jour de l'etat, pas le canal principal d'interaction.

---

## GET /assessments/{id}/score

Score detaille avec ventilation par critere.

**Response** `200 OK`:
```json
{
  "assessment_id": "uuid",
  "status": "completed",
  "overall_score": 65.5,
  "color": "orange",
  "pillars": {
    "environment": {
      "score": 72.0,
      "criteria": [
        { "code": "E1", "label": "Gestion des dechets", "score": 7, "max": 10, "weight": 1.2 },
        { "code": "E2", "label": "Consommation energie", "score": 5, "max": 10, "weight": 1.5 }
      ]
    },
    "social": {
      "score": 68.0,
      "criteria": [...]
    },
    "governance": {
      "score": 56.5,
      "criteria": [...]
    }
  },
  "strengths_count": 5,
  "gaps_count": 8,
  "recommendations_count": 6
}
```

---

## GET /benchmarks/{sector}

Benchmark sectoriel pour comparaison.

**Path Parameters**:
- `sector` : Code secteur (agriculture, energie, recyclage, transport, construction, textile, agroalimentaire, services, commerce, artisanat)

**Response** `200 OK`:
```json
{
  "sector": "agriculture",
  "sector_label": "Agriculture",
  "sample_size": "estimation",
  "averages": {
    "environment": 52,
    "social": 48,
    "governance": 45,
    "overall": 48
  },
  "top_criteria": ["E6", "E1", "S4"],
  "weak_criteria": ["G3", "G5", "G10"]
}
```

**Errors**:
- `404` : Secteur inconnu
