# Contrat SSE Events — Tool Calling

## Événements existants (inchangés)

| Type | Payload | Description |
|------|---------|-------------|
| `token` | `{ content: string }` | Token de texte streamé |
| `done` | `{ message_id: string }` | Réponse complète sauvegardée |
| `document_upload` | `{ document_id, filename, status }` | Document uploadé |
| `document_status` | `{ document_id, status }` | Progression analyse document |
| `document_analysis` | `{ document_id, summary, document_type }` | Analyse terminée |
| `profile_update` | `{ field, value, label }` | Champ profil mis à jour |
| `profile_completion` | `{ identity_completion, esg_completion, overall_completion }` | Complétion profil |
| `report_suggestion` | `{ assessment_id, message }` | Suggestion rapport ESG |
| `error` | `{ content: string }` | Erreur générale |

## Nouveaux événements

### `tool_call_start`

Émis quand le LLM initie un appel de tool.

```json
{
  "type": "tool_call_start",
  "tool_name": "update_company_profile",
  "tool_args": { "sector": "agriculture", "city": "Bouaké", "employee_count": 30 },
  "tool_call_id": "call_abc123"
}
```

### `tool_call_end`

Émis quand un tool a terminé avec succès.

```json
{
  "type": "tool_call_end",
  "tool_name": "update_company_profile",
  "tool_call_id": "call_abc123",
  "success": true,
  "result_summary": "Profil mis à jour : sector, city, employee_count. Complétion : 45%."
}
```

### `tool_call_error`

Émis quand un tool échoue après retry.

```json
{
  "type": "tool_call_error",
  "tool_name": "update_company_profile",
  "tool_call_id": "call_abc123",
  "error_message": "Erreur lors de la sauvegarde du profil. Veuillez réessayer."
}
```

## Séquence d'événements — Exemple complet

```
1. User: "je suis dans l'agriculture à Bouaké avec 30 employés"
2. → token: "Je vais sauvegarder..."  (streaming partiel, si le LLM écrit avant d'appeler le tool)
3. → tool_call_start: { tool_name: "update_company_profile", tool_args: {...} }
4. → tool_call_end: { tool_name: "update_company_profile", success: true, result_summary: "..." }
5. → token: "✅ J'ai mis à jour votre profil..." (réponse finale streamée)
6. → profile_update: { field: "sector", value: "agriculture", label: "Secteur" }
7. → profile_update: { field: "city", value: "Bouaké", label: "Ville" }
8. → profile_update: { field: "employee_count", value: 30, label: "Nombre d'employés" }
9. → profile_completion: { identity_completion: 45, esg_completion: 0, overall_completion: 30 }
10. → done: { message_id: "..." }
```

## Mapping Tool Name → Label Frontend

| tool_name | Label affiché |
|-----------|---------------|
| `update_company_profile` | Sauvegarde du profil... |
| `get_company_profile` | Chargement du profil... |
| `create_esg_assessment` | Création de l'évaluation ESG... |
| `save_esg_criterion_score` | Sauvegarde du critère... |
| `finalize_esg_assessment` | Finalisation de l'évaluation ESG... |
| `get_esg_assessment` | Chargement de l'évaluation... |
| `create_carbon_assessment` | Création du bilan carbone... |
| `save_emission_entry` | Sauvegarde de l'entrée... |
| `finalize_carbon_assessment` | Finalisation du bilan carbone... |
| `get_carbon_summary` | Chargement du bilan... |
| `search_compatible_funds` | Recherche des fonds compatibles... |
| `save_fund_interest` | Enregistrement de l'intérêt... |
| `get_fund_details` | Chargement des détails du fonds... |
| `create_fund_application` | Création du dossier... |
| `generate_application_section` | Génération de la section... |
| `update_application_section` | Mise à jour de la section... |
| `get_application_checklist` | Chargement de la checklist... |
| `simulate_financing` | Simulation financière... |
| `export_application` | Exportation du dossier... |
| `generate_credit_score` | Calcul du score de crédit... |
| `get_credit_score` | Chargement du score... |
| `generate_credit_certificate` | Génération de l'attestation... |
| `analyze_uploaded_document` | Analyse du document... |
| `get_document_analysis` | Chargement de l'analyse... |
| `list_user_documents` | Chargement des documents... |
| `generate_action_plan` | Génération du plan d'action... |
| `update_action_item` | Mise à jour de l'action... |
| `get_action_plan` | Chargement du plan d'action... |
| `get_user_dashboard_summary` | Chargement du tableau de bord... |
