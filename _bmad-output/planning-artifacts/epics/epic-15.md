---
title: "Cluster C — Moteur livrables bailleurs + SGES BETA NO BYPASS"
epic_number: 15
status: planned
story_count: 10
stories: [15.1a, 15.1b, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9]
dependencies:
  - epic: 10
    type: blocking
    reason: "Migration 023_create_deliverables_engine"
  - epic: 11
    type: blocking
    reason: "Company/Project (source de données)"
  - epic: 12
    type: blocking
    reason: "Maturity (calibration livrable)"
  - epic: 13
    type: blocking
    reason: "ESG facts/verdicts (source de données)"
  - story: 9.6
    type: already_delivered
    reason: "Guards LLM déjà livrés, consommés par 15.1b"
  - story: 9.10
    type: blocking
    reason: "BackgroundTask async pour validation perf NFR3/NFR4 (15.1b)"
blocks: [epic-16, epic-17, epic-18, epic-19, epic-20]
fr_covered: [FR36, FR37, FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR57]
nfr_renforces: [NFR3, NFR4, NFR20, NFR28]
qo_rattachees: [QO-C2]
notes: "PDF + DOCX bailleur-compliant (GCF, IFC AIMM, EUDR DDS, EIES Cat B, Proparco AIMM, SGES/ESMS BETA). Snapshot cryptographique (FR39). SGES BETA NO BYPASS — workflow bloquant avec verrou applicatif (15.5 — CQ-5). 15.1 splittée en 15.1a+15.1b."
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
