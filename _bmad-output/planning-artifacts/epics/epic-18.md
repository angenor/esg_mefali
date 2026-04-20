---
title: "Compliance & Security renforcés"
epic_number: 18
status: planned
story_count: 7
stories: [18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7]
dependencies:
  - epic: 10
    type: blocking
    reason: "Infra RLS + KMS + audit trail"
  - epic: 11
    type: blocking
    reason: "Enforcement sur data user (Company)"
  - epic: 12
    type: blocking
    reason: "Enforcement sur data user (Maturity)"
  - epic: 13
    type: blocking
    reason: "Enforcement sur data user (ESG)"
  - epic: 14
    type: blocking
    reason: "Enforcement sur data user (FundApplication)"
  - epic: 15
    type: blocking
    reason: "Enforcement sur data user (Deliverables snapshots)"
fr_covered: [FR58, FR60, FR61, FR65, FR66, FR68, FR69]
nfr_renforces: [NFR11, NFR13, NFR14, NFR19, NFR20, NFR21, NFR23, NFR26, NFR28]
qo_rattachees: []
notes: "Pipeline anonymisation PII avant LLM + audit annuel. KMS at rest. MFA admin_*/step-up actions à risque. Droit à l'effacement (soft delete + purge différée 30-90j). Export JSON/CSV. Password reset / magic link. Audit trail 5 ans."
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
