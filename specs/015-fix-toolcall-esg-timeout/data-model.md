# Data Model: 015-fix-toolcall-esg-timeout

## Entites impactees

Aucune nouvelle entite. Les modifications portent sur les tools et prompts, pas sur le schema de donnees.

### FundApplication (existante, inchangee)

- `id`: UUID (PK)
- `user_id`: UUID (FK users)
- `fund_id`: UUID (FK funds)
- `status`: Enum (draft, in_progress, submitted, accepted, rejected)
- `sections`: JSON (dictionnaire section_key → content)
- `created_at`, `updated_at`: Timestamps

**Impact**: Le nouveau tool `create_fund_application` cree des lignes dans cette table. Pas de migration Alembic necessaire.

### CreditScore (existante, inchangee)

- `id`: UUID (PK)
- `user_id`: UUID (FK users)
- `combined_score`, `solvability_score`, `green_impact_score`: Integer (0-100)
- `confidence_coefficient`: Float (0.5-1.0)
- `version`: Integer (auto-increment)
- `factors`: JSON (detail des facteurs)

**Impact**: Aucun changement de schema. Le tool `generate_credit_score` existe deja.

### EsgAssessment (existante, inchangee)

- `id`: UUID (PK)
- `user_id`: UUID (FK users)
- `sector`: String
- `status`: Enum (draft, in_progress, completed)
- `assessment_data`: JSON (contient `criteria_scores`: dict code → {score, justification})
- `evaluated_criteria`: Array[String] (liste des codes evalues)
- `current_pillar`: String (environment, social, governance)
- `overall_score`, `environment_score`, `social_score`, `governance_score`: Integer (0-100)

**Impact**: Le nouveau tool `batch_save_esg_criteria` ecrit dans `assessment_data.criteria_scores` et `evaluated_criteria` en une seule transaction, exactement comme `save_esg_criterion_score` mais pour N criteres a la fois. Pas de migration necessaire.

## Nouveaux tools (pas des entites, mais des interfaces)

### create_fund_application (nouveau)

- **Input**: `fund_id: str`, `target_type: str` (optional, defaut auto-detecte), `config: RunnableConfig`
- **Output**: String avec l'ID du dossier cree et les infos de base
- **Side effect**: INSERT dans la table `fund_applications`

### batch_save_esg_criteria (nouveau)

- **Input**: `assessment_id: str`, `criteria: list[dict]` (chaque dict: criterion_code, score, justification), `config: RunnableConfig`
- **Output**: String avec le nombre de criteres sauvegardes et les scores partiels
- **Side effect**: UPDATE unique sur `assessment_data` et `evaluated_criteria` de l'assessment
