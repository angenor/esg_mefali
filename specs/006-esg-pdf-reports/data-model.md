# Data Model: Génération de Rapports ESG en PDF

**Feature**: 006-esg-pdf-reports
**Date**: 2026-03-31

## Entités

### Report (nouvelle)

Représente un rapport PDF généré à partir d'une évaluation ESG.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-généré | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL | Propriétaire du rapport |
| assessment_id | UUID | FK → esg_assessments.id, NOT NULL | Évaluation source |
| report_type | Enum | NOT NULL, default: esg_compliance | Type de rapport |
| file_path | String | NOT NULL | Chemin relatif du fichier PDF |
| file_size | Integer | nullable | Taille du fichier en octets |
| status | Enum | NOT NULL, default: generating | Statut de génération |
| generated_at | DateTime | nullable | Date de fin de génération |
| created_at | DateTime | NOT NULL, auto | Date de création |

**Enum report_type** : `esg_compliance` (extensible pour futurs types : carbon_footprint, green_financing)

**Enum status** : `generating`, `completed`, `failed`

### Relations

```
User (1) ──── (N) Report
ESGAssessment (1) ──── (N) Report
```

- Un utilisateur peut avoir plusieurs rapports
- Une évaluation peut générer plusieurs rapports (régénération)
- Un rapport appartient à exactement un utilisateur et une évaluation

### Contraintes métier

- Un rapport ne peut être généré que pour une évaluation au statut `completed`
- Un seul rapport peut être en statut `generating` par évaluation à un instant donné
- L'utilisateur ne peut accéder qu'à ses propres rapports
- Le `file_path` est relatif au répertoire `uploads/reports/`

## Entités existantes impactées

### ESGAssessment (lecture seule)

Le module reports lit les données suivantes depuis l'évaluation existante :
- `overall_score`, `environment_score`, `social_score`, `governance_score`
- `assessment_data` (JSON : scores par critère, détails par pilier)
- `recommendations` (JSON : liste d'actions recommandées)
- `strengths` (JSON : critères forts)
- `gaps` (JSON : critères faibles)
- `sector_benchmark` (JSON : comparaison sectorielle)
- `sector` (string : secteur d'activité)

### User (lecture seule)

Le module reports lit :
- `full_name` (nom de l'utilisateur)
- `company_name` (nom de l'entreprise pour la couverture)

### CompanyProfile (lecture seule)

Le module reports lit si disponible :
- `sector` (secteur pour le benchmarking)
- `employee_count`, `annual_revenue` (contexte entreprise)

## Index recommandés

- `idx_reports_user_id` sur `reports.user_id` (liste des rapports par utilisateur)
- `idx_reports_assessment_id` sur `reports.assessment_id` (rapports par évaluation)
- Contrainte unique composite : `(assessment_id, status)` WHERE `status = 'generating'` (empêche les générations simultanées)

## Migration

Nom : `006_add_reports_table`
- Crée la table `reports`
- Ajoute les index
- Ajoute la contrainte d'unicité partielle
