# Modèles de données — Backend

Documentation du schéma SQLAlchemy async du backend. 22 classes ORM réparties en 14 fichiers sous [backend/app/models/](../backend/app/models/), 13 migrations Alembic, BDD PostgreSQL 16 avec extension `pgvector` pour les embeddings.

## 1. Vue d'ensemble

```
              ┌─────────────┐
              │    User     │
              └──────┬──────┘
                     │ 1:1
         ┌───────────┼───────────┐
         │           │           │
  ┌──────▼────┐ ┌────▼────────┐ ┌▼──────────┐ …etc par domaine métier
  │ Company   │ │Conversations│ │ Documents │
  │ Profile   │ │             │ │           │
  └───────────┘ └──┬──────────┘ └─┬─────────┘
                   │              │
                   │ 1:N          │ 1:N
                   ▼              ▼
              ┌─────────┐    ┌──────────────────┐
              │Messages │    │Document Analysis │
              └─────────┘    │Document Chunks   │
                             │(embedding vecteur)│
                             └──────────────────┘
```

## 2. Conventions

- **Clé primaire** : UUID v4 ou identifiant auto-incrémenté selon la table.
- **Timestamps** : `created_at` + `updated_at` (UTC, type `DateTime(timezone=True)`).
- **JSONB** : utilisé pour les champs structurés mais non normalisés (scores ESG, sections de dossiers, options de widgets).
- **Vecteurs** : `VECTOR(1536)` via pgvector (compatible `text-embedding-3-small`).
- **Soft delete** : non implémenté par défaut (ajout ponctuel via `status` enum pour `documents`, `applications`, `reports`).
- **Nommage** : tables en snake_case pluriel (`conversations`, `esg_scores`).

## 3. Modèles par domaine

### 3.1 Auth & Entreprise

#### User — [`models/user.py`](../backend/app/models/user.py)
Table : `users`

| Colonne | Type | Contrainte |
|---|---|---|
| `id` | UUID | PK |
| `email` | str | unique, indexed |
| `hashed_password` | str | bcrypt |
| `full_name` | str | nullable |
| `company_name` | str | nullable |
| `is_active` | bool | default true |
| `created_at`, `updated_at` | timestamp | — |

Relations : 1:1 `CompanyProfile`, 1:N `Conversation`, `Document`, `ESGAssessment`, `CarbonAssessment`, `CreditScore`, `FundMatch`, `FundApplication`, `ActionPlan`, `Report`.

#### CompanyProfile — [`models/company.py`](../backend/app/models/company.py)
Table : `company_profiles`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users, unique |
| `company_name` | str | |
| `country` | str(3) | code ISO |
| `sector` | str | agriculture / energie / recyclage / transport… |
| `employees` | int | |
| `revenue` | int | FCFA |
| `description` | text | |
| `esg_score_snapshot` | float | dernière évaluation |
| `carbon_emissions_snapshot` | float | tCO2e |
| `completion_percentage` | float | 0-100 |
| `created_at`, `updated_at` | timestamp | |

### 3.2 Conversation & Chat

#### Conversation — [`models/conversation.py`](../backend/app/models/conversation.py)
Table : `conversations`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users |
| `title` | str | auto-généré si vide |
| `thread_id` | str | identifiant LangGraph (pour checkpointing) |
| `previous_thread_summary` | text | résumé de la précédente (spec 003) |
| `active_module` | str \| null | spec 013 |
| `active_module_data` | JSONB \| null | spec 013 |
| `created_at`, `updated_at` | timestamp | |

Relations : N:1 `User`, 1:N `Message`, 1:N `InteractiveQuestion`, 1:N `ToolCallLog`.

#### Message — [`models/message.py`](../backend/app/models/message.py)
Table : `messages`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `conversation_id` | UUID | FK |
| `role` | enum | `user` / `assistant` / `tool` |
| `content` | text | markdown possible |
| `metadata` | JSONB | blocs richblocks, tool call ids, etc. |
| `created_at` | timestamp | indexed (tri chronologique) |

#### InteractiveQuestion — [`models/interactive_question.py`](../backend/app/models/interactive_question.py) *(spec 018)*
Table : `interactive_questions`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `conversation_id` | UUID | FK, indexed |
| `assistant_message_id` | UUID | FK → messages (la question) |
| `response_message_id` | UUID \| null | FK → messages (la réponse, si texte libre) |
| `module` | str | `chat`, `esg_scoring`, `carbon`, `financing`, `application`, `credit`, `action_plan` |
| `question_type` | enum | `qcu`, `qcm`, `qcu_justification`, `qcm_justification` |
| `prompt` | text | énoncé |
| `options` | JSONB | `[{id, label, description?}, …]` |
| `min_selections`, `max_selections` | int | bornes QCM |
| `requires_justification` | bool | |
| `justification_prompt` | str \| null | |
| `state` | enum | `pending` / `answered` / `abandoned` / `expired` |
| `response_values` | JSONB \| null | `[option_id, …]` |
| `response_justification` | str \| null | max 400 chars |
| `created_at`, `answered_at` | timestamp | |

**Invariant** : une seule question `pending` par `conversation_id` à tout instant. Les autres sont marquées `expired` lors de l'insertion d'une nouvelle.

**Indices** : `(conversation_id)`, `(state)`, `(module)`, `(conversation_id, state)`.

#### ToolCallLog — [`models/tool_call_log.py`](../backend/app/models/tool_call_log.py) *(spec 012)*
Table : `tool_call_logs`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK, indexed |
| `conversation_id` | UUID | FK, indexed |
| `node_name` | str | `chat`, `esg_scoring`, … |
| `tool_name` | str | indexed |
| `tool_args` | JSONB | |
| `tool_result` | JSONB | |
| `duration_ms` | int | |
| `status` | enum | `success` / `error` |
| `error_message` | text \| null | |
| `retry_count` | int | default 0 |
| `created_at` | timestamp | indexed |

**Indices** : `(user_id, created_at DESC)`, `(conversation_id)`, `(tool_name, status)`.

### 3.3 Documents

#### Document — [`models/document.py`](../backend/app/models/document.py)
Table : `documents`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `filename` | str | |
| `file_type` | enum | `pdf` / `docx` / `xlsx` |
| `file_path` | str | local filesystem |
| `status` | enum | `processing` / `analyzed` / `error` |
| `error_message` | text \| null | |
| `created_at`, `updated_at` | timestamp | |

#### DocumentAnalysis
Table : `document_analyses`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `document_id` | UUID | FK, unique |
| `summary` | text | résumé LLM |
| `extracted_text` | text | |
| `metadata` | JSONB | pages, langues détectées, etc. |
| `created_at`, `updated_at` | timestamp | |

#### DocumentChunk
Table : `document_chunks`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `document_id` | UUID | FK, indexed |
| `chunk_text` | text | |
| `embedding` | VECTOR(1536) | pgvector |
| `page_number` | int | |
| `order` | int | |
| `metadata` | JSONB | |
| `created_at` | timestamp | |

Usage : RAG sur les documents utilisateur, requête `<->` (cosine distance).

### 3.4 ESG

#### ESGAssessment — [`models/esg.py`](../backend/app/models/esg.py)
Table : `esg_assessments`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `conversation_id` | UUID | FK |
| `sector` | str | pondération dynamique |
| `criteria` | JSONB | 30 critères E-S-G |
| `scores` | JSONB | score par critère |
| `overall_score` | float | 0-100 |
| `status` | enum | `draft` / `completed` |
| `created_at`, `updated_at` | timestamp | |

**Note** : pas de table d'historique dédiée. L'historique se reconstruit via les assessments `completed` successifs.

### 3.5 Carbone

#### CarbonAssessment — [`models/carbon.py`](../backend/app/models/carbon.py)
Table : `carbon_assessments`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `conversation_id` | UUID | FK |
| `year` | int | |
| `status` | enum | `draft` / `completed` |
| `baseline_emissions` | float | tCO2e |
| `reduction_target` | float | % |
| `created_at`, `updated_at` | timestamp | |

**Contrainte unique** : `(user_id, year)` (un seul bilan par année).

#### CarbonEmissionEntry
Table : `carbon_emission_entries`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `assessment_id` | UUID | FK |
| `category` | enum | `energie` / `transport` / `dechets` / `industriel` / `agriculture` |
| `value` | float | quantité |
| `unit` | str | kWh, km, kg, L, … |
| `emission_factor` | float | facteur Afrique de l'Ouest |
| `tco2e` | float | résultat calculé |
| `source` | str | description libre |
| `created_at` | timestamp | |

### 3.6 Crédit vert

#### CreditScore — [`models/credit.py`](../backend/app/models/credit.py)
Table : `credit_scores`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `conversation_id` | UUID | FK |
| `score` | float | 0-100 |
| `confidence_level` | float | 0-1 |
| `criteria` | JSONB | facteurs de calcul |
| `expires_at` | timestamp | validité du certificat |
| `created_at` | timestamp | |

#### CreditDataPoint
Table : `credit_data_points`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `credit_score_id` | UUID | FK |
| `category` | str | `mobile_money`, `factures`, `photos_ia`, … |
| `value` | float | |
| `weight` | float | pondération |
| `created_at` | timestamp | |

### 3.7 Financement

#### Fund — [`models/financing.py`](../backend/app/models/financing.py)
Table : `funds`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | GCF, FEM, BOAD, BAD, SUNREF, FNDE… |
| `description` | text | |
| `country` | str | |
| `min_amount` | int | FCFA |
| `max_amount` | int | FCFA |
| `sector_focus` | JSONB | secteurs éligibles |
| `access_type` | enum | `direct` / `intermédiaire` |
| `criteria` | JSONB | conditions d'éligibilité |
| `contact` | JSONB | url, email, téléphone |
| `created_at`, `updated_at` | timestamp | |

#### Intermediary
Table : `intermediaries`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | |
| `type` | enum | `banque`, `ONG`, `institution_publique`, `cabinet_conseil` |
| `country` | str | |
| `location` | JSONB | ville, région |
| `contact` | JSONB | |
| `website` | str | |
| `description` | text | |
| `created_at`, `updated_at` | timestamp | |

#### FundIntermediary (table de liaison)
Table : `fund_intermediaries` — clef composite `(fund_id, intermediary_id)`.

#### FundMatch
Table : `fund_matches`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `fund_id` | UUID | FK |
| `match_score` | float | 0-100 |
| `criteria_matched` | JSONB | détail multi-critères |
| `status` | enum | `matched` / `applied` / `shortlisted` / `rejected` |
| `created_at`, `updated_at` | timestamp | |

#### FinancingChunk
Table : `financing_chunks` — embeddings des descriptifs de fonds pour RAG.

| Colonne | Type |
|---|---|
| `id` | UUID |
| `fund_id` | UUID FK |
| `chunk_text` | text |
| `embedding` | VECTOR(1536) |

### 3.8 Candidatures

#### FundApplication — [`models/application.py`](../backend/app/models/application.py)
Table : `fund_applications`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `fund_id` | UUID | FK |
| `conversation_id` | UUID | FK |
| `status` | enum | `draft` / `submitted` / `accepted` / `rejected` |
| `sections` | JSONB | `{summary, esg, financials, carbon_plan, …}` |
| `created_at`, `updated_at` | timestamp | |

### 3.9 Plan d'action

#### ActionPlan — [`models/action_plan.py`](../backend/app/models/action_plan.py)
Table : `action_plans`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `assessment_id` | UUID \| null | FK ESG ou carbon |
| `title` | str | |
| `description` | text | |
| `status` | enum | `active` / `archived` |
| `timeframe` | enum | `6m` / `12m` / `24m` |
| `created_at`, `updated_at` | timestamp | |

#### ActionItem
Table : `action_items`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `plan_id` | UUID | FK |
| `title`, `description` | str / text | |
| `category` | enum | `environment` / `social` / `governance` / `financing` / `carbon` / `intermediary_contact` |
| `priority` | enum | `low` / `medium` / `high` |
| `status` | enum | `todo` / `in_progress` / `done` |
| `completion_pct` | float | 0-100 |
| `due_date` | date | |
| `intermediary_snapshot` | JSONB \| null | coordonnées figées |
| `created_at`, `updated_at` | timestamp | |

#### Reminder
Table : `reminders`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `item_id` | UUID | FK |
| `type` | enum | `action_due` / `assessment_renewal` / `fund_deadline` / `intermediary_followup` / `custom` |
| `scheduled_at` | timestamp | |
| `sent_at` | timestamp \| null | |
| `message` | text | |
| `created_at` | timestamp | |

#### Badge
Table : `badges`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `plan_id` | UUID | FK |
| `badge_type` | enum | `first_carbon` / `esg_above_50` / `first_application` / `first_intermediary_contact` / `full_journey` |
| `earned_at` | timestamp | |
| `created_at` | timestamp | |

### 3.10 Rapports

#### Report — [`models/report.py`](../backend/app/models/report.py)
Table : `reports`

| Colonne | Type | Note |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `assessment_id` | UUID | FK (ESG ou carbon) |
| `report_type` | enum | `esg` / `carbon` / `financing` |
| `file_path` | str | |
| `status` | enum | `generating` / `ready` / `error` |
| `created_at`, `updated_at` | timestamp | |

## 4. Migrations Alembic

Toutes dans [backend/alembic/versions/](../backend/alembic/versions/). Ordre chronologique :

| Fichier | Contenu |
|---|---|
| `001_create_users.py` | Table `users` + extension `vector` |
| `f9b659a2b8e6_créer_les_tables_conversations_et_…` | Tables `conversations` + `messages` |
| `163318558259_add_documents_tables.py` | Tables `documents`, `document_analyses`, `document_chunks` (embedding pgvector) |
| `2b24b1676e59_add_company_profiles_table_and_…` | Table `company_profiles` |
| `005_add_esg_assessments.py` | Table `esg_assessments` |
| `006_add_reports_table.py` | Table `reports` |
| `007_add_carbon_tables.py` | Tables `carbon_assessments` + `carbon_emission_entries` |
| `008_add_financing_tables.py` | Tables `funds`, `intermediaries`, `fund_intermediaries`, `fund_matches`, `financing_chunks` |
| `73d72f6ebd8f_add_fund_applications_table.py` | Table `fund_applications` |
| `68cd43ef0091_add_credit_score_tables.py` | Tables `credit_scores` + `credit_data_points` |
| `5b7f090f1dcc_add_action_plan_dashboard_tables.py` | Tables `action_plans`, `action_items`, `reminders`, `badges` |
| `54432e29b7f3_add_tool_call_logs_table.py` | Table `tool_call_logs` (spec 012) |
| `018_create_interactive_questions.py` | Table `interactive_questions` + indices (spec 018) |

Commandes utiles (depuis `backend/` avec venv actif) :

```bash
alembic upgrade head         # Applique toutes les migrations en attente
alembic downgrade -1         # Revient d'un cran
alembic history              # Historique
alembic current              # Version actuelle
alembic revision --autogenerate -m "add_my_table"
```

## 5. Extensions PostgreSQL

- **`vector`** (pgvector) — embeddings `DocumentChunk.embedding` + `FinancingChunk.embedding`.
- **`uuid-ossp` / `pgcrypto`** — via la migration initiale pour génération d'UUID côté base.

## 6. Performance & indices

- Indices explicites :
  - `users(email)` unique.
  - `messages(conversation_id, created_at)` pour pagination conversationnelle.
  - `tool_call_logs(user_id, created_at DESC)`, `(conversation_id)`, `(tool_name, status)`.
  - `interactive_questions(conversation_id, state)` + `(state)` + `(module)`.
- Pas d'index ANN/HNSW sur les colonnes `embedding` — OK tant que le volume reste modeste (<100k documents). À ajouter avant la montée en charge.

## 7. Contraintes d'intégrité connues

- `CompanyProfile.user_id` unique (1:1 avec User).
- `CarbonAssessment(user_id, year)` unique.
- `InteractiveQuestion` : unicité implicite par l'invariant applicatif (le backend expire les anciennes avant insertion).
- Aucune contrainte `ON DELETE CASCADE` automatique — la suppression d'un utilisateur nécessite un cleanup manuel ou un script dédié. À prévoir avant un "right to be forgotten" RGPD.

## 8. Volumes de données attendus

| Table | Ordre de grandeur attendu |
|---|---|
| `users` | Milliers |
| `conversations` | Dizaines de milliers |
| `messages` | Centaines de milliers à millions |
| `document_chunks` | Millions (après accumulation) — à surveiller |
| `tool_call_logs` | Millions — prévoir une purge ou partitionnement |
| `interactive_questions` | Centaines de milliers — ratio ~30% des messages |

## 9. Stratégies d'évolution

- **Partitionnement temporel** des tables `messages` et `tool_call_logs` si la volumétrie explose.
- **Index HNSW** sur `document_chunks.embedding` dès 50k+ docs.
- **Archivage** des conversations inactives (> 6 mois).
- **Migration vers stockage objet** (S3/MinIO) pour les uploads — actuellement filesystem local.
