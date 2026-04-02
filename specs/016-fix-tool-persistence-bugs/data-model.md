# Data Model: Fix Tool Persistence Bugs

**Aucun nouveau modèle de données requis.** Les entités existantes sont correctes et suffisantes.

## Entités existantes concernées (lecture seule)

### ESG Assessment
- Table : `esg_assessments`
- Champs clés : `id`, `user_id`, `status`, `current_pillar`, `evaluated_criteria` (list), `assessment_data.criteria_scores` (dict)
- Le tool `save_esg_criterion_score` / `batch_save_esg_criteria` met à jour `evaluated_criteria` et `criteria_scores`

### Carbon Assessment
- Table : `carbon_assessments`
- Champs clés : `id`, `user_id`, `year`, `status`, `entries` (list), `total_emissions_tco2e`, `completed_categories`
- Le tool `save_emission_entry` ajoute à `entries` et met à jour `total_emissions_tco2e`

### Fund / Fund Intermediary
- Tables : `funds`, `fund_intermediaries`, `fund_intermediary_links`
- Le tool `search_compatible_funds` lit ces tables pour le matching

## Pas de migration Alembic nécessaire

Tous les changements sont dans la couche prompt/LLM, pas dans la couche données.
