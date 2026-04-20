---
title: "Cluster A — PME porteuse de projets multi-canal"
epic_number: 11
status: planned
story_count: 8
stories: [11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8]
dependencies:
  - epic: 10
    type: blocking
    reason: "Migration 020_create_projects_schema + RLS + admin_catalogue pour rôles N2 FR7"
blocks: [epic-12, epic-13, epic-14, epic-15]
fr_covered: [FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR67]
nfr_renforces: [NFR49, NFR50, NFR60]
qo_rattachees: [QO-A1]
notes: "Data model racine du système. Story 11.8 originale (CompanyProjection) déplacée en 14.1 (voir changelog global). 11.8 finale = Auditor time-bounded scoping."
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
