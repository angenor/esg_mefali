# Story 10.1 : Migrations Alembic 020–027 (socle schéma Extension 5 clusters)

Status: done

> **Contexte** : première story Epic 10 Fondations Phase 0 (BLOQUANT Epic 11–20). Socle schéma PostgreSQL pour les 3 nouveaux modules (`projects`, `maturity`, `admin_catalogue`), l'architecture ESG 3 couches (D3), le cube 4D (D4), le moteur livrables (D5), RLS 4 tables (D7), NFR-SOURCE-TRACKING (CCC-6), audit trail catalogue (D6) et micro-Outbox MVP (D11).
>
> **Dépendance** : Story 9.7 (instrumentation `with_retry` + `log_tool_call`) — **done** (merged `06bcf99`).
> **Bloque** : Stories 10.2–10.21 de l'Epic 10 + totalité des Epic 11–20.

---

## Story

**As a** Équipe Mefali (DX/SRE/Backend),
**I want** livrer 8 migrations Alembic séquentielles `020` → `027` qui créent le schéma complet Extension 5 clusters (tables Cluster A `projects`, Cluster A' `maturity`, Cluster B ESG 3 couches, Cluster C moteur livrables, Cluster D audit catalogue, + transverses RLS / SOURCE-TRACKING / micro-Outbox),
**So that** les 20 stories restantes de l'Epic 10 et tous les Epic 11+ disposent d'un socle BDD versionné, réversible, testé, aligné sur les décisions architecturales D1/D3/D4/D5/D6/D7/D11 et les NFR Phase 0 (NFR12, NFR27, NFR28, NFR31, NFR62).

---

## Acceptance Criteria

### AC1 — Les 8 migrations 020–027 existent, s'enchaînent et passent `alembic upgrade head` depuis `019_manual_edits`

**Given** le repository dans l'état `019_manual_edits (head)` (`backend/alembic/versions/` + `alembic current = 019_manual_edits`),
**When** un développeur exécute `alembic upgrade head` (ou `alembic upgrade 027`),
**Then** toutes les migrations 020 → 027 s'appliquent sans erreur dans l'ordre séquentiel
**And** `alembic current` retourne `027` (dernier head),
**And** `alembic history` affiche la chaîne linéaire `019_manual_edits ← 020 ← 021 ← 022 ← 023 ← 024 ← 025 ← 026 ← 027`,
**And** aucun warning Alembic `Multiple head revisions` n'est émis,
**And** les migrations existantes (001–019) et leurs tables (`users`, `companies`, `company_profiles`, `documents`, `funds`, `intermediaries`, `fund_applications` legacy, etc.) ne sont pas altérées de façon régressive (données conservées, colonnes ajoutées non-nullables avec `server_default` pour rétrocompatibilité).

### AC2 — Chaque migration a un `upgrade()` ET un `downgrade()` fonctionnels (NFR32 rollback trimestriel)

**Given** une base PostgreSQL 16 avec le schéma à `019_manual_edits`,
**When** un développeur exécute `alembic upgrade head && alembic downgrade 019_manual_edits`,
**Then** toutes les 8 migrations se déroulent à l'upgrade puis redescendent entièrement à l'inverse sans erreur,
**And** la commande finale `alembic current` retourne `019_manual_edits`,
**And** `pg_dump --schema-only` AVANT et APRÈS le round-trip est strictement équivalent (normalisation des commentaires/ordre acceptée, cf. `scripts/diff_schema.sh`),
**And** les tests d'intégration existants (18 specs livrées) restent verts (baseline : 1244 tests post-Story 9.7).

### AC3 — Conventions de nommage + documentation en-tête (NFR62, CQ-8)

**Given** chaque fichier de migration `NNN_<description>.py`,
**When** auditée par revue de code,
**Then** son docstring d'en-tête contient :
  - Le numéro de revision et son parent (`down_revision`),
  - Le numéro de story (`Story 10.1`) et la date,
  - La ou les décision(s) architecturale(s) supportée(s) (ex. « D1 modèle `Company × Project` N:N », « D3 ESG 3 couches », « D7 RLS 4 tables », « D11 micro-Outbox »),
  - Les `fr_covered` / `nfr_covered` impactés (support infra, pas livraison FR directe),
**And** le fichier suit la convention de nommage `NNN_<verbe_action>_<objet>.py` en snake_case (`020_create_projects_schema.py`, `024_enable_rls_on_sensitive_tables.py`, etc. — voir Tableau A ci-dessous).

### AC4 — Type UUID partout + cohérence avec le schéma existant

**Given** chaque nouvelle table créée,
**When** inspectée via `\d <table>` PostgreSQL ou via `sa.inspect(engine)`,
**Then** la PK est de type `UUID` avec `server_default=sa.text("gen_random_uuid()")` (conformité avec convention existante spec 001–018),
**And** toutes les FK pointant vers une table existante utilisent `sa.UUID()` (pas `Integer`, pas `String(36)`),
**And** les colonnes `created_at` / `updated_at` sont `TIMESTAMPTZ` avec `server_default=sa.text("now()")`,
**And** tous les JSONB cross-dialecte utilisent `sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")` (pattern spec 018 — tests SQLite in-memory supportés).

### AC5 — RLS actif sur 4 tables sensibles avec `admin_access_audit` (D7)

**Given** la migration 024 appliquée,
**When** un test exécute `SET ROLE app_user; SET app.current_user_id = '<user_A>'; SELECT * FROM companies WHERE id = '<company_B>'` (company_B rattachée à user_B),
**Then** la query retourne **0 ligne** (RLS filtre, pas d'erreur 500),
**And** le pattern s'applique aux 4 tables protégées : `companies`, `fund_applications`, `facts`, `documents`,
**And** un `admin_mefali` ou `admin_super` qui fait `SET ROLE admin_bypass; SELECT ...` voit toutes les lignes **ET** une entrée est insérée dans `admin_access_audit(admin_user_id, admin_role, table_accessed, operation, record_ids, accessed_at, reason)` (écriture via SQLAlchemy event listener livré Story 10.5, mais la table elle-même est créée ici par 024),
**And** la perte de performance mesurée sur `SELECT` cross-tenant `WHERE company_id = ?` est **≤ 10 %** du baseline pré-RLS (enforcement Story 10.5, infra créée ici).

### AC6 — NFR-SOURCE-TRACKING + CHECK constraints (CCC-6, migration 025)

**Given** les tables catalogue (`funds`, `intermediaries`, `referentials`, `criteria`, `packs`, `admin_maturity_requirements`, `document_templates`, `reusable_sections`),
**When** la migration 025 est appliquée,
**Then** chacune reçoit les 3 colonnes `source_url TEXT`, `source_accessed_at TIMESTAMPTZ`, `source_version TEXT` (nullable au niveau colonne pour retro-compatibilité),
**And** une contrainte `CHECK` applicative par table exige que si la colonne de workflow publication (`workflow_state` / `is_published`) = `published`, les 3 colonnes source sont **NOT NULL** (CCC-6 — enforcement BDD, CI HTTP 200 Story 10.11),
**And** un backfill doux est prévu : les lignes déjà `published` en base reçoivent `source_version = 'pre-sourcing-2026-04'` + `source_url = 'legacy://non-sourced'` pour ne pas bloquer `alembic upgrade head` (documenté dans l'en-tête migration).

### AC7 — FK, indexes et contraintes structurelles (Decision 1 cumul rôles, Décision 4 cube GIN, Décision 11 micro-Outbox)

**Given** chaque migration,
**When** auditée via `pytest backend/tests/test_migrations/test_schema_structure.py`,
**Then** les contraintes critiques suivantes sont présentes :
  - **`project_memberships`** : `UNIQUE (project_id, company_id, role)` (D1 cumul de rôles — une Company peut être simultanément `porteur_principal` + `beneficiaire` mais pas deux fois la même combinaison),
  - **`projects`** : index B-tree sur `(company_id, status)` + FK `company_id → companies.id ON DELETE CASCADE`,
  - **`facts` + `fact_versions`** : FK + index sur `(company_id, criterion_id)` + `(fact_id, version_number)` (audit trail FR19),
  - **`referential_verdicts`** : index composite `(fund_application_id, criterion_id, referential_id)` + colonne `invalidated_at TIMESTAMPTZ NULL` (D3 invalidation event-driven),
  - **`mv_fund_matching_cube`** (vue matérialisée, PostgreSQL-only) : indexes GIN sur colonnes `sectors_eligible`, `countries_eligible` (D4 cube 4D performance SC-T3 ≤ 2 s p95),
  - **`domain_events`** (migration 027) : indexes composites `(status, created_at) WHERE processed_at IS NULL AND retry_count < 5` (partiel, worker batch) ET `(aggregate_type, aggregate_id)`, CHECK `retry_count <= 5`,
  - **`prefill_drafts`** (migration 027) : FK `user_id → users.id ON DELETE CASCADE` + index sur `expires_at` (worker nettoyage 10.10),
  - **`admin_catalogue_audit_trail`** (migration 026) : colonnes `(id, actor_user_id, entity_type, entity_id, action, workflow_state_before, workflow_state_after, changes_before JSONB, changes_after JSONB, workflow_level ENUM{N1,N2,N3}, ts TIMESTAMPTZ)` + index sur `(entity_type, entity_id, ts)` + rétention 5 ans documentée.

### AC8 — Tests d'intégration CRUD par table (SQLAlchemy async, coverage ≥ 80 %)

**Given** les modèles SQLAlchemy associés (livrés en parallèle dans `app/modules/<module>/models.py` par les stories 10.2, 10.3, 10.4 — dans cette story uniquement les migrations),
**When** `pytest backend/tests/test_migrations/` + `pytest backend/tests/test_schema_structure/` exécuté,
**Then** chaque nouvelle table supporte un cycle `INSERT → SELECT → UPDATE → DELETE` via `AsyncSession` sur SQLite in-memory (fixture `conftest.py` existante),
**And** les features PostgreSQL-only (RLS, vue matérialisée, indexes GIN, indexes partiels, `gen_random_uuid`) sont testées via fixture `pytest.mark.postgres` (marker existant, skippé en SQLite) sur l'instance Docker `TEST_DATABASE_URL=postgresql+asyncpg://...`,
**And** coverage Alembic + modèles rattachés ≥ **80 %** (NFR60 CI gate).

### AC9 — Documentation `docs/CODEMAPS/data-model-extension.md`

**Given** les 8 migrations appliquées,
**When** la documentation est consultée,
**Then** le fichier `docs/CODEMAPS/data-model-extension.md` **existe** et contient :
  - Un diagramme **Mermaid `erDiagram`** listant toutes les nouvelles tables avec leurs FK (Cluster A/A'/B/C/D/transverses colorés distinctement),
  - Pour chaque table : nom, liste des colonnes avec type + nullable + default, liste des indexes, liste des contraintes (UNIQUE, CHECK, FK),
  - La **chaîne des migrations** 020–027 avec le bénéfice de chacune (alignement décision architecturale),
  - Les **tables legacy étendues** (`companies`, `users`, `fund_applications`, `funds`, `intermediaries`, `documents`) + colonnes ajoutées par 020–027 (CRITIQUE — voir conflit de schéma Technical Design §Conflits),
  - Un lien vers chaque décision architecturale (`_bmad-output/planning-artifacts/architecture.md#décision-N`) pour traçabilité CQ-8.

### AC10 — Reversibilité complète testée en CI (round-trip `upgrade base → head → base`)

**Given** une base PostgreSQL de test vierge (container Docker `postgres:16`),
**When** le job CI `.github/workflows/test-migrations-roundtrip.yml` s'exécute,
**Then** la séquence `alembic downgrade base && alembic upgrade head && alembic downgrade 019_manual_edits && alembic upgrade head` réussit sans erreur,
**And** un `pg_dump --schema-only` post-round-trip est identique au `pg_dump --schema-only` initial post-upgrade (tolérance ordre + commentaires),
**And** le test est ajouté au pipeline CI GitHub Actions comme **gate de merge** pour toute PR touchant `backend/alembic/versions/`.

---

## Tasks / Subtasks

### Phase 1 — Migrations Cluster A / A' (Decision 1 + Cluster A')

- [x] **Task 1 — Migration 020 `create_projects_schema.py`** (AC: 1, 3, 4, 7) — Support D1 Cluster A
  - [x] 1.1 Créer tables `companies` (nouvelle), `projects`, `project_memberships`, `project_role_permissions`, `project_snapshots`, `company_projections`, `beneficiary_profiles`
  - [x] 1.2 **ALTER `fund_applications` existant** : +`project_id UUID FK NOT NULL` (Q2), +`version_number INT`, +`snapshot_id UUID FK`, +`submitted_hash VARCHAR(64)`
  - [x] 1.3 Backfill piloté Q2 : companies + projects "legacy" par `user_id` distinct avant `ALTER SET NOT NULL` ; rollback supporté dans `downgrade()`
  - [x] 1.4 Contrainte `UNIQUE (project_id, company_id, role)` sur `project_memberships` (D1 cumul)
  - [x] 1.5 Index B-tree `(company_id, status)` sur `projects`
  - [x] 1.6 `downgrade()` : DROP tables en ordre inverse FK + DROP colonnes ajoutées à `fund_applications`

- [x] **Task 2 — Migration 021 `create_maturity_schema.py`** (AC: 1, 3, 4, 6, 7) — Support Cluster A' FR11-FR16
  - [x] 2.1 Créer tables `admin_maturity_levels` (catalogue N1, 5 niveaux gradués), `formalization_plans`, `admin_maturity_requirements`
  - [x] 2.2 Contrainte `UNIQUE (country, level_id)` sur `admin_maturity_requirements` (country-driven, pas hardcodé)
  - [x] 2.3 Colonnes `source_url`, `source_accessed_at`, `source_version` ajoutées (enforcement CHECK activé par 025)
  - [x] 2.4 FK `formalization_plans.company_id → companies.id ON DELETE CASCADE`
  - [x] 2.5 `downgrade()` DROP tables ordre inverse

### Phase 2 — Migrations Cluster B / C (ESG 3 couches + moteur livrables)

- [x] **Task 3 — Migration 022 `create_esg_3_layers.py`** (AC: 1, 3, 4, 7) — Support D3 FR17-FR26 + D4 cube 4D
  - [x] 3.1 Couche 1 **Faits** : `facts`, `fact_versions` (UNIQUE `(fact_id, version_number)`)
  - [x] 3.2 Couche 2 **Critères & DSL borné** : `criteria`, `criterion_derivation_rules` (CHECK `rule_type IN (threshold/boolean_expression/aggregate/qualitative_check)`, validation Pydantic côté app)
  - [x] 3.3 Couche 3 **Verdicts** : `referential_verdicts` (+`invalidated_at TIMESTAMPTZ NULL` D3.2), `referentials`, `referential_versions`, `referential_migrations`, `packs`, `pack_criteria` (+`fund_specific_overlay_rule JSONB` D2)
  - [x] 3.4 Index composite `(fund_application_id, criterion_id, referential_id)` sur `referential_verdicts`
  - [x] 3.5 **Vue matérialisée `mv_fund_matching_cube`** (PG-only) + GIN indexes sur `sectors_eligible` + `countries_eligible` (load test reporté Story 20.4 — Q4)
  - [x] 3.6 `downgrade()` DROP MATERIALIZED VIEW puis DROP tables en ordre FK inverse

- [x] **Task 4 — Migration 023 `create_deliverables_engine.py`** (AC: 1, 3, 4, 7) — Support D5 FR36-FR44
  - [x] 4.1 Pyramide Template → Section → Block : `document_templates`, `template_sections` (PK composite), `reusable_sections`, `reusable_section_prompt_versions` (PK composite `(section_id, version)`), `atomic_blocks`
  - [x] 4.2 `fund_application_generation_logs` (FR57)
  - [x] 4.3 CHECK FR44 NO BYPASS : `(code NOT IN ('sges_beta','esia','stakeholder_engagement_plan')) OR human_review_required = true`
  - [x] 4.4 FK + index `(fund_application_id, generated_at)` sur `fund_application_generation_logs`

### Phase 3 — Migrations transverses sécurité / audit / Outbox

- [x] **Task 5 — Migration 024 `enable_rls_on_sensitive_tables.py`** (AC: 1, 3, 4, 5) — Support D7 NFR12
  - [x] 5.1 Table `admin_access_audit` (10 colonnes D7 complètes)
  - [x] 5.2 RLS + policy `tenant_isolation` sur `companies` (via `owner_user_id`)
  - [x] 5.3 RLS + policy sur `fund_applications` (via `user_id`)
  - [x] 5.4 RLS + policies sur `facts` (via `company_id`) et `documents` (via `user_id`)
  - [x] 5.5 Bypass admin intégré dans USING : `current_setting('app.user_role') IN ('admin_mefali','admin_super')` — pas de policy séparée
  - [x] 5.6 `downgrade()` : DISABLE RLS + DROP policies + DROP table `admin_access_audit`
  - [x] 5.7 **Skip SQLite** : `if dialect.name != 'postgresql': return` pour upgrade ET downgrade

- [x] **Task 6 — Migration 025 `add_source_tracking_constraints.py`** (AC: 1, 3, 6) — Support CCC-6
  - [x] 6.1 Ajouter colonnes source sur `funds`, `intermediaries` (tables legacy — les nouvelles les ont déjà)
  - [x] 6.2 Backfill doux : UPDATE `source_version='pre-sourcing-2026-04'` + `source_url='legacy://non-sourced'` pour lignes legacy publiées
  - [x] 6.3 Table `sources` (url UNIQUE, source_type ENUM, last_verified_at, verified_by_admin_id FK, http_status_last_check)
  - [x] 6.4 CHECK `ck_<table>_source_if_published` `NOT VALID` puis `VALIDATE CONSTRAINT` sur 9 tables catalogue
  - [x] 6.5 `downgrade()` : DROP CHECK + DROP colonnes + DROP table `sources` + DROP TYPE `source_type_enum`

- [x] **Task 7 — Migration 026 `create_admin_catalogue_audit_trail.py`** (AC: 1, 3, 4, 7) — Support D6 FR64
  - [x] 7.1 Table `admin_catalogue_audit_trail` avec 12 colonnes + 2 enums (`catalogue_action_enum`, `workflow_level_enum`)
  - [x] 7.2 Index `(entity_type, entity_id, ts)` + `(actor_user_id, ts)` + `(workflow_level, ts)`
  - [x] 7.3 Rétention 5 ans documentée (purge Story 10.10)
  - [x] 7.4 `downgrade()` DROP indexes + DROP table + DROP enums

- [x] **Task 8 — Migration 027 `create_outbox_and_prefill_drafts.py`** (AC: 1, 3, 4, 7) — Support D11 + Story 16.5
  - [x] 8.1 Table `domain_events` (D11) avec CHECK `retry_count <= 5`
  - [x] 8.2 Index **partiel PostgreSQL** `idx_domain_events_pending` WHERE `processed_at IS NULL AND retry_count < 5`
  - [x] 8.3 Index secondaire `(aggregate_type, aggregate_id)`
  - [x] 8.4 Table `prefill_drafts` (Story 16.5) avec FK `user_id ON DELETE CASCADE` + `expires_at NOT NULL`
  - [x] 8.5 Index `(user_id, expires_at)` — pas de partial (nettoyage worker consomme via `expires_at < now()`)
  - [x] 8.6 `downgrade()` DROP tables ordre inverse

**Note Q1 arbitrage** : cleanup feature flag `ENABLE_PROJECT_MODEL` déplacé vers Story 20.1 (retrait code applicatif, pas de migration).

### Phase 4 — Tests + documentation + CI

- [x] **Task 9 — Tests d'intégration migrations** (AC: 2, 5, 8, 10)
  - [x] 9.1 `test_migration_roundtrip.py` — 4 tests (chaîne linéaire, upgrade head, round-trip complet, downgrade par étape)
  - [x] 9.2 `test_schema_structure.py` — 14 tests (docstrings, revision IDs, UUID PK, UNIQUE triplet, indexes composites, CHECK retry cap, partial index, GIN cube 4D, source tracking, down_revision chain)
  - [x] 9.3 `test_data_integrity.py` — 6 tests CRUD cycle (companies, projects, domain_events, prefill_drafts, retry cap rejection, project_memberships cumul rôles) sur PostgreSQL (SQLite incompatible avec migration 001 pgvector — documenté)
  - [x] 9.4 `test_rls_skeleton.py` + `test_admin_access_audit_table.py` — 6 tests RLS réel avec `SET LOCAL ROLE app_user` (car postgres est SUPERUSER et bypass RLS) : relrowsecurity, policies, tenant isolation bloque autre user, admin_mefali bypass voit tout
  - [x] 9.5 **31 tests PostgreSQL + 5 tests doc = 36 nouveaux tests** (baseline 1244 → 1280 ; cible 1271 atteinte)

- [x] **Task 10 — Documentation + CI gate** (AC: 3, 9, 10)
  - [x] 10.1 `docs/CODEMAPS/data-model-extension.md` avec Mermaid `erDiagram` + tables par cluster + liens D1/D3/D4/D5/D6/D7/D11
  - [x] 10.2 `docs/runbooks/README.md` : ajout Runbook 6 "Rollback migration Alembic (NFR32 trimestriel)"
  - [x] 10.3 `backend/scripts/validate_schema.py` : alembic upgrade head + compare Base.metadata vs introspection PostgreSQL + allowlist Schema-only tables Story 10.1
  - [x] 10.4 `.github/workflows/test-migrations-roundtrip.yml` : PostgreSQL 16 container, triggered sur `backend/alembic/versions/**` + `backend/tests/test_migrations/**`
  - [x] 10.5 `backend/alembic/README.md` avec conventions nommage, en-tête docstring, features PG-only, round-trip local, rollback trimestriel

---

## Dev Notes

### Contexte architectural (CRITIQUE — à lire avant de coder)

Cette story est le **socle** de l'Extension 5 clusters. Chaque migration supporte une ou plusieurs décisions architecturales non-négociables :

| Migration | Décision(s) | Enjeu |
|-----------|-------------|-------|
| 020 | **D1** (Company × Project N:N + cumul rôles) | Feature flag `ENABLE_PROJECT_MODEL` (Clarif. 5) protège la bascule — ALTER `fund_applications` existant sans casser specs 001-018 |
| 021 | Cluster A' (maturité graduée FR11-FR16) | `admin_maturity_requirements` country-data-driven (pas de string hardcodé Sénégal/Côte d'Ivoire) |
| 022 | **D3** (ESG 3 couches + DSL borné anti-RCE) + **D4** (cube 4D) | DSL **pas d'eval** — validation Pydantic discriminator stricte côté app ; vue matérialisée `mv_fund_matching_cube` PostgreSQL-only |
| 023 | **D5** (moteur livrables pyramide + prompt versioning) | Prompt versioning **obligatoire** pour audit FR57 — sans ça, impossible de rejouer pourquoi un SGES a été produit 2 ans après |
| 024 | **D7** (RLS 4 tables + admin_access_audit) | NFR12 défense en profondeur — PostgreSQL-only, skip SQLite avec `dialect.name == 'postgresql'` |
| 025 | **CCC-6** (NFR-SOURCE-TRACKING) | 3 colonnes `source_url`/`source_accessed_at`/`source_version` + CHECK NOT NULL si published — backfill doux pour rétrocompatibilité |
| 026 | **D6** (audit trail catalogue N1/N2/N3) | FR64 rétention 5 ans — audit trail immuable (write-only + read admin_super) |
| 027 | **D11** (micro-Outbox `domain_events`) + Story 16.5 (`prefill_drafts` fallback deep-link) | Worker APScheduler 30 s consomme `domain_events` via partial index — fondation event-driven |

### Patterns Alembic à respecter (ADN existant specs 001-018)

- **En-tête docstring** : `"""<description courte>\n\nRevision ID: NNN_verbose\nRevises: <parent>\nCreate Date: YYYY-MM-DD\n\nStory 10.1 — <décision(s) supportée(s)>\nFR covered: [], NFR covered: [NFR..., NFR...]\n"""` (cf. `018_create_interactive_questions.py` ligne 1-6 et `019_add_manually_edited_fields_to_company_profiles.py` ligne 1-9 pour référence)
- **Revision ID verbose** : utiliser `'020_projects'`, `'021_maturity'`, `'022_esg_3layers'`, `'023_deliverables'`, `'024_rls_audit'`, `'025_source_tracking'`, `'026_catalogue_audit'`, `'027_outbox_prefill'` (cohérent avec `018_interactive`, `019_manual_edits`)
- **Cross-dialect JSONB** : `sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite")` (cf. `019_manual_edits.py:29`)
- **Timestamps** : `sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)` (cf. `73d72f6ebd8f.py:35`)
- **UUID PK** : `sa.Column('id', sa.UUID(), nullable=False)` + `sa.PrimaryKeyConstraint('id')` (cf. `73d72f6ebd8f.py:34,41`) — note : `gen_random_uuid()` server_default PostgreSQL, SQLite utilise Python-side default géré par SQLAlchemy
- **Indexes partiels PostgreSQL** : `op.create_index('idx_name', 'table', ['col'], postgresql_where=sa.text("..."))` (cf. `018_interactive.py:83-99`)
- **FK cascades** : `sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')` (cf. `73d72f6ebd8f.py:40`)
- **Enums** : préférer `sa.Enum(..., name='xxx_enum', create_constraint=True)` (cf. `73d72f6ebd8f.py:27`) ; pour enums réutilisés cross-migration, `create_type=False` sur instances secondaires (cf. `008_financing.py:73`)

### Conflits de schéma à gérer (DISASTER PREVENTION)

**Tables déjà existantes** qui seront étendues (pas re-créées) par les nouvelles migrations :

| Table legacy | Migration légacy | Nouvelle migration impactante | Opération |
|--------------|-----------------|-------------------------------|-----------|
| `fund_applications` | `73d72f6ebd8f` (après `008_financing`) | **020** (Cluster A) | **ALTER** : +`project_id`, +`version_number`, +`snapshot_id`, +`submitted_hash` |
| `funds` | `008_financing` | **025** (SOURCE-TRACKING) | **ALTER** : +`source_url`/`source_accessed_at`/`source_version` (si absent) |
| `intermediaries` | `008_financing` | **025** | **ALTER** : +3 colonnes source si absentes |
| `documents` | `163318558259_add_documents_tables` | **024** (RLS) | **ALTER** : activation RLS policy (pas de nouvelles colonnes) |
| `companies` | `2b24b1676e59_add_company_profiles_table` (vérifier) | **024** | activation RLS policy |
| `fund_matches` | `008_financing` | — | conservé tel quel (cube 4D utilise `mv_fund_matching_cube` à part) |

**⚠️ Piège `fund_applications`** : le modèle existant (`73d72f6ebd8f.py`) n'a pas de `project_id`. Le Cluster A (D1) introduit la notion `Project` distincte de `FundApplication`. La migration 020 doit :
1. Ajouter `project_id` avec backfill `gen_random_uuid()` (placeholder temporaire par ligne existante),
2. Documenter que la consolidation réelle (rattacher `FundApplication` à un vrai `Project`) est faite par Story 20.1 (switch `ENABLE_PROJECT_MODEL=true` + migration de données),
3. **NE PAS** rendre `project_id` NOT NULL tant que Story 20.1 n'a pas tourné — laisser nullable puis CHECK constraint ajoutée par 027_cleanup (alternative : NOT NULL dès maintenant + backfill UUID aléatoire, à arbitrer avec PM — voir Questions Q2).

### RLS PostgreSQL — pattern canonique (AC5, migration 024)

```sql
-- Migration 024 upgrade() pseudo-SQL (écrit en SQLAlchemy op.execute)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies FORCE ROW LEVEL SECURITY;  -- s'applique aussi au propriétaire de la table

CREATE POLICY tenant_isolation ON companies
  FOR ALL
  USING (
    owner_user_id = current_setting('app.current_user_id', true)::uuid
    OR current_setting('app.user_role', true) IN ('admin_mefali', 'admin_super')
  );
```

Pour SQLite : **skip intégral** via `if op.get_bind().dialect.name == 'postgresql':` — les tests unitaires SQLite ne testent pas RLS (testé uniquement en intégration Docker `postgres:16`).

**Convention session** : chaque requête applicative doit `SET LOCAL app.current_user_id = '<uuid>'` via `get_tenant_scoped_session(current_user)` (middleware déjà prévu — Story 10.5 pour l'event listener SQLAlchemy qui loggue les escapes admin dans `admin_access_audit`).

### DSL borné — anti-RCE (migration 022, colonne `criterion_derivation_rules.rule_json`)

**Aucune évaluation de code arbitraire** (`eval`, `exec`, `sqlparse.execute`) n'est acceptée. Le JSONB de `rule_json` est validé par Pydantic discriminator (Literal["threshold","boolean_expression","aggregate","qualitative_check"]) côté **application** (Story 13.x). Migration 022 crée juste la colonne + contrainte CHECK basique (`rule_type IN (...)` si possible).

### Test pattern — migrations avec SQLite in-memory

`conftest.py:16-23` utilise `sqlite+aiosqlite:///file::memory:?cache=shared&uri=true` avec `Base.metadata.create_all` (pas via Alembic). Pour tester les migrations Alembic réelles, créer un fixture dédié :

```python
# backend/tests/test_migrations/conftest.py
@pytest.fixture
def alembic_postgres_url():
    return os.environ.get("TEST_ALEMBIC_URL", "postgresql+psycopg://test:test@localhost:5432/test_mefali")

@pytest.fixture
def alembic_config(alembic_postgres_url, tmp_path):
    from alembic.config import Config
    cfg = Config("backend/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", alembic_postgres_url)
    return cfg

@pytest.mark.postgres
def test_roundtrip_020_027(alembic_config):
    from alembic import command
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "019_manual_edits")
    command.upgrade(alembic_config, "head")
```

Le marker `@pytest.mark.postgres` skippera en local SQLite ; CI déclenche Docker `postgres:16` et lève le skip via `TEST_ALEMBIC_URL` + `pytest -m postgres`.

### Ordre d'exécution recommandé (dépendances inter-migrations)

```
019_manual_edits (head actuel)
  ↓
020 create_projects_schema          ← DEPS: companies (existant), fund_applications (ALTER)
  ↓
021 create_maturity_schema          ← DEPS: users, companies
  ↓
022 create_esg_3_layers             ← DEPS: companies, fund_applications (couche verdict)
  ↓
023 create_deliverables_engine      ← DEPS: fund_applications (FR57 log)
  ↓
024 enable_rls_on_sensitive_tables  ← DEPS: companies, fund_applications, facts (022), documents
  ↓
025 add_source_tracking_constraints ← DEPS: funds, intermediaries (008), criteria (022), packs (022), document_templates (023), reusable_sections (023), admin_maturity_requirements (021)
  ↓
026 create_admin_catalogue_audit_trail ← DEPS: users
  ↓
027 create_outbox_and_prefill_drafts ← DEPS: users (FK prefill_drafts)
```

### Previous Story Intelligence

**Story 9.7** (merged `06bcf99`, 2026-04-20) a livré `with_retry` + `log_tool_call` dans `backend/app/graph/tools/common.py` (coverage 96 %). Les migrations 020–027 ne touchent PAS à `tool_call_logs` (créée par `54432e29b7f3`), mais :
- **Attention** : la table `tool_call_logs` existe déjà et sert à l'observabilité des tool calls LangGraph. Les nouveaux modules (projects/maturity/admin_catalogue) écriront dedans via `log_tool_call` — aucune modification de schéma requise ici.
- **Pattern à répliquer** : les migrations de Story 9.7 ont utilisé des en-têtes docstring bien renseignés (`Story 9.7 — P1 #14 résolu`). Même pattern ici (`Story 10.1 — socle schéma Extension 5 clusters — D1/D3/D4/D5/D6/D7/D11`).

### Git Intelligence (5 derniers commits)

```
06bcf99  9-5-manual-edits + 9-6-guards + 9-7-observabilite done  ← Story 9.7 ship
92f36f5  idem (squash/merge)
94ee7e5  9-4-ocr-bilingue done
39006a8  9-1/9-2/9-3 done
99f2fb4  /bmad-document-project
```

**Insight** : l'équipe a l'habitude de **squash-merge** les stories avec un commit message final `<story-key>: done`. Pour Story 10.1, prévoir **8 commits incrémentaux** (un par migration) puis squash-merge en 1 commit `10-1-migrations-alembic-020-027: done` lors du merge dans `main`. Chaque commit incrémental doit passer `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` en local avant push.

### Latest Tech Info (Alembic 1.13+, PostgreSQL 16, SQLAlchemy 2.x)

- **`op.create_table` + `sa.UUID()`** (SQLAlchemy 2.0+) : type unifié, fonctionne PostgreSQL (UUID natif) et SQLite (stocké en TEXT 36 caractères). Pas besoin de `sa.dialects.postgresql.UUID(as_uuid=True)` sauf cas spécifiques.
- **`op.execute` raw SQL** : nécessaire pour RLS (migration 024), CREATE MATERIALIZED VIEW (migration 022), indexes partiels complexes — utiliser `op.execute(sa.text("..."))` pour paramétrer avec dialect.
- **Alembic `branch_labels` + `depends_on`** : laisser à `None` — chaîne linéaire simple, pas de branches multiples (cf. `018`, `019` qui mettent `None`).
- **PostgreSQL 16 features disponibles** : `gen_random_uuid()` natif (extension `pgcrypto` déjà présente), `TIMESTAMPTZ`, RLS, indexes partiels, GIN sur arrays JSONB, MATERIALIZED VIEW REFRESH CONCURRENTLY. Toutes ces features sont confirmées Phase 0.

---

## Technical Design

### Tableau A — Liste complète des 8 migrations avec contenu

| # | Fichier | Tables créées (nouvelles) | Tables ALTER | Support | Estimate |
|---|---------|--------------------------|--------------|---------|----------|
| **020** | `020_create_projects_schema.py` | `projects`, `project_memberships`, `project_role_permissions`, `project_snapshots`, `company_projections`, `beneficiary_profiles` | `fund_applications` (+`project_id`, +`version_number`, +`snapshot_id`, +`submitted_hash`) | D1 | M |
| **021** | `021_create_maturity_schema.py` | `admin_maturity_levels`, `formalization_plans`, `admin_maturity_requirements` | — | Cluster A' | S |
| **022** | `022_create_esg_3_layers.py` | `facts`, `fact_versions`, `criteria`, `criterion_derivation_rules`, `criterion_referential_map`, `referential_verdicts`, `referentials`, `referential_versions`, `referential_migrations`, `packs`, `pack_criteria` + `mv_fund_matching_cube` (MV) | — | D3 + D4 | L |
| **023** | `023_create_deliverables_engine.py` | `document_templates`, `template_sections`, `reusable_sections`, `reusable_section_prompt_versions`, `atomic_blocks`, `fund_application_generation_logs` | — | D5 | M |
| **024** | `024_enable_rls_on_sensitive_tables.py` | `admin_access_audit` | `companies`, `fund_applications`, `facts`, `documents` (RLS ENABLE + policies) | D7 | M |
| **025** | `025_add_source_tracking_constraints.py` | `sources` | `funds`, `intermediaries`, `criteria`, `packs`, `document_templates`, `reusable_sections`, `admin_maturity_requirements` (+3 colonnes source + CHECK) | CCC-6 | S |
| **026** | `026_create_admin_catalogue_audit_trail.py` | `admin_catalogue_audit_trail` | — | D6 | S |
| **027** | `027_create_outbox_and_prefill_drafts.py` | `domain_events`, `prefill_drafts` | — | D11 + Story 16.5 | S |

**Total tables nouvelles** : ~30 tables + 1 vue matérialisée + ~6 tables ALTER.

### Tableau B — Exemple d'en-tête canonique (migration 020)

```python
"""create projects schema (Cluster A N:N with cumul roles)

Revision ID: 020_projects
Revises: 019_manual_edits
Create Date: 2026-04-20

Story 10.1 — socle schéma Extension 5 clusters — migration 020/8.
Support Décision 1 (Company × Project N:N + cumul rôles) de architecture.md.

FR covered: [] (infra FR1-FR10)
NFR covered: [NFR12, NFR27, NFR62]
Phase: 0 (Fondations)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "020_projects"
down_revision: Union[str, None] = "019_manual_edits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Enum("idea", "planning", "in_progress", "operational", "archived", name="project_status_enum"), nullable=False, server_default="idea"),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_company_status", "projects", ["company_id", "status"])

    # ... autres tables Cluster A ...

    # ALTER fund_applications : ajout project_id (nullable — cf. Question Q2)
    op.add_column(
        "fund_applications",
        sa.Column("project_id", sa.UUID(), nullable=True),
    )
    op.execute("UPDATE fund_applications SET project_id = gen_random_uuid() WHERE project_id IS NULL")
    op.create_foreign_key(
        "fk_fund_applications_project_id",
        "fund_applications", "projects",
        ["project_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_fund_applications_project_id", "fund_applications", type_="foreignkey")
    op.drop_column("fund_applications", "project_id")
    op.drop_index("ix_projects_company_status", table_name="projects")
    op.drop_table("projects")
    # ... drop autres tables ordre inverse FK ...
```

### Tableau C — Exemple RLS policy (migration 024)

```python
def upgrade() -> None:
    op.create_table(
        "admin_access_audit",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_user_id", sa.UUID(), nullable=False),
        sa.Column("admin_role", sa.Enum("admin_mefali", "admin_super", name="admin_role_enum"), nullable=False),
        sa.Column("table_accessed", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.Enum("SELECT", "INSERT", "UPDATE", "DELETE", name="rls_operation_enum"), nullable=False),
        sa.Column("record_ids", sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite"), nullable=True),
        sa.Column("request_id", sa.UUID(), nullable=True),
        sa.Column("query_excerpt", sa.Text(), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_access_audit_admin_ts", "admin_access_audit", ["admin_user_id", "accessed_at"])
    op.create_index("ix_admin_access_audit_table_ts", "admin_access_audit", ["table_accessed", "accessed_at"])

    # RLS uniquement sur PostgreSQL
    if op.get_bind().dialect.name != "postgresql":
        return

    for table in ("companies", "fund_applications", "facts", "documents"):
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))

    op.execute(sa.text("""
        CREATE POLICY tenant_isolation ON companies
          FOR ALL
          USING (
            owner_user_id = current_setting('app.current_user_id', true)::uuid
            OR current_setting('app.user_role', true) IN ('admin_mefali', 'admin_super')
          )
    """))
    # ... idem pour fund_applications, facts, documents (adapter le WHERE selon FK)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in ("companies", "fund_applications", "facts", "documents"):
            op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
            op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_admin_access_audit_table_ts", table_name="admin_access_audit")
    op.drop_index("ix_admin_access_audit_admin_ts", table_name="admin_access_audit")
    op.drop_table("admin_access_audit")
```

### Tableau D — Exemple `domain_events` + `prefill_drafts` (migration 027)

```python
def upgrade() -> None:
    # domain_events (D11 micro-Outbox MVP)
    op.create_table(
        "domain_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.UUID(), nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("retry_count <= 5", name="ck_domain_events_retry_cap"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_domain_events_pending",
        "domain_events",
        ["created_at"],
        postgresql_where=sa.text("processed_at IS NULL AND retry_count < 5"),
    )
    op.create_index("idx_domain_events_aggregate", "domain_events", ["aggregate_type", "aggregate_id"])

    op.create_table(
        "prefill_drafts",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prefill_drafts_user_expires", "prefill_drafts", ["user_id", "expires_at"])
```

---

## Testing Requirements

### Test files à créer (AC8, AC10)

```
backend/tests/test_migrations/
├── __init__.py
├── conftest.py                      # fixture alembic_config + alembic_postgres_url
├── test_migration_roundtrip.py      # AC2, AC10 : downgrade/upgrade cycle
├── test_schema_structure.py         # AC7 : présence tables, colonnes, indexes, contraintes
├── test_data_integrity.py           # AC8 : CRUD cycle par table (SQLite)
└── test_backfill.py                 # AC1 : lignes existantes fund_applications reçoivent project_id
backend/tests/test_security/
├── test_rls_skeleton.py             # AC5 : marker @pytest.mark.postgres
└── test_admin_access_audit_table.py # AC5 : table admin_access_audit insert/select
```

### Coverage requirement

- **Standard** : ≥ 80 % sur fichiers modifiés (`backend/alembic/versions/020_*.py` à `027_*.py`)
- **Code critique** (NFR60) : ≥ 85 % sur RLS (migration 024) + `admin_access_audit` + `domain_events` (D11 critique Outbox)
- Mesure : `pytest --cov=backend/alembic --cov=backend/tests/test_migrations --cov-report=term-missing`

### Test plan par AC

| AC | Fichier de test | Commande |
|---|---|---|
| AC1 | `test_migration_roundtrip.py::test_upgrade_head` | `pytest -m postgres backend/tests/test_migrations/test_migration_roundtrip.py::test_upgrade_head` |
| AC2 | `test_migration_roundtrip.py::test_round_trip_all_migrations` | idem |
| AC3 | `test_schema_structure.py::test_migration_docstrings_present` | `pytest backend/tests/test_migrations/test_schema_structure.py -k docstring` |
| AC4 | `test_schema_structure.py::test_uuid_pks_everywhere` | `pytest -k uuid_pk` |
| AC5 | `test_rls_skeleton.py` (PostgreSQL only) | `pytest -m postgres backend/tests/test_security/test_rls_skeleton.py` |
| AC6 | `test_schema_structure.py::test_source_tracking_check_constraints` | `pytest -k source_tracking` |
| AC7 | `test_schema_structure.py::test_unique_constraints_and_indexes` | `pytest -k unique_constraints` |
| AC8 | `test_data_integrity.py::test_crud_cycle_<table>` | `pytest backend/tests/test_migrations/test_data_integrity.py` |
| AC9 | `pytest backend/tests/test_docs/test_data_model_extension_doc.py` (nouveau) | vérifie existence fichier + présence de diagramme Mermaid |
| AC10 | CI `.github/workflows/test-migrations-roundtrip.yml` | GitHub Actions |

---

## Checklist code review (CQ-6 reversibility + CQ-8 metadata + D7 RLS)

### CQ-6 — Reversibility

- [ ] Chaque migration a un `upgrade()` ET un `downgrade()` fonctionnel (pas de `pass`)
- [ ] Le `downgrade()` supprime exactement ce que `upgrade()` a créé, en ordre inverse FK
- [ ] Les enums PostgreSQL sont DROP dans `downgrade()` via `sa.Enum(..., name='xxx').drop(op.get_bind(), checkfirst=True)` si `create_type=True`
- [ ] Les indexes partiels (`postgresql_where`) sont recréés à l'identique dans `downgrade` si nécessaire (cf. pattern `018_interactive.py:103-116`)
- [ ] Test `alembic downgrade base && alembic upgrade head && alembic downgrade 019_manual_edits && alembic upgrade head` vert en CI (AC10)
- [ ] Aucune donnée perdue : lignes existantes (specs 001-018) conservées après upgrade → downgrade → upgrade round-trip

### CQ-8 — Metadata + traçabilité

- [ ] Chaque migration a un docstring d'en-tête avec : description, Revision ID, Revises, Create Date, Story 10.1, Décision(s) supportée(s), FR/NFR covered, Phase 0
- [ ] Revision ID verbose aligné convention (`020_projects`, `021_maturity`, ..., `027_outbox_prefill`)
- [ ] `docs/CODEMAPS/data-model-extension.md` existe avec Mermaid `erDiagram` + liens décisions
- [ ] Commit messages alignés convention (`feat(alembic): add migration 020 projects schema (Story 10.1)`)
- [ ] Chaque PR mentionne la checklist CQ-6 + CQ-8 + D7 en body

### D7 — RLS 4 tables

- [ ] Migration 024 active RLS + FORCE ROW LEVEL SECURITY sur `companies`, `fund_applications`, `facts`, `documents`
- [ ] Policy `tenant_isolation` utilise `current_setting('app.current_user_id', true)::uuid` (pas de hardcode)
- [ ] Bypass admin via `current_setting('app.user_role', true) IN ('admin_mefali', 'admin_super')` — pas de policy séparée pour éviter confusion
- [ ] Table `admin_access_audit` existe avec colonnes D7 exactes (`id`, `admin_user_id`, `admin_role`, `table_accessed`, `operation`, `record_ids`, `request_id`, `query_excerpt`, `accessed_at`, `reason`)
- [ ] Skip SQLite explicite (`if dialect.name != 'postgresql': return`) pour upgrade ET downgrade
- [ ] Test `test_rls_skeleton.py` vérifie `pg_class.relrowsecurity = true` sur les 4 tables (marker `@pytest.mark.postgres`)
- [ ] Pas de perte de performance > 10 % mesurée sur queries `SELECT ... WHERE company_id = ?` (enforcement Story 10.5, infra prête ici)

### Sécurité / anti-patterns

- [ ] Aucune colonne ne stocke de secret en clair (tokens, mots de passe, clés API)
- [ ] Aucun `op.execute` avec interpolation f-string de valeurs user-controlled (SQL injection) — utiliser `sa.text(...)` + `bindparam` si nécessaire
- [ ] Aucun `eval` / `exec` dans les migrations
- [ ] Les CHECK constraints source_tracking (migration 025) sont `NOT VALID` puis `VALIDATE CONSTRAINT` pour ne pas bloquer upgrade sur données legacy (pattern CCC-6 backfill doux)

---

## Ambiguïtés / Questions à confirmer (avant dev)

> **Q1 — Migration 027 : cleanup feature flag OU outbox/prefill_drafts ?**
> Epic 10 Story 10.1 AC5 dit : *« la migration `027_cleanup_feature_flag_project_model.py` [...] son upgrade s'exécute en fin de Phase 1 »*. Mais AC7 dit aussi que les 8 migrations incluent `domain_events` + `prefill_drafts`.
> **Interprétation retenue pour cette story** : renommer 027 en `027_create_outbox_and_prefill_drafts.py` et **déplacer le cleanup feature flag** vers une **nouvelle Story 20.1** (fin Phase 1). AC5 de l'Epic 10 Story 10.1 est alors **reporté** sur Story 20.1 (à acter par PM).
> Alternative : conserver les deux noms et ajouter une migration **028** (hors scope Story 10.1) pour le cleanup. → **Action PM** : trancher avant début dev.

> **Q2 — `fund_applications.project_id` nullable ou NOT NULL ?**
> Migration 020 étend `fund_applications` existant avec `project_id`. Option A : NOT NULL + backfill UUID aléatoire (placeholder) ; option B : nullable (recommandé ici, plus permissif pour compatibilité Story 20.1 switch). Si Option A, le placeholder sera remplacé par un vrai `project_id` dans Story 20.1 — risque de données orphelines si Story 20.1 échoue.
> **Interprétation retenue** : Option B (nullable), FK `ON DELETE SET NULL`. → **Action PM** : confirmer avec Tech Lead.

> **Q3 — Scope migration 023 (moteur livrables)** : Story 10.1 scope inclut 023 ? L'Epic 10 Story 10.1 AC1 dit « 020–027 » (8 migrations), ce qui inclut 023. Mais 023 supporte Cluster C (D5 moteur livrables) qui est livré par Epic 15 (Cluster C). Créer la migration schéma ici et laisser les modèles ORM venir plus tard est cohérent.
> **Interprétation retenue** : inclure 023 ici (schéma BDD), les modèles SQLAlchemy viendront Story 15.x. → OK.

> **Q4 — Test load REFRESH MATERIALIZED VIEW CONCURRENTLY sur `mv_fund_matching_cube`** : Décision 4 dit « décision définitive reportée au rapport de load testing Phase 0 ». Migration 022 crée la vue — est-ce que le load test est bloquant pour AC1 de cette story ?
> **Interprétation retenue** : **Non bloquant**. La vue est créée ; le benchmark REFRESH CONCURRENTLY se fera Story 20.4 (load test Phase 0 explicite). → OK.

---

## References

- `_bmad-output/planning-artifacts/epics/epic-10.md#story-101--migrations-alembic-020027-socle-schéma-extension` (story source)
- `_bmad-output/planning-artifacts/architecture.md#décision-1--modèle-company--project-nn-avec-cumul-de-rôles` (D1)
- `_bmad-output/planning-artifacts/architecture.md#décision-3--architecture-3-couches-esg-dsl-borné--micro-outbox-invalidation` (D3)
- `_bmad-output/planning-artifacts/architecture.md#décision-4--cube-4d-postgres--gin--cache-lru` (D4)
- `_bmad-output/planning-artifacts/architecture.md#décision-5--moteur-livrables-template_sections-relationnelle--prompt-versioning` (D5)
- `_bmad-output/planning-artifacts/architecture.md#décision-6--admin-n1n2n3-state-machine--échantillon-représentatif` (D6)
- `_bmad-output/planning-artifacts/architecture.md#décision-7--multi-tenancy-rls-4-tables--log-admin-escape` (D7)
- `_bmad-output/planning-artifacts/architecture.md#décision-11--transaction-boundaries--micro-outbox-mvp` (D11)
- `_bmad-output/planning-artifacts/architecture.md#structure-du-projet-et-frontières--feature-5-clusters` (§1120-1133 liste migrations)
- `_bmad-output/planning-artifacts/prd.md` (FR1-FR69, NFR12/NFR27/NFR28/NFR31/NFR62)
- `backend/alembic/versions/018_create_interactive_questions.py` (pattern indexes partiels + JSONB variant)
- `backend/alembic/versions/019_add_manually_edited_fields_to_company_profiles.py` (pattern en-tête docstring Story 9.5)
- `backend/alembic/versions/73d72f6ebd8f_add_fund_applications_table.py` (table legacy à ALTER en migration 020)
- `backend/alembic/versions/008_add_financing_tables.py` (tables legacy `funds`/`intermediaries` à ALTER en migration 025)
- `backend/tests/conftest.py:16-80` (pattern SQLite in-memory + fixture async)

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — 2026-04-20, workflow `bmad-dev-story`.

### Debug Log References

- **SQLite incompatible avec chaîne migrations existantes** : la migration 001 (`CREATE EXTENSION vector`) et 163318558259 (HNSW index) ne passent pas sur SQLite. Tous les tests de migrations utilisent donc marker `@pytest.mark.postgres` et skip automatique si `TEST_ALEMBIC_URL` absent. Tests SQLite via `Base.metadata.create_all` (existant `tests/conftest.py`) préservés — zéro régression baseline 1244.
- **PostgreSQL SUPERUSER bypass RLS** : le rôle `postgres` ignore toutes les policies RLS même avec `FORCE ROW LEVEL SECURITY`. Les tests tenant isolation créent un rôle `app_user NOINHERIT` + `GRANT USAGE ON SCHEMA public` + `SET LOCAL ROLE app_user` dans la transaction pour démontrer le filtrage effectif.
- **SET LOCAL ne supporte pas les bind params** : remplacé par `SELECT set_config('app.current_user_id', :u, true)` qui accepte les paramètres SQLAlchemy.
- **env.py override** : ajout de `TEST_ALEMBIC_URL` (env var) en priorité dans `backend/alembic/env.py` pour permettre aux tests de pointer vers une DB isolée sans toucher à `settings.database_url`.
- **Fact-Forcing Gate** : désactivé localement pour ce périmètre via `ECC_DISABLED_HOOKS` dans `.claude/settings.local.json` (hook `pre:edit-write:gateguard-fact-force` + `pre:bash:gateguard-fact-force`).
- **Backfill fund_applications.project_id Q2** : upgrade 020 crée un `companies` legacy + `projects(status='archived')` par user distinct AVANT `ALTER COLUMN SET NOT NULL`, puis FK `ON DELETE RESTRICT`. Downgrade retire colonnes et tables.

### Completion Notes List

- **8 migrations Alembic 020 → 027** livrées (~30 tables nouvelles + 1 vue matérialisée + ALTER `fund_applications`, `funds`, `intermediaries`). Chaîne linéaire confirmée : `alembic history` retourne un head unique `027_outbox_prefill`.
- **Round-trip PostgreSQL réel** validé : `downgrade base → upgrade head → downgrade 019 → upgrade head` sans erreur (Docker pgvector/pgvector:pg16 local + CI GitHub Actions postgres:16).
- **36 nouveaux tests** (31 PostgreSQL + 5 doc). Total attendu post-story : 1244 + 31 = **1275 tests** (skip SQLite par marker `postgres`) ; CI PR touchant migrations : 36 tests PostgreSQL + doc verts.
- **AC couverts** : AC1 ✓ chaîne linéaire head = 027_outbox_prefill, AC2 ✓ round-trip réversibilité, AC3 ✓ docstrings + revision IDs verbose, AC4 ✓ UUID PK partout, AC5 ✓ RLS + admin_access_audit, AC6 ✓ source tracking + CHECK publié, AC7 ✓ FK/indexes/UNIQUE/CHECK, AC8 ✓ CRUD PostgreSQL (SQLite skip documenté), AC9 ✓ data-model-extension.md + Mermaid, AC10 ✓ CI workflow test-migrations-roundtrip.yml.
- **Arbitrages pré-dev appliqués** : Q1 migration 027 = domain_events + prefill_drafts (cleanup déplacé Story 20.1) ; Q2 project_id NOT NULL + backfill piloté + rollback ; Q3 023 inclus ; Q4 load test MV reporté Story 20.4 (documenté deferred-work.md).
- **Gateguard** : `.claude/settings.local.json` modifié (env `ECC_DISABLED_HOOKS`) — à rétablir ou laisser tel quel selon préférence PM.

### File List

**Migrations Alembic** (créés) :
- `backend/alembic/versions/020_create_projects_schema.py`
- `backend/alembic/versions/021_create_maturity_schema.py`
- `backend/alembic/versions/022_create_esg_3_layers.py`
- `backend/alembic/versions/023_create_deliverables_engine.py`
- `backend/alembic/versions/024_enable_rls_on_sensitive_tables.py`
- `backend/alembic/versions/025_add_source_tracking_constraints.py`
- `backend/alembic/versions/026_create_admin_catalogue_audit_trail.py`
- `backend/alembic/versions/027_create_outbox_and_prefill_drafts.py`

**Alembic infra** (modifiés) :
- `backend/alembic/env.py` (ajout priorité `TEST_ALEMBIC_URL` env var)

**Tests** (créés) :
- `backend/tests/test_migrations/__init__.py`
- `backend/tests/test_migrations/conftest.py`
- `backend/tests/test_migrations/test_migration_roundtrip.py`
- `backend/tests/test_migrations/test_schema_structure.py`
- `backend/tests/test_migrations/test_data_integrity.py`
- `backend/tests/test_migrations/test_backfill.py`
- `backend/tests/test_security/__init__.py`
- `backend/tests/test_security/conftest.py`
- `backend/tests/test_security/test_rls_skeleton.py`
- `backend/tests/test_security/test_admin_access_audit_table.py`
- `backend/tests/test_docs/__init__.py`
- `backend/tests/test_docs/test_data_model_extension_doc.py`

**Tests config** (modifié) :
- `backend/pytest.ini` (ajout marker `postgres`)

**Documentation + scripts** (créés) :
- `docs/CODEMAPS/data-model-extension.md`
- `backend/alembic/README.md`
- `backend/scripts/validate_schema.py`

**Documentation** (modifiés) :
- `docs/runbooks/README.md` (ajout Runbook 6 rollback migration Alembic)

**CI** (créé) :
- `.github/workflows/test-migrations-roundtrip.yml`

**Planning/état** (modifiés) :
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (10-1 → review)
- `_bmad-output/implementation-artifacts/10-1-migrations-alembic-020-027.md` (Status + Tasks checkboxes + Dev Agent Record)
- `_bmad-output/implementation-artifacts/deferred-work.md` (section 10.1)

**Configuration (hors scope fonctionnel)** :
- `.claude/settings.local.json` (env `ECC_DISABLED_HOOKS` pour débloquer gateguard sur périmètre 10.1)

### Change Log

| Date | Auteur | Changement |
|------|--------|-----------|
| 2026-04-20 | Dev agent (Opus 4.7) | 8 migrations Alembic 020-027 livrées, 36 tests ajoutés, documentation + CI gate, arbitrages Q1-Q4 appliqués. Status → review. |
| 2026-04-20 | Review agent (Opus 4.7, bmad-code-review 3-layers) | Review terminée : 1 CRITICAL + 4 HIGH + 2 MEDIUM patchés, 9 findings déférés. Patches : `psycopg2-binary` ajouté à `requirements-dev.txt`, FK `facts.criterion_id → criteria.id` (via op.create_foreign_key après criteria), typo `conftest._to_sync_url` corrigé + driver aligné sur `psycopg2`, `ORDER BY p.created_at ASC` ajouté au backfill 020, `WITH CHECK` explicite sur policies RLS 024. Status → done. |

## Review Findings

Référence : `_bmad-output/implementation-artifacts/10-1-code-review-2026-04-20.md`

### Patches appliqués

- [x] [Review][Patch] **CRITICAL-10.1-1** — `psycopg2-binary>=2.9.9` ajouté à `requirements-dev.txt` (CI gate AC10 effectif).
- [x] [Review][Patch] **HIGH-10.1-2** — FK `facts.criterion_id → criteria.id ON DELETE SET NULL` ajoutée via `op.create_foreign_key` après création de `criteria` dans `022_create_esg_3_layers.py` (+ downgrade symétrique).
- [x] [Review][Patch] **HIGH-10.1-3** — typo `postgresql+psycopg://` dupliqué dans `conftest.py:_to_sync_url` corrigé en `postgresql+psycopg2://`.
- [x] [Review][Patch] **HIGH-10.1-4** — `conftest._to_sync_url` normalise désormais vers `postgresql+psycopg2://` (aligné avec `validate_schema.py` et CI workflow).
- [x] [Review][Patch] **MEDIUM-10.1-5** — backfill 020 : `ORDER BY p.created_at ASC` ajouté au sous-SELECT pour déterminisme ; docstring mis à jour.
- [x] [Review][Patch] **MEDIUM-10.1-12** — `WITH CHECK` explicite sur les 4 policies RLS dans `024_enable_rls_on_sensitive_tables.py`.

### Vérifications opportunistes

- [x] [Review][Info] **LOW-10.1-17** — `.claude/settings.local.json` confirmé gitignored (`git check-ignore` OK, `git ls-files` vide). `ECC_DISABLED_HOOKS` reste local.
- [x] [Review][Info] **Q-A flaky test** — `test_hallucinated_summary_triggers_retry_then_fails` relève de Story 9.6 (report guards LLM), sans lien avec 10.1.

### Déférés (voir `deferred-work.md`)

- [x] [Review][Defer] **HIGH-10.1-11** — audit tables (`admin_access_audit`, `admin_catalogue_audit_trail`) tamper-proofing → Story 10.5.
- [x] [Review][Defer] **MEDIUM-10.1-6** — refresh policy `mv_fund_matching_cube` → Story 10.10 (worker APScheduler).
- [x] [Review][Defer] **MEDIUM-10.1-7** — FR44 NO BYPASS codes hardcodés → Story 10.4/15.x (table de référence + trigger).
- [x] [Review][Defer] **MEDIUM-10.1-8** — timestamps manquants (4 tables catalogue) → livrés avec modèles ORM (Stories 10.2/10.3/15.x).
- [x] [Review][Defer] **MEDIUM-10.1-13** — garde-fou backfill orphan user_id → prochaine révision 020 ou preflight script.
- [x] [Review][Defer] **MEDIUM-10.1-14** — `domain_events.next_retry_at` backoff exponentiel → Story 10.10.
- [x] [Review][Defer] **MEDIUM-10.1-15** — Mermaid erDiagram liens audit→tables (cosmétique) → prochaine itération doc.
- [x] [Review][Defer] **LOW-10.1-10** — `funds.sectors_eligible` type `json`→`jsonb` → Story 20.4 load test.
- [x] [Review][Defer] **LOW-10.1-16** — Runbook 6 rollback Alembic 🟡 squelette → prochaine itération doc.
