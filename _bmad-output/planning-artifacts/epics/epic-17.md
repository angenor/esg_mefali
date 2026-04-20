---
title: "Dashboard & Monitoring"
epic_number: 17
status: planned
story_count: 6
stories: [17.1, 17.2, 17.3, 17.4, 17.5, 17.6]
dependencies:
  - epic: 10
    type: blocking
    reason: "Infra (catalogue, env, StorageProvider)"
  - epic: 11
    type: blocking
    reason: "Data source Company/Project"
  - epic: 12
    type: blocking
    reason: "Data source Maturity"
  - epic: 13
    type: blocking
    reason: "Data source ESG verdicts"
  - epic: 14
    type: blocking
    reason: "Data source Cube 4D matching"
  - epic: 15
    type: blocking
    reason: "Data source deliverables"
  - story: 9.7
    type: blocking
    reason: "Instrumentation source des métriques p95 tool / erreur / retry / guards LLM"
fr_covered: [FR51, FR52, FR53, FR54, FR55, FR56]
nfr_renforces: [NFR6, NFR39, NFR41, NFR74]
qo_rattachees: []
notes: "Dashboard PME étendu (extension module 011). Drill-down score ESG → verdicts. Multi-projets (Journey 2 Moussa). Reminders in-app. Dashboard admin monitoring + alerting."
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
