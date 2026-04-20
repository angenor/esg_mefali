---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-18.md
  - _bmad-output/implementation-artifacts/spec-audits/index.md
  - _bmad-output/implementation-artifacts/sprint-status.yaml
excludedLegacyDocuments:
  - _bmad-output/planning-artifacts/prd-019-floating-copilot.md
  - _bmad-output/planning-artifacts/architecture-019-floating-copilot.md
  - _bmad-output/planning-artifacts/epics-019-floating-copilot.md
uxDesignStatus: pending (/bmad-create-ux-design lancé en parallèle, UX-DRs à intégrer ultérieurement)
preventiveChecklist: CQ-1..CQ-14 (finding R-05-1 HIGH — readiness report 2026-04-18)
step1Arbitrations:
  granularityEpic9: 1 story par P1 (9 stories 9.7→9.15). Clusters 2-7 servent à prioriser au sprint planning, PAS à fusionner l'exécution (scopes orthogonaux incohérents sinon).
  numerotationEpics: Epic 9 (dette audit pure, 9.7→9.15) · Epic 10 (Fondations Extension Phase 0, prérequis bloquant) · Epic 11→Epic 15 (5 clusters métier PRD).
  cq9Attribution: chaque epic liste ses QO rattachées au Step 2. Règle — une QO appartient à l'epic dont le FR/NFR la soulève ; si multi-epic, dupliquer avec scope précis.
  epic10Scope: migrations Alembic 020-027, modules projects/maturity/admin_catalogue, nœuds project_node/maturity_node, RLS 4 tables, micro-Outbox, DSL borné Pydantic.
  story97Parallelism: P1 #14 observabilité (with_retry + log_tool_call) = candidat Phase 0 EN PARALLÈLE d'Epic 10, car prérequis pour instrumenter les nouveaux modules Extension.
  dagDependencies: Epic 10 Fondations bloque tous Epics 11+. À matérialiser dans le DAG des dépendances Step 2.
step2Arbitrations:
  epic18: mutualisé (7 FR — FR58, FR60, FR61, FR65, FR66, FR68, FR69). Split éventuel au niveau stories.
  epic20: mutualisé avec 4 stories distinctes (20.1 cleanup flag ENABLE_PROJECT_MODEL, 20.2 load test k6, 20.3 pen test externe, 20.4 audit WCAG externe).
  qtQT4: hors scope technique (atelier stakeholders business séparé). Exigences dérivées (quotas par tier, etc.) remonteront en stories dans epics concernés au sprint planning.
  story97BlockingDependency: Story 9.7 (P1 #14 observabilité with_retry + log_tool_call) = DÉPENDANCE BLOQUANTE d'Epic 10 (NON parallèle). Raison — instrumenter les nouveaux modules Extension (projects/maturity/admin_catalogue) DÈS leur création, sinon réintroduction de la dette.
  epic19Renaming: Epic 19 Phase 0 = « socle RAG refactor pour réutilisation cross-module » (pgvector infra existe depuis spec 004, seule manque l'abstraction réutilisable). Phase 1 = intégration ≥ 5 modules (applications FR-005 promesse spec 009 non tenue, carbon, credit, action_plan).
---

# ESG Mefali Extension — Epic Breakdown

## Changelog de renumérotation / refactor

- **Story 11.8 → 14.1** (Lot 4) : `CompanyProjection curée par Fund` déplacée pour respecter le DAG Epic 11 → 14 (la projection est sémantiquement liée au matching, pas à la création Company). Epic 11 passe à 8 stories.
- **Story 9.10** (Lot 2) : « Queue async Celery+Redis » → « BackgroundTask FastAPI + micro-Outbox `domain_events` » — alignement architecture Décision 7 (pas de Redis MVP) + Décision 11 (micro-Outbox). Estimate L → XL.
- **Story 13.4 → 13.4a + 13.4b** (Lot 4) : découpage moteur DSL borné (L) + matérialisation `ReferentialVerdict` + invalidation via Outbox (M).
- **Story 13.8 → 13.8a + 13.8b + 13.8c** (Lot 4) : découpage par workflow N1 / N2 / N3 avec UI commune.
- **Story 10.13 AJOUTÉE MVP** (post-Lot 4) : migration embeddings OpenAI → Voyage API activée dès Phase 0 (plus différée Phase Growth). Epic 10 passe de 12 → 13 stories. Story 9.13 `depends_on` étendu avec 10.13.
- **2026-04-19 — Stories 10.14-10.21 AJOUTÉES (socle UI fondation)** : réconciliation avec `ux-design-specification.md` Step 11 Component Strategy section 4 + section 5.1. Ajout de 8 stories UI fondation dans Epic 10 pour débloquer Phase 1 Sprint 1+ (prérequis à `FormalizationLevelGauge`, `FormalizationPlanCard`, `SourceCitationDrawer`, `ComplianceBadge`, `CubeResultTable`, `SignatureModal`, `ReferentialComparisonView`, `ImpactProjectionPanel`, `AdminCatalogueEditor`, etc.) : **10.14** Setup Storybook partiel + 6 stories à gravité (L), **10.15** `ui/Button.vue` 4 variantes (S), **10.16** `ui/Input.vue` + `ui/Textarea.vue` + `ui/Select.vue` (M), **10.17** `ui/Badge.vue` tokens sémantiques (S), **10.18** `ui/Drawer.vue` wrapper Reka UI (M), **10.19** `ui/Combobox.vue` + `ui/Tabs.vue` wrappers Reka UI (M), **10.20** `ui/DatePicker.vue` (M), **10.21** Setup Lucide + `EsgIcon.vue` wrapper + dossier icônes ESG custom (S). Epic 10 passe de 13 → 21 stories. **Cumul total : 101 → 109 stories.** Conflit numérotation UX Step 11 vs epics.md tranché : 10.13 reste Voyage (priorité epics.md finalisé), stories UI fondation décalées de 10.13-10.20 (numérotation UX initiale) vers 10.14-10.21.

## Consolidated Decisions Log (QO tranchées MVP)

- **QO-A1** → Tranchée 11.1 AC5 : pas de Project sans Company (FK NOT NULL).
- **QO-A'1** → Partiellement tranchée 12.2 AC2 : seuil OCR 0,8 + fallback `pending_human_review` (pilote affinera).
- **QO-A'3 + QO-A'4** → Tranchées 12.3 AC3 : `default_steps: JSONB` data-driven (4 étapes MVP, admin Phase Growth modifie sans migration).
- **QO-A'5** → Tranchée 12.5 AC2 : pas de régression auto ; soft-block user + self-service + audit trail (pas d'escalade admin obligatoire).
- **QO-B3** → Tranchée 13.4a AC2 : **`N/A` explicite** sur fact manquant ou expiré (pas NULL, pas PASS par défaut) + rationale `fact_missing|fact_expired`.
- **QO-B4** → Tranchée 13.6 AC2 : **STRICTEST WINS** (min appliqué, pas moyenne pondérée) + `overridden_by_pack` dans `verdict.metadata`.
- **Prompt versioning — 18 specs legacy** (post-Lot 5) : dette acceptée MVP. Les 18 prompts legacy conservés non-versionnés. **Nouveaux prompts Epic 10+ obligatoirement versionnés** via framework CCC-9 (Story 10.8). Migration legacy **opportuniste** : chaque modification d'un prompt legacy déclenche sa mise en conformité versioning. Tech lead surveille en reviews. Pas de story de migration globale.

## Overview

This document provides the complete epic and story breakdown for **ESG Mefali Extension (5 clusters)**, decomposing the requirements from the PRD (71 FR + 76 NFR + 9 Annexes), Architecture (11 décisions + 14 CCC + 12 patterns + 10 enforcement rules) et les 9 dettes P1 restantes de l'audit 18-specs en stories implémentables pour l'agent Developer.

**Contexte brownfield mature** : 18 spec-features déjà livrées (001–018) + feature 019 Floating Copilot. Cette extension ne livre **pas** de starter template neuf : elle étend la fondation existante avec 3 nouveaux modules métier (`projects/`, `maturity/`, `admin_catalogue/`) et refactore les modules `esg/`, `financing/`, `applications/`, `reports/`, `action_plan/`.

**Checklist de prévention qualité (CQ-1..CQ-14)** appliquée lors du breakdown epic/story en Step 2/3 (cf. finding R-05-1 HIGH du readiness report 2026-04-18).

## Requirements Inventory

### Functional Requirements

> **Source** : PRD §Functional Requirements (lignes 1087–1191). 71 FR répartis en 9 capability areas. Actors : PME User (owner/editor/viewer), Auditor (token expirable), Admin Mefali, Admin Super, System.

**Company & Project Management (FR1–FR10)**

- **FR1** : PME User (owner) can create a Company with basic profile (nom, secteur, pays, taille, filière export éventuelle).
- **FR2** : PME User (owner) can invite additional users to the Company with specific roles (editor, viewer, auditor).
- **FR3** : PME User (owner) can revoke access of any user (including auditor) at any time.
- **FR4** : PME User can create one or multiple Projects linked to a Company (cluster A).
- **FR5** : PME User can define a Project lifecycle state (idée/faisabilité/bancable/exécution/achevé) and update it over time.
- **FR6** : PME User can declare a Project as porté by one Company (solo) or by multiple Companies (consortium) via `ProjectMembership` with assignable roles.
- **FR7** : Admin Mefali can add new project-membership roles beyond the initial enum (`porteur_principal`, `co_porteur`, `beneficiaire`) via N2 workflow.
- **FR8** : PME User can attach project members to a beneficiary profile aggregate (`BeneficiaryProfile` with genre, revenus, taux formalisation).
- **FR9** : PME User can bulk-import beneficiary profiles or project members via CSV/Excel with validation + per-row error reporting (Journey 2 Moussa : 152 producteurs COOPRACA).
- **FR10** : System can generate a `CompanyProjection` (vue curée du profil entreprise) per Fund targeted.

**Administrative Maturity Management (FR11–FR16)**

- **FR11** : PME User can self-declare current administrative maturity level among 4 levels (informel / RCCM+NIF / comptes+CNPS / OHADA audité).
- **FR12** : System can validate declared maturity level via OCR of uploaded supporting documents (RCCM, NINEA/IFU, comptes, bilans audités).
- **FR13** : System can generate a `FormalizationPlan` from current to next level with estimated XOF cost, duration, country-specific coordinates.
- **FR14** : PME User can follow `FormalizationPlan` progress and mark steps as done with uploaded proof.
- **FR15** : System can auto-reclassify the maturity level when all required documents for next level are validated.
- **FR16** : Admin Mefali can maintain `AdminMaturityRequirement(country × level)` for each UEMOA/CEDEAO francophone country.

**ESG Multi-Referential Assessment (FR17–FR26)**

- **FR17** : PME User can record atomic facts (quantitatifs ou qualitatifs attestables) with their evidence documents.
- **FR18** : PME User can attest qualitative facts via multiple evidence types : document upload, video testimony (CLIP contextes extractif/agricole), déclaration sur l'honneur, signature de témoin (grief mechanism).
- **FR19** : System can version facts temporally (valid_until, historique des mesures).
- **FR20** : System can automatically derive verdicts (PASS/FAIL/REPORTED/N/A) for multiple referentials from a single set of facts via rules of dérivation.
- **FR21** : System can trace each verdict back to its source facts and applied rules (justification auditable).
- **FR22** : PME User can select a Pack (pré-assemblé façade) that activates a contextual subset of criteria and their weighting (Pack IFC Bancable, Pack EUDR-DDS, Pack Artisan Minimal).
- **FR23** : System can compute a global ESG score weighted across active referentials + drill-down per referential.
- **FR24** : Admin Mefali can define and maintain atomic facts, composable criteria, decision rules, packs, and referentials with versioning (N1/N2/N3 workflows).
- **FR25** : Admin Mefali can publish a new referential version and trigger a `ReferentialMigration` with plan de transition.
- **FR26** : PME User can access a comparative view of scoring for same facts across different referentials (Journey 3 Akissi).

**Funding Matching — Cube 4D (FR27–FR35)**

- **FR27** : PME User can query the cube 4D matcher (project maturity × company maturity × required referentials × access route).
- **FR28** : System can display for each matched Fund the concrete access route (direct submission OR identified intermediary with prerequisites + updated coordinates).
- **FR29** : System can display intermediate-specific criteria superposed on Fund criteria (ex. SIB min 2 ans ancienneté on top of BOAD Ligne Verte).
- **FR30** : PME User can create a `FundApplication` targeting a specific Fund via a specific access route.
- **FR31** : PME User can maintain multiple `FundApplication` for same Project (different Funds, different calibrations) without duplicating underlying facts.
- **FR32** : PME User can track `FundApplication` lifecycle status full path (draft → snapshot_frozen → signed → exported → submitted_to_bailleur → in_review → accepted|rejected|withdrawn) with timestamped transitions + user notes.
- **FR33** : System can archive a rejected `FundApplication` with motive + propose remediation path (Journey 4 Ibrahim).
- **FR34** : System can notify PME Users via in-app alert when a referential/pack/criterion in an active application is modified, offering stay-on-snapshot OR migrate-to-new.
- **FR35** : Admin Mefali can update Fund coordinates, Intermediary criteria, Fund-Intermediary liaisons in real-time (N1 workflow) sans redeploying.

**Document Generation & Deliverables (FR36–FR44)**

- **FR36** : System can generate bailleur-compliant PDF deliverables (GCF Funding Proposal, IFC AIMM, EUDR DDS, EIES Cat B, Proparco AIMM, SGES/ESMS BETA Phase 1).
- **FR37** : System can generate DOCX editable version of any deliverable for expert review.
- **FR38** : System can automatically annex supporting evidence from facts to deliverables (with user-driven selective mode).
- **FR39** : System can snapshot all source data (facts, verdicts, referential versions, company/project state) at generation moment with cryptographic hash.
- **FR40** : PME User must sign an electronic attestation before exporting a deliverable destined to a bailleur (mandatory modal + checkbox).
- **FR41** : System can block export of deliverables above 50 000 USD threshold until user confirms section-by-section human review.
- **FR42** : System can generate deliverables calibrated to access route (direct Fund template vs Intermediary template).
- **FR43** : Admin Mefali can manage catalogue of `DocumentTemplate`, `ReusableSection`, `AtomicBlock` (N2 workflow).
- **FR44** : System can enforce mandatory human consultant review before exporting any SGES/ESMS BETA deliverable. **NO BYPASS** — pas de bypass even `admin_mefali`/`admin_super`. Seule sortie : `admin_mefali` retire le BETA flag après critères GA Phase 2 (10+ reviews ≥ 4/5). Tentatives de bypass loggées comme incident sécurité.

**Conversational Copilot — Chat IA + Tools (FR45–FR50)**

- **FR45** : PME User can interact with Mefali via chat streaming SSE en français, copilot able to invoke tools for any capability.
- **FR46** : System can maintain conversation context with `active_project` + `active_module` across turns.
- **FR47** : System can present interactive widgets (QCU, QCM, QCU+justification) within chat.
- **FR48** : System can surface guided tours triggered by LLM via LangChain tool (infrastructure livrée spec 019).
- **FR49** : System can fall back gracefully to manual input when LLM fails, preserving conversation continuity.
- **FR50** : PME User can resume an interrupted conversation from last checkpoint (LangGraph MemorySaver).

**Dashboard, Monitoring & Notifications (FR51–FR56)**

- **FR51** : PME User can view dashboard aggregating scores ESG/carbone/crédit/financement/plan d'action (module 011 étendu).
- **FR52** : PME User can drill down from global score into each active referential's verdicts.
- **FR53** : PME User can view multi-project dashboard (Journey 2 Moussa).
- **FR54** : PME User can receive in-app reminders for upcoming events (deadline bailleur, renouvellement certification, expiration faits, MàJ référentiel, étape `FormalizationPlan`).
- **FR55** : Admin Mefali can access system monitoring dashboard (p95 latence par tool, taux erreur, échecs guards LLM, couverture catalogue).
- **FR56** : System can trigger alert to Admin on anomalies (échec guards LLM, taux retry anormal, source URL HTTP ≠ 200).

**Audit, Compliance & Security (FR57–FR69)**

- **FR57** : System can log every generation of deliverable with full metadata in `FundApplicationGenerationLog` (LLM version, timestamp, anonymized prompts, referential versions, snapshot hash, user ID).
- **FR58** : System can anonymize PII (noms, adresses, RCCM/NINEA/IFU, téléphones) before sending any prompt to LLM.
- **FR59** : System can enforce RLS (Row-Level Security) PostgreSQL sur `companies`, `fund_applications`, `facts`, `documents`.
- **FR60** : System can encrypt sensitive data at rest (bilans, RCCM, IFU, documents uploadés) via KMS-managed keys.
- **FR61** : System can require MFA for `admin_mefali`/`admin_super` permanently + step-up MFA for high-risk actions on all roles (soumission > 50k USD, signature, modification bancaire, changement credentials, suppression docs/projets, export sensibles).
- **FR62** : System can enforce NFR-SOURCE-TRACKING : any catalogue entity without `source_url`, `source_accessed_at`, `source_version` stays DRAFT, cannot be published.
- **FR63** : System can run nightly CI test verifying HTTP 200 accessibility of all `source_url` in catalogue.
- **FR64** : System can maintain audit trail of all catalogue modifications by admins (who/what/when/before-after), retained min 5 years, Admin UI for consultation.
- **FR65** : PME User can exercise right to erasure (soft delete + deferred purge 30–90 j), submitted FundApplications snapshots remain frozen.
- **FR66** : PME User can export all data in machine-readable format (JSON + CSV optionnel) — data portability.
- **FR67** : PME User can grant time-bounded access (auditor role with expirable token) to external reviewers.
- **FR68** : PME User can initiate password reset via email verification (ou magic link passwordless onboarding MVP). Admin Mefali can force-reset avec audit log.
- **FR69** : System can maintain audit trail of all accesses to sensitive data, retained 5 years minimum.

**Search & Knowledge Retrieval — RAG (FR70–FR71)**

- **FR70** : System can retrieve relevant fragments from uploaded documents via pgvector embeddings, to support fact extraction, narrative generation, ESG assessment **across at least 5 modules** (signal PRD 6 — RAG transversal, cf. SC-T9).
- **FR71** : System can cite source documents in generated content (rule-level citation in verdicts, paragraph-level citation in narratives).

### NonFunctional Requirements

> **Source** : PRD §Non-Functional Requirements (lignes 1193–1347). 76 NFR répartis en 12 catégories. Chaque NFR est testable.

**Performance (NFR1–NFR8)**

- **NFR1** : Requête cube 4D matching ≤ 2 s p95 avec cache tiède (SC-T3).
- **NFR2** : Génération verdicts multi-référentiels évaluation ESG complète (30–60 critères sur 3–5 référentiels actifs) ≤ 30 s p95 (SC-T4).
- **NFR3** : Génération PDF simple (EUDR DDS, plan d'action) ≤ 30 s p95.
- **NFR4** : Génération livrable lourd (SGES/ESMS BETA, IFC AIMM full, GCF Funding Proposal) ≤ 3 min p95. Au-delà récurrent → file jobs asynchrones (Phase Growth).
- **NFR5** : Latence chat (premier token SSE) ≤ 2 s p95 (MO-6).
- **NFR6** : Latence navigation dashboard (TTI) ≤ 1,5 s p95 sur 4G.
- **NFR7** : Chargement initial application (FCP) ≤ 2 s p95 sur 4G, ≤ 5 s p95 sur 3G dégradée (low-data Phase 3).
- **NFR8** : Cold start backend ≤ 30 s (chargement catalogue en mémoire + warm-up pgvector).

**Security (NFR9–NFR18)**

- **NFR9** : TLS 1.3 minimum toutes connexions. Certificats valides, renouvellement automatique.
- **NFR10** : Chiffrement at rest via KMS pour documents uploadés, snapshots FundApplication, journal audit.
- **NFR11** : Anonymisation PII systématique avant LLM. Pipeline testé + audit annuel.
- **NFR12** : RLS PostgreSQL activé dès MVP sur `companies`, `fund_applications`, `facts`, `documents`. Généralisation Phase Growth.
- **NFR13** : Authentification JWT stateless + refresh token (1 h access, 30 j refresh révocable). Rotation sur action sensible.
- **NFR14** : MFA obligatoire `admin_mefali`/`admin_super`. Opt-in fortement recommandé `owner`. Step-up MFA actions à risque (FR61).
- **NFR15** : Gestion secrets via env vars (MVP) puis Secret Manager (Growth). Rotation trimestrielle. Lint pre-commit `detect-secrets`/`truffleHog`.
- **NFR16** : Pas de secrets/PII dans logs. Enforcement via structured logging + anonymisation auto.
- **NFR17** : Rate limiting 30 msg/min par user sur endpoints chat (livré story 9.1). Extension tools coûteux Phase Growth.
- **NFR18** : Pen test externe OBLIGATOIRE avant premier pilote PME réelle. Findings CRITIQUES corrigés avant activation. Audit sécurité indépendant Phase 0 (5 j, ~5–8 k€).

**Privacy, Data Residency & Compliance (NFR19–NFR28)**

- **NFR19** : Conformité loi SN 2008-12, CI 2013-450, règlement CEDEAO. Alignement structurel RGPD.
- **NFR20** : Rétention par catégorie : profil (compte+2 ans), documents ordinaires (compte+5 ans), **SGES/ESMS + associés (10 ans min après fin FundApplication)**, faits (versions historiques indéfiniment), logs applicatifs (12 mois), logs audit sensibles (5 ans).
- **NFR21** : Soft delete + purge différée 30–90 j. Purge définitive irréversible + auditable.
- **NFR22** : Consentement explicite pour partage vers bailleur ou intermédiaire (acte distinct du « saisi dans Mefali »).
- **NFR23** : Droit à l'effacement : snapshots FundApplication soumis figés, indépendants du profil vivant.
- **NFR24** : Data residency **AWS EU-West-3 Paris** (Option A). Plan contingence migration Cape Town ou local si évolution réglementaire. Clauses-types CEDEAO dans DPA + consentement. Localisation par type de document documentée.
- **NFR25** : Documents sensibles (bilans, RCCM, IFU, ID) : localisation documentée + auditable. Transfert hors UEMOA/CEDEAO → trace + consentement.
- **NFR26** : Data portability — export JSON + CSV (FR66).
- **NFR27** : NFR-SOURCE-TRACKING : `source_url`, `source_accessed_at`, `source_version` obligatoires. DRAFT non publiable sinon (FR62).
- **NFR28** : Audit trail complet immuable (accès sensibles, modifs catalogue, générations livrables). 5 ans min.

**Availability, Reliability & DR (NFR29–NFR36)**

- **NFR29** : SLA différencié — endpoints critiques (soumission, SGES, dossier lourd) = **99,5 % dès MVP**. Non-critiques (chat, dashboard, recherche) = 99 % MVP, 99,5 % Growth.
- **NFR30** : Soumissions dossiers bailleurs atomiques + resumables. Reprise sur échec réseau sans perte via LangGraph checkpointer.
- **NFR31** : Backups PostgreSQL + pgvector — incrémentales quotidiennes, complètes hebdo, 30 j chaud + 1 an archivé.
- **NFR32** : Test de restauration BDD trimestriel documenté.
- **NFR33** : Backups fichiers uploadés — réplication géographique 2 AZ min, rétention alignée.
- **NFR34** : RTO cible MVP : **4 h**.
- **NFR35** : RPO cible MVP : **24 h max**.
- **NFR36** : Plan de continuité documenté + runbooks. Tabletop exercise trimestriel (mitigation RM-7).

**Observability (NFR37–NFR41)**

- **NFR37** : Logs JSON structurés + `request_id` UUID frontend → FastAPI → LangGraph → tools → DB. Zéro log non-structuré en prod.
- **NFR38** : 100 % tools métier LangChain instrumentés `with_retry` + `log_tool_call` (clôture P1 #14 audit, SC-T11).
- **NFR39** : Dashboard monitoring interne admin_mefali — p95 tool, erreur, retry, échecs guards LLM, timeouts.
- **NFR40** : Alerting échec guards, retry anormal, erreurs DB, timeouts, `source_url` HTTP ≠ 200 (FR63).
- **NFR41** : Budget LLM surveillé par user + global. Alerting dépassement (mitigation RM-6).

**Integration (NFR42–NFR48)**

- **NFR42** : LLM **Anthropic via OpenRouter**. Abstraction Provider pour switch < 2 sem. Backup provider (OpenAI ou Mistral).
- **NFR43** : Embeddings OpenAI `text-embedding-3-small` pgvector. Alternative open-source évaluée Growth.
- **NFR44** : OCR Tesseract bilingue `fra+eng` (story 9.4). Extension `por` Phase Vision.
- **NFR45** : Email transactionnel **Mailgun** MVP (DKIM+SPF+DMARC, monitoring délivrance, domaine dédié, templates Git).
- **NFR46** : Génération PDF WeasyPrint + Jinja2 (module 006 étendu Cluster C).
- **NFR47** : Génération DOCX python-docx (spec 009 étendu).
- **NFR48** : Stockage documents local `/uploads/` MVP + backup géographique (NFR33). Migration S3 Growth.

**Scalability (NFR49–NFR53)**

- **NFR49** : Architecture stateless backend FastAPI (sauf LangGraph checkpointer persisté BDD) pour scaling horizontal.
- **NFR50** : Capacité cible MVP 500 users actifs simultanés sans dégradation. Growth 5 000. Vision 50 000+.
- **NFR51** : PostgreSQL — indexes composites cube 4D, vues matérialisées requêtes chaudes, partitionnement évalué Growth.
- **NFR52** : pgvector IVFFlat MVP, migration HNSW si > 100 k embeddings.
- **NFR53** : Cache tiède Redis Phase Growth (sessions, catalogues chauds, matching fréquents).

**Accessibility (NFR54–NFR58)**

- **NFR54** : Conformité WCAG 2.1 niveau AA minimum toutes pages user-facing.
- **NFR55** : Navigation clavier complète (livrée spec 019 story 1.7), étendue aux nouvelles pages.
- **NFR56** : ARIA roles conformes (livrés spec 018), étendus aux nouveaux composants.
- **NFR57** : Contraste WCAG AA (4.5:1 texte normal, 3:1 texte large). Vérification CI axe-core/pa11y.
- **NFR58** : Support lecteurs d'écran NVDA, JAWS, VoiceOver parcours critiques. Audit accessibilité indépendant Phase 3 (1–2 j, ~1–2 k€).

**Maintainability & Code Quality (NFR59–NFR64)**

- **NFR59** : *Zero failing tests on main* (opérationnel depuis story 9.3). Baseline croissante à chaque clôture de phase.
- **NFR60** : Couverture tests différenciée — **≥ 80 %** standard, **≥ 85 %** code critique (guards LLM, anonymisation PII, RLS, rate limiting, signature, snapshot, livrables bailleur). Coverage gates CI : PR rejetée sous ces seuils.
- **NFR61** : Docstrings Python fonctions publiques, JSDoc/TSDoc composables TS. CLAUDE.md à jour à chaque nouveau module.
- **NFR62** : Conventions CLAUDE.md — code en anglais, commentaires en français, snake_case Python, PascalCase composants Vue, structure Nuxt 4 `app/`, dark mode obligatoire, migrations Alembic.
- **NFR63** : Pas de feature flag permanent — tout flag (ex. `ENABLE_PROJECT_MODEL`) retiré via story dédiée en fin Phase 1.
- **NFR64** : Anti-pattern God service (P2 #25 audit) — services consomment services d'autres modules, pas leurs tables directement.

**Internationalization (NFR65–NFR67)**

- **NFR65** : Locale user unique `fr` (ou `fr-FR`). Aucun hardcoded string user-facing hors fichier traduction.
- **NFR66** : Paramétrage pays via tables BDD (`AdminMaturityRequirement`, `regulation_reference`, `Country`). Séparation locale (langue) vs country (data).
- **NFR67** : Framework i18n Nuxt (`@nuxtjs/i18n` ou `vue-i18n`) installé Phase 0. Extensibilité `en` Vision sans refactor majeur.

**Budget & Ops (NFR68–NFR70)**

- **NFR68** : Budget LLM — alerting dépassement mensuel. Seuil défini Phase 0 avec business.
- **NFR69** : Budget infra cible MVP **800–2 000 €/mois** (AWS compute+RDS+S3+CloudFront ~300–600, LLM Anthropic/OpenRouter ~200–800, Embeddings ~50–200, Mailgun ~50–100, Backup ~100–200, Monitoring ~100–300). À confirmer Phase 0 costing détaillé.
- **NFR70** : Cyber insurance évaluée Phase Growth (mitigation RM-7).

**DevOps Practices & Release Engineering (NFR71–NFR76)**

- **NFR71** : **Load Testing obligatoire avant prod** — 100 users simultanés 30 min chat+cube 4D, 10 générations SGES simultanées, 500 appels/min read-only. Tous NFR Performance respectés. Rapport archivé. À re-lancer à chaque Phase avant prod.
- **NFR72** : **Security Dependency Audit automatisé** — scan quotidien `pip-audit` + `npm audit`/Snyk/Dependabot. PR automatique CVE MEDIUM+. Blocage merge CVE CRITICAL non résolue.
- **NFR73** : **Environment Isolation** — DEV (données synthétiques), STAGING (mirror anonymisé), PROD (accès limité, audit full). Prod JAMAIS copiée vers dev/staging sans anonymisation. Secrets différents par env.
- **NFR74** : **LLM Quality Observability** — taux passage guards (> 90 %), retry auto (< 5 %), échec définitif (< 1 %), temps moyen génération, coût moyen. Dashboard admin_mefali. Alerting dégradation soudaine.
- **NFR75** : **LLM Retry Strategy** — max 3 retries exponential backoff (1 s, 3 s, 9 s). Uniquement sur transient (timeout, 5xx, 429). Pas de retry sur définitives (400, guards fail, schema fail). Circuit breaker : 10 échecs consécutifs → désactivation 60 s + alerting.
- **NFR76** : **Code Review mandatory** — min 1 reviewer approval avant merge. Code critique (sécurité, compliance, guards, snapshot, signature, rate limiting, RLS) : 2 reviewers dont 1 senior. Checklist auto (tests, secrets, debug, TODO, CLAUDE.md, dark mode, types). Branch protection rules.

### Additional Requirements

> **Sources** : Architecture §Décisions/Clarifications/CCC/Patterns/Enforcement (architecture.md) + Implementation Readiness Report (finding R-05-1 HIGH) + Spec-Audits Index (9 P1 restants OUVERTS) + Sprint Status.

**Starter / Fondation technique (Step 3 Architecture)**

- AR-ST-1 — **Pas de starter template neuf**. Brownfield mature 18 specs livrées + spec 019 ; extension par 3 nouveaux modules `projects/`, `maturity/`, `admin_catalogue/` dans `backend/app/modules/` (monolithe modulaire FastAPI maintenu).
- AR-ST-2 — Langages figés : Python 3.12 backend (pas 3.13+), TypeScript 5.x strict frontend.
- AR-ST-3 — LangGraph reste à **11 nœuds** (chat, esg_scoring, carbon, financing, applications, credit, action_plan, document, **project (nouveau)**, **maturity (nouveau)**) + ToolNode conditionnel. **Pas de `admin_node`** (Clarification 2).

**Décisions architecturales structurantes (11 décisions — architecture.md §423–829)**

- AR-D1 — Modèle `Company × Project` N:N avec cumul de rôles (impact FR1–FR10).
- AR-D2 — Pack par fonds + résolution conflits **STRICTEST WINS** (impact FR22, FR27–FR35).
- AR-D3 — Architecture 3 couches ESG (DSL borné + micro-Outbox invalidation) (impact FR17–FR26).
- AR-D4 — Cube 4D Postgres + GIN + cache LRU (impact FR27, NFR1).
- AR-D5 — Moteur livrables (`template_sections` relationnelle + prompt versioning) (impact FR36–FR44).
- AR-D6 — Admin N1/N2/N3 state machine + échantillon représentatif (impact FR24, FR25, FR35, FR43).
- AR-D7 — Multi-tenancy RLS 4 tables (`companies`, `fund_applications`, `facts`, `documents`) + log admin escape (impact FR59, NFR12).
- AR-D8 — Environnements DEV/STAGING/PROD séparés + validation anonymisation (impact NFR73).
- AR-D9 — Backup + PITR 5 min + RTO 4 h / RPO 24 h engagé (impact NFR31–NFR36).
- AR-D10 — LLM Provider Layer avec 2 niveaux de switch (impact NFR42, RM-6).
- AR-D11 — Transaction boundaries + micro-Outbox MVP (impact CCC-14 différée — à trancher Epic Breakdown).

**Clarifications actées (6 — architecture.md §343–422)**

- AR-C1 — Pas de split microservices ; monolithe modulaire conservé MVP/Growth/Scale.
- AR-C2 — `admin_node` rejeté ; admin catalogue UI-only (Journey 5 Mariam).
- AR-C3 — Orchestration container : AWS ECS Fargate recommandé MVP (alternative EC2+Docker Compose ; EKS rejeté MVP).
- AR-C4 — Stratégie tests 5 clusters : pytest + pytest-asyncio + Hypothesis (property-based SC-T6) + httpx.AsyncClient + Playwright (5 journeys) + Locust/k6 (NFR71).
- AR-C5 — Feature flag `ENABLE_PROJECT_MODEL` simple (var env + wrapper Python) ; pas de librairie externe ; **cleanup obligatoire fin Phase 1** (NFR63 + RT-3).
- AR-C6 — Pattern Outbox appliqué module interne (pas inter-service).

**Nouvelles migrations Alembic (ordre séquentiel)**

- `020_create_projects_schema.py`
- `021_create_maturity_schema.py`
- `022_create_esg_3_layers.py`
- `023_create_deliverables_engine.py`
- `024_enable_rls_on_sensitive_tables.py`
- `025_add_source_tracking_constraints.py`
- `026_create_admin_catalogue_audit_trail.py`
- `027_cleanup_feature_flag_project_model.py` (retrait flag fin Phase 1 — NFR63)

**Nouvelles dépendances Python**

- `Hypothesis` (property-based testing SC-T6)
- `boto3` (migration S3 Phase Growth)
- `celery` + `redis` (queue asynchrone P1 #6 — prep Phase 0)
- `detect-secrets` / `truffleHog` pre-commit (NFR15 Phase 0)
- `clamav-daemon` + `python-clamd` (détection malware P2 #7, optionnel)

**Remplacements ciblés (Phase 0)**

- Hard-coding catalogue (`seed.py` 889 lignes) → Tables BDD `fund`, `intermediary`, `fund_intermediary_liaison` + admin UI N1.
- `SECTOR_WEIGHTS` / `SECTOR_BENCHMARKS` hard-codés → Tables BDD + admin UI N2 (P1 #9, P2 #9).
- Facteurs émission carbone hard-codés → Table `carbon_emission_factor(country × activity × scope × version)` + admin.
- 4 spec-correctifs prompts (013/015/016/017) → Framework d'injection unifié registry + builder (CCC-9).
- Stockage local `/uploads/` → S3 EU-West-3 + backup 2 AZ (abstraction `StorageProvider` Phase 0).

**Integration / Mapping (Annexe C PRD — Clusters → FR → Phase)**

- AR-MAP-1 — Cluster A (FR1–FR10) Phase 1, racine aucune dépendance upstream.
- AR-MAP-2 — Cluster A' (FR11–FR16) Phase 1, utilise Cluster A.
- AR-MAP-3 — Cluster B ESG (FR17–FR26) Phase 1 catalogue P0 + Phase 2 ext P1 + Phase 4 ext P2. Parallèle A. Utilisé par C.
- AR-MAP-4 — Cube 4D (FR27–FR35) Phase 1, dépend A + A' + B.
- AR-MAP-5 — Cluster C Moteur livrables (FR36–FR44, dont FR44 SGES BETA) Phase 1 BETA + Phase 2 GA. Dépend A + A' + B.
- AR-MAP-6 — Copilot (FR45–FR50) Phase 1 extension existant. Transverse.
- AR-MAP-7 — Cluster D Dashboard+Monitoring (FR51–FR56) Phase 1 MVP + Phase 3 UX enrichi. Parallèle.
- AR-MAP-8 — Audit/Compliance/Security (FR57–FR69) Phase 0 prérequis + Phase 1 enforcement. Transverse — obligatoire MVP.
- AR-MAP-9 — RAG transversal (FR70–FR71) Phase 0 (≥ 5 modules) + Phase 4 (8/8). Transverse.

**Epic 9 — Dette audit 18-specs (PURE) — 9 P1 RESTANTS À PLANIFIER (spec-audits/index.md §Actions consolidées)**

> **État Epic 9 au 2026-04-19 (sprint-status.yaml)** :
> - **6 stories `done`** : 9.1 rate limiting chat, 9.2 quota stockage user, 9.3 hygiène CI (fix 4 tests rouges), 9.4 OCR bilingue FR+ENG, 9.5 flag `manually_edited_fields`, 9.6 guards LLM persistés documents bailleurs.
> - **Epic 9 statut global : `in-progress`** — 9 P1 résiduels (#1, #3, #5, #6, #9, #11, #12, #13, #14) restent à planifier comme stories **9.7 → 9.15** (ou regroupées par cluster si pertinent — voir regroupement suggéré ci-dessous).
>
> **Règle de séparation stricte (confirmée utilisateur 2026-04-19)** :
> - **Epic 9 = dette audit PURE** (issues des audits rétrospectifs specs 001–018). **Aucun doublon** avec les nouvelles features.
> - **Epics 10+ = nouvelles features** issues du PRD Extension 5 clusters (FR1–FR71 nouveaux modules `projects/`, `maturity/`, `admin_catalogue/` + refactors ESG 3-couches, Cube 4D, Moteur livrables, etc.).
> - Les stories 9.1–9.6 `done` sont **gelées** et ne seront jamais recréées.
>
> **Regroupement par cluster suggéré** (6 clusters restants ; Cluster 1 sécurité/data-loss déjà complet via 9.1/9.2/9.4/9.5/9.6/9.3) — à trancher définitivement Step 2 :
>
> | Cluster | Libellé | P1 couverts | Story ID candidate |
> |---|---|---|---|
> | Cluster 2 | Observabilité | #14 (`with_retry` + `log_tool_call` 9 modules tools) | 9.7 |
> | Cluster 3 | Dead code + tests manquants | #3 (dead code `profiling_node`) + #11 (5 tests backend spec 008) | 9.8 (ou 9.8 + 9.9) |
> | Cluster 4 | Scalabilité | #6 (queue async LLM+PDF) + #12 (`batch_save_emission_entries` carbon) | 9.9 (ou 9.10 + 9.11) |
> | Cluster 5 | Promesses non tenues | #5 (FR-019 notification chat PDF + `REPORT_TOOLS`) + #13 (FR-005 RAG applications) | 9.10 (ou 9.12 + 9.13) |
> | Cluster 6 | Alignement marché | #9 (`SECTOR_WEIGHTS` 11 secteurs) | 9.11 (ou 9.14) |
> | Cluster 7 | Dette frontend | #1 (migration 7 composables → `apiFetch`) | 9.12 (ou 9.15) |
>
> **Arbitrage Step 2** : story par cluster (6 stories 9.7→9.12) OU story par P1 (9 stories 9.7→9.15). À trancher lors du design epics.

- AR-P1-1 — **Migration 7 composables → `apiFetch`** (source 001). Composables : `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`. Impact : intercepteur 401 cassé → sessions expirées mal gérées.
- AR-P1-3 — **Supprimer dead code `profiling_node` + `chains/extraction.py`** (source 003). Fichiers : `backend/app/graph/nodes.py:1192+` (~240 lignes), `backend/app/chains/extraction.py` (~150 lignes), tests associés. ~300 lignes non référencées depuis spec 012.
- AR-P1-5 — **Implémenter FR-019 notification chat PDF + `REPORT_TOOLS` LangChain** (source 006). Fichiers : `backend/app/graph/tools/report_tools.py` (à créer), `backend/app/graph/graph.py`, `backend/app/api/chat.py`. Fonctionnalité marquée `[X]` mais non implémentée.
- AR-P1-6 — **Queue asynchrone opérations longues LLM + PDF** Celery/RQ/BackgroundTask (source 006, élargi 011). Fichiers : `backend/app/modules/reports/service.py` (PDF ESG ~30 s), `backend/app/modules/action_plan/service.py` (LLM plan 5–30 s). Bloque workers uvicorn → pannes cascade > 5 users simultanés.
- AR-P1-9 — **Compléter `SECTOR_WEIGHTS` 11 secteurs** (source 005). Fichier `backend/app/modules/esg/weights.py:12`. 5 secteurs sur 11 (textile, agroalimentaire, commerce, artisanat, construction) retombent sur `general` — dominants PME AO francophones (>60 % selon BCEAO).
- AR-P1-11 — **Créer 5 tests backend spec 008 Financing** (source audit forensique). Fichiers : `test_matching.py`, `test_models.py`, `test_router_funds.py`, `test_router_matches.py`, `test_service_pathway.py`. Silence total sur le cœur matching projet-financement.
- AR-P1-12 — **`batch_save_emission_entries` module carbon** (source 007). Fichier `backend/app/graph/tools/carbon_tools.py`. Timeout LLM imminent sur bilans multi-véhicules (7–15 appels séquentiels vs timeout 60 s).
- AR-P1-13 — **Implémenter FR-005 RAG documentaire applications** (source 009). Fichier `backend/app/modules/applications/service.py` (`generate_section`). Promesse spec 009 non tenue — aucune utilisation `search_similar_chunks`. Consolidation P2 #6 (RAG sous-exploité).
- AR-P1-14 — **`with_retry` + `log_tool_call` sur 9 modules tools** (source 012, absorbe P2 #2). Fichiers : `backend/app/graph/tools/` (profiling, esg, carbon, financing, credit, application, document, action_plan, chat). FR-021 (retry) + FR-022 (journalisation) non câblés 9/11 modules.

**Note divergence comptage P1** : l'utilisateur a indiqué « 10 P1 restants » ; l'index des audits à date du 2026-04-19 (post-story 9.6 `done`) liste 9 P1 OUVERTS (index.md ligne 43 : « 4 résolus, 10 à ouvrir » reflète l'état pré-9.6). **À trancher en Step 2** : confirmation périmètre final Epic 0 avec l'utilisateur.

**Checklist préventive CQ-1..CQ-14 (finding R-05-1 HIGH — readiness report 2026-04-18)**

> Ces garde-fous s'appliquent à **chaque story produite** lors du breakdown (Step 2/3 de ce workflow).

- **CQ-1** : Pas d'epic technique sans valeur user. Orienter sur capability user (ex. « PME porteuse de projets multi-canal » couvre FR1–FR10 + data model + UI).
- **CQ-2** : Pas de forward dependency inter-epic. Respecter ordre Annexe C : A → A' → B → Cube 4D → C → D.
- **CQ-3** : Pas de stories épics-sized non complétables. Décomposer par Fact-type, par critère, par pack.
- **CQ-4** : Phase 0 structurée en **2 epics distincts** (séparation stricte — clarification utilisateur 2026-04-19) :
  - **Epic 9 (dette audit pure)** — continuation du sprint existant, stories 9.7+ pour les 9 P1 résiduels (cf. §Dette audit ci-dessus).
  - **Epic 10+ (fondations Extension)** — nouveau, couvre les fondations Phase 0 issues du PRD Extension (migrations catalogue data-driven, framework prompts CCC-9, abstraction `StorageProvider`, audit sécurité externe, sourcing documentaire, infra DEV/STAGING/PROD, feature flag `ENABLE_PROJECT_MODEL` + cleanup).
  - **Aucun doublon** entre Epic 9 et Epic 10+. Ne pas recréer dans Epic 9 ce qui relève de nouvelles features ; ne pas dupliquer dans Epic 10+ ce que les P1 audit couvrent déjà.
- **CQ-5** : FR44 SGES BETA NO BYPASS → **story dédiée** « Workflow revue humaine SGES BETA NO BYPASS avec verrou applicatif ».
- **CQ-6** : AC format Given/When/Then avec **métriques quantifiées** (ex. NFR1 → « Given cube 4D warmed cache, When user submits multi-dim query, Then p95 latency ≤ 2 s »).
- **CQ-7** : Pas de création BDD upfront. Créer tables au moment où la première story qui les utilise est livrée (ex. `FundApplicationGenerationLog` dans story `guards-llm-universels`, pas `setup-bdd`).
- **CQ-8** : Chaque story porte `fr_covered: [FR12, FR15]` et `phase: 0` pour mapping Annexe C.
- **CQ-9** : 10 Questions Ouvertes (QO-A1/A4/A5/A'1/A'3/A'4/A'5/B3/B4/C2/T4) **attribuées à un epic** pour tranchage.
- **CQ-10** : Cleanup feature flag `ENABLE_PROJECT_MODEL` — story dédiée fin Phase 1 (NFR63 + RT-3).
- **CQ-11** : Format stories aligné sur `implementation-artifacts/9-X` + `spec-audits/`.
- **CQ-12** : Table de traçabilité normalisée `epic ↔ Cluster ↔ FR ↔ NFR ↔ Risk ↔ QO`.
- **CQ-13** : Estimations indicatives XS/S/M/L/XL ou story points par story.
- **CQ-14** : Jalon « re-validation estimation » fin Phase 0 obligatoire (PRD ligne 941).

**Cadencement phasé (PRD §Project Scoping & Phased Development)**

- AR-PH-0 — **Phase 0** structurée en 2 epics distincts (cf. CQ-4) :
  - **Epic 9 dette audit pure** — 9 P1 résiduels (stories 9.7+), continuation sprint existant.
  - **Epic 10+ fondations Extension** — migrations catalogue data-driven, framework prompts CCC-9, abstraction `StorageProvider`, audit sécurité externe, sourcing documentaire, infra DEV/STAGING/PROD, feature flag.
- AR-PH-1 — **Phase 1 MVP** : 5 clusters (A, A', B, Cube 4D, C BETA, D Dashboard MVP) + Copilot extension + cleanup feature flag.
- AR-PH-2 — **Phase 2 Growth** : SGES GA, ESG extension P1, queue async Celery+Redis, S3.
- AR-PH-3 — **Phase 3 UX enrichi** : Dashboard UX, mode low-data 3G, audit accessibilité indépendant.
- AR-PH-4 — **Phase 4 RAG étendu 8/8 modules + ESG extension P2**.
- AR-PH-5 — **Phase 5 Vision** : évaluations microservices, scale > 50 000 users.

### UX Design Requirements

> **Statut** : `/bmad-create-ux-design` **lancé en parallèle**. Aucun document UX Design n'existe à date dans `_bmad-output/planning-artifacts/`.
>
> **Plan d'intégration** : dès livraison du spec UX, les UX-DRs (design tokens, composants réutilisables, accessibilité WCAG AA, responsive, interactions) seront intégrés en Step supplémentaire + re-mapping FR → UX-DR. Les stories existantes seront mises à jour le cas échéant.
>
> **UX implicitement couvert** à date dans le PRD (§Frontend-Specific Considerations lignes 786–820, Journey 5 personas, NFR54–NFR58 accessibilité, pattern dark mode CLAUDE.md, composant UI `components/ui/` pattern de réutilisabilité) et dans les 18 specs livrées (interactive widgets 018, guided tours 019, ChatMessage dark mode, etc.). Ces couvertures implicites **ne remplacent pas** un UX Design formel à produire.

### FR Coverage Map

> 71/71 FR couverts = **100 %**, zéro FR orphelin.

| FR | Epic | Description courte |
|---|---|---|
| FR1–FR10 | **Epic 11** | Cluster A — PME porteuse de projets multi-canal |
| FR11–FR16 | **Epic 12** | Cluster A' — Maturité administrative graduée |
| FR17–FR26 | **Epic 13** | Cluster B — ESG multi-contextuel 3 couches |
| FR27–FR35 | **Epic 14** | Cube 4D — Matching projet-financement |
| FR36–FR44 | **Epic 15** | Cluster C — Moteur livrables (dont FR44 SGES BETA story dédiée CQ-5) |
| FR45–FR50 | **Epic 16** | Copilot conversationnel — extension tool-calling |
| FR51–FR56 | **Epic 17** | Dashboard & Monitoring |
| FR57 | **Epic 15** | Log `FundApplicationGenerationLog` généré avec livrable |
| FR58 | **Epic 18** | Anonymisation PII pipeline transverse |
| FR59 | **Epic 10** | RLS 4 tables (migration 024, fondation) |
| FR60 | **Epic 10** | Chiffrement at rest KMS (infra) |
| FR61 | **Epic 18** | MFA `admin_*` + step-up actions à risque |
| FR62 | **Epic 10** | Enforcement NFR-SOURCE-TRACKING (migration 025) |
| FR63 | **Epic 10** | CI nightly HTTP 200 `source_url` |
| FR64 | **Epic 10** | Audit trail catalogue (migration 026) |
| FR65 | **Epic 18** | Droit à l'effacement (soft delete + purge différée) |
| FR66 | **Epic 18** | Data portability export JSON/CSV |
| FR67 | **Epic 11** | Auditor time-bounded scoping sur Company |
| FR68 | **Epic 18** | Password reset + magic link |
| FR69 | **Epic 18** | Audit trail accès sensibles |
| FR70 | **Epic 19** | RAG pgvector ≥ 5 modules MVP |
| FR71 | **Epic 19** | Citations source documents |

**NFR coverage (mapping indicatif — détail au Step 3)** :

- NFR1–NFR8 (Performance) → critères d'acceptance quantifiés dans chaque epic métier (CQ-6).
- NFR9–NFR18 (Security) → Epic 10 (infra) + Epic 18 (enforcement) + Epic 20.3 pen test.
- NFR19–NFR28 (Privacy/Residency/Compliance) → Epic 10 (data residency setup) + Epic 18 (droits PME).
- NFR29–NFR36 (Availability/DR) → Epic 10 (backup+PITR+RTO/RPO setup).
- NFR37–NFR41 (Observability) → Story 9.7 (dep bloquante Epic 10) + Epic 17 (dashboard admin).
- NFR42–NFR48 (Integration) → Epic 10 (LLM Provider Layer, Mailgun, OCR, Storage).
- NFR49–NFR53 (Scalability) → Epic 10 (stateless + Celery prep) + Epic 15 (queue SGES).
- NFR54–NFR58 (Accessibility) → critères transverses chaque epic UI + Epic 20.4 audit WCAG.
- NFR59–NFR64 (Maintainability) → Epic 9 + Epic 10 (patterns, conventions).
- NFR65–NFR67 (i18n) → Epic 10 (framework `@nuxtjs/i18n`).
- NFR68–NFR70 (Budget/Ops) → Epic 10 (alerting budget LLM) + Epic 17 (dashboard).
- NFR71–NFR76 (DevOps) → Epic 10 (env isolation, dependency audit) + Epic 20 (load/pen test, code review).

## Epic List

**Total : 12 epics** — Epic 9 (dette audit PURE, in-progress) + Epic 10 (Fondations Phase 0 BLOQUANT) + Epics 11–15 (5 clusters métier PRD) + Epics 16–19 (transverses) + Epic 20 (Cleanup & Release Engineering).

### Epic 9 : Dette audit 18-specs (PURE)

**Goal** : consolider le socle livré (specs 001–018) en résolvant les dettes P1 identifiées par les audits rétrospectifs, sans réintroduire de doublons avec les nouvelles features PRD Extension. **Statut : `in-progress`** — 6 stories `done`, 9 stories 9.7–9.15 à livrer (1 story par P1, arbitrage granularité utilisateur 2026-04-19).

- **FRs couverts** : — (dette audit sur FR-021 retry + FR-022 journalisation déjà livrés ; renforce NFR16, NFR38, NFR59, NFR60, NFR64)
- **NFRs renforcés** : NFR16, NFR38, NFR59, NFR60, NFR64
- **Stories already done** : 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
- **Stories to design Step 3** : 9.7 (P1 #14 observabilité — **DEP BLOQUANTE Epic 10**), 9.8 (P1 #3 dead code), 9.9 (P1 #11 tests Financing), 9.10 (P1 #6 queue async), 9.11 (P1 #12 batch carbon), 9.12 (P1 #5 FR-019 chat PDF), 9.13 (P1 #13 RAG applications), 9.14 (P1 #9 SECTOR_WEIGHTS), 9.15 (P1 #1 apiFetch)
- **QO rattachées** : — (pas de QO ouverte rattachée)
- **Dépendances** : aucune en amont. Story 9.7 livre les prérequis d'instrumentation d'Epic 10.

### Epic 10 : Fondations Extension Phase 0 (BLOQUANT)

**Goal** : livrer la fondation technique opérationnelle requise par tous les Epics 11+. Catalogue data-driven (BDD vs hard-coding), migrations 020-027, 3 nouveaux modules squelettes (`projects/`, `maturity/`, `admin_catalogue/`), nœuds LangGraph `project_node` + `maturity_node`, RLS 4 tables, micro-Outbox, DSL borné Pydantic, framework prompts unifié (CCC-9), abstraction `StorageProvider`, env DEV/STAGING/PROD isolés, feature flag `ENABLE_PROJECT_MODEL`, sourcing documentaire complet Annexe F, **socle UI fondation (Storybook + 6 composants `ui/` génériques + `EsgIcon.vue` wrapper Lucide)** prérequis à tous les composants métier Phase 1 Sprint 1+.

- **FRs couverts** : FR59, FR62, FR63, FR64
- **NFRs couverts** : NFR5, NFR7, NFR12, NFR15, NFR24, NFR27, NFR28, NFR31–NFR36, NFR42, NFR43, NFR48, NFR54, NFR55, NFR56, NFR57, NFR58, NFR62, NFR67, NFR72, NFR73, NFR74
- **Additional Requirements** : AR-ST-1..3, AR-D3, AR-D4, AR-D5, AR-D6, AR-D7, AR-D8, AR-D9, AR-D10, AR-D11, AR-C1..C6, migrations 020–026, dépendances `celery`+`redis`+`detect-secrets`+`boto3`+`@storybook/vue3-vite`+`@storybook/addon-a11y`+`@storybook/addon-interactions`+`reka-ui`+`lucide-vue-next`
- **Stories (21 au total)** : 10.1 à 10.13 (fondation backend/infra) + **10.14–10.21 (socle UI fondation — ajout 2026-04-19, voir changelog)**.
- **QO rattachées** : — (infra neutre)
- **Dépendances amont** : **Story 9.7 bloquante** (observabilité `with_retry` + `log_tool_call`) pour instrumenter les nouveaux modules dès création.

### Epic 11 : Cluster A — PME porteuse de projets multi-canal

**Goal** : le propriétaire d'une Company peut créer/gérer son entreprise, inviter collaborateurs et auditeurs, porter 1+ Projects (solo ou consortium via `ProjectMembership`), enregistrer bénéficiaires en masse par CSV/Excel, générer une `CompanyProjection` par fonds cible. Data model racine du système.

- **FRs couverts** : FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR67
- **NFRs renforcés** : NFR49 (stateless), NFR50 (capacité), NFR60 (coverage standard ≥ 80 %)
- **QO rattachées** : **QO-A1** (Project sans Company ?)
- **Dépendances** : Epic 10 (migration 020_create_projects_schema + RLS + admin_catalogue pour rôles N2 FR7)

### Epic 12 : Cluster A' — Maturité administrative graduée

**Goal** : la PME auto-déclare son niveau parmi 4 (informel / RCCM+NIF / comptes+CNPS / OHADA audité), uploade justifs validés par OCR, suit un `FormalizationPlan` chiffré XOF + durée + coordonnées pays (tribunal commerce, bureau fiscal, caisse sociale), progression step-by-step + auto-reclassification. Admin Mefali maintient `AdminMaturityRequirement(country × level)` pour UEMOA/CEDEAO francophone.

- **FRs couverts** : FR11, FR12, FR13, FR14, FR15, FR16
- **NFRs renforcés** : NFR19 (compliance SN/CI/CEDEAO), NFR66 (country data driven)
- **QO rattachées** : **QO-A'1** (OCR validation humaine), **QO-A'3** (niveaux intermédiaires), **QO-A'4** (formalisation vs conformité fiscale), **QO-A'5** (régression niveau liquidation)
- **Dépendances** : Epic 10 (migration 021_create_maturity_schema + admin_catalogue), Epic 11 (Company model racine)

### Epic 13 : Cluster B — ESG multi-contextuel 3 couches

**Goal** : la PME enregistre des faits atomiques (quanti + quali attestables) avec preuves multi-type (doc, vidéo CLIP, déclaration honneur, signature témoin), le système dérive automatiquement des verdicts PASS/FAIL/REPORTED/N/A multi-référentiels avec traçabilité, version temporellement les faits, applique un Pack pré-assemblé (IFC Bancable, EUDR-DDS, Artisan Minimal), calcule un score global pondéré + drill-down. Admin gère facts/critères/rules/packs/référentiels avec workflow N1/N2/N3 + `ReferentialMigration` avec plan de transition.

- **FRs couverts** : FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26
- **NFRs renforcés** : NFR2 (≤ 30 s p95 verdicts), NFR27 (SOURCE-TRACKING), SC-T6 (property-based non-contradiction)
- **QO rattachées** : **QO-B3** (scoring évaluation partielle), **QO-B4** (arbitrage faits conflictuels)
- **Dépendances** : Epic 10 (migration 022_create_esg_3_layers + DSL Pydantic + micro-Outbox + catalogue admin)

### Epic 14 : Cube 4D — Matching projet-financement

**Goal** : la PME interroge le matcher 4D (`project maturity × company maturity × required referentials × access route`), reçoit recommandations avec voie directe ou intermédiée (prerequisites + coordonnées à jour + critères intermédiaire superposés), crée et gère N `FundApplication` sur un même Project sans duplication de faits, suit le lifecycle complet (draft → snapshot_frozen → signed → exported → submitted → in_review → accepted/rejected/withdrawn) avec notes horodatées, remédiation automatique sur rejet, notification sur modification référentiel avec choix snapshot vs migration.

- **FRs couverts** : FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR35
- **NFRs renforcés** : NFR1 (≤ 2 s p95 cube 4D), NFR30 (soumissions atomiques resumables)
- **QO rattachées** : **QO-A4** (changements scope post-financement), **QO-A5** (clonage FundApplication)
- **Dépendances** : Epic 10 (admin catalogue N1), Epic 11 (Company/Project), Epic 12 (maturité), Epic 13 (ESG référentiels)

### Epic 15 : Cluster C — Moteur livrables bailleurs + SGES BETA NO BYPASS

**Goal** : la PME génère des livrables PDF + DOCX bailleur-compliant (GCF, IFC AIMM, EUDR DDS, EIES Cat B, Proparco AIMM, **SGES/ESMS BETA Phase 1**) calibrés par voie d'accès, annexe preuves automatiquement (ou sélectif), snapshot cryptographique au moment de génération (immutabilité FR39), signe attestation électronique obligatoire avant export (FR40), blocage export > 50k USD sans review section-par-section (FR41). **FR44 SGES BETA NO BYPASS** — workflow bloquant sans bypass applicatif, tentatives loggées comme incident sécurité (**story dédiée CQ-5**). Admin gère catalogue `DocumentTemplate` + `ReusableSection` + `AtomicBlock` N2.

- **FRs couverts** : FR36, FR37, FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR57
- **NFRs renforcés** : NFR3 (≤ 30 s p95 PDF simple), NFR4 (≤ 3 min p95 SGES/IFC AIMM), NFR20 (rétention 10 ans SGES), NFR28 (audit trail immuable)
- **QO rattachées** : **QO-C2** (import gabarits non officiels)
- **Dépendances** : Epic 10 (migration 023_create_deliverables_engine), Epic 11–13 (data source), Story 9.6 déjà livrée (guards LLM)

### Epic 16 : Copilot conversationnel — extension tool-calling

**Goal** : la PME invoque toute capability (catalogue, facts entry, matching, génération, FormalizationPlan) via le chat streaming SSE en français, le copilot maintient `active_project` + `active_module` cross-turn, surface widgets interactifs (QCU, QCM, QCU+justification), déclenche guided tours via LangChain tool (spec 019 livrée), fallback manuel gracieux si LLM échoue, reprise conversation interrompue (LangGraph MemorySaver).

- **FRs couverts** : FR45, FR46, FR47, FR48, FR49, FR50
- **NFRs renforcés** : NFR5 (≤ 2 s p95 premier token SSE), NFR17 (rate limiting déjà livré 9.1), NFR42 (LLM Provider Layer), NFR74–NFR75 (observability + retry LLM)
- **QO rattachées** : —
- **Dépendances** : Epic 10 (framework prompts CCC-9 + LLM Provider Layer), Epics 11–15 (tools rattachés à chaque cluster)

### Epic 17 : Dashboard & Monitoring

**Goal** : la PME visualise un dashboard agrégeant scores ESG/carbone/crédit/financement/plan d'action (module 011 étendu), drille du score global vers chaque verdict par référentiel, voit multi-projets (Journey 2 Moussa), reçoit reminders in-app (deadline bailleur, renouvellement certif, expiration faits, MàJ référentiel, étape formalisation). Admin Mefali accède au dashboard de monitoring système (p95 tool, erreur, retry, guards LLM, couverture catalogue, budget LLM) + alerting anomalies.

- **FRs couverts** : FR51, FR52, FR53, FR54, FR55, FR56
- **NFRs renforcés** : NFR6 (≤ 1,5 s p95 TTI dashboard 4G), NFR39 (dashboard admin), NFR41 (budget LLM alerting), NFR74 (LLM quality obs)
- **QO rattachées** : —
- **Dépendances** : Epic 10 (infra), Epics 11–15 (data sources agrégées), Story 9.7 (instrumentation source des métriques)

### Epic 18 : Compliance & Security renforcés

**Goal** : la PME exerce son droit à l'effacement (soft delete + purge différée 30–90 j, snapshots figés préservés), export data portability JSON + CSV, reset password via email/magic link, sécurité renforcée (MFA `admin_*` + step-up actions à risque PME). Admin trace tous les accès aux données sensibles (5 ans min). Pipeline d'anonymisation PII systématique avant LLM (audit annuel).

- **FRs couverts** : FR58, FR60, FR61, FR65, FR66, FR68, FR69
- **NFRs renforcés** : NFR11, NFR13, NFR14, NFR19–NFR21, NFR23, NFR26, NFR28
- **QO rattachées** : —
- **Dépendances** : Epic 10 (infra RLS + KMS + audit trail), Epics 11–15 (enforcement sur data user)

### Epic 19 : Socle RAG refactor + intégration ≥ 5 modules

**Goal** *(Phase 0)* : refactor du socle RAG existant (pgvector livré spec 004) en une abstraction réutilisable cross-module — extraction de l'interface commune, factorisation de `search_similar_chunks`, pattern de chunking + embedding + citation standardisé. *(Phase 1)* : intégration de l'abstraction dans ≥ 5 modules — priorité aux promesses non tenues (applications FR-005 spec 009 — déjà P1 #13 dans story 9.13) + carbon + credit + action_plan. *(Phase 4)* : extension 8/8 modules.

- **FRs couverts** : FR70, FR71
- **NFRs renforcés** : NFR43 (embeddings), NFR52 (pgvector IVFFlat → HNSW Growth)
- **QO rattachées** : —
- **Dépendances** : Epic 10 (infra catalogue + StorageProvider), Story 9.13 (P1 #13 RAG applications — consomme l'abstraction refactorisée)

### Epic 20 : Cleanup & Release Engineering

**Goal** : équipe livre le MVP en prod avec 4 stories distinctes verrouillant les pre-flights. **20.1** cleanup feature flag `ENABLE_PROJECT_MODEL` (NFR63 + RT-3 + CQ-10). **20.2** load testing k6/Locust conformément scénarios NFR71 (100 users chat+cube 4D, 10 SGES simultanés, 500 appels/min read-only). **20.3** pen test externe indépendant (NFR18, 5 j ~5–8 k€, findings CRITIQUES corrigés avant pilote). **20.4** audit accessibilité WCAG AA externe (NFR58, 1–2 j ~1–2 k€).

- **FRs couverts** : — (NFR-only)
- **NFRs renforcés** : NFR18, NFR58, NFR63, NFR71
- **QO rattachées** : — (QT-4 hors scope technique — atelier business séparé)
- **Dépendances** : Epics 11–19 livrés (pre-flight est par construction en fin de Phase 1)

---

---

## Epic 9 — Stories détaillées

### Story 9.7 : Instrumentation `with_retry` + `log_tool_call` sur les 9 modules tools LangChain

**As a** Équipe Mefali (SRE/DX),
**I want** que les 9 modules tools métier LangChain (`profiling_tools`, `esg_tools`, `carbon_tools`, `financing_tools`, `credit_tools`, `application_tools`, `document_tools`, `action_plan_tools`, `chat_tools`) soient instrumentés via `with_retry()` + `log_tool_call()` déjà présents dans `backend/app/graph/tools/common.py`,
**So that** les échecs transients ne causent plus d'erreurs silencieuses côté user, les investigations d'incidents bénéficient d'un log structuré sur chaque appel d'outil, et que les nouveaux modules d'Epic 10 (`projects/`, `maturity/`, `admin_catalogue/`) naissent instrumentés — clôture P1 #14 audit.

**Metadata (CQ-8)**
- `fr_covered`: [] (renforce FR-021 retry + FR-022 journalisation déjà livrés côté infra)
- `nfr_covered`: [NFR38, NFR75]
- `phase`: 0
- `cluster`: dette-audit (cluster 2 observabilité)
- `estimate`: M
- `qo_rattachees`: —
- `blocks`: **Epic 10 — DÉPENDANCE BLOQUANTE (CQ-11)**

**Acceptance Criteria**

**AC1** — **Given** les 9 modules `backend/app/graph/tools/`, **When** un audit de code est exécuté, **Then** 100 % des tools exposés sont wrappés via `with_retry()` + `log_tool_call()` (vs 2/11 actuels `interactive_tools` + `guided_tour_tools`).

**AC2** — **Given** un tool qui lève une erreur transient (TimeoutError, ConnectionError, 5xx, 429), **When** invoqué depuis un nœud LangGraph, **Then** `with_retry()` déclenche jusqu'à 3 retries exponential backoff (1 s, 3 s, 9 s) conformément NFR75, **And** chaque tentative est loggée avec `reason`.

**AC3** — **Given** un tool qui lève une erreur définitive (400, validation Pydantic, guards fail), **When** invoqué, **Then** aucun retry n'est déclenché (NFR75) **And** l'erreur est loggée une seule fois.

**AC4** — **Given** un appel réussi, **When** `log_tool_call()` s'exécute, **Then** une entrée est créée dans `tool_call_logs` avec (`tool_name`, `user_id`, `conversation_id`, `duration_ms`, `status=success`, `input_size_bytes`, `output_size_bytes`, `timestamp`).

**AC5** — **Given** 10 échecs consécutifs sur un même endpoint LLM, **When** détectés par `with_retry()`, **Then** le circuit breaker s'active pour 60 s **And** un event d'alerting est émis (NFR75 circuit breaker).

**AC6** — **Given** la suite de tests, **When** `pytest backend/tests/test_graph/test_tools_instrumentation.py` exécuté, **Then** les 9 modules sont couverts par ≥ 1 test vérifiant le wrapping **And** coverage ≥ 85 % (code critique NFR60).

**AC7** — **Given** cette story mergée, **When** l'Epic 10 démarre, **Then** les trois nouveaux modules `projects_tools.py`, `maturity_tools.py`, `admin_catalogue_tools.py` sont créés **instrumentés dès leur première ligne** (pas de rattrapage a posteriori).

---

### Story 9.8 : Suppression dead code `profiling_node` + `chains/extraction.py`

**As a** Équipe Mefali (DX),
**I want** supprimer définitivement `profiling_node` (~240 lignes `backend/app/graph/nodes.py:1192+`), `backend/app/chains/extraction.py` (~150 lignes), et les tests associés (`test_profiling_node.py`, `test_extraction_chain.py`, `test_chat_profiling.py`),
**So that** le codebase ne comporte plus de code non référencé depuis spec 012 (tool-calling LangGraph) et qu'aucun contributeur ne puisse réactiver accidentellement ces chemins obsolètes.

**Metadata (CQ-8)**
- `fr_covered`: —
- `nfr_covered`: [NFR59, NFR61, NFR64]
- `phase`: 0
- `cluster`: dette-audit (cluster 3)
- `estimate`: S

**Acceptance Criteria**

**AC1** — **Given** le code source, **When** `grep -r "profiling_node"` est exécuté sur `backend/` (hors changelog), **Then** zéro occurrence.

**AC2** — **Given** le code source, **When** `grep -r "chains.extraction\|from chains import extraction"` est exécuté, **Then** zéro occurrence.

**AC3** — **Given** les tests backend, **When** `pytest backend/tests/` exécuté, **Then** tous verts (baseline NFR59 zero failing tests maintenue).

**AC4** — **Given** la couverture backend, **When** mesurée post-refactor, **Then** régression ≤ 0,5 % par rapport à la baseline (compensation du retrait de code testé par la non-inclusion dans le dénominateur).

**AC5** — **Given** le graphe LangGraph runtime, **When** les nœuds sont construits, **Then** aucun nœud `profiling_node` enregistré (fonctionnalité déjà reprise par le tool `update_company_profile` depuis spec 012).

---

### Story 9.9 : 5 tests backend manquants module `financing` (spec 008)

**As a** Équipe Mefali (QA/DX),
**I want** les 5 fichiers `backend/tests/test_financing/` — `test_matching.py`, `test_models.py`, `test_router_funds.py`, `test_router_matches.py`, `test_service_pathway.py` —,
**So that** une régression sur le cœur du matching projet-financement soit détectée en CI avant déploiement, et non par un entrepreneur recevant des recommandations biaisées sans alerte.

**Metadata (CQ-8)**
- `fr_covered`: — (couvre l'existant spec 008 FR-001..FR-006)
- `nfr_covered`: [NFR59, NFR60 (≥ 85 % code critique matching)]
- `phase`: 0
- `cluster`: dette-audit (cluster 3)
- `estimate`: M

**Acceptance Criteria**

**AC1** — **Given** `test_matching.py` créé, **When** `pytest` exécuté, **Then** ≥ 15 tests couvrent : secteur match/partiel/no-match, taille compatible/incompatible, géographie couverte/hors zone, seuil ESG atteint/non-atteint, docs requis présents/manquants, voie directe vs intermédiée.

**AC2** — **Given** `test_models.py`, **When** exécuté, **Then** les modèles `Fund`, `Intermediary`, `FundIntermediaryLiaison`, `FundApplication` sont testés sur invariants (relations, contraintes, defaults, enums).

**AC3** — **Given** `test_router_funds.py` + `test_router_matches.py`, **When** exécutés, **Then** les endpoints `GET /api/financing/funds`, `GET /api/financing/matches/{project_id}`, `POST /api/financing/applications` sont couverts sur happy path + 401/403/404/422.

**AC4** — **Given** `test_service_pathway.py`, **When** exécuté, **Then** les 2 parcours (direct vs intermédiaire) sont testés avec ≥ 1 cas nominal + ≥ 1 cas dégradé (fonds fermé, intermédiaire obsolète).

**AC5** — **Given** la couverture de `backend/app/modules/financing/`, **When** mesurée, **Then** ≥ 85 % (code critique NFR60).

**AC6** — **Given** les tests ajoutés, **When** exécutés dans la CI, **Then** tous verts **And** baseline augmentée d'au moins 15 tests (NFR59).

---

### Story 9.10 : Queue asynchrone `BackgroundTask` FastAPI + micro-Outbox `domain_events` pour opérations longues (LLM + PDF)

**As a** PME User,
**I want** que la génération d'un rapport ESG PDF (~30 s), d'un plan d'action IA (~5–30 s) et d'un dossier application lourd n'occupe plus un worker uvicorn synchrone pendant toute sa durée,
**So that** la plateforme reste réactive même avec > 5 utilisateurs simultanés en génération et que je reçoive une notification dès que mon livrable est prêt, **en respectant la décision architecturale « pas de Redis MVP » + micro-Outbox `domain_events`** (architecture.md §Décision 11, CCC-14).

**Metadata (CQ-8)**
- `fr_covered`: — (infra support FR36, FR51, FR32)
- `nfr_covered`: [NFR4, NFR49, NFR50]
- `phase`: 0
- `cluster`: dette-audit (cluster 4 scalabilité)
- `estimate`: **XL** (migration 3 endpoints synchrones : `reports/service.py` PDF ESG, `action_plan/service.py` LLM plan, `applications/service.py` génération de dossier)
- `depends_on`: **[Story 10.10 micro-Outbox `domain_events` + worker batch 30 s]** (Epic 10 doit livrer la table + worker avant que 9.10 consomme le pattern)
- `architecture_alignment`: Décision 11 (pas de Celery+Redis MVP, pattern micro-Outbox) + CCC-14 (transaction boundaries)

**Acceptance Criteria**

**AC1** — **Given** `BackgroundTask` FastAPI + table `domain_events` livrée par Story 10.10, **When** un user déclenche la génération d'un PDF ESG, **Then** l'appel HTTP retourne en < 500 ms p95 avec un `job_id` (vs 30 s bloquants aujourd'hui) **And** une ligne `domain_event(event_type='report_generation_requested', payload=…, status='pending')` est insérée **dans la même transaction** que la création du `Report` (CCC-14 atomicité).

**AC2** — **Given** `BackgroundTask` attachée à la response, **When** FastAPI renvoie le 202, **Then** le rendu PDF s'exécute de manière **non bloquante** dans le même process uvicorn (pool `BackgroundTask`) **And** à la complétion, un event `report_generation_completed` est émis vers `domain_events` pour traitement par le worker batch 30 s (notification SSE).

**AC3** — **Given** 10 utilisateurs simultanés déclenchent chacun une génération lourde, **When** le pool uvicorn tourne (workers = 2 × CPU + 1), **Then** aucune cascade de pannes (zéro 503 sur endpoints non-génération) **And** p95 latence chat ≤ 2 s (NFR5) préservée **And** limite concurrente BackgroundTask documentée pour éviter saturation mémoire.

**AC4** — **Given** le worker batch `domain_events` tourne toutes les 30 s (Story 10.10), **When** il consomme un event `report_generation_completed`, **Then** un événement SSE `report_ready` est envoyé sur la conversation active du user avec `job_id` + URL signée **And** l'event est marqué `status='processed'` (idempotence : redelivery sans double notification).

**AC5** — **Given** un job échoue (LLM timeout, PDF render error), **When** constaté dans le `BackgroundTask`, **Then** un event `report_generation_failed` est inséré dans `domain_events` avec motif **And** le worker déclenche l'event SSE `report_failed` avec message user-friendly + suggestion remédiation **And** une entrée loggée dans `tool_call_logs`.

**AC6** — **Given** le mode synchrone legacy (pré-9.10) doit rester possible en DEV pour debug, **When** la variable d'env `USE_ASYNC_GENERATION=false`, **Then** les 3 endpoints se comportent en mode synchrone historique (graceful degradation).

**AC7** — **Given** la suite de tests, **When** `pytest backend/tests/test_reports/test_background_tasks.py` + `test_action_plan/test_background_tasks.py` + `test_applications/test_background_tasks.py` exécutés, **Then** scénarios (enqueue via BackgroundTask, domain_event insertion atomique, worker consume 30 s, SSE notification, échec, idempotence redelivery, graceful degradation) tous verts **And** coverage ≥ 85 % (code critique NFR60).

**AC8** — **Given** le changelog technique, **When** reviewé, **Then** il explicite que **Celery + Redis sont écartés MVP** (conformément Décision 11) et que la migration vers Celery reste documentée comme option Phase Growth si la charge dépasse les capacités BackgroundTask.

---

### Story 9.11 : `batch_save_emission_entries` pour le module carbon

**As a** PME User (owner) effectuant un bilan carbone,
**I want** que mes 7–15 entrées d'émission multi-véhicules/multi-postes soient sauvegardées via un seul tool call batch,
**So that** la génération du bilan ne subisse plus un timeout LLM silencieux après le 6ᵉ appel séquentiel (incident récurrent transport/logistique — même pattern que ESG spec 015).

**Metadata (CQ-8)**
- `fr_covered`: — (infra module carbon spec 007)
- `nfr_covered`: [NFR5, NFR75]
- `phase`: 0
- `cluster`: dette-audit (cluster 4 scalabilité)
- `estimate`: S

**Acceptance Criteria**

**AC1** — **Given** `backend/app/graph/tools/carbon_tools.py`, **When** un nouveau tool `batch_save_emission_entries(entries: List[EmissionEntrySchema])` est ajouté sur le modèle `batch_save_esg_criteria`, **Then** il accepte jusqu'à 20 entrées en une seule transaction SQLAlchemy atomique.

**AC2** — **Given** une PME transport déclare 12 véhicules, **When** le LLM invoque `batch_save_emission_entries`, **Then** les 12 entrées sont persistées en ≤ 1 appel tool **And** l'appel retourne en < 2 s p95 (vs timeout 60 s aujourd'hui).

**AC3** — **Given** une entrée invalide (facteur négatif, category hors enum), **When** le batch soumis, **Then** la transaction entière échoue (atomicité) **And** le message d'erreur identifie la/les ligne(s) fautive(s).

**AC4** — **Given** le prompt `backend/app/prompts/carbon.py`, **When** le LLM décide comment collecter, **Then** une instruction explicite privilégie `batch_save_emission_entries` sur `save_emission_entry` dès ≥ 3 entrées connues.

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_carbon/test_batch_save.py` exécuté, **Then** scénarios (1 entrée, 10 entrées, 20 entrées, entrée invalide, rollback) couverts **And** coverage ≥ 85 % (NFR60).

---

### Story 9.12 : FR-019 notification chat PDF + `REPORT_TOOLS` LangChain

**As a** PME User,
**I want** recevoir une notification in-chat quand mon rapport ESG PDF est prêt,
**So that** je n'aie plus à rafraîchir manuellement `/reports` et que je télécharge le PDF directement depuis la conversation où je l'ai demandé (promesse spec 006 FR-019 jamais livrée).

**Metadata (CQ-8)**
- `fr_covered`: (implémente réellement FR-019 spec 006)
- `nfr_covered`: [NFR5, NFR37, NFR74]
- `phase`: 0
- `cluster`: dette-audit (cluster 5 promesses non tenues)
- `estimate`: M
- `depends_on`: Story 9.10 (queue async) + Story 9.7 (instrumentation)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/graph/tools/report_tools.py` créé, **When** le module est chargé, **Then** il expose au minimum `generate_esg_report(project_id, referentials)` + `get_report_status(job_id)` wrappés `with_retry` + `log_tool_call` (story 9.7).

**AC2** — **Given** un user demande « génère-moi mon rapport ESG » par chat, **When** le LLM invoque `generate_esg_report`, **Then** un `job_id` est retourné en < 500 ms **And** un event SSE `report_requested` est émis.

**AC3** — **Given** le job termine en succès, **When** l'event terminal remonte, **Then** un message chat auto-généré apparaît : « Votre rapport ESG est prêt. [Télécharger le PDF] » avec lien signé **And** le lien fonctionne sans rafraîchissement manuel de `/reports`.

**AC4** — **Given** le job échoue, **When** l'event d'échec remonte, **Then** un message chat explique le motif user-friendly + suggestion remédiation **And** un log structuré est créé (NFR37).

**AC5** — **Given** le graphe LangGraph, **When** `generate_esg_report` est enregistré dans `chat_node`, **Then** la route est testée dans `backend/tests/test_graph/test_report_tools.py`.

**AC6** — **Given** cette story mergée, **When** la checklist audit est mise à jour, **Then** P1 #5 audit passe à ✅ RÉSOLU **And** la discordance speckit « `[X]` sans livrable » est documentée comme cas rétrospectif.

---

### Story 9.13 : FR-005 RAG documentaire dans le module `applications`

**As a** PME User qui a uploadé bilans, statuts juridiques et politiques internes,
**I want** que les sections générées de mon dossier de financement s'ancrent dans le contenu réel de mes documents via RAG pgvector,
**So that** mon livrable soit différencié d'un dossier générique et que les sections narratives citent effectivement mes éléments de preuve (promesse spec 009 FR-005 non tenue).

**Metadata (CQ-8)**
- `fr_covered`: (implémente promesse FR-005 spec 009, préfigure FR70/FR71 Epic 19)
- `nfr_covered`: [NFR2, NFR60]
- `phase`: 0
- `cluster`: dette-audit (cluster 5 promesses non tenues)
- `estimate`: M
- `consolide_avec`: P2 #6 (RAG sous-exploité transverse)
- `depends_on`: **[Epic 19 Story 19.1 socle RAG refactor cross-module, Story 10.13 Voyage migration]** — 9.13 consomme (a) l'abstraction RAG réutilisable d'Epic 19.1 et (b) l'`EmbeddingProvider` Voyage de Story 10.13, **sans recréer de 2ᵉ abstraction**. Sprint planning ordonnancera 10.13 → 19.1 → 9.13 pour éviter double migration. 9.13 reste dans Epic 9 pour traçabilité P1 #13 dette-audit.

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/applications/service.py::generate_section`, **When** invoquée pour un projet avec ≥ 3 documents uploadés, **Then** elle appelle `search_similar_chunks(query, top_k=5, project_id=X)` **And** incorpore les chunks dans le prompt.

**AC2** — **Given** la section générée, **When** relue, **Then** ≥ 1 citation explicite (nom fichier + page/chunk) pointe vers un document du user quand la section porte sur un sujet documentable (sécurité, bilan, politique).

**AC3** — **Given** un projet sans document uploadé, **When** `generate_section` invoquée, **Then** le fallback actuel (profil + scores) est conservé sans régression **And** aucune citation fictive n'est générée.

**AC4** — **Given** le module applications, **When** audité, **Then** ≥ 3 appels à `search_similar_chunks` présents (un par type de section narrative : contexte, impact ESG, plan d'action).

**AC5** — **Given** les projets ayant ≥ 3 docs, **When** la métrique CI est mesurée, **Then** ratio de sections avec citation ≥ 60 %.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_applications/test_rag_integration.py` exécuté, **Then** scénarios (avec docs, sans docs, fallback, citation présente) tous verts.

---

### Story 9.14 : Complétion `SECTOR_WEIGHTS` pour les 11 secteurs

**As a** PME User dans un secteur dominant AO (agroalimentaire, commerce, artisanat, textile, construction),
**I want** que le scoring ESG pondère correctement selon mon secteur réel,
**So that** mon score ne soit pas dégradé par un fallback générique et que le bailleur voie une note contextualisée fidèle à ma filière.

**Metadata (CQ-8)**
- `fr_covered`: (renforce FR23 calcul ESG score + alignement marché PME AO)
- `nfr_covered`: [NFR60]
- `phase`: 0
- `cluster`: dette-audit (cluster 6 alignement marché)
- `estimate`: S
- `prep_epic13`: préfigure migration hard-code → table BDD (Epic 13 cluster B)
- `feeds_into`: [Epic 13] (Epic 13 prendra le relais en migrant `weights.py` vers une table BDD `sector_weight` + admin UI N2 ; la story 9.14 est le garde-fou intérimaire qui comble le trou marché sans attendre Epic 13)

**Acceptance Criteria**

**AC1** — **Given** `backend/app/modules/esg/weights.py`, **When** le fichier est modifié, **Then** les 11 secteurs du profil entreprise (énergie, agriculture, transport, industrie, services, textile, agroalimentaire, commerce, artisanat, construction, général) ont chacun un jeu E-S-G explicite (vs 5/11 aujourd'hui).

**AC2** — **Given** une PME agroalimentaire sénégalaise, **When** son scoring ESG est calculé, **Then** les pondérations utilisées sont spécifiques `agroalimentaire` (à définir avec conseiller ESG AO, valeurs par défaut documentées), **And** ne tombent pas sur `general`.

**AC3** — **Given** les jeux définis, **When** le code est lu, **Then** chaque jeu porte un commentaire justifiant le choix (source référentiel, étude de marché, ou note « préliminaire à affiner pilote Phase 0 »).

**AC4** — **Given** les tests, **When** `pytest backend/tests/test_esg/test_sector_weights.py` exécuté, **Then** les 11 secteurs sont testés sur `get_sector_weights(sector)` + le scoring E2E change selon le secteur.

**AC5** — **Given** cette story mergée, **When** le fichier est lu, **Then** un `TODO migration Epic 13` explicite indique que `weights.py` sera remplacé par une table BDD + admin UI N2.

---

### Story 9.15 : Migration des 7 composables frontend vers `apiFetch`

**As a** PME User dont la session JWT expire,
**I want** que l'intercepteur 401 redirige correctement vers `/login` depuis tous les modules (applications, crédit score, plan d'action, rapports, documents, profil entreprise, chat),
**So that** je ne subisse plus d'écran blanc ou d'erreur silencieuse quand mon token expire en cours de navigation.

**Metadata (CQ-8)**
- `fr_covered`: — (dette frontend infra)
- `nfr_covered`: [NFR13, NFR59]
- `phase`: 0
- `cluster`: dette-audit (cluster 7 dette frontend)
- `estimate`: M

**Acceptance Criteria**

**AC1** — **Given** les 7 composables `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`, **When** ils sont audités, **Then** tous utilisent `apiFetch` (wrapper centralisé Nuxt) **And** aucun n'utilise `$fetch` / `fetch` / `axios` brut.

**AC2** — **Given** un JWT expiré, **When** un user invoque n'importe quel composable migré, **Then** l'intercepteur 401 d'`apiFetch` déclenche redirection `/login?redirect=<currentPath>` en < 500 ms.

**AC3** — **Given** un refresh token encore valide, **When** une 401 survient, **Then** `apiFetch` tente un refresh silencieux (1 tentative max, NFR13) avant redirection — comportement centralisé à valider non-régression.

**AC4** — **Given** la couverture frontend, **When** `npm test` exécuté, **Then** les tests unitaires des 7 composables passent **And** un test E2E Playwright vérifie « JWT expiré → redirect → re-login → retour sur page » sur ≥ 3 des 7 modules.

**AC5** — **Given** le diff git, **When** reviewé, **Then** suppression totale des anciens appels `$fetch`/`fetch` (pas de co-existence laissée en dette).

**AC6** — **Given** cette story mergée, **When** `index.md` §P1 est mis à jour, **Then** P1 #1 passe à ✅ RÉSOLU **And** l'Epic 9 progresse vers clôture.

---

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

## Epic 11 — Stories détaillées (Cluster A — PME porteuse de projets multi-canal)

> **Pré-requis** : Epic 10 complet (migrations 020, modules squelettes, RLS, feature flag `ENABLE_PROJECT_MODEL=true`).

### Story 11.1 : Création de Company avec profil de base

**As a** PME User (owner),
**I want** créer ma Company avec profil de base (nom, secteur, pays UEMOA/CEDEAO, taille, filière export éventuelle),
**So that** je puisse ensuite porter des Projects, inviter des collaborateurs et recevoir des recommandations de financement contextualisées.

**Metadata (CQ-8)** — `fr_covered`: [FR1] · `nfr_covered`: [NFR5, NFR12, NFR66] · `phase`: 1 · `cluster`: A · `estimate`: M · `qo_rattachees`: **QO-A1** (Project sans Company ?) · `depends_on`: [Epic 10]

**Acceptance Criteria**

**AC1** — **Given** un user authentifié sans Company, **When** il soumet `POST /api/companies` avec payload valide (nom ≥ 2 chars, secteur parmi les 11 enum, pays parmi UEMOA/CEDEAO francophone, taille parmi `micro/petite/moyenne`), **Then** l'endpoint retourne 201 en < 500 ms p95 **And** le user est automatiquement promu `owner` sur cette Company.

**AC2** — **Given** un user ayant déjà une Company `owner`, **When** il tente d'en créer une seconde, **Then** l'endpoint retourne 409 Conflict avec message « 1 Company owner max par user MVP » (à relaxer Phase Growth).

**AC3** — **Given** un payload invalide (secteur hors enum, pays hors scope, taille non reconnue), **When** soumis, **Then** 422 avec erreurs Pydantic lisibles (i18n FR — NFR65).

**AC4** — **Given** RLS activée (Story 10.5), **When** un autre user `GET /api/companies/{other_id}`, **Then** 404 (RLS masque) **And** audit log de la tentative (NFR69).

**AC5** — **Given** QO-A1 tranchée (projet sans company ? réponse attendue : **NON** en MVP), **When** un dev tente d'implémenter `Project` sans `company_id`, **Then** la FK NOT NULL bloque au niveau BDD.

**AC6** — **Given** la suite de tests, **When** exécutée, **Then** scénarios (create owner auto, duplicate 409, validation 422, RLS isolation) verts + coverage ≥ 80 %.

---

### Story 11.2 : Invitation de collaborateurs (editor, viewer, auditor) + révocation

**As a** PME User (owner),
**I want** inviter des collaborateurs avec rôles `editor` / `viewer` / `auditor` et révoquer leur accès à tout moment,
**So that** mon comptable, mon conseiller ESG externe et un auditeur ponctuel puissent contribuer sans accès permanent non maîtrisé.

**Metadata (CQ-8)** — `fr_covered`: [FR2, FR3] · `nfr_covered`: [NFR12, NFR14, NFR28] · `phase`: 1 · `cluster`: A · `estimate`: M · `depends_on`: [11.1]

**Acceptance Criteria**

**AC1** — **Given** un owner authentifié, **When** `POST /api/companies/{id}/invitations` avec email + rôle ∈ {`editor`, `viewer`, `auditor`}, **Then** 201 + email invitation Mailgun (NFR45) en < 30 s **And** lien signé TTL 48 h.

**AC2** — **Given** un invité clique sur le lien, **When** le token est valide, **Then** l'accès est activé avec rôle demandé **And** un event `user_invited` est émis vers `domain_events` (Story 10.10).

**AC3** — **Given** un `auditor` dont le token est expirable (72 h par défaut), **When** la TTL est dépassée, **Then** l'accès est automatiquement révoqué **And** audit log (NFR69).

**AC4** — **Given** un owner `DELETE /api/companies/{id}/members/{user_id}`, **When** appelé, **Then** 204 + révocation immédiate + event `user_revoked` **And** les sessions JWT actives de ce user sont invalidées en < 1 min.

**AC5** — **Given** un `viewer` tente une opération write (ex. `POST /api/facts`), **When** la requête atteint le backend, **Then** 403 (RBAC enforcement).

**AC6** — **Given** la couverture, **When** mesurée, **Then** ≥ 85 % sur le service d'invitation (code critique — contrôle d'accès NFR60).

---

### Story 11.3 : Création / mise à jour de Project avec cycle de vie

**As a** PME User (editor ou owner),
**I want** créer un ou plusieurs Projects rattachés à ma Company et faire évoluer l'état parmi `idée / faisabilité / bancable / exécution / achevé`,
**So that** je puisse structurer mon portefeuille de projets et en suivre la maturité pour cibler les bonnes voies de financement.

**Metadata (CQ-8)** — `fr_covered`: [FR4, FR5] · `nfr_covered`: [NFR12, NFR63] · `phase`: 1 · `cluster`: A · `estimate`: M · `depends_on`: [11.1, 10.9 (`ENABLE_PROJECT_MODEL=true`)]

**Acceptance Criteria**

**AC1** — **Given** `ENABLE_PROJECT_MODEL=true` + user `editor`/`owner`, **When** `POST /api/projects` avec nom + description + `state='idée'`, **Then** 201 + `project.id` retourné **And** la Company peut désormais en créer N sans limite MVP.

**AC2** — **Given** un Project en `idée`, **When** `PATCH /api/projects/{id}` avec `state='faisabilité'`, **Then** transition enregistrée + timestamp + audit log + event `project_state_changed` dans `domain_events`.

**AC3** — **Given** une transition illégale (ex. `exécution → idée`), **When** tentée, **Then** 400 avec liste des transitions autorisées (state machine documentée).

**AC4** — **Given** `ENABLE_PROJECT_MODEL=false`, **When** `POST /api/projects`, **Then** 404 (feature masquée — Story 10.2 AC4 harmonisée).

**AC5** — **Given** la couverture, **When** mesurée, **Then** ≥ 80 % sur le module `projects`.

---

### Story 11.4 : Project porté en solo OU consortium via `ProjectMembership`

**As a** PME User (owner),
**I want** déclarer un Project comme porté en solo (1 Company) OU en consortium (N Companies) via `ProjectMembership` avec rôles assignables,
**So that** les coopératives et JV (Journey 2 Moussa — COOPRACA) puissent être modélisées sans contournement.

**Metadata (CQ-8)** — `fr_covered`: [FR6] · `nfr_covered`: [NFR64] · `phase`: 1 · `cluster`: A · `estimate`: M · `depends_on`: [11.3]

**Acceptance Criteria**

**AC1** — **Given** Project créé, **When** `POST /api/projects/{id}/memberships` avec `company_id` + `role ∈ {porteur_principal, co_porteur, beneficiaire}`, **Then** membership créée + cumul de rôles possible (Décision 1).

**AC2** — **Given** un Project sans `porteur_principal`, **When** une action de soumission est tentée, **Then** 409 Conflict (règle métier : 1 `porteur_principal` minimum).

**AC3** — **Given** RLS (Story 10.5), **When** un user d'une Company co-portant visite `GET /api/projects/{id}`, **Then** il voit le Project **And** la RLS le laisse passer via la jointure `ProjectMembership`.

**AC4** — **Given** la couverture, **When** mesurée, **Then** ≥ 85 % sur le service de membership (critique multi-tenant NFR60).

---

### Story 11.5 : Admin ajoute un nouveau `project-membership role` via workflow N2

**As a** Admin Mefali,
**I want** ajouter un nouveau rôle de membership au-delà de l'enum initial via workflow N2 (peer review catalogue),
**So that** l'écosystème puisse évoluer (ex. ajouter `facilitateur_local`, `pme_sous_traitante`) sans redéploiement.

**Metadata (CQ-8)** — `fr_covered`: [FR7] · `nfr_covered`: [NFR63] · `phase`: 1 · `cluster`: A · `estimate`: M · `depends_on`: [10.4 (admin_catalogue), 11.4]

**Acceptance Criteria**

**AC1** — **Given** l'UI admin `/admin/catalogue/membership-roles/`, **When** un `admin_mefali` crée un nouveau rôle + soumet pour N2, **Then** l'entité passe `draft → review_requested` (state machine Décision 6).

**AC2** — **Given** un 2ᵉ `admin_mefali` approuve, **When** `publish` cliqué, **Then** le rôle devient disponible pour les PME Users sans redéploiement **And** audit trail (Story 10.12).

**AC3** — **Given** un rôle publié est utilisé dans des memberships actives, **When** un admin tente `archive`, **Then** 409 Conflict (référence encore en cours — archivage après migration).

---

### Story 11.6 : Rattacher un `BeneficiaryProfile` aux membres du projet

**As a** PME User (owner/editor),
**I want** attacher à mes membres de projet un `BeneficiaryProfile` agrégeant genre, revenus moyens, taux de formalisation,
**So that** les indicateurs d'impact (ODD 5, 8, 10) soient directement disponibles pour les livrables bailleurs sans ressaisie.

**Metadata (CQ-8)** — `fr_covered`: [FR8] · `nfr_covered`: [NFR11] · `phase`: 1 · `cluster`: A · `estimate`: M · `depends_on`: [11.4]

**Acceptance Criteria**

**AC1** — **Given** un Project consortium, **When** `POST /api/projects/{id}/beneficiary-profiles` avec payload (N hommes/femmes, tranche revenus, taux formalisation), **Then** 201 + profile ID.

**AC2** — **Given** un livrable bailleur est généré (Epic 15), **When** le moteur demande les indicateurs d'impact, **Then** il lit depuis `BeneficiaryProfile` (pas ressaisie).

**AC3** — **Given** anonymisation PII (NFR11), **When** les données du profile sont envoyées au LLM pour narrative, **Then** aucun nom individuel n'est exposé (agrégats seuls).

---

### Story 11.7 : Bulk-import CSV/Excel de bénéficiaires (Journey 2 Moussa — 152 producteurs)

**As a** PME User (owner) d'une coopérative,
**I want** importer en masse mes bénéficiaires / producteurs depuis un template CSV/Excel avec validation + reporting d'erreurs ligne par ligne,
**So that** je n'aie pas à saisir manuellement 152 producteurs un à un (cas COOPRACA).

**Metadata (CQ-8)** — `fr_covered`: [FR9] · `nfr_covered`: [NFR5, NFR50] · `phase`: 1 · `cluster`: A · `estimate`: L · `depends_on`: [11.6, 10.6 (StorageProvider)]

**Acceptance Criteria**

**AC1** — **Given** un template CSV/XLSX téléchargeable depuis `/api/projects/{id}/beneficiaries/template`, **When** un user uploade un fichier ≤ 500 lignes, **Then** l'import retourne en ≤ 30 s p95 avec rapport `{lignes_ok, lignes_erreurs, erreurs_detail}`.

**AC2** — **Given** 10 lignes invalides parmi 152, **When** importé, **Then** **les 142 valides sont persistées** (partial success) **And** les 10 erreurs sont téléchargeables en CSV pour correction.

**AC3** — **Given** un fichier > 500 lignes, **When** uploadé, **Then** l'import bascule en mode asynchrone via `BackgroundTask` + `domain_events` (Story 9.10 / 10.10) avec notification SSE à complétion.

**AC4** — **Given** les tests, **When** exécutés, **Then** scénarios (template correct, 1 ligne, 152 lignes, 10 erreurs partiel, > 500 async, format invalide) verts + coverage ≥ 80 %.

---

### Story 11.8 : Auditor time-bounded scoping sur la Company

> **Renumérotation post-arbitrage Lot 3** : l'ancienne story 11.8 « CompanyProjection curée par Fund » a été **déplacée en Epic 14 (Story 14.1)** pour respecter le DAG Epic 10→11→12→13→14 et éviter un stub Fund. Epic 11 passe à 8 stories (11.1 à 11.8).

**As a** PME User (owner),
**I want** accorder un accès temporaire à un auditeur externe (cabinet comptable, conseiller ESG) avec token expirable,
**So that** il puisse revoir mes données sans accès permanent après la mission.

**Metadata (CQ-8)** — `fr_covered`: [FR67] · `nfr_covered`: [NFR12, NFR13, NFR28] · `phase`: 1 · `cluster`: A · `estimate`: S · `depends_on`: [11.2]

**Acceptance Criteria**

**AC1** — **Given** owner, **When** `POST /api/companies/{id}/auditor-access` avec email + TTL (ex. 7 j), **Then** 201 + email magic link envoyé + token JWT stocké avec `expires_at`.

**AC2** — **Given** l'auditeur consulte, **When** le token expire, **Then** 401 auto **And** sessions actives invalidées en < 1 min (NFR13).

**AC3** — **Given** tout accès auditeur, **When** exécuté, **Then** audit trail (NFR69) avec `actor_id`, `resource_accessed`, `ts`.

**As a** PME User (owner),
**I want** accorder un accès temporaire à un auditeur externe (cabinet comptable, conseiller ESG) avec token expirable,
**So that** il puisse revoir mes données sans accès permanent après la mission.

**Metadata (CQ-8)** — `fr_covered`: [FR67] · `nfr_covered`: [NFR12, NFR13, NFR28] · `phase`: 1 · `cluster`: A · `estimate`: S · `depends_on`: [11.2]

**Acceptance Criteria**

**AC1** — **Given** owner, **When** `POST /api/companies/{id}/auditor-access` avec email + TTL (ex. 7 j), **Then** 201 + email magic link envoyé + token JWT stocké avec `expires_at`.

**AC2** — **Given** l'auditeur consulte, **When** le token expire, **Then** 401 auto **And** sessions actives invalidées en < 1 min (NFR13).

**AC3** — **Given** tout accès auditeur, **When** exécuté, **Then** audit trail (NFR69) avec `actor_id`, `resource_accessed`, `ts`.

---

## Epic 12 — Stories détaillées (Cluster A' — Maturité administrative graduée)

> **Pré-requis** : Epic 10 complet (migration 021, module `maturity/` squelette, RLS). Epic 11 livré (Company rattachée).

### Story 12.1 : Auto-déclaration du niveau de maturité parmi 4

**As a** PME User (owner),
**I want** déclarer mon niveau de maturité administrative actuelle parmi les 4 levels (`informel` / `RCCM+NIF` / `comptes+CNPS` / `OHADA audité`),
**So that** le système me recommande les bons parcours de financement (voie directe vs intermédiée) et la prochaine étape de formalisation.

**Metadata (CQ-8)** — `fr_covered`: [FR11] · `nfr_covered`: [NFR19] · `phase`: 1 · `cluster`: A' · `estimate`: S · `qo_rattachees`: — · `depends_on`: [11.1, 10.3]

**Acceptance Criteria**

**AC1** — **Given** owner authentifié, **When** `POST /api/maturity/declare` avec `level ∈ {informel, rccm_nif, comptes_cnps, ohada_audite}`, **Then** 201 + enregistrement **And** l'état apparaît sur le profil entreprise en < 500 ms p95.

**AC2** — **Given** un niveau déclaré, **When** `PATCH` avec un niveau inférieur (régression), **Then** 400 avec message « Régression de niveau nécessite preuve de liquidation partielle — QO-A'5 à trancher pilote » (soft block).

**AC3** — **Given** la loi SN 2008-12 + CI 2013-450, **When** le user consulte la page maturité, **Then** une mention légale contextuelle apparaît avec source référentiel (NFR27).

---

### Story 12.2 : Validation OCR des justificatifs (RCCM, NINEA/IFU, comptes, bilans)

**As a** PME User (owner),
**I want** uploader mes justificatifs et les faire valider automatiquement par OCR (tesseract `fra+eng` — story 9.4 livrée),
**So that** mon niveau déclaré soit cohérent avec les preuves effectives et que je n'aie pas à attendre une review humaine manuelle.

**Metadata (CQ-8)** — `fr_covered`: [FR12] · `nfr_covered`: [NFR11, NFR44] · `phase`: 1 · `cluster`: A' · `estimate`: M · `qo_rattachees`: **QO-A'1** (OCR validation humaine en boucle ?) · `depends_on`: [12.1, 10.6 StorageProvider, 9.4 OCR bilingue]

**Acceptance Criteria**

**AC1** — **Given** un user uploade un RCCM (PDF ≤ 10 Mo), **When** l'OCR tesseract `fra+eng` tourne, **Then** il extrait `numero_rccm`, `denomination`, `date_immatriculation` **And** retourne score de confiance ≥ 0,8 pour validation auto.

**AC2** — **Given** score < 0,8, **When** constaté, **Then** l'état du document passe `pending_human_review` **And** QO-A'1 tranchée en pilote (fallback humain en boucle à activer si nécessaire).

**AC3** — **Given** un justificatif validé, **When** FR15 (auto-reclassification story 12.5) est déclenché, **Then** l'état maturité peut progresser automatiquement.

**AC4** — **Given** une image illisible, **When** OCR échoue, **Then** message user-friendly + suggestion re-upload avec meilleure résolution.

---

### Story 12.3 : Génération `FormalizationPlan` chiffré XOF + durée + coordonnées pays

**As a** PME User (owner) niveau `informel`,
**I want** un `FormalizationPlan` automatique me guidant du niveau actuel vers le suivant avec coût estimé XOF, durée, coordonnées country-specific (tribunal de commerce, bureau fiscal, caisse sociale),
**So that** je sache concrètement combien ça coûte, combien ça prend et à qui je dois m'adresser.

**Metadata (CQ-8)** — `fr_covered`: [FR13] · `nfr_covered`: [NFR19, NFR66] · `phase`: 1 · `cluster`: A' · `estimate`: L · `qo_rattachees`: **QO-A'3** (niveaux intermédiaires ?), **QO-A'4** (formalisation vs conformité fiscale) · `depends_on`: [12.1, 10.3 (`AdminMaturityRequirement`)]

**Acceptance Criteria**

**Architecture data-driven (arbitrage Lot 3 ajustement 2)** :
- `AdminMaturityRequirement.default_steps: JSONB` — liste des étapes par défaut, configurable par admin (Story 12.6) **sans migration**.
- `FormalizationPlan.steps: JSONB` — copie de `default_steps` au moment de la génération pour immuabilité du plan (pas d'effet rétroactif sur les plans en cours si un admin ajuste `default_steps`).

**AC1** — **Given** un user `informel` au Sénégal, **When** `GET /api/maturity/formalization-plan`, **Then** 200 + plan structuré `{steps: [{step, cost_xof, duration_days, coordinates{name, address, phone, url}}]}` **And** les étapes sont **copiées depuis `AdminMaturityRequirement.default_steps` du pays** au moment de la génération (pas hard-codées dans le code Python).

**AC2** — **Given** des coordonnées pays sourcées (Story 10.11), **When** une coordonnée devient obsolète (`source_unreachable`), **Then** un badge « à vérifier » apparaît dans le plan **And** le user est encouragé à valider sur place.

**AC3** — **Given** QO-A'3 et QO-A'4 ouvertes, **When** le plan est généré MVP, **Then** `default_steps` contient **4 étapes par défaut** (RCCM, NINEA/IFU, adhésion caisse sociale, 1ᵉʳ bilan comptable) injectées au seed initial, **And** le contrat technique est **modifiable sans migration par l'admin Phase Growth** via Story 12.6 (QO-A'3 niveaux intermédiaires + QO-A'4 formalisation vs conformité fiscale tranchées en atelier pilote). Flag explicite dans le schéma OpenAPI : `"default_steps_schema_version: 1 (MVP, évolutif sans breaking change grâce au JSONB)"`.

**AC4** — **Given** un admin `admin_mefali` modifie `default_steps` pour un pays (ex. SN passe à 5 étapes), **When** un nouveau `FormalizationPlan` est généré pour un user SN après la modification, **Then** il utilise les 5 étapes (plan basé sur la dernière version publiée) **And** les plans existants conservent leurs 4 étapes figées (immuabilité `FormalizationPlan.steps`).

**AC5** — **Given** un pays hors UEMOA/CEDEAO francophone, **When** l'user essaie d'accéder, **Then** 404 avec message « Pays non couvert MVP » (extensibilité NFR66 via table BDD).

---

### Story 12.4 : Suivi du `FormalizationPlan` étape par étape avec preuves

**As a** PME User (owner),
**I want** marquer chaque étape de mon `FormalizationPlan` comme `done` en uploadant la preuve correspondante,
**So that** je vois concrètement ma progression et que le système puisse me reclasser automatiquement au niveau supérieur quand toutes les étapes sont validées.

**Metadata (CQ-8)** — `fr_covered`: [FR14] · `nfr_covered`: [NFR5] · `phase`: 1 · `cluster`: A' · `estimate`: M · `depends_on`: [12.3, 12.2 (OCR validation)]

**Acceptance Criteria**

**AC1** — **Given** un plan 4 étapes, **When** user complète l'étape 1 avec upload preuve, **Then** l'étape passe `done` + progression 25 % affichée **And** badge gamification (module 011 existant).

**AC2** — **Given** les 4 étapes `done`, **When** déclenchement `auto-reclassify` (story 12.5), **Then** le niveau maturité progresse automatiquement **And** notification SSE + email.

**AC3** — **Given** une preuve invalide, **When** uploadée, **Then** l'étape reste `pending` **And** message d'aide pour re-upload.

---

### Story 12.5 : Auto-reclassification du niveau après validation des justificatifs

**As a** System,
**I want** re-classifier automatiquement le niveau de maturité d'une PME quand toutes les preuves du niveau suivant sont validées,
**So that** le parcours de formalisation soit une expérience fluide sans intervention manuelle admin.

**Metadata (CQ-8)** — `fr_covered`: [FR15] · `nfr_covered`: [NFR30, NFR37, NFR69] · `phase`: 1 · `cluster`: A' · `estimate`: M · `qo_rattachees`: **QO-A'5** (régression niveau si liquidation partielle) · `depends_on`: [12.4, 10.10 (`domain_events`), 10.12 (audit trail)]

**Pattern régression arbitrage Lot 3 ajustement 3** — soft-block user + self-service + audit trail (PAS escalade admin obligatoire). Raison : cas régression rare + pas d'incitatif fraude (downgrade = perte d'accès fonds) + user mieux placé pour constater. Escalade admin = feature Phase Growth si anomalies détectées a posteriori via monitoring.

**Acceptance Criteria**

**AC1** — **Given** toutes les étapes du plan `done`, **When** le handler `on_plan_completed` est invoqué via `domain_events`, **Then** l'entity `maturity` est updaté vers niveau suivant **And** event `maturity_level_upgraded` émis + notification user + `MaturityChangeLog` audit trail (NFR69) avec `direction='upgrade'`, `reason='plan_completed'`, `actor_id=system`.

**AC2** — **Given** un user veut signaler une régression (QO-A'5 — perte d'un justificatif critique, liquidation partielle), **When** il clique « Signaler un changement de niveau » sur `/maturity`, **Then** **un modal de confirmation explicite** s'affiche : « Vous signalez la perte du justificatif X. Votre niveau passera de 2 (`rccm_nif`) à 1 (`informel`). Vous perdrez l'accès à **N fonds** actuellement recommandés. Confirmer ? » **And** l'action est **self-service** (pas d'escalade admin bloquante).

**AC3** — **Given** l'user confirme la régression, **When** l'action est persistée, **Then** le niveau est downgradé + `MaturityChangeLog(direction='downgrade', reason=<choix user parmi enum>, justification_text, actor_id=<user_id>, ts)` inséré **And** un event `maturity_level_downgraded_self_service` est émis vers `domain_events` pour monitoring admin (pas d'approbation requise).

**AC4** — **Given** monitoring admin (dashboard FR55 Epic 17), **When** `N > seuil` régressions self-service détectées sur une période, **Then** alerte admin pour investigation a posteriori (possible signe de fraude ou bug — mais pas bloquage par défaut).

**AC5** — **Given** les tests, **When** exécutés, **Then** scénarios (upgrade auto post-plan_completed, downgrade self-service avec modal, audit trail persisté, event émis, pas d'escalade admin requise MVP) tous verts + coverage ≥ 85 % (code critique NFR60 — maturité affecte matching fonds).

---

### Story 12.6 : Admin maintien `AdminMaturityRequirement` par pays (UEMOA/CEDEAO)

**As a** Admin Mefali,
**I want** maintenir les requirements `(country × level)` pour chaque pays UEMOA/CEDEAO francophone via l'UI admin (N2 peer review),
**So that** les PME sénégalaises, ivoiriennes, béninoises, togolaises, burkinabé, maliennes, nigériennes voient leurs propres procédures (pas une soupe générique).

**Metadata (CQ-8)** — `fr_covered`: [FR16] · `nfr_covered`: [NFR27, NFR66] · `phase`: 1 · `cluster`: A' · `estimate`: M · `depends_on`: [10.4 admin_catalogue, 10.11 sourcing, 10.12 audit trail]

**Acceptance Criteria**

**AC1** — **Given** un admin crée un requirement `(country=SN, level=rccm_nif)`, **When** il saisit les étapes, coûts, coordonnées, `source_url`, **Then** l'entité passe `draft → review_requested` (N2 peer review Décision 6).

**AC2** — **Given** un 2ᵉ admin approuve + publie, **When** le seed est consommé par `FormalizationPlan.generate()`, **Then** le plan utilise les valeurs mises à jour sans redéploiement.

**AC3** — **Given** FR62 (SOURCE-TRACKING), **When** un requirement est publié sans `source_url`, **Then** bloqué en `draft` (enforcement Story 10.11).

**AC4** — **Given** la CI nightly (Story 10.11), **When** une `source_url` devient `source_unreachable`, **Then** le requirement est marqué visible pour admin intervention **And** les PME voient un badge « à vérifier » sur leur plan (Story 12.3 AC2).

---

---

## Epic 13 — Stories détaillées (Cluster B — ESG multi-contextuel 3 couches)

> **Pré-requis** : Epic 10 complet (migration 022 ESG 3-layers + DSL Pydantic + micro-Outbox AR-D3 invalidation cache + admin_catalogue N1/N2/N3). Story 9.14 livrée (SECTOR_WEIGHTS complet avant migration BDD Story 13.7).
>
> **Architecture 3 couches (Décision 3)** :
> - **Couche 1 — Atomic Facts** : faits unitaires attestables (quanti + quali), versionnés temporellement, rattachés à evidence.
> - **Couche 2 — Composable Criteria** : critères composables qui lisent les facts et déclenchent des rules DSL.
> - **Couche 3 — Verdicts** : PASS/FAIL/REPORTED/N/A dérivés automatiquement + traçabilité vers facts + rules.
>
> **Packs** = assemblages façade (IFC Bancable, EUDR-DDS, Artisan Minimal) qui activent un sous-ensemble de critères + pondérations contextuelles.

### Story 13.1 : Enregistrement de faits atomiques quanti + quali avec evidence

**As a** PME User (editor ou owner),
**I want** enregistrer des faits atomiques (ex. « émissions CO2eq Scope 1 = 12 tCO2e/an » ou « politique SST formalisée = oui ») avec documents de preuve rattachés,
**So that** le système puisse dériver automatiquement mes verdicts multi-référentiels à partir d'un seul jeu de faits partagé (source unique de vérité).

**Metadata (CQ-8)** — `fr_covered`: [FR17] · `nfr_covered`: [NFR11, NFR27, NFR60] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [Epic 10 migration 022, Story 10.6 StorageProvider, Story 9.7]

**Acceptance Criteria**

**AC1** — **Given** un user authentifié, **When** `POST /api/facts` avec `{fact_type_id, value (numérique ou booléen ou enum), unit, period, evidence_ids: []}`, **Then** 201 + fact persisté avec `company_id` + `project_id` + `valid_from=now`, `valid_until=null`.

**AC2** — **Given** un `fact_type` défini dans le catalogue avec `value_schema` Pydantic (DSL borné AR-D3), **When** une valeur non conforme est soumise, **Then** 422 avec validation Pydantic explicite (ex. « Scope 1 doit être un float ≥ 0 »).

**AC3** — **Given** evidence_ids rattachés, **When** le fact est persisté, **Then** la cohérence referential est vérifiée (documents existent + appartiennent au même tenant RLS) **And** lien many-to-many `fact_evidence` peuplé.

**AC4** — **Given** le micro-Outbox AR-D3, **When** un fact est créé/modifié, **Then** un event `fact_changed` est émis dans `domain_events` pour invalidation du cache verdicts (story 13.4) **dans la même transaction**.

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_esg_3layers/test_facts.py` exécuté, **Then** coverage ≥ 85 % (code critique NFR60 — base de tous les verdicts).

---

### Story 13.2 : Evidence multi-type (doc, vidéo CLIP, déclaration honneur, signature témoin)

**As a** PME User (owner) du secteur informel,
**I want** attester mes faits qualitatifs via plusieurs types de preuves : upload document PDF/image, témoignage vidéo (CLIP contextes extractif/agricole), déclaration sur l'honneur signée électroniquement, signature d'un témoin (grief mechanism),
**So that** le marché informel AO soit éligible aux référentiels exigeants sans être exclu pour manque de preuves formelles.

**Metadata (CQ-8)** — `fr_covered`: [FR18] · `nfr_covered`: [NFR11, NFR22, NFR44] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [13.1, 10.6 StorageProvider]

**Acceptance Criteria**

**AC1** — **Given** `POST /api/evidence` avec `{fact_id, type ∈ {document, video, declaration_honor, witness_signature}}`, **When** le type = `document` (PDF/image ≤ 50 Mo), **Then** upload multipart + OCR si applicable + stockage via `StorageProvider` (S3 EU-West-3).

**AC2** — **Given** type = `video`, **When** uploadée (MP4 ≤ 500 Mo), **Then** preview généré + transcodage thumbnail + fact marqué `evidence_pending_review_CLIP` pour le pilote (QO future : intégration CLIP inference).

**AC3** — **Given** type = `declaration_honor`, **When** l'user signe électroniquement (checkbox + saisie nom + timestamp), **Then** une attestation PDF générée (WeasyPrint) avec hash cryptographique + archive immuable.

**AC4** — **Given** type = `witness_signature`, **When** un 2ᵉ user (témoin non affilié à la Company) signe le fait via un lien magic, **Then** la signature est enregistrée + audit trail + le fact bénéficie d'une pondération réputationnelle dans le scoring.

**AC5** — **Given** les tests, **When** exécutés sur les 4 types, **Then** chaque type testé en happy path + erreur (fichier trop gros, format invalide, expiration lien témoin).

---

### Story 13.3 : Versioning temporel des faits (valid_until + historique)

**As a** System,
**I want** versionner les faits temporellement (un fait obsolète voit son `valid_until` posé + une nouvelle version créée avec `valid_from=now`),
**So that** l'historique des mesures soit préservé indéfiniment (NFR20) et que les `FundApplication` puissent référencer la version valide au moment de leur snapshot (FR39).

**Metadata (CQ-8)** — `fr_covered`: [FR19] · `nfr_covered`: [NFR20, NFR23] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.1]

**Acceptance Criteria**

**AC1** — **Given** un fact F1 actif, **When** user soumet `PATCH /api/facts/{F1.id}` avec nouvelle value, **Then** F1 reçoit `valid_until=now` **And** un nouveau fact F2 est créé avec `valid_from=now`, `valid_until=null`, `previous_version_id=F1.id` (chaîne de versions).

**AC2** — **Given** une requête de verdict à `t=T`, **When** le moteur dérive un verdict, **Then** il lit les facts `WHERE valid_from ≤ T AND (valid_until IS NULL OR valid_until > T)` (historique auditable).

**AC3** — **Given** un snapshot `FundApplication` figé (Epic 15), **When** consulté a posteriori, **Then** il référence les `fact_version_id` explicites du moment **And** reste immuable même si les faits évoluent.

**AC4** — **Given** les tests, **When** `test_esg_3layers/test_facts_versioning.py` exécuté, **Then** scénarios (création initiale, 3 versions successives, query historique à un timestamp passé, snapshot préservé) tous verts.

---

### Story 13.4a : Moteur DSL borné Pydantic — exécution d'une rule sur un jeu de facts

**As a** System,
**I want** un moteur d'exécution de rules DSL borné (Pydantic typed expressions, enum verdict `PASS/FAIL/REPORTED/N/A`, sandbox timeout 5 s par rule),
**So that** les admins définissent des rules déclaratives sans exposer le système à du code arbitraire ni à des boucles infinies.

**Metadata (CQ-8)** — `fr_covered`: [FR20 partiel] · `nfr_covered`: [NFR2, NFR60] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [13.1, 10.4 (admin_catalogue)]

**Acceptance Criteria**

**AC1** — **Given** un `Rule` défini avec expression DSL Pydantic (ex. `{operator: "gte", left: "fact.co2e_scope1", right: 12}`), **When** exécutée contre un jeu de facts valides, **Then** elle retourne `VerdictValue ∈ {PASS, FAIL, REPORTED, N/A}` + `rationale` structurée + `facts_used: [fact_version_id]`.

**AC2** — **Given** un fact requis manquant OU `valid_until < now()` (**QO-B3 tranchage explicite MVP**), **When** la rule s'exécute, **Then** verdict = **`N/A` explicite** (pas NULL, pas PASS par défaut) **And** `rationale = 'fact_missing'` ou `'fact_expired'` **And** `facts_used` liste les fact_ids attendus non fournis.

**AC3** — **Given** une rule catastrophique (division par zéro, boucle infinie, allocation excessive), **When** exécutée dans le sandbox borné (timeout 5 s CPU + limite mémoire 100 Mo), **Then** le verdict est marqué `evaluation_error` **And** admin alerting (NFR40) **And** aucun crash du worker.

**AC4** — **Given** les opérateurs DSL supportés MVP (enum explicite : `eq, ne, lt, lte, gt, gte, in, not_in, has_evidence, boolean_and, boolean_or`), **When** un admin tente d'utiliser un opérateur hors enum, **Then** validation Pydantic rejette à la création de la Rule (pas au runtime).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_esg_3layers/test_dsl_engine.py` exécuté, **Then** scénarios (happy path PASS/FAIL/REPORTED/N/A, fact_missing, fact_expired, timeout rule, sandbox OOM, opérateur invalide) couverts **And** coverage ≥ 85 % (NFR60).

---

### Story 13.4b : Matérialisation `ReferentialVerdict` + invalidation via `domain_events` Outbox

**As a** System,
**I want** matérialiser les verdicts dérivés dans une table `referential_verdict(fact_set_hash, criterion_id, referential_version, verdict, rationale, computed_at)` et invalider cette matérialisation via `domain_events` quand les facts ou rules changent,
**So that** les queries UI (dashboard, drill-down, comparative view) retournent en < 2 s p95 au lieu de ré-exécuter les rules à chaque page-view.

**Metadata (CQ-8)** — `fr_covered`: [FR20 partiel] · `nfr_covered`: [NFR1, NFR2] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.4a, 10.10 (`domain_events` + worker batch 30 s + `FOR UPDATE SKIP LOCKED`)]

**Acceptance Criteria**

**AC1** — **Given** un event `fact_changed` émis par Story 13.1 ou 13.3, **When** consommé par le worker `domain_events`, **Then** les `referential_verdict` rattachés (via `Criterion` dépendant du fact) sont invalidés (`status='stale'`) **And** re-calculés en lazy-eval à la prochaine query OU en batch 30 s.

**AC2** — **Given** une évaluation ESG complète (30–60 critères × 3–5 référentiels actifs), **When** demandée à froid (cache stale), **Then** re-calcul complet en **≤ 30 s p95** (NFR2) **And** les verdicts sont persistés pour les queries suivantes.

**AC3** — **Given** un event `rule_published` (Story 13.8b), **When** consommé, **Then** les `referential_verdict` liés à cette rule sont invalidés sans erreur race-condition grâce au `FOR UPDATE SKIP LOCKED` (Story 10.10).

**AC4** — **Given** idempotence, **When** le worker consomme deux fois le même event (redelivery), **Then** aucune double invalidation ni double calcul (guard par `event_id` unique).

**AC5** — **Given** les tests d'intégration, **When** `pytest backend/tests/test_esg_3layers/test_verdicts_materialization.py` exécuté, **Then** scénarios (invalidation on fact_changed, invalidation on rule_published, re-calcul batch, idempotence redelivery, performance p95) tous verts **And** coverage ≥ 85 %.

---

### Story 13.5 : Traçabilité verdict → facts + rules appliqués (justification auditable)

**As a** PME User + Auditor + Bailleur,
**I want** pour chaque verdict affiché, voir les facts sources et les rules qui ont produit le verdict,
**So that** la justification soit vérifiable et défendable en audit/contrôle bailleur.

**Metadata (CQ-8)** — `fr_covered`: [FR21] · `nfr_covered`: [NFR28, NFR37] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.4a, 13.4b] (correction Step 4 — split 13.4 appliquée Lot 5)

**Acceptance Criteria**

**AC1** — **Given** un verdict V, **When** `GET /api/verdicts/{V.id}/trace`, **Then** 200 + `{verdict, criterion, rule_applied: {id, version, expression}, facts_used: [{fact_id, value, version, evidence_ids}]}`.

**AC2** — **Given** UI PME, **When** le user clique sur un verdict, **Then** un panneau latéral affiche la trace **And** permet de naviguer vers chaque fact et son evidence (NFR71 citation).

**AC3** — **Given** une rule mise à jour (N3 versioning), **When** un vieux verdict est consulté, **Then** la trace affiche la **version de rule effective au moment du calcul** (pas la version courante).

---

### Story 13.6 : Sélection de Pack (IFC Bancable / EUDR-DDS / Artisan Minimal)

**As a** PME User (owner),
**I want** sélectionner un Pack pré-assemblé qui active un sous-ensemble pertinent de critères avec pondérations contextuelles,
**So that** je ne subisse pas 200 critères non pertinents pour mon secteur/maturité (ex. « Artisan Minimal » pour COOPRACA informelle, « IFC Bancable » pour Akissi palme OHADA).

**Metadata (CQ-8)** — `fr_covered`: [FR22] · `nfr_covered`: [NFR1] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.4a, 13.4b, 10.4 admin_catalogue] (correction Step 4 — split 13.4)

**Acceptance Criteria**

**AC1** — **Given** le catalogue Pack MVP (≥ 3 packs : IFC Bancable, EUDR-DDS, Artisan Minimal), **When** user sélectionne via `PATCH /api/projects/{id}/active-pack`, **Then** seuls les critères du pack sont évalués **And** l'UI affiche uniquement les critères concernés.

**AC2** — **Given** 2+ Packs actifs avec seuils contradictoires sur un même critère (**QO-B4 tranchage explicite MVP**), **When** la dérivation s'exécute, **Then** **STRICTEST WINS (min appliqué — pas moyenne pondérée)** tranche conformément Décision 2 **And** `verdict.metadata` inscrit `overridden_by_pack: <pack_id>` pour audit trail (FR21) **And** un log explicite documente quel pack a gagné.

**AC3** — **Given** un changement de pack en cours d'évaluation, **When** appliqué, **Then** les facts restent inchangés **And** les verdicts sont re-calculés pour le nouveau pack (pas de perte de données).

---

### Story 13.7 : Score ESG global pondéré + drill-down + migration SECTOR_WEIGHTS vers BDD

**As a** PME User (owner),
**I want** voir un score ESG global pondéré à travers les référentiels actifs + drill-down par référentiel + par dimension E/S/G + par secteur,
**So that** j'aie une note synthétique pour mon dashboard et une vue détaillée pour cibler mes améliorations.

**Metadata (CQ-8)** — `fr_covered`: [FR23] · `nfr_covered`: [NFR2, NFR60, NFR63] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [13.4b (matérialisation verdicts requise pour agrégation), 9.14 (`SECTOR_WEIGHTS` complet avant migration)] (correction Step 4 — split 13.4)

**Acceptance Criteria**

**AC1** — **Given** une évaluation complète, **When** `GET /api/esg/score?project_id=X`, **Then** 200 en < 5 s p95 avec `{global_score_0_100, per_referential: [{ref, score}], per_dimension: [{E,S,G}], per_sector_context: weights}`.

**AC2** — **Given** la table `sector_weight(sector, referential, dimension, weight, version)` livrée en migration Epic 13, **When** le calcul est effectué, **Then** il lit les pondérations depuis la BDD **(plus depuis `weights.py` hard-codé)** **And** un `TODO migration Epic 13` retiré du code Python (complétion de la transition démarrée en Story 9.14).

**AC3** — **Given** un admin publie un nouveau set de `sector_weight`, **When** le flag de release `NEW_WEIGHTS_VERSION` est poussé, **Then** les scores sont re-calculés en batch asynchrone via `domain_events` **And** les users affectés reçoivent notification (FR34).

**AC4** — **Given** la couverture, **When** mesurée, **Then** ≥ 85 % sur le calcul du score (critique marketing + business NFR60).

---

### Story 13.8a : Scaffolding admin catalogue ESG + CRUD `FactType` + `Criterion` (workflow N1 publish direct)

**As a** Admin Mefali,
**I want** un scaffolding UI admin commun (liste + formulaire multi-étape + preview diff) et les CRUD `FactType` + `Criterion` avec workflow N1 (publish direct par 1 seul admin),
**So that** les entités basse criticité du catalogue ESG soient gérables rapidement sans peer review lourd.

**Metadata (CQ-8)** — `fr_covered`: [FR24 partiel] · `nfr_covered`: [NFR27, NFR28, NFR62] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [10.4 (scaffolding admin), 10.11 sourcing, 10.12 audit trail]

**Acceptance Criteria**

**AC1** — **Given** UI admin `/admin/catalogue/fact-types/` et `/admin/catalogue/criteria/`, **When** un `admin_mefali` crée une entité avec `source_url` + `source_accessed_at` + `source_version`, **Then** l'entité est publiée directement (N1 — pas de review) **And** `admin_catalogue_audit_trail` rempli.

**AC2** — **Given** FR62, **When** admin tente publish sans source, **Then** 422 Pydantic **And** l'entité reste `draft` (Story 10.11 enforcement).

**AC3** — **Given** le scaffolding commun, **When** Stories 13.8b et 13.8c réutilisent les composants (table list, modal diff, formulaire step-by-step, dark mode), **Then** aucune duplication composant frontend **And** factorisation dans `components/admin/catalogue/` (NFR62 réutilisabilité).

**AC4** — **Given** un FactType publié, **When** consommé par Epic 13 Story 13.1 (`POST /api/facts`), **Then** la validation Pydantic dynamique lit le `value_schema` du FactType (pas de hardcoding).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/test_n1_workflow.py` exécuté + tests frontend admin, **Then** scénarios (CRUD FactType, CRUD Criterion, publish N1 direct, blocage source manquant, audit trail rempli) tous verts.

---

### Story 13.8b : Workflow N2 peer review pour `Pack` + `Rule` (2e admin + threaded comments)

**As a** Admin Mefali,
**I want** un workflow N2 où `Pack` et `Rule` (entités haute criticité) nécessitent l'approbation d'un 2ᵉ `admin_mefali` avec threaded comments avant publication,
**So that** les assemblages stratégiques (packs) et la logique dérivée (rules) ne soient pas modifiés en solo sans contrôle croisé.

**Metadata (CQ-8)** — `fr_covered`: [FR24 partiel] · `nfr_covered`: [NFR14, NFR28, NFR76] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [13.8a, 13.4a (validation DSL des Rules)]

**Acceptance Criteria**

**AC1** — **Given** un `admin_mefali` soumet un Pack ou Rule pour review, **When** l'entité passe à `review_requested`, **Then** un 2ᵉ admin est notifié in-app + email Mailgun **And** peut ajouter des threaded comments sur l'entité.

**AC2** — **Given** un 2ᵉ admin ajoute des comments, **When** il demande des changements, **Then** l'entité repasse à `draft` **And** l'auteur original reçoit notification pour itérer.

**AC3** — **Given** le 2ᵉ admin approuve, **When** `publish` cliqué, **Then** l'entité passe à `published` **And** un event `rule_published` ou `pack_published` est émis vers `domain_events` (Story 13.4b invalidation cache).

**AC4** — **Given** l'auteur de l'entité est le même que le reviewer (auto-approbation), **When** tenté, **Then** 403 + message « un 2ᵉ admin distinct doit réviser » (enforcement NFR76 adapté catalogue).

**AC5** — **Given** FR62 SOURCE-TRACKING + validation DSL (13.4a), **When** entité publiée sans source OU avec expression DSL invalide, **Then** blocage au moment du `publish` (pas à la soumission — permet draft avec source partielle).

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/test_n2_workflow.py` exécuté, **Then** scénarios (soumission review, comments threaded, request changes, approve, event émis, auto-approbation bloquée) tous verts.

---

### Story 13.8c : Workflow N3 `Referential` + `ReferentialMigration` (ImpactProjectionPanel + test rétroactif ≥ 50 snapshots + seuil 20 %)

**As a** Admin Mefali,
**I want** un workflow N3 strict pour publier une nouvelle version de `Referential` avec une panel d'impact projection Terraform-style, un test rétroactif obligatoire sur un échantillon stratifié ≥ 50 `FundApplication` snapshots, un seuil d'alerte à 20 % de régression, une `effective_date` planifiée et un plan de transition attaché,
**So that** aucune publication réglementaire (ex. EUDR 2.0) n'explose silencieusement les dossiers en cours (Décision 6 + FR25).

**Metadata (CQ-8)** — `fr_covered`: [FR24 partiel, FR25 support] · `nfr_covered`: [NFR23, NFR28, NFR74] · `phase`: 1 · `cluster`: B · `estimate`: L · `depends_on`: [13.8b] (correction Step 4 — dépendance 13.9 retirée : 13.9 consomme 13.8c, pas l'inverse, circular dependency résolue)

**Acceptance Criteria**

**AC1** — **Given** un admin crée `Referential v2` dans l'UI N3, **When** il lance le dry-run, **Then** le système exécute un test rétroactif sur un **échantillon stratifié de ≥ 50 snapshots** `FundApplication` récents (stratification par secteur + maturité + taille pour représentativité) **And** affiche un **ImpactProjectionPanel style Terraform** (`+ créés`, `~ modifiés`, `- supprimés`, `≠ régression`) avec diff verdict par application.

**AC2** — **Given** l'ImpactProjectionPanel, **When** le **pourcentage de régressions dépasse 20 %**, **Then** un warning rouge s'affiche **And** la publication requiert une justification écrite + double approbation senior (admin_super).

**AC3** — **Given** admin valide, **When** il définit une `effective_date` (ex. J+14), **Then** la version est marquée `scheduled` **And** un job planifié la rendra `published` automatiquement à la date (Story 13.9).

**AC4** — **Given** un `ReferentialMigration(v1 → v2, breaking_changes, plan_transition_text)` est attachée, **When** les PME affectées sont identifiées, **Then** la liste + estimation d'impact (verdicts modifiés par PME) est disponible pour communication proactive (Story 14.9).

**AC5** — **Given** la publication, **When** la version devient `published`, **Then** event `referential_published(v1 → v2)` émis vers `domain_events` pour Story 14.9 (notification stay/migrate PME).

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_admin_catalogue/test_n3_workflow.py` exécuté, **Then** scénarios (dry-run échantillon 50, seuil 20 % warning, effective_date planification, double approval senior, event émis) tous verts **And** coverage ≥ 85 % (code critique NFR60).

---

### Story 13.9 : Publication nouvelle version Referential + `ReferentialMigration` avec plan de transition

**As a** Admin Mefali,
**I want** publier une nouvelle version d'un Referential avec une `ReferentialMigration` décrivant les breaking changes + plan de transition pour les users affectés,
**So that** je respecte FR34 (user choisit stay-snapshot OR migrate) et que l'évolution réglementaire (ex. EUDR 2.0) n'explose pas les dossiers en cours.

**Metadata (CQ-8)** — `fr_covered`: [FR25] · `nfr_covered`: [NFR23, NFR28] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.8c]

**Note scope 13.9** : 13.9 est **focalisée sur le déclenchement** à `effective_date` atteinte (worker batch + notification SSE aux PME impactées + wizard stay/migrate FR34). La **projection d'impact pré-publication** (ImpactProjectionPanel + échantillon 50 snapshots + seuil 20 %) est dans 13.8c. Les deux stories sont complémentaires.

**Acceptance Criteria**

**AC1** — **Given** admin publie `Referential v2`, **When** `ReferentialMigration(v1 → v2, breaking_changes: [...])` est créée, **Then** tous les `FundApplication` actifs utilisant v1 sont listés avec impact estimé (critères modifiés, verdicts potentiellement affectés).

**AC2** — **Given** user affecté, **When** il reçoit la notification FR34, **Then** il peut choisir « Rester en v1 (snapshot figé) » OU « Migrer vers v2 » depuis un wizard.

**AC3** — **Given** l'user choisit « rester v1 », **When** confirmé, **Then** le snapshot v1 est préservé éternellement pour ce FundApplication (FR39 immuabilité).

**AC4** — **Given** l'user choisit « migrer v2 », **When** confirmé, **Then** les verdicts sont re-calculés + review obligatoire user avant soumission (éviter surprises).

---

### Story 13.10 : Vue comparative de scoring multi-référentiels (Journey 3 Akissi)

**As a** PME User OHADA audité (Akissi),
**I want** voir une vue comparative de mes scores pour les mêmes facts à travers différents référentiels (IFC / EUDR / GCF / RSPO),
**So that** je choisisse stratégiquement quel bailleur cibler en premier (Option 3 Akissi = SGES + IFC Bancable + RSPO Certified).

**Metadata (CQ-8)** — `fr_covered`: [FR26] · `nfr_covered`: [NFR1] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.4b, 13.6, 13.7] (correction Step 4 — split 13.4)

**Acceptance Criteria**

**AC1** — **Given** un Project avec ≥ 2 référentiels actifs, **When** `GET /api/esg/compare?project_id=X&referentials=IFC,EUDR,GCF`, **Then** 200 avec matrice `{referential, global_score, strengths, gaps, fit_score_for_bailleur}` en < 2 s p95 (NFR1 cache tiède).

**AC2** — **Given** la vue, **When** l'user clique sur un écart, **Then** drill-down vers les critères différenciants + facts sources (traceabilité FR21).

---

### Story 13.11 : Tests property-based Hypothesis sur non-contradiction verdicts (SC-T6)

**As a** Équipe Mefali (QA/Ops),
**I want** une suite de tests property-based Hypothesis qui vérifie l'invariant de non-contradiction des verdicts multi-référentiels,
**So that** aucune paire de rules ne produise des verdicts logiquement incompatibles pour un même fact (garde-fou de cohérence sémantique).

**Metadata (CQ-8)** — `fr_covered`: [] (couvre FR20, FR21) · `nfr_covered`: [NFR60] · `phase`: 1 · `cluster`: B · `estimate`: M · `depends_on`: [13.4a, 13.4b]

**Acceptance Criteria**

**AC1** — **Given** `backend/tests/test_esg_3layers/test_non_contradiction_property.py`, **When** exécuté avec ≥ 1000 itérations Hypothesis, **Then** aucun scenario ne produit `PASS` et `FAIL` simultanément pour un même `(fact_set, criterion, user_context)`.

**AC2** — **Given** un contre-exemple est trouvé, **When** CI échoue, **Then** le fixture shrink d'Hypothesis fournit le minimal reproducing case + affecté `rule_id(s)`.

**AC3** — **Given** CI, **When** le run dépasse 10 min, **Then** timeout + marqué flaky (à optimiser pas ignorer).

---

## Epic 14 — Stories détaillées (Cube 4D — Matching projet-financement + lifecycle FundApplication)

> **Pré-requis** : Epic 10 complet (indexes GIN cube 4D + admin_catalogue N1 pour Fund/Intermediary). Epic 11 + 12 + 13 livrés (data sources Project, Maturity, ESG).

### Story 14.1 : `CompanyProjection` — vue curée par Fund ciblé (déplacée depuis 11.8)

**As a** PME User (owner),
**I want** générer une vue curée de mon profil entreprise adaptée à chaque Fund ciblé (mise en avant des points qui matchent les critères du fonds),
**So that** mon positionnement stratégique soit optimisé sans mentir (les faits restent identiques, seule la mise en avant change).

**Metadata (CQ-8)** — `fr_covered`: [FR10] · `nfr_covered`: [NFR1, NFR11] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [11.1, **Fund model pré-existant spec 008 livré + Epic 10 Story 10.4 admin_catalogue scaffolding**] (correction forward dependency Step 4 — 14.10 Admin real-time update Fund est une **évolution ultérieure** du model, pas sa création. La création du model `Fund` est antérieure à l'Extension via spec 008 déjà livrée.)

**Acceptance Criteria**

**AC1** — **Given** une Company + un `fund_id` cible, **When** `GET /api/companies/{id}/projection?fund_id=X`, **Then** 200 avec vue curée (sections mises en avant = critères du fonds) en < 2 s p95.

**AC2** — **Given** la projection, **When** relue, **Then** aucun fait n'est inventé (toute donnée vient de facts Epic 13 — garde-fou RT-2).

**AC3** — **Given** un Fund sans critères explicites, **When** la projection est demandée, **Then** fallback vue neutre (pas d'hallucination — guards NFR74).

---

### Story 14.2 : Query cube 4D matcher (project × company × referentials × access route)

**As a** PME User (owner ou editor),
**I want** interroger le matcher cube 4D (project maturity × company maturity × required referentials × access route) et recevoir des recommandations de fonds triées par pertinence,
**So that** je ne perde pas du temps à candidater à des fonds hors de ma portée actuelle.

**Metadata (CQ-8)** — `fr_covered`: [FR27] · `nfr_covered`: [NFR1, NFR51] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: L · `depends_on`: [Epic 10 indexes GIN AR-D4, Epic 11 Project, Epic 12 Maturity, Epic 13 Referentials]

**Acceptance Criteria**

**AC1** — **Given** un Project + Company, **When** `POST /api/matching/query` avec `{project_id, filters?}`, **Then** 200 en **≤ 2 s p95** (NFR1) avec liste de fonds triée par `fit_score` descendant + cache LRU warmed.

**AC2** — **Given** un cache tiède (≥ 90 % hit rate attendu après warm-up), **When** la même query est relancée < 5 min après, **Then** < 100 ms p95 (cache hit).

**AC3** — **Given** les indexes GIN cube 4D, **When** un audit de plan `EXPLAIN` est fait sur la hot path, **Then** **aucun Seq Scan** sur `fund` ou `fund_intermediary_liaison` (condition Story 10.7 AC7).

**AC4** — **Given** fallback cube 3D (RT-1 mitigation), **When** le cube 4D sature, **Then** la query bascule automatiquement vers une version allégée (3 dimensions sur 4) **And** un warning est loggé pour investigation.

**AC5** — **Given** la couverture, **When** mesurée, **Then** ≥ 85 % sur le matcher (cœur value proposition NFR60).

---

### Story 14.3 : Affichage de la voie d'accès (directe OU intermédiée avec prerequisites)

**As a** PME User (owner),
**I want** pour chaque Fund matché, voir concrètement la voie d'accès (soumission directe OU intermédiaire identifié avec prerequisites + coordonnées à jour),
**So that** je sache immédiatement si je peux déposer moi-même ou si je dois passer par SIB/BOAD (Journey 2 Moussa).

**Metadata (CQ-8)** — `fr_covered`: [FR28] · `nfr_covered`: [NFR1] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [14.2, 10.11 source_url CI]

**Acceptance Criteria**

**AC1** — **Given** un Fund matché, **When** l'UI affiche la carte, **Then** chaque voie d'accès est rendue avec `{type: direct|intermediate, prerequisites, coordinates: {intermediary_name, address, phone, url, last_verified_at}}`.

**AC2** — **Given** un intermédiaire avec `source_url` HTTP ≠ 200 (Story 10.11), **When** affiché, **Then** badge « coordonnées à vérifier » visible **And** l'user peut signaler pour mise à jour admin.

**AC3** — **Given** un Fund sans intermédiaire disponible, **When** affiché, **Then** seule la voie directe est proposée.

---

### Story 14.4 : Critères intermédiaire superposés aux critères Fund

**As a** PME User,
**I want** voir, quand une voie intermédiée est proposée, les critères spécifiques de l'intermédiaire (ex. SIB min 2 ans ancienneté) **en plus** des critères du Fund (ex. BOAD Ligne Verte),
**So that** je n'aille pas découvrir en cours de route un critère bloquant que Mefali connaissait déjà.

**Metadata (CQ-8)** — `fr_covered`: [FR29] · `nfr_covered`: [NFR27] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [14.3, 13.4 (verdicts calculés)]

**Acceptance Criteria**

**AC1** — **Given** un Fund + voie intermédiée + `FundIntermediaryLiaison` avec critères additionnels, **When** l'user voit les détails, **Then** la liste combinée Fund + Intermediary est affichée + statut PASS/FAIL pour chaque critère.

**AC2** — **Given** une superposition conflictuelle (Fund demande X, Intermediary demande Y), **When** évaluée, **Then** **STRICTEST WINS** (Décision 2) tranche **And** le critère le plus strict apparaît.

---

### Story 14.5 : Création `FundApplication` ciblant un Fund + voie d'accès

**As a** PME User (owner),
**I want** créer un `FundApplication` en ciblant un Fund précis + une voie d'accès (directe OU via un intermédiaire spécifique),
**So that** mon dossier soit calibré dès le départ (FR42 — template direct vs template intermédiaire).

**Metadata (CQ-8)** — `fr_covered`: [FR30] · `nfr_covered`: [NFR30, NFR60] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [14.3]

**Acceptance Criteria**

**AC1** — **Given** user, **When** `POST /api/applications` avec `{project_id, fund_id, access_route: direct|intermediate_id}`, **Then** 201 + application en état `draft` + lien vers Project.

**AC2** — **Given** une application `draft`, **When** user revient plus tard, **Then** le brouillon est retrouvé avec toutes les saisies intermédiaires préservées (pas de perte).

**AC3** — **Given** la voie d'accès change en cours, **When** user switch direct → intermediate, **Then** le template sous-jacent change (Epic 15) **And** les sections déjà remplies sont **migrées si possible** OU marquées « à revoir ».

---

### Story 14.6 : Multiples `FundApplication` sur un même Project sans duplication de facts

**As a** PME User (owner),
**I want** créer plusieurs `FundApplication` pour un même Project ciblant différents Funds avec différentes calibrations,
**So that** je puisse diversifier mes candidatures sans dupliquer 200 facts manuellement.

**Metadata (CQ-8)** — `fr_covered`: [FR31] · `nfr_covered`: [NFR64] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: S · `depends_on`: [14.5]

**Acceptance Criteria**

**AC1** — **Given** un Project P avec 150 facts, **When** user crée A1 (Fund GCF) puis A2 (Fund BOAD), **Then** les 2 applications lisent les mêmes facts Epic 13 **And** aucune duplication BDD (pas de `fact_copy_per_application` table).

**AC2** — **Given** les calibrations spécifiques par application (ex. narrative contextualisée), **When** saisies, **Then** stockées dans `application_context` séparé par application.

---

### Story 14.7 : Lifecycle `FundApplication` (draft → submitted_to_bailleur → in_review → accepted/rejected/withdrawn)

**As a** PME User,
**I want** suivre le cycle de vie complet de mon application avec timestamps + notes à chaque étape (`draft → snapshot_frozen → signed → exported → submitted_to_bailleur → in_review → accepted | rejected | withdrawn`),
**So that** je garde un historique fin de mes candidatures (ex. « soumission via portail BOAD le 15 juin, référence #XYZ »).

**Metadata (CQ-8)** — `fr_covered`: [FR32] · `nfr_covered`: [NFR28, NFR30] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: L · `depends_on`: [14.5, Epic 15 pour `snapshot_frozen` + `signed` + `exported`]

**Acceptance Criteria**

**AC1** — **Given** une application `draft`, **When** une transition de statut est déclenchée (manuelle par user OU automatique par Epic 15), **Then** le timestamp + actor + note optionnelle sont persistés dans `application_status_history`.

**AC2** — **Given** user a réellement soumis au bailleur hors Mefali, **When** il clique « Marquer comme soumis », **Then** la transition `exported → submitted_to_bailleur` avec saisie libre (date + référence soumission) est enregistrée.

**AC3** — **Given** l'application est `accepted`, **When** marquée, **Then** un event `application_accepted` émis + gamification (FR51 Epic 17).

**AC4** — **Given** une transition illégale (ex. `draft → accepted`), **When** tentée, **Then** 400 avec liste transitions autorisées (state machine).

---

### Story 14.8 : Archive `FundApplication` rejeté + proposition de remédiation (Journey 4 Ibrahim)

**As a** PME User (owner) dont une candidature vient d'être refusée,
**I want** archiver proprement le FundApplication avec le motif de rejet et recevoir une proposition de remédiation (re-matching avec critères ajustés),
**So that** un refus ne soit pas un cul-de-sac mais un point de départ vers d'autres fonds plus adaptés.

**Metadata (CQ-8)** — `fr_covered`: [FR33] · `nfr_covered`: [NFR30] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [14.7, 14.2 (matcher re-query)]

**Acceptance Criteria**

**AC1** — **Given** une application `rejected`, **When** user saisit le motif (enum + texte libre), **Then** un cube 4D re-matching est déclenché en excluant les causes d'échec **And** 3 à 5 fonds alternatifs suggérés.

**AC2** — **Given** la suggestion, **When** user accepte une alternative, **Then** un nouveau `FundApplication draft` pré-rempli avec les sections compatibles est créé.

---

### Story 14.9 : Notification user sur changement de referential/pack/criterion avec choix stay/migrate

**As a** PME User avec application active,
**I want** être notifié quand un referential/pack/criterion utilisé par mon application est modifié et pouvoir choisir de rester sur mon snapshot ou migrer,
**So that** je ne sois pas surpris par un changement invisible le jour du dépôt.

**Metadata (CQ-8)** — `fr_covered`: [FR34] · `nfr_covered`: [NFR40] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [13.9 (`ReferentialMigration`), 10.10 (`domain_events`)]

**Acceptance Criteria**

**AC1** — **Given** un `referential_published` event, **When** consommé par le worker, **Then** tous les users avec applications actives utilisant la version obsolète reçoivent une notification in-app + email avec wizard.

**AC2** — **Given** le wizard, **When** user choisit « Rester v1 », **Then** le snapshot v1 est marqué explicitement « legacy — version figée » dans l'UI.

**AC3** — **Given** l'user choisit « Migrer v2 », **When** la migration tourne, **Then** les verdicts sont re-calculés + review section-by-section obligatoire avant re-soumission.

---

### Story 14.10 : Admin met à jour Fund / Intermediary / `FundIntermediaryLiaison` en temps réel (N1)

**As a** Admin Mefali,
**I want** mettre à jour les coordonnées Fund, les critères Intermediary et les liaisons Fund-Intermediary en temps réel (N1 workflow) sans redéploiement,
**So that** l'évolution du marché (nouvelles lignes, changements de coordonnées) soit reflétée immédiatement pour les PME.

**Metadata (CQ-8)** — `fr_covered`: [FR35] · `nfr_covered`: [NFR27, NFR28] · `phase`: 1 · `cluster`: Cube 4D · `estimate`: M · `depends_on`: [10.4, 10.11, 10.12]

**Acceptance Criteria**

**AC1** — **Given** UI admin `/admin/catalogue/funds/`, **When** admin mefali modifie un Fund et sauvegarde (N1 direct), **Then** changement effectif en < 5 min **And** cache matching invalidé via `domain_events`.

**AC2** — **Given** une modification, **When** sauvegardée, **Then** `admin_catalogue_audit_trail` (Story 10.12) rempli avec before/after.

**AC3** — **Given** CI nightly (Story 10.11), **When** `source_url` du Fund HTTP 200 perdu, **Then** badge `source_unreachable` visible admin + users affichent la mise en garde Story 14.3 AC2.

---

---

## Epic 15 — Stories détaillées (Cluster C — Moteur livrables bailleurs + SGES BETA NO BYPASS)

> **Pré-requis** : Epic 10 complet (migration 023 deliverables engine + framework prompts CCC-9 + StorageProvider S3 + micro-Outbox). Epic 11 + 12 + 13 + 14 livrés (data sources complets : Company, Project, Maturity, Facts/Verdicts, FundApplication).
>
> **Enjeu juridique** : Story 15.5 SGES BETA NO BYPASS est **story dédiée CQ-5** avec verrou applicatif sans bypass même `admin_super`. Toute tentative de contournement est un **incident sécurité loggé**. Épic à traiter avec rigueur maximale.

### Story 15.1a : Template engine PDF (Jinja2 + WeasyPrint + templates relationnels DB-driven)

**As a** System + Équipe Mefali (backend),
**I want** un template engine DB-driven qui assemble les sections d'un livrable PDF à partir de `template_sections` + `ReusableSection` + `AtomicBlock`, avec rendu Jinja2 + WeasyPrint + assets (logos, charts matplotlib) + tests cross-browser du HTML intermédiaire,
**So that** l'assemblage structurel soit robuste, les templates bailleurs évoluent sans redéploiement (data-driven), et la qualité de rendu soit vérifiable indépendamment de l'IA (garde-fou isolation couches).

**Metadata (CQ-8)** — `fr_covered`: [FR36 partiel, FR42] · `nfr_covered`: [NFR46, NFR60] · `phase`: 1 · `cluster`: C · `estimate`: L · `depends_on`: [Epic 10 migration 023 + StorageProvider]

**Acceptance Criteria**

**AC1** — **Given** table `template_sections(template_id, section_order, block_type, prompt_ref, static_content)` (migration 023) + catalogue `ReusableSection` + `AtomicBlock`, **When** un user demande un preview (sans IA), **Then** le moteur assemble les sections dans l'ordre défini avec placeholders `{{variable}}` **And** un HTML intermédiaire est produit + rendu WeasyPrint → PDF.

**AC2** — **Given** les templates supportés MVP (GCF Funding Proposal, IFC AIMM, EUDR DDS, EIES Cat B, Proparco AIMM, SGES/ESMS BETA), **When** auditée, **Then** chacun est représenté en BDD (pas hardcodé en Python) avec son ordre de sections + ses blocs atomiques référencés.

**AC3** — **Given** le HTML intermédiaire, **When** ouvert dans Chrome + Firefox + Safari (tests Playwright), **Then** le rendu est visuellement cohérent (dimensions, polices, layout multi-page, page breaks) **And** aucun warning WeasyPrint critique dans les logs.

**AC4** — **Given** les assets (logos bailleurs, graphiques matplotlib SVG générés à partir de facts/verdicts), **When** intégrés, **Then** ils sont embarqués dans le PDF (pas de liens externes cassables) **And** chargés depuis `StorageProvider` (Story 10.6).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_applications/test_template_engine.py` exécuté, **Then** scénarios (assemblage template simple, assemblage template lourd, variables résolues, assets intégrés, cross-browser HTML) tous verts **And** coverage ≥ 85 % (NFR60).

---

### Story 15.1b : Intégration guards LLM (9.6) + BackgroundTask async (9.10) + validation perf NFR3/NFR4

**As a** PME User (owner),
**I want** que la génération complète d'un livrable (assemblage template + remplissage des sections IA + guards + async) aboutisse sur un PDF livré en ≤ 30 s p95 (NFR3) pour templates simples et ≤ 3 min p95 (NFR4) pour templates lourds, avec les guards LLM qui bloquent toute hallucination,
**So that** la qualité du livrable soit défendable en audit bailleur et la perf reste compatible avec NFR Performance.

**Metadata (CQ-8)** — `fr_covered`: [FR36 complet] · `nfr_covered`: [NFR3, NFR4, NFR74, NFR75] · `phase`: 1 · `cluster`: C · `estimate`: L · `depends_on`: [15.1a, Story 9.10 BackgroundTask + micro-Outbox, Story 9.6 guards LLM, Story 10.8 framework prompts CCC-9]

**Acceptance Criteria**

**AC1** — **Given** un `FundApplication` + template choisi, **When** l'user déclenche la génération, **Then** l'orchestration `BackgroundTask` (Story 9.10) lance : (1) assemblage template via 15.1a, (2) remplissage sections IA via framework prompts CCC-9, (3) application guards LLM par section (Story 9.6), (4) rendu PDF final.

**AC2** — **Given** une section IA générée, **When** les guards s'appliquent (longueur, langue FR détectée, cohérence numérique avec facts source, vocabulaire interdit « garanti/certifié/validé par »), **Then** toute violation bloque la génération avec message explicite « Section X bloquée : raison Y » (NFR74) **And** l'user peut re-générer avec prompt ajusté.

**AC3** — **Given** un template simple (EUDR DDS ≤ 20 pages), **When** exécuté sous charge (100 users simultanés NFR71), **Then** p95 ≤ 30 s (NFR3) **And** mesure archivée dans le rapport de charge (Story 20.2).

**AC4** — **Given** un template lourd (GCF Funding Proposal, IFC AIMM full, SGES/ESMS BETA), **When** exécuté, **Then** p95 ≤ 3 min (NFR4) **And** si dépassement récurrent, migration prévue vers pool worker dédié Phase Growth (documentée, pas livrée ici).

**AC5** — **Given** une erreur LLM transient, **When** le guard échoue faute de réponse, **Then** retry NFR75 (3 tentatives exponential backoff) **And** échec définitif marqué `report_failed` avec event SSE (Story 9.10 AC5).

**AC6** — **Given** le PDF finalisé, **When** stocké via `StorageProvider`, **Then** URL signée TTL 15 min + event SSE `report_ready` (Story 9.10 AC4).

**AC7** — **Given** les tests d'intégration, **When** `pytest backend/tests/test_applications/test_pdf_end_to_end.py` exécuté, **Then** scénarios (happy path template simple, happy path template lourd, échec guards, retry transient, fallback erreur définitive, performance) tous verts **And** coverage ≥ 85 %.

---

### Story 15.2 : Génération DOCX éditable en parallèle du PDF

**As a** PME User (owner) ou son consultant,
**I want** obtenir une version DOCX éditable de chaque livrable en parallèle du PDF,
**So that** un expert humain puisse réviser manuellement avant export final (pattern Akissi + Ibrahim).

**Metadata (CQ-8)** — `fr_covered`: [FR37] · `nfr_covered`: [NFR47] · `phase`: 1 · `cluster`: C · `estimate`: M · `depends_on`: [15.1]

**Acceptance Criteria**

**AC1** — **Given** la génération lancée, **When** `export_format=docx` ou `both`, **Then** `python-docx` (NFR47) produit le DOCX à partir du même AST intermédiaire que le PDF (pas de double génération LLM) en ≤ 60 s p95.

**AC2** — **Given** un DOCX généré, **When** ouvert dans Word/LibreOffice, **Then** la mise en forme reproduit fidèlement la structure du PDF (headings, tableaux, images) **And** les champs variables (`{{company_name}}`, etc.) sont résolus (pas de placeholder laissé).

**AC3** — **Given** un utilisateur modifie le DOCX localement, **When** il le ré-uploade dans Mefali, **Then** l'upload est accepté et tracé comme « version post-review humaine » sur le `FundApplication` (pas de re-génération auto).

---

### Story 15.3 : Annexe automatique des evidence aux livrables (avec mode sélectif)

**As a** PME User (owner),
**I want** que les evidence rattachés aux facts utilisés dans le livrable soient automatiquement annexés (avec option mode sélectif pour exclure ce qui est confidentiel),
**So that** le bailleur ait les preuves documentées sans que je fasse un zip manuel + que je puisse exclure les données bancaires sensibles.

**Metadata (CQ-8)** — `fr_covered`: [FR38] · `nfr_covered`: [NFR11, NFR22] · `phase`: 1 · `cluster`: C · `estimate`: M · `depends_on`: [15.1, 13.2 (evidence)]

**Acceptance Criteria**

**AC1** — **Given** un livrable en génération, **When** le moteur identifie les facts utilisés, **Then** il collecte les `evidence_ids` rattachés **And** les annexe automatiquement dans un dossier `annexes/` du package livré (PDF fusionné OU zip).

**AC2** — **Given** mode sélectif activé, **When** user décoche certaines evidence avant export, **Then** elles sont exclues du package **And** un warning affiche « N evidence exclues — le bailleur pourrait les demander ultérieurement ».

**AC3** — **Given** consent partage explicite FR-22 NFR22, **When** evidence contient des PII sensibles, **Then** un deuxième consentement modal est requis avant inclusion dans le package.

---

### Story 15.4 : Snapshot cryptographique `FundApplication` au moment de génération (hash immuable)

**As a** System,
**I want** figer cryptographiquement toutes les données sources (facts version_ids, verdicts, referential_versions, company state, project state) au moment de la génération d'un livrable, avec hash SHA-256 stocké en BDD,
**So that** l'immuabilité du dossier soumis soit garantie en cas de litige (FR39 + NFR28 audit trail immuable).

**Metadata (CQ-8)** — `fr_covered`: [FR39, FR57] · `nfr_covered`: [NFR20, NFR28] · `phase`: 1 · `cluster`: C · `estimate`: L · `depends_on`: [15.1, 10.10 (`domain_events` atomicité CCC-14), 10.12 (audit trail)]

**Acceptance Criteria**

**AC1** — **Given** une génération finalisée, **When** le snapshot est créé, **Then** il contient `{fact_version_ids, verdict_ids, referential_versions, company_snapshot, project_snapshot, pack_version, template_version, prompt_versions, llm_model, llm_params, generated_at, user_id}` sérialisé en JSONB **And** un hash SHA-256 est calculé sur la représentation canonique.

**AC2** — **Given** le snapshot + hash, **When** persistés, **Then** insertion atomique dans `FundApplicationSnapshot` **dans la même transaction** que la mise à jour du `FundApplication` (CCC-14) **And** event `application_snapshot_frozen` émis.

**AC3** — **Given** `FundApplicationGenerationLog(llm_version, timestamp, anonymized_prompts, referential_versions, snapshot_hash, user_id)` (FR57), **When** la génération est complétée, **Then** une entrée est créée **And** les prompts envoyés au LLM sont anonymisés (PII masquées NFR11) avant stockage.

**AC4** — **Given** un snapshot vieux, **When** consulté par l'user OU par un auditeur légitime, **Then** il est reproductible à l'identique (même hash) **And** la rétention suit NFR20 (10 ans min SGES/ESMS + associés).

**AC5** — **Given** un attaquant tente d'altérer un snapshot en base, **When** détecté (trigger PostgreSQL append-only + re-hash de vérification), **Then** l'anomalie est loggée comme incident sécurité (NFR28) **And** alerting admin.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_applications/test_snapshot.py` exécuté, **Then** scénarios (snapshot atomic, hash stable, re-génération identique, rétention 10 ans policy, altération bloquée) tous verts **And** coverage ≥ 85 % (code critique NFR60).

---

### Story 15.5 : SGES/ESMS BETA — workflow de revue humaine consultant NO BYPASS avec verrou applicatif (CQ-5)

**As a** System + Admin Mefali (gardien de la conformité),
**I want** qu'aucun livrable SGES/ESMS BETA Phase 1 ne puisse être exporté sans revue humaine consultant validée, **sans bypass possible même pour `admin_mefali` ou `admin_super`**, avec logging de toute tentative comme incident de sécurité,
**So that** l'enjeu juridique (livrable erroné → responsabilité Mefali contractuelle) soit verrouillé au niveau applicatif et pas seulement procédural (FR44 + clause protection PME Phase 1 BETA).

**Metadata (CQ-8)** — `fr_covered`: [FR44] · `nfr_covered`: [NFR14, NFR18, NFR28, NFR76] · `phase`: 1 · `cluster`: C · `estimate`: XL · `depends_on`: [15.1, 15.4, 10.12 (audit trail)] · `story_dedicated`: **CQ-5** (garde-fou explicite readiness report)

**Acceptance Criteria**

**AC1** — **Given** un `FundApplication` avec `template_type='sges_esms_beta'`, **When** l'user demande `export`, **Then** un **verrou applicatif** (`export_blocked_reason='sges_beta_consultant_review_required'`) est enforcé **And** l'endpoint `POST /api/applications/{id}/export` retourne 409 Conflict **sans exception** (pas de paramètre `force=true`, pas de query string bypass).

**AC2** — **Given** un `admin_mefali` ou `admin_super` tente d'exporter, **When** la requête atteint le backend, **Then** le même verrou bloque **sans exception de rôle** **And** l'event est traité en **deux couches distinctes** :
  - **Log systématique (sans exception)** : insertion `security_events(user_id, role, ip, user_agent, timestamp, path, result, bypass_context)` pour TOUTE tentative, sans filtre. `bypass_context` capture `{maintenance_mode: bool, reason_comment: str|null, pair_admin_id: UUID|null}` si admin a renseigné **avant** la tentative (pre-declared).
  - **Ticket automatique (conditionnel)** Sentry/PagerDuty déclenché SI `(frequency > 3 attempts/heure) OR (hors heures ouvrées : < 6h OR > 22h heure pays admin configurable) OR (IP hors whitelist office) OR (role != admin_super)`. Si admin a renseigné `bypass_context` avec `reason_comment` + `pair_admin_id` AVANT tentative, le ticket reste **silencieux** (audit trail conservé).
  - **Review hebdomadaire manuelle** par la security team sur les `security_events` sans ticket (détection patterns lents — exfiltration discrète, reconnaissance).

**AC3** — **Given** un consultant humain externe (intégré via workflow dédié) soumet une revue signée avec score ≥ 4/5, **When** l'entrée `SgesConsultantReview(application_id, reviewer_id, score, comments, signed_at)` est persistée, **Then** le verrou est levé pour **cet `application_id` uniquement** (pas global) **And** event `sges_review_approved` émis.

**AC4** — **Given** admin mefali souhaite retirer le BETA flag (GA Phase 2), **When** les critères sont atteints (**≥ 10 reviews positives avec score ≥ 4/5** historiques), **Then** il peut publier « `sges_esms_beta` → `sges_esms_ga` » via un workflow N3 dédié (Story 13.8c pattern) **And** le verrou NO BYPASS est désactivé pour ce template via migration Alembic dédiée.

**AC5** — **Given** 10 critères GA non atteints, **When** admin tente le passage GA, **Then** 403 + message explicite listant les critères manquants (compteur persistant).

**AC6** — **Given** pen test externe (Story 20.3), **When** un attaquant tente d'exploiter le workflow (injection SQL, manipulation state machine, bypass rôle), **Then** aucun bypass exploitable **And** toutes tentatives loggées (condition de passage pilote — NFR18).

**AC7** — **Given** les tests (**confirmation coverage 95 %** au-dessus NFR60 standard — enjeu juridique), **When** `pytest backend/tests/test_applications/test_sges_no_bypass.py` exécuté, **Then** la batterie OBLIGATOIRE couvre :
  - tentative bypass via URL directe (curl + query string `force=true` + headers `X-Bypass`),
  - tentative bypass via API JSON malformée / paramètre caché,
  - tentative par `admin_super` (bloquée + contexte bypass_context testé),
  - tentative par `auditor` (bloquée),
  - session expirée (401 → pas de bypass partiel),
  - token invalide / forgé / replay (403),
  - SQL injection patterns sur `application_id`, `reviewer_id` (ORM Pydantic + tests `'; DROP TABLE--`, `' OR 1=1--`),
  - **race conditions** guard vs génération (concurrent PUT review + POST export — le verrou doit être atomique via transaction PG),
  - audit trail complet (chaque tentative produit exactement 1 ligne `security_events`),
  - ticket conditionnel (fréquence > 3/h, hors heures, IP hors whitelist, rôle non-admin_super),
  - review approuvée lève verrou **pour cet `application_id` uniquement** (pas d'effet de bord autre applicaiton),
  - GA workflow N3 avec compteur 10 reviews positives (< 10 = 403 avec détail manquant)
  tous verts **And** coverage ≥ **95 %** (code critique juridique — au-dessus NFR60 standard 85 %). **Pen test externe Story 20.3 = validation boîte noire complémentaire.**

**AC8** — **Given** la documentation, **When** reviewée, **Then** un document `docs/security/sges-no-bypass-invariants.md` décrit l'invariant, les chemins de code concernés, la procédure GA, et déclare explicitement « aucun bypass sera ajouté, aucun flag `force`, aucune query string » pour contributions futures.

---

### Story 15.6 : Attestation électronique user obligatoire avant export (signature checkbox + modal)

**As a** PME User (owner),
**I want** signer électroniquement une attestation avant chaque export de livrable destiné à un bailleur,
**So that** je confirme la véracité des données + ma responsabilité, conformément aux exigences bailleur et à FR40.

**Metadata (CQ-8)** — `fr_covered`: [FR40] · `nfr_covered`: [NFR14, NFR28] · `phase`: 1 · `cluster`: C · `estimate`: M · `depends_on`: [15.1, step-up MFA Epic 18]

**Acceptance Criteria**

**AC1** — **Given** user clique sur « Exporter », **When** le modal s'ouvre, **Then** il affiche le texte d'attestation (données véridiques, conscient responsabilité contractuelle) **And** requiert (a) checkbox explicite « Je confirme et signe » **(b)** saisie nom complet **(c)** step-up MFA (FR61 + NFR14).

**AC2** — **Given** l'attestation signée, **When** persistée, **Then** une ligne `ApplicationAttestation(user_id, application_id, signed_at, ip, user_agent, attestation_hash)` est créée **And** l'export est débloqué.

**AC3** — **Given** l'user refuse ou ferme le modal, **When** tenté, **Then** l'export est bloqué **And** aucune trace « consentement inféré » ne peut être créée (consentement explicite obligatoire NFR22).

---

### Story 15.7 : Blocage export > 50 000 USD sans review humaine section-par-section

**As a** System,
**I want** bloquer l'export d'un livrable dont le montant demandé dépasse 50 000 USD tant que l'user n'a pas confirmé avoir revu section par section,
**So that** les gros dossiers bénéficient d'une friction protective (FR41) évitant les soumissions IA non-revues à fort enjeu.

**Metadata (CQ-8)** — `fr_covered`: [FR41] · `nfr_covered`: [NFR74] · `phase`: 1 · `cluster`: C · `estimate`: M · `depends_on`: [15.1]

**Acceptance Criteria**

**AC1** — **Given** `FundApplication.amount_requested_usd > 50000`, **When** l'export est tenté, **Then** un checklist modal affiche toutes les sections du livrable **And** l'user doit cliquer explicitement « Section revue » pour chacune avant que `export` soit débloqué.

**AC2** — **Given** une section marquée revue, **When** la trace est persistée, **Then** `ApplicationSectionReview(user_id, application_id, section_id, reviewed_at)` créée **And** l'UI affiche un indicateur de progression.

**AC3** — **Given** 1 section non revue, **When** user tente `export`, **Then** 409 avec liste explicite des sections restantes.

---

### Story 15.8 : Calibration livrable par voie d'accès (direct vs intermédiaire — Journey 2 Moussa)

**As a** PME User (owner) en consortium intermédié,
**I want** que le livrable soit calibré au template intermédiaire (SIB, BOAD) quand je passe par une voie intermédiée, et au template direct sinon,
**So that** je ne soumette pas un dossier IFC-format à une porte BOAD (FR42).

**Metadata (CQ-8)** — `fr_covered`: [FR42] · `nfr_covered`: [NFR46] · `phase`: 1 · `cluster`: C · `estimate`: M · `depends_on`: [15.1, 14.3 (voie d'accès)]

**Acceptance Criteria**

**AC1** — **Given** `FundApplication.access_route='intermediate:SIB'`, **When** export, **Then** le moteur sélectionne le template SIB-spécifique (si disponible) OU un template intermédiaire générique avec encart « adresse SIB, prerequisites SIB ».

**AC2** — **Given** access_route = `direct`, **When** export, **Then** template direct du Fund utilisé.

**AC3** — **Given** un Fund sans template intermédiaire défini, **When** `intermediate` est choisi, **Then** fallback vers template générique + warning admin (à enrichir catalogue).

---

### Story 15.9 : Admin gère catalogue `DocumentTemplate` + `ReusableSection` + `AtomicBlock` (N2)

**As a** Admin Mefali,
**I want** gérer le catalogue de templates, sections réutilisables et blocs atomiques via workflow N2 (peer review) avec versioning de prompts,
**So that** les templates bailleurs évoluent avec leurs mises à jour officielles sans redéploiement (FR43 + Décision 5 prompt versioning).

**Metadata (CQ-8)** — `fr_covered`: [FR43] · `nfr_covered`: [NFR27, NFR28] · `phase`: 1 · `cluster`: C · `estimate`: L · `depends_on`: [10.4, 10.11, 10.12, 13.8b (pattern N2)]

**Acceptance Criteria**

**AC1** — **Given** UI admin `/admin/catalogue/document-templates/`, **When** admin mefali crée un template avec sections ordonnées + prompts rattachés + `source_url` bailleur officiel, **Then** l'entité suit workflow N2 (peer review Story 13.8b).

**AC2** — **Given** un prompt modifié dans un `AtomicBlock`, **When** publié, **Then** un `prompt_version` est incrémenté et les snapshots précédents continuent de référencer la version historique (immuabilité 15.4).

**AC3** — **Given** la CI nightly source (Story 10.11), **When** `source_url` du template devient inaccessible, **Then** badge admin + possibilité mise à jour prioritaire.

---

---

## Epic 16 — Stories détaillées (Copilot conversationnel — extension tool-calling)

> **Contexte brownfield** : specs 012 (tool-calling), 013 (routing multi-tour active_module), 014 (style concis), 015/016/017 (corrections), 018 (widgets interactifs), 019 (floating copilot + guided tours) **déjà livrées**. Epic 16 est une **extension incrémentale** ciblant les nouveaux tools Epic 10–15 (projects, maturity, admin_catalogue, deliverables, cube 4D matching) et les manques FR45–FR50.

### Story 16.1 : Enregistrement tools des nouveaux modules dans LangGraph `chat_node`

**As a** PME User,
**I want** pouvoir invoquer par chat toutes les nouvelles capabilities des clusters A/A'/B/Cube 4D/C (créer Company, déclarer maturité, enregistrer facts, matcher fonds, générer livrable) de la même manière que les modules existants,
**So that** la modalité secondaire « tout invocable par chat » soit complète (FR45).

**Metadata (CQ-8)** — `fr_covered`: [FR45] · `nfr_covered`: [NFR5, NFR17, NFR38] · `phase`: 1 · `cluster`: Copilot · `estimate`: L · `depends_on`: [Story 9.7 instrumentation, Epic 10 nouveaux modules, Epic 11–15 tools métiers]

**Acceptance Criteria**

**AC1** — **Given** les nouveaux tools métier des Epics 11–15 (`projects_tools`, `maturity_tools`, `admin_catalogue_tools` UI-only côté admin, `deliverables_tools`, `cube4d_matching_tools`, `fund_application_tools`), **When** chargés, **Then** ils sont tous enregistrés dans le `ToolNode` LangGraph **And** instrumentés `with_retry` + `log_tool_call` (Story 9.7 garde-fou).

**AC2** — **Given** un user demande « crée-moi un projet agroalimentaire au Sénégal en phase idée », **When** `chat_node` traite, **Then** le LLM invoque `create_project` avec les bons arguments parsés **And** réponse streamée en < 2 s p95 premier token (NFR5).

**AC3** — **Given** une chaîne d'outils (ex. `create_project` → `attach_beneficiary_profile` → `declare_maturity_level`), **When** le LLM orchestre, **Then** max 5 tool calls par turn (pattern spec 012) + retry automatique 1× par tool + timeout LLM 60 s.

**AC4** — **Given** un tool échoue après retry, **When** constaté, **Then** le chat fallback gracieusement avec message « je n'ai pas pu <action>, voici le lien vers le formulaire » (préfigure FR49 Story 16.5).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_graph/test_chat_node_extended_tools.py` exécuté, **Then** scénarios (chaque nouveau tool invoqué, chaîne 3 tools, retry transient, fallback error) tous verts + coverage ≥ 80 %.

---

### Story 16.2 : Extension `ConversationState` avec `active_project` cross-turn

**As a** PME User,
**I want** que le copilot maintienne le contexte du projet actif à travers les tours de conversation (en plus de `active_module` déjà livré spec 013),
**So that** je n'aie pas à ré-indiquer « pour mon projet X » à chaque nouveau message quand je travaille sur un même projet.

**Metadata (CQ-8)** — `fr_covered`: [FR46] · `nfr_covered`: [NFR50] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 013 `active_module` livré]

**Acceptance Criteria**

**AC1** — **Given** `ConversationState`, **When** auditée, **Then** elle porte **toujours** le champ `active_project_id: UUID|null` (schéma unique, pas de variant conditionnel — infra toujours prête) + reducer approprié (pattern spec 013 pour `active_module`) + persistance LangGraph MemorySaver **And** défaut `null` + aucune contrainte `NOT NULL`.

**AC2** — **Given** `ENABLE_PROJECT_MODEL=false` (Story 10.9), **When** `router_node` traite un tour, **Then** il **ignore** la valeur de `active_project_id` dans sa classification (feature masquée côté routing) **And** aucune erreur n'est levée si le champ est déjà peuplé.

**AC3** — **Given** un user dans une conversation avec `active_project_id=P1` et `ENABLE_PROJECT_MODEL=true`, **When** il demande « génère le rapport ESG », **Then** le copilot comprend implicitement `project_id=P1` (pas de ressaisie).

**AC4** — **Given** l'user change de projet dans le chat (« travaillons sur P2 maintenant »), **When** détecté par le routing (spec 013 pattern classification continuation vs changement), **Then** `active_project_id` passe à P2 + event SSE UI updaté + `active_module` réinitialisé.

**AC5** — **Given** une transition flag `false → true` en cours de migration Phase 1, **When** constatée, **Then** **pas de backfill forcé** sur les conversations existantes : `active_project_id` reste `null` **And** est settée progressivement à la prochaine interaction user avec un tool `projects_*` (set progressif lazy).

**AC6** — **Given** un user a `N > 3` projets et en nomme un ambigu, **When** le LLM ne peut trancher, **Then** il propose widget QCU listant les projets candidats (réutilise Story 16.3 interactive widgets).

---

### Story 16.3 : Extension widgets interactifs aux nouveaux modules (FR47 étendu)

**As a** PME User,
**I want** que le copilot utilise les widgets interactifs (QCU, QCM, QCU+justification livrés spec 018) pour la collecte de données structurées dans les nouveaux modules (maturité niveau, pack ESG, voie d'accès Fund, niveau confirmation snapshot),
**So that** les nouveaux parcours bénéficient de la même ergonomie que les parcours existants.

**Metadata (CQ-8)** — `fr_covered`: [FR47] · `nfr_covered`: [NFR54, NFR56] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 018 widgets livré]

**Acceptance Criteria**

**AC1** — **Given** un user demande « quelle est ma maturité administrative ? », **When** le LLM interroge, **Then** il propose un widget QCU avec les 4 niveaux (spec 018 pattern) + ARIA roles conformes (NFR56).

**AC2** — **Given** les widgets sont déjà mono-pending (spec 018 invariant), **When** un nouveau widget est émis, **Then** l'ancien `pending` est marqué `expired` automatiquement (pas de régression).

**AC3** — **Given** l'user répond via widget, **When** valeur captée, **Then** le tool adapté est invoqué avec la valeur structurée (`declare_maturity_level`, `select_pack`, etc.).

---

### Story 16.4 : Extension guided tours aux nouveaux parcours Epic 11–15

**As a** PME User nouvel arrivant,
**I want** que le copilot propose des guided tours (infrastructure livrée spec 019) pour les nouveaux parcours (création Company, FormalizationPlan, évaluation ESG 3-couches, cube 4D matching, génération livrable),
**So that** je découvre l'app fluidement sans lire une doc.

**Metadata (CQ-8)** — `fr_covered`: [FR48] · `nfr_covered`: [NFR55] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1, spec 019 guided tours livrée, Epic 11–15 UI livrées]

**Acceptance Criteria**

**AC1** — **Given** le registre de parcours guidés spec 019, **When** étendu, **Then** il inclut au minimum 5 nouveaux parcours : `company_creation`, `formalization_plan`, `esg_facts_entry`, `fund_matching`, `application_generation`.

**AC2** — **Given** chaque nouvelle UI Epic 11–15, **When** les composants clés sont implémentés, **Then** ils portent les attributs `data-guide-target="<id>"` conformes au pattern spec 019.

**AC3** — **Given** un user demande ou le LLM détecte un besoin (nouveau user, action inédite), **When** guided tour `company_creation` est déclenché, **Then** il navigue les étapes avec retract du widget (spec 019 livré) + decompteur multi-pages.

---

### Story 16.5 : Fallback gracieux manual input quand LLM échoue

**As a** PME User,
**I want** que lorsque le LLM échoue répétitivement (timeout persistant, guards bloquants, erreur parsing), le copilot bascule gracieusement vers le formulaire manuel correspondant,
**So that** je ne sois jamais bloqué dans une impasse conversationnelle (FR49).

**Metadata (CQ-8)** — `fr_covered`: [FR49] · `nfr_covered`: [NFR42, NFR75] · `phase`: 1 · `cluster`: Copilot · `estimate`: M · `depends_on`: [Story 16.1]

**Acceptance Criteria**

**AC1** — **Given** un tool échoue 3 fois consécutives (NFR75 retry budget épuisé), **When** le circuit breaker s'active, **Then** le chat affiche message « Je rencontre un souci temporaire sur <action>. Voici le lien vers le formulaire » avec deep-link via `?prefill_key=<uuid>` (pas de JSON en query string — éviter limite 8 Kio).

**AC2** — **Given** table `prefill_drafts(id UUID PK, payload JSONB, user_id UUID FK, expires_at TIMESTAMP, created_at)` (migration consolidée dans Story 10.1), **When** un tool échoue + fallback, **Then** le backend crée un enregistrement avec TTL 1 h **And** retourne l'UUID au chat.

**AC3** — **Given** RLS sur `prefill_drafts` (pattern Story 10.5 étendu), **When** un user charge `/projects/new?prefill_key=<uuid>`, **Then** l'endpoint `GET /api/prefill-drafts/{uuid}` retourne `200 payload` si user propriétaire + non expiré, **404** sinon (RLS masque cross-user).

**AC4** — **Given** la page du formulaire charge le prefill, **When** les champs sont remplis, **Then** l'user voit immédiatement ses données captées + peut corriger avant soumission (conservation du travail).

**AC5** — **Given** le nettoyage des drafts expirés, **When** le worker `domain_events` (Story 10.10) tourne sa passe batch 30 s, **Then** il consomme un handler `prefill_drafts_cleanup` qui supprime les lignes `WHERE expires_at < now()` **And** aucun 2ᵉ worker cron séparé n'est nécessaire.

**AC6** — **Given** l'user complète le formulaire manuel, **When** il revient ensuite au chat, **Then** la conversation continue comme si le tool avait réussi (pas de rupture contexte).

**AC7** — **Given** les tests, **When** `pytest backend/tests/test_graph/test_chat_fallback.py` + `test_core/test_prefill_drafts.py` exécutés, **Then** scénarios (retry échec → fallback UUID, prefill RLS isolé, 404 cross-user, nettoyage TTL expiré, reprise chat) tous verts.

---

### Story 16.6 : Reprise conversation interrompue depuis checkpoint LangGraph MemorySaver

**As a** PME User,
**I want** reprendre une conversation là où je l'ai laissée après fermeture onglet / déconnexion / appareil différent,
**So that** mon travail ESG (facts collectés, verdicts générés, FormalizationPlan progression) ne soit jamais perdu (FR50).

**Metadata (CQ-8)** — `fr_covered`: [FR50] · `nfr_covered`: [NFR30, NFR49] · `phase`: 1 · `cluster`: Copilot · `estimate`: S · `depends_on`: [Story 16.1, LangGraph checkpointer persisté BDD livré]

**Acceptance Criteria**

**AC1** — **Given** un user ferme son onglet pendant une conversation active, **When** il rouvre l'app sur un autre appareil, **Then** la conversation reprend depuis le dernier checkpoint persisté (MemorySaver PostgreSQL) **And** `active_project_id` + `active_module` sont restaurés.

**AC2** — **Given** une conversation > 30 min sans activité, **When** l'user revient, **Then** un récapitulatif automatique des N derniers échanges est injecté dans le contexte (spec 003 pattern `_summarize_previous_conversation`).

**AC3** — **Given** un user supprime explicitement une conversation, **When** confirmé, **Then** l'historique est purgé (NFR21 soft delete + purge différée 30 j).

---

## Epic 17 — Stories détaillées (Dashboard & Monitoring)

> **Contexte brownfield** : module 011 (dashboard scores + plan d'action) **déjà livré**. Epic 17 étend avec nouveaux blocs (projets, maturité, ESG 3-couches, cube 4D matching, livrables), ajoute le multi-projets (Journey 2 Moussa) et le dashboard admin de monitoring.

### Story 17.1 : Dashboard PME étendu avec nouveaux blocs (projets, maturité, ESG, matching, livrables)

**As a** PME User (owner),
**I want** voir sur mon dashboard un agrégat étendu (scores ESG/carbone/crédit/financement/plan d'action **+ projets actifs, niveau maturité, matches cube 4D, livrables en cours**),
**So that** j'aie une vue d'ensemble actualisée de ma situation sans naviguer entre 8 pages (FR51).

**Metadata (CQ-8)** — `fr_covered`: [FR51] · `nfr_covered`: [NFR6, NFR7] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: L · `depends_on`: [Epic 11–15 livrés, module 011 existant]

**Acceptance Criteria**

**AC1** — **Given** user arrive sur `/dashboard`, **When** la page charge, **Then** TTI ≤ 1,5 s p95 sur 4G (NFR6) avec les blocs existants + nouveaux blocs `ProjectsWidget`, `MaturityWidget`, `MatchingWidget`, `DeliverablesWidget`.

**AC2** — **Given** un user sans Project, **When** dashboard affiché, **Then** les nouveaux blocs affichent un empty state informatif + CTA vers parcours de création.

**AC3** — **Given** un user avec plusieurs clusters actifs (A/A'/B/14/15), **When** dashboard affiché, **Then** chaque bloc affiche une métrique synthétique + un lien drill-down (vers `/projects`, `/maturity`, `/esg`, etc.) en dark mode (NFR62).

**AC4** — **Given** le bloc `MatchingWidget`, **When** rendu, **Then** il affiche top 3 fonds matchés avec `fit_score` + voie d'accès + CTA « voir toutes les recommandations ».

---

### Story 17.2 : Drill-down score global ESG → verdicts par référentiel

**As a** PME User,
**I want** cliquer sur mon score ESG global et voir un drill-down par référentiel actif avec les verdicts détaillés,
**So that** je comprenne d'où vient ma note et quelles sont mes marges de progression (FR52).

**Metadata (CQ-8)** — `fr_covered`: [FR52] · `nfr_covered`: [NFR1, NFR6] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: M · `depends_on`: [13.4b, 13.5, 13.10]

**Acceptance Criteria**

**AC1** — **Given** user clique score global ESG, **When** drill-down ouvert, **Then** tableau affiche `referential × score × top 3 PASS × top 3 FAIL × REPORTED count × N/A count` en < 1 s p95.

**AC2** — **Given** user clique un verdict, **When** drill-down niveau 2, **Then** panneau traçabilité Story 13.5 s'ouvre (facts utilisés, rule appliquée, version).

**AC3** — **Given** UI, **When** dark mode actif, **Then** codes couleurs PASS vert / FAIL rouge / REPORTED orange / N/A gris adaptés contrastes WCAG AA (NFR57).

---

### Story 17.3 : Dashboard multi-projets (Journey 2 Moussa COOPRACA)

**As a** PME User (owner ou membre) portant plusieurs Projects,
**I want** un dashboard multi-projets agrégeant les scores et statuts de chacun,
**So that** je pilote mon portefeuille de projets sans ouvrir chacun individuellement (FR53 Journey 2 Moussa).

**Metadata (CQ-8)** — `fr_covered`: [FR53] · `nfr_covered`: [NFR6, NFR50] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: M · `depends_on`: [17.1, Epic 11 Project livrés]

**Acceptance Criteria**

**AC1** — **Given** user avec ≥ 2 Projects, **When** dashboard affiché, **Then** un onglet « Tous les projets » liste chaque projet avec `state`, score ESG si calculé, FundApplications actives, prochaines deadlines.

**AC2** — **Given** un consortium (ProjectMembership multi-Company), **When** un membre non-owner visite, **Then** il voit les projets auxquels il est rattaché (RLS enforcement Story 10.5) + pas les autres.

**AC3** — **Given** N Projects avec N grand (≥ 50), **When** dashboard affiché, **Then** pagination + filtres `state`, `cluster_actif`, `secteur` + tri par `last_activity_at` **And** p95 chargement ≤ 2 s.

---

### Story 17.4 : Reminders in-app (deadline bailleur, renouvellement, expiration facts, MàJ référentiel, étape formalisation)

**As a** PME User,
**I want** recevoir des reminders in-app pour tous les événements à échéance (deadline bailleur, renouvellement certification, expiration facts versionnés, MàJ référentiel via `ReferentialMigration`, étape `FormalizationPlan` à exécuter),
**So that** rien ne passe en retard par oubli (FR54).

**Metadata (CQ-8)** — `fr_covered`: [FR54] · `nfr_covered`: [NFR40] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: M · `depends_on`: [10.10 `domain_events`, Epic 12 FormalizationPlan, Epic 13 facts versioning + ReferentialMigration, Epic 14 FundApplication]

**Acceptance Criteria**

**AC1** — **Given** les 5 types de reminders, **When** déclenchés par des handlers de `domain_events`, **Then** chaque reminder est persisté `Reminder(user_id, type, due_at, metadata, status)` + notification in-app visible sur `/reminders`.

**AC2** — **Given** user, **When** un reminder est à due, **Then** il apparaît dans le header avec badge de compte + toast discret à la première visite (**in-app only MVP — pas de web push**).

**AC3** — **Given** un reminder **critique** (deadline J-7 bailleur, deadline J-1, refus dossier, publication référentiel impactant l'user), **When** constaté, **Then** **email Mailgun** est envoyé à l'user (NFR45, absorbe pattern Story 17.6 alerting) **And** trace d'envoi dans `notification_log`.

**AC4** — **Given** un reminder **non-critique** (deadline J-30, renouvellement certification lointain, MàJ référentiel non-impactant, étape formalisation optionnelle), **When** constaté, **Then** **in-app only** (pas d'email) pour éviter la fatigue notifications.

**AC5** — **Given** un user complète l'action associée (ex. step plan `done`), **When** constaté, **Then** le reminder est auto-marqué `done` **And** retiré de la liste active.

**AC6** — **Given** les web push notifications (PWA), **When** évoquées, **Then** **différées Phase 4 PWA** (cohérent roadmap) si métrique engagement justifie (pas scope MVP).

**AC7** — **Given** les tests, **When** exécutés, **Then** 5 scénarios (1 par type de reminder) + logique critique vs non-critique + rate-limiting email (≤ 3 par user par jour) verts.

---

### Story 17.5 : Dashboard monitoring admin (p95 tools, guards, couverture catalogue, budget LLM)

**As a** Admin Mefali,
**I want** un dashboard de monitoring système agrégeant les métriques clés (p95 latence par tool, taux erreur, taux retry, échecs guards LLM, couverture catalogue source_url HTTP 200, budget LLM consommé),
**So that** je détecte les anomalies avant les users (FR55).

**Metadata (CQ-8)** — `fr_covered`: [FR55] · `nfr_covered`: [NFR37, NFR39, NFR41, NFR74] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: L · `depends_on`: [Story 9.7 instrumentation, 10.10 `domain_events`, 10.11 source_url CI]

**Acceptance Criteria**

**AC1** — **Given** UI admin `/admin/monitoring/`, **When** chargée, **Then** 6 widgets : (1) p95 latence par tool (tableau trié), (2) taux erreur par module, (3) taux retry, (4) échecs guards LLM dernières 24 h, (5) couverture catalogue `source_url` HTTP 200 %, (6) budget LLM mensuel consommé + projection fin mois.

**AC2** — **Given** widget budget LLM, **When** la projection fin de mois est calculée, **Then** **extrapolation linéaire simple** : `projected_month_end = current_consumption / days_elapsed × days_total_in_month` **And** warning jaune si `projected_month_end > 80 % budget mensuel`, **And** critical rouge si `current_consumption ≥ 100 % budget mensuel` avec throttling LLM activé (rate limit renforcé) + alert ops (Story 17.6).

**AC3** — **Given** Phase Growth future, **When** le modèle évolue, **Then** un historique glissant 3 derniers mois est ajouté pour détection de patterns (saisonnalité, spikes) — **non livré MVP**, documenté comme évolution.

**AC4** — **Given** un admin filtre par période (last 1h / 24h / 7j / 30j), **When** sélectionné, **Then** les agrégats se re-calculent depuis `tool_call_logs` en ≤ 2 s p95.

**AC5** — **Given** un seuil atteint (ex. guards LLM > 80 % cible NFR74), **When** le widget s'affiche, **Then** badge rouge + lien drill-down vers les events récents.

---

### Story 17.6 : Alerting anomalies (échec guards, retry anormal, source_url, budget, circuit breaker)

**As a** Admin Mefali + Équipe Mefali (SRE),
**I want** recevoir des alertes proactives (Sentry + PagerDuty + email) sur les anomalies système (échec guards LLM > seuil, taux retry > 5 %, `source_url` HTTP ≠ 200, dépassement budget LLM mensuel, circuit breaker LLM activé),
**So that** je n'aie pas à regarder le dashboard en permanence pour détecter un incident en cours (FR56 + NFR40).

**Metadata (CQ-8)** — `fr_covered`: [FR56] · `nfr_covered`: [NFR40, NFR41, NFR75] · `phase`: 1 · `cluster`: D Dashboard · `estimate`: M · `depends_on`: [17.5, 10.11]

**Acceptance Criteria**

**AC1** — **Given** les 5 types d'alertes, **When** déclenchés, **Then** intégration Sentry (tous) + PagerDuty (critiques seuls : circuit breaker LLM, source_url catastrophique) + email admin (daily digest + alertes critiques temps réel).

**AC2** — **Given** un taux de retry anormal, **When** > 5 % sur 15 min, **Then** alerte médium émise + lien vers Story 17.5 widget correspondant.

**AC3** — **Given** `source_url` HTTP ≠ 200 détecté par CI nightly (Story 10.11), **When** 3 runs consécutifs échouent, **Then** alerte admin + badge déjà posé sur l'entité (Story 10.11 AC4) + ticket Sentry.

**AC4** — **Given** les tests, **When** exécutés, **Then** 5 scénarios (1 par type) déclenchent bien les bonnes cibles Sentry/PD/email + rate-limiting (pas de spam > 1 alerte identique / heure).

---

---

## Epic 18 — Stories détaillées (Compliance & Security renforcés)

> **Pré-requis** : Epic 10 complet (RLS + KMS + audit trail catalogue infra). FR59/FR62/FR63/FR64 déjà couverts dans Epic 10 — Epic 18 = enforcement applicatif sur les flows PME user.

### Story 18.1 : Pipeline anonymisation PII systématique avant LLM + audit annuel

**As a** System + Équipe Mefali (compliance),
**I want** un pipeline d'anonymisation PII appliqué à **100 % des prompts** envoyés au LLM (noms, adresses, RCCM/NINEA/IFU, téléphones) avec tests automatisés CI + audit annuel manuel,
**So that** aucune donnée personnelle identifiable ne fuite vers un provider tiers (NFR11 + compliance SN 2008-12 / CI 2013-450 / RGPD).

**Metadata (CQ-8)** — `fr_covered`: [FR58] · `nfr_covered`: [NFR11, NFR19, NFR25] · `phase`: 1 · `cluster`: Compliance · `estimate`: L · `depends_on`: [Story 10.8 framework prompts CCC-9]

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/pii_anonymizer.py`, **When** auditée, **Then** elle expose `anonymize(text, context) -> AnonymizedText` détectant 5 classes de PII (nom personne, adresse, numéro RCCM/NINEA/IFU, téléphone, email) avec mapping déterministe (même PII → même token).

**AC2** — **Given** le framework prompts CCC-9 (Story 10.8), **When** il construit un prompt destiné LLM, **Then** il passe **obligatoirement** par `anonymize()` avant envoi **And** le hook est enforcé (pas de bypass direct vers provider).

**AC3** — **Given** les tests CI, **When** `pytest backend/tests/test_security/test_pii_anonymization.py` exécuté, **Then** ≥ 50 cas tests (noms FR typiques AO, numéros RCCM SN/CI/ML/BF/BJ/TG/NE, téléphones +221 +225 +223, adresses, emails) couverts **And** coverage ≥ 95 % (code critique juridique — au-dessus NFR60 standard).

**AC4** — **Given** un faux positif (mot commun détecté comme PII) ou faux négatif (PII manquée), **When** découvert, **Then** un cas régression est ajouté aux tests **And** l'anonymizer évolue sans régression sur les cas existants.

**AC5** — **Given** un audit annuel manuel (NFR11), **When** planifié, **Then** un checklist documentée + sample de prompts réels anonymisés (anonymisés deux fois pour vérif) + rapport signé + archivé 5 ans.

---

### Story 18.2 : Chiffrement at rest KMS sur tables/buckets sensibles

**As a** System + Équipe Mefali (SRE/security),
**I want** que les documents uploadés (bilans, RCCM, IFU, preuves), les snapshots `FundApplication` et le journal d'audit soient chiffrés at rest via KMS-managed keys AWS EU-West-3,
**So that** une compromission du disque brut ne donne pas accès aux données sensibles (FR60 + NFR10).

**Metadata (CQ-8)** — `fr_covered`: [FR60] · `nfr_covered`: [NFR10, NFR25] · `phase`: 1 · `cluster`: Compliance · `estimate`: M · `depends_on`: [Story 10.6 StorageProvider, Story 10.7 envs]

**Acceptance Criteria**

**AC1** — **Given** S3 bucket `mefali-prod-sensitive` (Story 10.6), **When** configuré, **Then** chiffrement at rest KMS activé par défaut (SSE-KMS) + clés rotées trimestriellement.

**AC2** — **Given** RDS PostgreSQL `mefali-prod` (Story 10.7), **When** configurée, **Then** storage chiffré via KMS + snapshots chiffrés + clés distinctes par environnement (DEV/STAGING/PROD).

**AC3** — **Given** l'accès aux clés KMS, **When** audité, **Then** IAM role limité (admin_super seul) + audit log CloudTrail + alerting sur tentative d'accès non autorisée.

**AC4** — **Given** tabletop exercise trimestriel (NFR36), **When** un disaster « clé KMS compromise » est simulé, **Then** runbook de rotation d'urgence existe + exécutable en < 4 h (RTO NFR34).

---

### Story 18.3 : MFA obligatoire `admin_mefali`/`admin_super` + step-up actions à risque (tous rôles)

**As a** System + Admin Mefali,
**I want** MFA permanent pour les rôles admin et step-up MFA pour les actions à risque élevé de tous les rôles (soumission > 50k USD, signature électronique, modification bancaire, changement credentials, suppression docs/projets, export sensibles),
**So that** les actions critiques nécessitent une re-authentification forte même avec session active (FR61 + NFR14).

**Metadata (CQ-8)** — `fr_covered`: [FR61] · `nfr_covered`: [NFR13, NFR14] · `phase`: 1 · `cluster`: Compliance · `estimate`: L · `depends_on`: [Epic 10]

**Acceptance Criteria**

**AC1** — **Given** login `admin_mefali` ou `admin_super`, **When** authenticated, **Then** MFA (TOTP via app authenticator) obligatoire avec fail-fast si non configuré + recovery codes générés à l'enrollment.

**AC2** — **Given** action à risque (enum : `submit_over_50k`, `sign_attestation`, `update_banking`, `change_credentials`, `delete_document`, `delete_project`, `export_sensitive_data`), **When** user (tous rôles) l'invoque, **Then** step-up MFA requis avec TTL 15 min **And** la session MFA step-up est tracée dans audit trail.

**AC3** — **Given** un `owner` refuse l'opt-in MFA, **When** il accède, **Then** accès autorisé MAIS avec warning permanent dashboard + CTA « activer MFA pour protection accrue » (opt-in fortement recommandé NFR14).

**AC4** — **Given** les tests, **When** `pytest backend/tests/test_security/test_mfa.py` exécuté, **Then** scénarios (admin MFA obligatoire, step-up sur 7 actions, recovery code, session MFA TTL, opt-in owner) verts + coverage ≥ 85 %.

---

### Story 18.4 : Droit à l'effacement — soft delete + purge différée 30–90 j + snapshots préservés

**As a** PME User (owner),
**I want** exercer mon droit à l'effacement (compte + données associées) avec un délai de rétractation 30 j, une purge définitive après 30–90 j, tout en conservant les snapshots `FundApplication` soumis (indépendants du profil vivant),
**So that** je respecte mes obligations légales (SN 2008-12 / CI 2013-450 / RGPD art.17) sans casser les dossiers bailleurs déjà soumis (FR65 + NFR21 + NFR23).

**Metadata (CQ-8)** — `fr_covered`: [FR65] · `nfr_covered`: [NFR19, NFR20, NFR21, NFR23] · `phase`: 1 · `cluster`: Compliance · `estimate`: L · `depends_on`: [Epic 10, Story 15.4 snapshots immuables]

**Acceptance Criteria**

**AC1** — **Given** user demande l'effacement `POST /api/users/me/erasure`, **When** confirmé avec step-up MFA (Story 18.3), **Then** soft delete posé `deleted_at=now, purge_at=now + 30d` **And** notification email confirmation + délai de rétractation.

**AC2** — **Given** user rétracte pendant les 30 j, **When** `POST /api/users/me/undelete`, **Then** le soft delete est retiré + accès restauré + audit trail.

**AC3** — **Given** `purge_at < now()`, **When** le worker `domain_events` consomme le handler `user_purge_due`, **Then** purge définitive exécutée en cascade (User + Company + Project + Facts + Evidence + Reminders + Sessions) **sauf** `FundApplicationSnapshot` + `ApplicationAttestation` + `AdminCatalogueAuditTrail` (rétention 10 ans SGES NFR20).

**AC4** — **Given** snapshots préservés, **When** consultés a posteriori par audit bailleur, **Then** ils restent lisibles (`company_snapshot`, `project_snapshot` encapsulés dans le JSONB — pas de FK cassée).

**AC5** — **Given** les tests, **When** `pytest backend/tests/test_security/test_erasure.py` exécuté, **Then** scénarios (soft delete, rétractation, purge cascade, snapshot préservé, audit trail) verts + coverage ≥ 85 %.

---

### Story 18.5 : Export data portability JSON + CSV optionnel

**As a** PME User (owner),
**I want** exporter toutes mes données en format machine-readable (JSON structuré + CSV optionnel pour tabulaires),
**So that** je puisse les réutiliser ailleurs conformément à mon droit à la portabilité (FR66 + NFR26 + RGPD art.20).

**Metadata (CQ-8)** — `fr_covered`: [FR66] · `nfr_covered`: [NFR26] · `phase`: 1 · `cluster`: Compliance · `estimate`: M · `depends_on`: [Story 10.6 StorageProvider, Story 9.10 BackgroundTask]

**Acceptance Criteria**

**AC1** — **Given** user demande `POST /api/users/me/export?format=json|csv|both`, **When** validé avec step-up MFA, **Then** un `BackgroundTask` assemble toutes les données (Company, Projects, Facts, Evidence métadata, Verdicts, FundApplications, Reminders) en JSON structuré.

**AC2** — **Given** format=both, **When** assemblé, **Then** JSON principal + CSV tabulaires (un par table) + un README markdown expliquant le schéma + zip compressé.

**AC3** — **Given** export terminé, **When** stocké via `StorageProvider`, **Then** URL signée TTL 24 h envoyée par email **And** l'export est purgé automatiquement après 7 j (pas d'accumulation stockage).

**AC4** — **Given** les tests, **When** exécutés, **Then** scénarios (export JSON complet, CSV tabulaires, README présent, TTL URL, purge 7 j) verts **And** coverage ≥ **85 %** (code critique — export incomplet / PII oublié / corruption format = non-conformité légale RGPD art.20 + loi SN 2008-12 + CI 2013-450).

---

### Story 18.6 : Password reset + magic link passwordless onboarding + force reset admin

**As a** PME User + Admin Mefali,
**I want** un parcours password reset via email verification, un onboarding magic link passwordless (nouveaux users MVP), et la capacité admin de forcer un reset d'urgence avec audit log,
**So that** l'accès soit récupérable sans password perdu (FR68).

**Metadata (CQ-8)** — `fr_covered`: [FR68] · `nfr_covered`: [NFR13, NFR45] · `phase`: 1 · `cluster`: Compliance · `estimate`: M · `depends_on`: [Epic 10 NFR45 Mailgun]

**Acceptance Criteria**

**AC1** — **Given** user `POST /api/auth/password-reset` avec email, **When** validé, **Then** email Mailgun envoyé avec lien signé TTL 1 h **And** rate-limiting (3 tentatives / heure / email).

**AC2** — **Given** onboarding MVP, **When** nouvel user invité (Story 11.2), **Then** magic link passwordless activable (pas de mot de passe à la 1ère connexion) **And** setup password proposé en 2ᵉ étape non bloquante.

**AC3** — **Given** admin_mefali `POST /admin/users/{id}/force-reset` avec raison obligatoire, **When** exécuté avec step-up MFA, **Then** password user invalidé + email reset envoyé **And** `admin_action_log` rempli avec raison, timestamp, IP admin.

**AC4** — **Given** les tests, **When** exécutés, **Then** scénarios (reset email, magic link onboarding, force reset admin, rate limiting) verts + coverage ≥ 85 %.

---

### Story 18.7 : Audit trail accès données sensibles (rétention 5 ans)

**As a** System + Admin Mefali,
**I want** logger tous les accès aux données sensibles (bilans, RCCM, IFU, snapshots, PII, documents chiffrés) avec rétention 5 ans,
**So that** une enquête sécurité ou un audit bailleur puisse retracer qui a consulté quoi et quand (FR69 + NFR28).

**Metadata (CQ-8)** — `fr_covered`: [FR69] · `nfr_covered`: [NFR28, NFR20] · `phase`: 1 · `cluster`: Compliance · `estimate`: M · `depends_on`: [Epic 10]

**Acceptance Criteria**

**AC1** — **Given** table `sensitive_access_log(actor_id, resource_type, resource_id, action, ts, request_id, ip, user_agent)`, **When** créée, **Then** append-only enforcement PG trigger (Story 10.12 pattern).

**AC2** — **Given** un GET sur `/api/documents/{id}` ou `/api/applications/{id}/snapshot`, **When** exécuté, **Then** une ligne log insérée automatiquement via middleware FastAPI (pas d'oubli au cas par cas).

**AC3** — **Given** rétention 5 ans (NFR20), **When** le job de purge tourne, **Then** aucune ligne supprimée avant 5 ans **And** archivage froid S3 Glacier envisageable Phase Growth (documenté).

**AC4** — **Given** pen test (Story 20.3), **When** tentative altération ou suppression du log détectée, **Then** trigger PG rejette + incident sécurité loggé.

---

## Epic 19 — Stories détaillées (Socle RAG refactor + intégration cross-module)

### Story 19.1 : Socle RAG refactor — abstraction réutilisable cross-module

**As a** Équipe Mefali (backend/AI),
**I want** refactoriser l'usage du RAG pgvector (livré spec 004) en une abstraction réutilisable (`RagService` avec méthodes typées `search(query, scope, top_k)`, `cite(chunks) -> Citations`, `chunk_document(doc) -> Chunks`) consommant l'`EmbeddingProvider` Voyage (Story 10.13),
**So that** les 5+ modules consommateurs (applications, carbon, credit, action_plan, puis 8/8 Phase 4) n'implémentent pas chacun leur propre pattern RAG (anti-duplication).

**Metadata (CQ-8)** — `fr_covered`: [FR70 partiel, FR71 partiel] · `nfr_covered`: [NFR43, NFR52, NFR60] · `phase`: 0 · `cluster`: RAG transversal · `estimate`: L · `depends_on`: [Story 10.13 Voyage, spec 004 pgvector livré]

**Acceptance Criteria**

**AC1** — **Given** `backend/app/core/rag/`, **When** auditée, **Then** elle contient `service.py` (`RagService` — interface stable), `chunker.py` (stratégies chunking par type de document), `citation.py` (formateur de citations avec nom fichier + page), `cache.py` (cache LRU optionnel).

**AC2** — **Given** l'abstraction, **When** consommée par Story 9.13 (RAG applications) ou par Story 19.2 (extension cross-module), **Then** aucune duplication du pattern pgvector dans les modules consommateurs (tous passent par `RagService`).

**AC3** — **Given** `RagService.search(query, scope={project_id, document_types?}, top_k=5)`, **When** invoquée, **Then** elle appelle `EmbeddingProvider.embed(query)` puis exécute la query pgvector avec les bons filtres RLS + retourne les chunks ordonnés par similarity score.

**AC4** — **Given** `RagService.cite(chunks)`, **When** invoquée, **Then** elle retourne un format structuré `[{fichier: str, page: int, chunk_excerpt: str, confidence: float}]` utilisable dans les prompts ou rendu UI.

**AC5** — **Given** le refactor, **When** les modules existants (documents spec 004, chat) sont migrés vers `RagService`, **Then** aucune régression fonctionnelle **And** tous les tests existants restent verts.

**AC6** — **Given** les tests, **When** `pytest backend/tests/test_core/test_rag_service.py` exécuté, **Then** scénarios (search avec scope, cite format, chunker par type doc, cache hit/miss, RLS isolation) verts + coverage ≥ 85 %.

---

### Story 19.2 : Intégration `RagService` aux modules cross-functional (carbon + credit + action_plan)

**As a** PME User,
**I want** que les modules carbon (spec 007), credit (spec 010), action_plan (spec 011) bénéficient également du RAG documentaire pour ancrer leurs analyses dans mes documents uploadés (pas seulement applications FR-005 traité par Story 9.13),
**So that** le signal PRD 6 « RAG transversal ≥ 5 modules MVP » (FR70 + SC-T9) soit tenu.

**Metadata (CQ-8)** — `fr_covered`: [FR70 complet, FR71 complet] · `nfr_covered`: [NFR60] · `phase`: 1 · `cluster`: RAG transversal · `estimate`: L · `depends_on`: [Story 19.1, Story 9.13 RAG applications (consommateur de référence)]

**Acceptance Criteria**

**Liste explicite des 5 modules consommateurs MVP** (arbitrage Lot 7) :
1. **`esg_service`** (spec 005 existant) — reconnecté à `RagService` abstraction (retire l'usage direct de pgvector spec 004).
2. **`applications_service`** — consomme via Story 9.13 (FR-005 promesse tenue).
3. **`carbon_service`** (spec 007) — nouvelle intégration RAG.
4. **`credit_service`** (spec 010) — nouvelle intégration RAG.
5. **`action_plan_service`** (spec 011) — nouvelle intégration RAG.

**AC1** — **Given** `esg_service`, **When** un verdict multi-référentiel est calculé (Story 13.4b materialization), **Then** `RagService.search(query, scope={project_id, document_types: ['bilan', 'politique_sst']})` est invoqué pour **renforcer** la traçabilité des facts utilisés (Story 13.5) avec citations documentaires vers les preuves originales (FR71) **And** le code legacy spec 005 appelant pgvector directement est migré vers `RagService` (pas de duplication).

**AC2** — **Given** `applications_service` via Story 9.13, **When** `generate_section` est exécutée, **Then** elle consomme `RagService` de l'abstraction Story 19.1 (pas de 2ᵉ pattern RAG recréé).

**AC3** — **Given** `carbon_service` (spec 007), **When** un bilan carbone est analysé, **Then** `RagService` cherche dans les documents uploadés (factures énergie, rapports transport) des éléments confirmant les valeurs déclarées **And** les chunks pertinents sont cités dans le rapport de bilan (FR71).

**AC4** — **Given** `credit_service` (spec 010), **When** le score crédit est calculé, **Then** `RagService` cherche des preuves complémentaires (historique bancaire, relevés Mobile Money documentés) **And** les citations renforcent la justification du score.

**AC5** — **Given** `action_plan_service` (spec 011), **When** le plan est généré par Claude, **Then** `RagService` fournit des extraits documentaires ciblant les faiblesses identifiées ESG (ex. « politique SST manquante » → cherche si un document interne existe déjà).

**AC6** — **Given** les 5 modules listés, **When** SC-T9 est vérifié, **Then** **exactement 5 modules consomment `RagService` MVP** (esg + applications + carbon + credit + action_plan) — signal PRD 6 tenu.

**AC7** — **Given** Phase 4, **When** évoquée, **Then** extension 8/8 modules (ajouter `financing_service`, `profiling` remplaçant `update_company_profile`, `documents_service` spec 004 déjà socle) documentée mais **non livrée MVP**.

**AC8** — **Given** les tests d'intégration, **When** `pytest backend/tests/test_rag_cross_module/` exécuté avec un fichier de test par module (`test_esg_rag.py`, `test_applications_rag.py`, `test_carbon_rag.py`, `test_credit_rag.py`, `test_action_plan_rag.py`), **Then** **chaque module** a un test vérifiant (a) `RagService` est appelé, (b) les citations sont présentes dans le résultat, (c) fallback gracieux si aucun document uploadé (pattern spec 009), (d) RLS isolation cross-user **And** coverage ≥ 80 % par module.

---

## Epic 20 — Stories détaillées (Cleanup & Release Engineering)

### Story 20.1 : Cleanup feature flag `ENABLE_PROJECT_MODEL` (fin Phase 1)

**As a** Équipe Mefali (DX/SRE),
**I want** retirer définitivement le feature flag `ENABLE_PROJECT_MODEL` à la fin de la Phase 1 (après GA du modèle Company × Project pour tous les tenants),
**So that** la dette technique du flag temporaire soit soldée conformément NFR63 + RT-3 + CQ-10.

**Metadata (CQ-8)** — `fr_covered`: — · `nfr_covered`: [NFR63] · `phase`: 1 (fin) · `cluster`: Release · `estimate`: S · `depends_on`: [Epic 11–19 livrés + pilote validé]

**Acceptance Criteria**

**AC1** — **Given** le code source, **When** un `grep -r "ENABLE_PROJECT_MODEL\|is_project_model_enabled"` est exécuté, **Then** zéro occurrence post-story.

**AC2** — **Given** migration `027_cleanup_feature_flag_project_model.py`, **When** exécutée, **Then** colonnes/indexes/contraintes temporaires liés au flag sont retirés proprement (Story 10.1 AC5).

**AC3** — **Given** les variables d'env de tous les manifests (DEV/STAGING/PROD), **When** auditées, **Then** `ENABLE_PROJECT_MODEL` disparaît des 3 environnements.

**AC4** — **Given** les tests, **When** exécutés, **Then** aucune régression (baseline NFR59 maintenue) **And** les tests qui testaient le comportement off-flag sont soit supprimés (dead), soit reconvertis en tests de non-régression.

---

### Story 20.2 : Load testing k6 conforme NFR71 (avant pilote prod)

**As a** Équipe Mefali (SRE/QA),
**I want** exécuter les scénarios de charge NFR71 (100 users simultanés 30 min chat+cube 4D, 10 générations SGES simultanées, 500 appels/min read-only) via k6 ou Locust,
**So that** tous les NFR Performance (NFR1–NFR8) soient respectés sous charge avant ouverture du premier pilote PME réelle.

**Metadata (CQ-8)** — `fr_covered`: — · `nfr_covered`: [NFR1, NFR2, NFR3, NFR4, NFR5, NFR6, NFR7, NFR8, NFR50, NFR71] · `phase`: 1 (fin) · `cluster`: Release · `estimate`: L · `depends_on`: [Epic 11–19 livrés]

**Acceptance Criteria**

**AC1** — **Given** les 3 scénarios k6, **When** exécutés sur STAGING (Story 10.7 minimal t3.micro), **Then** les 8 NFR Performance sont respectés **And** le rapport est archivé + partagé.

**AC2** — **Given** un dépassement de p95, **When** détecté, **Then** ticket bloquant ouvert + résolution avant passage prod (CI gate).

**AC3** — **Given** Phase Growth, **When** les NFR cibles augmentent (5 000 users NFR50), **Then** les tests k6 sont relancés à chaque fin de Phase avant prod (NFR71 récurrence).

**AC4** — **Given** les EXPLAIN hot paths (Story 10.7 AC7), **When** exécutés en parallèle, **Then** aucun Seq Scan régressé.

---

### Story 20.3 : Pen test externe indépendant (avant pilote prod)

**As a** Équipe Mefali (security) + compliance,
**I want** commander un pen test externe indépendant (5 j, ~5–8 k€) couvrant OWASP Top 10 + cross-tenant RLS + SGES NO BYPASS + PII anonymization + audit trail immutability,
**So that** les findings CRITIQUES soient corrigés avant le premier pilote PME réelle (NFR18).

**Metadata (CQ-8)** — `fr_covered`: — · `nfr_covered`: [NFR9, NFR11, NFR12, NFR14, NFR15, NFR18, NFR28] · `phase`: 1 (fin) · `cluster`: Release · `estimate`: M · `depends_on`: [Epic 10–19 livrés]

**Acceptance Criteria**

**AC1** — **Given** le prestataire pen test sélectionné, **When** la mission démarre, **Then** scope documenté inclut : OWASP Top 10, RLS bypass (Story 10.5 AC2), SGES NO BYPASS (Story 15.5), PII leak vers LLM (Story 18.1), altération audit trail (Story 10.12 + 18.7).

**AC2** — **Given** le rapport final, **When** livré, **Then** findings catégorisés CRITICAL/HIGH/MEDIUM/LOW **And** CRITICAL + HIGH corrigés avant activation prod (merge PROD gate).

**AC3** — **Given** les corrections, **When** livrées, **Then** un re-test (ou re-validation ciblée) est exécuté pour confirmer remédiation.

**AC4** — **Given** rétention 5 ans (NFR18), **When** archivé, **Then** le rapport + re-test + plan de correction sont conservés auditables.

---

### Story 20.4 : Audit accessibilité WCAG AA externe (Phase 3 ou avant pilote si enjeu)

**As a** Équipe Mefali (accessibilité) + compliance,
**I want** commander un audit accessibilité externe indépendant (1–2 j, ~1–2 k€) couvrant WCAG 2.1 AA sur les pages user-facing (PME + Admin),
**So that** l'engagement NFR54–NFR58 soit vérifié par un tiers avant Phase 3 UX enrichi (ou avant pilote si enjeu spécifique).

**Metadata (CQ-8)** — `fr_covered`: — · `nfr_covered`: [NFR54, NFR55, NFR56, NFR57, NFR58] · `phase`: **1 (fin, avant pilote go-live)** · `cluster`: Release · `estimate`: M · `depends_on`: [Epic 11–17 livrés UI]

**Reclassement Phase 3 → Phase 1 fin** (arbitrage Lot 7) : WCAG AA est un engagement **pré-MVP go-live** (NFR58 + SC-B-PILOTE Aminata niveau 0 public vulnérable). Découvrir des dettes a11y majeures après traction utilisateurs réels = mauvais timing. L'audit WCAG externe doit précéder le premier pilote PME, au même titre que pen test (Story 20.3) et load test (Story 20.2).

**Acceptance Criteria**

**AC1** — **Given** l'auditeur externe, **When** mission démarre, **Then** scope inclut : navigation clavier complète (NFR55), ARIA roles conformes (NFR56), contrastes WCAG AA (NFR57), lecteurs d'écran NVDA/JAWS/VoiceOver (NFR58).

**AC2** — **Given** CI axe-core / pa11y (Story 10.7 pipeline), **When** complétée par l'audit humain, **Then** les angles non détectés automatiquement (compréhension cognitive, UX screen reader) sont validés.

**AC3** — **Given** le rapport, **When** livré, **Then** findings catégorisés (bloquant / majeur / mineur) **And** bloquants corrigés avant tag Phase 3 (ou avant pilote si trigger NFR18).

**AC4** — **Given** les corrections, **When** livrées, **Then** re-validation ciblée + tests CI étendus.

---

## DAG de dépendances Phase 0 → Phase 1

```
Story 9.7 (observabilité) ───BLOQUE───→ Epic 10 (Fondations)
                                           │
                                           ├─ stories 9.8–9.15 (dettes P1) — parallèle à Epics 11+ (cibles indépendantes)
                                           │
                                           ├─→ Epic 19 Phase 0 (socle RAG refactor)
                                           │
                                           └─→ Epic 11 (Cluster A)
                                                 └─→ Epic 12 (Cluster A')
                                                       └─→ Epic 13 (Cluster B)
                                                             ├─→ Epic 14 (Cube 4D)
                                                             └─→ Epic 15 (Moteur livrables)
                                                                   ├─→ Epic 16 (Copilot tools)
                                                                   ├─→ Epic 17 (Dashboard)
                                                                   ├─→ Epic 18 (Compliance enforcement)
                                                                   ├─→ Epic 19 Phase 1 (RAG ≥ 5 modules)
                                                                   └─→ Epic 20 (Cleanup & Release, fin Phase 1)
```
