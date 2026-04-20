---
title: "Cluster B — ESG multi-contextuel 3 couches"
epic_number: 13
status: planned
story_count: 14
stories: [13.1, 13.2, 13.3, 13.4a, 13.4b, 13.5, 13.6, 13.7, 13.8a, 13.8b, 13.8c, 13.9, 13.10, 13.11]
dependencies:
  - epic: 10
    type: blocking
    reason: "Migration 022_create_esg_3_layers + DSL Pydantic + micro-Outbox + catalogue admin"
blocks: [epic-14, epic-15]
fr_covered: [FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26]
nfr_renforces: [NFR2, NFR27, SC-T6]
qo_rattachees: [QO-B3, QO-B4]
notes: "3 couches (facts atomiques → rules DSL bornées → verdicts multi-référentiels). Pack pré-assemblé (IFC Bancable, EUDR-DDS, Artisan Minimal). Workflow admin N1/N2/N3. 13.4 splittée en 13.4a+13.4b ; 13.8 splittée en 13.8a+13.8b+13.8c (voir changelog global)."
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
