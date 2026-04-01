# Catalogue des Tools par Noeud

## Pattern commun

Chaque tool :
- Est décoré avec `@tool` de `langchain_core.tools`
- Accepte `config: RunnableConfig` pour accéder à `user_id` et `db`
- Retourne une `str` (message structuré pour le LLM)
- Gère ses erreurs et retourne un message d'erreur lisible

---

## profiling_node (2 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `update_company_profile` | company_name?, sector?, sub_sector?, employee_count?, annual_revenue_xof?, city?, country?, year_founded?, has_waste_management?, has_energy_policy?, has_gender_policy?, has_training_program?, has_financial_transparency?, governance_structure?, environmental_practices?, social_practices? | `company_service.update_profile()` |
| `get_company_profile` | (aucun) | `company_service.get_profile()` |

---

## esg_scoring_node (4 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `create_esg_assessment` | (aucun) | `esg_service.create_assessment()` |
| `save_esg_criterion_score` | assessment_id: str, criterion_code: str, score: int (0-10), justification: str | `esg_service.update_assessment()` |
| `finalize_esg_assessment` | assessment_id: str | `esg_service.finalize_assessment_with_benchmark()` |
| `get_esg_assessment` | assessment_id?: str | `esg_service.get_assessment()` ou `get_resumable_assessment()` |

---

## carbon_node (4 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `create_carbon_assessment` | year: int | `carbon_service.create_assessment()` |
| `save_emission_entry` | assessment_id: str, category: str, subcategory?: str, quantity: float, unit: str, source_description: str | `carbon_service.add_entries()` |
| `finalize_carbon_assessment` | assessment_id: str | `carbon_service.complete_assessment()` |
| `get_carbon_summary` | assessment_id?: str | `carbon_service.get_assessment_summary()` |

---

## financing_node (4 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `search_compatible_funds` | (aucun) | `financing_service.get_fund_matches()` |
| `save_fund_interest` | fund_id: str | `financing_service.update_match_status()` |
| `get_fund_details` | fund_id: str | `financing_service.get_fund_by_id()` + `compute_compatibility_score()` |
| `create_fund_application` | fund_id: str, intermediary_id?: str | `application_service.create_application()` |

---

## application_node (5 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `generate_application_section` | application_id: str, section_key: str, instructions?: str | `application_service.generate_section()` |
| `update_application_section` | application_id: str, section_key: str, content: str | `application_service.update_section()` |
| `get_application_checklist` | application_id: str | `application_service.get_checklist()` |
| `simulate_financing` | application_id: str | À créer dans le service |
| `export_application` | application_id: str, format: str ("pdf"/"docx") | À créer dans le service |

---

## credit_node (3 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `generate_credit_score` | (aucun) | `credit_service.generate_credit_score()` |
| `get_credit_score` | (aucun) | `credit_service.get_latest_score()` |
| `generate_credit_certificate` | (aucun) | À créer dans le service |

---

## document_node (3 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `analyze_uploaded_document` | document_id: str | `document_service.analyze_document()` |
| `get_document_analysis` | document_id: str | `document_service.get_document()` |
| `list_user_documents` | document_type?: str | `document_service.list_documents()` |

---

## action_plan_node (3 tools)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `generate_action_plan` | timeframe: int (6/12/24 mois) | `action_plan_service.generate_action_plan()` |
| `update_action_item` | action_id: str, status?: str, completion_percentage?: int | `action_plan_service.update_action_item()` |
| `get_action_plan` | (aucun) | `action_plan_service.get_active_plan()` |

---

## chat_node (4 tools — lecture seule)

| Tool | Paramètres LLM | Service appelé |
|------|----------------|----------------|
| `get_user_dashboard_summary` | (aucun) | `dashboard_service.get_dashboard_summary()` |
| `get_company_profile` | (aucun) | `company_service.get_profile()` |
| `get_esg_assessment` | assessment_id?: str | `esg_service.get_assessment()` |
| `get_carbon_summary` | assessment_id?: str | `carbon_service.get_assessment_summary()` |

---

## Total : 32 tools (28 uniques + 4 partagés entre noeuds)

### Services à étendre (nouvelles méthodes)

| Service | Méthode manquante | Description |
|---------|-------------------|-------------|
| `ApplicationService` | `simulate()` | Simulation financière pour un dossier |
| `ApplicationService` | `export()` | Export PDF/Word d'un dossier |
| `CreditService` | `generate_certificate()` | Génération PDF attestation score |
