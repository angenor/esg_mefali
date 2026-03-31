# Data Model: Calculateur d'Empreinte Carbone

**Date**: 2026-03-31 | **Feature**: 007-carbon-footprint-calculator

## Entities

### CarbonAssessment

Represente un bilan carbone annuel pour une entreprise.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identifiant unique |
| user_id | UUID | FK → users.id, NOT NULL | Utilisateur proprietaire |
| conversation_id | UUID | FK → conversations.id, NULL | Conversation associee |
| year | INTEGER | NOT NULL | Annee du bilan |
| sector | VARCHAR | NULL | Secteur d'activite (copie du profil) |
| total_emissions_tco2e | FLOAT | NULL | Total emissions calculees |
| status | ENUM | NOT NULL, default 'in_progress' | in_progress, completed |
| completed_categories | JSON | default [] | Liste des categories deja completees |
| reduction_plan | JSON | NULL | Plan de reduction genere par l'IA |
| created_at | TIMESTAMP | auto | Date de creation |
| updated_at | TIMESTAMP | auto | Date de derniere modification |

**Contraintes**:
- UNIQUE(user_id, year) — un seul bilan par utilisateur et par annee
- status IN ('in_progress', 'completed')

**Relations**:
- Un CarbonAssessment appartient a un User (many-to-one)
- Un CarbonAssessment peut etre lie a une Conversation (many-to-one, nullable)
- Un CarbonAssessment contient plusieurs CarbonEmissionEntry (one-to-many, cascade delete)

---

### CarbonEmissionEntry

Represente une ligne d'emission individuelle dans un bilan.

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identifiant unique |
| assessment_id | UUID | FK → carbon_assessments.id, NOT NULL | Bilan parent |
| category | VARCHAR | NOT NULL | Categorie (energy, transport, waste, industrial, agriculture) |
| subcategory | VARCHAR | NOT NULL | Sous-categorie (electricity, diesel_generator, gasoline, etc.) |
| quantity | FLOAT | NOT NULL | Quantite mesuree |
| unit | VARCHAR | NOT NULL | Unite (kWh, L, kg, km) |
| emission_factor | FLOAT | NOT NULL | Facteur d'emission applique (kgCO2e/unite) |
| emissions_tco2e | FLOAT | NOT NULL | Emissions calculees en tCO2e |
| source_description | VARCHAR | NULL | Description libre de la source |
| created_at | TIMESTAMP | auto | Date de creation |

**Contraintes**:
- quantity > 0
- emission_factor > 0
- emissions_tco2e > 0
- category IN ('energy', 'transport', 'waste', 'industrial', 'agriculture')

**Relations**:
- Un CarbonEmissionEntry appartient a un CarbonAssessment (many-to-one)

## State Transitions

### CarbonAssessment.status

```
in_progress → completed (quand toutes les categories obligatoires sont completees)
```

Note : Pas de transition retour (completed → in_progress). Un bilan complete est immutable. Pour corriger, l'utilisateur cree un nouveau bilan (annee suivante) ou demande une revision (future feature).

### Categories (progression)

```
energy → transport → waste → [industrial] → [agriculture] → FINALIZE
```

Les categories entre crochets sont optionnelles (proposees selon le secteur de l'entreprise).

## Indexes

- `idx_carbon_assessments_user_id` ON carbon_assessments(user_id)
- `idx_carbon_assessments_user_year` UNIQUE ON carbon_assessments(user_id, year)
- `idx_carbon_entries_assessment_id` ON carbon_emission_entries(assessment_id)
- `idx_carbon_entries_category` ON carbon_emission_entries(assessment_id, category)
