---
title: "Cube 4D — Matching projet-financement + lifecycle FundApplication"
epic_number: 14
status: planned
story_count: 10
stories: [14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10]
dependencies:
  - epic: 10
    type: blocking
    reason: "Admin catalogue N1 (Fund / Intermediary / FundIntermediaryLiaison)"
  - epic: 11
    type: blocking
    reason: "Company/Project/CompanyProjection (14.1 déplacée depuis 11.8)"
  - epic: 12
    type: blocking
    reason: "Maturité administrative pour dimension du cube"
  - epic: 13
    type: blocking
    reason: "ESG référentiels/verdicts pour dimension du cube"
blocks: [epic-15, epic-16, epic-17, epic-18, epic-19]
fr_covered: [FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR35]
nfr_renforces: [NFR1, NFR30]
qo_rattachees: [QO-A4, QO-A5]
notes: "Story 14.1 (CompanyProjection) déplacée depuis 11.8 (voir changelog global). Cube 4D = project × company × referentials × access route. Lifecycle FundApplication complet avec snapshot + remédiation."
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
