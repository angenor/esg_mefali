---
title: "Cluster A' — Maturité administrative graduée"
epic_number: 12
status: planned
story_count: 6
stories: [12.1, 12.2, 12.3, 12.4, 12.5, 12.6]
dependencies:
  - epic: 10
    type: blocking
    reason: "Migration 021_create_maturity_schema + admin_catalogue"
  - epic: 11
    type: blocking
    reason: "Company model racine"
blocks: [epic-14]
fr_covered: [FR11, FR12, FR13, FR14, FR15, FR16]
nfr_renforces: [NFR19, NFR66]
qo_rattachees: [QO-A'1, QO-A'3, QO-A'4, QO-A'5]
notes: "Auto-déclaration 4 niveaux (informel / RCCM+NIF / comptes+CNPS / OHADA audité), OCR justifs, FormalizationPlan XOF data-driven, auto-reclassification."
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
