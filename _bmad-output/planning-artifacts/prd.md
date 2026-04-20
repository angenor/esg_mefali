---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
completedAt: '2026-04-18'
lastModified: '2026-04-18'
annexesCount: 9
status: 'complete'
classification:
  projectType: 'web_app'
  domain: 'fintech'
  subDomain: 'sustainability_esg'
  complexity: 'high'
  projectContext: 'brownfield'
  secondaryModalities:
    - 'saas_b2b'  # multi-tenant, quotas par user, facturation future
    - 'copilot_ia_first'  # toute feature doit être invocable depuis le chat
    - 'consulting_augmented_by_ai'  # guards LLM critiques pour documents persistés remis aux bailleurs
inputDocuments:
  - _bmad-output/brainstorming/brainstorming-session-2026-04-18-1414.md
  - _bmad-output/implementation-artifacts/spec-audits/index.md
  - _bmad-output/planning-artifacts/product-brief-esg-mefali-copilot.md
  - _bmad-output/planning-artifacts/architecture-019-floating-copilot.md
  - _bmad-output/planning-artifacts/epics-019-floating-copilot.md
  - _bmad-output/planning-artifacts/prd-019-floating-copilot.md
  - CLAUDE.md
  - docs/project-overview.md
  - docs/architecture-backend.md
  - docs/architecture-frontend.md
  - docs/integration-architecture.md
workflowType: 'prd'
documentCounts:
  briefCount: 1
  researchCount: 0
  brainstormingCount: 1
  projectDocsCount: 8
---

# Product Requirements Document — ESG Mefali Extension

**Auteur :** Angenor
**Date :** 2026-04-18
**Basé sur :** brainstorming-session-2026-04-18-1414 (5 clusters + 1 abstraction centrale)

## Executive Summary

ESG Mefali est une plateforme conversationnelle IA web (accessible ordinateur et mobile) qui démocratise l'accès à la finance durable pour les PME francophones d'Afrique de l'Ouest (zone UEMOA/CEDEAO). Elle traduit les standards internationaux de finance verte — IFC Performance Standards, GCF, BAD, BOAD, EUDR, GRI, RSPO, ISO 14001/45001/26000/37001 — en exigences opérationnelles concrètes, accessibles à une PME à moins de 5 M XOF de chiffre d'affaires, sans recours à un consultant ESG à 50–200 k€.

**Le problème profond :** plusieurs milliards USD de financement vert sont pré-alloués à la région par GCF, FEM, BAD, BOAD, IFC, Proparco, mais moins de 20 % des PME ouest-africaines ont accès au crédit formel, et les consultants ESG qui feraient le pont restent économiquement inaccessibles. L'asymétrie d'information et le coût de l'accompagnement bloquent donc le capital à la source. Les solutions ESG existantes, conçues pour le contexte européen, ignorent en outre la **voie d'accès concrète** (directe vs intermédiée) propre à chaque fonds — elles suggèrent des financements théoriquement compatibles mais pratiquement inaccessibles, détruisant la confiance utilisateur.

**Cette extension PRD** fait passer ESG Mefali d'un produit validé (8 modules métier, 18 specs livrées, ~1100 tests verts — baseline restaurée le 17 avril 2026 par la story 9.3 après mise en place du principe *zero failing tests on main*) à une profondeur métier alignée avec la réalité du consultant ESG ouest-africain. Elle réarchitecture cinq axes critiques identifiés lors du brainstorming du 18 avril 2026 :

1. **Unité d'analyse projet ou entreprise** — modèle N:N `Company × Project` avec cycle de vie (idée → faisabilité → bancable → exécution → achevé) et snapshot propre à chaque soumission.
2. **Maturité entreprise graduée** — parcours 4 niveaux (informel → RCCM+NIF → comptes+CNPS → OHADA audité) comme pré-requis d'adoption pour ~80 % du marché cible (PME informelles). Positionnée en Phase 1 MVP.
3. **ESG multi-contextuel** — architecture à trois couches (Faits atomiques → Critères composables → Verdicts par référentiel). Une saisie unique des faits produit automatiquement les verdicts pour N référentiels (IFC, GRI, RSPO…).
4. **Moteur de livrables multi-destinataires** — génération automatique de dossiers conformes bailleurs (GCF, IFC AIMM), clients export (EUDR DDS, SMETA), régulateurs (EIES locales), investisseurs (GRI, TCFD).
5. **UX enrichie et contextuelle** — registre de blocs visuels extensibles, mode low-data, PWA offline, parcours pédagogiques IA par rôle.

**Scope régional :** le PRD cible exclusivement l'Afrique de l'Ouest francophone UEMOA/CEDEAO. L'architecture est conçue i18n-compatible (pas de hardcoding `lang='fra'`, messages extractibles, schémas sans présupposé UEMOA) pour supporter une expansion ultérieure vers l'Afrique anglophone (Ghana, Nigeria, Liberia, Sierra Leone) puis continentale — horizon stratégique non engagé, pas de date.

**Exploitation de la base existante :** ce PRD ne construit pas from scratch. Il élève une base opérationnelle validée : le module financement (spec 008) dispose déjà de 12 fonds, 14 intermédiaires, ~50 liaisons fund-intermediary, et d'un workflow fiche préparation PDF. La voie d'accès est donc partiellement modélisée — ce PRD en fait une dimension centrale du cube de qualification bailleur. C'est un **refactor d'élévation, pas un greenfield**, ce qui réduit significativement le risque de livraison.

### What Makes This Special

Le différenciateur primaire est le **Cube de qualification bailleur à quatre dimensions** — maturité projet × maturité entreprise × référentiels × voie d'accès — qui n'affiche à l'utilisateur que les financements **réellement accessibles** avec le **parcours concret** d'accès : dossier direct au fonds, ou identification de l'intermédiaire agréé à contacter avec ses prérequis spécifiques. La voie d'accès modélise explicitement que chaque fonds impose son propre canal (GCF via BOAD/BAD, FEM via PNUD, SUNREF via banques partenaires, BOAD Ligne Verte via SIB/Ecobank/BDU, ou directement pour FNDE et certains guichets BAD). Les critères de l'intermédiaire s'ajoutent à ceux du fonds — Mefali les expose tous les deux.

Le différenciateur structurel suivant est l'**architecture ESG à trois couches (Faits → Critères composables → Verdicts par référentiel)** : une seule saisie utilisateur produit automatiquement, par règles de dérivation, les verdicts IFC Performance Standards, GRI Standards, RSPO, ISO 14001, TCFD, EUDR, etc. Zéro double saisie, cohérence absolue entre référentiels, traçabilité auditable de chaque score.

**Core insight :** la fonction du consultant ESG ouest-africain — *interface entre les standards internationaux et la réalité opérationnelle locale, et identification de la voie d'accès réelle pour chaque financement* — est automatisable par IA conversationnelle. Mefali n'est pas une grille de scoring ESG de plus ; c'est l'automatisation du rôle consultant AO, calibrée sur la spécificité régionale (secteurs dominants agroalimentaire 60–70 % des PME, filières export cacao/palme/coton, bailleurs effectivement actifs dans la zone, droit OHADA, régimes sociaux par pays).

**Différenciateurs secondaires :**
- Accompagnement à la formalisation graduée (informel → OHADA audité) — **pré-requis d'adoption pour 80 % du marché cible**, intégré en Phase 1 MVP.
- Contextualisation AO intrinsèque (zone agroécologique, pays OHADA, benchmarks BCEAO, facteurs d'émission réseau électrique local, codes environnementaux ANDE/DEEC/BUNEE).
- Copilot IA-first — toute feature est invocable depuis le chat LangGraph, jamais uniquement derrière un menu.
- Positionnement assumé : **premier outil opérationnel aligné** avec l'AFAC Continental Sustainable Finance Taxonomy (BAD), **validée juillet 2025 à Nairobi** et en déploiement opérationnel. Plus besoin d'anticiper une publication future — le cadre est opérationnel, Mefali s'y aligne en Phase 2 catalog sourcing. Positionnement institutionnel (référence régulateur/académique) non ambitionné à ce stade — ouvre la place à un partenariat futur avec la BAD/AFAC.

**Pourquoi maintenant :** convergence de cinq vecteurs — (1) capacité des LLM francophones à tenir une conversation ESG technique en français académique africain (tipping point 2024–2025), (2) entrée en vigueur du règlement européen EUDR (2026–2027) qui force les PME cacao/palme/bois à se conformer sous peine de perdre le marché EU, (3) taxonomie africaine BAD en structuration laissant une fenêtre pour devenir l'outil opérationnel de référence régional, (4) maturité du stack agentique (LangGraph, pgvector, tool calling stable) qui rend viable une architecture d'agent production-ready impensable il y a 18 mois, (5) base produit déjà validée par 18 specs livrées.

## Project Classification

| Dimension | Valeur |
|---|---|
| **Project Type** | `web_app` — Nuxt 4 frontend + FastAPI backend, API REST, streaming SSE |
| **Domain** | `fintech` avec spécialisation `sustainability_esg` (finance verte, scoring crédit alternatif, compliance multi-référentiel) |
| **Modalités secondaires** | SaaS B2B multi-tenant (quotas par user, facturation future) · Copilot IA-first (toute feature invocable depuis le chat) · Consulting augmenté par IA (guards LLM critiques pour documents persistés remis aux bailleurs) |
| **Complexity** | `high` — LangGraph 9–10 nœuds + 100+ tools LangChain, RAG pgvector, architecture 3 couches ESG, compliance multi-bailleurs, public cible hétérogène du secteur informel à la PME OHADA audité, extension brownfield sur base existante |
| **Project Context** | `brownfield` — 18 specs implémentées, 8 modules métier opérationnels, ~1100 tests verts (baseline restaurée le 17 avril 2026 par la story 9.3 après mise en place du principe *zero failing tests on main*). Extension = réarchitecture majeure (Company×Project N:N + ESG multi-référentiel + cube bailleur 4D) avec **14 dettes P1 identifiées par l'audit 18-specs du 16 avril 2026** (4 résolues à date : rate limiting chat, quota stockage, OCR bilingue, flag édition manuelle ; 10 à ouvrir) |
| **Scope régional** | AO francophone UEMOA/CEDEAO uniquement. Architecture i18n-compatible pour expansion anglophone et continentale non engagée |

## Success Criteria

### User Success

Le produit est considéré comme un succès utilisateur quand, sans expertise ESG préalable et sans accompagnement humain rémunéré :

- **SC-U1 — Découvrabilité des financements** : une PME ouest-africaine identifie, en moins de 30 minutes de chat, au moins 3 fonds pour lesquels elle est réellement éligible (dimension « voie d'accès » prise en compte : direct OU via intermédiaire identifié). Le moment « aha! » : « je ne savais pas que ce fonds existait ET que je pouvais y postuler ».
- **SC-U2 — Génération de livrables bailleurs** : une PME produit, à partir d'une saisie guidée de 2 à 4 heures cumulées, un dossier bancable conforme au format exigé (GCF Funding Proposal, IFC AIMM Report, EUDR Due Diligence Statement, EIES catégorie B) exportable en PDF + DOCX.
- **SC-U3 — Progression administrative graduée** : une PME informelle reçoit un plan chiffré et séquencé pour atteindre le niveau administratif ouvrant l'accès à un fonds donné (ex. RCCM + NINEA pour accéder au FEM SGP). Le passage de niveau N à N+1 est mesurable via la présence validée des documents.
- **SC-U4 — Cohérence multi-référentiel sans re-saisie** : pour une même donnée déclarée (ex. `BOD = 30 mg/L`), l'utilisateur voit simultanément les verdicts IFC PS, RSPO, ISO 14001, GRI sans ressaisir la donnée. Le moment différenciateur attendu : « ah, je n'ai saisi ça qu'une fois ».
- **SC-U5 — Lisibilité de la voie d'accès** : pour chaque fonds suggéré, l'utilisateur comprend en un coup d'œil s'il postule directement ou via un intermédiaire, et dispose des coordonnées actualisées de l'intermédiaire le cas échéant.

### Business Success

> **Note d'engagement sur les métriques quantitatives :** les métriques marquées `[à quantifier]` (SC-B1, SC-B5, SC-B6, MO-5) seront précisées avant Go-to-Market MVP lors d'un atelier stratégique avec stakeholders business. Le PRD n'engage pas de chiffres arbitraires à ce stade.

- **SC-B1 — Adoption cible (PME AO francophones)** : `[à quantifier]` utilisateurs actifs mensuels (PME ou consultants/accompagnateurs institutionnels agissant pour le compte de PME) d'ici T+12 mois post-lancement MVP.
- **SC-B2 — Taux de conversion dossier soumis → accepté** : supérieur ou égal à la moyenne constatée dans la région sur les fonds cibles (benchmark à constituer).
- **SC-B3 — Partenariats institutionnels** : au moins **2 Lettres d'intention (MOU) signées** avec intermédiaires agréés (BOAD, SIB, Ecobank, BDU, banques SUNREF) d'ici **T+9 mois**, dont au moins **1 partenariat opérationnel end-to-end** (parcours intermédié intégré dans Mefali) d'ici **T+15 mois**.
  _Rationale : les processus bancaires institutionnels AO prennent en moyenne 12–18 mois ; un partenariat opérationnel end-to-end en 9 mois serait agressif sans équipe Business Development dédiée._
- **SC-B4 — Reconnaissance AFAC Continental Sustainable Finance Taxonomy (BAD)** : l'AFAC Continental Taxonomy étant déjà validée (juillet 2025, Nairobi), l'objectif est désormais l'alignement opérationnel effectif — intégration du référentiel AFAC dans le catalogue Mefali d'ici Phase 2, et inclusion comme « premier outil opérationnel aligné » dans au moins un support de communication BAD/AFAC (publication, événement BRVM, note technique) d'ici T+18 mois. Pas un objectif de certification institutionnelle.
- **SC-B5 — Revenus d'abonnement (modalité SaaS B2B)** : modèle économique validé sur cohorte pilote `[à quantifier]`. La facturation effective est hors scope MVP (modalité secondaire Phase Growth).
- **SC-B6 — Rétention à 6 mois** : au moins `[à quantifier]` % des PME ayant complété un dossier reviennent pour un second dossier, une nouvelle évaluation annuelle, ou le suivi d'un plan d'action.

### Technical Success

- **SC-T1 — Dette P1 résolue** : les 10 dettes P1 restantes de l'audit 18-specs (hors 4 déjà résolues : rate limiting chat, quota stockage, OCR bilingue, flag édition manuelle) sont soit closes soit formellement acceptées comme différées (`deferred-work.md` à jour).
- **SC-T2 — Baseline tests verts conservée** : le principe *zero failing tests on main* (mis en place story 9.3 le 17 avril 2026) est respecté tout au long de l'extension. À chaque clôture de phase (Phase 0, 1, 2, 3), la baseline de tests verts doit être documentée et croissante.
- **SC-T3 — Performance du cube 4D** : une requête multi-dimensionnelle sur le catalogue (~500 critères × ~50 référentiels × 8 pays × 5 maturités projet × 4 maturités entreprise × 2 voies d'accès) renvoie en moins de 2 s au p95 avec cache tiède.
- **SC-T4 — Performance de la génération de verdicts** : pour une évaluation ESG complète (30–60 critères issus du cube), les verdicts multi-référentiels sont calculés et persistés en moins de 30 s p95.
- **SC-T5 — Intégrité du snapshot** : 100 % des `FundApplication` portent un snapshot propre et non-mutable (hash stocké, versions de référentiels gelées, profil et projet figés à la date de soumission). Vérification par test d'intégration à chaque merge.
- **SC-T6 — Cohérence multi-référentiel** : zéro cas de verdicts contradictoires sur un même fait atomique à verdicts déclenchés sur le même snapshot. Vérification par test de propriété (property-based testing).
- **SC-T7 — i18n-ready** : aucun hardcoding `fra` ou `lang='fra'` hors du fichier de configuration par défaut. Tous les messages sortants extractibles vers un système i18n. Vérification par lint + CI.
- **SC-T8 — Guards LLM sur documents persistés remis aux bailleurs** : 100 % des contenus LLM destinés à un bailleur (résumé exécutif, plan d'action, fiche préparation, narratifs de dossier) passent un guard structurel (longueur, cohérence numérique avec les faits source, vocabulaire interdit, schéma Pydantic strict). Aucun déploiement possible sans guards actifs.
- **SC-T9 — Couverture RAG transversale** : au moins 5 modules sur 8 exploitent le RAG documentaire (FR-005 spec 009 enfin tenue, cohérent avec P1 #13 de l'audit) en fin de Phase 2. Objectif 8/8 en fin de Phase 4.
- **SC-T10 — Protection des données (obligatoire prod)** :
  - Chiffrement at rest pour les données financières et sensibles (bilans, RCCM, documents fiscaux) + chiffrement in transit (TLS 1.3 minimum)
  - Rétention documentée par type de donnée (profil utilisateur, documents uploadés, logs, snapshots FundApplication), droit à l'effacement implémenté (soft delete + purge après délai documenté)
  - Audit trail complet des accès aux données sensibles (qui a consulté quoi, quand)
  - Conformité loi sénégalaise 2008-12 sur la protection des données personnelles et équivalents nationaux UEMOA/CEDEAO (Côte d'Ivoire 2013-450, règlement CEDEAO)
  - Aucun PII (nom, adresse, numéros documents administratifs) envoyé aux prompts LLM sans anonymisation préalable (cf. NFR10 à définir en Step 10)
- **SC-T11 — Observabilité (clôture P1 #14 de l'audit)** :
  - 100 % des tools métier LangChain instrumentés avec `with_retry` + `log_tool_call` (clôt la dette P1 #14 : actuellement 2/11 modules instrumentés)
  - Dashboard monitoring interne avec p95 de latence par tool, taux d'erreur, taux de retry
  - Alerting configuré sur : échec de guards LLM, timeouts LLM, erreurs DB, taux de retry anormal (circuit breaker implicite)
  - Logs structurés JSON avec `request_id` traversant tout le graphe LangGraph (corrélation frontend → chat node → tool → DB)

### Measurable Outcomes

- **MO-1** — Une PME seule complète un dossier bancable **en quelques heures à quelques jours** (vs plusieurs semaines avec consultant traditionnel). **Divisé par 10 comme ordre de grandeur.**
- **MO-2** — Nombre médian de fonds suggérés avec voie d'accès concrète par utilisateur activement accompagné : ≥ 3.
- **MO-3** — Nombre de référentiels supportés dans le catalogue à chaque jalon : Phase 1 = 3 (IFC PS + EUDR + grille interne), Phase 2 = 6, Phase 3 = 10, Phase 4 = 15+.
- **MO-4** — Nombre de templates de livrables opérationnels : Phase 2 = 4, Phase 3 = 8, Phase 4 = 12+.
- **MO-5** — Taux de passage de niveau administratif (informel → RCCM) chez les utilisateurs activement accompagnés : `[à quantifier]` % à 6 mois.
- **MO-6** — Latence chat utilisateur (temps de réponse perçu du premier token) : ≤ 2 s p95 pendant le streaming SSE.

## Product Scope

> **Note sur les durées de phases :** les estimations indiquées pour chaque phase sont des **fourchettes initiales à affiner par l'équipe Dev lors du Sprint Planning** de chaque phase. Le PRD n'engage pas sur ces fourchettes comme SLA calendaire — elles guident le séquencement et la pondération relative, pas le calendrier absolu.

### MVP — Minimum Viable Product

Objectif MVP : démontrer qu'une PME ouest-africaine peut générer un dossier bancable conforme pour au moins un bailleur international majeur sans consultant, en incluant le pré-requis d'adoption (formalisation graduée).

**Phase 0 — Dettes P1 transverses (prérequis bloquants, estimation ~4–6 semaines)** :
- Migration catalogues hard-codés → BDD + interface admin (`fund`, `intermediary`, `esg_sector_config`, `carbon_emission_factor`, `regulation_reference`)
- Framework d'injection d'instructions unifié (registry + builder — consolide `STYLE` + `WIDGET` + `GUIDED_TOUR` + nouveaux contextes)
- Enforcement applicatif du contexte actif (`active_project` + `active_module` + guards pré-tool, state machine)
- Registre de blocs visuels extensible (prérequis avant dashboard enrichi)
- Snapshot propre systématique
- RAG transversal étendu à au moins 5 modules sur 8

**Phase 1 — Cube bailleur 4D + ESG multi-contextuel + Formalisation graduée (MVP cœur, estimation ~12–16 semaines)** :
- **Cluster A** : modèle `Company × Project` (N:N) avec `ProjectMembership` et rôle (porteur principal / co-porteur / bénéficiaire), `FundApplication` (N par projet), `CompanyProjection` (vue curée par fonds), `ProjectSnapshot`, cycle de vie projet en 5 états (idée / faisabilité / bancable / exécution / achevé).
- **Cluster A'** (intégré Phase 1 au lieu de Phase 2 — nuance utilisateur : pré-requis d'adoption 80 % du marché cible) : `AdminMaturityLevel` avec 4 niveaux (informel / RCCM+NIF / comptes+CNPS / OHADA audité), détection mixte (auto-déclaration + validation OCR progressive via module 004), `FormalizationPlan` généré par Claude, `BeneficiaryProfile` pour consortiums (coopérative, GIE, cluster), table `AdminMaturityRequirement(country × level)` pour paramétrage pays.
- **Cluster B — Catalogue P0** : architecture 3 couches (`Fact` atomique, `Criterion` composable, `ReferentialVerdict` dérivé), référentiels P0 livrés = IFC PS1–PS8 + EUDR + grille interne Mefali. Packs livrés = Pack IFC Bancable + Pack EUDR-DDS + Pack Artisan Minimal.
- **Cube 4D opérationnel** : le matching fonds consomme `projet.maturité × entreprise.maturité × référentiels_requis × voie_d'accès`, résultat affiché avec parcours concret d'accès (dossier direct OU identification de l'intermédiaire + coordonnées + prérequis).

**Compliance minimums MVP non négociables :**
- Guards LLM actifs sur tous documents persistés remis aux bailleurs (SC-T8)
- Snapshot propre sur 100 % des soumissions (SC-T5)
- Zero failing tests on main (principe déjà opérationnel)
- Interface admin pour gestion du catalogue (signal PRD 1 de l'audit)
- Protection des données prod conforme SC-T10
- Observabilité minimale conforme SC-T11 (tools instrumentés + logs JSON)

### Growth Features (Post-MVP)

Objectif Growth : rendre le produit compétitif sur la largeur de couverture et la profondeur UX.

**Phase 2 — Moteur de livrables + extension catalogue (estimation ~10–14 semaines)** :
- **Cluster C** : pyramide `DocumentTemplate` → `ReusableSection` → `AtomicBlock` ; premier lot de templates (GCF Funding Proposal, IFC AIMM Report, EUDR DDS, EIES Cat B, Proparco AIMM Report).
- **Cluster B extension P1** : certifications sectorielles (RSPO, Rainforest Alliance), ISO 14001, packs régionaux AO (Pack BCEAO, Pack RSE Sénégal, Pack RSE Côte d'Ivoire).
- Tags de renforcement AO activés (`community_relations`, `local_content`, `climate_adaptation`, `anti_corruption`) avec pondération par pack régional.

**Phase 3 — UX enrichi + renforcements AO profonds (estimation ~8–10 semaines)** :
- **Cluster D P1** : registre typé de blocs visuels (11 types : KPI, donut, barres, timeline, carte géo, heatmap, gauge, table croisée, radar, waterfall, Sankey), personas différenciées (entrepreneur mono-projet / multi-projets / consortium / dirigeant / équipes fonctionnelles / admin), mobile-first low-data.
- **Cluster B P1 suite** : anti-corruption gradué ISO 37001, adaptation climatique physique TCFD (extension module carbone existant), scoring S ouest-africain (CLIP, grief, contenu local, travail des enfants).
- Multi-tenant B2B (quotas par user), préparation facturation.
- Nouveaux types de rappels (renouvellement certifs, expiration de faits, MàJ version référentiel).

**Phase 4 — Extension catalogue + personnalisation (estimation ~6–10 semaines)** :
- **Cluster B P2** : GRI, TCFD, CDP, SASB, IFC AIMM, Proparco AIMM, IRIS+, certifs régionales CGECI.
- **Cluster D P2** : PWA offline, drag & drop dashboard, formation par rôle (Claude pour socle + review humaine pour spécialisation filière), multi-tenant consultant-like (exploration Option 3 hybridation).
- Extension Chrome (item du roadmap initial ESG Mefali, hors scope MVP mais réintroduit en Phase 4).

### Vision (Future)

Objectif Vision : devenir l'infrastructure de référence pour la finance verte PME en Afrique de l'Ouest.

- **Hybridation marketplace consultant** (Option 3 complète) : consultants ESG certifiés peuvent opérer dans l'outil et facturer leurs interventions ; les PME choisissent mode autonome ou mode assisté. Modèle de revenus mixte.
- **Expansion régionale anglophone** : Ghana, Nigeria, Liberia, Sierra Leone. Architecture i18n activée, codes OHADA non applicables → mapping documentaire pays-spécifique à enrichir.
- **Expansion continentale** : Afrique centrale (CEMAC), Afrique de l'Est, Afrique australe.
- **Reconnaissance institutionnelle taxonomie BAD** : passage de « opérationnel aligné » (SC-B4) à « référence institutionnelle reconnue ».
- **Intégration API directe avec bailleurs** : soumission automatisée vers les portails GCF, FEM, BAD, BOAD (après partenariat technique).
- **Signatures électroniques eIDAS-qualifiées** sur les livrables PDF.
- **File de jobs asynchrones (Celery/RQ)** pour génération de gros dossiers (post-MVP identifié dans QO-C1 du brainstorming).

## User Journeys

> **Note sur les personas :** Aminata Diagne et Moussa Kouakou sont repris des personas utilisés dans les tests e2e existants (stories 8.1, 8.2) pour cohérence produit. Fatou Diallo (Dakar, agroalim — persona test e2e 8.3) reste à sa place d'origine et n'est pas utilisée ici pour éviter toute confusion sémantique. Akissi Kouadio, Ibrahim Sawadogo et Mariam Touré sont de nouveaux personas narratifs introduits pour ce PRD.

### Journey 1 — Aminata (PME solo informelle, voie directe) — Primary user success path

**Persona.** Aminata Diagne, 34 ans, transformatrice de mangues séchées à Ziguinchor (Sénégal). Depuis 3 ans, elle opère en totale informalité : pas de RCCM, pas de NINEA, paie ses 4 salariés en espèces, vend sur les marchés locaux et à un exportateur français qui la paie via Orange Money Business. Son exportateur lui a dit : « tes mangues sont super mais à partir du 30 juin 2027 (date EUDR pour les PME), je ne pourrai plus acheter sans preuve de chaîne d'approvisionnement conforme EUDR. Tu dois régulariser. » Elle ne sait ni ce qu'est l'EUDR, ni par où commencer à se formaliser.

**Opening scene.** Aminata ouvre son navigateur mobile sur un vieil Android 2 Go de RAM. Une connexion 3G faible. Elle tape le lien donné par une amie commerçante à Dakar. Mefali répond : « Bonjour, je suis votre conseillère ESG IA. Pour commencer, dites-moi simplement ce que vous faites et dans quelle région. »

**Rising action.** En 15 minutes de chat entrecoupé de reconnexions, Mefali identifie le secteur (agroalimentaire, transformation fruits), le pays (Sénégal), le niveau de formalisation (0 — informel), la présence d'un client export EU. Mefali active automatiquement le pack **EUDR-DDS** en façade, détecte les faits manquants pour la compliance déforestation, et signale qu'il y a **2 fonds FEM Small Grants Programme** éligibles à son cas dès qu'elle passera au niveau 1 (RCCM + NINEA). Voie d'accès : FNDE au Sénégal en direct, pas d'intermédiaire obligatoire.

**Climax.** Mefali génère un **FormalizationPlan** chiffré : 125 000 FCFA pour RCCM Ziguinchor + 15 000 FCFA NINEA + 3 semaines estimées. Plan d'action personnalisé avec les coordonnées du Tribunal de commerce de Ziguinchor et du bureau NINEA local. Aminata voit pour la première fois un chemin concret. Elle coche « je commence le RCCM cette semaine ».

**Resolution.** 6 semaines plus tard, Aminata uploade ses documents RCCM+NINEA. Le niveau est automatiquement validé par OCR (module 004). Mefali débloque le FEM SGP et commence à guider la préparation du dossier. Parallèlement, la déclaration EUDR DDS se remplit automatiquement avec les faits saisis (géolocalisation plantations, traçabilité chaîne). Son exportateur reçoit le premier DDS bancable. Continuité commerciale assurée.

**Capabilities révélées :** Cluster A (projet mono, maturité idée→bancable) · Cluster A' (niveau 0→1, `FormalizationPlan`, coordonnées locales) · Cluster B (pack EUDR-DDS, faits qualitatifs attestables sur traçabilité) · Cluster C (template EUDR DDS) · UX mobile low-data · Rappels (relance sur RCCM J+14 si silence).

---

### Journey 2 — Moussa (Coopérative cacao, voie intermédiée) — Primary multi-projets consortium

**Persona.** Moussa Kouakou, 48 ans, président de la coopérative COOPRACA (152 producteurs de cacao en région Bouaflé, Côte d'Ivoire). La coopérative est formalisée (OHADA, RCCM, IFU), niveau 2 administratif. Mais 80 % de ses membres restent en niveau 0 (informel individuel). COOPRACA veut financer deux projets distincts : (1) une unité de fermentation centralisée pour améliorer la qualité et (2) un programme de reforestation d'arbres d'ombrage pour aller vers Rainforest Alliance et se conformer à EUDR. Budget projet 1 : 380 M FCFA. Budget projet 2 : 210 M FCFA.

**Opening scene.** Moussa ouvre Mefali sur un ordinateur portable au bureau de la coopérative. Il crée deux projets distincts — Mefali lui explique que ce sont deux `Project` séparés liés à la même `Company` (COOPRACA), et que chaque projet pourra être présenté à plusieurs fonds via des `FundApplication` différentes, calibrées à chaque bailleur, sans duplication des faits réels (impact mesuré une seule fois).

**Rising action.** Pour le projet 1 (fermentation), le cube 4D matche : GCF (voie intermédiée via BOAD), BOAD Ligne Verte (voie intermédiée via Ecobank CI), SUNREF (voie intermédiée via SIB). Mefali expose les prérequis SPÉCIFIQUES de chaque intermédiaire (Ecobank veut un minimum de 5 ans d'ancienneté, SIB accepte 3 ans). COOPRACA a 12 ans d'existence : les trois voies sont ouvertes. Pour le projet 2 (reforestation), le cube matche GCF + FEM + Rainforest (certif sectorielle, pack Rainforest + EUDR).

**Climax.** Moussa doit choisir l'intermédiaire pour le projet 1. Mefali affiche un tableau comparatif : SIB propose 12 mois de traitement, Ecobank 9 mois, BOAD Ligne Verte 18 mois mais taux préférentiel. Moussa choisit SIB. Mefali génère la fiche de préparation orientée SIB (pas orientée GCF) avec les critères propres à SIB + coordonnées actualisées du conseiller PME régional d'Abidjan. Pour le projet 2, Mefali active le **BeneficiaryProfile** pour déclarer les 152 producteurs en bénéficiaires (genre, revenus, niveau de formalisation individuel), sans exiger que chacun soit formalisé — c'est la coopérative qui porte.

**Resolution.** Moussa soumet le dossier fermentation à SIB. Le snapshot est figé : le profil COOPRACA au 15 mai, les faits au 15 mai, les versions de référentiels IFC PS au 15 mai. Le projet 2 Rainforest est en cours de préparation parallèle. Quand SIB demandera des pièces complémentaires 6 mois plus tard, le snapshot garantit la cohérence. Parallèlement Mefali a généré une déclaration EUDR DDS pour l'acheteur européen de COOPRACA.

**Capabilities révélées :** Cluster A (Project multi, `ProjectMembership` consortium, lifecycle et snapshot) · Cluster A' (niveau 2 stable, `BeneficiaryProfile` pour membres) · Cluster B (packs GCF + BOAD + SUNREF + Rainforest + EUDR, voie intermédiée avec critères superposés) · Cluster C (template SIB vs GCF, même projet mais templates différents) · Dashboard multi-projets.

---

### Journey 3 — Akissi (PME palme OHADA audité, voie mixte + SGES) — Advanced case

**Persona.** Akissi Kouadio, 51 ans, DG de Palmoil Côte d'Ivoire SARL, 47 salariés, installée à Abidjan (zone industrielle de Yopougon) depuis 2008. SARL OHADA, comptes audités annuellement, niveau 3 administratif complet. Ses 2 500 tonnes/an d'huile de palme sont vendues à des industriels européens qui exigent désormais RSPO. La Côte d'Ivoire est le premier pays producteur d'huile de palme en Afrique de l'Ouest, et RSPO y est particulièrement actif. Akissi veut financer une modernisation de l'usine (efficacité énergétique + traitement des effluents) : budget 1,2 Md FCFA.

**Opening scene.** Akissi se connecte à Mefali depuis son bureau. Elle a déjà consulté plusieurs cabinets ESG européens qui lui ont demandé 35 000 EUR pour un audit complet et la construction d'un SGES/ESMS conforme IFC. Elle cherche une alternative viable.

**Rising action.** Mefali charge rapidement son profil depuis les documents uploadés (statuts SARL, 3 derniers bilans audités). Le niveau est validé automatiquement à 3 par OCR. Le cube 4D matche : GCF (voie intermédiée via BOAD), IFC direct (voie directe, niveau 3 requis — ouvert), Proparco (voie directe), BOAD Ligne Verte, FEM. Rendu : 5 fonds accessibles, 3 en voie directe. Mefali déclenche automatiquement un **pack IFC Bancable** + **pack RSPO Premium** + **pack BCEAO**.

**Climax.** Akissi saisit ses faits sur les effluents (BOD, COD, volumes, système existant). Mefali produit en 28 secondes les verdicts simultanés : **IFC PS3 = FAIL** (BOD 45 mg/L > seuil IFC EHS 30), **RSPO 5.3 = PASS conditionnel** (seuil RSPO plus tolérant), **ISO 14001 = gap système documenté**, **GRI 303 = reporté**. Akissi voit pour la première fois comment le même fait produit des verdicts différents selon le référentiel — et comprend pourquoi sa conformité RSPO ne suffit pas pour IFC. En parallèle, Mefali assemble un **SGES/ESMS complet** à partir des faits saisis : politique E&S, procédures opérationnelles (gestion des effluents, santé-sécurité au travail, relations communautaires), manuel qualité, registre des risques catégorisé selon IFC PS1–PS8, mécanisme de grief opérationnel, plan d'action correctif (ESAP). Le tout généré en 2 semaines (pré-revue humaine recommandée) vs 35 000 EUR et 6 mois auprès d'un cabinet européen. Guards LLM actifs (SC-T8) sur chaque section du SGES avant validation.

**Resolution.** Mefali génère un plan d'action priorisé : investissement lagunage complémentaire (estimation 35 M FCFA) pour passer IFC, documentation ISO 14001 parallèle. Le dossier IFC est assemblé en 2 semaines avec les livrables (IFC AIMM template + SGES/ESMS + EIES Cat B + RSPO certification dossier). Akissi soumet directement à IFC en voie directe. Elle soumet le même projet en parallèle à BOAD via Ecobank (voie intermédiée) comme backup stratégique. Chaque `FundApplication` a son snapshot propre. Le SGES devient un actif durable : réutilisable pour d'autres demandes, renouvelable annuellement, conforme aux exigences récurrentes des bailleurs internationaux.

**Capabilities révélées :** Cluster A (Project unique, multiple FundApplications calibrées différemment, snapshot par application) · Cluster A' (niveau 3 validé automatiquement) · Cluster B (architecture 3 couches avec cohérence multi-référentiel prouvée, packs IFC + RSPO + BCEAO actifs) · Cluster C (IFC AIMM + EIES + RSPO + **SGES/ESMS** — livrable phare exigé par bailleurs internationaux, nouvelle classe de template) · Dashboard avancé (vue comparative 5 fonds × 3 packs).

---

### Journey 4 — Ibrahim (Edge case : projet refusé, parcours de remédiation)

**Persona.** Ibrahim Sawadogo, 39 ans, dirigeant d'une PME de recyclage plastique à Ouagadougou. Niveau 2 (comptes, CNSS). Soumet en voie directe à FNDE Sénégal — rejeté (FNDE finance projets au Sénégal, pas au Burkina).

**Opening scene.** Notification push : « Votre dossier FNDE a été refusé — motif : localisation hors zone d'intervention. » Ibrahim est découragé.

**Rising action.** Mefali propose immédiatement un **parcours de remédiation** : relance du cube 4D avec critère `country = BF`. Nouveaux matches : FEM SGP Burkina, BOAD Ligne Verte via BDU, fonds nationaux (FAARF femmes — non applicable, FODEL éligible pour élevage — non applicable, FEDER Burkina — éligible).

**Climax.** Mefali identifie l'erreur passée (filtrage pays insuffisant lors de la suggestion initiale) et corrige le catalogue en arrière-plan (signalement admin). Ibrahim voit 3 nouvelles pistes dont FEDER Burkina en voie directe, très adaptée.

**Resolution.** Le `FundApplication` refusé est archivé avec son motif de refus (trace pour apprentissage). Le nouveau dossier FEDER est en préparation.

**Capabilities révélées :** Gestion de cycle de vie `FundApplication` (statut refusé), observabilité admin (détection erreur matching), boucle de feedback sur catalogue.

---

### Journey 5 — Mariam (Admin Mefali — Catalog Owner)

**Persona.** Mariam Touré, data owner Mefali, responsable du catalogue faits / critères / référentiels / packs / fonds / intermédiaires. Aujourd'hui elle maintient tout cela via PR Git (dette P1 de l'audit).

**Opening scene — mise à jour référentiel.** RSPO (Roundtable on Sustainable Palm Oil) publie l'entrée en vigueur obligatoire de la version 2024 v4.0 des Principles & Criteria au 31 mai 2026 (adoption novembre 2024, postponement décidé en novembre 2025). Impact : évolutions sur la gestion des effluents, critères CLIP renforcés, nouvelles exigences de traçabilité ; plusieurs PME clientes Mefali (dont Palmoil Côte d'Ivoire SARL – Journey 3 Akissi) doivent migrer leur pack RSPO avant la deadline.

**Rising action.** Mariam se connecte à l'interface admin Mefali (livrée en Phase 0). Elle crée un nouveau référentiel `RSPO_PC@2024_v4.0`, importe la matrice de mapping depuis le CSV officiel RSPO. Mefali génère automatiquement un `ReferentialMigration` avec les `changed_facts[]` et les `changed_criteria[]` par rapport à la version antérieure.

**Climax référentiel.** Mariam active le référentiel `RSPO_PC@2024_v4.0` avec date d'effet `2026-05-31` (date obligatoire RSPO). Tous les `FundApplication` déjà soumises restent figées sur la version antérieure (snapshot). Les nouvelles évaluations basculent automatiquement sur `RSPO_PC@2024_v4.0`. Les utilisateurs avec un dossier en cours reçoivent une notification proposant soit de finaliser sur l'ancienne version, soit de migrer.

**Scene complémentaire — mise à jour intermédiaire.** Un mois plus tard, SIB annonce qu'elle assouplit ses critères : 2 ans d'ancienneté minimum au lieu de 3. Mariam met à jour `min_company_age_years` sur l'`Intermediary` SIB via l'interface admin. La modification est effective immédiatement dans le cube 4D, aucun redéploiement n'est nécessaire. Les PME de 2 à 3 ans d'existence voient SIB apparaître dans leurs voies d'accès dès leur prochain matching. Parallèlement, Mariam ajoute un nouveau fonds (GEF IW:LEARN Initiative lancé récemment) : formulaire admin, caractéristiques (instrument, maturité acceptée, seuils, pays couverts, voies d'accès), liaisons avec intermédiaires agréés — le fonds est immédiatement disponible pour le matching dans le cube.

**Resolution.** Les données historiques restent auditables. Les nouveaux dossiers bénéficient des nouvelles versions de référentiels, des intermédiaires actualisés et des nouveaux fonds ajoutés. Aucun rework manuel, aucune re-saisie utilisateur, **aucun PR Git** sur le code backend. La dette P1 de l'audit (12 fonds + 14 intermédiaires + 50 liaisons hard-codés dans `seed.py` 889 lignes) est entièrement couverte.

**Capabilities révélées :** Interface admin complète (signal PRD 1 de l'audit) couvrant référentiels + fonds + intermédiaires + liaisons, versioning des référentiels (SC-T5), snapshot propre rend la migration sûre, plan de migration automatique, mise à jour temps réel du cube de qualification.

---

### Journey Requirements Summary

Les 5 journeys révèlent les capacités suivantes que le PRD doit livrer :

**Data model (Cluster A + A') :**
- `Company × Project` N:N avec `ProjectMembership` (porteur, co-porteur, bénéficiaire)
- `FundApplication` multiple par projet, chacune calibrée par fonds, avec snapshot propre
- `CompanyProjection` (vue curée par fonds)
- `AdminMaturityLevel` 4 niveaux avec détection mixte auto-déclaration + OCR
- `FormalizationPlan` avec coordonnées pays-spécifiques
- `BeneficiaryProfile` agrégé pour consortiums

**Moteur ESG (Cluster B) :**
- `Fact` atomiques (quantitatifs + qualitatifs attestables) versionnés temporellement
- `Criterion` composables avec métadonnées (référentiels, secteurs, tailles, maturités, voies d'accès)
- `ReferentialVerdict` dérivé automatiquement avec règles de dérivation
- `Pack` pré-assemblés en façade (IFC Bancable, RSPO Premium, EUDR-DDS, BCEAO, etc.)
- Versioning et migration des référentiels

**Matching cube 4D :**
- Requête multi-dimensionnelle (projet × entreprise × référentiels × voie d'accès)
- Affichage des prérequis par intermédiaire quand voie intermédiée
- Gestion des rejets avec parcours de remédiation
- Coordonnées intermédiaires actualisées

**Moteur de livrables (Cluster C) :**
- Pyramide `DocumentTemplate` → `ReusableSection` → `AtomicBlock`
- Templates : GCF, IFC AIMM, EUDR DDS, EIES Cat B, RSPO, Proparco, SIB (intermédiaire), **SGES/ESMS IFC-conforme** (livrable phare exigé par bailleurs internationaux)
- Génération calibrée selon voie d'accès (template fonds vs template intermédiaire)
- Snapshot + hash pour immutabilité

**Interface admin (Cluster C + P1 audit) :**
- Gestion CRUD complète : référentiels (versions, packs), fonds, intermédiaires, liaisons fonds-intermédiaires, faits, critères, règles de dérivation
- Mise à jour temps réel sans redéploiement
- Import CSV pour matrices référentielles
- Migration automatique entre versions

**UX (Cluster D) :**
- Mode mobile low-data avec reconnexion gracieuse (Aminata)
- Vue multi-projets avec tabs (Moussa)
- Dashboard comparatif (Akissi)
- Notifications de rejet + parcours de remédiation (Ibrahim)
- Interface admin (Mariam)

**Transversal :**
- Guards LLM sur tous livrables remis aux bailleurs (SC-T8), y compris SGES/ESMS
- Observabilité (logs structurés avec `request_id`)
- Protection des données + anonymisation PII avant LLM (SC-T10)
- i18n-ready pour futures expansions anglophones

## Domain-Specific Requirements

### Compliance & Regulatory

**Référentiels bailleurs internationaux (Phase 1–2) :**
- **IFC Performance Standards** (PS1–PS8) — référentiel pivot pour tout financement IFC, Proparco, FMO, DEG, BIO, BAD SSI, BOAD. Version actuelle en vigueur : `IFC_PS@2012`. Update Framework en consultation (Phase I Dialogue jan–mars 2026, Phase II Consultation publique avril 2026 – mars 2028) — **nouvelle version publique attendue ≥ 2028**, à anticiper via le pattern `ReferentialMigration` mais pas d'urgence court-terme.
- **Principes de l'Équateur** — pour banques régionales (Ecobank, NSIA, Coris, BOA, Société Générale CI, Orabank, UBA) qui syndiquent avec banques internationales.
- **Système de Sauvegardes Intégré BAD** — conditionne les prêts BAD.
- **GCF Safeguards** — Green Climate Fund, voie accès via entités nationales désignées (BOAD, BAD) pour l'AO.
- **FEM Safeguards Standards** — Fonds pour l'Environnement Mondial.
- **Banque Mondiale ESF (Environmental and Social Framework)** — 10 ESS (Environmental and Social Standards), pour projets financés via BM/IDA. Phase 2.
- **DFI Harmonized Approach to Private Sector Operations** — accord inter-bailleurs (FMO, Proparco, BIO, DEG, IFC, CDC...) harmonisant les exigences ESG. Phase 2.

**Conventions fondamentales OIT/ILO (Phase 1 — critique) :**
- 8 conventions fondamentales : **travail forcé (29, 105)**, **travail des enfants (138, 182)**, **non-discrimination (100, 111)**, **liberté syndicale (87, 98)**.
- Exigée explicitement par **CS3D** et **EUDR** — tolérance zéro sur le travail des enfants dans les filières cacao, coton, palme.

**Réglementations clients export européens (Phase 1 — critique pour filières cacao / palme / coton / bois) :**
- **EUDR (Règlement UE 2023/1115, modifié par Règlement UE 2025/2650)** — déforestation importée, géolocalisation des parcelles, traçabilité chaîne d'approvisionnement, déclaration DDS. Dates d'application définitives : **30 décembre 2026 pour grandes entreprises**, **30 juin 2027 pour PME et micro-entreprises (= cible Mefali)**. Une simplification review est attendue de la Commission UE avant le 30 avril 2026 — un report supplémentaire reste possible, à surveiller (RM-4).
- **CS3D (Directive européenne devoir de vigilance)** — transposition nationale en cours, applicable aux fournisseurs de grandes entreprises UE.
- Autres cadres non-réglementaires mais quasi-obligatoires commercialement : Sedex/SMETA (4-pillar audit), EcoVadis (scoring ESG fournisseur), SA8000 (responsabilité sociale), BSCI (conformité sociale).

**Référentiels d'engagement volontaire (Phase 2) :**
- **UN Global Compact** — adhésion référencée par nombreux bailleurs d'impact.
- **Principes Volontaires sur la Sécurité et les Droits de l'Homme** — crucial pour zones minières et Sahel (gestion des forces de sécurité privées). Phase 3, secteur extractif.

**Référentiels certifications sectorielles (Phase 2) :**
- **RSPO** (huile de palme), **Rainforest Alliance / UTZ** (cacao, café), **Fairtrade**, **Bonsucro** (sucre), **FSC** (bois), **ResponsibleSteel**, **IRMA** (mines).

**Normes ISO valorisables (Phase 2) :**
- ISO 14001 (environnement), ISO 45001 (SST), ISO 26000 (RSE lignes directrices), ISO 37001 (anti-corruption), ISO 14040 (LCA).

**Reporting extra-financier (Phase 3–4) :**
- **GRI Standards** (référentiel dominant pour rapports de durabilité en AO), **TCFD** (risques climatiques physiques + transition), **CDP** (climat, eau, forêts), **SASB**, **IFC AIMM** et **Proparco AIMM** (impact mesuré bailleurs), **GIIN IRIS+**, **ITIE** (transparence extractives).

**Référentiels régionaux AO (Phase 2–3) :**
- **Charte RSE Sénégal**, **Plateforme RSE Côte d'Ivoire**, **RSE & Développement Durable Bénin**, **Label RSE CGECI**, **AFAC Continental Sustainable Finance Taxonomy (BAD)** — validée juillet 2025 à Nairobi par régulateurs, banques, assureurs et DFI sous la plateforme African Financial Alliance on Climate Change (AFAC). Support technique PwC Luxembourg, financement Global Center on Adaptation via AAAP. Déploiement opérationnel en cours.

**Droit des sociétés + régimes sociaux (Cluster A' — table `AdminMaturityRequirement`) :**
- **OHADA** (Acte uniforme sur les sociétés commerciales) — uniforme UEMOA/CEDEAO francophone, RCCM uniforme.
- **Identifiants fiscaux** : NINEA (SN), IFU (CI, BF, BJ, TG), NIF (ML, NE) — variable par pays.
- **Régimes sociaux** : CNPS (CI, BF, BJ, TG, NE), IPRES+CSS (SN), INPS (ML) — variable par pays.
- **Salaire minimum (SMIG)** — variable par pays.
- **Codes environnementaux nationaux** : ANDE (CI), DEEC (SN), BUNEE (BF).

**Protection des données personnelles (SC-T10) :**
- **Loi sénégalaise 2008-12** sur la protection des données personnelles.
- **Loi ivoirienne 2013-450**.
- **Règlement CEDEAO** sur la protection des données.
- Principe d'alignement structurel avec le **RGPD** pour anticiper les échanges transfrontaliers avec des clients/bailleurs européens.

**Anti-corruption et transparence :**
- **FCPA** et **UK Bribery Act** — extra-territoriaux, engagent les PME traitant avec des multinationales US/UK.
- **HABG** (Haute Autorité pour la Bonne Gouvernance, Côte d'Ivoire), **OFNAC** (Office national de lutte contre la fraude et la corruption, Sénégal).
- **ITIE** — pour extractives.

### Technical Constraints

**Sécurité :**
- **TLS 1.3 minimum** pour toutes les connexions client-serveur et serveur-serveur.
- **Chiffrement at rest** avec clés gérées via KMS pour les données sensibles : RCCM, bilans audités, preuves documentaires (effluents, traçabilité), faits qualitatifs attestables.
- **Audit trail structuré** sur tous les accès aux données sensibles, avec rétention minimum de 12 mois en chaud, 5–10 ans archivés.
- **Authentification multi-facteur** pour les rôles admin Mefali.
- **Anonymisation PII systématique** avant envoi aux prompts LLM (noms, adresses, numéros RCCM, NINEA, IFU, téléphones) — substitution par tokens déterministes.
- **Rate limiting** déjà livré pour le chat (story 9.1), à étendre aux tools coûteux (génération PDF, dossiers complets).

**Privacy et rétention (par catégorie) :**
- **Profil utilisateur** : durée de compte + 2 ans.
- **Documents uploadés ordinaires** : durée de compte + 5 ans (traçabilité bailleur).
- **SGES/ESMS et documents associés** (politique E&S, grief log, EIES, PGES, PAR/RAP) : **conservation 10 ans minimum** après fin de la `FundApplication` associée (ou date d'amortissement si supérieure à 10 ans). C'est un document légal de référence que les bailleurs peuvent demander jusqu'à 10 ans après fin du financement.
- **Faits atomiques** : versions historiques conservées indéfiniment (SC-T5 snapshot).
- **Logs applicatifs** : 12 mois.
- **Logs d'audit accès données sensibles** : 5 ans.
- **Soft delete + purge différée** (30–90 jours) pour permettre réversibilité.
- **Consentement explicite** pour tout partage vers un bailleur ou un intermédiaire (distinction « saisi dans Mefali » vs « partagé avec tiers »).
- **Droit à l'effacement** implémenté avec impact documenté sur les `FundApplication` soumis (figées par snapshot, indépendantes du profil vivant).

**Performance :**
- Requête cube 4D ≤ 2 s p95 (SC-T3).
- Génération verdicts multi-référentiels ≤ 30 s p95 pour évaluation complète (SC-T4).
- Génération de livrable PDF simple ≤ 30 s p95.
- Génération de livrable lourd (SGES/ESMS complet, IFC AIMM full) : jusqu'à 2–3 minutes acceptable — si dépassement régulier, migration vers file Celery post-MVP (QO-C1 du brainstorming, Vision).
- Latence chat utilisateur ≤ 2 s p95 pour le premier token streaming (MO-6).

**Disponibilité — SLA différencié :**
- **Endpoints critiques** (soumission `FundApplication`, génération SGES/ESMS, génération dossier bailleur lourd) : **objectif 99.5 % dès MVP** (~3,6 h d'indisponibilité tolérée par mois). Ces endpoints doivent être **atomiques et resumables** (reprise sur échec réseau sans perte, via LangGraph checkpointer existant). Les soumissions aux deadlines bailleurs sont des moments critiques absolus.
- **Endpoints non-critiques** (chat conversationnel, dashboard read-only, recherche catalogue) : objectif 99 % MVP, 99.5 % Phase Growth.
- Plan de continuité : sauvegarde automatique BDD (pgvector inclus) avec rétention 30 jours minimum, test de restauration trimestriel.

**Observabilité (SC-T11) :**
- Logs structurés JSON avec `request_id` traversant frontend → LangGraph → tool → DB.
- Dashboard interne : p95 latence par tool, taux d'erreur, taux de retry, échecs guards LLM, timeouts LLM.
- Alerting sur échecs de guards LLM, taux de retry anormal (circuit breaker), erreurs DB, timeouts.

### Integration Requirements

**Systèmes externes en lecture / écriture :**

- **LLM provider (Anthropic via OpenRouter)** — streaming SSE, timeout explicite 60 s (livré spec 015), gestion de quotas et de coûts par utilisateur (rate limiting tool par tool en Phase Growth, cf. P3 #30 audit).
- **Embeddings multilingues** — OpenAI `text-embedding-3-small` pour pgvector (existant). Évaluation à terme d'alternatives open-source pour maîtrise des coûts.
- **OCR Tesseract** — bilingue `fra+eng` (livré story 9.4), à étendre à `por` en Phase Vision (expansion lusophone éventuelle).
- **Stockage de documents** — local `/uploads/` en MVP (cohérent avec l'existant), migration S3/MinIO identifiée en Phase Growth pour scaling.
- **Email sortant** — notifications de rappels, confirmations d'upload, alertes d'échéance. Provider à définir (Mailgun, SendGrid, SMTP direct).
- **SMS / WhatsApp** (Phase Growth) — canal notification pour PME à connectivité email limitée, particulièrement coopératives en zones rurales.

**Paiement (décision : freemium MVP, intégration Phase Growth) :**
- **MVP = pas de paiement.** Freemium ou free pour early adopters. Cohérent avec la priorité Phase 0–1 (cube 4D + catalogue + formalisation).
- **Phase Growth — architecture d'intégration :**
  - **Priorité 1 : un agrégateur africain** (CinetPay OU Paystack) pour simplifier le multi-opérateurs mobile money (Orange Money dominant, Wave disruptif, MTN MoMo, Moov Money). Une seule intégration technique couvrant tous les opérateurs.
  - **Priorité 2 : Stripe** pour paiements internationaux (consultants Phase Vision, partenariats bailleurs, subscription card).
  - Décision finale CinetPay vs Paystack à trancher lors de Phase Growth avec étude comparative commissions / couverture pays / UX.
  - **NFR :** facturation multi-devises XOF + EUR + USD, mobile money prioritaire sur carte pour le marché cible.

**Systèmes tiers envisagés (hors MVP) :**
- **APIs bailleurs** (Vision — réaliste, ne pas s'engager) — GCF, FEM, BAD Connect : soumission directe de dossiers, statut de traitement, reporting d'impact post-financement. Aucun bailleur AO majeur n'expose d'API publique de soumission à ce jour (GCF, FEM, BAD, BOAD ont des portails web, pas d'APIs tierces). Prérequis : partenariat institutionnel explicite, protocole de sécurité conforme bailleur (probablement mTLS + certificats), modèle de données mappé entité par entité. Si une opportunité partenariat émerge plus tôt : story dédiée ad-hoc.
- **Registres publics** (Vision) — RCCM régional CEDEAO pour vérification automatique, registres tribunal commerce par pays.
- **Plateformes de certification** (Phase Growth) — RSPO palm tracer, Rainforest certification management.

**Flux de données internes :**
- Frontend Nuxt 4 → FastAPI REST + SSE streaming (existant).
- LangGraph orchestration → tools LangChain → BDD PostgreSQL + pgvector (existant).
- Tools Admin → BDD directement, sans passage par LLM (Interface admin, Phase 0).

### Risk Mitigations

**Risque 1 — Hallucinations LLM sur documents persistés.**
Mitigations : guards structurels par type de contenu (longueur, cohérence numérique avec faits source, vocabulaire interdit : « garanti », « certifié », « validé par »), schémas Pydantic stricts pour les sorties JSON (plan d'action, verdicts), validation humaine **obligatoire** avant export pour livrables financiers à enjeu (voir Risque 10).

**Risque 2 — Dérive temporelle des référentiels.**
Mitigations : versioning explicite des référentiels (ex. `RSPO_PC@2018` vs `RSPO_PC@2024_v4.0`, `IFC_PS@2012` vs futur `IFC_PS@2028+`), snapshot propre de chaque `FundApplication` (SC-T5), `ReferentialMigration` automatique avec plan de transition notifié à l'utilisateur.

**Risque 3 — Obsolescence des coordonnées intermédiaires.**
Mitigations : table `Intermediary` avec champ `last_verified_at`, pipeline de vérification trimestriel (manuel ou automatisé), alerte admin si coordonnée utilisée > 6 mois sans vérification. Cf. P2 #18 de l'audit.

**Risque 4 — Conflit de verdicts multi-référentiels.**
Mitigations : architecture 3 couches garantit que les verdicts sont dérivés du même fait source. Tests de propriété (property-based testing) pour vérifier la non-contradiction (SC-T6).

**Risque 5 — Données sensibles exposées par les prompts LLM.**
Mitigations : anonymisation systématique PII avant envoi (SC-T10), politique de rétention stricte chez provider LLM, audit annuel du pipeline d'anonymisation.

**Risque 6 — Dossiers bancaires refusés pour non-conformité formelle.**
Mitigations : parcours de remédiation intégré (Journey 4), check-list de conformité bailleur avant soumission, pré-revue automatique par matching des critères sur le template bailleur.

**Risque 7 — Secteur informel et absence de preuves documentaires.**
Mitigations : accompagnement à la formalisation graduée (Cluster A'), faits qualitatifs attestables comme alternative aux preuves formelles (CLIP par témoignage vidéo, grief mechanism par log d'appels), acceptance levels adaptés aux fonds micro-financement (FEM SGP).

**Risque 8 — Expansion régionale future bloquée par hardcoding.**
Mitigations : architecture i18n-ready dès Phase 0 (SC-T7), table `AdminMaturityRequirement(country × level)` paramétrable, pas de présupposé UEMOA dans les schémas data.

**Risque 9 — Adoption freinée par le coût de connectivité.**
Mitigations : mode low-data mobile (Cluster D, Phase 3), PWA offline avec synchronisation différée (Phase 4), alternative SMS/WhatsApp pour notifications critiques.

**Risque 10 — Responsabilité juridique sur documents générés par IA remis aux bailleurs.**
Dispositif renforcé, obligatoire et non négociable :
- **Disclaimer explicite visible en tête ET en pied** de chaque document généré (pas seulement pied de page).
- **Signature électronique de l'utilisateur** validant son engagement sur les contenus **avant** l'export PDF final. L'action « exporter » déclenche un modal : « Je, [Nom], atteste avoir relu et valide l'ensemble du contenu généré pour soumission à [Bailleur]. Je comprends que Mefali est un assistant IA et que la responsabilité finale reste mienne. » avec case à cocher obligatoire.
- **Audit trail complet de la génération** stocké dans une nouvelle table `FundApplicationGenerationLog` : version du LLM utilisée, horodatage, prompts utilisés (anonymisés), versions de référentiels appliquées, hash du snapshot, ID utilisateur. Auditable a posteriori par un bailleur ou par Mefali.
- **Revue humaine OBLIGATOIRE** (non « recommandée ») pour livrables avec montant déclaré > 50 000 USD équivalents XOF. Workflow bloquant dans l'app : draft → revue par le user section par section → export bloqué tant que la case « relu section par section » n'est pas cochée pour chaque section. Pas de bypass possible.

### NFR Structurants (garde-fous anti-dérive)

**NFR-SOURCE-TRACKING — Traçabilité documentaire du catalogue.**
Toute entité du catalogue (`fund`, `intermediary`, `referential`, `criterion`, `pack`, `template`, `emission_factor`, `sector_weight`, `regulation_reference`) doit porter 3 champs de traçabilité **obligatoires** :
- `source_url` : URL officielle de référence (pas Wikipedia, pas « base de connaissances générale », pas « Claude training data »).
- `source_accessed_at` : date de consultation (ISO 8601).
- `source_version` : version du document référencé (ex. `IFC PS 2012`, `RSPO P&C 2024 v4.0`, `EUDR 2023/1115` modifié par `2025/2650`).

Sans ces 3 champs, l'entité reste en état **DRAFT non-publiable** (contrainte au niveau modèle de données + validation API + UI admin).

Cette exigence protège contre : dérive des données (hallucinations LLM lors de l'import), obsolescence (IFC PS révisés, RSPO 2018→2024), incohérence (admin qui invente un seuil), inaudibilité par un bailleur qui demanderait les sources utilisées.

**NFR-ADMIN-LEVELS — 3 niveaux de criticité d'édition.**
L'interface admin implémente 3 workflows d'édition selon la criticité de la donnée. Chaque entité porte un champ `edition_criticality: enum(N1, N2, N3)` qui détermine le workflow applicable.
- **N1 — Édition libre** : coordonnées intermédiaires, statuts actifs, seuils simples (âge min, montants). Effet immédiat, un seul admin autorisé.
- **N2 — Peer review** : nouveaux critères composables, packs, règles de dérivation Fact→Verdict, pondérations sectorielles. Workflow `draft` → `review` par un 2e admin → `publication`.
- **N3 — Versioning strict** : nouveaux référentiels complets (ex. `RSPO_PC@2024_v4.0` avec date d'effet 31 mai 2026, futur `IFC_PS@2028+`), migration de versions, changement de seuils de conformité réglementaire. Workflow `draft` → `review` → `test rétroactif sur snapshot` → `migration planifiée avec date d'effet`.

**Exigence — Web search ciblé avant clôture du PRD (step 11–12).**
Avant la clôture du PRD (Polish step 11 / Complete step 12), un web search ciblé doit valider que les décisions architecturales ne reposent pas sur des hallucinations pour les référentiels suivants :
- IFC Performance Standards : version en vigueur, seuils EHS par secteur
- GCF Funding Proposal template : structure actuelle
- EUDR règlement 2023/1115 : annexes, obligations PME fournisseurs UE
- RSPO P&C : **version 2024 v4.0** retenue (effective obligatoire 31 mai 2026, cf. Annexe B Web Search Light)
- Taxonomie BAD : état de structuration 2025
- Banque Mondiale ESF : ESS 1-10
- Conventions OIT fondamentales : liste et scope

Chaque fait cité dans le PRD doit porter sa source en note de bas de page ou annexe « Sources documentaires ».

**Exigence — Story Phase 0 « 9-X-catalog-sourcing-documentaire ».**
Prérequis **BLOQUANT** à toute publication publique de la plateforme : pas de mise en prod avec un catalogue non-sourcé.

Objectif : validation documentaire exhaustive de TOUS les éléments catalogue initiaux avec URL sources officielles. Alimente directement les champs `source_url` / `source_accessed_at` / `source_version` (NFR-SOURCE-TRACKING).

Catégories à valider :
- **Référentiels internationaux** : IFC PS, GCF, FEM, Proparco AIMM, BOAD SSI, BAD SSI, BM ESF, DFI Harmonized Approach, EUDR, CS3D
- **Certifications sectorielles** : RSPO, Rainforest Alliance, Fairtrade, Bonsucro, FSC, IRMA, ResponsibleSteel
- **Standards reporting** : GRI, TCFD, CDP, IRIS+, SASB
- **ISO** : 26000, 14001, 45001, 37001, 14040
- **Audits clients EU** : Sedex/SMETA, EcoVadis, SA8000, BSCI
- **Conventions OIT fondamentales** : 8 conventions
- **UN Global Compact, Principes Volontaires sur la Sécurité et les Droits de l'Homme**
- **Référentiels régionaux AO** : Charte RSE SN, Plateforme RSE CI, Label CGECI, Taxonomie BAD, ITIE
- **Réglementation nationale** : codes miniers et environnement par pays, OHADA, lois protection données, anti-corruption locales
- **Données opérationnelles** : frais RCCM par pays, facteurs d'émission électricité par réseau, SMIG, cotisations CNPS/IPRES/CNSS
- **Bailleurs et intermédiaires régionaux** : conditions actuelles BOAD/SUNREF/SIB/Ecobank/BDU/BGFI, fonds d'impact, agences d'implémentation PNUD/ONUDI/BM

Cette story s'ajoute aux 6 prérequis Phase 0 déjà listés dans le Product Scope, comme **7ème prérequis bloquant**.

## Innovation & Novel Patterns

### Detected Innovation Areas

Cinq zones d'innovation structurelle émergent de la conception, validées par le brainstorming et les journeys :

**INN-1 — Architecture ESG à trois couches (Faits → Critères → Verdicts).**
L'industrie ESG fonctionne aujourd'hui par « grilles » (ensembles de questions par référentiel). Les solutions commerciales européennes (EcoVadis, Worldfavor, Sweep, Greenly) demandent à l'utilisateur de répondre N fois aux questions équivalentes quand il vise N référentiels. Mefali casse ce modèle : les **faits atomiques** (volume d'effluents, taux de femmes employées, BOD mesuré, présence d'un mécanisme de grief…) sont saisis **une seule fois**, stockés avec leurs preuves et leur preuve documentaire, et **N référentiels dérivent automatiquement leurs verdicts** via des règles de dérivation explicites. L'innovation est d'avoir **atomisé la matière première ESG en objets réutilisables**, comme des briques Lego sémantiques.

**INN-2 — Trio PME-intermédiaire-bailleur comme objet métier de premier ordre.**
Les solutions de matching fond-entreprise existantes (quelques bases de données de fonds verts, outils de consultants) retournent une liste de fonds « théoriquement compatibles » par secteur et pays. L'innovation principale de Mefali **n'est pas l'ajout d'une dimension technique au matching, mais la modélisation du trio PME-intermédiaire-bailleur comme objet métier de premier ordre**. Dans la réalité AO, un fonds GCF n'est pas accessible à une PME isolément : il est accessible via un intermédiaire agréé (BOAD, SIB, Ecobank, BDU, BGFI…) qui a ses propres critères, son propre processus et ses propres coordonnées. Mefali expose **ce trio et ses dépendances explicitement**, là où les outils existants proposent un matching direct théoriquement compatible mais pratiquement inaccessible. Le cube 4D `maturité projet × maturité entreprise × référentiels × voie d'accès` est la matérialisation technique de cette modélisation métier ; l'objet « voie d'accès » agrège les critères intermédiaires, le canal de candidature, les prérequis spécifiques.

**INN-3 — Automatisation conversationnelle du métier de consultant ESG ouest-africain.**
Le métier de consultant ESG en AO combine : traduction des standards internationaux en exigences locales opérationnelles, identification de la voie d'accès, accompagnement à la formalisation, production de livrables bailleurs (SGES, EIES, fiches préparation). Coût d'une mission complète : 50 000 à 200 000 EUR. Mefali propose l'**automatisation de ce rôle par LLM conversationnel** sur la base d'une architecture d'agent production-ready (LangGraph + tools + RAG + guards). L'innovation n'est pas le « chatbot ESG » (qui existe) mais la **démonstration systémique qu'un agent IA peut tenir la profondeur métier du consultant AO sur l'ensemble du cycle**, incluant des livrables institutionnels comme le SGES/ESMS conforme IFC.

> **Note de prudence :** à notre connaissance à la date du PRD, aucun outil commercial identifié ne couvre la profondeur du rôle consultant ESG AO (matching + formalisation + livrables institutionnels type SGES conformes IFC) dans une architecture agent IA unique. Ce périmètre et cette profondeur seront **confirmés** par la revue du landscape concurrentiel lors de l'étape de validation documentaire (cf. « Web search ciblé » dans Domain Requirements, exigé avant clôture du PRD steps 11–12).

**INN-4 — Formalisation graduée comme gate d'accès bailleur.**
Les plateformes ESG internationales présupposent toutes une entreprise formalisée (SARL européenne, comptes audités). Or plus de 80 % du marché cible AO est partiellement informel. Mefali introduit un **parcours de formalisation graduée à 4 niveaux** (informel → RCCM+NIF → comptes+CNPS → OHADA audité) intégré au produit, avec génération d'un plan chiffré de transition. L'innovation est de traiter la formalisation non pas comme prérequis externe, mais comme **feature produit intégrée à l'expérience ESG**, avec effet miroir sur le cube bailleur (un fonds débloqué à chaque niveau atteint).

**INN-5 — Agent conversationnel dont les actions opèrent sur un catalogue dynamique extensible sans redéploiement.**
L'approche « toute feature invocable depuis le chat » (modalité secondaire validée en Step 2) combinée à l'architecture composable (packs pré-assemblés en façade, catalogue granulaire en interne) est un **pattern rare en production**. Les copilotes IA sectoriels existants (GitHub Copilot, Cursor, legal AI tools) sont soit des surcouches conversationnelles à un produit existant, soit des agents autonomes opérant sur un code figé. Mefali est un **agent conversationnel dont les actions opèrent sur un catalogue dynamique**, et où **un admin peut étendre les capacités sans redéploiement code** (nouveau référentiel, nouveau fonds, nouvel intermédiaire, nouveau pack, nouveau critère composable). La combinaison « agent IA + catalogue dynamique + interface admin typée par criticité NFR-ADMIN-LEVELS » constitue un modèle d'extension rare à ce niveau de production-readiness.

### Market Context & Competitive Landscape

**Segments adjacents et leurs limites :**

| Segment | Exemples | Limite pour Mefali |
|---|---|---|
| Plateformes ESG Enterprise européennes | EcoVadis, Worldfavor, Sweep, Greenly, Position Green | Calibrées grandes entreprises CSRD, payantes (> 10 k€/an), non adaptées PME AO, pas de matching bailleur |
| Plateformes de matching financement général | Crunchbase, CB Insights pour startups | Pas d'angle ESG ni de spécialisation AO |
| Outils de reporting GRI/TCFD | Workiva, Datamaran | Outils de compliance reporting, pas d'accompagnement de dossier bailleur |
| Plateformes de certification sectorielle | RSPO Palm Tracer, Rainforest Certification Portal | Monovalentes (un seul référentiel), pas de vue holistique |
| Consultants ESG AO traditionnels | Cabinets Deloitte, EY, PwC Afrique, boutiques locales | Coût prohibitif pour PME, lenteur (semaines à mois), non scalable |
| Solutions locales « maison » | Excel, Google Forms, relations informelles | Pas structurées, pas auditables, perte de données, zéro automatisation |

**Gap de marché confirmé :** aucun acteur n'adresse le chaînon manquant entre **PME informelle AO** et **bailleurs internationaux** avec une architecture permettant de couvrir **à la fois** la formalisation, le scoring ESG multi-référentiel, le matching bailleur avec voie d'accès et la génération de livrables conformes. Mefali vise cet espace blanc.

> **Note — carte concurrentielle à compléter.** La carte ci-dessus sera complétée lors de la phase de validation documentaire (steps 11–12) par un **web search ciblé sur les acteurs africains émergents**, notamment :
> - Startups nigérianes (54ESG, Climate Fund Managers, autres ESG/fintech durables)
> - Plateformes d'investissement d'impact AO (distinguer fonds vs outils : Adenia, Partech Africa, Janngo Capital = fonds d'impact, non des outils)
> - Initiatives publiques BCEAO / BOAD / BAD de plateformes numériques
> - Outils gratuits type Climate Finance Toolkit Banque Mondiale
> - Solutions portées par incubateurs/accélérateurs régionaux (CTIC Dakar, Orange Digital Center, Impact Hub Abidjan, Bond'Innov, MEST Africa)
>
> Si un concurrent direct est identifié lors de cette revue, retour sur le positionnement INN-3 et éventuelle révision du pitch de différenciation.

**Indicateurs de timing validés (cf. « Why Now » Exec Summary) :**
- Tipping point LLM francophones 2024–2025.
- EUDR : dates d'application définitives 30 décembre 2026 (grandes entreprises) / 30 juin 2027 (PME et micro-entreprises = cible Mefali) → force commerciale sur filières cacao/palme/coton/bois. Report supplémentaire possible (simplification review Commission UE avant 30 avril 2026) à surveiller.
- AFAC Continental Sustainable Finance Taxonomy (BAD) **validée juillet 2025 à Nairobi** → déploiement opérationnel en cours, fenêtre d'intégration immédiate pour Mefali (Phase 2 catalog sourcing).
- Maturité stack agentique (LangGraph stable, pgvector mature, tool calling production-ready).

### Validation Approach

**Validation pilote avant lancement public (Phase 1 fin de cycle MVP) :**
- **3 à 5 PME pilotes** représentatives : 1 par secteur dominant (agroalimentaire mangue/manioc Sénégal, cacao coopérative CI, palme SARL CI, artisanat/recyclage BF, transformation Bénin ou Togo). Mix niveaux administratifs (niveau 0 à 3) pour valider le parcours complet.
- **Chaque pilote doit produire au moins 1 dossier bailleur complet** (GCF, IFC, FEM SGP ou BOAD Ligne Verte selon maturité) avec revue humaine finale avant soumission réelle.
- **Mesure quantitative** : temps effectif de complétion (objectif MO-1 : quelques heures à quelques jours vs semaines consultant), taux d'acceptation dossier par le bailleur (vs benchmark régional SC-B2), nombre de référentiels couverts par fait saisi (validation INN-1).
- **Mesure qualitative** : entretiens post-utilisation structurés sur les « moments aha » (SC-U1, SC-U4, SC-U5), friction perçue sur la formalisation graduée, compréhension de la voie d'accès intermédiée.

**Clause de protection PME pilote (non négociable) :**
Les PME pilotes soumettent des VRAIS dossiers à des VRAIS bailleurs. Si Mefali produit un dossier insuffisant et qu'il est refusé, la PME porte le coût du refus (perte d'opportunité de financement, retard commercial, voire blacklisting potentiel par certains bailleurs). Par conséquent :
- **Tout dossier généré par Mefali destiné à une soumission réelle doit passer par la revue des 2 consultants ESG AO seniors AVANT soumission au bailleur.**
- **En cas de discordance significative (≥ 2 points sur l'échelle 1–5), le dossier est retravaillé par Mefali + consultants jusqu'à alignement avant soumission.**
- **Aucune PME pilote ne porte seule le risque de première itération.**
- Budget de cette revue expert **inclus dans le coût pilote** (voir SC-B-PILOTE ci-dessous).

**Validation experte indépendante :**
- Revue par **2 consultants ESG AO seniors** (cabinets locaux à identifier) sur un échantillon de 5 livrables générés par Mefali (SGES, EIES, IFC AIMM, EUDR DDS, plan d'action). Évaluation « serait-ce cohérent avec votre livrable » sur échelle 1–5 avec commentaires.
- Revue par **1 chargé de financement régional** côté bailleur (idéalement BOAD ou BAD, à défaut AFD/Proparco régional) sur la qualité d'un dossier soumis fictivement.

**Métrique business additionnelle (ajoutée à la section Success Criteria) :**
- **SC-B-PILOTE — Budget pilote** : `[à quantifier]` EUR répartis entre consultants experts seniors (~15–30 k€ estimation indicative pour 10 jours-expert cumulés), support PME pilotes, et incentives d'accompagnement. Le chargé bailleur régional est souvent disposé à revoir gratuitement par intérêt mutuel. Décision de budget à prendre lors de l'atelier stratégique avec stakeholders business (cf. note step 2c).

**Instrumentation in-product pour validation continue :**
- Dashboard interne sur SC-T6 (cohérence multi-référentiel), SC-T8 (guards LLM), MO-3 (couverture catalogue) collectés automatiquement.
- Feedback utilisateur in-app à la fin de chaque journey majeure (« est-ce utile ? », « qu'est-ce qui manque ? »).

### Risk Mitigation

**RI-1 — Cube 4D trop complexe à maintenir.**
Risque : l'explosion combinatoire (500+ critères × 50 référentiels × 8 pays × 5 maturités × 4 niveaux admin × 2 voies) rend la maintenance du catalogue insoutenable, et les requêtes trop lentes en prod.
Mitigation : dans l'architecture, la complexité est encapsulée dans l'interface admin (NFR-ADMIN-LEVELS). **Critère de déclenchement explicite du fallback** : le fallback cube 3D (voie d'accès en flag binaire directe/intermédiée sans critères intermédiaires détaillés) n'est activable **que si les tests de charge Phase 0 démontrent que le cube 4D complet dépasse SC-T3 (2 s p95 avec cache tiède) après optimisations raisonnables** (indexes composites, matérialisation partielle). Sinon, le cube 4D complet est maintenu comme vision produit non négociable — c'est un différenciateur INN-2 central, et renoncer à la voie d'accès détaillée affaiblirait le positionnement. Cache tiède agressif sur les requêtes catalogue (SC-T3). Indices composites PostgreSQL sur les dimensions principales.

**RI-2 — Architecture 3 couches : performance des dérivations de verdicts.**
Risque : dériver N verdicts depuis un fait à chaque modification dépasse 30 s (SC-T4).
Mitigation : **matérialisation des verdicts** en table dédiée (pattern cache), invalidation sélective lors des modifications de faits ou règles de dérivation, calcul batch asynchrone via file Celery en Phase Growth. Tests de charge dès Phase 1 fin de cycle (10 puis 50 puis 100 critères simultanés).

**RI-3 — Voie d'accès trop volatile (intermédiaires changent leurs critères).**
Risque : maintenance des critères intermédiaires (ex. SIB passe de 3 à 2 ans d'ancienneté) trop fréquente.
Mitigation : interface admin N1 (édition libre, effet immédiat — Journey 5 Mariam), pipeline de vérification trimestriel (SC-T11 observabilité), notifications automatiques aux utilisateurs concernés si leur voie d'accès a changé. Fallback simplifié : si la dynamique devient ingérable, simplification à 2 états (directe/intermédiée) sans critères intermédiaires détaillés (dégradation UX mais pas blocage).

**RI-4 — Automatisation du consultant : livrables insuffisamment qualitatifs.**
Risque : les dossiers générés (SGES, IFC AIMM, EIES) sont rejetés ou dévalorisés par les bailleurs parce qu'insuffisamment profonds ou techniquement incorrects.
Mitigation : guards LLM stricts (SC-T8) avec schéma Pydantic pour livrables structurés ; validation humaine OBLIGATOIRE (Risque 10 du domaine) pour livrables > 50 000 USD ; revue par 2 consultants experts pendant le pilote (Validation Approach) ; versionning du SGES pour amélioration itérative sur retours utilisateurs réels. **Si un type de livrable ne passe pas le seuil de qualité** (ex. SGES trop superficiel), **report du déblocage en Phase ultérieure** — pas de livrable bancal en prod.

**RI-5 — Formalisation graduée : taux de conversion niveau N → N+1 bas.**
Risque : les utilisateurs reçoivent un `FormalizationPlan` mais n'exécutent jamais les étapes (coût, complexité admin locale, manque de motivation), rendant MO-5 invalide.
Mitigation : chiffrage exact dans le plan (coûts en XOF), coordonnées locales précises, rappels de suivi automatisés (module 011 rappels existant), badges et gamification (module 011 existant). Si le taux reste bas malgré tout : partenariats avec des cabinets comptables / bureaux de juristes locaux pour un service d'accompagnement humain payant (post-MVP, Option 3 hybridation marketplace).

**RI-6 — Catalogue sourcé insuffisamment étanche à l'hallucination malgré NFR-SOURCE-TRACKING.**
Risque : admin qui ajoute une entrée en copie-collant depuis une source secondaire non vérifiée, invalidant la traçabilité.
Mitigation : contrôle qualité à deux niveaux (NFR-ADMIN-LEVELS N2 peer review pour critères, N3 versioning strict pour référentiels), **test automatisé CI nocturne** qui vérifie la cohérence (ex. un `source_url` doit renvoyer un document accessible HTTP 200 ; sinon alerte admin avec entity flaggée pour re-validation), audit aléatoire trimestriel par l'équipe Mefali sur un échantillon du catalogue.

## Web App + SaaS B2B Specific Requirements

### Project-Type Overview

ESG Mefali est une **web app fintech/ESG** à architecture client-serveur moderne :
- **Frontend Nuxt 4** (Vue 3 Composition API + Pinia + TailwindCSS + Chart.js) avec SSR sélectif et SPA majoritaire
- **Backend FastAPI** (Python 3.12, SQLAlchemy async, LangGraph orchestration, LangChain tools)
- **BDD PostgreSQL 16 + pgvector** pour embeddings multilingues
- **LLM provider Anthropic** via OpenRouter, streaming SSE
- **Stockage** : local `/uploads/` MVP → S3/MinIO Phase Growth

Trois modalités secondaires superposent des contraintes architecturales :
1. **SaaS B2B** : multi-tenancy logique par `Company`, quotas par user, facturation différée Phase Growth
2. **Copilot IA-first** : toute feature invocable via le chat LangGraph, actions tool calling sur le catalogue dynamique
3. **Consulting augmenté par IA** : guards LLM stricts, audit trail complet, signature électronique utilisateur sur livrables financiers

### Technical Architecture Considerations

**Architecture applicative :**
- Backend monolithe modulaire FastAPI (8 modules métier actuels : chat, documents, ESG, carbone, financement, crédit, applications, rapports, dashboard/plan, auth). Extension à 10–12 modules post-Phase 1 (projet, maturité entreprise, admin catalogue).
- Frontend Nuxt 4 avec routing automatique, composables pour logique partagée, layouts différenciés par persona.
- Orchestration LangGraph : 9–10 nœuds avec tool calling, streaming SSE natif, MemorySaver checkpointer pour reprise sur interruption.
- Communication client-serveur : REST pour CRUD + SSE pour streaming chat et événements longs.

**Scalabilité et performance :**
- Design stateless côté FastAPI (sauf LangGraph checkpointer qui persiste en BDD) → scaling horizontal possible via Kubernetes/ECS.
- PostgreSQL : design pour read-heavy avec requêtes dimensionnelles (cube 4D) optimisées par indexes composites et vues matérialisées (SC-T3).
- pgvector : index IVFFlat ou HNSW selon volume, migration vers HNSW si > 100k embeddings.
- Cache tiède applicatif (Redis Phase Growth pour sessions, catalogues chauds, résultats de matching).
- File de jobs asynchrones (Celery + Redis) en Phase Growth / Vision pour génération lourde.

**Observabilité (SC-T11) :** logs structurés JSON avec `request_id` UUID traversant frontend → FastAPI → LangGraph → tools → DB. Métriques via OpenTelemetry (validation Step 10) vers Grafana / Datadog.

### Multi-Tenancy Model (saas_b2b)

**Modèle logique :**
- Entité racine de tenant : `Company`. User rattaché à 1+ companies via `CompanyMember`.
- Toutes les données métier (`Project`, `FundApplication`, `Fact`, `FormalizationPlan`) portent une FK vers `Company`. Aucune fuite inter-tenant.
- Catalogue commun Mefali (`Fund`, `Intermediary`, `Referential`, `Pack`, templates) partagé en lecture seule, modifiable uniquement par rôle `admin_mefali`.

**Isolation technique — stratégie hybride MVP :**
- **Filtre WHERE applicatif** (SQLAlchemy session scope + dependency injection) systématique sur toutes les tables.
- **RLS PostgreSQL activé dès MVP sur les 4 tables les plus sensibles** : `companies`, `fund_applications`, `facts`, `documents`. C'est un cran supplémentaire de sécurité (pas un substitut) : si un dev oublie un WHERE, PostgreSQL refuse la ligne au niveau BDD. Conformité protection données (loi SN 2008-12, CI 2013-450) renforcée.
- **Phase Growth** : généralisation de RLS à toutes les tables, abandon progressif des filtres WHERE applicatifs.
- Chiffrement at rest sur documents uploadés, key-per-tenant évalué en Phase Growth (KMS).

**Quotas par utilisateur (partiellement livrés) :**
- Quota stockage user (livré story 9.2 — `QUOTA_BYTES_PER_USER_MB`, `QUOTA_DOCS_PER_USER`) ✅
- Rate limiting chat (livré story 9.1 — `SlowAPI @limiter.limit("30/minute")`) ✅
- Rate limiting par tool coûteux (génération PDF, SGES) : Phase Growth (P3 #30 audit)
- Quota évaluations ESG / bilans carbone / dossiers / mois : Phase Growth (facturation)

### Permissions Model (RBAC)

**Rôles utilisateur :**

| Rôle | Scope | Permissions typiques |
|---|---|---|
| `owner` / porteur principal | Un seul user par `Company` | CRUD complet sur la `Company`, gestion des membres, soumission dossiers, paiement |
| `editor` / équipe fonctionnelle | Multi-user possible par `Company` | Saisie des faits, édition profil, consultation dashboards, pas de soumission ni suppression |
| `viewer` / dirigeant | Multi-user possible | Lecture seule sur Company, dashboards, dossiers |
| `auditor` | Scope limité dans le temps (token d'accès expirable) | Lecture complète sur périmètre défini + annotation/commentaires sur faits et livrables + pas d'édition ni de soumission |
| `admin_mefali` | Transverse système | CRUD catalogue (référentiels, fonds, intermédiaires, packs, templates) selon NFR-ADMIN-LEVELS |
| `admin_super` | Transverse système | Gestion utilisateurs, quotas, audit logs, configuration système |

**Rôle `auditor` — usages types :**
- Akissi (SARL palme) donne accès auditor à son cabinet comptable pour valider les bilans en préparation dossier IFC (durée 30 j).
- Moussa donne accès auditor à un conseiller ESG local pour revue EIES avant soumission (durée 15 j).
- Phase Vision : ce rôle est le socle pour le futur marketplace consultants (Option 3 hybridation).

Créé dans ce PRD pour préparer Vision, utilisation légère en MVP (cas optionnels).

**Rôles projet-spécifiques (Cluster A) — enum extensible par admin N2 :**
- Set initial fixé : `porteur_principal`, `co_porteur`, `beneficiaire`.
- Un `admin_mefali` peut ajouter un nouveau rôle à la liste centralisée via interface admin N2 (peer review) si un besoin métier documenté émerge — exemples : `financial_sponsor` pour montages syndiqués, `community_representative` pour consultations CLIP en secteur extractif, `project_manager` pour coordinateur dédié.
- Chaque rôle porte des permissions configurables (lecture/écriture par champ).
- Évite la rigidité sans basculer dans le chaos.

**Workflow admin catalogue (NFR-ADMIN-LEVELS) :**
- N1 édition libre (un admin, effet immédiat) : coordonnées intermédiaires, seuils simples, statuts.
- N2 peer review (draft → review 2e admin → publication) : critères composables, packs, règles de dérivation.
- N3 versioning strict (draft → review → test rétroactif sur snapshot → migration datée) : nouveaux référentiels, migration de versions, seuils de conformité.

### Authentication & Authorization

**Authentification :**
- MVP : JWT stateless avec refresh token (pattern actuel du projet).
- Évaluation SSO OAuth2 en Phase Growth (Google, Microsoft).
- Passwordless (magic link) évalué pour onboarding PME informelles sans email pro stable.

**MFA — niveaux différenciés :**
- **OBLIGATOIRE en permanence** : `admin_mefali`, `admin_super`.
- **FORTEMENT RECOMMANDÉ mais opt-in** : `owner` (avec incitation UI et badge sécurité si activé).
- **STEP-UP MFA obligatoire sur actions à risque élevé** (tous rôles concernés) :
  - Soumission `FundApplication` avec montant déclaré > 50 000 USD
  - Signature électronique sur livrable bailleur (Risque 10)
  - Modification des données bancaires de l'entreprise
  - Changement de mot de passe / email de contact
  - Suppression de documents ou de projets
  - Export de données sensibles

Le step-up MFA permet la protection forte aux moments critiques sans friction permanente.

**Session :**
- Renouvellement JWT transparent pendant le streaming (déjà livré story 7.2 PRD 019).
- Durée d'idle session : 4 heures (confirmation Step 10).
- Invalidation immédiate sur logout, changement de mot de passe, révocation admin.

### Integration Interfaces

**Intégrations existantes (à étendre) :**
- **OpenRouter / Anthropic** : LLM streaming, timeout 60 s, retry avec backoff exponentiel (livré spec 015).
- **OpenAI Embeddings API** : `text-embedding-3-small` pour pgvector.
- **Tesseract OCR** : bilingue fra+eng (story 9.4), extension langues Vision.
- **WeasyPrint + Jinja2** : PDF pour rapports, dossiers, SGES.
- **python-docx** : export DOCX éditable.

**Intégrations à ajouter (Phase 1–2) :**
- **Email transactionnel** : **provider reporté Step 10 NFR**. Options candidates à évaluer : Mailgun (bon pour AO), Amazon SES (économique si infra AWS), Postmark (fiabilité), Resend (moderne). Critères de choix : coût, taux de délivrance en AO, support SMTP direct, conformité protection données.
- **Stockage S3-compatible** : migration Phase Growth.

**Intégrations Phase Growth :**
- **Agrégateur mobile money / cartes** (CinetPay ou Paystack, à trancher).
- **Stripe** pour paiements internationaux.
- **SMS / WhatsApp** : notifications PME à connectivité email limitée.

**Intégrations Vision (non engagées) :**
- APIs bailleurs (GCF, FEM, BAD Connect) — nécessite partenariats.
- Registres publics RCCM régionaux CEDEAO.

### Frontend-Specific Considerations

**Design responsive :**
- Premier écran mobile (≤ 480 px) pour PME solos en informel (Journey 1 Aminata).
- Desktop optimisé pour utilisateurs avancés multi-projets (Journey 2 Moussa) et admin (Journey 5 Mariam).
- Tablet intermédiaire supporté via media queries.

**Dark mode (CONVENTION PROJET OBLIGATOIRE) :**
- Chaque composant, page, layout compatible dark mode via variantes `dark:` Tailwind.
- Convention déjà enforcée dans le projet existant (cf. CLAUDE.md), étendue à toutes les nouvelles features.
- Thème géré par `stores/ui.ts` (persistance localStorage).

**Internationalisation (SC-T7) — locale simplifiée :**
- **Locale utilisateur unique : `fr`** (ou `fr-FR` si i18n technique l'exige). Pas de variantes par pays UEMOA (français parlé très proche entre pays, sur-ingénierie inutile).
- **Paramétrage par pays géré indépendamment via tables data-driven** :
  - `AdminMaturityRequirement(country × level)` → références réglementaires (NINEA vs IFU vs NIF)
  - `regulation_reference` → montants par défaut (SMIG, frais RCCM, cotisations sociales)
  - Table `Country` enrichie → coordonnées (tribunaux, bailleurs nationaux, intermédiaires régionaux)
  - Libellés métier pays-spécifiques (ex. « patente » vs « taxe professionnelle »)
- **Séparation claire** : `locale` = langue, `country` = data paramétrée.
- **Phase Vision (expansion anglophone)** : ajout locale `en` au même pattern, avec variantes si nécessaire à ce moment-là.

**Performance web :**
- Lazy loading composants lourds (Chart.js, Toast UI Editor).
- Code splitting par route.
- Optimisation images : WebP + srcset.
- Mode low-data (Phase 3 Cluster D) : réduction images, graphiques allégés ou tableaux uniquement.
- PWA offline (Phase 4) : service worker pour cache critique + IndexedDB pour queue offline.

**Accessibilité :**
- ARIA roles conformes (radiogroup, checkbox, aria-checked, aria-describedby — livrés interactive widgets spec 018).
- Navigation clavier complète (livrée widget flottant spec 019 story 1.7).
- Contraste conforme WCAG AA minimum.

### SaaS B2B Specific Considerations

**Onboarding multi-étapes :**
- Création Company → choix du niveau de formalisation déclaratif → profil entreprise → premier projet optionnel.
- Workflow adapté à la maturité : Aminata niveau 0 suit un parcours très progressif ; Akissi niveau 3 peut tout saisir en une session.

**Facturation (Phase Growth, Vision) :**
- Pas de facturation MVP (freemium décidé Step 5).
- Phase Growth : modèle freemium avec tier payant pour quotas étendus, templates premium (GCF complet, IFC AIMM full), export DOCX éditable, accès prioritaire au support.
- Phase Vision : marketplace consultants (Option 3 hybridation) avec commission sur interventions facturées.

**Support utilisateur :**
- FAQ in-app dans la plateforme (Phase 2).
- Chat de support différencié du chat IA produit (pour ne pas confondre l'aide produit avec l'assistant ESG).
- Escalation vers support humain sur demande (Phase Growth).

**Admin panel :**
- Interface Mefali Admin livrée en Phase 0 (prérequis bloquant).
- Gestion catalogue (référentiels, fonds, intermédiaires, packs, templates, critères, faits, règles de dérivation) avec workflow N1/N2/N3.
- Gestion utilisateurs Mefali (création admin, quotas tenant, suspension, audit logs).
- Observabilité (dashboard monitoring) intégré.

### Data Residency & Hébergement (CRITIQUE — compliance AO)

Les lois SN 2008-12 et CI 2013-450 sur la protection des données personnelles imposent des contraintes sur le transfert de données hors territoire national. Décision data residency **à trancher en Step 10 NFR** entre :

- **Option A — Hébergement EU** (AWS EU-West-1 Irlande ou EU-West-3 Paris) : disponibilité/performance éprouvée, proximité raisonnable avec AO, latence acceptable. Nécessite garanties contractuelles conformes aux lois SN/CI/CEDEAO sur transfert de données + consentement explicite utilisateur.
- **Option B — Hébergement AWS Afrique** (AWS Cape Town) : conformité locale facilitée, latence AO meilleure, mais écosystème services plus restreint, coût plus élevé.
- **Option C — Provider local AO** (Orange Business Services CI, Sonatel SN) : alignement réglementaire optimal, mais maturité infrastructure parfois limitée pour stack containers + managed services.

**Exigence transverse (non négociable quelle que soit l'option) :** les documents classés « données sensibles » (bilans, RCCM, IFU, pièces identité) doivent avoir leur localisation documentée et auditable. Tout transfert hors zone UEMOA/CEDEAO nécessite trace et consentement utilisateur.

### Gestion des Secrets (critique)

- **Jamais de secrets en dur** dans le code ou committés (lint obligatoire via pre-commit + détection automatique type `truffleHog`, `detect-secrets`).
- **Variables d'environnement pour MVP** (+ `.env.example` documenté, jamais `.env` committé).
- **Secret Manager** (AWS Secrets Manager, HashiCorp Vault ou équivalent) en Phase Growth.
- **Rotation documentée** pour les secrets critiques (API keys LLM, DB credentials, JWT secret) : rotation trimestrielle minimum.
- **Pas de secrets dans les logs applicatifs** (enforcement via structured logging avec anonymisation automatique des champs sensibles).

### Backup Strategy & Disaster Recovery (exigences de base)

Détails complets en Step 10 NFR, mais exigences à acter dès maintenant :

- **Sauvegardes BDD PostgreSQL + pgvector** :
  - Incrémentales quotidiennes
  - Complètes hebdomadaires
  - Rétention 30 jours en chaud, 1 an archivé
  - Test de restauration trimestriel documenté

- **Sauvegardes fichiers uploadés (documents PME)** :
  - Réplication géographique (2 AZ minimum)
  - Rétention alignée sur politique de rétention documents (5 ans profil + 10 ans pour SGES/ESMS)

- **RTO (Recovery Time Objective) cible MVP** : 4 heures (récupération après panne majeure).
- **RPO (Recovery Point Objective) cible MVP** : 24 heures max (perte de données tolérée).
- **Plan de continuité documenté** avec runbooks d'incident.

### Implementation Considerations

**Migration de l'existant (Cluster A) :**
- Le modèle actuel est `Company` centré (mono-projet implicite). Migration vers `Company × Project` N:N nécessite :
  1. Création des nouvelles tables `Project`, `ProjectMembership`, `FundApplication`, `CompanyProjection`, `ProjectSnapshot`.
  2. Migration des `Company` existantes : pour chaque `Company`, création d'un `Project` default avec `lifecycle_state = idée`. Scores ESG / bilans carbone / dossiers existants rattachés à ce projet default.
  3. Refactoring progressif des services pour opérer sur `Project` plutôt que `Company` directement, avec fallback vers le projet default pendant la transition.

**Feature flag `ENABLE_PROJECT_MODEL` + cleanup obligatoire :**
- Flag activé pendant la migration Phase 1 Cluster A. À chaque module migré, le flag est vérifié.
- **OBLIGATION cleanup** : story dédiée en fin de Phase 1 (ex. `11-X-cleanup-feature-flag-project-model`) pour éviter le « flag permanent » qui pollue le code indéfiniment (anti-pattern observé dans le projet avec `profiling_node` — dette P1 #3 audit).
- Tests de régression obligatoires dans les deux modes (flag on/off) pendant la migration. Une fois le flag retiré, les tests passent à mode unique.

**Compatibilité avec les modules existants :**
- Module **chat** (spec 002–018) : étendre avec contexte projet actif (signal PRD 2 — `active_project`).
- Module **documents** (spec 004) : OCR existant réutilisé pour validation niveau admin (Cluster A').
- Module **ESG** (spec 005) : refactoring majeur pour basculer vers architecture 3 couches (Cluster B).
- Module **carbone** (spec 007) : extension pour adaptation climatique physique TCFD.
- Module **financement** (spec 008) : base pour le cube 4D (12 fonds + 14 intermédiaires existants).
- Module **applications** (spec 009) : refactoring pour supporter le moteur de livrables multi-destinataires (Cluster C).
- Module **action_plan / dashboard** (spec 011) : extension rappels pour `FormalizationPlan`, renouvellement certifs, MàJ référentiel.

**Compliance avec conventions projet (cf. CLAUDE.md) :**
- Code en anglais (variables, fonctions, classes).
- Commentaires en français.
- UI/UX en français.
- snake_case Python, PascalCase composants Vue (pas de préfixe dossier).
- Structure Nuxt 4 : tous fichiers source sous `app/`.
- Dark mode obligatoire sur tous composants.
- Réutilisabilité composants UI : vérifier avant création, extraire patterns répétés (> 2 fois), privilégier composition via slots/props.
- Migrations Alembic, tables snake_case pluriel.
- Environnement Python venv obligatoire, jamais d'install globale.

## Project Scoping & Phased Development (consolidation stratégique)

### MVP Strategy & Philosophy

**MVP Approach retenu : Problem-Solving MVP + Experience MVP hybride.**

Hybride justifié par le public cible :
- **Problem-solving prioritaire** : les PME doivent pouvoir résoudre un problème concret (« obtenir un dossier GCF bancable sans consultant ») dès le MVP. Sans cela, le produit n'a pas de raison d'être.
- **Experience minimum acceptable** : le public inclut des PME informelles mobile-only, peu technophiles — un MVP uniquement fonctionnel qui demande de la tolérance UX tuerait l'adoption. L'onboarding doit être guidé, le copilot IA doit tenir sa promesse conversationnelle, les frictions critiques doivent être éliminées (friction = abandon irréversible pour ce public).

**Ce que le MVP PROUVE (validation learning) :**
1. Une PME ouest-africaine, seule, peut générer un dossier bancable conforme pour un bailleur international majeur — accepté comme recevable par le bailleur (MO-1, SC-B2).
2. Le cube 4D avec voie d'accès apporte une valeur mesurable par rapport à un matching simple secteur × pays (SC-U1, INN-2).
3. L'architecture 3 couches ESG produit des verdicts cohérents multi-référentiels sans re-saisie (SC-U4, SC-T6).
4. La formalisation graduée débloquée à chaque niveau génère un taux de progression non trivial (MO-5).

**Resource Requirements estimés (MVP Phase 0 + Phase 1) :**
- Équipe Dev : 2–3 backend (Python/FastAPI/LangGraph expérimentés, 1 senior), 1–2 frontend (Nuxt 4/Vue 3), 0.5 DevOps (infra, CI, observabilité), **1 FTE QA** (requis pour brownfield avec 1100+ tests existants + nouveau scope massif — enforcement SC-T2 zero failing tests on main).
- Équipe Produit : 1 PM (Angenor / équivalent), 0.3 designer UX (mobile-first AO).
- Équipe Data/Métier : 0.5 ESG data owner (contribue au sourcing documentaire Phase 0).
- **Ressources ponctuelles additionnelles OBLIGATOIRES (budget à prévoir ~10–15 k€)** :
  - **Consultant sécurité indépendant** — 5 jours pour revue architecture Phase 0 (data residency, RLS, chiffrement, gestion secrets). Audit avant mise en prod.
  - **Juriste ESG ou avocat IT** — 2–3 jours pour validation des disclaimers IA, clauses protection données, conformité lois SN 2008-12 / CI 2013-450, clauses de responsabilité sur livrables IA.
  - **Consultant accessibilité (WCAG)** — 1–2 jours pour audit UX avant déploiement, cohérent avec Phase 3 mode low-data.
  - **2 consultants ESG AO seniors** — pour la story `catalog-sourcing-documentaire` Phase 0 + validation pilote Phase 1 fin (budget SC-B-PILOTE à quantifier).

**Durée Phase 0 + Phase 1 — calendrier réaliste avec buffer :**
- **Calendrier idéal** (équipe 100 % disponible, zéro imprévu, pas de rework) : 4–6 mois.
- **Calendrier réaliste** (buffer MVP brownfield standard +20–30 % pour imprévus, maladie, rework, découvertes tech) : **5–7 mois** attendus en production.
- **Communication externe (clients, bailleurs, stakeholders)** : 6–8 mois avec jalon intermédiaire Phase 0 close à T+6 semaines (signal de progression précoce).
- **Re-validation obligatoire** de l'estimation à la fin de Phase 0 (T+6 semaines) avec données réelles de vélocité pour affiner Phase 1.

### MVP Feature Set (Phase 1) — boundaries explicites

**Core User Journeys supportés au MVP :**
- **Journey 1 (Aminata, solo informel → voie directe)** — support complet Phase 1.
- **Journey 2 (Moussa, coopérative multi-projets → voie intermédiée)** — support complet Phase 1.
- **Journey 3 (Akissi, PME OHADA → voie mixte + SGES)** — cube 4D + architecture 3 couches + dossier IFC AIMM + **SGES/ESMS en BETA Phase 1** (voir encadré ci-dessous).
- **Journey 4 (Ibrahim, projet refusé → remédiation)** — support complet Phase 1.
- **Journey 5 (Mariam, admin catalogue)** — support complet Phase 0 (prérequis bloquant).

**Encadré — SGES/ESMS en Phase 1 BETA + Phase 2 GA (compromis) :**

Le SGES/ESMS est la value prop la plus forte du Journey 3 Akissi (contrepoids direct aux 35 000 EUR d'un cabinet européen). Reporter entièrement en Phase 2 priverait le MVP de ce différenciateur central. Le compromis retenu :

**Phase 1 BETA — contraintes fortes non négociables :**
- **Flag BETA visible** sur le livrable généré.
- **Disclaimer explicite en tête ET en pied** : « Document généré en version BETA par IA — revue humaine experte obligatoire avant soumission bailleur. »
- **Revue humaine OBLIGATOIRE** (pas « recommandée ») par consultant ESG AO certifié avant tout export final — workflow bloquant dans l'app, pas de bypass.
- **Périmètre BETA restreint** : politique E&S + procédures opérationnelles essentielles + registre des risques catégorisé IFC PS1–PS8. PAS le grief mechanism complet, PAS les plans de réinstallation (PAR/RAP).
- **Instrumentation lourde** : chaque génération SGES BETA est taggée avec métadonnées qualité (LLM version, guards passés, référentiels utilisés, temps de génération, nombre de passes).
- **Feedback obligatoire du consultant réviseur** (template de revue) → alimenté en amélioration itérative.

**Phase 2 GA (General Availability) — passage hors BETA après :**
- Minimum 10 revues expertes positives (score ≥ 4/5 sur échelle qualité).
- Grief mechanism complet ajouté.
- Extension aux PAR/RAP pour secteurs spécifiques (extractif, grand agro).
- Retrait du flag BETA et du workflow de revue obligatoire (revue reste fortement recommandée en niveau N3).

Ce compromis permet de valider la value prop SGES dès le MVP tout en protégeant la qualité et les pilotes.

**Must-Have capabilities MVP (Phase 0 + Phase 1 strictes) :**

| Capability | Phase | Justification must-have |
|---|---|---|
| Interface admin catalogue (référentiels, fonds, intermédiaires, packs) | 0 | Sans cela, le projet est bloqué par hard-coding (signal PRD 1 audit) |
| Story `catalog-sourcing-documentaire` | 0 | Sans cela, risque de mise en prod avec catalogue non-sourcé (NFR-SOURCE-TRACKING) |
| Framework d'injection d'instructions unifié | 0 | Saturation du pattern prompts directifs (signal 3 audit) |
| Enforcement `active_project` + `active_module` | 0 | Multi-projets impossible sans cela |
| Registre blocs visuels extensibles | 0 | Dashboard enrichi impossible sans cela |
| Snapshot propre systématique | 0 | Audit bailleur impossible sans immutabilité snapshot |
| RAG transversal ≥ 5 modules sur 8 | 0 | Promesse FR-005 spec 009 non tenue aujourd'hui |
| Modèle `Company × Project` N:N | 1 | Cluster A racine, tout en dépend |
| Modèle `AdminMaturityLevel` 4 niveaux + `FormalizationPlan` | 1 | 80 % du marché cible est informel — sans cela, MVP inadopté |
| Architecture 3 couches ESG (Faits / Critères / Verdicts) | 1 | Cluster B, différenciateur INN-1 |
| Catalogue initial : IFC PS + EUDR + grille Mefali + 3 packs (IFC Bancable, EUDR-DDS, Artisan Minimal) | 1 | Juste assez pour prouver la valeur sur les 2 premiers journeys |
| Cube 4D opérationnel (projet × entreprise × référentiel × voie d'accès) | 1 | Différenciateur INN-2 |
| **SGES/ESMS BETA** (périmètre restreint + revue humaine obligatoire) | 1 | Value prop du Journey 3 Akissi, compromis BETA + GA |
| Guards LLM actifs sur documents persistés | 1 | Risque 10 (responsabilité IA) — non négociable |
| Protection données (RLS partiel, chiffrement at rest, anonymisation PII) | 1 | Conformité lois SN/CI — non déployable sinon |
| Observabilité minimale (tools instrumentés + logs JSON + alerting) | 1 | SC-T11 — sans observabilité, impossible de piloter la qualité |
| Signature électronique utilisateur + audit trail `FundApplicationGenerationLog` | 1 | Risque 10 renforcé — non négociable |

**Explicitly NOT in MVP (reportés en Phase 2+) :**
- **SGES/ESMS GA** (grief mechanism complet, PAR/RAP, retrait flag BETA) → Phase 2
- Moteur complet de livrables multi-destinataires (Cluster C — Phase 2)
- Certifications sectorielles RSPO / Rainforest / ISO 14001 (Phase 2)
- Reporting GRI / TCFD / CDP (Phase 3–4)
- Dashboard enrichi avec 11 blocs visuels (Phase 3)
- Mode mobile low-data / PWA offline (Phases 3–4)
- Formation par rôle (Phase 4)
- Extension Chrome (Phase 4)
- Multi-tenant consultant (Option 3 Vision)
- Facturation (Phase Growth)
- APIs bailleurs (Vision)

### Nice-to-Have Analysis

Features « pourraient améliorer MVP » mais **non essentielles** pour valider la thèse. Inclure **uniquement si** le budget Phase 1 n'est pas intégralement consommé par les must-have :
- Onboarding gamifié (badges formalisation, levels, progression visuelle)
- FAQ in-app contextuelle
- Export CSV brut des faits
- Notifications email de rappel (dépendant provider email Step 10)
- Support multi-thèmes dashboard (au-delà du dark/light obligatoire)

### Roadmap progressif consolidé (référence Step 3 Product Scope)

**Phase 0 — Dettes P1 transverses + Interface admin + Catalog sourcing** (bloquant, 7 prérequis).
**Phase 1 — Cube 4D + ESG 3 couches + Formalisation graduée + SGES BETA** (MVP cœur).
**Phase 2 — Moteur livrables + SGES GA + extension catalogue P1** (Growth).
**Phase 3 — UX enrichi + renforcements AO profonds** (Growth).
**Phase 4 — Catalogue étendu + personnalisation** (Growth).
**Phase 5 — Vision** (consultant marketplace, expansion anglophone, APIs bailleurs, signatures eIDAS, Celery).

### Risk Mitigation Strategy (consolidée — techniques + marché + ressource)

**Risques techniques :**
- **RT-1 Performance cube 4D** — critère déclenchement fallback cube 3D explicite (RI-1). Tests de charge dès Phase 0. Index composites, cache tiède.
- **RT-2 Qualité livrables LLM** — guards structurels + schéma Pydantic + signature utilisateur + audit trail + revue humaine obligatoire > 50 k USD + report livrable si qualité insuffisante (RI-4).
- **RT-3 Migration brownfield** — feature flag `ENABLE_PROJECT_MODEL` avec cleanup obligatoire, tests de régression dans les deux modes pendant la migration.
- **RT-4 Intégrité catalogue** — NFR-SOURCE-TRACKING obligatoire + test CI nocturne HTTP 200 sur `source_url` + audit trimestriel.
- **RT-5 Compliance données AO** — data residency tranchée Step 10 + RLS partiel dès MVP + anonymisation PII avant LLM + chiffrement at rest.

**Risques marché :**
- **RM-1 Adoption faible par PME informelles** — Journey 1 (Aminata) soigneusement validé en pilote, onboarding progressif avec plan de formalisation chiffré, alternative SMS/WhatsApp dès Phase 2.
- **RM-2 Rejet livrables par bailleurs** — validation pilote 3–5 PME avec revue experte obligatoire AVANT soumission réelle (clause protection PME pilote), guards qualité, signature utilisateur sur export.
- **RM-3 Concurrent direct apparaît sur segment** — web search ciblé Step 11–12 avant publication, revisite INN-3 si découverte d'un outil couvrant le même périmètre. Avantage de base validée (18 specs, 1100+ tests, 8 modules opérationnels) — difficile à rattraper.
- **RM-4 Réglementations AO évoluent plus vite que prévu** — NFR-ADMIN-LEVELS N3 versioning strict, migration automatique, data-driven via tables BDD (pas de redéploiement).
- **RM-5 Partenariats institutionnels retardés (SC-B3)** — SLA relaxé (MOU T+9 mois, end-to-end T+15 mois), story dédiée Business Development à ouvrir dès Phase 1 fin de cycle.
- **RM-6 Dépendance LLM provider (Anthropic/OpenRouter) — risque élevé :**
  - **Abstraction layer applicative** (pattern Provider déjà partiel via OpenRouter) : permettre le switch vers un autre provider en < 2 semaines.
  - **Suivi continu** des conditions d'utilisation (terms of service, politique d'usage des données, pricing).
  - **Backup provider configuré** (fallback vers OpenAI, Mistral ou provider régional si émergence) même si non utilisé en production quotidienne.
  - **Budget LLM surveillé** (alerting sur dépassement de seuil mensuel).
  - **Plan de continuité documenté** : que faire si OpenRouter subit outage > 24 h ? (dégradation gracieuse : désactivation chat, maintien des fonctions CRUD).
- **RM-7 Incident sécurité / data breach — risque existentiel :**
  - Couche technique déjà couverte (RLS partiel, chiffrement at rest, anonymisation PII, audit trail, rétention contrôlée).
  - **Plan de réponse à incident (IRP)** documenté et testé (tabletop exercise trimestriel).
  - **Cyber insurance** évaluée en Phase Growth.
  - **Communication d'incident préparée** (template notification user, notification autorité contrôle SN/CI).
  - **Bug bounty léger** ou programme responsible disclosure en Phase Growth.
  - **Pen test externe OBLIGATOIRE** avant toute ouverture à un premier pilote avec PME réelle (soumission à vrai bailleur = données critiques exposées).

  Ces 2 risques (RM-6, RM-7) ne peuvent pas être « mitigés » au sens classique — ils nécessitent une **préparation organisationnelle**, pas seulement technique.

**Risques ressource :**
- **RR-1 Budget Dev insuffisant** — priorisation stricte des must-have Phase 0 + Phase 1, report sans honte des nice-to-have.
- **RR-2 Manque d'expertise ESG interne** — contractualiser 2 consultants ESG AO seniors pour `catalog-sourcing-documentaire` et validation pilote (budget SC-B-PILOTE).
- **RR-3 Perte de contributeurs clés** — documentation rigoureuse (CLAUDE.md étendu), pair programming, tests extensifs.
- **RR-4 Dette technique qui ralentit** — `zero failing tests on main` maintenu, dettes P1 audit résolues, cleanup feature flags obligatoire.
- **RR-5 Dérive fonctionnelle (scope creep)** — la section « Explicitly NOT in MVP » fait foi. Tout ajout en Phase 1 nécessite arbitrage explicite documenté dans un journal de décisions.

### Stratégie de contingence (plan dégradé)

**Triggers d'activation du plan dégradé (l'un des suivants suffit) :**
- Équipe réelle < 70 % de l'estimation initiale à T+2 mois (ex. 1 backend au lieu de 2–3).
- Ratio story done/pending < 50 % à T+3 mois.
- 2+ stories P1 Phase 1 bloquées > 3 semaines consécutives sur même cause racine.
- Budget consommé > 80 % à mi-Phase 1 sans avancement cohérent.

**En cas d'activation, session de re-planification OBLIGATOIRE** avec stakeholders produit + dev + business, pour décider :
- Périmètre dégradé précis (Journey 1 seul ? Catalogue réduit ?).
- Timeline re-projetée.
- Conséquences sur la thèse produit (quels différenciateurs INN sacrifiés ?).

**Le plan dégradé n'est PAS activé silencieusement** — décision explicite documentée.

**Plan dégradé MVP (si équipe réduite à 1–2 devs et tous triggers allumés) :**
- Périmètre ultra-réduit : Journey 1 (Aminata) uniquement, voie directe simple (pas de voie intermédiée Phase 1).
- Catalogue initial réduit à 1 référentiel (IFC PS) + 1 pack (Artisan Minimal) + 1 template (GCF Funding Proposal Small Grant).
- Cube 2D (projet × fonds, sans maturité entreprise ni voie d'accès) puis évolution.
- Report Cluster A' entier en Phase 2 (acceptation d'une adoption réduite à ~20 % au lieu de 80 %).
- Retour à architecture 1 couche ESG (critères directs, pas de 3 couches) puis migration.

Ce plan dégradé **n'est pas la vision cible** mais un mode survie documenté. Si activé, re-plan complet après Phase 1 dégradée pour remettre en question la thèse produit. **À éviter autant que possible** — sacrifier INN-1, INN-2 ou INN-4 affaiblit le différenciateur fondamental.

## Functional Requirements

> **Capability Contract — binding :** toute feature non listée ici n'existera pas dans le produit final. Cette section est la source de vérité pour UX, architecture, et breakdown en épics/stories.
>
> **Actors référencés :** PME User (rôles `owner` / `editor` / `viewer`), Auditor (accès temporaire avec token expirable), Admin Mefali, Admin Super, System (capabilities automatiques).
>
> **Total : 71 FR répartis en 9 capability areas.**

### Company & Project Management

- **FR1** : PME User (owner) can create a Company with basic profile (nom, secteur, pays, taille, filière export éventuelle).
- **FR2** : PME User (owner) can invite additional users to the Company with specific roles (editor, viewer, auditor).
- **FR3** : PME User (owner) can revoke access of any user (including auditor) at any time.
- **FR4** : PME User can create one or multiple Projects linked to a Company (cluster A).
- **FR5** : PME User can define a Project lifecycle state (idée / faisabilité / bancable / exécution / achevé) and update it over time.
- **FR6** : PME User can declare a Project as porté by one Company (solo) or by multiple Companies (consortium) via `ProjectMembership` with assignable roles.
- **FR7** : Admin Mefali can add new project-membership roles beyond the initial enum (`porteur_principal`, `co_porteur`, `beneficiaire`) via N2 workflow.
- **FR8** : PME User can attach project members to a beneficiary profile aggregate (coopérative cas — `BeneficiaryProfile` with genre, revenus, taux formalisation).
- **FR9** : PME User can bulk-import beneficiary profiles or project members via CSV or Excel template with validation and per-row error reporting, to support consortium cases where dozens or hundreds of beneficiaries must be registered (Journey 2 Moussa : 152 producteurs COOPRACA).
- **FR10** : System can generate a `CompanyProjection` (vue curée du profil entreprise) per Fund targeted, to support strategic positioning.

### Administrative Maturity Management (formalisation graduée)

- **FR11** : PME User can self-declare their current administrative maturity level among 4 levels (informel / RCCM+NIF / comptes+CNPS / OHADA audité).
- **FR12** : System can validate declared maturity level via OCR of uploaded supporting documents (RCCM, NINEA/IFU, comptes, bilans audités).
- **FR13** : System can generate a `FormalizationPlan` from current level to next level, with estimated cost in XOF, estimated duration, and country-specific coordinates (tribunal de commerce, bureau fiscal, caisse sociale).
- **FR14** : PME User can follow the `FormalizationPlan` progress and mark steps as done with uploaded proof.
- **FR15** : System can auto-reclassify the maturity level when all required documents for the next level are validated.
- **FR16** : Admin Mefali can maintain `AdminMaturityRequirement(country × level)` for each country in scope (UEMOA/CEDEAO francophone).

### ESG Multi-Referential Assessment (architecture 3 couches)

- **FR17** : PME User can record atomic facts (quantitatifs ou qualitatifs attestables) with their evidence documents.
- **FR18** : PME User can attest qualitative facts via multiple evidence types : document upload (PDF, image, scan), video testimony (pour CLIP en contexte extractif/agricole), déclaration officielle sur l'honneur avec signature électronique, signature de témoin (grief mechanism compliance). Alternative aux preuves formelles pour le marché informel AO.
- **FR19** : System can version facts temporally (valid_until, historique des mesures).
- **FR20** : System can automatically derive verdicts (PASS / FAIL / REPORTED / N/A) for multiple referentials from a single set of facts, via rules of dérivation.
- **FR21** : System can trace each verdict back to its source facts and applied rules (justification auditable).
- **FR22** : PME User can select a Pack (pré-assemblé façade) that activates a contextual subset of criteria and their weighting (ex. Pack IFC Bancable, Pack EUDR-DDS, Pack Artisan Minimal).
- **FR23** : System can compute a global ESG score weighted across active referentials, plus drill-down per referential.
- **FR24** : Admin Mefali can define and maintain atomic facts, composable criteria, decision rules, packs, and referentials with versioning (N1/N2/N3 workflows).
- **FR25** : Admin Mefali can publish a new referential version and trigger a `ReferentialMigration` with plan de transition for affected users.
- **FR26** : PME User can access a comparative view of scoring for the same facts across different referentials (Journey 3 Akissi use case).

### Funding Matching (Cube 4D)

- **FR27** : PME User can query the cube 4D matcher to receive Fund recommendations filtered by `project maturity × company maturity × required referentials × access route`.
- **FR28** : System can display for each matched Fund the concrete access route: direct submission OR identified intermediary with prerequisites and updated coordinates.
- **FR29** : System can display intermediate-specific criteria superposed on Fund criteria (ex. SIB min 2 years ancienneté, on top of BOAD Ligne Verte requirements).
- **FR30** : PME User can create a `FundApplication` targeting a specific Fund via a specific access route.
- **FR31** : PME User can maintain multiple `FundApplication` for the same Project (different Funds, different calibrations) without duplicating underlying facts.
- **FR32** : PME User can track `FundApplication` lifecycle status through its full path: `draft` → `snapshot_frozen` → `signed` → `exported` → `submitted_to_bailleur` (déclaré par user avec date) → `in_review` → `accepted` | `rejected` | `withdrawn`. Each status transition is timestamped and logged. User can add notes at each step (ex. « soumission réelle via portail BOAD le 15 juin, référence #XYZ »).
- **FR33** : System can archive a rejected `FundApplication` with its rejection motive, and propose a remediation path (re-matching with adjusted criteria — Journey 4 Ibrahim).
- **FR34** : System can notify affected PME Users via in-app alert when a referential, pack, or criterion they currently use in an active `FundApplication` is modified, offering them the choice to stay on the previous version (snapshot préservé) or migrate to the new version.
- **FR35** : Admin Mefali can update Fund coordinates, Intermediary criteria, and Fund-Intermediary liaisons in real-time (N1 workflow) without redeploying.

### Document Generation & Deliverables

- **FR36** : System can generate a bailleur-compliant PDF deliverable from facts, verdicts, and calibrated narratives (templates: GCF Funding Proposal, IFC AIMM Report, EUDR DDS, EIES Bailleur Cat B, Proparco AIMM, SGES/ESMS BETA Phase 1).
- **FR37** : System can generate a DOCX editable version of any deliverable for expert review before submission.
- **FR38** : System can automatically annex supporting evidence from facts to deliverables (with user-driven selective mode).
- **FR39** : System can snapshot all source data (facts, verdicts, referential versions, company and project state) at the moment of generation, with cryptographic hash for immutability.
- **FR40** : PME User must sign an electronic attestation before exporting a deliverable destined to a bailleur (mandatory modal with checkbox).
- **FR41** : System can block export of deliverables above 50 000 USD threshold until user confirms section-by-section human review.
- **FR42** : System can generate deliverables calibrated to access route (direct Fund template vs Intermediary template — Journey 2 Moussa use case).
- **FR43** : Admin Mefali can manage the catalogue of `DocumentTemplate`, `ReusableSection`, and `AtomicBlock` (N2 workflow for templates).
- **FR44** : System can enforce a mandatory human consultant review before exporting any SGES/ESMS BETA deliverable. The blocking workflow has **NO BYPASS** — even for `admin_mefali` or `admin_super` roles. The only way to bypass is for `admin_mefali` to retire the BETA flag after Phase 2 GA criteria are met (10+ positive expert reviews with score ≥ 4/5). Any attempt to bypass is logged as a security incident and rejected at the application layer.

### Conversational Copilot (Chat IA + Tools)

- **FR45** : PME User can interact with Mefali via chat streaming SSE in French, with the copilot able to invoke tools for any available capability (catalogue query, facts entry, matching, generation, formalization planning).
- **FR46** : System can maintain conversation context with `active_project` and `active_module` state across turns (signal PRD 2).
- **FR47** : System can present interactive widgets (QCU, QCM, QCU+justification) within the chat for structured data collection.
- **FR48** : System can surface guided tours triggered by the LLM via a LangChain tool (infrastructure livrée spec 019).
- **FR49** : System can fall back gracefully to manual input when the LLM fails, preserving conversation continuity.
- **FR50** : PME User can resume an interrupted conversation from its last checkpoint (LangGraph MemorySaver).

### Dashboard, Monitoring & Notifications

- **FR51** : PME User can view a dashboard aggregating scores ESG, bilan carbone, crédit, financement, plan d'action (module 011 existant, étendu avec nouveaux blocs visuels).
- **FR52** : PME User can drill down from the global score into each active referential's verdicts.
- **FR53** : PME User can view a multi-project dashboard when owning or being member of multiple projects (Journey 2 Moussa).
- **FR54** : PME User can receive in-app reminders for upcoming events (deadline bailleur, renouvellement certification, expiration de faits, MàJ version référentiel, étape de `FormalizationPlan`).
- **FR55** : Admin Mefali can access a system monitoring dashboard (p95 latence par tool, taux erreur, échecs guards LLM, couverture catalogue).
- **FR56** : System can trigger an alert to Admin on anomalies (échec guards LLM, taux retry anormal, source URL catalogue HTTP ≠ 200).

### Audit, Compliance & Security

- **FR57** : System can log every generation of a deliverable with full metadata in `FundApplicationGenerationLog` (LLM version, timestamp, anonymized prompts, referential versions, snapshot hash, user ID).
- **FR58** : System can anonymize PII (noms, adresses, numéros RCCM/NINEA/IFU, téléphones) before sending any prompt to the LLM.
- **FR59** : System can enforce RLS (Row-Level Security) at the PostgreSQL level on tables `companies`, `fund_applications`, `facts`, `documents`.
- **FR60** : System can encrypt sensitive data at rest (bilans, RCCM, IFU, documents uploadés) using KMS-managed keys.
- **FR61** : System can require MFA for `admin_mefali` and `admin_super` roles permanently, with step-up MFA for high-risk actions on all roles (soumission > 50k USD, signature électronique, modification données bancaires, changement credentials, suppression documents/projets, export données sensibles).
- **FR62** : System can enforce the NFR-SOURCE-TRACKING rule: any catalogue entity without `source_url`, `source_accessed_at`, and `source_version` remains in DRAFT state and cannot be published.
- **FR63** : System can run a nightly CI test that verifies HTTP 200 accessibility of all `source_url` in the catalogue.
- **FR64** : System can maintain an audit trail of all catalogue modifications by admins (who modified, what entity, when, before/after values), retained minimum 5 years, with an Admin Mefali UI to consult modification history per entity.
- **FR65** : PME User can exercise the right to erasure (soft delete + deferred purge 30–90 days), with impact on submitted FundApplications documented (snapshots remain frozen).
- **FR66** : PME User can export all their data in a machine-readable format (JSON + CSV optionnel) for portability, aligned with the right to data portability under SN 2008-12, CI 2013-450, and RGPD equivalents.
- **FR67** : PME User can grant time-bounded access (auditor role with expirable token) to external reviewers (cabinet comptable, conseiller ESG).
- **FR68** : PME User can initiate a password reset via email verification link (or magic link for passwordless onboarding MVP). Admin Mefali can force-reset a user password in case of emergency with audit log.
- **FR69** : System can maintain an audit trail of all accesses to sensitive data, retained 5 years minimum.

### Search & Knowledge Retrieval (RAG)

- **FR70** : System can retrieve relevant fragments from uploaded documents via pgvector embeddings, to support fact extraction, narrative generation, and ESG assessment across at least 5 modules (application of signal PRD 6 — RAG transversal, cf. SC-T9).
- **FR71** : System can cite source documents in generated content (rule-level citation in verdicts, paragraph-level citation in narratives).

## Non-Functional Requirements

> Les NFR ci-dessous spécifient **HOW WELL** le système doit fonctionner. Chaque NFR est testable. **Total : 76 NFR répartis en 12 catégories.**

### Performance (NFR1–NFR8)

- **NFR1** — Requête cube 4D matching : ≤ 2 s p95 avec cache tiède (cf. SC-T3).
- **NFR2** — Génération verdicts multi-référentiels pour évaluation ESG complète (30–60 critères sur 3–5 référentiels actifs) : ≤ 30 s p95 (cf. SC-T4).
- **NFR3** — Génération PDF simple (EUDR DDS, plan d'action) : ≤ 30 s p95.
- **NFR4** — Génération livrable lourd (SGES/ESMS BETA, IFC AIMM full, GCF Funding Proposal) : ≤ 3 minutes p95. Au-delà récurrent, migration vers file de jobs asynchrones (Phase Growth).
- **NFR5** — Latence chat utilisateur (temps de réponse perçu du premier token streaming SSE) : ≤ 2 s p95 (cf. MO-6).
- **NFR6** — Latence navigation entre pages dashboard (Time to Interactive) : ≤ 1,5 s p95 sur connexion 4G.
- **NFR7** — Chargement initial application (First Contentful Paint) : ≤ 2 s p95 sur 4G, ≤ 5 s p95 sur 3G dégradée (mode low-data Phase 3).
- **NFR8** — Temps de démarrage backend (cold start) : ≤ 30 s, incluant chargement catalogue en mémoire et warm-up pgvector.

### Security (NFR9–NFR18)

- **NFR9** — TLS 1.3 minimum pour toutes les connexions client-serveur et serveur-serveur. Certificats valides, renouvellement automatique.
- **NFR10** — Chiffrement at rest via clés gérées par KMS pour : documents uploadés (bilans, RCCM, IFU, preuves), snapshots de `FundApplication`, journal d'audit.
- **NFR11** — Anonymisation systématique des PII avant envoi au LLM. Pipeline testé et audit annuel.
- **NFR12** — RLS PostgreSQL activé dès MVP sur `companies`, `fund_applications`, `facts`, `documents`. Généralisation Phase Growth.
- **NFR13** — Authentification JWT stateless avec refresh token. Durée : 1 h (access), 30 j (refresh révocable). Rotation sur action sensible.
- **NFR14** — MFA obligatoire `admin_mefali` / `admin_super`. Opt-in fortement recommandé `owner`. Step-up MFA sur actions à risque élevé (FR61).
- **NFR15** — Gestion des secrets via variables d'environnement (MVP) puis Secret Manager (Phase Growth). Rotation trimestrielle. Lint pre-commit `detect-secrets` / `truffleHog`.
- **NFR16** — Pas de secrets ou de PII dans les logs applicatifs. Enforcement via structured logging avec anonymisation automatique.
- **NFR17** — Rate limiting : 30 msg/min par user sur endpoints chat (livré story 9.1). Extension aux tools coûteux en Phase Growth.
- **NFR18** — Pen test externe OBLIGATOIRE avant premier pilote PME réelle. Findings CRITIQUES corrigés avant activation. Audit sécurité indépendant Phase 0 (5 jours, ~5–8 k€).

### Privacy, Data Residency & Compliance (NFR19–NFR28)

- **NFR19** — Conformité loi SN 2008-12, CI 2013-450, règlement CEDEAO sur protection données. Alignement structurel RGPD.
- **NFR20** — Rétention par catégorie : profil (compte + 2 ans), documents ordinaires (compte + 5 ans), **SGES/ESMS + associés (10 ans min après fin FundApplication)**, faits (versions historiques conservées indéfiniment), logs applicatifs (12 mois), logs audit accès sensibles (5 ans).
- **NFR21** — Soft delete + purge différée 30–90 j. Purge définitive irréversible et auditable.
- **NFR22** — Consentement explicite pour tout partage vers bailleur ou intermédiaire (acte distinct du « saisi dans Mefali »).
- **NFR23** — Droit à l'effacement : snapshots de `FundApplication` soumis restent figés, indépendants du profil vivant.
- **NFR24** — **Data residency : Option A retenue — hébergement EU (AWS EU-West-3 Paris ou EU-West-1 Irlande)**. Justifications : écosystème managed services complet, latence raisonnable depuis AO (~80–150 ms), DPA + clauses-types CEDEAO + consentement utilisateur à l'onboarding.
  - **Plan de contingence documenté** : migration déclenchable vers AWS Cape Town ou provider local si (a) évolution réglementaire SN/CI/CEDEAO imposant résidence locale, (b) volumétrie utilisateurs > seuil Phase Growth rendant Cape Town économiquement plus intéressant, (c) incident data residency lors d'un audit bailleur.
  - **Plan de migration** documenté dès Phase 0, testé en tabletop exercise annuellement.
  - **Clauses-types CEDEAO** référencées explicitement dans le DPA et dans le consentement utilisateur (pas juste RGPD).
  - **Localisation par type de document** documentée dans le catalogue technique (ex. bilans → EU-West-3 ; signatures → EU-West-3 + cache EU-West-1 pour résilience).
- **NFR25** — Documents « données sensibles » (bilans, RCCM, IFU, pièces d'identité) : localisation documentée et auditable. Tout transfert hors UEMOA/CEDEAO → trace + consentement.
- **NFR26** — Data portability : export complet des données user en format machine-readable (JSON + CSV optionnel) via FR66.
- **NFR27** — NFR-SOURCE-TRACKING : toute entité du catalogue porte obligatoirement `source_url`, `source_accessed_at`, `source_version`. DRAFT non-publiable sinon (FR62).
- **NFR28** — Audit trail complet et immuable des accès aux données sensibles, modifications catalogue, générations de livrables. Retenu 5 ans minimum.

### Availability, Reliability & Disaster Recovery (NFR29–NFR36)

- **NFR29** — SLA différencié : endpoints critiques (soumission, génération SGES, dossier lourd) = **99,5 % dès MVP**. Non-critiques (chat, dashboard, recherche) = 99 % MVP, 99,5 % Growth.
- **NFR30** — Soumissions de dossiers bailleurs atomiques et resumables. Reprise sur échec réseau sans perte via LangGraph checkpointer.
- **NFR31** — Sauvegardes BDD PostgreSQL + pgvector : incrémentales quotidiennes, complètes hebdomadaires, 30 j en chaud + 1 an archivé.
- **NFR32** — Test de restauration BDD trimestriel documenté.
- **NFR33** — Sauvegardes fichiers uploadés : réplication géographique 2 AZ minimum, rétention alignée sur politique.
- **NFR34** — RTO cible MVP : **4 heures**.
- **NFR35** — RPO cible MVP : **24 heures max**.
- **NFR36** — Plan de continuité documenté avec runbooks d'incident. Tabletop exercise trimestriel (mitigation RM-7).

### Observability (NFR37–NFR41)

- **NFR37** — Logs structurés JSON avec `request_id` UUID traversant frontend → FastAPI → LangGraph → tools → DB. Aucun log non-structuré en prod.
- **NFR38** — 100 % des tools métier LangChain instrumentés avec `with_retry` + `log_tool_call` (clôture P1 #14 audit, cf. SC-T11).
- **NFR39** — Dashboard monitoring interne (admin_mefali) : p95 latence par tool, taux erreur, taux retry, échecs guards LLM, timeouts.
- **NFR40** — Alerting configuré sur : échec guards LLM, taux retry anormal, erreurs DB, timeouts, `source_url` catalogue HTTP ≠ 200 (FR63).
- **NFR41** — Budget LLM surveillé par user et global, alerting sur dépassement mensuel (mitigation RM-6).

### Integration (NFR42–NFR48)

- **NFR42** — LLM provider : **Anthropic via OpenRouter**. Abstraction Provider layer pour switch en < 2 semaines. Backup provider configuré (OpenAI ou Mistral).
- **NFR43** — Embeddings : OpenAI `text-embedding-3-small` pour pgvector. Alternative open-source évaluée Phase Growth.
- **NFR44** — OCR : Tesseract bilingue `fra+eng` (story 9.4). Extension `por` Phase Vision.
- **NFR45** — **Email transactionnel : Mailgun retenu pour MVP** (bon taux délivrance AO, RGPD EU, coût compétitif).
  - **Configuration obligatoire** : DKIM + SPF + DMARC sur domaine d'envoi.
  - **Monitoring continu** du taux de délivrance avec alerting si < 95 % sur 7 jours glissants.
  - **Domaine dédié d'envoi** (ex. `notifications@mefali.com`) séparé du domaine principal pour préserver la réputation en cas d'incident.
  - **Templates email versionnés dans Git** (pas hardcodés dans Mailgun UI).
  - Alternatives fallback évaluées : Amazon SES (économique si AWS), Resend (moderne mais jeune en AO).
- **NFR46** — Génération PDF : WeasyPrint + Jinja2 (existant module 006 étendu Cluster C).
- **NFR47** — Génération DOCX : python-docx (existant spec 009 étendu).
- **NFR48** — Stockage documents : local `/uploads/` MVP avec backup géographique (NFR33). Migration S3-compatible Phase Growth.

### Scalability (NFR49–NFR53)

- **NFR49** — Architecture stateless backend FastAPI (sauf LangGraph checkpointer persisté BDD) pour scaling horizontal.
- **NFR50** — Capacité cible MVP : 500 users actifs simultanés sans dégradation. Phase Growth : 5 000. Phase Vision : 50 000+.
- **NFR51** — PostgreSQL : indexes composites sur dimensions cube 4D, vues matérialisées pour requêtes chaudes, partitionnement évalué Growth.
- **NFR52** — pgvector : IVFFlat MVP, migration vers HNSW si > 100 k embeddings.
- **NFR53** — Cache tiède Redis Phase Growth pour sessions, catalogues chauds, résultats de matching fréquents.

### Accessibility (NFR54–NFR58)

- **NFR54** — Conformité WCAG 2.1 niveau AA minimum pour toutes pages et composants user-facing.
- **NFR55** — Navigation clavier complète (livrée spec 019 story 1.7), étendue à toutes nouvelles pages.
- **NFR56** — ARIA roles conformes (livrés spec 018), étendus aux nouveaux composants.
- **NFR57** — Contraste couleurs WCAG AA (4.5:1 texte normal, 3:1 texte large). Vérification CI via axe-core / pa11y.
- **NFR58** — Support lecteurs d'écran NVDA, JAWS, VoiceOver pour parcours critiques. Audit accessibilité indépendant Phase 3 (1–2 jours, ~1–2 k€).

### Maintainability & Code Quality (NFR59–NFR64)

- **NFR59** — Principe *zero failing tests on main* maintenu (opérationnel depuis story 9.3). Baseline tests verts documentée et croissante à chaque clôture de phase.
- **NFR60** — Couverture de tests différenciée :
  - **≥ 80 %** sur code standard (backend + frontend).
  - **≥ 85 %** sur code critique : guards LLM, anonymisation PII, RLS enforcement, rate limiting, signature électronique, snapshot `FundApplication`, génération livrables bailleur.
  - **Coverage gates CI** : PR rejetée si couverture descend sous ces seuils.
- **NFR61** — Documentation inline : docstrings Python fonctions publiques, JSDoc/TSDoc composables TS. CLAUDE.md mis à jour à chaque nouveau module.
- **NFR62** — Conventions de code (cf. CLAUDE.md) : code en anglais, commentaires en français, snake_case Python, PascalCase composants Vue, structure Nuxt 4 `app/`, dark mode obligatoire, migrations Alembic.
- **NFR63** — Pas de feature flag permanent : tout feature flag introduit en migration (ex. `ENABLE_PROJECT_MODEL`) retiré via story dédiée en fin de Phase 1.
- **NFR64** — Anti-pattern God service (cf. P2 #25 audit) : services consomment services d'autres modules, pas leurs tables directement.

### Internationalization (NFR65–NFR67)

- **NFR65** — Locale utilisateur unique `fr` (ou `fr-FR`). Aucun hardcoded string user-facing hors fichier de traduction.
- **NFR66** — Paramétrage pays via tables BDD (`AdminMaturityRequirement`, `regulation_reference`, `Country` enrichie). Séparation stricte locale (langue) vs country (data).
- **NFR67** — Framework i18n Nuxt (`@nuxtjs/i18n` ou `vue-i18n`) installé en Phase 0. Extensibilité locale `en` Phase Vision sans refactor majeur.

### Budget & Ops (NFR68–NFR70)

- **NFR68** — Budget LLM : alerting sur dépassement mensuel. Seuil à définir Phase 0 avec stakeholders business.
- **NFR69** — Budget infrastructure cible MVP : ordre de grandeur **800–2 000 €/mois** avec décomposition indicative : AWS compute + RDS + S3 + CloudFront (~300–600 €), LLM Anthropic/OpenRouter (~200–800 €, poste le plus volatile), Embeddings OpenAI (~50–200 €), Mailgun (~50–100 €), Stockage + backup (~100–200 €), Monitoring Sentry/Datadog (~100–300 €). **À confirmer après Phase 0 par costing détaillé** basé sur volumétrie cible 100–500 users actifs.
- **NFR70** — Cyber insurance : évaluée en Phase Growth une fois la base user établie et volumes sensibles confirmés (mitigation RM-7).

### DevOps Practices & Release Engineering (NFR71–NFR76)

- **NFR71** — **Load Testing obligatoire avant prod** : tests de charge OBLIGATOIRES avant ouverture au premier pilote PME réelle. Scénarios :
  - 100 users simultanés pendant 30 min sur chat + cube 4D matching
  - 10 générations simultanées de livrables lourds (SGES / IFC AIMM)
  - 500 appels/min sur endpoints read-only (catalogue, dashboard)
  Critères de passage : tous les NFR Performance (NFR1–NFR8) respectés sous charge. Outil : Locust, k6 ou équivalent. Rapport archivé. À re-lancer à chaque Phase avant passage en prod.
- **NFR72** — **Security Dependency Audit automatisé** : scan quotidien des dépendances Python (`pip-audit`) et JavaScript/Node (`npm audit`, Snyk ou Dependabot) pour détecter CVE. PR automatique sur vulnerabilities MEDIUM+. Blocage du merge si vulnerability CRITICAL non résolue.
- **NFR73** — **Environment Isolation** : trois environnements distincts.
  - **DEV** : données synthétiques, intégration locale, test dev.
  - **STAGING** : mirror de prod côté infra, données anonymisées ou subset small, tests de régression + E2E + UAT.
  - **PROD** : données réelles, accès limité (`admin_super` uniquement pour debug, audit log tout accès), backup + monitoring + alerting full.

  Données prod **JAMAIS copiées vers dev/staging sans anonymisation préalable** (pipeline documenté). Secrets différents par environnement.
- **NFR74** — **LLM Quality Observability** : métriques continues sur qualité des générations LLM.
  - Taux de passage des guards (> 90 % cible, alerting si < 80 %).
  - Taux de retry automatique (< 5 % cible).
  - Taux d'échec définitif (< 1 % cible).
  - Temps moyen de génération par type de livrable.
  - Coût moyen par génération.
  Dashboard `admin_mefali`. Alerting sur dégradation soudaine (signal de régression modèle LLM upstream).
- **NFR75** — **LLM Retry Strategy** explicite.
  - Max 3 retries avec exponential backoff (1 s, 3 s, 9 s).
  - Retry uniquement sur erreurs transient (timeout, 5xx, rate limit 429).
  - **Pas de retry** sur erreurs définitives (400, guards fail, schema validation fail).
  - Circuit breaker : après 10 échecs consécutifs sur même endpoint LLM → désactivation 60 s + alerting.
  - Tous les retries loggés avec leur raison.
- **NFR76** — **Code Review mandatory** : toute PR vers main requiert minimum **1 reviewer approval** avant merge. Pour PR touchant du code critique (sécurité, compliance, guards LLM, snapshot, signature, rate limiting, RLS) : **2 reviewers minimum dont 1 senior**. Checklist de review automatique :
  - Tests ajoutés et passants.
  - Pas de secrets committé (`detect-secrets` pass).
  - Pas de `console.log` / `print` debug.
  - Pas de TODO sans ticket associé.
  - Respect conventions CLAUDE.md.
  - Dark mode enforcement frontend.
  - Type hints Python + TypeScript strict.
  Branch protection rules GitHub/GitLab appliquées.

---

# Annexes

## Annexe A — Table of Contents

1. Executive Summary — What Makes This Special — Project Classification
2. Success Criteria (User / Business / Technical / Measurable Outcomes)
3. Product Scope — MVP / Growth / Vision
4. User Journeys (Aminata, Moussa, Akissi, Ibrahim, Mariam) + Journey Requirements Summary
5. Domain-Specific Requirements (Compliance, Technical Constraints, Integration, Risk Mitigations, NFR Structurants)
6. Innovation & Novel Patterns (INN-1..5, Market Context, Validation Approach, Risk Mitigation)
7. Web App + SaaS B2B Specific Requirements (Architecture, Multi-Tenancy, RBAC, Auth, Integrations, Frontend, Data Residency, Secrets, Backup/DR, Implementation)
8. Project Scoping & Phased Development (MVP Strategy, Phase 0–5, Risk Mitigation consolidée, Stratégie de contingence)
9. Functional Requirements (FR1–FR71 en 9 capability areas)
10. Non-Functional Requirements (NFR1–NFR76 en 12 catégories)
11. Annexes A–I

## Annexe B — Résultats Web Search Light (step 11)

Validation factuelle de 4 points critiques avant clôture du PRD. Toutes les corrections identifiées ont été propagées dans les sections concernées.

### B.1 — IFC Performance Standards

- **Fait initial PRD** : `IFC_PS@2012` actuelle + `IFC_PS@2026` à anticiper.
- **Fait vérifié** : version 2012 toujours en vigueur en avril 2026. Update Framework en cours — **Phase I Dialogue janvier–mars 2026**, **Phase II Consultation publique avril 2026 – mars 2028**. Publication finale attendue ≥ 2028.
- **Correction appliquée** : remplacement de `IFC_PS@2026 (à anticiper)` par `IFC_PS@2028+ (Update Framework en consultation)`.
- **Source** : [Update of IFC's Sustainability Framework](https://www.ifc.org/en/what-we-do/sector-expertise/sustainability/policies-and-standards/update-of-ifc-s-sustainability-framework)
- **Date d'accès** : 2026-04-18.

### B.2 — EUDR (Règlement UE 2023/1115)

- **Fait initial PRD** : « EUDR en entrée en vigueur 2026–2027 » (imprécis).
- **Fait vérifié** : re-postponé en décembre 2025 par **Regulation EU 2025/2650**. Dates d'application définitives : **30 décembre 2026 pour grandes entreprises**, **30 juin 2027 pour PME et micro-entreprises**. Un rapport de simplification de la Commission est attendu avant le 30 avril 2026 — report supplémentaire possible.
- **Correction appliquée** : précision des deux dates dans Exec Summary, Domain Requirements, Innovation Why Now, Journey 1 Aminata. RM-4 ajusté.
- **Sources** :
  - [Delay until December 2026 and other developments (EU Access2Markets)](https://trade.ec.europa.eu/access-to-markets/en/news/delay-until-december-2026-and-other-developments-implementation-eudr-regulation)
  - [Council signs off postponement (Consilium)](https://www.consilium.europa.eu/en/press/press-releases/2025/12/18/deforestation-council-signs-off-targeted-revision-to-simplify-and-postpone-the-regulation/)
- **Date d'accès** : 2026-04-18.

### B.3 — AFAC Continental Sustainable Finance Taxonomy (BAD)

- **Fait initial PRD** : « Taxonomie africaine BAD (en structuration 2025+) ».
- **Fait vérifié** : **validée juillet 2025 à Nairobi** (AFAC — African Financial Alliance on Climate Change) par régulateurs, banques, assureurs et DFI. Développée en consultation d'un an avec > 60 institutions. Support technique PwC Luxembourg, financement Global Center on Adaptation via AAAP (Africa Adaptation Acceleration Program) / African Climate Change Fund. Déploiement opérationnel en cours.
- **Correction appliquée (impact positif fort)** : passage de « en structuration » à « validée juillet 2025, en déploiement opérationnel » dans Exec Summary, SC-B4, Innovation Why Now, Domain Requirements. Positionnement Mefali renforcé (cadre opérationnel, pas anticipation).
- **Source** : [Africa's Financial Industry Validates the Continental Sustainable Finance Taxonomy (AfDB)](https://www.afdb.org/en/news-and-events/africas-financial-industry-validates-continental-sustainable-finance-taxonomy-85995)
- **Date d'accès** : 2026-04-18.

### B.4 — RSPO Principles & Criteria

- **Fait initial PRD** : « RSPO P&C : version 2018 ou 2024 » (à trancher).
- **Fait vérifié** : **RSPO P&C 2024 (version 4.0)** adoptée par vote des membres à la 21ᵉ Assemblée Générale (GA21) le 13 novembre 2024. Mise à jour (Annexes 2 et 5) au 19 septembre 2025. **Date effective obligatoire postponée au 31 mai 2026** par résolution approuvée en novembre 2025.
- **Correction appliquée** : trancher sur `RSPO_PC@2024_v4.0` avec date d'effet 31 mai 2026 dans Domain Requirements, Journey 5 Mariam (exemple de ReferentialMigration), NFR source_version.
- **Sources** :
  - [RSPO Members Adopt the 2024 Principles and Criteria](https://rspo.org/rspo-members-adopt-the-2024-principles-and-criteria-and-independent-smallholder-standard/)
  - [Postponement of Mandatory Entry into Force of the 2024 RSPO P&C](https://rspo.org/postponement-of-mandatory-entry-into-force-of-the-2024-rspo-principles-and-criteria-pc/)
  - [2024 Standards Implementation](https://rspo.org/as-an-organisation/our-standards/2024-standards-implementation/)
- **Date d'accès** : 2026-04-18.

### B.5 — Synthèse des impacts sur le PRD

| # | Correction | Impact PRD |
|---|---|---|
| B.1 | IFC PS Update Framework 2028+ | Pattern ReferentialMigration inchangé ; exemple Journey 5 Mariam remplacé par RSPO ; pas de pression court-terme |
| B.2 | EUDR 30 juin 2027 pour PME | Cadencement MVP critique (doit être disponible avant juin 2027) ; urgence commerciale PME cacao/palme/coton/bois précisée |
| B.3 | Taxonomie AFAC validée juillet 2025 | Positionnement renforcé ; intégration Phase 2 au lieu d'anticipation ; SC-B4 reformulé |
| B.4 | RSPO 2024 v4.0 effective 31 mai 2026 | Pack RSPO Premium cible 2024 v4.0 dès le MVP ; Journey 5 Mariam = exemple réaliste de migration |

## Annexe C — Mapping Clusters → FR → Phase

| Cluster | FR couverts | Phase de livraison | Dépendances inter-cluster |
|---|---|---|---|
| **A — Projet (data model)** | FR1–FR10 | Phase 1 | Racine — aucune dépendance upstream |
| **A' — Maturité entreprise** | FR11–FR16 | Phase 1 | Utilise Cluster A (Company) |
| **B — ESG multi-contextuel (3 couches)** | FR17–FR26 | Phase 1 catalogue P0 + Phase 2 extension P1 + Phase 4 extension P2 | Parallèle à A ; utilisé par C |
| **Cube 4D Funding Matching** | FR27–FR35 | Phase 1 | Dépend de A + A' + B |
| **C — Moteur de livrables** | FR36–FR44 (dont FR44 SGES BETA Phase 1 + GA Phase 2) | Phase 1 BETA + Phase 2 GA | Dépend de A + A' + B |
| **Copilot conversationnel** | FR45–FR50 | Phase 1 (extension de l'existant) | Transverse |
| **D — Dashboard + Monitoring** | FR51–FR56 | Phase 1 MVP (dashboard existant) + Phase 3 UX enrichi | Parallèle |
| **Audit / Compliance / Security** | FR57–FR69 | Phase 0 (prérequis) + Phase 1 (enforcement) | Transverse — obligatoire MVP |
| **RAG transversal** | FR70–FR71 | Phase 0 (≥ 5 modules) + Phase 4 (8/8 modules) | Transverse |

## Annexe D — Risques consolidés

| Code | Libellé | Probabilité | Impact | Mitigation principale | Source |
|---|---|---|---|---|---|
| **RT-1** | Performance cube 4D insuffisante | Moyenne | Élevé | Fallback cube 3D sur critère déclenchement explicite | Step 8 |
| **RT-2** | Qualité livrables LLM | Moyenne | Critique | Guards + signature + audit trail + revue obligatoire > 50k USD | Step 5 + Step 8 |
| **RT-3** | Migration brownfield casse l'existant | Moyenne | Élevé | Feature flag `ENABLE_PROJECT_MODEL` + cleanup obligatoire + tests régression | Step 7 + Step 8 |
| **RT-4** | Intégrité catalogue (hallucination import) | Moyenne | Élevé | NFR-SOURCE-TRACKING + test CI nocturne HTTP 200 | Step 5 + Step 8 |
| **RT-5** | Compliance données AO | Faible | Critique | Data residency EU (NFR24) + RLS partiel + anonymisation PII + chiffrement at rest | Step 5 + Step 7 + Step 8 |
| **RM-1** | Adoption faible PME informelles | Moyenne | Critique | Journey 1 validé en pilote ; formalisation graduée P1 ; SMS/WhatsApp Phase 2 | Step 8 |
| **RM-2** | Rejet livrables par bailleurs | Moyenne | Critique | Revue experte obligatoire pilote (clause protection PME) ; guards ; signature user | Step 6 + Step 8 |
| **RM-3** | Concurrent direct apparaît | Faible-Moyenne | Élevé | Web search Step 11 (fait) + avantage base validée 18 specs | Step 6 + Step 8 |
| **RM-4** | Évolution EUDR ou réglementations AO | Moyenne | Moyen | NFR-ADMIN-LEVELS N3 versioning strict ; migration automatique ; surveillance simplification review EU avant 30 avril 2026 | Step 8 |
| **RM-5** | Partenariats institutionnels retardés | Élevée | Moyen | SLA relaxé MOU T+9 mois / end-to-end T+15 mois | Step 3 + Step 8 |
| **RM-6** | Dépendance LLM provider Anthropic/OpenRouter | Moyenne | Critique | Abstraction Provider layer + backup provider configuré + plan continuité outage | Step 8 |
| **RM-7** | Incident sécurité / data breach | Faible | Existentiel | IRP documenté et testé ; cyber insurance Phase Growth ; pen test externe obligatoire pré-pilote | Step 8 |
| **RR-1** | Budget Dev insuffisant | Moyenne | Élevé | Priorisation stricte must-have ; report nice-to-have | Step 8 |
| **RR-2** | Manque d'expertise ESG interne | Moyenne | Élevé | Contractualiser 2 consultants ESG AO seniors (SC-B-PILOTE) | Step 8 |
| **RR-3** | Perte de contributeurs clés | Faible | Moyen | Documentation CLAUDE.md ; pair programming ; tests extensifs | Step 8 |
| **RR-4** | Dette technique qui ralentit | Faible | Moyen | Zero failing tests on main ; cleanup feature flags ; dettes P1 audit résolues | Step 8 |
| **RR-5** | Scope creep en Phase 1 | Moyenne | Élevé | Section « Explicitly NOT in MVP » fait foi ; arbitrage explicite documenté | Step 8 |

## Annexe E — Questions ouvertes avec statut

| Code | Question | Origine | Statut |
|---|---|---|---|
| **QO-A1** | Un `Project` peut-il exister sans `Company` rattachée ? | Brainstorming | Ouverte — à trancher PRD/Architecture |
| **QO-A2** | Rôles consortium : enum fixe ou liste libre ? | Brainstorming | **Résolue** (FR7 — enum extensible via admin N2) |
| **QO-A3** | Stratégie de migration des Company existantes | Brainstorming | **Résolue** (Step 7 — default Project + feature flag) |
| **QO-A4** | Changements de scope projet post-financement | Brainstorming | Ouverte — versioning à préciser |
| **QO-A5** | Clonage `FundApplication` vers autre fonds | Brainstorming | Ouverte — à trancher Epic breakdown |
| **QO-A'1** | OCR validation vs humain en boucle | Brainstorming | Ouverte — pilote décidera |
| **QO-A'2** | Confidentialité documents / partage bailleur | Brainstorming | **Résolue** (NFR22 consentement explicite) |
| **QO-A'3** | Niveaux intermédiaires de formalisation | Brainstorming | Ouverte — pilote décidera |
| **QO-A'4** | Formalisation vs conformité fiscale | Brainstorming | Ouverte |
| **QO-A'5** | Régression de niveau si liquidation partielle | Brainstorming | Ouverte |
| **QO-B1** | Critère obsolète — archivage vs suppression | Brainstorming | **Résolue** (archivage, pas suppression) |
| **QO-B2** | Introduction `FactProvenance` | Brainstorming | **Résolue** (NFR-SOURCE-TRACKING) |
| **QO-B3** | Scoring évaluation partielle | Brainstorming | Ouverte — à trancher Epic breakdown |
| **QO-B4** | Arbitrage faits conflictuels | Brainstorming | Ouverte |
| **QO-B5** | Performance requête multi-dim | Brainstorming | **Résolue** (NFR1 + indexes + cache tiède + fallback cube 3D) |
| **QO-C1** | Streaming vs batch génération | Brainstorming | **Résolue** (Vision — file Celery) |
| **QO-C2** | Import gabarits bailleurs non officiels | Brainstorming | Ouverte |
| **QO-C3** | Immutabilité livrable soumis | Brainstorming | **Résolue** (FR39 — snapshot hash) |
| **QO-C4** | Traductions automatiques EN↔FR | Brainstorming | **Résolue** (IA + review humaine optionnelle) |
| **QO-C5** | Archivage long terme IFC AIMM | Brainstorming | **Résolue** (NFR20 — 10 ans min SGES) |
| **QO-D1** | Formation IA vs experts | Brainstorming | **Résolue** (Claude socle + humain spécialisation) |
| **QO-D2** | Attestation formation | Brainstorming | **Résolue** (certificat téléchargeable, pas juridique) |
| **QO-D3** | Extension Chrome intégrée au dashboard | Brainstorming | **Résolue** (oui, même registre blocs — Phase 4) |
| **QO-D4** | Hybridation consultant Option 3 | Brainstorming | **Résolue** (post-MVP Vision, porte ouverte) |
| **QO-D5** | Persona consultant multi-PME | Brainstorming | **Résolue** (retiré du MVP — positionnement Option 1 pur) |
| **QT-1** | Multi-langue effective | Brainstorming | **Résolue** (NFR65 — fr unique MVP) |
| **QT-2** | Politique rétention | Brainstorming | **Résolue** (NFR20) |
| **QT-3** | Interopérabilité API bailleurs | Brainstorming | **Résolue** (Vision non engagée) |
| **QT-4** | Modèle économique | Brainstorming | Ouverte — atelier business Phase 0 |
| **QT-5** | Gouvernance catalogue | Brainstorming | **Résolue** (NFR-ADMIN-LEVELS N1/N2/N3) |

**Statut global :** 20/30 résolues dans le PRD, 10/30 restent ouvertes (à trancher en Architecture, Epic breakdown, pilote ou atelier business).

## Annexe F — Sources à vérifier en Phase 0 (`9-X-catalog-sourcing-documentaire`)

Complément aux 4 points Web Search Light validés en Step 11. Cette liste alimente la story Phase 0 obligatoire.

**Référentiels internationaux restants à sourcer :**
- GCF Funding Proposal template (structure actuelle, annexes)
- FEM (GEF) Safeguards Standards + GEF Project Identification Form (PIF)
- Proparco AIMM (méthodologie et indicateurs d'impact)
- BOAD SSI (Système de Sauvegardes Intégré BOAD, version en vigueur)
- BAD SSI (Système de Sauvegardes Intégré BAD, version en vigueur)
- Banque Mondiale ESF (ESS 1–10, interprétation pour PME sous-traitantes)
- DFI Harmonized Approach to Private Sector Operations (accord inter-bailleurs)

**Certifications sectorielles restantes :**
- Rainforest Alliance (Sustainable Agriculture Standard 2020+, consolidation post UTZ)
- Fairtrade (Standards for Small-Scale Producers)
- Bonsucro (sucre)
- FSC (Forest Stewardship Council — versions FSC-STD-01-001 et -002)
- IRMA (mines — Initiative for Responsible Mining Assurance)
- ResponsibleSteel

**Standards reporting :**
- GRI Standards (dernière version 2021 + sectorial standards)
- TCFD recommendations (consolidé par ISSB en 2024 — migration ISSB S1/S2 ?)
- CDP (climat, eau, forêts — versions questionnaires 2026)
- SASB (intégré ISSB — version applicable)
- GIIN IRIS+ (Catalog of Metrics)
- ITIE (Norme ITIE — dernière version)

**Audits clients EU :**
- Sedex / SMETA (4-pillar audit methodology, version en vigueur)
- EcoVadis (scoring methodology)
- SA8000 (Social Accountability International, version en vigueur)
- BSCI / amfori BSCI Code of Conduct

**Conventions OIT fondamentales (8) :**
- Convention 29 (travail forcé, 1930)
- Convention 87 (liberté syndicale, 1948)
- Convention 98 (droit d'organisation et de négociation collective, 1949)
- Convention 100 (égalité de rémunération, 1951)
- Convention 105 (abolition du travail forcé, 1957)
- Convention 111 (discrimination en emploi, 1958)
- Convention 138 (âge minimum, 1973)
- Convention 182 (pires formes de travail des enfants, 1999)

**Engagements volontaires :**
- UN Global Compact (10 principes, Communication on Progress)
- Principes Volontaires sur la Sécurité et les Droits de l'Homme

**Référentiels régionaux AO :**
- Charte RSE Sénégal (initiative 2012 du Conseil national du patronat)
- Plateforme RSE Côte d'Ivoire
- Label RSE CGECI (Confédération Générale des Entreprises de Côte d'Ivoire)
- RSE & Développement Durable Bénin
- **AFAC Continental Sustainable Finance Taxonomy (BAD)** — documentation technique complète (PwC Luxembourg + Global Center on Adaptation / AAAP) — **à intégrer Phase 2**

**Réglementation nationale :**
- Codes miniers et environnement (CI, SN, BF, BJ, TG, ML, NE, GH, LR, SL)
- OHADA — Acte uniforme sur les sociétés commerciales
- Lois protection données (SN 2008-12, CI 2013-450, règlement CEDEAO)
- Lois anti-corruption locales (HABG CI, OFNAC SN)
- FCPA (USA) + UK Bribery Act (portées extra-territoriales)

**Données opérationnelles :**
- Frais RCCM par pays (tribunaux de commerce)
- Facteurs d'émission électricité par réseau national (CIE, SENELEC, SONABEL, etc.)
- SMIG par pays
- Cotisations CNPS (CI, BF, BJ, TG, NE), IPRES+CSS (SN), INPS (ML)

**Bailleurs et intermédiaires régionaux :**
- Conditions actuelles BOAD (Ligne Verte, conditions d'éligibilité)
- Conditions SUNREF (AFD — critères banques partenaires)
- Intermédiaires : SIB (CI), Ecobank (panafricain), BDU (CI), BGFI (CEMAC + AO), Coris Bank (BF)
- Fonds d'impact : AfricInvest, Mediterrania Capital, Adenia, Partech Africa, Janngo Capital
- Agences d'implémentation : PNUD, ONUDI, Banque Mondiale, AFD

**Concurrents africains émergents (analyse à compléter) :**
- Startups nigérianes ESG/fintech durables (54ESG, Climate Fund Managers…)
- Outils gratuits type Climate Finance Toolkit Banque Mondiale
- Solutions portées par incubateurs/accélérateurs régionaux (CTIC Dakar, Orange Digital Center, Impact Hub Abidjan, Bond'Innov, MEST Africa)
- Initiatives BCEAO / BOAD / BAD de plateformes publiques

**Obligation :** tout élément catalogue publié en Phase 0 doit porter `source_url`, `source_accessed_at`, `source_version` (NFR-SOURCE-TRACKING). Test CI nocturne vérifiant HTTP 200 sur `source_url` (FR63).

## Annexe G — Glossaire & Convention vocabulaire FR/EN

### Convention vocabulaire FR/EN (normative)

| Usage rédactionnel (FR) | Identifiant code (EN) | Contexte |
|---|---|---|
| entreprise | `Company` | Entité porteuse |
| projet | `Project` | Objet métier business |
| dossier | `FundApplication` | Formulation d'une demande |
| bailleur | `Fund` | Organisme de financement |
| intermédiaire | `Intermediary` | Tiers agréé |
| voie d'accès | `access_route` | Direct ou intermédié |
| fait | `Fact` | Donnée atomique |
| critère | `Criterion` | Brique composable |
| verdict | `ReferentialVerdict` | PASS/FAIL/REPORTED/N/A |
| référentiel | `Referential` | IFC PS, RSPO, GRI, etc. |
| pack | `Pack` | Pré-assemblé façade |
| niveau de maturité (entreprise) | `AdminMaturityLevel` | 0–3 |
| plan de formalisation | `FormalizationPlan` | Parcours N→N+1 |
| profil bénéficiaires | `BeneficiaryProfile` | Agrégat consortium |
| projection entreprise | `CompanyProjection` | Vue curée par fonds |
| pilote | pilot (tests) | Programme pilote |

### Glossaire métier

- **AFAC** — African Financial Alliance on Climate Change. Plateforme BAD.
- **AIMM** — Anticipated Impact Measurement and Monitoring (IFC et Proparco).
- **ANDE** — Agence Nationale De l'Environnement (Côte d'Ivoire).
- **BAD** — Banque Africaine de Développement.
- **BCEAO** — Banque Centrale des États de l'Afrique de l'Ouest.
- **BOAD** — Banque Ouest-Africaine de Développement.
- **BSCI** — amfori Business Social Compliance Initiative.
- **BUNEE** — Bureau National des Évaluations Environnementales (Burkina Faso).
- **CDP** — Carbon Disclosure Project (aujourd'hui CDP).
- **CEDEAO** — Communauté Économique des États de l'Afrique de l'Ouest.
- **CLIP** — Consentement Libre, Informé et Préalable (FPIC en anglais).
- **CNPS** — Caisse Nationale de Prévoyance Sociale (CI, BF, BJ, TG, NE).
- **CS3D** — Corporate Sustainability Due Diligence Directive (UE).
- **DEEC** — Direction de l'Environnement et des Établissements Classés (Sénégal).
- **DDS** — Due Diligence Statement (EUDR).
- **DPA** — Data Processing Addendum (RGPD).
- **EIES** — Étude d'Impact Environnemental et Social.
- **ESMS / SGES** — Environmental and Social Management System / Système de Gestion Environnementale et Sociale.
- **ESAP** — Environmental and Social Action Plan.
- **EUDR** — EU Deforestation Regulation (2023/1115, modifié par 2025/2650).
- **FCPA** — Foreign Corrupt Practices Act (USA).
- **FEM / GEF** — Fonds pour l'Environnement Mondial / Global Environment Facility.
- **FEM SGP** — GEF Small Grants Programme.
- **FNDE** — Fonds National de Développement de l'Environnement (Sénégal).
- **FSC** — Forest Stewardship Council.
- **GCF** — Green Climate Fund.
- **GHG Protocol** — Greenhouse Gas Protocol (scopes 1, 2, 3).
- **GRI** — Global Reporting Initiative.
- **HABG** — Haute Autorité pour la Bonne Gouvernance (Côte d'Ivoire).
- **IFC** — International Finance Corporation (groupe Banque Mondiale).
- **IFC PS** — IFC Performance Standards 1–8.
- **IFU** — Identifiant Fiscal Unique (plusieurs pays UEMOA).
- **IPRES** — Institution de Prévoyance Retraite du Sénégal.
- **IRIS+** — Impact Reporting and Investment Standards (GIIN).
- **IRMA** — Initiative for Responsible Mining Assurance.
- **ISO** — International Organization for Standardization.
- **ITIE** — Initiative pour la Transparence des Industries Extractives (EITI).
- **KMS** — Key Management Service (AWS KMS ou équivalent).
- **LLM** — Large Language Model.
- **MFA** — Multi-Factor Authentication.
- **MOU** — Memorandum of Understanding (Lettre d'intention).
- **NIF** — Numéro d'Identification Fiscale (Mali, Niger).
- **NINEA** — Numéro d'Identification Nationale des Entreprises et des Associations (Sénégal).
- **OFNAC** — Office National de lutte contre la Fraude et la Corruption (Sénégal).
- **OHADA** — Organisation pour l'Harmonisation en Afrique du Droit des Affaires.
- **OIT / ILO** — Organisation Internationale du Travail / International Labour Organization.
- **PAR / RAP** — Plan d'Action de Réinstallation / Resettlement Action Plan.
- **PGES** — Plan de Gestion Environnementale et Sociale.
- **PII** — Personally Identifiable Information.
- **P&C** — Principles & Criteria (RSPO).
- **Proparco** — Filiale AFD pour le financement du secteur privé.
- **RCCM** — Registre du Commerce et du Crédit Mobilier (OHADA, uniforme).
- **RLS** — Row-Level Security (PostgreSQL).
- **RPO / RTO** — Recovery Point / Time Objective.
- **RSPO** — Roundtable on Sustainable Palm Oil.
- **SASB** — Sustainability Accounting Standards Board (intégré ISSB).
- **SGES** — voir ESMS.
- **SIB** — Société Ivoirienne de Banque.
- **SLA** — Service Level Agreement.
- **SME** — Small and Medium Enterprise (= PME).
- **SMETA** — Sedex Members Ethical Trade Audit.
- **SMIG** — Salaire Minimum Interprofessionnel Garanti.
- **SUNREF** — Sustainable Use of Natural Resources and Energy Finance (AFD).
- **TCFD** — Task Force on Climate-related Financial Disclosures.
- **TLS** — Transport Layer Security.
- **UEMOA** — Union Économique et Monétaire Ouest-Africaine.

## Annexe H — Dépendances PRD ↔ Dettes P1 audit 18-specs

Mapping des FR du PRD vers les dettes P1 de l'audit `spec-audits/index.md`. Sert de pont concret entre dette audit et livrables PRD.

| FR PRD | Dépendance audit P1 | Statut dette | Phase 0 / story suggérée |
|---|---|---|---|
| FR12 (OCR validation maturité) | P1 #8 OCR bilingue FR+EN | ✅ résolu story 9.4 | — |
| FR17 (anonymisation PII) | Nouveau (SC-T10) | Nouveau | Phase 0 `anonymisation-pii-llm` |
| FR24 (admin catalogue real-time) | P1 audit hard-coding (SECTOR_WEIGHTS, seeds) | À ouvrir | Phase 0 `admin-catalogue-crud` |
| FR31 (update intermediaires real-time) | P1 #11 tests Financing + P2 #18 versioning intermédiaires + P2 #19 admin CRUD | À ouvrir | Phase 0 `admin-funds-intermediaires-crud` |
| FR36 (génération livrables) + FR40 (signature) + FR41 (blocage > 50k) + FR44 (SGES BETA NO BYPASS) | P1 #10 guards LLM sur contenus persistés + P2 #20 tests contenu PDF | À ouvrir | Phase 0 `guards-llm-universels` |
| FR39 (snapshot propre) | Signal PRD 5 (audit) — snapshot absent specs 008/010 | À ouvrir | Phase 0 `snapshot-systematique` |
| FR54 (logs JSON + request_id) + FR38-NFR38 (instrumentation tools) | P1 #14 `with_retry` + `log_tool_call` aux 9 modules | À ouvrir | Phase 0 `observability-metier-tools` |
| FR59 (RLS 4 tables) | Nouveau (NFR12) | Nouveau | Phase 0 `rls-postgresql-critiques` |
| FR62 (NFR-SOURCE-TRACKING) | Nouveau (NFR27) | Nouveau | Phase 0 `catalog-sourcing-documentaire` |
| FR63 (test CI HTTP 200) | Nouveau | Nouveau | Phase 0 `ci-nightly-source-url-check` |
| FR70 (RAG ≥ 5 modules) | P1 #13 FR-005 RAG non tenue spec 009 | À ouvrir | Phase 0 `rag-transversal-8-modules` |
| FR55–56 (monitoring admin + alerting) | P1 #14 (partiellement) | À ouvrir | Phase 0 (groupée avec observability-metier-tools) |
| FR36–44 génération livrables (migration) | P1 #6 queue asynchrone Celery | À ouvrir en Phase Growth | Post-MVP |
| FR46 (active_project + active_module) | Signal PRD 2 (audit) — enforcement applicatif | À ouvrir | Phase 0 `enforcement-context-actif` |
| Rich blocks dashboard | Signal PRD 4 + P3 #1 `MessageParser` registre extensible | À ouvrir | Phase 0 `registre-blocs-visuels` |

**Résumé :** 10 stories Phase 0 identifiées couvrant la dette P1 audit restante (10 sur 14, 4 déjà résolues : rate limiting, quota stockage, OCR bilingue, flag édition manuelle).

## Annexe I — Stack existante à conserver / compléter / remplacer

| Composant | Statut | Raison |
|---|---|---|
| **LangGraph orchestration** | À CONSERVER | Pattern éprouvé, base des 9 nœuds actuels + 2–3 nouveaux en extension |
| **pgvector + text-embedding-3-small** | À CONSERVER | RAG opérationnel, à étendre aux 8 modules (P1 #13) |
| **Streaming SSE** | À CONSERVER | Pattern validé depuis spec 002, support natif LangGraph `astream_events` |
| **JWT stateless + refresh token** | À CONSERVER | Validé, à compléter avec MFA (`admin_mefali`, `admin_super`, step-up) |
| **LangGraph MemorySaver checkpointer** | À CONSERVER | Reprise session + atomicité soumissions (NFR30) |
| **Filtre WHERE applicatif SQLAlchemy** | À COMPLÉTER | Ajout RLS PostgreSQL Phase 0 sur 4 tables sensibles (`companies`, `fund_applications`, `facts`, `documents`) — NFR12 |
| **Stockage local `/uploads/`** | À MIGRER | Phase Growth vers S3 EU-West-3 + backup géographique 2 AZ |
| **Rate limiting SlowAPI chat (30/min)** | À COMPLÉTER | Extension Phase Growth aux tools coûteux (PDF, SGES) — NFR17 |
| **Hard-coding catalogue (12 fonds, 14 intermédiaires, SECTOR_WEIGHTS, SECTOR_BENCHMARKS, facteurs émission)** | À REMPLACER | Phase 0 par tables BDD + interface admin (NFR-ADMIN-LEVELS N1/N2/N3) |
| **Prompts directifs accumulés (4 spec-correctifs 013/015/016/017)** | À REFACTORER | Phase 0 framework injection unifié (signal PRD 3) |
| **9 nœuds LangGraph existants** | À ÉTENDRE | + 2–3 nouveaux nœuds (projet / maturité entreprise / admin catalogue) Phase 1 |
| **Dashboard existant (4 cartes + financements)** | À ÉTENDRE | Phase 3 avec registre typé de 11 blocs visuels + personas différenciées |
| **Plan d'action (module 011)** | À ÉTENDRE | Phase 1 avec `FormalizationPlan` + nouveaux types de rappels (certifs, expiration faits, MàJ référentiels) |
| **OCR Tesseract fra+eng** | À CONSERVER | Livré story 9.4 ; extension `por` Phase Vision |
| **WeasyPrint + Jinja2 + python-docx** | À CONSERVER + ÉTENDRE | Base existante Cluster C ; extension pyramide `DocumentTemplate` → `ReusableSection` → `AtomicBlock` |
| **Baseline 1100+ tests verts + zero failing on main** | À PRÉSERVER | Principe operationnel depuis 17 avril 2026 — garantie Phase 0 non négociable (SC-T2, NFR59) |
| **Conventions CLAUDE.md** | À ÉTENDRE | Documentation nouveaux modules avec conventions existantes (anglais code, français commentaires, dark mode obligatoire, etc.) |

**Principe directeur :** Phase 0 ne remplace pas ce qui fonctionne — elle **complète** ce qui manque (RLS, admin UI, RAG transversal, observabilité métier) et **refactore** ce qui est bloquant pour les 5 clusters (hard-coding catalogue, framework d'instructions, context actif). Éviter tout « refactor creep » non justifié par une dette P1 audit ou une dépendance cluster.

---

*Fin des annexes. PRD complet au 2026-04-18.*









