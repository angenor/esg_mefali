---
title: "Cleanup & Release Engineering"
epic_number: 20
status: planned
story_count: 4
stories: [20.1, 20.2, 20.3, 20.4]
dependencies:
  - epic: 11
    type: blocking
  - epic: 12
    type: blocking
  - epic: 13
    type: blocking
  - epic: 14
    type: blocking
  - epic: 15
    type: blocking
  - epic: 16
    type: blocking
  - epic: 17
    type: blocking
  - epic: 18
    type: blocking
  - epic: 19
    type: blocking
fr_covered: []
nfr_renforces: [NFR18, NFR58, NFR63, NFR71]
qo_rattachees: []
notes: "Pre-flight fin Phase 1. 20.1 cleanup feature flag ENABLE_PROJECT_MODEL (NFR63 + RT-3 + CQ-10). 20.2 load test k6 (NFR71). 20.3 pen test externe (NFR18). 20.4 audit WCAG AA externe (NFR58). QT-4 hors scope technique."
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
