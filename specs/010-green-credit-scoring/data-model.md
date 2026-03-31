# Data Model: Scoring de Credit Vert Alternatif

**Feature**: 010-green-credit-scoring
**Date**: 2026-03-31

## Entities

### CreditScore

Represente un score de credit vert genere pour un utilisateur a un instant donne. Versionne pour historique.

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| id | UUID | Identifiant unique | PK, auto-genere |
| user_id | UUID | Utilisateur proprietaire | FK → users.id, NOT NULL |
| version | Integer | Numero de version auto-incremente | NOT NULL, >= 1 |
| solvability_score | Float | Score solvabilite (0-100) | NOT NULL, [0, 100] |
| green_impact_score | Float | Score impact vert (0-100) | NOT NULL, [0, 100] |
| combined_score | Float | Score combine ajuste par confiance | NOT NULL, [0, 100] |
| score_breakdown | JSON | Decomposition detaillee par facteur | NOT NULL |
| data_sources | JSON | Sources de donnees utilisees avec couverture | NOT NULL |
| confidence_level | Float | Coefficient de confiance (0.5-1.0) | NOT NULL, [0.5, 1.0] |
| confidence_label | String | Label affichage (tres_faible/faible/moyen/bon/excellent) | NOT NULL |
| recommendations | JSON | Actions d'amelioration personnalisees | NOT NULL |
| generated_at | DateTime | Date de generation | NOT NULL, auto |
| valid_until | DateTime | Date d'expiration (generated_at + 6 mois) | NOT NULL |
| created_at | DateTime | Date de creation en base | NOT NULL, auto |

**Contrainte d'unicite** : (user_id, version) — un utilisateur ne peut pas avoir deux scores avec le meme numero de version.

**Index** : user_id (pour requetes par utilisateur), (user_id, generated_at DESC) pour historique.

#### Structure score_breakdown (JSON)

```json
{
  "solvability": {
    "total": 65.0,
    "factors": {
      "activity_regularity": { "score": 70, "weight": 0.20, "details": "..." },
      "information_coherence": { "score": 60, "weight": 0.20, "details": "..." },
      "governance": { "score": 55, "weight": 0.20, "details": "..." },
      "financial_transparency": { "score": 75, "weight": 0.20, "details": "..." },
      "engagement_seriousness": { "score": 65, "weight": 0.20, "details": "...",
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
    "total": 72.0,
    "factors": {
      "esg_global_score": { "score": 72, "weight": 0.40, "details": "..." },
      "esg_trend": { "score": 60, "weight": 0.20, "details": "..." },
      "carbon_engagement": { "score": 80, "weight": 0.20, "details": "..." },
      "green_projects": { "score": 70, "weight": 0.20, "details": "...",
        "application_statuses": {
          "interested": 1,
          "submitted_via_intermediary": 2,
          "accepted": 0
        }
      }
    }
  }
}
```

#### Structure data_sources (JSON)

```json
{
  "sources": [
    { "name": "Profil entreprise", "available": true, "completeness": 0.85, "last_updated": "2026-03-15" },
    { "name": "Evaluation ESG", "available": true, "completeness": 1.0, "last_updated": "2026-03-20" },
    { "name": "Bilan carbone", "available": true, "completeness": 0.90, "last_updated": "2026-02-10" },
    { "name": "Documents fournis", "available": true, "completeness": 0.60, "last_updated": "2026-03-01" },
    { "name": "Candidatures fonds", "available": true, "completeness": 1.0, "last_updated": "2026-03-25" },
    { "name": "Interactions intermediaires", "available": true, "completeness": 0.70, "last_updated": "2026-03-28" }
  ],
  "overall_coverage": 0.84
}
```

### CreditDataPoint

Donnee unitaire collectee et utilisee pour le calcul du score. Trace l'origine de chaque element du scoring.

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| id | UUID | Identifiant unique | PK, auto-genere |
| user_id | UUID | Utilisateur proprietaire | FK → users.id, NOT NULL |
| category | Enum | Categorie : solvability, green_impact | NOT NULL |
| subcategory | String | Sous-facteur (activity_regularity, esg_global_score, etc.) | NOT NULL |
| data | JSON | Valeur brute de la donnee | NOT NULL |
| weight | Float | Poids dans le calcul (0-1) | NOT NULL |
| verified | Boolean | Donnee verifiee (via document, API, etc.) | NOT NULL, default false |
| source | String | Origine (profile, esg_assessment, carbon_assessment, fund_match, intermediary) | NOT NULL |
| source_id | UUID | ID de l'entite source (optionnel) | Nullable |
| created_at | DateTime | Date de collecte | NOT NULL, auto |

**Index** : user_id, (user_id, category), (user_id, source).

## Relationships

```
User (1) ──── (N) CreditScore        # Un utilisateur a N versions de score
User (1) ──── (N) CreditDataPoint     # Un utilisateur a N points de donnees

CreditScore utilise les donnees de :
  - CompanyProfile (profil entreprise)
  - ESGAssessment (score ESG, tendance)
  - CarbonAssessment (bilan carbone)
  - Document (documents fournis)
  - FundMatch (candidatures, statuts)
  - FundMatch.contacted_intermediary_id → Intermediary (interactions)
```

## Enums

### CreditCategory
- `solvability` — Facteurs de solvabilite
- `green_impact` — Facteurs d'impact vert

### ConfidenceLevel
- `very_low` — < 0.6
- `low` — 0.6 - 0.7
- `medium` — 0.7 - 0.8
- `good` — 0.8 - 0.9
- `excellent` — > 0.9

## State LangGraph (additions)

```python
# Ajouts a ConversationState
credit_data: dict | None        # Donnees scoring en cours
_route_credit: bool             # Flag routage vers credit_node
```

### Structure credit_data

```json
{
  "last_score_id": "uuid",
  "last_score": 74.5,
  "last_generated": "2026-03-31T10:00:00",
  "generating": false
}
```
