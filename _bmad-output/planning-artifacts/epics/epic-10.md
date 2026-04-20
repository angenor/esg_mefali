---
title: "Fondations Extension Phase 0 (BLOQUANT)"
epic_number: 10
status: planned
story_count: 21
stories: [10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 10.14, 10.15, 10.16, 10.17, 10.18, 10.19, 10.20, 10.21]
dependencies:
  - story: 9.7
    type: blocking
    reason: "Observabilité with_retry + log_tool_call requise avant création nouveaux modules Extension (projects/maturity/admin_catalogue)"
blocks: [epic-11, epic-12, epic-13, epic-14, epic-15, epic-16, epic-17, epic-18, epic-19]
fr_covered: [FR59, FR62, FR63, FR64]
nfr_couverts: [NFR5, NFR7, NFR12, NFR15, NFR24, NFR27, NFR28, NFR31, NFR32, NFR33, NFR34, NFR35, NFR36, NFR42, NFR43, NFR48, NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR67, NFR72, NFR73, NFR74]
qo_rattachees: []
notes: "Phase 0. Catalogue data-driven, migrations 020-027, 3 nouveaux modules squelettes, RLS 4 tables, micro-Outbox, DSL Pydantic, framework prompts CCC-9, StorageProvider, env DEV/STAGING/PROD, feature flag ENABLE_PROJECT_MODEL, socle UI fondation (Storybook + 6 composants ui/ + EsgIcon)."
---

## Epic 10 — Stories détaillées (Fondations Extension Phase 0, BLOQUANT)

> **Garde-fou global Epic 10** : toute story créant un module ou un nœud LangGraph doit **déjà être instrumentée `with_retry` + `log_tool_call`** (Story 9.7 merged en amont — CQ-11). Aucune exception.

### Story 10.1 : Migrations Alembic 020–027 (socle schéma Extension)

**As a** Équipe Mefali (DX/SRE),
**I want** livrer les 8 migrations Alembic `020_create_projects_schema.py` → `027_cleanup_feature_flag_project_model.py` (cette dernière prévue fin Phase 1) dans l'ordre séquentiel documenté,
**So that** les 3 nouveaux modules `projects/`, `maturity/`, `admin_catalogue/` disposent de leur schéma, que l'architecture 3-couches ESG (B) et le moteur livrables (C) puissent atterrir en Phase 1, et que les contraintes transverses (RLS, SOURCE-TRACKING, audit trail) soient enforçables au niveau BDD.

**Metadata (CQ-8)**
- `fr_covered`: [] (support infra FR1–FR10, FR11–FR16, FR17–FR26, FR24, FR36–FR44, FR59, FR62, FR64)
- `nfr_covered`: [NFR12, NFR27, NFR28, NFR31, NFR62]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 9.7]

**Acceptance Criteria**

**AC1** — **Given** `backend/alembic/versions/`, **When** les 8 migrations sont appliquées de façon incrémentale (`alembic upgrade head` depuis l'état 019 spec 019 livrée), **Then** toutes passent sans erreur **And** `alembic current` retourne `027` en tête.

**AC2** — **Given** chaque migration, **When** auditée, **Then** elle respecte la convention de nommage `NNN_description.py` (NFR62), comporte un `upgrade()` + `downgrade()` idempotents, et référence explicitement les décisions architecturales supportées (D1 pour 020, D3 pour 022, D5 pour 023, D7 pour 024, NFR-SOURCE-TRACKING pour 025, etc.) dans un commentaire d'en-tête.

**AC3** — **Given** le test de restauration BDD trimestriel (NFR32), **When** un rollback 027 → 019 est déclenché, **Then** toutes les migrations redescendent sans erreur (tests `alembic downgrade 019` dans CI).

**AC4** — **Given** un dump de prod vers STAGING anonymisé (NFR73), **When** les migrations 020–027 sont ré-appliquées, **Then** aucune perte de données existantes (compagnies, profils, documents des 18 specs livrées).

**AC5** — **Given** la migration `027_cleanup_feature_flag_project_model.py`, **When** son upgrade s'exécute en fin de Phase 1, **Then** elle retire proprement toute colonne/index/contrainte liée au feature flag temporaire (coupé par story 20.1).

**AC6** — **Given** les tests backend, **When** `pytest backend/tests/test_migrations/` exécuté, **Then** tests de schéma (présence des tables, indexes composites cube 4D NFR51, GIN indexes AR-D4, contraintes de clés étrangères) verts **And** coverage des modules d'ORM associés ≥ 80 %.

**AC7** — **Given** la migration **consolide également** deux tables transverses rattachées à des features non-schéma-migration-020-027 mais nécessaires dès Phase 0, **When** auditée, **Then** elle inclut :
  - **`prefill_drafts(id UUID PK, payload JSONB, user_id UUID FK, expires_at TIMESTAMP, created_at)`** — consommée par Story 16.5 (fallback deep-link copilot) avec RLS enforcement + index sur `expires_at` (pour nettoyage worker 10.10).
  - **`domain_events(id, event_type, aggregate_type, aggregate_id, payload, status, created_at, processed_at)`** — consommée par Story 10.10 avec indexes composites `(status, created_at)` + `(aggregate_type, aggregate_id)`.

  Les autres stories ne créent **pas** de migrations ad-hoc : elles consomment les tables créées ici (CQ-7 respecté — une migration par fichier, pas une migration par story).

---

### Story 10.2 : Module `projects/` squelette (router + service + schemas + models + node LangGraph)

**As a** PME User (owner),
**I want** disposer du socle technique minimal du module `projects` — endpoints REST stub, service bus, schemas Pydantic, models SQLAlchemy, nœud LangGraph `project_node` + `projects_tools.py` —,
**So that** les stories Epic 11 (Cluster A FR1–FR10) puissent y déposer la logique métier sans recréer la plomberie.

**Metadata (CQ-8)**
- `fr_covered`: [] (infra pour FR1–FR10)
- `nfr_covered`: [NFR49, NFR62, NFR64]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: M
- `depends_on`: [Story 10.1 (migration 020), Story 9.7 (instrumentation tools)]

**Acceptance Criteria**

**AC1** — **Given** la structure `backend/app/modules/projects/`, **When** auditée, **Then** elle contient `router.py` (préfixe `/api/projects`), `service.py`, `schemas.py`, `models.py` conformément au pattern CLAUDE.md (NFR62).

**AC2** — **Given** `backend/app/graph/nodes.py`, **When** relu, **Then** `project_node` est déclaré et enregistré dans le graphe (passant à 10 nœuds spécialistes — AR-ST-3), avec conditional edges vers le ToolNode.

**AC3** — **Given** `backend/app/graph/tools/projects_tools.py` créé, **When** chargé, **Then** il expose ≥ 1 tool stub `create_project(company_id, name, state='idée')` wrappé `with_retry` + `log_tool_call` (CQ-11 enforcement) **And** la signature est testée dans `test_graph/test_projects_tools.py`.

**AC4** — **Given** les endpoints stub `POST /api/projects`, `GET /api/projects/{id}`, **When** appelés sans auth, **Then** renvoient 401 ; **When** `ENABLE_PROJECT_MODEL=false`, **Then** renvoient **404** (feature masquée côté routing — Story 10.9 AC2) ; **When** `ENABLE_PROJECT_MODEL=true` mais Epic 11 pas encore livré, **Then** renvoient **501 Not Implemented** avec message explicite « livré en Epic 11 » **And** la distinction sémantique 404/501 est documentée dans OpenAPI (response schemas) pour consommateurs frontend + tests e2e.

**AC5** — **Given** un service consommateur (ex. futur `matching_service` Epic 14), **When** il importe `projects.service`, **Then** il n'accède **jamais directement à la table `project`** (anti God service NFR64).

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_projects/` exécuté, **Then** tests infra (import, route enregistrée, tool instrumenté, node dans graphe) verts.

---

### Story 10.3 : Module `maturity/` squelette

**As a** PME User (owner),
**I want** disposer du socle technique minimal du module `maturity` — endpoints REST stub, service, schemas, models, nœud LangGraph `maturity_node` + `maturity_tools.py` —,
**So that** les stories Epic 12 (Cluster A' FR11–FR16) puissent y déposer la logique métier de formalisation graduée.

**Metadata (CQ-8)**
- `fr_covered`: [] (infra pour FR11–FR16)
- `nfr_covered`: [NFR49, NFR62, NFR64, NFR66]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: M
- `depends_on`: [Story 10.1 (migration 021), Story 9.7, Story 10.2 (pattern répété)]

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/maturity/`, **When** auditée, **Then** même structure que `projects/` (router/service/schemas/models) + `formalization_plan_calculator.py` stub.

**AC2** — **Given** `maturity_node` dans le graphe, **When** le graphe est construit, **Then** il est enregistré (11ᵉ nœud spécialiste) avec routing conditionnel via `active_module` (pattern spec 013).

**AC3** — **Given** `maturity_tools.py`, **When** chargé, **Then** expose ≥ 1 tool stub `declare_maturity_level(level)` wrappé (Story 9.7).

**AC4** — **Given** la table `admin_maturity_requirement(country × level)` (migration 021), **When** auditée, **Then** elle porte la contrainte unique `(country, level)` et les colonnes `source_url`, `source_accessed_at`, `source_version` (NFR27 SOURCE-TRACKING — enforçable quand Story 10.11 livre la CI).

**AC5** — **Given** les endpoints stub, **When** auth + body valide, **Then** renvoient 501 avec message « livré en Epic 12 ».

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_maturity/` exécuté, **Then** tests infra verts + test du country-data-driven (ex. pas de string hardcodé pour « Sénégal »/« Côte d'Ivoire »).

---

### Story 10.4 : Module `admin_catalogue/` squelette (backend + UI admin catalogue UI-only)

**As a** Admin Mefali,
**I want** disposer du socle technique du module `admin_catalogue` côté backend (endpoints CRUD N1/N2/N3) **et** d'un squelette d'UI admin (`/admin/catalogue/*`), **sans** `admin_node` LangGraph (Clarification 2 architecture.md),
**So that** les workflows d'administration catalogue (fonds, intermédiaires, référentiels, packs, templates, rules) puissent être consommés par les Admins en UI form-based, sans couplage LLM inutile.

**Metadata (CQ-8)**
- `fr_covered`: [] (infra pour FR24, FR25, FR35, FR43 — aucun FR complet livré ici)
- `nfr_covered`: [NFR27, NFR28, NFR62, NFR64]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 10.1 (préparation table `admin_catalogue_audit_trail` migration 026)]
- `architecture_alignment`: Clarification 2 (`admin_node` rejeté, admin UI-only) + Décision 6 (state machine N1/N2/N3)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/admin_catalogue/`, **When** auditée, **Then** elle contient router `/api/admin/catalogue/*` + service + state machine N1/N2/N3 (`NodeState` enum : `draft`, `review_requested`, `reviewed`, `published`, `archived`) + schemas.

**AC2** — **Given** le graphe LangGraph, **When** les nœuds sont construits, **Then** **aucun `admin_node`** n'est enregistré (respect Clarification 2) et **aucun tool `create_catalogue_entity_N1` n'est exposé à LangChain** (UI-only).

**AC3** — **Given** les endpoints admin catalogue, **When** accédés par un user `owner`/`editor`/`viewer`, **Then** renvoient 403 **And** accès autorisé uniquement `admin_mefali` + `admin_super` avec MFA actif (FR61 — enforcement à livrer en Epic 18, stub acceptable ici).

**AC4** — **Given** `frontend/app/pages/admin/catalogue/`, **When** auditée, **Then** squelette de pages (liste + détail + formulaire multi-étape + preview diff) en dark mode par défaut (NFR62) et masqué aux rôles non-admin.

**AC5** — **Given** la state machine N1/N2/N3, **When** un admin `admin_mefali` invoque `request_review(entity_id)`, **Then** l'état passe `draft → review_requested` **And** un 2ᵉ admin `admin_mefali` peut approuver pour passer à `reviewed → published` (workflow peer review Décision 6).

**AC6** — **Given** une modification catalogue, **When** elle est confirmée, **Then** une ligne `admin_catalogue_audit_trail(actor_id, entity, action, before, after, ts)` est insérée (enforcement complet livré par Story 10.12).

**AC7** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/` + tests frontend admin exécutés, **Then** scénarios N1 → N2 → N3 + peer review + accès refusé non-admin tous verts.

---

### Story 10.5 : RLS PostgreSQL sur 4 tables sensibles + tests de contournement

**As a** System + Équipe Mefali (SRE/sécurité),
**I want** activer RLS (Row-Level Security) PostgreSQL sur `companies`, `fund_applications`, `facts`, `documents` via migration `024_enable_rls_on_sensitive_tables.py`, avec log d'escalade admin,
**So that** un user ne puisse **jamais** accéder aux données d'un autre tenant même en cas de bug applicatif (défense en profondeur FR59 + NFR12).

**Metadata (CQ-8)**
- `fr_covered`: [FR59]
- `nfr_covered`: [NFR12, NFR18]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 10.1 (migration 024), Story 9.7]
- `architecture_alignment`: Décision 7 (multi-tenancy RLS 4 tables + log admin escape)

**Acceptance Criteria**

**AC1** — **Given** migration 024 appliquée, **When** un `SELECT` est exécuté sur `companies`/`fund_applications`/`facts`/`documents` en tant que user connecté, **Then** seules les lignes rattachées au tenant du user sont retournées (policy RLS vérifiée).

**AC2** — **Given** un test de contournement simulant un bug applicatif (oublier un `WHERE company_id = ?` dans un query), **When** un user essaie d'accéder à une ressource d'un autre tenant, **Then** la query retourne `0 row` (RLS filtre) **And** aucune 500 n'est levée.

**AC3** — **Given** un `admin_super` effectue un escape RLS légitime (debug prod avec `SET ROLE admin_bypass`), **When** l'action est effectuée, **Then** une entrée `rls_admin_escape_log(admin_id, reason, ts, affected_tables)` est insérée (Décision 7) **And** alerting déclenché vers `admin_mefali` pour revue a posteriori.

**AC4** — **Given** les tests backend, **When** `pytest backend/tests/test_security/test_rls_enforcement.py` exécuté, **Then** scénarios (cross-tenant isolation, admin escape log, happy path own tenant, rôle `viewer` lecture seule) tous verts **And** coverage ≥ 85 % (code critique NFR60).

**AC5** — **Given** le pen test externe NFR18 (Story 20.3), **When** exécuté post-livraison, **Then** aucune faille de cross-tenant exploitable sur les 4 tables (condition de passage pilote).

**AC6** — **Given** les performances, **When** RLS activée, **Then** p95 queries sur les tables RLS reste ≤ 10 % du baseline pré-RLS (mesure avant/après documentée dans le rapport de story).

---

### Story 10.6 : Abstraction `StorageProvider` (local + S3 EU-West-3)

**As a** Équipe Mefali (SRE/backend),
**I want** une couche d'abstraction `StorageProvider` avec deux implémentations (`LocalStorageProvider` pour MVP/DEV, `S3StorageProvider` pour Phase Growth EU-West-3),
**So that** le passage de `/uploads/` local vers S3 (NFR24 data residency + NFR33 backup 2 AZ) soit un simple changement de config env, sans refactor métier dans les 8 modules existants qui manipulent des fichiers.

**Metadata (CQ-8)**
- `fr_covered`: [] (infra support FR36 deliverables + FR70 RAG + module documents spec 004)
- `nfr_covered`: [NFR24, NFR25, NFR33, NFR48, NFR60]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: M
- `depends_on`: [Story 9.7]

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/storage/`, **When** auditée, **Then** elle contient `base.py` (ABC `StorageProvider` avec `put(key, bytes) -> URI`, `get(key) -> bytes`, `delete(key)`, `signed_url(key, ttl)`, `list(prefix)`), `local.py`, `s3.py`.

**AC2** — **Given** la variable d'env `STORAGE_PROVIDER=local|s3`, **When** l'app démarre, **Then** l'instance correcte est injectée via `get_storage_provider()` dependency FastAPI.

**AC3** — **Given** les 8 modules existants (documents, reports, applications, financing fiche, etc.) qui manipulent `/uploads/`, **When** ils sont auditée, **Then** aucun n'utilise `open(path, "wb")` direct — tous passent par `storage.put()` (anti God service + portabilité).

**AC4** — **Given** `S3StorageProvider` avec credentials AWS valides, **When** `put()` est invoqué, **Then** l'objet atterrit en `s3://mefali-prod/<key>` région EU-West-3 (NFR24) **And** un `signed_url` TTL 15 min est retournable.

**AC5** — **Given** un fichier > 100 Mo, **When** uploadé, **Then** multipart upload S3 est utilisé (pas de OOM backend) **And** une progression SSE optionnelle peut être exposée à l'UI.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_core/test_storage_provider.py` exécuté avec `moto` ou équivalent pour mock S3, **Then** scénarios (put/get/delete/signed_url/list, round-trip local, round-trip S3, erreur réseau retry via `with_retry`) tous verts + coverage ≥ 80 %.

---

### Story 10.7 : Environnements DEV / STAGING / PROD ségrégués + pipeline anonymisation

> **Vigilance scope** : estimate L avec risque XL. **Split candidat à trancher en dev-story** si le périmètre déborde :
> - **10.7a** — Envs ségrégués (config AWS + secrets par env + CI pipelines avec approvals) → L
> - **10.7b** — Pipeline anonymisation STAGING mensuelle (copy-prod-to-staging.sh + mapping déterministe PII) → M
>
> **STAGING minimal Phase 0** (arbitrage Lot 2 Q2) : RDS t3.micro + 1 pod ECS Fargate. Check-list perf-sensibles dans CI (EXPLAIN plans sur hot paths) pour atténuer sous-dimensionnement. Montée en gamme déclenchée par traction business.

**As a** Équipe Mefali (SRE),
**I want** 3 environnements isolés (DEV local + STAGING AWS EU-West-3 minimal t3.micro + PROD AWS EU-West-3) avec secrets différenciés, pipeline de copie PROD → STAGING anonymisé, et accès PROD limité à `admin_super` avec audit full,
**So that** la dette NFR73 soit résolue avant le premier pilote PME (AR-D8 + NFR73).

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR15, NFR19, NFR25, NFR73]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 10.1, Story 10.6]

**Acceptance Criteria**

**AC1** — **Given** les 3 envs déployés, **When** un audit de config est mené, **Then** chacun possède ses propres `AWS RDS`, `S3 bucket`, `secret manager`, `domain`, et **aucun secret PROD** n'est accessible depuis DEV/STAGING.

**AC2** — **Given** le pipeline `copy-prod-to-staging.sh`, **When** exécuté, **Then** il anonymise PII (noms, emails, téléphones, RCCM/NINEA/IFU) via mapping déterministe avant insertion en STAGING **And** les documents sensibles (bilans, IDs) sont exclus de la copie par défaut.

**AC3** — **Given** un dev tente d'accéder à PROD pour debug, **When** il n'est pas `admin_super`, **Then** l'accès est refusé au niveau IAM **And** toute tentative est loggée vers audit trail + alerting.

**AC4** — **Given** les 3 envs, **When** leurs pipelines CI/CD tournent, **Then** ils appliquent la migration Alembic automatiquement (DEV auto, STAGING avec approval, PROD avec 2 approvals senior).

**AC5** — **Given** un tabletop exercise trimestriel (NFR36), **When** simulé, **Then** le plan de restauration BDD + file est documenté et exécutable **And** RTO 4 h + RPO 24 h respectés en test (NFR34/35).

**AC6** — **Given** la CI, **When** un dev merge sans passer STAGING, **Then** le merge PROD est bloqué (branch protection GitHub — NFR76).

**AC7** — **Given** STAGING minimal (RDS t3.micro + 1 pod Fargate), **When** la CI tourne, **Then** un job `explain-hotpaths.yml` analyse les plans EXPLAIN sur 5 requêtes critiques (cube 4D matching, ESG verdicts multi-référentiels, cube indexes GIN, query facts par entity, query FundApplication par status) **And** alerte si un plan bascule vers `Seq Scan` ou si le `total cost` dépasse un seuil défini (atténuation sous-dimensionnement STAGING Phase 0).

---

### Story 10.13 : Migration embeddings OpenAI → Voyage API (MVP, pas différée)

**As a** Équipe Mefali (backend/AI) + PME User indirectement,
**I want** migrer les embeddings de `OpenAI text-embedding-3-small` (1536 dim) vers **Voyage API** (`voyage-3` 1024 dim par défaut) dès le MVP via une abstraction `EmbeddingProvider` unique, avec fallback OpenAI automatique sur indisponibilité,
**So that** les performances + coût RAG soient optimisés dès le Phase 0 (valorisation crédit Voyage + qualité spécialisée FR/multilingue) et qu'Epic 19 Phase 0 (socle RAG refactor) consomme une seule abstraction (pas deux).

**Metadata (CQ-8)** — `fr_covered`: [] (NFR-only, migration provider + bench LLM) · `nfr_covered`: [NFR5, NFR7, NFR42, NFR43, NFR68, NFR74] · `phase`: 0 · `cluster`: Fondations · `estimate`: XL · `depends_on`: [10.1 migrations, 9.6 guards LLM, 9.7 observabilité] · `architecture_alignment`: Décision 10 (LLM Provider Layer 2 niveaux de switch — étendu aux embeddings + bench R-04-1 tranché 2026-04-19)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/embeddings/`, **When** auditée, **Then** elle contient `base.py` (ABC `EmbeddingProvider` avec `embed(texts: List[str], model: str) -> List[List[float]]`), `openai.py` (`OpenAIEmbeddingProvider` — legacy/fallback), `voyage.py` (`VoyageEmbeddingProvider` — MVP default).

**AC2** — **Given** variable d'env `EMBEDDING_PROVIDER=voyage`, **When** l'app démarre, **Then** Voyage est injecté via `get_embedding_provider()` dependency **And** fallback automatique vers OpenAI si Voyage indisponible (circuit breaker 60 s conformément pattern Story 9.7 AC5).

**AC3** — **Given** `voyage-3` (1024 dim) par défaut, **When** la variable d'env `VOYAGE_MODEL=voyage-3-large` est positionnée, **Then** le modèle large est utilisé (configurable sans redéploiement).

**AC4** — **Given** migration Alembic, **When** appliquée, **Then** nouvelle colonne `embedding_vec_v2 vector(1024)` créée + index HNSW sur la nouvelle colonne (NFR52) **And** l'ancienne `vector(1536)` est droppée **post-migration réussie** (pas avant pour permettre rollback).

**AC5** — **Given** corpus `DocumentChunk` existant (spec 004 livrée), **When** le batch job de re-embedding tourne, **Then** il procède par chunks de 100 docs (rate limits Voyage respectés) **And** la progression est trackée via `log_tool_call` (Story 9.7) + event `embedding_batch_progress` dans `domain_events`.

**AC6** — **Given** tests qualité sur corpus test (10 queries ESG FR + 5 queries EUDR EN), **When** `pytest backend/tests/test_core/test_embeddings_quality.py` exécuté, **Then** `recall@5` Voyage **≥ baseline OpenAI** (régression qualité refusée) **And** latence p95 < 2 s par batch de 100 textes.

**AC7** — **Given** observabilité (Story 9.7 instrumentation), **When** `EmbeddingProvider.embed()` est invoquée, **Then** `tool_call_logs` enregistre `duration_ms`, `tokens_used`, `cost_usd`, `provider`, `model` par appel.

**AC8** — **Given** la documentation, **When** `docs/CODEMAPS/rag.md` est mise à jour + `.env.example` comporte `VOYAGE_API_KEY=<placeholder>`, **Then** un dev onboarding peut switcher OpenAI ↔ Voyage en modifiant uniquement l'env **And** les tests de qualité CI valident la parité avant promotion.

**AC9** — **Given** bench comparatif 3 providers LLM × 5 tools représentatifs Phase 0 (scope R-04-1 readiness 2026-04-19 + `business-decisions-2026-04-19.md`), **When** `scripts/bench_llm_providers.py` exécuté, **Then** il mesure latence p95/p99 + coût par tool call (€ / 1000 tokens input+output) + qualité output (150 échantillons = 10 par tool × 3 providers) pour les 3 providers suivants : **(a) Anthropic via OpenRouter** (baseline si migration vers Claude), **(b) Anthropic direct** (`api.anthropic.com`, vérifier si l'absence d'intermédiaire améliore latence/coût), **(c) MiniMax (`minimax/minimax-m2.7`) via OpenRouter** [baseline actuelle `.env` du projet, valide si MiniMax tient la charge vs Claude], sur les 5 tools : `generate_formalization_plan`, `query_cube_4d`, `derive_verdicts_multi_ref`, `generate_action_plan`, `generate_executive_summary`. Qualité scorée sur 4 axes : (1) respect format structuré (Pydantic schema valid), (2) cohérence numérique avec données source (pas d'hallucinations chiffres), (3) respect vocabulaire interdit (guards LLM Story 9.6), (4) qualité rédactionnelle FR avec accents (é è ê à ç ù). Livrable `docs/bench-llm-providers-phase0.md` avec recommandation provider primaire MVP + fallback configuré dans `LLMProvider` abstraction (Décision D10 architecture). **Décision finale actée avant Sprint 1 Phase 1.**

---

### Story 10.8 : Framework d'injection unifié de prompts (CCC-9)

**As a** Équipe Mefali (backend/AI),
**I want** un framework `backend/app/prompts/registry.py` qui collecte automatiquement les instructions transverses (style concis spec 014, routing spec 013, guided tour spec 019, widgets spec 018, etc.) et les injecte dans chaque prompt module via un builder `build_prompt(module, variables)`,
**So that** les 4 spec-correctifs historiques (013/015/016/017) ne se reproduisent plus sous forme de patches éparpillés à travers `prompts/` (anti-pattern « prompts directifs » saturés).

**Metadata (CQ-8)**
- `fr_covered`: [] (support FR45–FR50 Copilot)
- `nfr_covered`: [NFR61, NFR62, NFR64]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 9.7]
- `architecture_alignment`: CCC-9 (framework injection unifié)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/prompts/registry.py` créé, **When** il est chargé, **Then** il expose un registre `INSTRUCTION_REGISTRY` qui liste toutes les instructions transverses (style, widgets, tour, routing, rate limit, etc.) avec `applies_to=["chat", "esg_scoring", …]` et ordre déterministe.

**AC2** — **Given** `build_prompt(module, variables)`, **When** invoquée pour `module="esg_scoring"`, **Then** elle retourne le prompt final avec les instructions applicables injectées dans l'ordre registry (déterministe + testable).

**AC3** — **Given** les 9 modules `prompts/*.py` existants (chat, esg_scoring, carbon, financing, applications, credit, action_plan, guided_tour, system), **When** audités post-refactor, **Then** chacun consomme `build_prompt()` **And** aucun `STYLE_INSTRUCTION` ou `WIDGET_INSTRUCTION` n'est dupliqué en dur entre modules.

**AC4** — **Given** l'ajout d'une nouvelle instruction transverse (cas futur), **When** un dev modifie uniquement le registre, **Then** tous les modules concernés en bénéficient sans toucher leur fichier `prompts/<module>.py`.

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_prompts/test_registry.py` + `test_build_prompt.py` exécutés, **Then** scénarios (applies_to filtrage, ordre déterministe, variable substitution, module inconnu → erreur explicite) tous verts **And** coverage ≥ 85 %.

**AC6** — **Given** les golden tests sur les prompts générés, **When** exécutés, **Then** les snapshots post-refactor des 9 modules sont identiques ou supérieurs aux pré-refactor (zéro régression sémantique).

---

### Story 10.9 : Feature flag `ENABLE_PROJECT_MODEL` (simple var env + wrapper)

**As a** Équipe Mefali (DX/SRE),
**I want** un feature flag unique `ENABLE_PROJECT_MODEL=true|false` via variable d'environnement + wrapper `backend/app/core/feature_flags.py::is_project_model_enabled()`, **sans** librairie externe (Flipper/Unleash/LaunchDarkly),
**So that** la migration brownfield vers le modèle `Company × Project` (Cluster A) puisse être activée/désactivée sans redéploiement pendant la Phase 1, et que le cleanup (NFR63 + RT-3 + CQ-10) soit trivial fin Phase 1 (story 20.1).

**Metadata (CQ-8)**
- `fr_covered`: [] (infra support FR4–FR10)
- `nfr_covered`: [NFR63]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: S
- `depends_on`: [Story 10.2]
- `architecture_alignment`: Clarification 5 (feature flag simple)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/feature_flags.py`, **When** auditée, **Then** elle contient une seule fonction `is_project_model_enabled() -> bool` lisant `ENABLE_PROJECT_MODEL` depuis l'env (défaut `false` en MVP jusqu'à bascule).

**AC2** — **Given** les endpoints `projects/` (Story 10.2 + Epic 11 livrés), **When** `ENABLE_PROJECT_MODEL=false`, **Then** les routes retournent 404 **And** le modèle `Company × Project` reste masqué côté UI (feature gate).

**AC3** — **Given** `ENABLE_PROJECT_MODEL=true`, **When** une PME crée son 1ᵉʳ projet, **Then** la bascule est transparente pour les autres PME non migrées (par-tenant éventuel : documenter si opt-in individuel ou global).

**AC4** — **Given** aucune librairie externe n'est installée, **When** `pip list` exécuté, **Then** aucun `flipper-client`, `unleash-client`, `launchdarkly-server-sdk` (Clarification 5 respectée).

**AC5** — **Given** la story 20.1 cleanup exécutée fin Phase 1, **When** le feature flag est retiré, **Then** toutes les occurrences `is_project_model_enabled()` dans le code sont supprimées **And** la variable d'env disparaît des manifests.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_core/test_feature_flags.py` exécuté, **Then** scénarios (flag off masque routes, flag on active routes, toggle live sans redeploy en DEV) tous verts.

---

### Story 10.10 : Micro-Outbox `domain_events` + worker batch 30 s

**As a** Équipe Mefali (backend),
**I want** une table `domain_events(id, event_type, aggregate_type, aggregate_id, payload, status, created_at, processed_at)` + un worker FastAPI tournant toutes les 30 s qui consomme les events `pending`, les traite de manière idempotente, et marque `processed` ou `failed` avec retry exponentiel,
**So that** les effets de bord transactionnels (notifications SSE, invalidation de cache, mise à jour d'agrégats dérivés ESG, événements inter-module) soient atomiquement cohérents avec les transactions métier (CCC-14) et que la queue async Story 9.10 consomme ce pattern.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR30, NFR37, NFR75]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: L
- `depends_on`: [Story 10.1 (migration qui introduit `domain_events`), Story 9.7]
- `architecture_alignment`: Décision 11 + CCC-14 (micro-Outbox MVP, pas de Celery)
- `consumed_by`: [Story 9.10, Epic 13 invalidation cache ESG AR-D3, Epic 14 snapshot events AR-D5]

**Acceptance Criteria**

**AC1** — **Given** migration `domain_events` appliquée, **When** auditée, **Then** elle porte un index composite `(status, created_at)` pour le worker qui consomme par batch **And** un index sur `(aggregate_type, aggregate_id)` pour reporting.

**AC2** — **Given** une opération métier atomique (ex. `Report.save()`), **When** exécutée dans une transaction, **Then** l'insert de l'event `domain_events(...)` est **dans la même transaction SQLAlchemy** (pas de scheduling externe — pattern Outbox strict CCC-14).

**AC3** — **Given** le worker `domain_events_worker.py` scheduled via **`APScheduler` intégré FastAPI**, **When** lancé, **Then** il exécute toutes les 30 s un batch de max 100 events `pending` triés `created_at ASC` **via `SELECT … FOR UPDATE SKIP LOCKED`** (verrou PostgreSQL natif garantissant l'idempotence multi-replicas sans coordination externe) **And** traite chaque event de manière idempotente (handler par `event_type`). **Documentation architecturale** : `APScheduler + FOR UPDATE SKIP LOCKED` est le pattern MVP ; la migration vers AWS EventBridge Phase Growth se fait **sans refactor Outbox** (seul le trigger change, la table + handlers restent identiques).

**AC4** — **Given** un event échoue (handler lève exception), **When** le worker retry, **Then** 3 tentatives max avec backoff (30 s, 2 min, 10 min) **And** marque `status='failed'` avec message après 3 échecs **And** alerting admin (NFR40).

**AC5** — **Given** un event avec un handler non enregistré, **When** consommé, **Then** il est marqué `failed` immédiatement avec raison `unknown_event_type` (fail-fast + alerting plutôt que re-queue infini).

**AC6** — **Given** le worker en DEV avec `DOMAIN_EVENTS_WORKER_ENABLED=false`, **When** l'app démarre, **Then** le worker est désactivé (permet debug ciblé).

**AC7** — **Given** les tests, **When** `pytest backend/tests/test_core/test_domain_events.py` exécuté, **Then** scénarios (atomicité transaction, batch 100, retry exponentiel, idempotence redelivery, event inconnu fail-fast, alerting on failure) tous verts **And** coverage ≥ 85 % (code critique NFR60).

---

### Story 10.11 : Sourcing documentaire Annexe F + CI nightly `source_url` HTTP 200

**As a** Admin Mefali + System,
**I want** compléter le sourcing documentaire obligatoire (Annexe F PRD : GCF, FEM, Proparco, BOAD SSI, BAD SSI, Banque Mondiale ESF, DFI Harmonized, Rainforest Alliance, Fairtrade, Bonsucro, FSC, IRMA, ResponsibleSteel, GRI, TCFD/ISSB, CDP, SASB, GIIN IRIS+) et activer une CI nightly qui teste HTTP 200 sur toutes les `source_url` du catalogue,
**So that** FR62 (entité DRAFT non-publiable sans source) soit enforçable **avec du contenu réel** (vs catalogue vide) et que FR63 (CI nightly) soit opérationnelle avant la première publication de référentiels en Epic 13.

**Metadata (CQ-8)**
- `fr_covered`: [FR62, FR63]
- `nfr_covered`: [NFR27, NFR40]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: M
- `depends_on`: [Story 10.1 (migration 025)]

**Acceptance Criteria**

**AC1** — **Given** les 22+ sources Annexe F, **When** le seed initial du catalogue est exécuté, **Then** chaque entité (référentiel, pack, template) porte obligatoirement `source_url`, `source_accessed_at` (date ISO), `source_version` **And** FR62 enforcement bloque toute publication d'entité sans ces champs.

**AC2** — **Given** la CI nightly `source_url_health_check.yml`, **When** exécutée chaque nuit, **Then** elle teste HTTP 200 sur toutes les `source_url` du catalogue **And** toute URL retournant HTTP ≠ 200 déclenche un ticket ou alerting admin (NFR40) **And** un rapport consolidé est publié dans un canal d'équipe.

**AC3** — **Given** une source déplacée (redirect 3xx), **When** détectée, **Then** elle est consignée comme `warning` (pas fail) mais requiert une action admin pour mettre à jour l'URL canonique.

**AC4** — **Given** une source inaccessible intermittent, **When** 3 runs consécutifs échouent, **Then** l'entité passe automatiquement en état `source_unreachable` (visible dans l'UI admin) **And** un badge apparaît sur l'entité pour informer les users PME.

**AC5** — **Given** l'audit annuel sécurité (NFR18), **When** mené, **Then** un rapport d'état du sourcing catalogue est fourni (pourcentage sources valides, âge moyen depuis `source_accessed_at`, sources en `source_unreachable`).

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/test_source_tracking.py` exécuté, **Then** scénarios (FR62 blocage sans source, FR63 CI check, redirect warning, transition `source_unreachable`) tous verts.

---

### Story 10.12 : Audit trail catalogue (migration 026 + endpoints admin)

**As a** Admin Mefali,
**I want** un audit trail complet et immuable des modifications catalogue (who / what entity / when / before / after values) via table `admin_catalogue_audit_trail` (migration 026) + endpoint `/api/admin/catalogue/audit-trail` avec UI dédiée,
**So that** FR64 (rétention 5 ans minimum + UI consultation) soit opérationnelle avant que les Admins modifient des référentiels en Epic 13, et que le respect NFR28 (audit trail immuable) puisse être vérifié au pen test externe.

**Metadata (CQ-8)**
- `fr_covered`: [FR64]
- `nfr_covered`: [NFR20, NFR28]
- `phase`: 0
- `cluster`: Fondations
- `estimate`: M
- `depends_on`: [Story 10.1 (migration 026), Story 10.4 (module admin_catalogue)]

**Acceptance Criteria**

**AC1** — **Given** table `admin_catalogue_audit_trail` (migration 026), **When** auditée, **Then** elle porte `actor_id`, `entity_type`, `entity_id`, `action` (`create`/`update`/`delete`/`publish`), `before` JSONB, `after` JSONB, `timestamp`, `request_id` (NFR37 traçabilité) **And** aucune colonne permettant update/delete au niveau applicatif (append-only — trigger PostgreSQL enforcement).

**AC2** — **Given** un `admin_mefali` modifie une entité catalogue, **When** la modification est persistée, **Then** une ligne `audit_trail` est insérée dans **la même transaction** que la modification (atomicité CCC-14) **And** l'événement est aussi émis dans `domain_events` pour consumers éventuels.

**AC3** — **Given** l'endpoint `GET /api/admin/catalogue/audit-trail?entity_type=fund&entity_id=X`, **When** appelé par `admin_mefali`, **Then** il retourne l'historique chronologique avec diff rendue côté frontend.

**AC4** — **Given** la rétention, **When** vérifiée par le job de purge, **Then** aucune ligne `audit_trail` n'est supprimée avant 5 ans (NFR20) **And** archivage froid S3 Glacier envisageable Phase Growth (documenté).

**AC5** — **Given** le pen test externe (Story 20.3), **When** un attaquant tente `UPDATE` ou `DELETE` sur `audit_trail` via l'appli, **Then** la BD refuse (trigger) **And** l'incident est loggé comme tentative de compromission.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/test_audit_trail.py` exécuté, **Then** scénarios (insert atomique, append-only enforcement, query par entité, diff before/after, rétention 5 ans policy) tous verts **And** coverage ≥ 85 % (code critique NFR60).

---

### Story 10.14 : Setup Storybook partiel + 6 stories à gravité

**As a** Équipe Mefali (frontend/design system),
**I want** un Storybook Vue 3 + Vite installé avec addons `a11y` et `interactions`, documentant les 6 composants à gravité transverses (`SignatureModal`, `SourceCitationDrawer`, `ReferentialComparisonView`, `ImpactProjectionPanel`, `SectionReviewCheckpoint`, `SgesBetaBanner`),
**So that** les composants à gravité (moments légalement/émotionnellement critiques : signature FR40, citations sources FR71, vue comparative FR26, Terraform Plan Q14, review > 50k USD FR41, SGES BETA FR44) soient documentés avec leurs états + variants + accessibilité temps réel, conformément UX Step 11 section 5.1 et Q16 (Storybook partiel pour les 8 à gravité uniquement, pas full design system MVP).

**Metadata (CQ-8)**
- `fr_covered`: [] (socle UI, NFR-only)
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: L
- `qo_rattachees`: []
- `depends_on`: [10.8 framework prompts CCC-9]
- `architecture_alignment`: UX Step 11 Q16 (Storybook partiel), Step 8 tokens `@theme`, Q15 Reka UI, Q20 Lucide

**Acceptance Criteria**

**AC1** — **Given** `frontend/.storybook/`, **When** auditée, **Then** elle contient `main.ts` avec `framework: '@storybook/vue3-vite'` + `addons: ['@storybook/addon-a11y', '@storybook/addon-interactions', '@storybook/addon-essentials']` **And** `preview.ts` charge les tokens `@theme` via `frontend/app/assets/css/main.css` + toggle dark mode global.

**AC2** — **Given** `npm run storybook`, **When** exécuté, **Then** Storybook démarre sur port 6006 **And** l'arborescence expose exactement 6 stories `Gravity/SignatureModal`, `Gravity/SourceCitationDrawer`, `Gravity/ReferentialComparisonView`, `Gravity/ImpactProjectionPanel`, `Gravity/SectionReviewCheckpoint`, `Gravity/SgesBetaBanner` (les 2 autres du lot « 8 composants à gravité » — `FormalizationPlanCard` et `RemediationFlowPage` — restent hors Storybook MVP selon Q16).

**AC3** — **Given** chaque story Storybook, **When** ouverte, **Then** elle expose au minimum les états documentés dans UX Step 11 section « Custom Components » (ex. pour `SignatureModal` : `initial`, `ready`, `signing`, `signed`, `error` ; pour `SourceCitationDrawer` : `closed`, `opening`, `open`, `loading`, `error`, `closing`) **And** chaque état est testable via contrôles Storybook (props) sans recompilation.

**AC4** — **Given** l'addon `addon-a11y`, **When** chaque story est visualisée, **Then** l'audit axe-core intégré Storybook s'exécute et remonte `0 violation` WCAG 2.1 AA (contrastes, ARIA roles, navigation clavier) **And** les violations sont bloquantes en CI (`npm run storybook:test` échoue sur violations).

**AC5** — **Given** l'addon `addon-interactions`, **When** chaque story expose un `play()` function, **Then** les interactions clavier critiques sont testées (Escape ferme `SignatureModal`, Tab trap dans `SourceCitationDrawer`, arrow keys dans `ReferentialComparisonView` cellules, etc.) **And** `npm run storybook:test-runner` valide les 6 composants.

**AC6** — **Given** le build statique `npm run storybook:build`, **When** exécuté, **Then** il produit `storybook-static/` déployable sur un static host (GitHub Pages / Vercel) **And** la taille du build reste < 15 MB (budget NFR7 : documentation interne, pas de dette poids sur le frontend prod).

**AC7** — **Given** les tests Vitest, **When** `npm run test` exécuté, **Then** chaque composant à gravité expose au minimum 3 tests (rendu par défaut, transitions d'état principales, accessibilité basique via `@testing-library/vue` + `jest-axe`) **And** coverage ≥ 80 % sur `frontend/app/components/gravity/*.vue`.

**AC8** — **Given** `prefers-reduced-motion: reduce`, **When** les 6 composants sont rendus dans Storybook avec ce paramètre système, **Then** toutes les animations sont désactivées ou réduites à une transition opacity simple (WCAG 2.3.3, respect CLAUDE.md dark mode + accessibilité).

---

### Story 10.15 : `ui/Button.vue` — 4 variantes primary/secondary/ghost/danger

**As a** Équipe Mefali (frontend),
**I want** un composant `frontend/app/components/ui/Button.vue` typé avec 4 variantes (`primary` / `secondary` / `ghost` / `danger`), 3 tailles (`sm` / `md` / `lg`), état `loading` (spinner inline), état `disabled`, support `icon` (slot leading/trailing), props `type` (button/submit/reset), `aria-label` obligatoire si pas de texte,
**So that** tous les boutons du produit (CTA Aminata, admin catalogue, signature FR40, « Demander une revue » SGES, navigation copilot, etc.) partagent une implémentation unique et accessible, et que la règle CLAUDE.md « discipline > 2 fois » soit enforcée dès Phase 0.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: S
- `qo_rattachees`: []
- `depends_on`: []
- `architecture_alignment`: UX Step 11 section 4 P0, Step 8 tokens `@theme`, CLAUDE.md réutilisabilité

**Acceptance Criteria**

**AC1** — **Given** `frontend/app/components/ui/Button.vue`, **When** auditée, **Then** elle expose `defineProps<{ variant?: 'primary'|'secondary'|'ghost'|'danger'; size?: 'sm'|'md'|'lg'; loading?: boolean; disabled?: boolean; type?: 'button'|'submit'|'reset' }>()` avec defaults `variant='primary'` + `size='md'` + `type='button'`.

**AC2** — **Given** les 4 variantes, **When** rendues côte à côte, **Then** elles utilisent exclusivement les tokens `@theme` (aucun hex hardcodé) : `primary=--color-brand-green`, `secondary=--color-surface-bg + border`, `ghost=transparent`, `danger=--color-brand-red` **And** dark mode rendu via variantes `dark:` Tailwind sur tous les éléments (fond, texte, bordure, hover, focus).

**AC3** — **Given** la taille `md` sur mobile (Aminata path, layout `aminata-mobile.vue`), **When** mesurée, **Then** la hauteur effective est ≥ 44 px (WCAG 2.5.5 touch target minimum) **And** la taille `sm` reste ≥ 44 px en touch (padding interne ajusté, pas de réduction sous seuil).

**AC4** — **Given** l'état `loading=true`, **When** le bouton est rendu, **Then** un spinner inline remplace le slot text (aria-hidden), `aria-busy="true"` + `disabled="true"` sont appliqués, le slot text est préservé pour lecteurs d'écran via `aria-label` de fallback **And** le clic est bloqué.

**AC5** — **Given** un bouton sans texte (icon-only), **When** audité, **Then** il exige `aria-label` via prop typé (erreur TypeScript si absent) — enforcement compile-time.

**AC6** — **Given** `prefers-reduced-motion: reduce`, **When** l'utilisateur hover / focus / click, **Then** les transitions sont réduites à une simple opacity step (pas de scale, pas de translate) **And** le spinner `loading` utilise une animation CSS simple (rotation ≤ 0,5 tour/s).

**AC7** — **Given** les tests Vitest `frontend/tests/components/ui/Button.test.ts`, **When** `npm run test` exécuté, **Then** minimum 3 tests verts : (1) rendu par défaut + variante custom, (2) états `loading` + `disabled`, (3) accessibilité axe-core (`expect(wrapper).toHaveNoViolations()`) **And** coverage ≥ 90 % sur `Button.vue`.

**AC8** — **Given** l'usage dans Storybook (si présent hors lot gravité — optionnel), **When** ajouté, **Then** il expose les 4 variantes × 3 tailles + états loading/disabled comme grille d'exemples.

---

### Story 10.16 : `ui/Input.vue` + `ui/Textarea.vue` + `ui/Select.vue`

**As a** Équipe Mefali (frontend),
**I want** 3 composants `frontend/app/components/ui/Input.vue`, `ui/Textarea.vue`, `ui/Select.vue` — chacun avec label accessible, message d'erreur inline, compteur caractères (`Textarea` uniquement, borne 400 chars conformément spec 018 AC5), placeholder, prop `required`, support dark mode complet,
**So that** tous les formulaires du produit (profil Company, `FormalizationPlanCard` CTAs, admin catalogue, `BeneficiaryProfileBulkImport`, `JustificationField` copilot, etc.) partagent des primitives cohérentes et accessibles, et que les validations Q17 batch composite aient un socle uniforme.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: M
- `qo_rattachees`: []
- `depends_on`: []
- `architecture_alignment`: UX Step 11 section 4 P0/P1, Step 8 tokens `@theme`, spec 018 AC5 (400 chars borne justification)

**Acceptance Criteria**

**AC1** — **Given** les 3 composants, **When** audités, **Then** chacun expose `defineProps<{ modelValue: string; label: string; error?: string; required?: boolean; disabled?: boolean; placeholder?: string; id?: string }>()` **And** émet `update:modelValue` pour support `v-model`.

**AC2** — **Given** un `<label>` associé, **When** inspecté en DOM, **Then** `<label for="...">` pointe vers `id` de l'input (auto-généré si non fourni), `aria-required="true"` si `required`, `aria-invalid="true"` + `aria-describedby` pointant vers message d'erreur si `error` présent.

**AC3** — **Given** `ui/Textarea.vue` avec prop `maxLength=400`, **When** rendu, **Then** un compteur `${value.length}/400` apparaît sous le champ (respect spec 018 AC5 défense en profondeur côté client) **And** le texte au-delà de 400 est tronqué ou empêché (comportement documenté).

**AC4** — **Given** dark mode activé (classe `dark` sur `<html>`), **When** les 3 composants sont rendus, **Then** fond/texte/bordure/placeholder utilisent les tokens `dark:bg-dark-input` + `dark:text-surface-dark-text` + `dark:border-dark-border` + `dark:placeholder-gray-500` conformément CLAUDE.md dark mode obligatoire.

**AC5** — **Given** `ui/Select.vue`, **When** implémenté, **Then** il est un wrapper minimal de Reka UI `<SelectRoot>` stylé Tailwind (pas de `<select>` natif non stylable cross-browser) **And** supporte les props `options: Array<{ value: string; label: string; disabled?: boolean }>`.

**AC6** — **Given** un message d'erreur `error="Ce champ est obligatoire"`, **When** affiché, **Then** il est rendu sous le champ avec `--color-brand-red` + icône Lucide `AlertCircle` (pas de couleur seule — conformément Règle 11 Custom Pattern) + rôle `role="alert"` pour lecteurs d'écran.

**AC7** — **Given** touch mobile, **When** les champs sont ciblés, **Then** la hauteur effective est ≥ 44 px (WCAG 2.5.5) **And** le clavier virtuel iOS/Android utilise `inputmode` approprié si la prop le requiert (ex. `inputmode="numeric"` pour montants FCFA).

**AC8** — **Given** les tests Vitest `frontend/tests/components/ui/`, **When** exécutés, **Then** minimum 3 tests par composant (rendu + label associé, v-model bidirectionnel, état erreur + axe-core sans violation) **And** coverage ≥ 85 % sur les 3 composants.

---

### Story 10.17 : `ui/Badge.vue` tokens sémantiques (lifecycle FA + verdicts ESG + criticité admin)

**As a** Équipe Mefali (frontend),
**I want** un composant `frontend/app/components/ui/Badge.vue` avec variantes sémantiques pré-définies couvrant (a) 7 états lifecycle `FundApplication` (FR32), (b) 4 verdicts ESG `PASS`/`FAIL`/`REPORTED`/`N/A` (Q21 + QO-B3), (c) 3 niveaux criticité admin `N1`/`N2`/`N3`, chaque variante combinant icône Lucide + couleur token + texte (jamais couleur seule, Règle 11 Custom Pattern UX Step 12),
**So that** les indicateurs visuels d'état soient cohérents transversalement (`FundApplicationLifecycleBadge`, `ComplianceBadge`, `AdminCatalogueEditor`, sidebar compacte) et accessibles aux utilisateurs daltoniens ou sous mode monochrome.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: S
- `qo_rattachees`: []
- `depends_on`: [10.21 EsgIcon + Lucide setup]
- `architecture_alignment`: UX Step 11 section 4 P0, Step 12 Règle 11 Custom Pattern (couleur jamais seule), Q21 verdicts ESG

**Acceptance Criteria**

**AC1** — **Given** `frontend/app/components/ui/Badge.vue`, **When** auditée, **Then** elle expose `defineProps<{ variant: BadgeVariant; label?: string; size?: 'sm'|'md' }>()` où `BadgeVariant` est un union type littéral couvrant : **lifecycle FA** (`fa-draft` / `fa-snapshot-frozen` / `fa-signed` / `fa-exported` / `fa-submitted` / `fa-in-review` / `fa-accepted-rejected-withdrawn`), **verdicts ESG** (`verdict-pass` / `verdict-fail` / `verdict-reported` / `verdict-na`), **criticité admin** (`admin-n1` / `admin-n2` / `admin-n3`).

**AC2** — **Given** chaque variante, **When** rendue, **Then** elle combine **3 signaux redondants** (Règle 11) : (1) token couleur `--color-fa-*` / `--color-verdict-*` / `--color-admin-*`, (2) icône Lucide ou `EsgIcon` contextuelle (ex. `CheckCircle` pour `verdict-pass`, `XCircle` pour `verdict-fail`, `AlertTriangle` pour `verdict-reported`, `Minus` pour `verdict-na`), (3) texte label court en français (ex. « Validé », « Non conforme », « À documenter », « Non applicable »).

**AC3** — **Given** le verdict `PASS` conditionnel (Q21 clarification post-Lot 4), **When** variante `verdict-pass` est rendue avec prop `conditional=true`, **Then** le label devient italique `Validé (conditionnel)` conformément UX Step 11 `ComplianceBadge` italic PASS conditionnel.

**AC4** — **Given** dark mode activé, **When** chaque variante est rendue, **Then** le contraste texte/fond reste ≥ 4.5:1 (WCAG 1.4.3 AA) **And** les tokens `dark:` sont appliqués sur fond + texte + bordure.

**AC5** — **Given** le mode monochrome / daltonisme simulé (outil dev), **When** les badges sont visualisés, **Then** les 3 états lifecycle FA critiques (`fa-signed`, `fa-in-review`, `fa-rejected`) restent distinguables grâce à icône + texte même sans couleur (enforcement Règle 11).

**AC6** — **Given** les tests Vitest, **When** `npm run test` exécuté, **Then** minimum 3 tests verts : (1) rendu de chaque variante avec icône + label corrects, (2) mode conditional PASS italique, (3) axe-core sans violation sur les 14 variantes **And** coverage ≥ 85 %.

---

### Story 10.18 : `ui/Drawer.vue` wrapper Reka UI Dialog (variant side)

**As a** Équipe Mefali (frontend),
**I want** un composant `frontend/app/components/ui/Drawer.vue` wrapper de Reka UI `<DialogRoot>` en variant side (panneau latéral droit), largeur fixe 480 px desktop / plein écran mobile (< 768 px), scrollable via Reka UI `<ScrollArea>`, focus trap natif, fermeture Escape, overlay semi-transparent,
**So that** tous les drawers du produit (`SourceCitationDrawer` FR71, `IntermediaryComparator` Moussa, `PeerReviewThreadedPanel` admin N2, drawers filtres catalogue) partagent une base accessible ARIA et responsive unique.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: M
- `qo_rattachees`: []
- `depends_on`: []
- `architecture_alignment`: UX Step 11 section 4 P0, Q15 Reka UI, UX spec `SourceCitationDrawer`

**Acceptance Criteria**

**AC1** — **Given** `frontend/app/components/ui/Drawer.vue`, **When** auditée, **Then** elle utilise Reka UI `<DialogRoot>` + `<DialogPortal>` + `<DialogContent>` + `<DialogOverlay>` **And** expose `defineProps<{ open: boolean; title: string; ariaLabel?: string }>()` + émet `update:open`.

**AC2** — **Given** la largeur du drawer, **When** mesurée, **Then** elle vaut exactement 480 px en viewport desktop (≥ 768 px) **And** 100 vw + 100 vh en viewport mobile (< 768 px) avec transition slide-in depuis la droite (desktop) ou bottom (mobile).

**AC3** — **Given** le focus à l'ouverture, **When** drawer ouvert, **Then** focus trap natif Reka UI actif (Tab reste dans le drawer), focus initial sur le premier élément focusable (bouton fermeture ou premier champ), Escape ferme le drawer **And** focus restauré sur le déclencheur à la fermeture.

**AC4** — **Given** l'attribut ARIA, **When** inspecté, **Then** le conteneur porte `role="complementary"` (panneau latéral contextuel) + `aria-label` ou `aria-labelledby` pointant vers le titre + `aria-modal="true"` sur l'overlay.

**AC5** — **Given** le contenu scrollable, **When** dépasse la hauteur viewport, **Then** Reka UI `<ScrollArea>` est utilisé (scrollbar stylée, pas de scrollbar native cross-browser inconsistant) **And** header + footer éventuel restent sticky.

**AC6** — **Given** dark mode activé, **When** drawer rendu, **Then** fond `dark:bg-dark-card`, texte `dark:text-surface-dark-text`, bordure `dark:border-dark-border`, overlay `dark:bg-black/60` **And** contraste ≥ 4.5:1 sur tous les textes.

**AC7** — **Given** `prefers-reduced-motion: reduce`, **When** drawer s'ouvre, **Then** la transition slide est remplacée par un fade opacity ≤ 200 ms (pas de translate).

**AC8** — **Given** les tests Vitest, **When** exécutés, **Then** minimum 3 tests verts : (1) ouverture/fermeture via `update:open`, (2) Escape ferme + focus restauré, (3) axe-core sans violation **And** coverage ≥ 85 %.

---

### Story 10.19 : `ui/Combobox.vue` + `ui/Tabs.vue` wrappers Reka UI

**As a** Équipe Mefali (frontend),
**I want** deux composants `frontend/app/components/ui/Combobox.vue` (wrapper Reka UI `<ComboboxRoot>` avec support single + multi-select) et `frontend/app/components/ui/Tabs.vue` (wrapper Reka UI `<TabsRoot>` avec styling Tailwind + tokens `@theme`),
**So that** les filtres catalogue (référentiels actifs, pack sélecteur, sélection intermédiaires multi-pays Moussa) et la navigation multi-vue (`ReferentialComparisonView` tabs Vue comparative / Détail par règle / Historique, dashboard multi-projets Moussa, onglets admin N1/N2/N3) partagent des primitives cohérentes accessibles ARIA.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: M
- `qo_rattachees`: []
- `depends_on`: []
- `architecture_alignment`: UX Step 11 section 3 Reka UI primitives + section 4 P1, Q15 Reka UI

**Acceptance Criteria**

**AC1** — **Given** `ui/Combobox.vue`, **When** auditée, **Then** elle utilise Reka UI `<ComboboxRoot>` + `<ComboboxInput>` + `<ComboboxList>` + `<ComboboxItem>` **And** expose `defineProps<{ modelValue: string | string[]; options: Array<{ value: string; label: string }>; multiple?: boolean; placeholder?: string; label: string }>()`.

**AC2** — **Given** `multiple=true`, **When** l'utilisateur sélectionne plusieurs options, **Then** les valeurs sélectionnées s'affichent comme `Badge` (réutilisation `ui/Badge.vue` 10.17) dans la zone d'input avec bouton « × » par item (touch ≥ 44 px mobile) **And** `modelValue` est un `string[]`.

**AC3** — **Given** `ui/Tabs.vue`, **When** auditée, **Then** elle utilise Reka UI `<TabsRoot>` + `<TabsList>` + `<TabsTrigger>` + `<TabsContent>` **And** expose `defineProps<{ modelValue: string; tabs: Array<{ value: string; label: string; icon?: Component }> }>()` avec support slot `content-${value}` par onglet.

**AC4** — **Given** dark mode activé, **When** les 2 composants sont rendus, **Then** tous les éléments utilisent les tokens `@theme` (fond, texte, bordure, hover, focus, active tab indicator) avec variantes `dark:` **And** contraste ≥ 4.5:1.

**AC5** — **Given** l'accessibilité, **When** inspectée, **Then** Combobox expose `role="combobox" aria-expanded aria-controls aria-activedescendant` (fournis par Reka UI) **And** Tabs expose `role="tablist" role="tab" role="tabpanel" aria-selected` conformément WAI-ARIA Authoring Practices.

**AC6** — **Given** la navigation clavier, **When** testée, **Then** Combobox supporte ↑ ↓ Home End Enter Escape + recherche par caractère tapé **And** Tabs supporte ← → Home End pour naviguer entre onglets avec cycle infini (focus wrap).

**AC7** — **Given** `prefers-reduced-motion: reduce`, **When** l'active tab change, **Then** l'indicateur underline se déplace sans animation (position change immédiate) **And** les dropdowns Combobox n'utilisent pas d'animation slide.

**AC8** — **Given** les tests Vitest, **When** exécutés, **Then** minimum 3 tests par composant (rendu + v-model, navigation clavier, axe-core sans violation) **And** coverage ≥ 85 % sur les 2 composants.

---

### Story 10.20 : `ui/DatePicker.vue`

**As a** Équipe Mefali (frontend),
**I want** un composant `frontend/app/components/ui/DatePicker.vue` basé sur Reka UI `<PopoverRoot>` + calendrier mensuel navigable clavier, format date localisé français (`JJ/MM/AAAA`) + stockage ISO-8601 (`YYYY-MM-DD`), support plage `min`/`max`, état erreur inline,
**So that** la sélection de date (`effective_date` admin N3 FR32, deadlines `FundApplication` FR32, dates de rappels action plan, `source_accessed_at` admin catalogue) soit cohérente, accessible et évite la fragmentation des `<input type="date">` natifs non stylable cross-browser.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: M
- `qo_rattachees`: []
- `depends_on`: [10.16 ui/Input, 10.21 Lucide icons]
- `architecture_alignment`: UX Step 11 section 4 P2, Q15 Reka UI Popover, Step 8 format date français

**Acceptance Criteria**

**AC1** — **Given** `frontend/app/components/ui/DatePicker.vue`, **When** auditée, **Then** elle expose `defineProps<{ modelValue: string | null; label: string; min?: string; max?: string; required?: boolean; error?: string; disabled?: boolean }>()` avec `modelValue` au format ISO-8601 (`YYYY-MM-DD`) **And** émet `update:modelValue`.

**AC2** — **Given** le trigger d'ouverture, **When** cliqué, **Then** il utilise `ui/Input.vue` (réutilisation 10.16) en lecture seule affichant le format `JJ/MM/AAAA` (locale `fr-FR`) + icône `Calendar` Lucide à droite **And** touche Entrée ou Espace ouvre le popover calendrier.

**AC3** — **Given** le popover calendrier, **When** ouvert, **Then** il utilise Reka UI `<PopoverRoot>` + `<PopoverContent>` avec focus trap + Escape ferme **And** affiche un mois navigable (flèches ← → mois précédent/suivant, clic sur année pour sélectionner rapidement).

**AC4** — **Given** la navigation clavier dans le calendrier, **When** testée, **Then** ← → ↑ ↓ naviguent entre jours, Home/End début/fin de semaine, PageUp/PageDown mois précédent/suivant, Shift+PageUp/PageDown année précédente/suivante, Enter sélectionne la date focusée (conformité WAI-ARIA Date Picker Dialog pattern).

**AC5** — **Given** les bornes `min`/`max`, **When** positionnées, **Then** les jours hors plage sont rendus avec `aria-disabled="true"` + opacité réduite + non-focusables **And** le message d'erreur inline (si `error`) suit le pattern `ui/Input.vue` (icône + texte, rôle `role="alert"`).

**AC6** — **Given** dark mode activé, **When** calendrier ouvert, **Then** fond `dark:bg-dark-card`, jours `dark:text-surface-dark-text`, jour sélectionné `bg-brand-green text-white dark:bg-brand-green-dark`, hover `dark:hover:bg-dark-hover` **And** contraste ≥ 4.5:1.

**AC7** — **Given** mobile touch, **When** calendrier ouvert, **Then** chaque cellule jour a une taille effective ≥ 44 px (WCAG 2.5.5) **And** le popover s'ajuste au viewport (pas de débordement horizontal).

**AC8** — **Given** les tests Vitest, **When** exécutés, **Then** minimum 3 tests verts : (1) rendu + format français + parsing ISO bidirectionnel, (2) navigation clavier (← → ↑ ↓ Home End Enter Escape), (3) axe-core sans violation **And** coverage ≥ 85 %.

---

### Story 10.21 : Setup Lucide + dossier icônes ESG custom + `EsgIcon.vue` wrapper

**As a** Équipe Mefali (frontend),
**I want** installer `lucide-vue-next` comme pile d'icônes unique (Q20), créer un dossier `frontend/app/assets/icons/esg/*.svg` pour les icônes ESG custom (initiales : `effluents.svg`, `biodiversite.svg`, `audit-social.svg` — extensible par PR), et un composant `frontend/app/components/ui/EsgIcon.vue` exposant la même interface API que les composants Lucide (`<EsgIcon name="effluents" :size="24" />`),
**So that** la cohérence visuelle iconographique soit unifiée (Lucide pour le catalogue général + `EsgIcon` pour les concepts ESG spécialisés absents de Lucide) et que les composants ultérieurs (`ComplianceBadge`, `PackFacadeSelector`, `ReferentialComparisonView`, etc.) consomment une API unique.

**Metadata (CQ-8)**
- `fr_covered`: []
- `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR7]
- `phase`: 0
- `cluster`: transverse-ui
- `estimate`: S
- `qo_rattachees`: []
- `depends_on`: []
- `architecture_alignment`: UX Step 11 section 4 P0, Q20 pile icônes Lucide unique

**Acceptance Criteria**

**AC1** — **Given** `frontend/package.json`, **When** auditée, **Then** elle liste `lucide-vue-next` en dépendance runtime (version stable courante) **And** un import type-safe `import { Icon } from 'lucide-vue-next'` fonctionne en TypeScript strict.

**AC2** — **Given** le dossier `frontend/app/assets/icons/esg/`, **When** listé, **Then** il contient au minimum `effluents.svg`, `biodiversite.svg`, `audit-social.svg` (3 icônes initiales) **And** chaque SVG respecte la convention Lucide : viewBox `0 0 24 24`, `stroke="currentColor"`, `stroke-width="2"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"` (cohérence visuelle avec Lucide).

**AC3** — **Given** `frontend/app/components/ui/EsgIcon.vue`, **When** auditée, **Then** elle expose `defineProps<{ name: string; size?: number | string; strokeWidth?: number; color?: string; class?: string }>()` avec defaults `size=24` + `strokeWidth=2` **And** rend dynamiquement le SVG via `<svg>` + `<use xlink:href="#esg-{name}">` ou import dynamique `import(\`~/assets/icons/esg/${name}.svg?component\`)` selon convention Nuxt 4.

**AC4** — **Given** l'usage `<EsgIcon name="effluents" />` et `<Droplet />` (Lucide), **When** comparés, **Then** l'API est identique (mêmes props `size`, `color`, `stroke-width`) **And** les 2 icônes peuvent cohabiter dans un même composant sans friction.

**AC5** — **Given** un nom d'icône inexistant, **When** `<EsgIcon name="inexistant" />` est utilisé, **Then** un placeholder visuel (ex. cercle barré) + warning console dev est affiché (pas de crash runtime) **And** en production le warning est stripé.

**AC6** — **Given** dark mode activé, **When** `EsgIcon` est rendu avec `color="currentColor"` (défaut), **Then** il hérite de la couleur du parent (classe Tailwind `text-brand-green dark:text-brand-green-dark`) sans hardcode.

**AC7** — **Given** les tests Vitest, **When** exécutés, **Then** minimum 3 tests verts : (1) rendu SVG avec props `size` + `stroke-width` appliqués, (2) fallback placeholder + warning dev sur nom inconnu, (3) axe-core sans violation + `aria-hidden="true"` par défaut (icônes décoratives) ou `role="img" aria-label="..."` si prop `label` fournie.

**AC8** — **Given** la documentation, **When** `docs/CODEMAPS/frontend.md` est mise à jour, **Then** un dev peut ajouter une nouvelle icône ESG en 3 étapes : (1) déposer `nouvelle-icone.svg` dans `frontend/app/assets/icons/esg/`, (2) respecter convention Lucide (viewBox + stroke), (3) utiliser `<EsgIcon name="nouvelle-icone" />` sans modifier le composant wrapper.

---

---
