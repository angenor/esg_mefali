# Modèles de données — Backend

Documentation exhaustive des modèles SQLAlchemy async du backend. 16 fichiers dans `backend/app/models/`, ~1717 lignes de code, 13 migrations Alembic, BDD PostgreSQL 16 avec extension `pgvector`.

## 1. Mixins communs — `models/base.py`

- `Base` — `DeclarativeBase` SQLAlchemy 2.x
- `UUIDMixin` — colonne `id: Mapped[UUID]` primary key (UUID v4 généré côté Python)
- `TimestampMixin` — `created_at` / `updated_at` (`DateTime(timezone=True)`, default `func.now()`)

Toutes les tables métier héritent de `Base + UUIDMixin + TimestampMixin`.

## 2. Utilisateurs et profil entreprise

### `users` — `models/user.py`

| Colonne | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `email` | str unique | Login, index |
| `hashed_password` | str | bcrypt |
| `full_name` | str | Nom complet |
| `company_name` | str \| None | Renseigné à l'inscription |
| `created_at` / `updated_at` | timestamp | Mixin |

**Relations** : 1-1 avec `CompanyProfile` (via `user_id`), 1-N avec `Conversation`, `Document`, `ESGAssessment`, `CarbonAssessment`, `FundApplication`, `CreditScore`, `ActionPlan`, `Report`.

### `company_profiles` — `models/company.py`

Profil métier dérivé du `User`. Un `CompanyProfile` par utilisateur, initialisé à l'inscription avec le pays détecté par IP.

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | 1-1 |
| `company_name` | str | |
| `country` | str | Code ISO |
| `sector` | `SectorEnum` | Agriculture, énergie, recyclage, transport, industrie, services, etc. |
| `employees` | int \| None | |
| `revenue_fcfa` | int \| None | Chiffre d'affaires en FCFA |
| `location` | str \| None | Région |
| `city` | str \| None | |
| `year_founded` | int \| None | |

## 3. Conversation et chat

### `conversations` — `models/conversation.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `title` | str | Généré automatiquement à partir du 1er message |
| `archived` | bool | Archivage soft |
| `created_at` / `updated_at` | timestamp | Tri dernière activité |

**Relations** : 1-N avec `Message`.

### `messages` — `models/message.py`

| Colonne | Type | Notes |
|---|---|---|
| `conversation_id` | UUID FK | Cascade delete |
| `role` | str | `user` ou `assistant` |
| `content` | text | Réponse brute (peut contenir markers `<!--SSE:...-->` pour widgets) |
| `created_at` | timestamp | |

## 4. Documents et RAG

### `documents` — `models/document.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | Propriétaire |
| `filename` | str | Nom original |
| `file_path` | str | Chemin relatif dans `/uploads/` |
| `original_mime_type` | str | PDF / DOCX / XLSX / image |
| `file_size` | int | Octets |
| `status` | `DocumentStatus` enum | `uploaded` / `processing` / `analyzed` / `failed` |
| `document_type` | `DocumentType` enum | Type métier (facture, bilan, rapport ESG, ...) |

**Relations** : 1-1 avec `DocumentAnalysis` (résumé LLM), 1-N avec `DocumentChunk` (chunks vectoriels).

### `document_analyses`

- `document_id` FK
- `analysis_summary` : text — résumé généré par Claude
- `key_findings` : JSONB — points clés structurés
- `esg_signals` : JSONB — signaux ESG extraits (opportunités, risques)

### `document_chunks`

- `document_id` FK
- `chunk_index` : int — ordre dans le document
- `content` : text — texte brut du chunk (1000-2000 tokens typiquement)
- `embedding` : `Vector(1536)` — pgvector, modèle `text-embedding-3-small` OpenAI

## 5. Évaluation ESG

### `esg_assessments` — `models/esg.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `sector` | str | Dupliqué depuis `CompanyProfile` (peut différer) |
| `status` | `ESGStatusEnum` | `draft` / `in_progress` / `completed` |
| `scores_e` / `scores_s` / `scores_g` | float \| None | Score de chaque pilier (0-100) |
| `overall_score` | float \| None | Score global pondéré |
| `criteria_scores` | JSONB | 30 critères : `{criterion_id: {score, notes, evidence}}` |
| `recommendations` | JSONB | Recommandations LLM |
| `benchmark` | JSONB | Position vs benchmark sectoriel |

**Logique de scoring** : 30 critères répartis sur E (environnement), S (social), G (gouvernance), pondérés par secteur (fichier `modules/esg/weights.py`). Fallback si secteur inconnu.

## 6. Empreinte carbone

### `carbon_assessments` — `models/carbon.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `year` | int | Contrainte unique `(user_id, year)` |
| `status` | `CarbonStatusEnum` | `draft` / `in_progress` / `completed` |
| `scope1_tco2` / `scope2_tco2` / `scope3_tco2` | float \| None | Émissions par scope |
| `total_tco2` | float \| None | Somme |
| `reduction_targets` | JSONB | Objectifs de réduction |
| `benchmark` | JSONB | Comparaison secteur (9 secteurs) |

### `carbon_emission_entries`

Chaque entrée correspond à une ligne d'activité (ex. "3000 L gasoil/an" → X tCO2e).

| Colonne | Type | Notes |
|---|---|---|
| `assessment_id` | UUID FK | Cascade delete |
| `category` | str | `energy` / `transport` / `waste` / `industrial` / `agriculture` |
| `subcategory` | str | Ex. `diesel`, `electricity`, `paper_waste` |
| `quantity` | float | Quantité brute |
| `unit` | str | Unité (L, kWh, kg, ...) |
| `emission_factor` | float | Facteur appliqué (kgCO2e/unit) |
| `co2_tonnes` | float | Résultat calculé |

Facteurs d'émission : `modules/carbon/emission_factors.py` (adaptés Afrique de l'Ouest). Benchmarks : `modules/carbon/benchmarks.py`.

## 7. Financement vert

### `funds` — `models/financing.py`

Catalogue des fonds de financement vert (GCF, FEM, BOAD, BAD, SUNREF, FNDE, ...). 12 fonds réels seedés au départ.

| Colonne | Type | Notes |
|---|---|---|
| `name` | str | Nom public |
| `fund_type` | `FundType` enum | Multilatéral, bilatéral, national, privé, impact |
| `funding_source` | str | Bailleur |
| `amount_min_fcfa` / `amount_max_fcfa` | int | Fourchette |
| `eligible_sectors` | JSONB | Array de secteurs |
| `eligible_countries` | JSONB | Array de codes pays |
| `access_type` | `AccessType` enum | `direct` / `intermediary` / `both` |
| `status` | `FundStatus` enum | `open` / `closed` / `upcoming` |
| `description` | text | |
| `requirements` | JSONB | Documents, critères |
| `embedding` | `Vector(1536)` | pgvector pour matching sémantique |

### `intermediaries`

14 intermédiaires seedés (banques, IMF, agences). Liaison N-N via `fund_intermediaries`.

| Colonne | Type |
|---|---|
| `name` | str |
| `type` | `IntermediaryType` enum |
| `country` | str |
| `contact_email` / `contact_phone` / `website` | str |
| `services` | JSONB |

### `fund_intermediaries` (table d'association)

| Colonne | Type |
|---|---|
| `fund_id` | UUID FK |
| `intermediary_id` | UUID FK |
| `is_primary` | bool |

### `fund_matches`

Matching calculé entre un `User` et un `Fund` via scoring multi-critères (secteur, taille entreprise, ESG, localisation, documents disponibles).

| Colonne | Type | Notes |
|---|---|---|
| `user_id` / `fund_id` | UUID FK | |
| `score` | float | 0-100 |
| `status` | str | `suggested` / `interested` / `preparing` / `applied` / `rejected` |
| `selected_intermediary_id` | UUID FK \| None | |
| `preparation_data` | JSONB | Feuille de préparation |

### `financing_chunks`

Chunks vectoriels des descriptions de fonds (RAG pgvector pour recherche sémantique).

## 8. Dossier de candidature (Applications)

### `fund_applications` — `models/application.py`

Workflow : `draft` → `submitted` → `under_review` → `accepted` / `rejected`.

| Colonne | Type | Notes |
|---|---|---|
| `user_id` / `fund_id` | UUID FK | |
| `status` | `ApplicationStatus` enum | |
| `sections` | JSONB | `{section_key: {content, generated_at, generated_by}}` |
| `target_type` | `TargetType` enum | Direct ou intermédiaire |
| `intermediary_id` | UUID FK \| None | |
| `financing_simulation` | JSONB \| None | Montant, durée, taux |
| `submitted_at` | timestamp \| None | |

## 9. Scoring crédit vert

### `credit_scores` — `models/credit.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `score` | int | 0-100 |
| `confidence_label` | str | `low` / `medium` / `high` |
| `categories_breakdown` | JSONB | `{solvency, impact, data_quality, behavior}` |
| `risk_factors` | JSONB | Array d'alertes |
| `recommendations` | JSONB | Actions d'amélioration |
| `certificate_url` | str \| None | PDF généré |
| `expiry_date` | date | Date de renouvellement |

### `credit_data_points`

Donnée individuelle non-conventionnelle (Mobile Money, photo, document, profil).

| Colonne | Type |
|---|---|
| `credit_score_id` | UUID FK |
| `category` | str |
| `source_type` | str |
| `value` | JSONB |
| `weight` | float |

## 10. Plan d'action et gamification

### `action_plans` — `models/action_plan.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | 1-N |
| `horizon` | str | `6_months` / `12_months` / `24_months` |
| `generated_at` | timestamp | |
| `summary` | text | Résumé LLM |
| `overall_progress` | float | 0-100, recalculé dynamiquement |

### `action_items`

| Colonne | Type | Notes |
|---|---|---|
| `plan_id` | UUID FK | Cascade |
| `category` | str | `environment` / `social` / `governance` / `financing` / `carbon` / `intermediary_contact` |
| `title` / `description` | str / text | |
| `priority` | str | `high` / `medium` / `low` |
| `status` | str | `todo` / `in_progress` / `done` / `cancelled` |
| `target_date` | date \| None | |
| `intermediary_snapshot` | JSONB \| None | Coordonnées snapshot si catégorie `intermediary_contact` |

### `reminders`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `reminder_type` | str | `action_due` / `assessment_renewal` / `fund_deadline` / `intermediary_followup` / `custom` |
| `due_date` | timestamp | |
| `title` / `body` | str / text | |
| `notified` | bool | |

### `badges`

5 badges automatiques : `first_carbon`, `esg_above_50`, `first_application`, `first_intermediary_contact`, `full_journey`.

| Colonne | Type |
|---|---|
| `user_id` | UUID FK |
| `badge_type` | str |
| `awarded_at` | timestamp |
| `metadata` | JSONB |

## 11. Rapports PDF

### `reports` — `models/report.py`

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `type` | str | `esg` / `carbon` / `credit` |
| `generated_at` | timestamp | |
| `content_url` | str | Chemin PDF sur `/uploads/reports/` |
| `charts` | JSONB | Métadonnées des graphiques |

## 12. Observabilité du LLM

### `tool_call_logs` — `models/tool_call_log.py`

Journal complet des appels aux tools LangChain (feature 012).

| Colonne | Type | Notes |
|---|---|---|
| `user_id` | UUID FK | |
| `conversation_id` | UUID FK | |
| `tool_name` | str | |
| `input_args` | JSONB | Arguments fournis au tool |
| `output` | JSONB \| None | Retour |
| `status` | str | `success` / `error` / `retry` |
| `error_message` | text \| None | |
| `duration_ms` | int \| None | |
| `timestamp` | timestamp | |

## 13. Questions interactives (feature 018)

### `interactive_questions` — `models/interactive_question.py`

Table satellite, pas de modification des tables existantes.

| Colonne | Type | Notes |
|---|---|---|
| `user_id` / `conversation_id` / `message_id` | UUID FK | |
| `type` | `InteractiveQuestionType` enum | `qcu` / `qcm` / `qcu_justification` / `qcm_justification` |
| `state` | `InteractiveQuestionState` enum | `pending` / `answered` / `abandoned` / `expired` |
| `question_text` | str | |
| `options` | JSONB | `[{id, label, description?}]` |
| `answer_data` | JSONB \| None | Réponse + justification (max 400 car) |
| `answered_at` / `abandoned_at` / `expired_at` | timestamp \| None | |

**Invariant** : une seule question `pending` par conversation à la fois ; les précédentes sont marquées `expired` avant insertion.

## 14. Migrations Alembic (13)

Dossier `backend/alembic/versions/` :

| Migration | Feature |
|---|---|
| `001_create_users.py` | Users, conversations, messages |
| `2b24b1676e59_*` | CompanyProfile + country detection |
| `163318558259_*` | Documents + analyses + chunks pgvector |
| `005_add_esg_assessments.py` | ESG |
| `006_add_reports_table.py` | Rapports |
| `007_add_carbon_tables.py` | Carbone |
| `008_add_financing_tables.py` | Financement + chunks RAG |
| `68cd43ef0091_*` | Credit scoring |
| `73d72f6ebd8f_*` | Fund applications |
| `5b7f090f1dcc_*` | Action plan + reminders + badges |
| `54432e29b7f3_*` | Tool call logs |
| `018_create_interactive_questions.py` | Questions interactives |

Commande : `alembic upgrade head` (dans le venv) ou `make migrate` (via Docker Compose).

## 15. Index et contraintes clés

- `users.email` — unique + index
- `conversations.user_id + updated_at` — index pour liste paginée
- `carbon_assessments(user_id, year)` — contrainte unique
- `documents.user_id + created_at` — index
- `document_chunks.embedding` — index HNSW pgvector (cosine)
- `financing_chunks.embedding` — index HNSW pgvector
- `interactive_questions.conversation_id + state` — index pour détecter le `pending`

## 16. Relations globales (vue d'ensemble)

```
User (1) ─┬─ (1) CompanyProfile
          ├─ (N) Conversation ─ (N) Message
          │                    └ (N) InteractiveQuestion
          ├─ (N) Document ─ (1) DocumentAnalysis
          │               └ (N) DocumentChunk
          ├─ (N) ESGAssessment
          ├─ (N) CarbonAssessment ─ (N) CarbonEmissionEntry
          ├─ (N) FundMatch ─ (N:1) Fund ─ (N:N via fund_intermediaries) ─ Intermediary
          ├─ (N) FundApplication
          ├─ (1) CreditScore ─ (N) CreditDataPoint
          ├─ (N) ActionPlan ─ (N) ActionItem
          ├─ (N) Reminder
          ├─ (N) Badge
          ├─ (N) Report
          └─ (N) ToolCallLog
```
