---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
startedAt: '2026-04-19'
completedAt: '2026-04-19'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-18.md
  - _bmad-output/implementation-artifacts/spec-audits/index.md
  - CLAUDE.md
  - docs/architecture-backend.md
  - docs/architecture-frontend.md
  - docs/integration-architecture.md
  - docs/data-models-backend.md
  - _bmad-output/brainstorming/brainstorming-session-2026-04-18-1414.md
  - _bmad-output/planning-artifacts/product-brief-esg-mefali-copilot.md
  - _bmad-output/planning-artifacts/architecture-019-floating-copilot.md
legacyArtifacts:
  - _bmad-output/planning-artifacts/architecture-019-floating-copilot.md
  - _bmad-output/planning-artifacts/epics-019-floating-copilot.md
  - _bmad-output/planning-artifacts/prd-019-floating-copilot.md
workflowType: 'architecture'
project_name: 'esg_mefali'
user_name: 'Angenor'
date: '2026-04-19'
featureId: 'esg-mefali-extension-5-clusters'
scope: 'Extension PRD — projet dynamique + maturité graduée + ESG 3 couches + cube 4D voie d''accès + moteur livrables'
---

# Document de Décisions Architecturales — Extension ESG Mefali

_Ce document se construit collaborativement à travers une découverte étape par étape. Les sections sont ajoutées au fur et à mesure des décisions architecturales._

_**Scope** : PRD d'extension validé 2026-04-18 (statut `READY-WITH-DOWNSTREAM-DEPENDENCIES`, 0 CRITICAL). 5 clusters (A — projet dynamique, A' — maturité graduée, B — ESG 3 couches, Cube 4D — matching multidimensionnel, C — moteur livrables, D — interface admin N1/N2/N3). Architecture brownfield : étendre la stack existante, pas la remplacer (Annexe I du PRD)._

## Analyse du contexte projet

### Vue d'ensemble des exigences

**Exigences fonctionnelles — 71 FR répartis en 9 zones de capacité :**

| Zone | FRs | Implications architecturales |
|---|---|---|
| Company & Project Management | FR1–FR10 | Modèle `Company × Project` N:N, `ProjectMembership` avec rôles enum extensible (admin N2), `FundApplication` multiple par projet, `CompanyProjection` (vue curée par fonds), `BeneficiaryProfile` consortium, import CSV/Excel bulk (coopératives 100+ bénéficiaires) |
| Maturité administrative | FR11–FR16 | `AdminMaturityLevel` 4 niveaux (informel / RCCM+NIF / comptes+CNPS / OHADA audité), détection mixte auto-déclaration + OCR (module 004), `FormalizationPlan` chiffré pays-spécifique, `AdminMaturityRequirement(country × level)` paramétrable, auto-reclassement sur validation docs |
| ESG 3 couches | FR17–FR26 | `Fact` atomiques versionnés temporellement, `Criterion` composables avec métadonnées, `ReferentialVerdict` dérivé avec traçabilité, `Pack` pré-assemblés, `ReferentialMigration` avec plan de transition (RSPO_PC@2024_v4.0, IFC_PS@2028+) |
| Cube 4D Funding Matching | FR27–FR35 | Requête multi-dim projet × entreprise × référentiels × voie d'accès, critères intermédiaires superposés, cycle de vie `FundApplication` (draft → snapshot_frozen → signed → exported → submitted → in_review → accepted/rejected/withdrawn), admin real-time N1 |
| Document Generation & Deliverables | FR36–FR44 | Pyramide `DocumentTemplate` → `ReusableSection` → `AtomicBlock`, snapshot + hash cryptographique, signature électronique modal obligatoire, blocage export > 50 k USD section-par-section, SGES/ESMS BETA NO BYPASS (FR44) |
| Copilot conversationnel | FR45–FR50 | Chat SSE avec tools LangChain, `active_project` + `active_module` enforcement, widgets interactifs (QCU/QCM), tours guidés tool LangChain (spec 019), fallback gracieux, reprise conversation LangGraph MemorySaver |
| Dashboard / Monitoring / Notifications | FR51–FR56 | Dashboard existant étendu, drill-down par référentiel, vue multi-projets, rappels (deadlines bailleurs, renouvellement certifs, expiration faits, MàJ référentiel, étapes formalisation), monitoring admin, alerting anomalies |
| Audit / Compliance / Security | FR57–FR69 | `FundApplicationGenerationLog` (version LLM, prompts anonymisés, versions référentiels, hash snapshot, user), anonymisation PII, RLS 4 tables, chiffrement at rest KMS, MFA + step-up, NFR-SOURCE-TRACKING enforcement, audit trail catalogue 5 ans, right to erasure + portability, auditor token expirable |
| Search & Knowledge Retrieval | FR70–FR71 | RAG pgvector transversal ≥ 5 modules sur 8 en Phase 0, citations rule-level (verdicts) + paragraph-level (narratifs) |

**Exigences non-fonctionnelles — 76 NFR en 12 catégories :**

| Catégorie | NFRs | Contraintes architecturales structurantes |
|---|---|---|
| Performance | NFR1–NFR8 | Cube 4D ≤ 2 s p95 avec cache tiède · verdicts multi-ref ≤ 30 s p95 · PDF simple ≤ 30 s · livrable lourd (SGES, IFC AIMM) ≤ 3 min · chat first-token ≤ 2 s · TTI ≤ 1,5 s 4G · FCP ≤ 2 s 4G / ≤ 5 s 3G · cold start ≤ 30 s |
| Sécurité | NFR9–NFR18 | TLS 1.3 · chiffrement at rest KMS · anonymisation PII systématique · RLS 4 tables dès MVP · JWT+refresh · MFA obligatoire admin + step-up · rate limiting · pen test externe obligatoire pré-pilote |
| Privacy / Residency / Compliance | NFR19–NFR28 | Conformité SN 2008-12 + CI 2013-450 + CEDEAO + alignement RGPD · rétention différenciée (profil +2 ans, docs ordinaires +5 ans, SGES +10 ans, faits indéfini, logs 12 m, audit 5 ans) · soft delete + purge 30–90 j · **data residency AWS EU-West-3 Paris** avec plan contingence · NFR-SOURCE-TRACKING obligatoire · audit trail immuable |
| Availability / Reliability / DR | NFR29–NFR36 | SLA différencié 99,5 % endpoints critiques vs 99 % non-critiques · soumissions atomiques resumables (checkpointer) · backup BDD incrémentaux quotidiens + complets hebdo · rétention 30 j chaud + 1 an archive · test restauration trimestriel · **RTO 4 h / RPO 24 h** · runbooks + tabletop trimestriel |
| Observabilité | NFR37–NFR41 | Logs JSON structurés `request_id` end-to-end · 100 % tools instrumentés `with_retry + log_tool_call` · dashboard monitoring admin · alerting guards LLM / retry / DB / timeouts / source_url HTTP ≠ 200 · budget LLM surveillé |
| Intégration | NFR42–NFR48 | Anthropic via OpenRouter avec abstraction Provider (switch < 2 sem) + backup (OpenAI/Mistral) · OpenAI text-embedding-3-small · Tesseract fra+eng · **Mailgun MVP** avec DKIM/SPF/DMARC · WeasyPrint+Jinja2 · python-docx · stockage local MVP → S3 Growth |
| Scalabilité | NFR49–NFR53 | Stateless FastAPI (LangGraph checkpointer persistant) · indexes composites cube 4D + vues matérialisées · pgvector IVFFlat → HNSW > 100 k · Redis cache tiède Phase Growth · cible voir section « Échelle et complexité » ci-dessous |
| Accessibilité | NFR54–NFR58 | WCAG 2.1 AA minimum · navigation clavier · ARIA roles · contraste vérifié CI (axe-core/pa11y) · lecteurs d'écran parcours critiques · audit accessibilité Phase 3 |
| Maintenabilité | NFR59–NFR64 | **Zero failing tests on main** (opérationnel depuis story 9.3) · coverage 80 % standard + 85 % code critique · coverage gates CI · docstrings · conventions CLAUDE.md · **pas de feature flag permanent** (anti-pattern P1 #3) · pas de God service (P2 #25) |
| i18n | NFR65–NFR67 | Locale unique `fr` MVP · séparation stricte locale (langue) vs country (data paramétrée) · framework i18n Nuxt installé Phase 0 · extensibilité `en` Vision sans refactor |
| Budget / Ops | NFR68–NFR70 | Budget LLM alerting · budget infra ~800–2 000 €/mois MVP à confirmer post-Phase 0 · cyber insurance évaluée Phase Growth |
| DevOps / Release | NFR71–NFR76 | **Load testing obligatoire avant prod** · security dependency audit quotidien · environnements DEV/STAGING/PROD isolés (données prod jamais copiées sans anonymisation) · LLM quality observability · LLM retry strategy (3 retries exp backoff + circuit breaker 10) · code review obligatoire (1 reviewer + 2 dont 1 senior sur code critique) |

### Échelle et complexité

- **Niveau de complexité** : `high` à enterprise
- **Domaine technique principal** : `web_app` fintech/sustainability_esg brownfield — Nuxt 4 + FastAPI + LangGraph + PostgreSQL+pgvector + LLM Claude via OpenRouter
- **Modalités secondaires superposées** : SaaS B2B multi-tenant · Copilot IA-first · Consulting augmenté par IA

**Cible de charge (remplace l'ancienne progression 500 → 5 000 → 50 000+) :**

> **Cible 500 users actifs SIMULTANÉS MVP** (~10 000 actifs hebdomadaires, sessions 15–30 min). **À confirmer par tests de charge Phase 0** (NFR-NEW-1 — scénarios NFR71 : 100 users simultanés 30 min sur chat+cube 4D, 10 générations SGES simultanées, 500 appels/min endpoints read-only). **Re-plan architecture si volumétrie réelle sensiblement différente** (upscale si > 500 simultanés observés T+6 mois post-lancement ; downscale possible si < 100 — exemple : reporter Redis/HNSW si embeddings stagnent < 50 k).

**Indicateurs combinatoires justifiant le niveau « high to enterprise » :**
- 5 clusters produit imbriqués + 1 cube 4D central + admin typé par criticité
- Catalogue dynamique final (Phase 4) : ~500 critères × 15 référentiels × 8 pays UEMOA/CEDEAO × 5 maturités projet × 4 maturités entreprise × 2 voies d'accès
- **10–11 modules métier post-Phase 1** (vs 8 actuels — voir « Nouveaux modules et nœuds » ci-dessous)
- 6 rôles RBAC (owner/editor/viewer/auditor/admin_mefali/admin_super) + rôles projet extensibles via N2
- Multi-projets par Company, multi-FundApplications par Project, snapshot immuable par soumission
- Temps-réel catalogue (admin N1) + versioning strict référentiels (admin N3) + migration automatique avec date d'effet
- SLA différencié 99,5 % endpoints critiques vs 99 % non-critiques

**Nouveaux modules et nœuds LangGraph (ajustement 4) :**

- **3 nouveaux modules métier** : `projects`, `maturity`, `admin_catalogue`
- **2 nouveaux nœuds LangGraph confirmés** : `project_node`, `maturity_node`
- **1 nœud optionnel** : `admin_node` — à trancher Step 4 (simplicité UI pure vs cohérence Copilot IA-first). Si admin catalogue reste invocable depuis le chat (Mariam peut créer un fonds via une conversation), ajouter `admin_node` ; sinon laisser l'admin en UI-only.
- **Nœuds modifiés (pas nouveaux)** :
  - `esg_scoring_node` → architecture 3 couches (Fact → Criterion → ReferentialVerdict)
  - `applications_node` + `reports_node` → moteur livrables Cluster C (pyramide Template → Section → Block)
  - `financing_node` → cube 4D (matching multi-dim + voie d'accès avec critères intermédiaires superposés)
  - `carbon_node`, `credit_node`, `action_plan_node`, `document_node`, `chat_node` → conservation + éventuelle extension RAG transversal (CCC-8)

### Contraintes techniques et dépendances

**Stack brownfield classée (Annexe I PRD) :**

- **À CONSERVER** : LangGraph orchestration (9 nœuds), pgvector + text-embedding-3-small, streaming SSE, JWT stateless + refresh, LangGraph MemorySaver, Tesseract fra+eng, WeasyPrint+Jinja2+python-docx, conventions CLAUDE.md, **baseline 1103 tests verts + zero failing on main**
- **À COMPLÉTER** : filtre WHERE applicatif → +RLS 4 tables sensibles (`companies`, `fund_applications`, `facts`, `documents`) · rate limiting chat → +tools coûteux Phase Growth · 9 nœuds → +2–3 nouveaux · dashboard 4 cartes → +registre 11 blocs visuels Phase 3 · plan d'action → +FormalizationPlan + nouveaux types de rappels
- **À REMPLACER** : hard-coding catalogue (12 fonds, 14 intermédiaires, SECTOR_WEIGHTS, SECTOR_BENCHMARKS, facteurs émission) → tables BDD + admin N1/N2/N3 (Phase 0) · prompts directifs accumulés (specs 013/015/016/017) → framework injection unifié (Phase 0) · stockage local `/uploads/` → S3 EU-West-3 + backup 2 AZ (Phase Growth, prep Phase 0)

**10 dettes P1 audit restantes à résoudre en Phase 0 :**

1. P1 #1 — Migration 7 composables frontend → `apiFetch` (intercepteur 401)
2. P1 #3 — Dead code `profiling_node` + `chains/extraction.py` (~300 lignes)
3. P1 #5 — FR-019 notification chat PDF + `REPORT_TOOLS` LangChain
4. P1 #6 — Queue asynchrone Celery/RQ/BackgroundTask pour LLM + PDF lourds
5. P1 #9 — SECTOR_WEIGHTS 5/11 secteurs manquants (agroalim/commerce/artisanat dominants AO)
6. P1 #10 — Guards LLM universels sur contenus persistés (résumé exec, fiche prep, plan action)
7. P1 #11 — 5 tests backend manquants spec 008 Financing
8. P1 #12 — `batch_save_emission_entries` carbone (timeout LLM imminent bilans multi-véhicules)
9. P1 #13 — RAG documentaire applications FR-005 + extension 7 autres modules
10. P1 #14 — `with_retry` + `log_tool_call` aux 9 modules tools

**Contraintes data residency (NFR24) :** AWS EU-West-3 Paris retenu · plan de contingence documenté (migration Cape Town/provider local si évolution réglementaire SN/CI/CEDEAO imposant résidence locale, ou volumétrie Phase Growth, ou incident audit bailleur) · clauses-types CEDEAO explicites dans DPA et consentement · localisation par type de document documentée.

**Contraintes réglementaires compliance :**
- IFC PS1–PS8 (pivot bailleurs internationaux), Principes Équateur, SSI BAD/BOAD, GCF Safeguards, FEM Safeguards, Banque Mondiale ESF (ESS 1–10), DFI Harmonized Approach
- 8 conventions fondamentales OIT (travail forcé 29/105, travail enfants 138/182, non-discrimination 100/111, liberté syndicale 87/98) — critique EUDR/CS3D filières cacao/palme/coton
- **EUDR 30 juin 2027 PME** (Règlement UE 2023/1115 modifié par 2025/2650)
- **RSPO P&C 2024 v4.0 effective obligatoire 2026-05-31**
- **AFAC Continental Sustainable Finance Taxonomy (BAD) validée juillet 2025** à intégrer Phase 2
- Droit OHADA, identifiants fiscaux pays-variables (NINEA/IFU/NIF), régimes sociaux pays-variables (CNPS/IPRES+CSS/INPS)
- Protection données : **SN 2008-12, CI 2013-450, règlement CEDEAO**, alignement structurel RGPD
- Anti-corruption : FCPA + UK Bribery Act (extra-territoriaux), HABG CI, OFNAC SN, ITIE

### Préoccupations transversales identifiées

**CCC-1 — Guards LLM production-grade (Risque 10 non-négociable).** Schémas Pydantic stricts, longueur, cohérence numérique avec faits source, vocabulaire interdit ; retry strategy explicite (NFR75), circuit breaker, quality observability (NFR74) ; signature électronique utilisateur (FR40), audit trail `FundApplicationGenerationLog` (FR57), revue humaine obligatoire > 50 k USD (FR41), SGES BETA NO BYPASS (FR44).

**CCC-2 — Snapshot immuable + versioning référentiels.** Hash cryptographique sur 100 % des `FundApplication` (SC-T5), versions de référentiels gelées à la soumission, `ReferentialMigration` automatique avec date d'effet (ex. RSPO 2026-05-31), FundApplication existantes préservées, nouvelles évaluations basculent sur nouvelle version, notification utilisateurs concernés (FR34).

**CCC-3 — Observabilité end-to-end.** `request_id` UUID traversant frontend → FastAPI → LangGraph → tools → DB ; logs JSON structurés exclusivement en prod ; 100 % tools instrumentés `with_retry + log_tool_call` (clôt P1 #14) ; dashboard monitoring admin (p95 latence/tool, taux erreur, retry, guards fails) ; alerting multi-axe (guards LLM, retry anormal, DB, timeouts, source_url ≠ HTTP 200, budget LLM).

**CCC-4 — Anonymisation PII avant LLM.** Pipeline systématique sur noms, adresses, RCCM, NINEA, IFU, téléphones → substitution tokens déterministes ; audit annuel du pipeline ; aucun PII dans les logs ; rétention stricte chez provider LLM.

**CCC-5 — Multi-tenancy et isolation.** RLS PostgreSQL sur 4 tables sensibles dès MVP (NFR12) + filtre WHERE applicatif SQLAlchemy session scope/DI systématique ; RBAC 6 rôles + rôles projet extensibles ; catalogue commun read-only (modification `admin_mefali` seul) ; généralisation RLS Phase Growth.

**CCC-6 — NFR-SOURCE-TRACKING.** 3 champs obligatoires (`source_url`, `source_accessed_at`, `source_version`) sur toute entité catalogue ; DRAFT non-publiable sans les 3 (contrainte modèle + validation API + UI) ; test CI nocturne HTTP 200 (FR63) ; audit trimestriel.

**CCC-7 — Interface admin typée par criticité NFR-ADMIN-LEVELS.** N1 édition libre (coordonnées, seuils simples, un admin, effet immédiat) ; N2 peer review (critères, packs, règles dérivation, pondérations — draft → review 2e admin → publication) ; N3 versioning strict (nouveaux référentiels, migrations — draft → review → test rétroactif snapshot → migration datée) ; audit trail 5 ans complet (FR64).

**CCC-8 — RAG transversal.** pgvector étendu à ≥ 5 modules sur 8 en Phase 0 (SC-T9, clôt P1 #13 promesse FR-005 spec 009), 8/8 en fin Phase 4 ; embeddings text-embedding-3-small ; citations rule-level (verdicts) + paragraph-level (narratifs).

**CCC-9 — Framework d'injection d'instructions unifié.** Prérequis Phase 0 (signal PRD 3 audit) ; consolide STYLE + WIDGET + GUIDED_TOUR + nouveaux contextes dans registry + builder ; évite la saturation des 4 spec-correctifs accumulés (013/015/016/017).

**CCC-10 — Enforcement context actif applicatif.** `active_project` + `active_module` enforcés par guards pré-tool + state machine ; prérequis Phase 0 (signal PRD 2) ; sans cela, multi-projets impossible.

**CCC-11 — Registre blocs visuels extensible.** Prérequis Phase 0 pour 11 blocs typés Phase 3 (KPI, donut, barres, timeline, carte géo, heatmap, gauge, table croisée, radar, waterfall, Sankey) ; résout dette P3 #1 `MessageParser` hardcodé.

**CCC-12 — Performance cube 4D + matérialisation verdicts.** Indexes composites PostgreSQL sur dimensions ; vues matérialisées requêtes chaudes ; cache tiède Redis Phase Growth ; matérialisation verdicts en table dédiée avec invalidation sélective (RI-2) ; batch async file Celery Phase Growth.

> **Critère de déclenchement fallback cube 3D (explicite) :** le fallback cube 3D (voie d'accès en flag binaire directe/intermédiée sans critères intermédiaires détaillés) est activable **UNIQUEMENT si** :
> - `p95 > 3 s` (≥ 50 % au-dessus de SC-T3 ≤ 2 s),
> - **après** application des **3 optimisations de base** (indexes composites sur dimensions cube, matérialisation verdicts en table cache, cache tiède applicatif LRU),
> - **sur scénario de référence** : 100 users simultanés avec catalogue à mi-complétion Phase 1 (≈ 150–250 critères, ≈ 5–8 référentiels, ≈ 4 pays couverts, ≈ 30 fonds enrichis de voies d'accès).
>
> **Sans cette conjonction cumulative, le cube 4D complet est maintenu** — c'est un différenciateur INN-2 central, non négociable au niveau du positionnement produit. Renoncer à la voie d'accès détaillée affaiblirait la promesse « financements réellement accessibles avec parcours concret ».

**CCC-13 — Risques critiques existentiels à préparer organisationnellement (pas seulement techniquement)** :

- **RM-6 dépendance LLM provider (technique)** : abstraction Provider layer (switch < 2 sem), backup provider configuré (OpenAI/Mistral), budget surveillé, plan de continuité outage > 24 h
- **RM-7 incident sécurité / data breach (organisationnel + technique)** : IRP documenté + tabletop trimestriel, cyber insurance Phase Growth, pen test externe obligatoire pré-pilote PME réelle, bug bounty léger Phase Growth, communication d'incident préparée (template user + autorité contrôle SN/CI)
- **RM-5 partenariats institutionnels retardés (mitigation architecturale)** : **admin N1 maintient les critères intermédiaires à jour même sans partenariat formel** avec SIB/Ecobank/BDU/BOAD. Le cube 4D opère à partir des données publiques vérifiées et trackées (`last_verified_at`, pipeline vérification trimestriel, NFR-SOURCE-TRACKING) ; un partenariat signé accélère la fraîcheur des données mais n'est pas un prérequis d'opération.
- **RM-3 concurrent direct apparaît sur le segment (mitigation architecturale)** : **catalogue data-driven + interface admin N1/N2/N3 + temps-réel sans redéploiement = time-to-market sur nouvelles certifications/référentiels** inférieur à un concurrent hard-codé. Ajouter un référentiel émergent (ex. nouvelle taxonomie régionale, nouvelle norme sectorielle) = quelques heures d'admin N3 vs semaines/mois d'un concurrent devant pousser du code en prod.

**CCC-14 — Transaction boundaries et cohérence (à décider Step 4).** Contours d'opérations atomiques vs eventually consistent à définir lors des décisions architecturales :

- **Opérations strictement atomiques** (candidats) : soumission `FundApplication` (snapshot + hash + signature + verdicts gelés doivent être cohérents en une transaction), génération livrable complète avec `FundApplicationGenerationLog`, réévaluation d'un critère avec propagation aux verdicts.
- **Opérations eventually consistent** (candidats) : matérialisation verdicts (pattern cache invalidable), notifications FR34 après publication d'un `ReferentialMigration`, audit trail d'accès aux données sensibles, budget LLM alerting.
- **Pattern Outbox** à évaluer pour les événements cross-bounded-context (ex. publication référentiel → invalidation cache matching → notification users impactés) afin d'éviter les incohérences inter-tables lors d'échecs partiels.
- **Verrouillage optimiste par `version_number`** à évaluer sur entités concurrent-éditées : `Company`, `Project`, `Fund`, `Intermediary`, `Criterion`, `Pack` (évite les écrasements silencieux quand 2 admins éditent en parallèle).
- **Dernière-écriture-gagne sur `Fact`** acceptable **si et seulement si** audit trail complet (`fact_version_history`) conservant toutes les valeurs antérieures avec horodatage et auteur — la donnée la plus récente gagne mais aucune valeur n'est perdue. À rapprocher de FR19 (versioning temporel des faits).
- **Décision à trancher en Step 4** : périmètre exact des opérations transactionnelles, stratégie de propagation d'événements, choix Outbox vs émission directe, politique de versioning.

**Dépendances inter-clusters (séquencement critique) :**
- Cluster A racine → tous les autres clusters en dépendent
- Cluster A' dépend de A (Company)
- Cluster B parallèle à A, utilisé par C et Cube 4D
- Cube 4D dépend de A + A' + B
- Cluster C dépend de A + A' + B
- Audit/Compliance/Security et RAG transversaux à tous

**10 Questions Ouvertes PRD (Annexe E) à trancher côté architecture :**
QO-A1 (Project sans Company ?), QO-A4 (changements scope post-financement — versioning à préciser), QO-A5 (clonage FundApplication → autre fonds), QO-A'1 (OCR validation vs humain en boucle), QO-A'3 (niveaux intermédiaires formalisation), QO-A'4 (formalisation vs conformité fiscale), QO-A'5 (régression niveau si liquidation partielle), QO-B3 (scoring évaluation partielle), QO-B4 (arbitrage faits conflictuels), QO-C2 (import gabarits bailleurs non officiels).

## Évaluation du starter / Fondation technique

### Préférences techniques déjà documentées (project context)

**Depuis `CLAUDE.md` (conventions projet) :** Nuxt 4 + Vue 3 Composition API + Pinia + TailwindCSS + GSAP + toast-ui/editor + Chart.js côté frontend ; FastAPI + Python 3.12 + SQLAlchemy async + LangGraph + LangChain + Claude via OpenRouter + PostgreSQL 16 + pgvector côté backend ; code en anglais / commentaires FR / UI FR / snake_case Python / PascalCase Vue sans préfixe dossier / structure Nuxt 4 sous `app/` ; **dark mode obligatoire** sur tous composants ; réutilisabilité composants UI (extraire patterns > 2 fois) ; migrations Alembic ; venv Python obligatoire.

**Depuis `docs/architecture-backend.md`, `architecture-frontend.md`, `integration-architecture.md`, `data-models-backend.md` :** architecture consolidée au 2026-04-16 couvrant 8 modules métier, 9 nœuds LangGraph, 32+ tools LangChain, streaming SSE, JWT+refresh, RAG pgvector, contrats REST/SSE exhaustifs.

**Depuis `Annexe I PRD` :** classification formelle conserver/compléter/remplacer de chaque composant pour la feature 5 clusters.

### Contexte : projet brownfield mature

**Point de départ non-négociable — état au 2026-04-19 :**
- 18 specs implémentées (001 → 018) livrées
- 8 modules métier opérationnels (chat, documents, ESG, carbone, financement, crédit, applications, dashboard/action_plan)
- 9 nœuds LangGraph + ToolNode conditionnel + 32+ tools LangChain dispatchés par module dans `graph/tools/`
- ~1103 tests verts avec principe **zero failing tests on main** opérationnel depuis story 9.3 (2026-04-17)
- Feature 019 (floating copilot + guided navigation) terminée avec `architecture-019-floating-copilot.md` — patterns SSE cross-routes, Driver.js lazy, tool `trigger_guided_tour`, widgets interactifs 018 — à réutiliser/étendre, pas à réécrire
- 14 dettes P1 identifiées par l'audit 18-specs du 2026-04-16 (4 résolues : #2 rate limiting, #4 quota stockage, #7 flag édition manuelle, #8 OCR bilingue) → 10 P1 restantes cadrent la Phase 0 (Annexe H PRD)

**Implication Step 3 :** l'« évaluation de starter » est une consolidation de la **fondation technique héritée**, pas un choix de boilerplate neuf. Pas de `npx create-*`. Les décisions de langage, framework, BDD, ORM, orchestration agent, testing, tooling sont toutes prises et validées en production.

### Domaine technique principal

- **Classification PRD** : `web_app` fintech avec spécialisation `sustainability_esg`, brownfield mature
- **Modalités secondaires superposées** : SaaS B2B multi-tenant · Copilot IA-first · Consulting augmenté par IA
- **Stack-type** : full-stack monolithe modulaire (FastAPI backend + Nuxt 4 frontend) avec orchestration agent LangGraph + RAG pgvector — architecture de référence stack agentique production-ready
- **Pas de candidat starter neuf pertinent** : les starters T3/RedwoodJS/Next.js/NestJS/Supabase sont conçus pour greenfield, incompatibles avec la dette technique et le scope brownfield déjà investi

### Stack existante (fondation de la feature 5 clusters)

**Frontend — Nuxt 4 + Vue 3 Composition API :**

| Composant | Version / Configuration | Rôle dans la feature |
|---|---|---|
| Nuxt 4 | App Router, structure `app/`, SSR sélectif + SPA majoritaire | Étendue avec 3 nouveaux modules UI (`projects`, `maturity`, `admin_catalogue`) |
| Vue 3 Composition API | `<script setup lang="ts">`, TypeScript strict | Nouveaux composants (`BeneficiaryProfileEditor`, `FormalizationPlanTimeline`, `CubeMatchResults`, `ReferentialVerdictTable`, `AdminCatalogueN1N2N3`) |
| Pinia | Stores par domaine | Nouveaux : `stores/projects.ts`, `stores/maturity.ts`, `stores/adminCatalogue.ts` |
| TailwindCSS + dark mode | `@theme` + variables dark dans `main.css` | Dark mode enforcement sur tous nouveaux composants |
| Chart.js + vue-chartjs | Dashboard | Étendu aux 11 blocs visuels typés Phase 3 |
| GSAP / toast-ui/editor / Driver.js lazy | Animations / éditeur Markdown / tours guidés | Conservés (pattern 019 réutilisé) |
| `useFetch` / `apiFetch` | Client API avec intercepteur 401 | **Dette P1 #1** : migrer 7 composables vers `apiFetch` (Phase 0) |

**Backend — FastAPI + Python 3.12 :**

| Composant | Version / Configuration | Rôle dans la feature |
|---|---|---|
| FastAPI | Python 3.12, ASGI uvicorn, monolithe modulaire 8 modules | Extension à **10–11 modules** (+ `projects`, `maturity`, `admin_catalogue`) |
| SQLAlchemy async | ORM asynchrone, sessions scoped | Étendu aux nouveaux modèles + vues matérialisées verdicts |
| Alembic | Migrations BDD | 8 nouvelles migrations Phase 1 (voir section Extensions requises) |
| Pydantic v2 | Schemas request/response | Schemas stricts pour guards LLM (SGES, IFC AIMM, plans, verdicts) |
| LangGraph | 9 nœuds + ToolNode + MemorySaver checkpointer | Extension à **11 nœuds** (+ `project_node`, `maturity_node`) — **`admin_node` rejeté, voir Clarification 2** |
| LangChain ≥ 0.3.0 | 32+ tools dispatchés dans `graph/tools/` par module | Extension avec nouveaux tools Cluster A/A'/B/C/D |
| langchain-openai ≥ 0.3.0 | Provider OpenRouter | Conservé. **Abstraction Provider layer** à formaliser (NFR42, RM-6) |
| Claude API via OpenRouter | `claude-sonnet-4`, streaming SSE natif, `request_timeout=60` (spec 015) | Conservé avec guards Pydantic stricts partout (CCC-1) |
| pgvector | Embeddings OpenAI `text-embedding-3-small`, IVFFlat MVP → HNSW > 100 k (NFR52) | Étendu aux 8 modules RAG via **service partagé, voir Clarification 6** |
| PostgreSQL 16 | + pgvector | +RLS 4 tables sensibles Phase 0 (NFR12) ; indexes composites cube 4D + vues matérialisées verdicts (CCC-12) |
| Tesseract OCR | `fra+eng` bilingue (story 9.4) | Conservé pour validation maturité admin (FR12) |
| WeasyPrint + Jinja2 + python-docx | PDF bailleurs + DOCX éditable | Base moteur livrables Cluster C |
| pytest + pytest-asyncio | ~1103 tests verts | Voir **Clarification 4 — Stratégie tests** |

**Orchestration agent — LangGraph :**

| Nœud | Rôle | Évolution feature 5 clusters |
|---|---|---|
| `chat_node` | Conversation générale | Conservé. Injection `active_project` + `active_module` (CCC-10 Phase 0) |
| `esg_scoring_node` | Scoring ESG 30 critères | **Refactoré** : architecture 3 couches Fact→Criterion→Verdict (Cluster B Phase 1) |
| `carbon_node` | Bilan empreinte carbone | Conservé. `batch_save_emission_entries` (P1 #12 Phase 0), adaptation TCFD Phase 3 |
| `financing_node` | Matching projet-financement | **Refactoré** : cube 4D Phase 1 |
| `applications_node` | Génération dossiers bailleurs | **Refactoré** : moteur livrables Cluster C + SGES BETA Phase 1 |
| `credit_node` | Scoring crédit vert | Conservé. Extension RAG via service partagé (CCC-8) |
| `action_plan_node` | Plan d'action + timeline | Extension : `FormalizationPlan` + nouveaux rappels |
| `document_node` | Upload + analyse documents | Conservé. Extension : validation maturité + attestations qualitatives (FR18) |
| `profiling_node` | **Dead code** (P1 #3) | **À supprimer Phase 0** |

**Nouveaux nœuds feature 5 clusters (confirmés) :**
- `project_node` — création/édition Project, ProjectMembership, FundApplication, snapshot, cycle de vie 5 états (FR4–FR10)
- `maturity_node` — self-declaration + OCR validation + FormalizationPlan + auto-reclassement (FR11–FR16)

### Décisions architecturales héritées

**Langage & runtime** : Python 3.12 backend (pas de 3.13+ MVP), TypeScript 5.x strict frontend. Monolithe modulaire, **pas de microservices, pas de polyglot** — voir Clarification 1.

**Patterns d'organisation backend :**
- Modules métier par domaine : `backend/app/modules/<domain>/{router.py, service.py, schemas.py, models.py}`
- Services consomment services d'autres modules, **pas leurs tables directement** (anti God service P2 #25)
- Tools LangChain dans `backend/app/graph/tools/<domain>_tools.py`
- Prompts dans `backend/app/prompts/<domain>.py` → **à consolider** via framework d'injection unifié (CCC-9 Phase 0)
- Migrations Alembic nommage `NNN_description.py`
- Tests dans `backend/tests/test_<module>/`, SQLite in-memory pour CI (spec 017)

**Patterns d'organisation frontend :**
- Pages : `frontend/app/pages/` (routing auto Nuxt)
- Composables : `frontend/app/composables/useXxx.ts`
- Stores Pinia : `frontend/app/stores/`
- Composants : `frontend/app/components/` (PascalCase sans préfixe dossier)
- Composants UI génériques : `frontend/app/components/ui/`
- Dark mode obligatoire sur tous nouveaux composants

**Infrastructure & déploiement (à confirmer Step 10 NFR) :**
- **Data residency tranchée** : AWS EU-West-3 Paris (NFR24)
- Orchestration container : voir **Clarification 3** ci-dessous
- PostgreSQL managé RDS EU-West-3 + pgvector extension
- CloudFront + S3 Phase Growth
- Environnements isolés DEV / STAGING / PROD (NFR73)

### Extensions requises pour la feature 5 clusters

**Nouveaux modules métier (Phase 1) :**

```
backend/app/modules/
├── projects/           # Cluster A (FR1–FR10)
├── maturity/           # Cluster A' (FR11–FR16)
└── admin_catalogue/    # Signal PRD 1 + Cluster D (FR24, FR35, FR43, FR64, NFR-ADMIN-LEVELS)
```

**Modules étendus significativement :** `modules/esg/` (refactor 3 couches), `modules/financing/` (cube 4D), `modules/applications/` (moteur livrables + SGES BETA), `modules/reports/` (guards LLM universels), `modules/action_plan/` (FormalizationPlan + nouveaux rappels).

**Nouveaux tools LangChain (non exhaustif) :** `projects_tools.py`, `maturity_tools.py`, `admin_catalogue_tools.py`, extension de `esg_tools.py` et `financing_tools.py`.

**Nouvelles dépendances Python (à formaliser Step 4) :**
- `Hypothesis` (property-based testing SC-T6)
- `boto3` (migration S3 Phase Growth)
- `celery` + `redis` (queue asynchrone P1 #6 — Phase Growth mais prep Phase 0)
- `detect-secrets` / `truffleHog` en pre-commit (NFR15 Phase 0)
- `clamav-daemon` + `python-clamd` (détection malware P2 #7, à prioriser si scope sécurité étendu)

**Nouvelles migrations Alembic (ordre séquentiel à affiner Step 4) :**
1. `020_create_projects_schema.py`
2. `021_create_maturity_schema.py`
3. `022_create_esg_3_layers.py`
4. `023_create_deliverables_engine.py`
5. `024_enable_rls_on_sensitive_tables.py`
6. `025_add_source_tracking_constraints.py`
7. `026_create_admin_catalogue_audit_trail.py`
8. `027_cleanup_feature_flag_project_model.py` (retrait flag fin Phase 1 — NFR63)

**Remplacements ciblés (pas de starter neuf) :**

| Existant à remplacer | Replacement Phase 0 |
|---|---|
| Hard-coding catalogue (`seed.py` 889 lignes) | Tables BDD `fund`, `intermediary`, `fund_intermediary_liaison` + admin UI N1 |
| `SECTOR_WEIGHTS` / `SECTOR_BENCHMARKS` hard-codés (P1 #9, P2 #9) | Tables BDD + admin UI N2 |
| Facteurs émission carbone hard-codés | Table `carbon_emission_factor(country × activity × scope × version)` + admin |
| 4 spec-correctifs prompts (013/015/016/017) | Framework d'injection unifié (registry + builder) — CCC-9 |
| Stockage local `/uploads/` | S3 EU-West-3 + backup 2 AZ (abstraction `StorageProvider` layer Phase 0) |

### Clarifications structurantes actées Step 3 (6 décisions)

Les 6 clarifications suivantes sont **actées définitivement ici** pour éviter leur remise en question en Step 4. Elles constituent des garde-fous architecturaux.

**Clarification 1 — Pas de split microservices.**

- **Décision** : monolithe modulaire FastAPI maintenu pour MVP, Growth et Scale. 3 nouveaux modules (`projects`, `maturity`, `admin_catalogue`) dans `backend/app/modules/`, pas de nouveau service indépendant.
- **Rationale** : coût opérationnel des microservices (orchestration, latence inter-service, observabilité distribuée, consistency patterns) est **prohibitif** face à l'équipe MVP (2–3 devs backend + 0.5 DevOps). Le monolithe modulaire existant supporte largement la charge cible (500 users simultanés MVP, NFR50 révisé). Les préoccupations de scale sont adressées par (a) stateless FastAPI + scaling horizontal (NFR49), (b) RDS PostgreSQL managé avec read replicas Phase Growth, (c) cache tiède Redis Phase Growth, (d) file asynchrone Celery Phase Growth pour livrables lourds.
- **Re-évaluation** : Phase 5 Vision uniquement si un sous-système présente un besoin concret (scaling indépendant, équipes distinctes, contraintes de conformité). Candidats théoriques (non engagés) : moteur livrables si volume génération > 1000/jour, admin_catalogue si équipe catalogue distincte émerge.
- **Conséquence** : tous les modules partagent la même session SQLAlchemy, les mêmes transactions, la même observabilité. Pattern Outbox évalué au niveau module interne (CCC-14), pas inter-service.

**Clarification 2 — `admin_node` rejeté, admin catalogue UI-only.**

- **Décision** : **pas de nœud LangGraph `admin_node`**. L'interface admin catalogue (Mariam — Journey 5) reste intégralement UI (formulaires Vue 3 + validation multi-étape + workflow N1/N2/N3). Pas de chat agent pour les admins Mefali.
- **Rationale** :
  1. Le positionnement Copilot IA-first cible **les users finaux (PME)**, pas les admins système Mefali. Le PRD Executive Summary et la modalité secondaire « toute feature invocable depuis le chat » concernent l'expérience utilisateur PME, pas l'administration du catalogue.
  2. Les workflows N2 (peer review) et N3 (versioning strict avec test rétroactif sur snapshot + migration datée) sont **structurellement UI** : formulaires multi-étape, upload de matrices CSV, validation asynchrone par un 2ᵉ admin, préview des diffs, confirmation avec date d'effet. Ces workflows ne gagnent rien à passer par un agent conversationnel et perdraient en discoverabilité + rigueur d'audit trail.
  3. Éviter la sur-ingénierie : un `admin_node` ajouterait un couplage entre les opérations CRUD catalogue et la couche LLM (coût, latence, risque d'hallucination sur des données structurelles).
- **Conséquence Step 4** : LangGraph reste à **11 nœuds** (`chat_node`, `esg_scoring_node`, `carbon_node`, `financing_node`, `applications_node`, `credit_node`, `action_plan_node`, `document_node`, `project_node` nouveau, `maturity_node` nouveau) + ToolNode conditionnel. Les tools admin (`create_catalogue_entity_N1`, `submit_catalogue_review_N2`, `publish_referential_N3`, etc.) restent accessibles via endpoints REST classiques consommés par l'UI admin, **pas via LangChain**.

**Clarification 3 — Orchestration container : AWS ECS Fargate recommandé MVP.**

- **Décision MVP** : **AWS ECS Fargate** recommandé. Alternative plus simple acceptable : **EC2 + Docker Compose** si la complexité Fargate (task definitions, IAM roles, ALB integration) s'avère excessive en Phase 0. **Kubernetes/EKS rejeté pour le MVP.**
- **Rationale** :
  1. Équipe MVP 2–3 devs backend + 0.5 DevOps : **overhead opérationnel Kubernetes incompatible** (cluster updates, networking CNI, RBAC, ingress controllers, helm charts). Le 0.5 FTE DevOps serait saturé par Kubernetes sans livrer de valeur produit.
  2. ECS Fargate : serverless containers sur AWS, tarification au pod-hour, intégration native ALB + CloudWatch + IAM, **zéro gestion de nodes**. Suffisant largement pour 500 users simultanés MVP.
  3. EC2 + Docker Compose : encore plus simple si équipe préfère une infra unique visible ; trade-off = scaling manuel + pas d'auto-healing.
  4. Migration future vers EKS **possible** Phase 5 Vision si volumétrie réelle dépasse 50 000 users simultanés ET si équipe DevOps s'étoffe — pas engagé.
- **À confirmer Step 10 NFR** : choix final ECS Fargate vs EC2+Compose après costing détaillé + benchmark latence EU-West-3 ↔ AO.

**Clarification 4 — Stratégie tests pour les 5 clusters.**

Détail structuré à reprendre en Step 4 dans la section patterns de tests :

| Niveau | Framework | Scope | Seuils / gates |
|---|---|---|---|
| **Unitaires** | `pytest` + `pytest-asyncio` (backend), `Vitest` (frontend) | Fonctions pures, services isolés, composants UI isolés | **80 % coverage standard** / **85 % code critique** (guards LLM, anonymisation PII, RLS, rate limiting, signature, snapshot, livrables) — CI gate NFR60 |
| **Property-based** | `Hypothesis` (Python) | **SC-T6 non-contradiction verdicts multi-référentiels** : pour un même `Fact` à verdicts dérivés, aucune paire de verdicts ne doit être logiquement contradictoire | Tests Phase 1, scénarios générés auto (≥ 1000 itérations par suite) |
| **Intégration** | `pytest` + `httpx.AsyncClient` + SQLite in-memory (spec 017) ou Postgres Docker | Cube 4D end-to-end (query → match → access routes), pipeline `ReferentialMigration` complet (publish → notify → user choice → snapshot preserved), transaction boundaries `FundApplication.submit()` avec snapshot + hash + signature + verdicts atomiques (CCC-14) | 100 % parcours critiques Phase 1 |
| **E2E** | `Playwright` (extension du socle stories 8.1–8.3) | **5 journeys PRD** (Aminata solo informel, Moussa consortium multi-projets, Akissi OHADA + SGES BETA, Ibrahim remédiation, Mariam admin catalogue) — un scénario par persona, exécution navigateur mobile + desktop | Tous verts avant release Phase 1 |
| **Load testing** | `Locust` ou `k6` | **Scénarios NFR71 obligatoires avant pilote** : 100 users simultanés 30 min sur chat+cube 4D, 10 générations SGES simultanées, 500 appels/min endpoints read-only | Tous NFR Performance (NFR1–NFR8) respectés sous charge. Rapport archivé. À re-lancer à chaque phase avant prod. |

- **Politique CI** : zero failing tests on main (NFR59) — enforcé depuis story 9.3.
- **Détail complet** à expliciter en Step 4 patterns d'implémentation.

**Clarification 5 — Feature flag `ENABLE_PROJECT_MODEL` : simple, pas de librairie externe.**

- **Décision** : simple variable d'environnement `ENABLE_PROJECT_MODEL=true|false` + wrapper Python léger `backend/app/core/feature_flags.py` exposant `is_project_model_enabled() -> bool`. Pas de `flipper` / `Unleash` / `LaunchDarkly` / autre librairie externe.
- **Rationale** :
  1. **Un seul flag à gérer pendant toute la migration Phase 1**. Les librairies externes sont conçues pour des dizaines de flags, targeting par user/segment, rollout progressif — sur-ingénierie totale pour ce cas.
  2. Coût cognitif et ops réduit à zéro : var env + wrapper 10 lignes vs service externe + API calls.
  3. Conforme au principe CLAUDE.md (réutilisabilité composants — extraire seulement si pattern > 2 fois). Ici, pattern unique, pas d'extraction.
- **Pattern de test pendant migration** :
  1. **2 suites de tests exécutées en CI** : `make test-with-project-flag=on` + `make test-with-project-flag=off`, toutes deux vertes en continu pendant la Phase 1.
  2. À l'issue de la migration (fin Phase 1), story dédiée `cleanup-feature-flag-project-model` (migration Alembic 027) retire le flag, supprime le code legacy path, consolide les 2 suites en **1 seule suite** (mode unique).
  3. Si le flag reste > 3 mois après clôture Phase 1 sans retrait : alerte équipe (anti-pattern observé avec `profiling_node` dette P1 #3).
- **Implémentation prévue** :
```python
# backend/app/core/feature_flags.py
import os

def is_project_model_enabled() -> bool:
    """Phase 1 migration flag — à retirer fin Phase 1 via migration 027."""
    return os.getenv("ENABLE_PROJECT_MODEL", "false").lower() == "true"
```

**Clarification 6 — Dépendances complémentaires tranchées.**

- **i18n Nuxt** : `@nuxtjs/i18n` retenu (**pas** `vue-i18n` direct). Rationale : intégration Nuxt native (auto-imports, routing localisé optionnel, config centralisée `nuxt.config.ts`), meilleure DX, maintenu par l'équipe Nuxt. Locale **`fr` seule MVP** (NFR65). Architecture extensible `en` Phase Vision sans refactor.
- **RAG transversal — service partagé** : création de `backend/app/rag/service.py` exposant 3 fonctions canoniques :
  - `search_similar_chunks(query: str, module: str | None = None, top_k: int = 5) -> list[ChunkMatch]` — recherche vectorielle pgvector
  - `store_document_chunks(document_id: UUID, chunks: list[Chunk], embeddings_model: str) -> None` — ingestion
  - `citation_extractor(chunks: list[ChunkMatch], generation_output: str) -> list[Citation]` — extraction de citations rule-level + paragraph-level (FR71)
  - Chaque module consomme via `from app.rag.service import search_similar_chunks`. **Pas de duplication du code RAG par module.**
- **Conséquence** : le module `applications` (qui devait l'utiliser selon FR-005 spec 009 non tenue, P1 #13) + les 7 autres modules cibles (RAG transversal CCC-8) importent le même code. Cohérence garantie. Un seul pipeline à maintenir (embeddings model, chunking strategy, re-ranking éventuel Phase Growth).

---

**Pas d'initialisation CLI à exécuter.** La première story Phase 0 sera `0-1-extension-setup-and-discovery` (plutôt qu'un `create-*`) : brancher les nouvelles migrations Alembic 020–023, créer les squelettes de modules (`projects`, `maturity`, `admin_catalogue`), installer `@nuxtjs/i18n` + `Hypothesis` + `detect-secrets`, créer `backend/app/rag/service.py`, créer `backend/app/core/feature_flags.py`, valider que la baseline 1103 tests reste verte.

## Décisions architecturales fondamentales

### Analyse de priorité des décisions

**Déjà tranché (Steps 1–3 + PRD + 6 Clarifications Step 3) — ne pas re-décider :** stack technique, monolithe modulaire (Clarif. 1), `admin_node` rejeté (Clarif. 2), AWS ECS Fargate recommandé (Clarif. 3), tests strategy 5 niveaux (Clarif. 4), feature flag simple env var (Clarif. 5), `@nuxtjs/i18n` + RAG service partagé (Clarif. 6), data residency EU-West-3 (NFR24), JWT+MFA+step-up, RLS 4 tables sensibles, chiffrement at rest KMS, anonymisation PII, NFR-SOURCE-TRACKING, snapshot hash, guards LLM Pydantic, observabilité `request_id`, SLA différencié.

**11 décisions critiques (tranchées ici) :**

| # | Catégorie | Décision |
|---|---|---|
| 1 | Data — Cluster A | Modèle `Company × Project` N:N avec cumul de rôles |
| 2 | Data — Matching | Pack par fonds (absorbe 5ᵉ dim) + résolution conflits STRICTEST WINS |
| 3 | Data — Cluster B | Architecture 3 couches ESG avec DSL borné + micro-Outbox invalidation |
| 4 | Data — Matching | Cube 4D Postgres + GIN + cache LRU (Redis différé Phase Growth) + fallback 3D critère strict |
| 5 | Data — Cluster C | Moteur livrables pyramide + template_sections relationnelle + prompt versioning |
| 6 | Data — Cluster D | Admin N1/N2/N3 state machine + échantillon représentatif N3 |
| 7 | Ops | Multi-tenancy RLS 4 tables + filtre WHERE + log admin escape obligatoire |
| 8 | Ops | DEV/STAGING/PROD + copie mensuelle PROD→STAGING anonymisée + validation automatique |
| 9 | Ops | Backup + PITR 5 min + RTO 4h / RPO 24h engagé |
| 10 | Ops | LLM Provider Layer + switch dégradé <2 sem / optimal 4-6 sem |
| 11 | Data | Transaction boundaries + micro-Outbox MVP `domain_events` |

---

### Décision 1 — Modèle `Company × Project` N:N avec cumul de rôles

**Contexte** : FR1–FR10. Migration vers N:N. QO-A1 et QO-A4 à trancher.

**Décision** : tables `projects` / `project_memberships` / `project_role_permissions` / `fund_applications` / `project_snapshots` / `company_projections` / `beneficiary_profiles`.

**Contrainte clé (ajustement D1)** : `UNIQUE (project_id, company_id, role)` — **permet cumul de rôles** sur un même projet. Exemple : Company X peut être simultanément `porteur_principal` ET `beneficiaire` dans un consortium interne (cas coopérative où la structure porte ET fait partie des bénéficiaires).

**QO-A1 tranchée** : `Project` NE PEUT PAS exister sans `Company` — contrainte métier CHECK service (≥ 1 membership `porteur_principal`). Pas de projet orphelin (responsabilité juridique).

**QO-A4 tranchée** : versioning via `project_snapshots` + `version_number` (optimistic locking). Changements post-financement n'affectent pas les FundApplication soumises (snapshot gelé). Nouveau scope = nouvelle FundApplication ou amendment path Phase Growth.

**QO-A5 différée** : clonage `FundApplication` → autre fonds, à trancher Epic breakdown (endpoint suggéré : `POST /api/fund-applications/{id}/clone?target_fund_id=X`).

**Rationale** : enum role extensible (vs fixe) aligne FR7 ; cumul de rôles reflète réalité consortium AO ; table permissions séparée = DRY + audit cleaner (FR64).

**Implications cascade** : RBAC étendu au niveau membership, feature flag `ENABLE_PROJECT_MODEL` protège la bascule (Clarif. 5), migration `020_create_projects_schema.py` première.

---

### Décision 2 — Pack par fonds + résolution conflits STRICTEST WINS

**Contexte** : chaque fonds superpose ses exigences. Modélisation des "sur-exigences" dans le cube 4D.

**Décision** : **Option 2.C — Pack par fonds** avec overlay au niveau `pack_criteria.fund_specific_overlay_rule`. Cube reste **4D**, la 5ᵉ dimension est **absorbée dans le Pack**.

**Règle de résolution des conflits (ajustement D2) — STRICTEST WINS** :
- Quand plusieurs Packs actifs (Akissi : IFC + RSPO + BCEAO) définissent des `fund_specific_overlay_rule` sur le **même critère**, la règle la plus stricte l'emporte.
- Exemple : IFC EHS BOD ≤ 30 mg/L, RSPO 5.3 BOD ≤ 50 mg/L → verdict basé sur 30 mg/L (IFC strictiste).
- **Alerte UI obligatoire** : badge "Conflit de seuils détecté" sur le critère, avec détail des règles superposées et indication du seuil appliqué. L'utilisateur comprend pourquoi son verdict est FAIL sur un Pack et PASS conditionnel sur l'autre (cf. Journey 3 Akissi : IFC PS3 FAIL, RSPO 5.3 PASS conditionnel).
- Cohérent avec esprit « aller au-delà du minimum » : le plus strict protège l'utilisateur vis-à-vis de tous les bailleurs ciblés.

**Rationale** : Pack est façade naturelle FR22 ; composition > héritage ; absorbe la complexité sans explosion combinatoire cube 5D.

**Implications** : Admin N2 configure les Packs (peer review obligatoire) ; UI `ReferentialVerdictTable` affiche alerte de conflit.

---

### Décision 3 — Architecture 3 couches ESG (DSL borné + micro-Outbox invalidation)

**Contexte** : FR17–FR26. INN-1 différenciateur. Performance SC-T4 ≤ 30 s verdicts multi-ref.

**Décision — Matérialisation verdicts + DSL borné + invalidation event-driven** :

**Modèles** : `facts`, `fact_versions` (audit), `criteria`, `criterion_derivation_rules`, `criterion_referential_map`, `referential_verdicts` (matérialisé), `referentials`, `referential_versions`, `referential_migrations`, `packs`, `pack_criteria`.

**Ajustement D3.1 — DSL borné obligatoire** (pas `eval`) :

Primitives supportées **exclusivement** :
- `threshold` : `{ "fact_key": "effluent.bod_mg_per_liter", "operator": "<=|<|>|>=|==|!=", "threshold": 30, "unit": "mg/L" }`
- `boolean_expression` : `{ "op": "AND|OR|NOT", "operands": [<sous-règle>] }` (arbre borné, profondeur max 5)
- `aggregate` : `{ "fact_keys": ["hr.workforce.*"], "agg_function": "sum|avg|min|max|count", "then_threshold": {...} }`
- `qualitative_check` : `{ "fact_key": "grievance.mechanism_exists", "attestation_required": ["document", "signed_declaration"] }`

**Validation Pydantic stricte au parsing + discriminator sur `rule_type`** → toute règle malformée rejetée à l'édition. **Aucune évaluation de code arbitraire possible**. Sécurité : même si admin compromis, pas de RCE via injection de règle.

**Ajustement D3.2 — Invalidation sélective event-driven via micro-Outbox (D11)** :
- Event `fact_updated(fact_id)` ou `criterion_rule_updated(criterion_id)` inséré dans table `domain_events` (D11)
- Worker batch 30s consomme event → identifie `referential_verdicts` impactés via jointure (criterion_referential_map + facts/fact usage) → `UPDATE invalidated_at = NOW() WHERE ...` sur verdicts concernés
- Recalcul à la demande (lazy) ou batch nocturne selon volumétrie
- **Pas de trigger PostgreSQL** — portabilité, testabilité, debugging simple

**Rationale** : matérialisation nécessaire pour SC-T4 ; DSL borné = sécurité critique (admin peut éditer rules sans risque RCE) ; event-driven via `domain_events` = durabilité (D11).

**Implications** : migration `022_create_esg_3_layers.py` ; tests property-based Hypothesis sur SC-T6 ; story `micro-outbox-domain-events` (D11 nouvelle) prérequis Phase 0.

---

### Décision 4 — Cube 4D Postgres + GIN + cache LRU

**Contexte** : FR27–FR35. SC-T3 ≤ 2 s p95.

**Décision** : indexes composites GIN + vue matérialisée `mv_fund_matching_cube` + cache applicatif LRU 5 min + fallback cube 3D sur critère strict (CCC-12 Step 2).

**Ajustement D4 — REFRESH CONCURRENTLY à mesurer en load testing Phase 0** :
- Vue `mv_fund_matching_cube` potentiellement 10 k+ lignes (funds × intermediaries × countries × sectors)
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` = pas de lock mais coût CPU/IO proportionnel au volume
- **Si `REFRESH CONCURRENTLY` > 10 s** en load testing Phase 0 → alternatives à étudier :
  - **Refresh incrémental via triggers** sur `funds`, `intermediaries`, `fund_intermediary_liaison` (INSERT/UPDATE/DELETE → marquer rows dirty + background refresh ciblé)
  - **Matérialisation partielle par pays** : `mv_fund_matching_cube_CI`, `mv_fund_matching_cube_SN`, etc. (refresh du sous-ensemble impacté seulement)
- **Décision définitive reportée au rapport de load testing Phase 0**, pas maintenant. Dans l'intervalle, `REFRESH CONCURRENTLY` global reste la stratégie par défaut.

**Redis différé Phase Growth** : seuil d'activation = > 500 users simultanés confirmés OU latence cache LRU insuffisante.

**Fallback cube 3D** : critère explicite Step 2 (p95 > 3 s ET 3 optimisations ET scénario 100 users sur catalogue mi-Phase 1).

**Implications** : test de charge Phase 0 obligatoire (NFR71) — scénarios explicites "100 users + catalogue mi-Phase 1" + mesure latence REFRESH CONCURRENTLY.

---

### Décision 5 — Moteur livrables (template_sections relationnelle + prompt versioning)

**Contexte** : FR36–FR44. SGES BETA NO BYPASS.

**Décision — pyramide Template → Section → Block** avec 2 améliorations :

**Ajustement D5.1 — Table relationnelle pour structure template (vs JSONB)** :
```
document_templates (id, name, target_type, target_entity_id FK NULL, version, ...)
  └─ Plus de structure_json JSONB — structure déléguée à template_sections

template_sections (
  template_id FK,
  section_id FK,
  order_index INT,
  is_optional BOOL DEFAULT false,
  PRIMARY KEY (template_id, section_id)
)
```

Bénéfices : réordonner une section = UPDATE simple (pas rewrite JSONB complet), audit trail granulaire (CRUD event par `template_sections` row vs blob), validation FK cohérente.

**Ajustement D5.2 — Prompt versioning obligatoire** :
```
reusable_sections (id, code UNIQUE, name, purpose, current_prompt_version INT, pydantic_schema_json JSONB, human_review_required BOOL)

reusable_section_prompt_versions (
  section_id FK,
  version INT,
  template_text TEXT,  -- prompt Jinja-like avec placeholders {{facts.xxx}}
  created_at TIMESTAMPTZ,
  created_by_user_id FK,
  change_note TEXT,
  PRIMARY KEY (section_id, version)
)
```

Rationale : reproductibilité historique **indispensable** pour l'audit — *« pourquoi ce SGES a été produit avec ces mots ? »* doit pouvoir se rejouer avec le même prompt + même facts + même référentiels 2 ans après. Sans versioning = audit catastrophiquement impossible. Les `fund_application_generation_logs` (FR57) référencent `(section_id, prompt_version)`.

**Guards par section** (CCC-1) : `pydantic_schema_json` + longueur + cohérence numérique + vocabulaire interdit.

**SGES BETA NO BYPASS** (FR44) : `human_review_required = true` forcé, workflow bloquant applicatif rejette toute tentative de bypass même `admin_mefali`/`admin_super` (log security incident).

**Implications** : migration `023_create_deliverables_engine.py` inclut les 2 tables relationnelles + prompt versions ; tests contenu PDF (P2 #20 audit) parse sections ; queue Celery Phase Growth pour SGES complet.

---

### Décision 6 — Admin N1/N2/N3 state machine + échantillon représentatif

**Contexte** : FR24, FR35, FR43, FR64, NFR-ADMIN-LEVELS.

**Décision** : state machines N1/N2/N3 explicites en Python + audit trail table dédiée (pas trigger PG).

**Workflow N1** : `published` (édition immédiate).
**Workflow N2** : `draft → pending_review → published | rejected` (2e admin obligatoire).
**Workflow N3** : `draft → pending_review → tested_retroactively → scheduled_migration → published | rejected`.

**Ajustement D6 — Scope explicite du test rétroactif N3 (état `tested_retroactively`)** :

**Échantillon représentatif** (pas 100 %, pas 10 derniers) :
- Stratification par `sector` × `country` × `company_maturity` × `project_maturity`
- Taille cible : **≥ 50 snapshots représentatifs** OU 5 % de la population totale (le plus grand des deux)
- Sélection aléatoire stratifiée (éviter biais temporel)
- Calcul métriques de divergence entre verdicts ancienne version vs nouvelle version :
  - % verdicts changés (PASS → FAIL, PASS → REPORTED, etc.)
  - % FundApplications dont score global bascule au-dessus/sous-dessous seuil bancable
  - Distribution des changements par cluster/critère

**Seuil blocage migration (configurable par admin N3)** : si **% verdicts changés > 20 %** sur échantillon, la migration est bloquée et nécessite une revue élargie (ex. 3 admins + consultant ESG externe) avant autorisation.

Rationale :
- 100 % snapshots = coûteux (heures de compute sur catalogue complet) et disproportionné (N snapshots = N × M verdicts recalculés)
- 10 derniers = non représentatif (biais secteur/pays/maturité)
- Échantillon représentatif 50+ = équilibre statistique + coût acceptable (~minutes compute)
- Seuil 20 % = changement significatif nécessitant alerte (configurable par admin N3 selon contexte, ex. 10 % pour référentiel sensible comme IFC PS)

**Audit trail table dédiée** (pas trigger PG) : `admin_catalogue_audit_trail` avec `workflow_level`, `changes_before/after`, `actor_user_id`, `workflow_state_before/after`, rétention 5 ans (FR64).

**Implications** : migration `026_create_admin_catalogue_audit_trail.py` ; UI frontend distingue visuellement N1/N2/N3 ; rapport de test rétroactif généré automatiquement avant `scheduled_migration`.

---

### Décision 7 — Multi-tenancy RLS 4 tables + log admin escape

**Contexte** : NFR12. RLS 4 tables sensibles. Conformité SN/CI.

**Décision** : RLS activé sur `companies`, `fund_applications`, `facts`, `documents` + filtre WHERE applicatif ailleurs + migration Growth pour généralisation.

**Policies PostgreSQL** avec escape pour `admin_mefali`/`admin_super`.

**Ajustement D7 — Log admin escape obligatoire** :

Tout accès aux tables RLS par les rôles `admin_mefali` ou `admin_super` DOIT être logué systématiquement dans une nouvelle table `admin_access_audit` (rétention 5 ans) :

```
admin_access_audit (
  id UUID PK,
  admin_user_id FK,
  admin_role ENUM{admin_mefali, admin_super},
  table_accessed TEXT,
  operation ENUM{SELECT, INSERT, UPDATE, DELETE},
  record_ids JSONB,  -- IDs des lignes accédées si disponibles
  request_id UUID,  -- corrélation avec logs applicatifs
  query_excerpt TEXT NULL,  -- requête exécutée (tronquée)
  accessed_at TIMESTAMPTZ,
  reason TEXT NULL  -- motif optionnel documenté par l'admin
)
```

**Enforcement** via middleware SQLAlchemy event listener :
```python
@event.listens_for(Session, "before_flush")
def log_admin_access(session, flush_context, instances):
    if current_user_role() in ('admin_mefali', 'admin_super'):
        for obj in session.new | session.dirty | session.deleted:
            if obj.__tablename__ in RLS_PROTECTED_TABLES:
                log_admin_access_audit(...)
```

Pour les SELECT (non capturés par `before_flush`), interceptor via `Query.execute` + flag sur session.

Rationale : sans ce log, l'escape admin RLS est un bypass invisible du user → risque confiance + conformité SN/CI. Les admins ont des raisons légitimes d'accéder (support, debug, audit bailleur, signalement modération) mais chaque accès doit être traçable.

**Implications** : middleware SQLAlchemy à implémenter Phase 0 ; migration `024_enable_rls_on_sensitive_tables.py` inclut création table `admin_access_audit` ; tests sécurité dédiés (user A ne peut pas lire données user B ; admin accès loggé).

---

### Décision 8 — Environnements DEV/STAGING/PROD + validation anonymisation

**Contexte** : NFR73.

**Décision** : 3 environnements isolés + pipeline de copie PROD→STAGING anonymisée + validation automatique.

**Ajustement D8.1 — Fréquence formalisée** :
- **Copie mensuelle** PROD → STAGING anonymisée : **1er du mois**, créneau maintenance **hors heures ouvrées AO** (ex. 02:00–06:00 GMT dimanche précédent le 1er)
- **Ad-hoc sur demande** avant UAT pilote majeur (consultant ESG, bailleur review) — déclenchement manuel via runbook

**Ajustement D8.2 — Test automatique de complétude anonymisation** :

Avant toute restore STAGING, script de validation `validate_anonymization.py` qui scanne l'export :
- Regex RCCM (format OHADA) : détection motifs `\bRC[CM]?\s*\w+\s*\d+\b`
- Regex NINEA (SN) : `\b\d{7,9}\s*[A-Z]\s*\d\b`
- Regex IFU (CI, BF, BJ, TG) : `\b\d{7,13}[A-Z]?\b` selon format pays
- Regex NIF (ML, NE) : formats pays-spécifiques
- Regex emails réels : `\b[\w.-]+@(?!anonymized\.test)[\w.-]+\b`
- Regex téléphones AO : `\b\+?22[1-9]\s?\d{8,9}\b` (préfixes CEDEAO)
- Regex noms détectés par NER (spaCy `fr_core_news_lg` ou équivalent) sur champs `name`, `contact_person`, `legal_representative`

**Si détection d'un champ non anonymisé** → pipeline **fail fast**, dump rejeté, alerte équipe DevOps + audit log. STAGING conserve l'état précédent.

Rationale : automatisation empêche fuite PII par oubli de règle d'anonymisation (ex. ajout colonne `contact_secondaire_phone` non mappée). Conformité SN 2008-12 + CI 2013-450 renforcée.

**Implications** : story Phase 0 `environment-isolation-pipelines` inclut ce script ; runbook documenté pour restore ad-hoc + tests mensuels.

---

### Décision 9 — Backup + PITR 5 min + RTO 4h / RPO 24h engagé

**Contexte** : NFR29–NFR36.

**Décision** : backups AWS RDS + PITR activé en arrière-plan + S3 CRR EU-West-3 → EU-West-1.

**Ajustement D9.1 — PITR activé** :
- **RPO engagé MVP : 24 h** (simplicité communication + runbook)
- **Capacité technique réelle : 5 min** via AWS RDS Point-in-Time Recovery (logs WAL archivés toutes les 5 min) — **activé en arrière-plan dès Phase 0** sans coût supplémentaire significatif (inclus dans AWS RDS)
- Usage PITR : incidents critiques (corruption données suite bug, suppression accidentelle) avant la fenêtre de backup quotidien — runbook documenté pour rollback granulaire

**Ajustement D9.2 — Coût CRR S3 budgété explicitement** :
- Cross-Region Replication S3 EU-West-3 → EU-West-1 : stockage dupliqué = **coût ×2 sur le volume répliqué**
- À budgéter explicitement dans NFR69 (actuellement ~100–200 €/mois stockage+backup pour MVP 500 users) : impact estimé +30–50 €/mois pour CRR sur volume MVP, à confirmer costing Phase 0
- Alternative si budget serré : Cross-Region Replication uniquement sur documents sensibles (SGES, RCCM, bilans), pas sur documents ordinaires

**RTO 4 h runbook** :
1. Détection incident (monitoring alerting) — 0–15 min
2. Décision restore (décideur : admin_super ou CTO) — 15–30 min
3. Restore RDS snapshot ou PITR vers RDS SANDBOX — 30 min
4. Validation smoke tests (scripts automatisés) — 30 min
5. Switch DNS/ALB vers nouvelle instance — 15 min
6. Communication incident utilisateurs — 15 min (en parallèle)
= total ~2.5 h théorique, marge jusqu'à 4 h

**Tabletop exercise trimestriel** (NFR36, mitigation RM-7).

**Implications** : configuration Terraform/CloudFormation Step 10 ; runbook `incident_response_rto_rpo.md` dans `docs/runbooks/` ; ligne budget CRR dans NFR69.

---

### Décision 10 — LLM Provider Layer avec 2 niveaux de switch

**Contexte** : NFR42, RM-6.

**Décision** : pattern Provider (Ports & Adapters) + backup provider configuré + dégradation gracieuse.

**Ajustement D10 — 2 niveaux de switch documentés** :

**Niveau 1 — Switch DÉGRADÉ (acceptable en cas d'outage critique)** :
- **Délai cible : < 2 semaines**
- Activation via env var `LLM_PROVIDER=openai|mistral`
- Code fonctionne (abstraction Provider), toutes les features opèrent
- **Qualité non garantie optimale** : prompts Claude-calibrated peuvent produire outputs moins précis sur GPT/Mistral (tics de formulation différents)
- Acceptable en situation d'urgence (outage Anthropic > 24 h)

**Niveau 2 — Switch OPTIMAL (parité qualité)** :
- **Délai réaliste : 4–6 semaines**
- Recalibrer prompts par provider (chaque modèle a ses tics — Claude verbeux + structuré, GPT plus concis mais parfois hallucine, Mistral économique mais moins cohérent sur longs contextes)
- Re-tester tous les guards LLM (hallucinations et patterns d'erreur diffèrent)
- Vérifier qualité outputs sur sample PDFs bailleurs (SGES, IFC AIMM, plan d'action)
- Re-benchmark coûts par provider (coût par 1M tokens varie 3×–10× selon provider/modèle)

**Phase 0 — tester concrètement les 3 providers backup sur les 5 tools critiques** :
1. `trigger_guided_tour` (spec 019)
2. `ask_interactive_question` (spec 018)
3. `batch_save_esg_criteria` (spec 015)
4. `generate_executive_summary` (spec 006)
5. `generate_action_plan` (spec 011)

Résultats documentés dans `docs/llm-providers/` avec comparatif qualité + coût + tics par provider.

**Intégration LangGraph** : 9 nœuds consomment `get_llm_provider()` via DI, pas d'appel direct à `langchain-openai`.

**Circuit breaker** (NFR75) sur erreurs 5xx > 10 consécutives → alerting + auto-switch vers backup.

**Dégradation gracieuse** : tous providers down → désactivation chat temporaire, maintien CRUD (endpoints non-LLM opérationnels).

**Implications** : story Phase 0 `llm-abstraction-provider-layer` ; Phase 0 inclut bench des 3 providers sur 5 tools critiques ; dashboard coût par provider + taux échec.

---

### Décision 11 — Transaction boundaries + micro-Outbox MVP

**Contexte** : CCC-14 Step 2.

**Décision** : atomicité sur opérations critiques + eventually consistent ailleurs + **micro-Outbox MVP simplifié** (vs background tasks FastAPI pures) + verrouillage optimiste + dernière-écriture-gagne avec audit.

**Opérations strictement atomiques (transaction BDD unique)** :
- `FundApplication.submit()` : snapshot + hash + signature + verdicts gelés
- `publish_referential_version_N3()` : création `referential_migrations` + enqueuing event notification
- Génération livrable complète avec `FundApplicationGenerationLog`

**Ajustement D11 — Micro-Outbox MVP simplifié** (remplace les background tasks FastAPI pures) :

```sql
CREATE TABLE domain_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,  -- ex. 'fact_updated', 'criterion_rule_updated', 'referential_published', 'admin_access_audited'
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ NULL,
  error_message TEXT NULL,
  retry_count INT DEFAULT 0,
  CONSTRAINT retry_cap CHECK (retry_count <= 5)
);

CREATE INDEX idx_domain_events_pending ON domain_events (created_at)
  WHERE processed_at IS NULL AND retry_count < 5;
```

**Worker batch** (APScheduler dans le process FastAPI MVP, à migrer vers process Celery séparé Phase Growth) :
- Exécution toutes les **30 secondes**
- Algorithme :
  1. `SELECT * FROM domain_events WHERE processed_at IS NULL AND retry_count < 5 ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED`
  2. Pour chaque event : appelle handler enregistré par `event_type` (dispatcher Python)
  3. Succès → `UPDATE processed_at = NOW()`
  4. Échec → `UPDATE retry_count += 1, error_message = <...>`
  5. Si `retry_count >= 5` → event taggé mort, alerte admin

**Handlers enregistrés (exemples)** :
- `fact_updated` → invalidation `referential_verdicts` impactés (D3)
- `criterion_rule_updated` → invalidation `referential_verdicts` + recalcul verdicts déjà persistés pour FundApplications actives (non-submitted)
- `referential_published` → notifications users impactés (FR34) + recalcul eligibility cube 4D
- `admin_access_audited` → écriture `admin_access_audit` (D7, en mode eventually consistent pour ne pas pénaliser performance queries)

**Avantages vs background tasks FastAPI pures** :
- **Durable** : survit au restart serveur (events en BDD)
- **Retryable** : handlers doivent être idempotents (convention documentée)
- **Auditable** : table events = trace complète
- **Simple** : pas Celery/Redis/SQS MVP, juste APScheduler + handlers Python
- **Coût implémentation estimé** : ~2–3 jours
- **ROI** : très élevé vs risque perte audit trail / invalidation ratée

**Pattern Outbox COMPLET (cross-service, message broker)** : reste différé Phase Growth si microservices émergent (différés Phase 5 Vision seulement, Clarif. 1).

**Verrouillage optimiste par `version_number`** : `Company`, `Project`, `Fund`, `Intermediary`, `Criterion`, `Pack` → colonne `version_number INT DEFAULT 1` + UPDATE `WHERE id = X AND version_number = N` → 409 Conflict si 0 rows.

**Dernière-écriture-gagne sur `Fact`** avec `fact_versions` audit : aucune donnée perdue (FR19 + CCC-14).

**Implications** :
- Nouvelle story Phase 0 `micro-outbox-domain-events` (PRÉREQUIS avant activation modules `projects`, `maturity`, nouveaux handlers verdicts)
- Migration dédiée `02X_create_domain_events.py` (à intercaler dans séquence Phase 0)
- Convention : tous handlers **idempotents** (si event rejoué, même résultat)
- Column `version_number` ajoutée tables listées (migrations Phase 1)

---

### Analyse d'impact des décisions

**Séquence d'implémentation révisée (ordre ajustements utilisateur intégrés) :**

**Phase 0 (prérequis bloquants)** :
1. Migration `024_enable_rls_on_sensitive_tables.py` + table `admin_access_audit` (D7)
2. Migration `025_add_source_tracking_constraints.py` (CCC-6)
3. Migration `026_create_admin_catalogue_audit_trail.py` (D6)
4. Migration `02X_create_domain_events.py` (D11 — micro-Outbox)
5. Feature flag setup `ENABLE_PROJECT_MODEL` (Clarif. 5 — env var + wrapper simple)
6. Stories Phase 0 **parallélisables** (indépendantes, à exécuter en parallèle par devs distincts pour gain temps) :
   - `llm-abstraction-provider-layer` (D10) — inclut bench 3 providers sur 5 tools critiques
   - `rag-transversal-service-partagé` (Clarif. 6) — `backend/app/rag/service.py`
   - `micro-outbox-domain-events` (D11 — worker APScheduler + handlers skeleton)
7. Autres stories Phase 0 : `guards-llm-universels` (CCC-1), `environment-isolation-pipelines` (D8), `observability-metier-tools` (CCC-3)

**Phase 1 (MVP cœur)** :
1. Migration `020_create_projects_schema.py` + activation feature flag ON (D1)
2. Migration `021_create_maturity_schema.py` (Cluster A')
3. Migration `022_create_esg_3_layers.py` (D3 + DSL borné)
4. Migration `023_create_deliverables_engine.py` (D5 + template_sections relationnelle + prompt versioning)
5. Cube 4D activation sur catalogue mi-Phase 1 (D4) — load test NFR71 déclenché ici
6. Admin catalogue workflows N1/N2/N3 UI-only (D6, Clarif. 2)
7. SGES BETA avec NO BYPASS (FR44)
8. Migration `027_cleanup_feature_flag_project_model.py` (fin Phase 1, NFR63)

**Dépendances croisées (cross-component)** :
- D1 (Project N:N) → prérequis D3, D4, D5
- D3 (ESG 3 couches) → prérequis D4 (cube consomme criteria) + D5 (livrables consomment verdicts)
- D6 (admin N1/N2/N3) → maintient D2, D3, D4, D5 (sans admin, retour hard-coding)
- D7 (RLS 4 tables) → s'applique D1 + D3 (companies, fund_applications, facts)
- D10 (LLM provider) → transverse
- D11 (transaction boundaries + micro-Outbox) → cadre D1, D3, D5 (submit atomique) + invalidation verdicts (D3) + audit admin (D7) + notifications référentiel (D3 → D2 → D6)
- `micro-outbox-domain-events` → prérequis de **tous** les handlers invalidation/notification/audit → Phase 0 obligatoire **avant** activation modules métier

**Résumé des 10 ajustements intégrés** :
- **D1** : cumul de rôles via `UNIQUE (project_id, company_id, role)`
- **D2** : résolution STRICTEST WINS + alerte UI conflit
- **D3.1** : DSL borné (4 primitives) + validation Pydantic (anti-RCE)
- **D3.2** : invalidation via micro-Outbox (D11)
- **D4** : REFRESH CONCURRENTLY à mesurer load testing Phase 0 (fallback triggers/partitioning si > 10 s)
- **D5.1** : table `template_sections` relationnelle (vs JSONB)
- **D5.2** : table `reusable_section_prompt_versions` (reproductibilité historique)
- **D6** : échantillon représentatif ≥ 50 snapshots stratifiés + seuil blocage 20 % configurable
- **D7** : `admin_access_audit` obligatoire via SQLAlchemy event listener
- **D8.1** : copie mensuelle formalisée + ad-hoc UAT
- **D8.2** : validation automatique anonymisation regex + NER (fail fast)
- **D9.1** : PITR activé arrière-plan (RPO technique 5 min, engagé MVP 24 h)
- **D9.2** : coût CRR S3 budgété NFR69
- **D10** : 2 niveaux switch (dégradé < 2 sem, optimal 4–6 sem) + bench 3 providers × 5 tools Phase 0
- **D11** : micro-Outbox MVP (table `domain_events` + worker APScheduler 30 s)

## Patterns d'implémentation et règles de consistance

### Points de conflit potentiels identifiés

**Conflits de nommage** : tables/colonnes/indexes, endpoints REST des 3 nouveaux modules, events `domain_events` vs SSE vs tools LangChain, nommage des JSONB.

**Conflits structurels** : placement state machines N1/N2/N3, placement DSL règles dérivation, placement handlers `domain_events` (registre centralisé vs par-module), organisation tests property-based Hypothesis.

**Conflits de format** : format erreur API, format dates JSON, format seuils DSL (`"<= 30"` vs `{ "operator": "<=", "value": 30 }`), format snapshot hash, format payload `domain_events`.

**Conflits de communication** : payload `domain_events` plat vs wrapper, error handling tool LLM (exception vs retour `{success:false}`), structure guards LLM errors.

**Conflits de processus** : pattern activation feature flag (env vs request), pattern invalidation cache (sync vs event-driven), pattern retry tool LLM vs retry guard LLM.

### Patterns de nommage

**BDD — tables** : `snake_case` pluriel systématique (`projects`, `fund_applications`, `facts`, `criteria`, `referential_verdicts`, `packs`, `domain_events`, `admin_access_audit`, `admin_catalogue_audit_trail`, `template_sections`, `reusable_section_prompt_versions`, `fact_versions`, `project_snapshots`, etc.). Aucun préfixe applicatif. Tables d'association M2M : nom descriptif (`criterion_referential_map`, `fund_intermediary_liaison`).

**BDD — colonnes** : `snake_case`. FK format `<singular>_id`. Timestamps `_at` (TIMESTAMPTZ) vs `_date` (DATE pur). Booléens préfixe `is_` / `has_`. Enums au singulier (`state`, `role`, `access_route`, `lifecycle_state`, `workflow_level`, `operation`, `event_type`, `value_type`, `verdict`). JSONB : suffixe `_json`/`_blob` ou nom descriptif (`payload`, `changes_before`, `facts_blob`, `pydantic_schema_json`, `derivation_rule`).

**BDD — indexes** : `idx_<table>_<columns>`. Indexes partiels : suffixe `_active` ou condition explicite. Vues matérialisées : préfixe `mv_` (`mv_fund_matching_cube`). Contraintes unique : laisser Alembic générer avec Naming Convention SQLAlchemy.

**API REST** : routes pluriel, **kebab-case** dans URLs (`/api/fund-applications/{id}/submit`, `/api/referential-migrations/{id}/publish`). `{id}` path params (standard FastAPI). Query params `snake_case` backend. Admin prefix `/api/admin/catalogue/*`. Endpoints workflow : suffixe verbe (`/submit`, `/publish`, `/reject`, `/clone`, `/restore`, `/abandon`).

**Code Python backend** : `snake_case` fonctions/variables/modules, `PascalCase` classes. Services : `<Module>Service`. Tools LangChain : `<verb>_<object>` (`query_cube_4d`, `create_fund_application`, `submit_fund_application`, `publish_referential_N3`, `record_atomic_fact`, `attest_qualitative_fact`, `derive_verdicts`, `generate_sges_beta`, `validate_maturity_via_ocr`). Pas de synonymes anarchiques.

**Code TypeScript frontend** : `camelCase` fonctions/variables, `PascalCase` composants/types. Composables `useXxx.ts`. Stores `stores/<domain>.ts`. Types `types/<domain>.ts`.

**Events `domain_events`** (D11) — **snake_case event_type au passé simple `<entity>_<verb_past>`** : `fact_updated`, `fact_version_created`, `criterion_rule_updated`, `criterion_published`, `referential_version_published`, `referential_migration_scheduled`, `referential_migration_activated`, `pack_published`, `fund_updated`, `intermediary_updated`, `fund_intermediary_liaison_updated`, `admin_access_audited`, `fund_application_submitted`, `fund_application_signed`, `formalization_plan_generated`, `maturity_level_auto_reclassified`, `pack_overlay_conflict_detected` (D2).

Payload **toujours dict plat** (pas wrapping `{data:...}`) avec clés minimales pour handlers idempotents. UUIDs en string, timestamps ISO 8601 avec TZ, pas de PII (références par ID).

**Events SSE (streaming chat) — convention cohérence passé simple (Raffinement 1)** :

> **Règle explicite** : tous les **NOUVEAUX** events (SSE et `domain_events`) utilisent le **passé simple** `<entity>_<verb_past>`. Les events SSE **existants legacy** (`token`, `tool_call_start`, `tool_call_end`, `tool_call_error`, `interactive_question`) sont **conservés tels quels** pour éviter régression, mais **ne sont pas un modèle à suivre** pour la feature 5 clusters.

Nouveaux events SSE feature 5 clusters (tous au passé) : `referential_migration_notified`, `formalization_plan_updated`, `catalogue_entity_published`, `guard_llm_failed`, `snapshot_frozen`, `fund_application_submitted`, `verdict_recalculated`, `pack_overlay_conflict_detected`.

### Patterns structurels

**Organisation des 3 nouveaux modules** :
```
backend/app/modules/projects/
├── __init__.py, router.py, service.py, schemas.py, models.py, enums.py
├── workflow.py    # State machine FundApplication status
└── events.py      # Payloads domain_events émis par ce module

backend/app/modules/maturity/
├── (même pattern)
├── ocr_validator.py
└── formalization_plan_generator.py

backend/app/modules/admin_catalogue/
├── (même pattern)
├── workflow.py              # N1/N2/N3 state machines
├── anonymization.py
└── retroactive_tester.py    # Échantillonnage représentatif D6
```

**Composants transverses** :
- `backend/app/core/feature_flags.py` (Clarif. 5)
- `backend/app/core/dsl/` (D3.1) — `parser.py`, `validator.py`, `evaluator.py`
- `backend/app/events/` (D11) — `outbox.py`, `worker.py`, `handlers/` (registre central `HANDLERS = {event_type: handler_fn}` dans `__init__.py`)
- `backend/app/llm/provider.py` (D10)
- `backend/app/rag/service.py` (Clarif. 6)
- `backend/app/security/pii_anonymizer.py` (NFR11)
- `backend/app/security/admin_access_logger.py` (D7, event listener SQLAlchemy)

**Convention nommage fichiers tests (normalisée)** :
- **Unitaires** : `test_<module>_<function_or_class>.py` (ex. `test_projects_create_membership.py`, `test_maturity_formalization_plan_generator.py`)
- **Intégration** : `test_<flow>_integration.py` (ex. `test_fund_application_submit_atomic.py`, `test_referential_migration_pipeline_integration.py`)
- **Property-based** : `test_<invariant>_property.py` (ex. `test_verdict_non_contradiction_property.py`)
- **RLS sécurité** : `test_rls_<table>.py` (ex. `test_rls_companies.py`, `test_rls_fund_applications.py`)
- **Load** : `test_load_<scenario>.py` via Locust (ex. `test_load_cube_4d_100_users.py`)
- **E2E Playwright** : `frontend/tests/e2e/<journey>.spec.ts` (ex. `aminata.spec.ts`, `moussa.spec.ts`, `akissi.spec.ts`, `ibrahim.spec.ts`, `mariam.spec.ts`)

Objectif : `grep`/`glob` permet de retrouver rapidement tous les tests d'un flow sans naviguer une arborescence confuse.

**Handlers `domain_events`** : registre centralisé `backend/app/events/handlers/__init__.py` (pas dispatch par module). Un handler peut appeler des services de plusieurs modules.

### Patterns de format

**API response** : succès = objet direct (pas wrapper `{data:...}`), pagination = `{items, total, page, limit}`, erreur FastAPI standard `{detail: ...}` 4xx/5xx, erreurs métier spécifiques `{detail: {code, message, ...}}` (ex. `version_conflict`).

**Dates JSON** : ISO 8601 avec timezone systématique. Pas d'epoch, pas de format localisé. Conversion locale en frontend au render.

**JSON fields** : snake_case conservé côté response (cohérence avec données brutes, simplicité, convention spec 001+). Types TypeScript camelCase avec mapping explicite dans composables.

**DSL seuils (D3.1)** :
```json
{ "rule_type": "threshold",
  "rule_payload": { "fact_key": "effluent.bod_mg_per_liter",
                    "operator": "<=", "value": 30, "unit": "mg/L" } }
```
Opérateurs symboliques `<=, <, >, >=, ==, !=`. Unité toujours présente pour threshold numérique. Validation Pydantic discriminator `Literal`.

**Snapshot hash** : SHA-256 hex lowercase 64 chars. Source canonique : JSON serialization `sort_keys=True, separators=(',', ':')` de `facts_blob + profile_blob + referential_versions_blob + project_lifecycle_state`, hash UTF-8 bytes. Test unitaire reproductibilité obligatoire.

**Payload `domain_events`** : dict plat JSON-serializable, UUIDs en string, timestamps ISO 8601 TZ, pas de PII.

### Patterns de communication

**Émission `domain_event`** (pattern canonique) — dans la même transaction que l'opération métier :
```python
async def update_fact(session, fact_id, new_value, user_id):
    async with session.begin():
        # ... opération métier
        await enqueue_domain_event(session, event_type="fact_updated",
                                   payload={"fact_id": str(fact.id), ...})
    # Transaction commit : l'event est durable
```

**Handler idempotent** (pattern canonique) : si rejoué, même résultat. Convention documentée en tête de chaque handler.

**Error handling tool LangChain** : toujours retourner `str` JSON-serializable. Succès `{"success": true, "result": {...}}`, erreur attendue `{"success": false, "error_code": "...", "message": "..."}`, erreur inattendue → exception Python (interceptée par `with_retry` + `log_tool_call`). **Pas de mélange** (toujours retour string avec flag `success`).

**SSE events frontend** : composable `useChat` parse et dispatche par `event.type`. Nouveaux handlers : `onReferentialMigrationNotified`, `onFormalizationPlanUpdated`, `onCatalogueEntityPublished`, `onGuardLlmFailed`, `onSnapshotFrozen`, `onFundApplicationSubmitted`, `onPackOverlayConflictDetected`. Toasters non-bloquants pour events informatifs, modals pour events bloquants.

**State management Pinia** : updates immutables, actions async `fetchXxx`/`createXxx`/`updateXxx`/`submitXxx`/`signXxx`, getters nommés par ce qu'ils retournent.

### Patterns de processus

**Invalidation cache** : event-driven via micro-Outbox (D11) — **JAMAIS** synchrone dans transaction. Lecteurs vérifient `invalidated_at`, recalcul on-demand ou batch.

**Activation feature flag** (Clarif. 5) : check env-level au boot, jamais request-level. Pattern : check dans router ou en tête de service, pas dispersé.

**Guards LLM obligatoires (CCC-1) — pattern canonique** :
```python
from app.guards import validate_llm_output
raw_output = await llm_provider.complete(prompt, schema=ExecutiveSummarySchema)
validated = validate_llm_output(
    raw_output, schema=ExecutiveSummarySchema,
    checks=[length_between(200, 2000),
            numeric_consistency_with_facts(facts),
            no_forbidden_vocabulary(["garanti", "certifié", "validé par"]),
            language_is("fr")])
```

**Retry guards LLM — seuil canonique explicite (Raffinement 2)** :

- **1ère tentative** : LLM génère, guards valident.
- **Si guard échoue** : retry **1× unique** avec prompt enrichi du feedback explicite (ex. *« Ta sortie précédente contenait le mot interdit "garanti". Reformule sans ce mot. »*).
- **Si 2ᵉ tentative échoue** : émission event `guard_llm_failed` SSE + blocage de l'opération + message utilisateur explicite *« La génération a rencontré un problème de qualité. Un consultant humain doit revoir manuellement. »*
- **JAMAIS de 3ᵉ tentative** : coût LLM disproportionné, signe de dérive prompt ou modèle défaillant.
- **Distinction retry guard VS retry tool LLM (NFR75)** :
  - **Retry tool LLM** (`with_retry`, 3× exponential backoff 1 s/3 s/9 s) : concerne échecs **techniques** (timeout, 5xx provider, rate limit 429). Appliqué au niveau infrastructure LLM.
  - **Retry guard** (1× avec feedback prompt) : concerne échecs **qualitatifs** (validation Pydantic, vocabulaire interdit, cohérence numérique, longueur). Appliqué au niveau applicatif post-output.
- **Ne pas cumuler** : un échec guard ne déclenche pas de retry tool (car le tool a techniquement réussi, seul l'output est non conforme).
- Chaque `guard_llm_failed` produit un **log structuré** avec le diff entre output LLM et contraintes violées (champ `guard_violations: [{check_name, expected, actual}]`), pour analyse de dérive prompt par `admin_mefali` (dashboard NFR74 LLM quality observability).

**Transaction atomique pour opérations critiques (D11)** : `FundApplication.submit()` = freeze snapshot + hash + verrouillage verdicts + signature + enqueue event → transaction atomique unique (`session.begin()`). Tout ou rien.

**Versioning optimiste** (D11) : UPDATE avec `WHERE version_number = expected_version` → 409 Conflict si 0 rows.

**Workflow admin N1/N2/N3** : state machine dédiée, jamais UPDATE direct de `state`. Chaque transition émet `admin_catalogue_audit_trail` row.

**Retry tool LLM** : `with_retry` existant (3 retries exp backoff), retry uniquement sur timeout/5xx/429, pas sur 400/guards fail/Pydantic fail. `log_tool_call` systématique avec `request_id`.

**Anonymisation PII avant LLM** (NFR11) : pattern pipeline `anonymize_for_llm` → LLM → `restore_tokens`. Token map request-scope mémoire (jamais persisté). `anonymized_prompts` dans `fund_application_generation_logs` pour FR57.

### Tests obligatoires `test_fund_application_submit_atomic.py` (Raffinement 3)

Ces 8 tests sont **non-négociables en Phase 1** — ils protègent le cœur de la compliance bailleur (SC-T5 snapshot immuable + signature + audit) :

1. **`submit_happy_path`** : freeze snapshot + hash + signature + verdicts figés + event → tout OK
2. **`submit_with_crash_between_steps`** : simulation crash entre steps 2-3 (exception patchée) → rollback complet, aucune donnée partielle persistée
3. **`submit_double_click_protection`** : 2 submits concurrents sur même `fund_application_id` → 1 réussit via `version_number`, l'autre reçoit `ConflictError` 409
4. **`submit_idempotency_check`** : re-trigger submit sur FundApplication déjà signed → rejet 400 (status invalide pour action)
5. **`submit_hash_reproducibility`** : même state initial → même hash calculé (déterminisme testé explicitement)
6. **`submit_event_emission`** : event `fund_application_submitted` présent dans `domain_events` après commit, payload conforme
7. **`submit_verdicts_frozen`** : après submit, modifier un fact sous-jacent → verdicts de la FundApplication restent inchangés (snapshot immuable)
8. **`submit_audit_log_created`** : `fund_application_generation_logs` row créée avec metadata complète (version LLM, prompts anonymisés, versions référentiels, hash snapshot, user ID)

### Règles d'enforcement

**Tous les contributeurs (humains + agents IA) DOIVENT** :

1. Respecter les conventions de nommage — aucune exception sans discussion + update du document.
2. Émettre un `domain_event` dans la même transaction que l'opération métier — pas d'émission post-commit via background task pure.
3. Implémenter les handlers `domain_events` comme idempotents — convention documentée en tête de chaque handler.
4. Valider toute output LLM via `validate_llm_output` avant persistence — pas d'exception, même pour du "simple texte".
5. Ajouter un test property-based Hypothesis pour toute nouvelle règle de dérivation critère/verdict (SC-T6).
6. Ajouter un test intégration cube 4D dès que les dimensions impactent un nouveau matching.
7. Ajouter un test RLS sécurité dès qu'une table sensible reçoit de nouveaux endpoints.
8. Documenter `source_url`/`source_accessed_at`/`source_version` à toute création d'entité catalogue — DRAFT non publiable sinon (NFR27).
9. Utiliser le feature flag `ENABLE_PROJECT_MODEL` sur tous endpoints/services concernés Phase 1 — supprimer via migration 027 en fin Phase 1 (NFR63).
10. Ne jamais bypass le workflow humain SGES BETA (FR44) — enforcement applicatif + log security si tentative.

**Pattern enforcement vérifié** :
- CI lint : conventions de nommage (ruff rules custom), detect-secrets, pre-commit hooks
- CI tests : coverage gates 80 % / 85 % critique (NFR60)
- Code review obligatoire (NFR76) : 1 reviewer min, 2 dont 1 senior sur code critique (guards, snapshot, signature, RLS, admin workflows)
- Architecture review checkpoint à chaque fin de phase (Phase 0, Phase 1) : vérifier que les patterns sont respectés

### Anti-patterns à éviter

**AP-1 — JSONB blob surchargé.** Stocker structure complète d'un `DocumentTemplate` dans `structure_json JSONB` (rejeté D5.1). Préférer tables relationnelles quand règles de cohérence/audit granulaires.

**AP-2 — Feature flag permanent.** Observé avec `profiling_node` (dette P1 #3). Tout flag DOIT avoir date/jalon de retrait. Alerte si > 3 mois après clôture phase (NFR63).

**AP-3 — God service / cross-tables.** Observé `dashboard/service.py` (P2 #25). Services consomment services d'autres modules, pas leurs tables directement.

**AP-4 — Eval dynamique de règles.** JAMAIS `eval()`/`exec()`/DSL permettant code Python arbitraire pour `criterion_derivation_rules` (D3.1). Risque RCE via admin compromis. DSL borné Pydantic uniquement.

**AP-5 — Background tasks FastAPI non-durables.** Pour traitements qui DOIVENT survivre au restart serveur : `domain_events` (D11) + worker APScheduler, pas `BackgroundTasks` FastAPI seul.

**AP-6 — Invalidation cache synchrone dans transaction.** Ne PAS appeler `invalidate_cache()` inline dans transaction métier. Event-driven + handler asynchrone.

**AP-7 — Copie prod brute vers staging/dev.** Interdit (D8.2, NFR73). Toujours pipeline anonymisation + validation automatique.

**AP-8 — Feature en chat sans raison.** Clarif. 2 `admin_node` rejeté. Pas de nœud LangGraph pour workflows structurellement UI.

**AP-9 — Trigger PostgreSQL pour logique métier.** Rejeté D3, D6. Logique métier en code applicatif Python, pas en trigger PG. Portabilité, testabilité, debuggabilité.

**AP-10 — Retry sur guards LLM fail.** Clarifié Raffinement 2 : retry 1× unique avec feedback enrichi, pas 3×.

**AP-11 — Hard-coding de seuils ou références catalogue.** Observé audit P1 #9. Tout seuil/facteur/référence en table BDD avec NFR-SOURCE-TRACKING. Admin N1/N2/N3 pour édition.

**AP-12 — Filtre WHERE applicatif oublié.** Même avec RLS sur 4 tables sensibles, autres tables reposent sur filtre WHERE via session scope. Tout nouveau CRUD DOIT utiliser `get_tenant_scoped_session(current_user)`, jamais session brute.

**AP-13 — Conflit d'overlay pack résolu silencieusement (Raffinement 4).**

Quand plusieurs Packs activés ont des `fund_specific_overlay_rule` différents sur le même critère (ex. IFC Bancable dit BOD ≤ 30 mg/L, RSPO Premium dit BOD ≤ 50 mg/L), le système applique silencieusement la règle plus stricte (30 mg/L).

**MAUVAIS** : l'utilisateur ne sait pas que ses 2 packs se superposent et que la règle appliquée ne vient pas du pack qu'il pense.

**BON** : l'UI expose visiblement le conflit avec :
- (a) règle retenue avec origine du pack,
- (b) règle(s) alternative(s) également applicables,
- (c) explication du choix (strictest wins — cohérent avec esprit « aller au-delà du minimum »).

**Enforcement** : service applicatif qui détecte les overlays multiples sur même critère DOIT émettre un événement `pack_overlay_conflict_detected` consommé par l'UI comme **alerte informative (pas bloquante)**. Implémentation dans `VerdictDerivationService` : lors du calcul d'un verdict, détection des multiples `fund_specific_overlay_rule` applicables → enqueue event + ajout métadata dans `referential_verdicts.justification` listant les règles évaluées.

## Structure du projet et frontières — Feature 5 clusters

_Focus brownfield : seuls les fichiers impactés par la feature sont listés. Structure existante (8 modules, 9 nœuds, ~1103 tests) conservée sauf mention explicite._

### Arborescence des fichiers nouveaux et modifiés

**Backend (`backend/`) :**

**Migrations Alembic (`alembic/versions/`)** — NOUVEAU Phase 0 + Phase 1 :
- `020_create_projects_schema.py` (D1) — `projects`, `project_memberships`, `project_role_permissions`, `fund_applications`, `project_snapshots`, `company_projections`, `beneficiary_profiles`
- `021_create_maturity_schema.py` (Cluster A') — `admin_maturity_levels`, `formalization_plans`, `admin_maturity_requirements`
- `022_create_esg_3_layers.py` (D3) — `facts`, `fact_versions`, `criteria`, `criterion_derivation_rules`, `criterion_referential_map`, `referential_verdicts`, `referentials`, `referential_versions`, `referential_migrations`, `packs`, `pack_criteria` + vue matérialisée `mv_fund_matching_cube`
- `023_create_deliverables_engine.py` (D5) — `document_templates`, `template_sections`, `reusable_sections`, `reusable_section_prompt_versions`, `atomic_blocks`, `fund_application_generation_logs`
- `024_enable_rls_on_sensitive_tables.py` (D7) — policies RLS sur `companies`/`fund_applications`/`facts`/`documents` + création `admin_access_audit`
- `025_add_source_tracking_constraints.py` (CCC-6) — colonnes `source_url`/`source_accessed_at`/`source_version` + CHECK NOT NULL pour state published
- `026_create_admin_catalogue_audit_trail.py` (D6) — table `admin_catalogue_audit_trail`
- `02X_create_domain_events.py` (D11) — table `domain_events` pour micro-Outbox (ordre à intercaler Phase 0)
- `027_cleanup_feature_flag_project_model.py` (NFR63) — retrait flag fin Phase 1

**Composants transverses (`app/`) — NOUVEAU** :
- `app/core/feature_flags.py` (Clarif. 5)
- `app/core/dsl/` (D3.1) : `parser.py`, `validator.py` (Pydantic discriminator Literal), `evaluator.py`
- `app/events/` (D11) : `outbox.py` (enqueue), `worker.py` (APScheduler 30s), `handlers/__init__.py` (registre `HANDLERS = {event_type: fn}`), handlers dédiés par event_type (`fact_updated`, `criterion_rule_updated`, `referential_version_published`, `referential_migration_activated`, `pack_published`, `admin_access_audited`, `fund_application_submitted`, `formalization_plan_generated`, `maturity_level_auto_reclassified`, `pack_overlay_conflict_detected`)
- `app/llm/provider.py` (D10) — `LLMProvider` ABC + `OpenRouterClaudeProvider` / `OpenAIProvider` / `MistralProvider` + factory
- `app/rag/service.py` (Clarif. 6) — `search_similar_chunks`, `store_document_chunks`, `citation_extractor`
- `app/security/pii_anonymizer.py` (NFR11), `app/security/admin_access_logger.py` (D7 event listener SQLAlchemy)
- `app/guards/` (CCC-1) : `validator.py` (`validate_llm_output`), `checks.py` (`length_between`, `numeric_consistency_with_facts`, `no_forbidden_vocabulary`, `language_is`)

**3 nouveaux modules métier (`app/modules/`) — NOUVEAU** :
- `projects/` (Cluster A FR1-FR10) : `router.py`, `service.py`, `schemas.py`, `models.py` (Project, ProjectMembership, ProjectRolePermission, FundApplication, ProjectSnapshot, CompanyProjection, BeneficiaryProfile), `enums.py`, `workflow.py` (FundApplicationStatus state machine), `snapshot.py` (hash SHA-256 canonique), `events.py`, `csv_import.py` (FR9)
- `maturity/` (Cluster A' FR11-FR16) : `router.py`, `service.py`, `schemas.py`, `models.py` (AdminMaturityLevel, FormalizationPlan, AdminMaturityRequirement), `ocr_validator.py`, `formalization_plan_generator.py`, `events.py`
- `admin_catalogue/` (Cluster D FR24/FR35/FR43/FR64) : `router.py`, `service.py`, `schemas.py`, `models.py` (AdminCatalogueAuditTrail, AdminAccessAudit), `workflow.py` (N1/N2/N3 state machines), `retroactive_tester.py` (D6 échantillon stratifié + métriques divergence), `source_validator.py` (FR63 CI HTTP 200), `events.py`

**Modules existants étendus** :
- `modules/esg/` (D3 refactor 3 couches) : +`verdict_derivation.py`, +`pack_overlay_resolver.py` (D2 strictest wins), +modèles Fact/Criterion/Verdict/Pack/ReferentialMigration, router étendu
- `modules/financing/` (D4 cube 4D) : +`cube_matching.py` (query_cube_4d), modèles enrichis (access_route, fund_specific_overlay_rule)
- `modules/applications/` (D5 moteur livrables) : +`deliverable_engine.py` (pyramide Template→Section→Block), +`sges_beta.py` (FR44 NO BYPASS), +`prompt_versioning.py` (D5.2), +models DocumentTemplate/TemplateSection/ReusableSection/ReusableSectionPromptVersion/AtomicBlock/FundApplicationGenerationLog
- `modules/reports/` : wrapping `validate_llm_output` sur `generate_executive_summary`
- `modules/action_plan/` : intégration FormalizationPlan reminders + ReminderType enum étendu
- `modules/carbon/` : +`batch_save_emission_entries` tool (P1 #12)
- `modules/dashboard/` : refactor God service (P2 #25) — consomme services, pas tables

**Orchestration agent (`app/graph/`) — MODIFIÉ** :
- `graph.py` : +`project_node`, +`maturity_node` (admin_node rejeté Clarif. 2)
- `nodes.py` : implémentation nouveaux nœuds ; **suppression `profiling_node`** (dette P1 #3)
- `state.py` : `active_project` + `active_module` enforcement (CCC-10)
- `tools/` : +`projects_tools.py`, +`maturity_tools.py`, +`admin_catalogue_tools.py` (exposé via REST, pas chat — Clarif. 2) ; extension `esg_tools.py`, `financing_tools.py`, `application_tools.py`, `carbon_tools.py` ; `common.py` étendu (généralisation `with_retry` + `log_tool_call` aux 9 modules — P1 #14)

**Prompts (`app/prompts/`) — MODIFIÉ (CCC-9)** :
- +`registry.py` (framework injection unifié), +`builder.py` (PromptBuilder consolide STYLE + WIDGET + GUIDED_TOUR + CONTEXT)
- +`project.py`, +`maturity.py` pour nouveaux nœuds
- Refactor prompts existants via registry

**API (`app/api/`)** : `chat.py` MODIFIÉ avec nouveaux SSE events (Raffinement 1 — passé simple)

**Tests (`backend/tests/`) — NOUVEAU organisés selon convention Step 5** :
- `test_projects/` : test_projects_create.py, test_projects_create_membership.py, test_projects_membership_cumul_roles.py (D1), test_projects_lifecycle.py, test_projects_beneficiary_import_csv.py
- `test_maturity/` : test_maturity_self_declare.py, test_maturity_ocr_validation.py, test_maturity_formalization_plan_generator.py
- `test_admin_catalogue/` : test_admin_catalogue_workflow_n1/n2/n3.py, test_admin_catalogue_retroactive_tester.py
- `test_esg/` étendu : test_esg_fact_versioning.py, test_esg_verdict_derivation.py, test_esg_pack_overlay_resolver.py (D2), test_esg_dsl_parser_validator.py (D3.1 anti-RCE), test_esg_referential_migration.py
- `test_financing/` étendu : test_financing_cube_matching.py + 5 tests backend manquants P1 #11
- `test_applications/` étendu : test_applications_deliverable_engine.py, test_applications_sges_beta_no_bypass.py (FR44), test_applications_prompt_versioning.py (D5.2)
- `integration/` (NOUVEAU) : **test_fund_application_submit_atomic.py** (8 tests Raffinement 3), test_referential_migration_pipeline_integration.py, test_cube_4d_integration.py, test_admin_access_audit_integration.py, test_domain_events_worker_integration.py
- `property/` (NOUVEAU, Hypothesis) : test_verdict_non_contradiction_property.py (SC-T6), test_snapshot_hash_determinism_property.py
- `security/` (NOUVEAU) : test_rls_companies.py, test_rls_fund_applications.py, test_rls_facts.py, test_rls_documents.py, test_admin_access_audit_obligatoire.py (D7), test_pii_anonymization.py
- `load/` (NOUVEAU, Locust) : test_load_cube_4d_100_users.py, test_load_sges_generation_10_concurrent.py, test_load_read_only_500_per_min.py
- `test_guards/` (NOUVEAU) : test_guards_validator.py, test_guards_checks.py, test_guards_retry_policy.py (Raffinement 2 — 1× retry)

**`requirements.txt` MODIFIÉ** : +Hypothesis, +detect-secrets, +boto3 (prep Phase Growth), +celery (prep), +APScheduler

**Frontend (`frontend/`) :**

**Pages (`app/pages/`) — NOUVEAU** :
- `projects/index.vue`, `projects/[id].vue`, `projects/[id]/fund-applications/index.vue`, `projects/[id]/fund-applications/[appId].vue` (inclut SignatureModal + SectionBySectionReview)
- `maturity/formalization-plan.vue`
- `admin/catalogue/index.vue` (hub), `admin/catalogue/funds/[id].vue` (N1), `admin/catalogue/intermediaries/[id].vue` (N1), `admin/catalogue/criteria/[id].vue` (N2), `admin/catalogue/packs/[id].vue` (N2), `admin/catalogue/referentials/[id]/migrate.vue` (N3 + RetroactiveTestReport), `admin/catalogue/templates/[id].vue` (N2), `admin/catalogue/audit-trail.vue`

**Composants (`app/components/`) — NOUVEAU** :
- `projects/` : ProjectCard, ProjectMembershipEditor (cumul rôles D1), FundApplicationStatusBadge, ProjectLifecycleStepper
- `maturity/` : MaturityLevelBadge, FormalizationPlanTimeline, BeneficiaryProfileEditor
- `esg/` : FactEntryForm, QualitativeAttestationUploader, ReferentialVerdictTable, PackActivationPanel, **PackOverlayConflictAlert** (AP-13 UI)
- `financing/` : CubeMatchResults, AccessRoutePanel, IntermediaryPrerequisitesCard
- `applications/` : DeliverableGenerator, **SgesBetaReviewWorkflow** (FR44 NO BYPASS), SignatureModal (FR40), SectionBySectionReview (FR41 > 50k USD)
- `admin/` : CatalogueEntityCard, WorkflowN1Editor, WorkflowN2PeerReview, WorkflowN3Migration, RetroactiveTestReport (D6), AuditTrailViewer
- `common/` : GuardLlmFailedToast (SSE event)

**Composables** : useProjects.ts, useMaturity.ts, useFormalizationPlan.ts, useCubeMatching.ts, useVerdicts.ts, usePackActivation.ts, useDeliverables.ts, useAdminCatalogue.ts ; **useChat.ts MODIFIÉ** avec nouveaux SSE handlers (onReferentialMigrationNotified, onFormalizationPlanUpdated, onCatalogueEntityPublished, onGuardLlmFailed, onSnapshotFrozen, onFundApplicationSubmitted, onPackOverlayConflictDetected)

**Stores Pinia** : stores/projects.ts, stores/maturity.ts, stores/adminCatalogue.ts, stores/verdicts.ts

**Types** : types/projects.ts, types/maturity.ts, types/esg.ts (Fact/Criterion/Verdict/Pack), types/financing.ts modifié (CubeMatchResult, AccessRoute), types/admin.ts

**i18n** : `i18n.config.ts` (Clarif. 6 `@nuxtjs/i18n`) + `nuxt.config.ts` modifié (+module) + `package.json` (+`@nuxtjs/i18n`)

**Tests E2E (`frontend/tests/e2e/`) — NOUVEAU** : aminata.spec.ts, moussa.spec.ts, akissi.spec.ts (SGES BETA), ibrahim.spec.ts (remédiation), mariam.spec.ts (admin catalogue)

**Documentation (`docs/`) — MÀJ/NOUVEAU** :
- `docs/architecture-backend.md` + `architecture-frontend.md` + `data-models-backend.md` + `integration-architecture.md` : MÀJ post-Phase 0/1
- `docs/llm-providers/` NOUVEAU (D10 bench Phase 0) : claude-anthropic.md, openai-gpt.md, mistral.md
- `docs/runbooks/` NOUVEAU (D9) : incident_response_rto_rpo.md, outage_llm_provider_switch.md, data_residency_migration.md, staging_anonymized_copy_monthly.md

**Infrastructure (`infra/`) — NOUVEAU (détails Step 10)** : terraform/ (AWS ECS Fargate + RDS EU-West-3 + S3 CRR), runbooks/

### Frontières architecturales

**Frontières API (externes) :**
- **PME-facing** : `/api/projects/*`, `/api/fund-applications/*`, `/api/facts/*`, `/api/maturity/*`, `/api/formalization-plans/*`, `/api/financing/match-cube`, `/api/applications/*`, `/api/chat` (SSE), `/api/documents/*`, `/api/dashboard/*`, `/api/action-plan/*`
- **Admin-facing** (préfixe `/api/admin/`, rôles `admin_mefali`/`admin_super` + MFA obligatoire) : `/api/admin/catalogue/*`, `/api/admin/monitoring/*`, `/api/admin/audit-trail/*`, `/api/admin/users/*`
- **Webhooks / callbacks externes** : aucun MVP (APIs bailleurs différées Vision)

**Frontières internes entre modules (monolithe modulaire Clarif. 1)** :
- Un module **consomme** les services d'autres modules via import Python, **jamais** leurs tables directement (AP-3 anti God service)
- Ex. `applications.service` importe `esg.service.get_active_verdicts()`, `projects.service.get_fund_application()`, `maturity.service.get_level()` — pas de SQL cross-module
- Émissions `domain_events` (D11) pour intégrations async cross-module (ex. `pack_published` → invalide cache cube matching)

**Frontière LangGraph ↔ modules métier** : tools `graph/tools/<module>_tools.py` sont des **façades minces** qui appellent `modules.<module>.service` — pas de logique métier dans les tools. État LangGraph contient `active_project` + `active_module` propagés via `config["configurable"]`. Pas d'accès direct aux models ORM depuis les tools.

**Frontière authentification / autorisation** : middleware JWT FastAPI injecte `current_user` + role dans chaque request. `get_tenant_scoped_session(current_user)` : session SQLAlchemy configurée avec `current_setting('app.current_user_id')` pour RLS + filtre WHERE applicatif. Admin catalogue : vérif rôle + step-up MFA via `require_mfa_step_up(['admin_mefali', 'admin_super'])` au niveau router.

**Frontière données (bounded contexts)** :
- **Company-scoped** : toutes données métier (Projects, FundApplications, Facts, Documents) ont FK `company_id` + RLS ou filtre WHERE applicatif
- **Catalogue commun (read-only users, write admin_mefali)** : Funds, Intermediaries, Referentials, Criteria, Packs, DocumentTemplates — partagés lecture à tous via service layer
- **Audit trails (write-only services + read admin_super)** : `admin_catalogue_audit_trail`, `admin_access_audit`, `fund_application_generation_logs`, `domain_events` — rétention 5–10 ans (NFR20)

**Frontière synchrone vs asynchrone** :
- **Synchrone** (transaction unique atomique) : `FundApplication.submit()`, `publish_referential_version_N3()`, génération livrable avec log, update fact avec versioning optimiste
- **Asynchrone** (via `domain_events` + worker APScheduler 30 s) : invalidation verdicts post-fact-update, notifications utilisateurs post-migration référentiel, audit trail admin access, recalcul batch vue matérialisée cube
- **Frontière explicite** : tout ce qui est nécessaire à la cohérence immédiate du user-facing commit = atomique ; tout ce qui tolère délai 30 s–quelques minutes = event-driven

### Mapping exigences → fichiers (pattern Annexe H PRD)

| FR | Module / Fichiers clés | Migration |
|---|---|---|
| **FR1-FR10** Company & Project | `modules/projects/{router,service,models,workflow}.py` ; `frontend/pages/projects/*` | 020 |
| **FR11-FR16** Maturité admin | `modules/maturity/{router,service,models,ocr_validator,formalization_plan_generator}.py` ; `frontend/pages/maturity/*` | 021 |
| **FR17-FR26** ESG 3 couches | `modules/esg/{router,service,verdict_derivation,pack_overlay_resolver}.py` ; `core/dsl/*` ; `frontend/components/esg/*` | 022 |
| **FR27-FR35** Cube 4D | `modules/financing/{cube_matching,service}.py` ; `frontend/components/financing/{CubeMatchResults,AccessRoutePanel,IntermediaryPrerequisitesCard}.vue` | 022 (vue matérialisée) |
| **FR36-FR44** Moteur livrables | `modules/applications/{deliverable_engine,sges_beta,prompt_versioning}.py` ; `frontend/components/applications/*` | 023 |
| **FR44** SGES BETA NO BYPASS | `modules/applications/sges_beta.py` (fonction `ensure_not_bypass()`) + `test_applications_sges_beta_no_bypass.py` | 023 |
| **FR45-FR50** Copilot | `graph/{graph,nodes,state}.py` ; `graph/tools/*_tools.py` ; `api/chat.py` ; `frontend/composables/useChat.ts` | — |
| **FR51-FR56** Dashboard | `modules/dashboard/service.py` (refactor God P2 #25) ; `frontend/pages/dashboard/*` | — |
| **FR57** `FundApplicationGenerationLog` | `modules/applications/{models,deliverable_engine}.py` | 023 |
| **FR58** Anonymisation PII | `security/pii_anonymizer.py` (transverse) | — |
| **FR59** RLS 4 tables | `alembic/versions/024_enable_rls_on_sensitive_tables.py` + policies SQL | 024 |
| **FR60** Chiffrement at rest KMS | Config AWS RDS + S3 (infra/terraform Step 10) | — |
| **FR61** MFA + step-up | `security/mfa.py` + middleware FastAPI | — |
| **FR62-FR63** NFR-SOURCE-TRACKING + CI HTTP 200 | `modules/admin_catalogue/source_validator.py` + `.github/workflows/ci-source-url-check.yml` | 025 |
| **FR64** Audit trail catalogue 5 ans | `modules/admin_catalogue/models.py` (AdminCatalogueAuditTrail) | 026 |
| **FR65-FR66** Right erasure + portability | `modules/users/service.py` (existant étendu) | — |
| **FR67** Auditor token expirable | `modules/users/service.py` + middleware JWT scoped | — |
| **FR68** Password reset / admin force | `modules/auth/service.py` (existant étendu) | — |
| **FR69** Audit trail accès sensibles | `security/admin_access_logger.py` (event listener) + `admin_access_audit` | 024 |
| **FR70-FR71** RAG transversal + citations | `rag/service.py` (service partagé Clarif. 6) — import par 8 modules | — |
| **NFR-SOURCE-TRACKING** | `modules/admin_catalogue/source_validator.py` + CHECK constraints | 025 |
| **NFR-ADMIN-LEVELS** N1/N2/N3 | `modules/admin_catalogue/workflow.py` state machines | — |
| **Dettes P1 audit** | Voir Annexe H PRD ; mapping par story Phase 0 | — |

### Flux de données — 5 parcours guidés

**Flux 1 — Soumission `FundApplication` (opération atomique critique)** :
```
UI (frontend/pages/projects/[id]/fund-applications/[appId].vue) + SignatureModal
  → POST /api/fund-applications/{id}/submit
  → modules/projects/router.py → ProjectService.submit_fund_application() [session.begin()]
    ├─ freeze snapshot (snapshot.py canonical SHA-256)
    ├─ copy active verdicts → fa-specific verdicts (immuable)
    ├─ create FundApplicationGenerationLog (metadata complète)
    ├─ set signed_at + version_number++
    ├─ enqueue_domain_event("fund_application_submitted", payload)
  [COMMIT atomique]
  → SSE event fund_application_submitted → frontend
  → Worker APScheduler 30s traite event :
    ├─ handler notifie admin observability dashboard (NFR74)
    └─ update métriques submitted count
  → Frontend : store updated → toast success + redirection détail
```

**Flux 2 — Publication `ReferentialMigration` N3 (cascade asynchrone)** :
```
UI admin (/admin/catalogue/referentials/[id]/migrate.vue)
  → N3Workflow : draft → pending_review → tested_retroactively → scheduled_migration
  → Test rétroactif (retroactive_tester.py) :
    ├─ sélection échantillon stratifié ≥ 50 snapshots
    ├─ recalcul verdicts avec nouvelle version
    ├─ métriques divergence, bloque si > 20% (seuil configurable)
  → Scheduled à effective_date → admin confirme publish
  → AdminCatalogueService.publish_referential_migration() [session.begin()]
    ├─ create referential_migrations row
    ├─ update referential_versions.state = 'published'
    ├─ create admin_catalogue_audit_trail row
    ├─ enqueue "referential_version_published" event
  [COMMIT]
  → Worker traite event :
    ├─ identifie users impactés (FundApplications actives non-soumises)
    ├─ émet SSE referential_migration_notified
    ├─ refresh mv_fund_matching_cube CONCURRENTLY
    └─ invalide verdicts cachés dépendants (chain fact_updated events)
  → Users : toast in-app « RSPO 2024 v4.0 — migrer mon dossier ? »
```

**Flux 3 — Query cube 4D (lecture performante)** :
```
UI (CubeMatchResults.vue)
  → GET /api/financing/match-cube?project_id=X
  → useCubeMatching.ts composable → router financing
  → CubeMatchingService.query_cube_4d()
    ├─ check cache LRU in-process (clé = hash(company, project, active_packs))
    ├─ miss : SELECT from mv_fund_matching_cube JOIN ... WHERE dimensions
    ├─ apply pack_overlay_resolver (AP-13 → si conflit, enqueue event)
    ├─ cache LRU 5 min
  → Return funds[] + access_routes[] + intermediary_prerequisites[]
  → Frontend : + éventuel PackOverlayConflictAlert.vue si SSE event reçu
```

**Flux 4 — Saisie `Fact` + invalidation verdicts (async event-driven)** :
```
UI (FactEntryForm.vue) ou chat tool (record_atomic_fact)
  → POST /api/facts → FactService.create_or_update_fact() [session.begin()]
    ├─ insert/update fact + fact_versions audit
    ├─ enqueue "fact_updated" event
  [COMMIT]
  → Worker 30s : handler fact_updated
    ├─ identifie referential_verdicts dépendant de ce fact
    ├─ UPDATE invalidated_at = NOW() sur verdicts impactés
    ├─ si FundApplication snapshot_frozen utilise ce fact → verdicts gelés restent intacts
  → Prochain lecture verdict : recalcul lazy depuis criteria rules
```

**Flux 5 — Admin escape RLS (audit systématique)** :
```
Admin Mefali accède à une company quelconque (support, debug, audit)
  → SQL query via get_tenant_scoped_session(admin_user)
  → RLS policy permet accès (current_setting('app.user_role') IN admin roles)
  → SQLAlchemy event listener before_flush/before_execute :
    ├─ détecte current_user_role admin
    ├─ INSERT dans admin_access_audit (table_accessed, operation, record_ids, request_id, ...)
  → Rétention 5 ans, UI admin_super pour audit a posteriori (FR64, D7)
```

## Résultats de validation architecturale

### Validation de cohérence ✅

**Compatibilité des décisions** : stack Python 3.12 + FastAPI + SQLAlchemy async + LangChain ≥ 0.3.0 + Alembic + Pydantic v2 + Nuxt 4 + Vue 3 + Pinia + TypeScript 5.x strict cohérente. D1-D11 compatibles entre elles (D1↔D7 RLS fund_applications, D3↔D11 invalidation verdicts via micro-Outbox, D4↔D2 cube 4D avec Pack par fonds, D5.2↔FR57 prompt_version référencé, D6↔D11 transitions émettent events, D8.2↔D9 CRR validé, D10 DI compatible tous modules, D11 cadre D1/D3/D5/D6/D7). 6 Clarifications Step 3 renforcent les décisions (Clarif. 1 monolithe ↔ D11 pas Outbox complet ; Clarif. 2 admin_node rejeté ↔ D6 workflows UI ; Clarif. 5 feature flag simple ↔ D1 cleanup obligatoire ; Clarif. 6 RAG service partagé ↔ CCC-8).

**Consistance patterns** : nommage BDD (snake_case pluriel) + events (passé simple Raffinement 1) + anti-patterns (AP-1 à AP-13) + convention tests (`test_<module>_<function>` / `<flow>_integration` / `<invariant>_property` / `rls_<table>` / `load_<scenario>`) — alignés uniformément.

**Alignement structure** : 3 nouveaux modules suivent le pattern existant `modules/<domain>/{router,service,schemas,models}.py`. Composants transverses (`core/`, `events/`, `llm/`, `rag/`, `security/`, `guards/`) à la racine `app/`. LangGraph étendu à 11 nœuds sans casser l'orchestration existante.

### Validation de couverture des exigences ✅

**71 FR couverts architecturalement à 100 %** :
| Zone | FRs | Couverture |
|---|---|---|
| Company & Project (FR1-FR10) | 10/10 | D1 + migration 020 + module `projects/` |
| Maturité (FR11-FR16) | 6/6 | Module `maturity/` + migration 021 + OCR validator + FormalizationPlan generator |
| ESG 3 couches (FR17-FR26) | 10/10 | D3 + DSL borné + migration 022 |
| Cube 4D (FR27-FR35) | 9/9 | D4 + D2 (Pack par fonds) |
| Livrables (FR36-FR44) | 9/9 | D5 + FR44 NO BYPASS applicatif + tests dédiés |
| Copilot (FR45-FR50) | 6/6 | LangGraph 11 nœuds + ToolNode + MemorySaver |
| Dashboard (FR51-FR56) | 6/6 | Refactor God service P2 #25 |
| Audit/Compliance/Security (FR57-FR69) | 13/13 | FR57-59 migrations 023-024, FR62-63 source_validator + CI, FR64 AdminCatalogueAuditTrail 026, FR69 admin_access_audit D7 |
| RAG (FR70-FR71) | 2/2 | Clarif. 6 service partagé |

**76 NFR couverts à 100 %** — validation par catégorie (Performance/Sécurité/Privacy/DR/Observabilité/Intégration/Scalabilité/Accessibilité/Maintenabilité/i18n/Budget/DevOps) : toutes NFR ont une décision architecturale ou pattern associé. NFR24 (data residency AWS EU-West-3) tranché, NFR42 (LLM Provider abstraction D10 avec 2 niveaux switch), NFR71 (load testing scénarios explicites).

**10 QO PRD Annexe E traitées** : 3 tranchées architecturalement (A1 Project sans Company → non, A4 versioning via snapshots, B4 dernière-écriture-gagne via D11), 4 différées pilote (A'1, A'3, A'4, A'5), 3 différées Epic breakdown (A5 clonage, B3 scoring partiel, C2 import gabarits non officiels). **Aucune QO ne bloque l'implémentation MVP.**

### Analyse des lacunes

**Gaps critiques : aucun.**

**Gaps importants (tracés vers sprints cibles)** :
- **G-1** Costing infra détaillé → raffiner post-Phase 0 avec volumétrie réelle + bench LLM + ligne CRR S3
- **G-2** Seuils configurables (migration N3 20 %, circuit breaker LLM 10 échecs, budget LLM) → admin UI Phase 0
- **G-3** Runbooks opérationnels (`incident_response_rto_rpo.md`, `outage_llm_provider_switch.md`, `data_residency_migration.md`, `staging_anonymized_copy_monthly.md`) → rédaction Phase 0
- **G-4** Pydantic schemas guards LLM par type de livrable → story `guards-llm-universels` Phase 0
- **G-5** DSL vocabulary gouvernance → process N2 peer review + architect

**Gaps nice-to-have (non bloquants) : G-6 à G-9** documentés (tics LLM providers, exemples guards, migration Redis Growth, formalisation Outbox complet si microservices émergent).

**Gaps adressés par artefacts BMAD downstream** : UX design doc (5 journeys + signature + admin N1/N2/N3 + 11 blocs), epics/stories breakdown (13 stories Phase 0 Annexe H + checklist CQ-1..14).

### Checklist de complétude architecturale

**✅ Requirements Analysis (Step 2)** — 71 FR + 76 NFR + 5 journeys + 9 annexes analysés, scale high-to-enterprise, contraintes Annexe I, 14 CCC cross-cutting identifiés.

**✅ Architectural Decisions (Step 4)** — 11 critical decisions (D1-D11) avec rationale + implications + cascade ; stack brownfield formalisée Step 3 ; 6 clarifications + 10 ajustements intégrés.

**✅ Implementation Patterns (Step 5)** — conventions nommage (BDD/API/Python/TS/events/SSE passé simple) + 12 patterns + 13 anti-patterns + 10 règles enforcement + convention tests normalisée + 4 raffinements.

**✅ Project Structure (Step 6)** — arborescence brownfield nouveaux/modifiés, frontières API/internes/LangGraph/auth/bounded contexts/sync-vs-async, mapping FR → fichiers → migrations, 5 flux de données explicites.

### Évaluation de préparation

**Statut : READY FOR IMPLEMENTATION ✅**

**Niveau de confiance : ÉLEVÉ**

**Rationale niveau élevé** : PRD extensif traçable et testable, 11 décisions + 6 clarifications + 10 ajustements + 4 raffinements = **20+ points de précision** par itération utilisateur, architecture brownfield-aware (Annexe I), 14 CCC + 12 patterns + 13 anti-patterns + 10 règles = guidance AI agents exhaustive, zero gap critique, 10 QO PRD traitées.

**Points forts remarquables** : (1) Brownfield discipline, (2) Compliance IA production-grade bout-en-bout Risque 10, (3) Performance pragmatique sans Redis MVP, (4) Sécurité défense en profondeur, (5) Traçabilité exemplaire FR→fichiers→migrations, (6) Extensibilité catalogue data-driven RM-3 mitigation, (7) Simplicité calibrée (pas microservices/Kubernetes/Outbox/Redis MVP), (8) Durabilité asynchrone via micro-Outbox sans Celery prématuré.

**Aires d'amélioration future (post-MVP, non bloquantes)** : Pattern Outbox complet Phase 5 si microservices, RLS complet Phase Growth, Redis tiède Phase Growth, HNSW > 100 k embeddings, Celery queue asynchrone, Marketplace consultant Vision, APIs bailleurs Vision, Extension Chrome Phase 4.

### Handoff d'implémentation

**Guidelines agents IA (humains + AI)** :
- Suivre strictement les 11 décisions + 6 clarifications + 10 ajustements + 4 raffinements
- Utiliser uniformément les 12 patterns Step 5 (domain_events dans transaction, handlers idempotents, validate_llm_output avant persistence, anonymisation PII, versioning optimiste)
- Éviter systématiquement les 13 anti-patterns
- Respecter la structure Step 6 (3 nouveaux modules + composants transverses + convention tests)
- Référencer ce document pour toute question architecturale

**Priorité première — Phase 0 stories (séquence révisée)** :

**1. Migrations transverses séquentielles** : `024_enable_rls_on_sensitive_tables.py` + `admin_access_audit` (D7) → `025_add_source_tracking_constraints.py` (CCC-6) → `026_create_admin_catalogue_audit_trail.py` (D6) → `02X_create_domain_events.py` (D11) → feature flag setup (Clarif. 5).

**2. Stories Phase 0 parallélisables (gain temps, devs distincts)** :
- `llm-abstraction-provider-layer` (D10) — inclut bench 3 providers × 5 tools critiques
- `rag-transversal-service-partagé` (Clarif. 6)
- **`micro-outbox-domain-events` (D11 NOUVELLE — prérequis bloquant avant Phase 1)**
- `guards-llm-universels` (CCC-1, recoupe story 9.6 en cours cohérent)
- `environment-isolation-pipelines` (D8)
- `observability-metier-tools` (CCC-3)

**3. Autres stories Phase 0 obligatoires (Annexe H PRD)** :
- `admin-catalogue-crud` (admin N1/N2/N3 base)
- `catalog-sourcing-documentaire` (7ème prérequis bloquant PRD)
- `anonymisation-pii-llm` (NFR11)
- `snapshot-systematique` (SC-T5)
- `enforcement-context-actif` (CCC-10)
- `registre-blocs-visuels` (CCC-11)
- `ci-nightly-source-url-check` (FR63)
- `rag-transversal-8-modules` (étendre)

**4. Re-validation obligatoire fin Phase 0 (T+6 semaines)** :
- Load testing NFR71 scénarios (100 users 30 min, 10 SGES simultanés, 500 read/min)
- Mesure REFRESH CONCURRENTLY `mv_fund_matching_cube` (D4 — si > 10 s, plan B triggers/partitionnement)
- Bench 3 LLM providers × 5 tools critiques (D10, `docs/llm-providers/` rédigés)
- Vélocité équipe → affinage fourchette Phase 1 (PRD ligne 941)
- Zero failing tests on main (NFR59) vérifié
- 14 dettes P1 audit résolues ou documentées (SC-T1)

**Phase 1 (MVP cœur) démarre après Phase 0 + re-validation réussie.**
