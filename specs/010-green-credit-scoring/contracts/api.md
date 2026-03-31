# API Contracts: Scoring de Credit Vert Alternatif

**Base URL**: `/api/credit`

## POST /credit/generate

Genere un nouveau score de credit vert pour l'utilisateur authentifie.

**Request**: Aucun body requis (utilise les donnees existantes de l'utilisateur).

**Response 201**:
```json
{
  "id": "uuid",
  "version": 3,
  "combined_score": 74.5,
  "solvability_score": 68.0,
  "green_impact_score": 81.0,
  "confidence_level": 0.85,
  "confidence_label": "bon",
  "generated_at": "2026-03-31T10:00:00Z",
  "valid_until": "2026-09-30T10:00:00Z"
}
```

**Response 409**: Generation deja en cours pour cet utilisateur.
```json
{
  "detail": "Une generation de score est deja en cours. Veuillez patienter."
}
```

**Response 422**: Donnees insuffisantes (profil non cree).
```json
{
  "detail": "Profil entreprise requis pour generer un score. Completez votre profil d'abord."
}
```

---

## GET /credit/score

Retourne le score le plus recent de l'utilisateur authentifie.

**Response 200**:
```json
{
  "id": "uuid",
  "version": 3,
  "combined_score": 74.5,
  "solvability_score": 68.0,
  "green_impact_score": 81.0,
  "confidence_level": 0.85,
  "confidence_label": "bon",
  "generated_at": "2026-03-31T10:00:00Z",
  "valid_until": "2026-09-30T10:00:00Z",
  "is_expired": false
}
```

**Response 404**: Aucun score genere.
```json
{
  "detail": "Aucun score de credit vert genere. Utilisez POST /credit/generate pour en creer un."
}
```

---

## GET /credit/score/breakdown

Retourne le detail complet du score le plus recent.

**Response 200**:
```json
{
  "id": "uuid",
  "version": 3,
  "combined_score": 74.5,
  "solvability_score": 68.0,
  "green_impact_score": 81.0,
  "confidence_level": 0.85,
  "confidence_label": "bon",
  "score_breakdown": {
    "solvability": {
      "total": 68.0,
      "factors": {
        "activity_regularity": { "score": 70, "weight": 0.20, "details": "Activite reguliere sur 12 mois" },
        "information_coherence": { "score": 60, "weight": 0.20, "details": "Informations partiellement coherentes" },
        "governance": { "score": 55, "weight": 0.20, "details": "Structure de gouvernance basique" },
        "financial_transparency": { "score": 75, "weight": 0.20, "details": "3 documents financiers fournis" },
        "engagement_seriousness": { "score": 80, "weight": 0.20, "details": "2 intermediaires contactes, 1 dossier soumis",
          "intermediary_interactions": {
            "contacted": 2,
            "appointments": 1,
            "submitted": 1,
            "intermediary_names": ["SUNREF BOAD", "FDE BNDA"]
          }
        }
      }
    },
    "green_impact": {
      "total": 81.0,
      "factors": {
        "esg_global_score": { "score": 72, "weight": 0.40, "details": "Score ESG 72/100" },
        "esg_trend": { "score": 85, "weight": 0.20, "details": "Amelioration de +12 points sur 6 mois" },
        "carbon_engagement": { "score": 80, "weight": 0.20, "details": "Bilan carbone realise, plan de reduction actif" },
        "green_projects": { "score": 90, "weight": 0.20, "details": "2 candidatures soumises via intermediaire",
          "application_statuses": {
            "interested": 1,
            "submitted_via_intermediary": 2,
            "accepted": 0
          }
        }
      }
    }
  },
  "data_sources": {
    "sources": [
      { "name": "Profil entreprise", "available": true, "completeness": 0.85 },
      { "name": "Evaluation ESG", "available": true, "completeness": 1.0 },
      { "name": "Bilan carbone", "available": true, "completeness": 0.90 },
      { "name": "Documents fournis", "available": true, "completeness": 0.60 },
      { "name": "Candidatures fonds", "available": true, "completeness": 1.0 },
      { "name": "Interactions intermediaires", "available": true, "completeness": 0.70 }
    ],
    "overall_coverage": 0.84
  },
  "recommendations": [
    { "action": "Completez votre profil entreprise (15% manquant)", "impact": "high", "category": "solvability" },
    { "action": "Contactez un intermediaire pour votre candidature GCF", "impact": "medium", "category": "engagement" },
    { "action": "Fournissez vos etats financiers des 2 derniers exercices", "impact": "high", "category": "solvability" }
  ],
  "generated_at": "2026-03-31T10:00:00Z",
  "valid_until": "2026-09-30T10:00:00Z"
}
```

---

## GET /credit/score/history

Retourne l'historique des scores de l'utilisateur.

**Query Parameters**:
- `limit` (int, optional, default 10) : Nombre max de scores retournes
- `offset` (int, optional, default 0) : Pagination

**Response 200**:
```json
{
  "scores": [
    {
      "id": "uuid",
      "version": 3,
      "combined_score": 74.5,
      "solvability_score": 68.0,
      "green_impact_score": 81.0,
      "confidence_level": 0.85,
      "confidence_label": "bon",
      "generated_at": "2026-03-31T10:00:00Z"
    },
    {
      "id": "uuid",
      "version": 2,
      "combined_score": 62.0,
      "solvability_score": 55.0,
      "green_impact_score": 69.0,
      "confidence_level": 0.72,
      "confidence_label": "moyen",
      "generated_at": "2026-01-15T10:00:00Z"
    }
  ],
  "total": 3,
  "limit": 10,
  "offset": 0
}
```

---

## GET /credit/score/certificate

Telecharge l'attestation PDF du score le plus recent.

**Response 200**: `application/pdf` — Fichier PDF binaire.

**Response 404**: Aucun score genere.
```json
{
  "detail": "Aucun score disponible pour generer une attestation."
}
```

**Response 410**: Score expire.
```json
{
  "detail": "Score expire. Regenerez votre score avant de telecharger l'attestation."
}
```
