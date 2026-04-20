---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/implementation-artifacts/spec-audits/index.md
session_topic: "Exploration des évolutions ESG Mefali avant PRD d'extension — regroupement en 4 clusters + 1 transverse par dépendance fonctionnelle"
session_goals: "Révéler implications cachées, dépendances croisées, prérequis (dettes P1), priorités P0/P1/P2, personas impactés, questions ouvertes à clarifier avant PRD"
selected_approach: 'cluster-driven AI-recommended facilitation'
techniques_used: []
ideas_generated: []
context_file: '_bmad-output/implementation-artifacts/spec-audits/index.md'
clusters:
  - A: "Maturité PROJET (data model + cycle de vie projet)"
  - A_prime: "Maturité ENTREPRISE (jumeau symétrique — ex-Transverse T)"
  - B: "Référentiel ESG multi-contextuel (pilier scoring)"
  - C: "Moteur de livrables multi-destinataires (output — absorbe étude d'impact)"
  - D: "Expérience & accompagnement utilisateur (UX, parallèle)"
central_abstraction: "Cube de qualification bailleur = Projet × Entreprise × Référentiel"
dissolved_items:
  - "Étude d'impact (ex-évolution 5) — dissoute dans B (grille scoring impact) + C (templates de livrables : EIES réglementaire, EIES bailleur, LCA, EUDR, PAR, auto-éval)"
---

# Brainstorming Session Results

**Facilitator:** Angenor
**Date:** 2026-04-18

## Session Overview

**Topic :** Exploration de 6 évolutions candidates pour un PRD d'extension ESG Mefali — financement de projet (vs entreprise), profil dynamique multi-projets, dossier projet/entreprise, critères ESG relatifs, étude d'impact, dashboard plus graphique.

**Goals :**
- Révéler les implications architecturales cachées de chaque évolution
- Identifier les dépendances croisées
- Prioriser (P0/P1/P2) et séquencer les évolutions
- Cartographier les personas impactés
- Lister les prérequis (dettes P1 de l'audit 18-specs à fixer avant)
- Produire des questions ouvertes à clarifier avant le PRD

### Context Guidance

Contexte chargé depuis `_bmad-output/implementation-artifacts/spec-audits/index.md` (audit des 18 specs existantes).

**Signaux PRD prioritaires à intégrer :**
1. **Data-driven vs hard-coded** — Tables `fund`, `intermediary`, `esg_sector_config`, `carbon_emission_factor`, `regulation_reference` + interface admin.
2. **Saturation du pattern « prompts directifs »** — 4 spec-correctifs consécutives (013/015/016/017) ; passer à un enforcement applicatif (state machines, guards pré-tool, agents dédiés).
3. **Framework d'injection d'instructions** — 3 instructions transverses dupliquées (STYLE + WIDGET + GUIDED_TOUR) ; refactor préventif avant 2-3 nouvelles.
4. **Rich blocks extensibles** — Registre de blocs visuels attendu pour le dashboard enrichi.
5. **Snapshot des données source** — Obligatoire pour profil dynamique et étude d'impact.
6. **RAG transversal** — Promesse FR-005 de la spec 009 non tenue (1/8 modules) ; étude d'impact et dossier projet en bénéficieraient directement.

**Enrichissement métier à garder en tête :**
- Le consultant ESG ouest-africain est tiré par les bailleurs (IFC PS1–PS8, Équateur, BAD SSI), les clients export (EUDR, CS3D, SMETA, EcoVadis), et non par une CSRD locale.
- Missions typiques : diagnostic E&S, SGES/ESMS, EIES, PGES, PAR/RAP, certifications sectorielles (RSPO, Rainforest, Fairtrade), anti-corruption, contenu local, adaptation climatique.
- Cœur du métier : traduire les standards internationaux dans le contexte opérationnel local — ce qui éclaire directement l'évolution « critères ESG relatifs » et « étude d'impact ».

### Session Setup — Regroupement validé

**Constat initial :** 6 évolutions listées par l'utilisateur + 10 fonctionnalités émergeant d'une recherche sur le rôle du consultant ESG en Afrique de l'Ouest = **16 items candidats**.

**Regroupement par dépendance (validé) :**

```
         [Transverse T : Formalisation informel→formel]
                         │
                         ▼
        ┌────────────────┴────────────────┐
        │                                 │
   [A: Company×Project]          [B: ESG multi-contextuel]
        │                                 │
        └────────────────┬────────────────┘
                         ▼
              [C: Moteur livrables]

   [D: UX/Dashboard/Formation] ──► parallèle, largement indépendant
```

**Cluster A — Unité d'analyse (data model projet/entreprise)**
Items : financement de projet, profil dynamique multi-projets, dossier projet/entreprise, étude d'impact projet ou entreprise.

**Cluster B — Référentiel ESG multi-contextuel**
Items : critères ESG relatifs, SGES/ESMS aligné IFC PS1–PS8, référentiels bailleurs & certifications sectorielles, renforcement S (communautés/contenu local), G (anti-corruption OHADA/ITIE), E (adaptation climatique physique).

**Cluster C — Moteur de livrables multi-destinataires**
Items : conformité clients export (EUDR/CS3D/SMETA/EcoVadis), reporting extra-financier (GRI/TCFD/CDP/IFC AIMM), livrables extractifs/agro-industriels (EIES/PGES/PAR).

**Cluster D — Expérience & accompagnement**
Items : dashboard plus expressif et graphique, formation & renforcement de capacités par rôle.

**Transverse T — Formalisation informel→formel**
Parcours d'onboarding spécifique (prérequis utilisateur pour ~90 % des PME AO).

**Questions d'attribution encore ouvertes :**
- Étude d'impact placée dans A (jambe data) mais a aussi une jambe forte dans B (référentiel d'évaluation d'impact).
- Certifications sectorielles placées dans B (grille de critères) mais pourraient être lues comme un livrable en C.
→ Ces chevauchements seront re-discutés lors de la facilitation du cluster concerné.

---

## Cluster A — Maturité PROJET — Synthèse (FERMÉ)

**Technique utilisée :** Morphological Analysis + Assumption Reversal

### Dimensions morphologiques identifiées

| Dimension | Valeurs | Insight terrain |
|---|---|---|
| Granularité | mono-projet / multi-projets | L'entreprise mono-projet est un cas dégénéré où `Company = Project` |
| Maturité du projet | idée → faisabilité → bancable → exécution → achevé | La majorité des bailleurs verts financent AVANT démarrage, pas après |
| Porteur | solo / coopérative / GIE / PPP / cluster agri | N:N `Project × Company` avec rôle (porteur principal, co-porteur, bénéficiaire) |
| Cycle de vie | objet vivant sur 5–10 ans | IFC AIMM et Proparco exigent reporting annuel post-financement |
| Face exposée | profil complet vs vue curée par fonds | Naissance de `CompanyProjection` |
| Unicité | `1 Project × N FundApplications × N CompanyProjections` | Contre l'intuition « 2 projets distincts » — évite les contradictions d'impact |

### Modèle de données émergent

```
Company ────┬──► ProjectMembership (rôle) ◄──┬──── Project
            │                                 │     ├─ lifecycle_state
            │                                 │     ├─ maturity_level
            │                                 │     └─ realite physique unique
            │                                 │
            ▼                                 ▼
       CompanyProjection ◄────────────── FundApplication
       (vue curée par fonds)             ├─ narratif calibré fonds
                │                         ├─ budget adapté bailleur
                │                         └─ snapshot(Project, Projection, date)
                │                                │
                └────────────────┬───────────────┘
                                 ▼
                         Fund (table BDD)
                         └─ instruments acceptés × maturité × seuils
```

### Prérequis P1 (dettes audit 18-specs à fixer AVANT)

| Dette | Source audit | Pourquoi bloquant |
|---|---|---|
| Tables `fund`/`intermediary` en BDD | Signal PRD 1 | `Fund` doit porter instruments × maturité × seuils — impossible en hard-code |
| Snapshot propre | Signal PRD 5 | `FundApplication` doit figer l'état à soumission (absent specs 008/010) |
| Enforcement applicatif du contexte actif | Signal PRD 2 | Le routeur doit maintenir `active_project` en plus de `active_module` |
| Framework injection instructions | Signal PRD 3 | 6 nœuds LangGraph devront recevoir le `Project` en contexte |
| Migration existante | Nouveau | Convertir les `Company` actuelles en `(Company, default Project)` ou garder Company-only comme cas valide |

### Personas impactés (nouveaux / modifiés)

- **Entrepreneur mono-projet** — cas simple, rétro-compatible (Project unique implicite)
- **Entrepreneur multi-projets** — nouveau persona à part entière (sélecteur de projet actif dans le chat)
- **Coopérative / GIE / PPP** — nouveau persona à rôle collectif (consortium)
- **Consultant ESG externe** — suit N PME × N projets → tableau croisé requis
- **Admin Mefali** — gère les référentiels fonds (instruments, maturités, seuils)
- **Bailleur** — jamais utilisateur, mais contraint fortement la structure (instruments, catégorisation A/B/C)

### Priorité : **P0** (racine absolue — A', B, C en dépendent)

### Questions ouvertes (à trancher au PRD)

- **QO-A1** — Un `Project` peut-il exister sans `Company` rattachée (startup en pré-création, à enregistrer) ? → Plus probablement non : Company est obligatoire, même en niveau 0.
- **QO-A2** — Rôles dans un consortium : enum fixe (porteur/co-porteur/bénéficiaire) ou liste libre ? → Penche vers enum fixe + libellé libre.
- **QO-A3** — Stratégie de migration : les `Company` actuelles deviennent-elles `Company + default Project` ou restent-elles mono-entité ?
- **QO-A4** — Comment gérer les changements de scope projet post-financement sans casser les snapshots ? → Versioning du Project.
- **QO-A5** — Un `FundApplication` peut-il être cloné vers un autre fond (re-calibré), ou chaque soumission est-elle écrite à zéro depuis le `Project` ?

### Idées générées — comptage

6 dimensions morphologiques, 6 entités/relations data, 5 prérequis P1, 6 personas, 5 questions ouvertes.

---

## Cluster A' — Maturité ENTREPRISE — Synthèse (FERMÉ)

**Technique utilisée :** Attribute Listing + propositions cadrées terrain.

### Les 4 niveaux (validés)

| Niveau | Documents-preuves | Bailleurs débloqués |
|---|---|---|
| **0 — Informel pur** | Mobile money, oral, pas de RCCM | Aucun direct — via IMF/ONG proxy uniquement |
| **1 — RCCM + NIF** | Registre commerce OHADA + identifiant fiscal pays | Microfinance verte, FEM SGP <50k USD, FNDE |
| **2 — Comptes + cotisations** | Niveau 1 + comptabilité + CNPS/IPRES | SUNREF, BOAD small, banques vertes locales |
| **3 — OHADA audité** | Niveau 2 + SARL/SA + bilan annuel audité | GCF, FEM full, BAD, IFC, Proparco, SUNREF grand |

### Dimensions / Attributs identifiés

| Attribut | Valeurs |
|---|---|
| Niveau administratif | 0 / 1 / 2 / 3 |
| Mode de détection | Auto-déclaration + validation progressive OCR (mix) |
| Plan d'accompagnement | Génération par Claude d'un parcours N → N+1 (cf. module 011 plan d'action) |
| Scoring coopérative | Admin = porteur seul ; Bénéficiaires = profil agrégé séparé |
| Dimension pays | Structure uniforme 4 niveaux ; preuves paramétrées par pays via `AdminMaturityRequirement(country × level)` |

### Modèle de données émergent

```
Company ──┬── AdminMaturityLevel
          │    ├─ declared_level (auto-déclaré)
          │    ├─ validated_level (validé par OCR / humain)
          │    ├─ last_validation_at
          │    └─ snapshot historique
          │
          ├── FormalizationPlan (plan Claude N → N+1)
          │    ├─ actions[] (RCCM à obtenir, NIF à demander, comptable à recruter...)
          │    ├─ estimated_cost_fcfa
          │    └─ duration_weeks
          │
          └── BeneficiaryProfile  (cas coopérative / GIE / cluster)
               ├─ aggregate_count
               ├─ gender_breakdown
               ├─ avg_income_fcfa
               └─ informality_rate_pct

AdminMaturityRequirement (country × level) ──► documents requis (libellé local)
```

### Prérequis P1

| Dette | Statut | Commentaire |
|---|---|---|
| OCR multi-format | ✅ Existant (module 004) | Réutilisable — OCR déjà testé FR/EN |
| Plan d'action / rappels | ✅ Existant (module 011) | À étendre pour inclure actions de type `formalization` |
| Data-driven par pays | ❌ Nouveau | Table `AdminMaturityRequirement` — cf. signal PRD 1 |
| Snapshot du niveau | ❌ Nouveau | `FundApplication` doit figer le niveau admin à la soumission |

### Personas impactés

- **Entrepreneur informel hésitant** — parcours guidé, niveau dégradé mais action possible via proxy
- **Porteur de coopérative** — scoring dédié (porteur niveau X + bénéficiaires profil agrégé)
- **Admin Mefali** — maintenance des `AdminMaturityRequirement` par pays (interface admin requise)
- **Juriste local / comptable** — jamais utilisateur direct mais le `FormalizationPlan` le mentionne comme ressource

### Priorité : **P1** (bloquant pour ~90 % des PME AO, mais pas racine comme A)

### Questions ouvertes

- **QO-A'1** — Qui valide définitivement un document uploadé ? OCR automatique (risque erreur) ou humain en boucle (coût, latence) ?
- **QO-A'2** — Confidentialité : les documents (RCCM, NIF, bilan) sont-ils stockés en silo (utilisateur seul) ou partageables au bailleur dans le dossier ?
- **QO-A'3** — Niveau intermédiaire (RCCM OK mais comptes partiels) : arrondi au niveau inférieur ou sous-niveaux (1.5) ?
- **QO-A'4** — Formalisation vs conformité fiscale courante : peut-on avoir RCCM en règle + défaut de paiement impôts ? Scoring distinct ?
- **QO-A'5** — Régression : si entreprise perd un document (liquidation partielle, radiation), redescente de niveau + notification ?

### Idées générées

4 niveaux, 5 attributs, 4 entités data, 4 prérequis, 4 personas, 5 questions ouvertes.

---

## Cluster B — ESG multi-contextuel

**Technique utilisée :** Five Whys + propositions cadrées + décisions architecturales.

### B.1 — Diagnostic + architecture retenue

**Diagnostic des 3 gels actuels (priorisation a priori — pas de retour terrain) :**

| Gel | Douleur | Facilité déblocage | Séquence |
|---|---|---|---|
| Critères figés | 🔴 Haute | Difficile | **D'abord** |
| Pondérations sectorielles | 🟡 Moyenne | Facile | Parallèle |
| Benchmarks sectoriels | 🟢 Faible | Facile mais dépend de données externes | En dernier |

**Décision architecturale : option (c') — grille composable + packs pré-assemblés**

- **En interne** : chaque critère est un atome sémantique avec métadonnées (référentiels applicables, secteurs, tailles, maturité entreprise)
- **En façade** : packs lisibles (« Pack IFC PS bancable », « Pack RSPO premium », « Pack artisan minimal ») qui masquent la complexité à l'utilisateur final
- **Grille d'évaluation** = résultat d'une requête contextuelle sur le catalogue

**Architecture à 3 couches (décision majeure) :**

```
┌─────────────────────────────────────────────────┐
│ C3 — VERDICTS par référentiel                   │
│      ex : IFC=PASS, RSPO=PASS, ISO=system-needed│
│      Dérivation automatique via règles          │
├─────────────────────────────────────────────────┤
│ C2 — CRITÈRES composables                       │
│      Brique sémantique avec :                   │
│       - référentiels applicables[]              │
│       - secteurs concernés[]                    │
│       - tailles concernées[]                    │
│       - faits agrégés[]                         │
│       - règle de décision                       │
├─────────────────────────────────────────────────┤
│ C1 — FAITS atomiques                            │
│      Quantitatifs (BOD, volumes, %, tCO2e)      │
│      Qualitatifs attestables (CLIP, grief)      │
│      Versionnés dans le temps (refresh annuel)  │
│      Liés à des preuves documentaires           │
└─────────────────────────────────────────────────┘
```

**Règle centrale :**
- On évalue **une seule fois les faits** (C1) — pas de re-saisie utilisateur.
- Un nouveau référentiel = on écrit ses **règles de dérivation** (C3) depuis les faits existants.
- Support RAG naturel (signal PRD 6) : chaque règle peut citer sa source documentaire.
- Snapshot propre (signal PRD 5) : fige faits + règles actives à la date d'évaluation.

**Chantier taxonomique accepté** — catalogue de plusieurs centaines de faits atomiques à constituer.

### Entités data émergentes

```
Fact ───────────────┐
 ├─ code                 ← "water_effluent_bod"
 ├─ type                 ← quantitatif | qualitatif attestable
 ├─ unit                 ← "mg/L"
 ├─ value                ← 30
 ├─ measured_at          ← 2026-04-18
 ├─ evidence[]           ← FK uploads
 └─ valid_until          ← date d'expiration (annuel)
                         
Criterion ──────────────┐
 ├─ code                 ← "water_management"
 ├─ applicable_refs[]    ← [IFC_PS3, ISO_14001, RSPO_5_3, GRI_303]
 ├─ applicable_sectors[] 
 ├─ applicable_sizes[]
 ├─ facts_required[]     ← FK Fact.code
 └─ decision_rule        ← expression DSL ou code

ReferentialVerdict ─────┐
 ├─ referential          ← "IFC_PS3"
 ├─ criterion_id
 ├─ verdict              ← PASS | FAIL | REPORTED | N/A
 ├─ derivation_trace     ← explication auditée
 └─ derived_at

Pack ───────────────────┐
 ├─ code                 ← "ifc_bancable_pack"
 ├─ label                ← "Pack IFC PS bancable"
 └─ criteria_selection[] ← requête paramétrée ou liste statique
```

### Prérequis P1 additionnels B.1

- **Interface admin** (signal PRD 1) — gestion du catalogue de faits + critères + règles + packs
- **Versioning temporel** — les faits expirent, les règles évoluent (nouvelle version IFC PS)
- **Migration des 30 critères actuels** — chaque critère existant doit être re-exprimé en termes de faits + règle

### B.2 — Multi-référentiel : catalogue, gouvernance, évolution

**Priorisation (validée Q16) :**

| Priorité | Catégories | Raison |
|---|---|---|
| **P0** | Bailleurs (IFC PS, GCF, BAD, BOAD, SUNREF) + EUDR | Accès financement + survie commerciale |
| **P1** | Certifs sectorielles (RSPO, Rainforest) + ISO 14001 | Secteurs dominants AO |
| **P2** | GRI/TCFD/CDP + Régional (RSE SN/CI) + Impact (AIMM, IRIS+) | Grandes entreprises + émergent |

**Gouvernance du catalogue (validé Q17 — a puis b) :**

- **Phase 1 (bootstrap)** — équipe Mefali uniquement (qualité contrôlée)
- **Phase 2 (ouverture)** — consultants ESG partenaires certifiés après stabilisation
- Pattern : « bootstrap contrôlé → ouverture progressive »

**Évolution temporelle des référentiels (proposé Q18) :**

- Chaque référentiel porte une **version** (`IFC_PS@2012`, `IFC_PS@2025`) avec date de mise en vigueur
- Évaluations passées **snapshotent la version active** → restent auditables, jamais invalidées
- Publication nouvelle version → génération automatique d'un `MigrationPlan` (faits changés, critères bougés, étapes proposées)
- Notification via rappels (module 011 existant)
- Transition gracieuse : `FundApplication` en cours peut finaliser sur ancienne version ou rebasculer volontairement

**Affichage scoring (proposé Q19 — option c) :**

- Score global `/100` pondéré depuis les référentiels actifs
- Drill-down par référentiel avec verdicts détaillés (PASS/FAIL/REPORTED/N/A)
- Couleur sémantique pour référentiels en difficulté
- Justification auditable : chaque score trace sa décomposition

**Entités data additionnelles B.2 :**

```
Referential ────────────┐
 ├─ code                 ← "IFC_PS3"
 ├─ version              ← "2012" | "2025"
 ├─ effective_date
 └─ parent_group         ← "IFC_PS"

ReferentialMigration ───┐
 ├─ from_version
 ├─ to_version
 ├─ changed_facts[]
 ├─ changed_criteria[]
 └─ migration_steps[]
```

### B.3 — Relativité réelle : relatif à quoi ?

**Dimensions de contextualisation (validées Q20) — métadonnées du critère composable :**

| Dimension | Valeurs type | Source donnée |
|---|---|---|
| Secteur | agroalim, commerce, artisanat, construction, transport, énergie, mines | Profil entreprise |
| Taille | TPE (<10) / petite (10–49) / moyenne (50–249) | Profil entreprise |
| Maturité entreprise | 0–3 (cluster A') | A' |
| Maturité projet | idée → achevé (cluster A) | A |
| Fonds ciblé | GCF, FEM, BOAD, BAD, IFC, Proparco | FundApplication |
| Pays | CI, SN, BF, BJ, TG, ML, NE, GH, NG, LR, SL | Profil |
| Zone agroécologique | sahel / soudanien / forêt / littoral | Géoloc projet |
| Filière export | cacao, coton, anacarde, palme / interne | Profil projet |

→ Grille d'évaluation = **requête multi-dimensionnelle** sur un catalogue de 500+ critères. Retour : sous-ensemble pertinent de 30–60 critères.

**Pondération (validé Q21) :** portée par le **Pack**, pas par le critère.
- Critère composable neutre, réutilisable
- Pack définit ses propres pondérations (ex. Pack IFC bancable = 40 % E / 30 % S / 30 % G)

**Seuils (validé Q22) :** portés par le **référentiel (C3)**, pas par le critère (C2).
- Même fait `bod = 40 mg/L` → IFC PS3 = FAIL, norme CI = PASS (seuil 50) → cohérent et auditable

### B.4 — Renforcements AO (S / G / E)

**Intégration (validé Q23) :** au catalogue, avec **tags thématiques** (`community_relations`, `local_content`, `climate_adaptation`, `anti_corruption`). Packs régionaux AO sur-pondèrent ces tags.

**Adaptation climatique (validé Q24) :** extension du module carbone (007) — pas de nouveau module. Ajout de faits :
- `zone_climatic_risk`, `flood_exposure_score`, `drought_vulnerability_index`, `adaptation_measures[]`
- Cohérent avec TCFD (physical + transition risks)

**Anti-corruption (validé Q25) :** scoring gradué aligné IFC PS1 / ISO 37001

| Niveau | Preuve | Score |
|---|---|---|
| 0 | Rien | 0 % |
| 1 | Politique formalisée | 25 % |
| 2 | + Formation équipes | 50 % |
| 3 | + Due diligence fournisseurs | 75 % |
| 4 | + Audit ISO 37001 | 100 % |

**Renforcement S (validé Q26) :** nouveaux critères composables tag `community_relations` :
- CLIP obtenu (qualitatif attestable)
- Mécanisme de grief opérationnel
- Taux d'emploi local (< 50 km)
- Taux sous-traitance locale (< 100 km)
- Investissement communautaire (% CA)
- Taux de femmes employées + promotions
- Traçabilité absence travail des enfants (cacao, coton)

---

## Cluster B — Synthèse (FERMÉ)

### Décisions majeures

1. **Architecture 3 couches** : Faits (C1) → Critères composables (C2) → Verdicts par référentiel (C3)
2. **Option (c')** : grille composable + packs pré-assemblés en façade
3. **Catalogue centralisé** (phase 1) puis partenaires certifiés (phase 2)
4. **Versioning** des référentiels avec snapshot + MigrationPlan
5. **Score global pondéré + drill-down** par référentiel
6. **Pondération au niveau Pack**, seuils au niveau Référentiel
7. **Renforcements AO** via tags, pas via modules séparés
8. **Adaptation climatique** = extension du module carbone 007

### Priorité : **P0** (corrélée au cluster A — démarrer simultanément)

### Prérequis P1 spécifiques B

- Interface admin (signal PRD 1) — catalogue faits + critères + règles + packs
- Versioning temporel (versions référentiels, expiration des faits)
- Migration des 30 critères actuels vers le nouveau modèle
- Moteur RAG transversal (signal PRD 6) — chaque règle peut citer sa source

### Questions ouvertes B

- **QO-B1** — Comment gérer un critère obsolète ? (archivage, pas suppression — pour traçabilité historique)
- **QO-B2** — Faut-il introduire un concept de `FactProvenance` pour tracer **qui** a saisi un fait (entreprise, consultant, tool IA, OCR) ?
- **QO-B3** — Scoring d'une évaluation partielle : si 60 % des faits sont saisis, calculer un score partiel ou bloquer ?
- **QO-B4** — Faits conflictuels (deux sources disent des choses différentes) : qui arbitre ?
- **QO-B5** — Performance : une requête de sélection de critères multi-dimensionnelle sur 500+ critères + 50 référentiels — optimisation requise (index, cache) ?

### Idées générées Cluster B

8 dimensions contextuelles, 7 entités data, 4 classes renforcement AO, 5 prérequis, 5 questions ouvertes, ~35 idées structurelles.

---

## Cluster C — Moteur de livrables multi-destinataires — Synthèse (FERMÉ)

**Technique utilisée :** SCAMPER + propositions directes validées.

### C.1 — Architecture pyramidale (3 niveaux)

```
┌─────────────────────────────────────────────────┐
│ N3 — DocumentTemplate (par destinataire)        │
│      "IFC_AIMM_annual_report",                  │
│      "RSPO_certification_dossier",              │
│      "EUDR_due_diligence_statement",            │
│      "EIES_bailleur_catA",                      │
│      "GCF_funding_proposal",                    │
│      "Proparco_AIMM_report",                    │
│      "Sedex_SMETA_4pillar",                     │
│      "GRI_sustainability_report_core",          │
│      "TCFD_climate_disclosure"                  │
├─────────────────────────────────────────────────┤
│ N2 — ReusableSection (par thème)                │
│      "company_presentation",                    │
│      "project_summary", "esg_scoring",          │
│      "action_plan", "evidence_annex",           │
│      "carbon_footprint", "risk_matrix"          │
├─────────────────────────────────────────────────┤
│ N1 — AtomicBlock (par composant)                │
│      narratif, tableau faits, graphique,        │
│      verdicts, carte, annexe, charte, timeline  │
└─────────────────────────────────────────────────┘
```

**Stack :** Jinja2 + WeasyPrint (existant module 006) — étendu. Templates en BDD (signal PRD 1).

**Connexion B ↔ C :** les blocs N1 puisent dans Faits (C1-B), Verdicts (C3-B) et narratifs `FundApplication`. **Aucune re-saisie**.

### C.2 — Formats de sortie

| Format | Outil | Usage |
|---|---|---|
| PDF | WeasyPrint | Livrable officiel figé |
| DOCX | python-docx | Éditable consultant/révision |
| HTML | Natif | Preview + partage web |
| XLSX | openpyxl | Tableaux exportables |

### C.3 — Preuves documentaires

- Annexe automatique des preuves des faits mobilisés
- Mode sélectif (cocher/décocher)
- Fichiers > 10 Mo → URL signée plutôt qu'inline

### C.4 — Évolution des templates

- Versioning (miroir référentiels)
- Notification proactive sur MàJ bailleur
- Re-génération à la demande

### C.5 — Multi-langue

| Destinataire | Langue défaut |
|---|---|
| Bailleur international (IFC, GCF, Proparco int.) | EN (toggle FR) |
| Régulateur local (ANDE, DEEC, BUNEE) | FR |
| Client export EU | Langue client (EN/FR/ES/PT) |
| Bailleur régional (BOAD, BAD) | FR (toggle EN) |

### C.6 — Signatures (hors MVP phase 1)

- **MVP** : PDF imprimable avec espaces signature visibles
- **Post-MVP** : DocuSign ou solution eIDAS-qualifiée

### C.7 — Priorité

**P1** — démarre après A + B (dépendance forte).
Premier lot MVP : `GCF_funding_proposal`, `IFC_AIMM_report`, `EUDR_dds`, `EIES_bailleur_catB`.

### Entités data émergentes

```
DocumentTemplate ──────┐
 ├─ code, version, effective_date
 ├─ target_audience     ← bailleur | régulateur | client_eu | investisseur | interne
 ├─ sections[]          ← FK ReusableSection
 ├─ output_formats[]    ← [pdf, docx]
 └─ language

ReusableSection ───────┐
 ├─ code
 ├─ blocks[]            ← FK AtomicBlock
 └─ data_requirements   ← quels faits, verdicts, narratifs

AtomicBlock ───────────┐
 ├─ code
 ├─ type                ← narrative | fact_table | chart | verdict_table | map | annex | timeline
 └─ template_snippet    ← fragment Jinja2

GeneratedDocument ─────┐
 ├─ template_id + version
 ├─ fund_application_id (FK optionnel)
 ├─ project_id (FK optionnel)
 ├─ snapshot_hash       ← immutabilité
 ├─ output_url (PDF/DOCX)
 └─ generated_at
```

### Questions ouvertes C

- **QO-C1** — Génération streaming vs batch (gros dossiers minutes) → file Celery post-MVP ?
- **QO-C2** — Gabarits non officiels imposés par bailleur spécifique → import DOCX + mapping assisté ?
- **QO-C3** — Immutabilité livrable soumis → snapshot + hash (proposition : **OUI**).
- **QO-C4** — Traductions automatiques narratifs (EN↔FR) → IA avec review humaine optionnelle (proposition : **IA + review opt**).
- **QO-C5** — Archivage long terme (5–10 ans reporting IFC AIMM) → politique de rétention à définir.

### Idées générées Cluster C

9 templates MVP, 7 sections réutilisables, 8 blocs atomiques, 4 formats sortie, 4 personas linguistiques, 5 questions ouvertes, ~25 idées structurelles.

---

## Cluster D — UX / Dashboard / Formation — Synthèse (FERMÉ)

**Technique utilisée :** propositions directes + correction positionnement.

### D.1 — Dashboard : registre de blocs extensibles (signal PRD 4)

Registre unique typé + versionné (évite système parallèle — leçon spec 018).

| Type de bloc | Usage typique |
|---|---|
| KPI card | Score ESG, tCO2e, financement obtenu |
| Donut / pie | Répartition E/S/G, mix énergétique |
| Barres (stacked/grouped) | Évolution temporelle, comparaison sectorielle |
| Timeline | Échéances bailleurs, jalons projet, renouvellements certifs |
| Carte géo | Projets par pays/région, zones risque climatique |
| Heatmap | Risques E/S/G par projet × critère |
| Gauge | Progression cible (score, formalisation) |
| Table croisée | Vue multi-projets |
| Radar | Comparatif multi-référentiel |
| Waterfall | Décomposition score |
| Sankey | Flux financement, chaîne d'approvisionnement |

Stack : Chart.js (existant) + registre TypeScript typé.

### D.2 — Personas MVP (corrigés — Option 1 pure)

⚠️ **Correction positionnement :** persona « consultant ESG multi-PME » retiré. Mefali démocratise l'ESG aux PME, il ne sert pas les consultants.

| Persona | Vue | Densité |
|---|---|---|
| Entrepreneur solo mobile | 4–5 KPIs, action suivante | Très basse |
| Entrepreneur multi-projets | Sélecteur projet + tabs | Moyenne |
| Dirigeant / executive | Executive summary, top 5 risques | Moyenne |
| Équipes fonctionnelles (HSE, RH, achats, financier, comm) | Vue rôle-spécifique | Basse-moyenne |
| Admin Mefali | Vue système (catalogue, référentiels) | Très haute |

### D.3 — Contextualisation AO

- Mode **low-data** (graphiques allégés, tableaux uniquement)
- **PWA offline** (sauvegarde locale faits + évaluations)
- **Progressive loading** (KPIs critiques d'abord)
- Compressions agressives (WebP, SVG minifié)

### D.4 — Personnalisation dashboard

- Drag & drop de blocs
- Sauvegarder des vues nommées
- Partage entre utilisateurs d'un même tenant

### D.5 — Alertes (extension module 011)

Nouveaux types :
- Évaluation ESG à renouveler (annuelle)
- Deadline bailleur à X jours
- Certificat RSPO/Rainforest à renouveler
- Nouvelle version IFC PS → plan migration
- Faits expirés (mesure > 12 mois)

### D.6 — Formation par rôle

| Rôle entreprise | Contenu |
|---|---|
| Dirigeant | Intro ESG, enjeux, ROI bailleurs |
| HSE | Santé-sécurité, Code du Travail, PGES |
| Achats | Traçabilité, fournisseurs, EUDR |
| RH | Contrats, CNPS/IPRES, genre |
| Financier | Bailleurs, instruments, reporting |
| Communication | Narratif ESG, certifications |

Format : modules 5–10 min, quiz, contexte AO, génération IA (Claude) + review humaine pour socle.

### D.7 — Priorité

| Sous-item | Priorité |
|---|---|
| Registre blocs extensible | **P1** (prérequis architectural) |
| Personas / vues différenciées | **P1** (mobile-first AO) |
| Contextualisation mobile/offline | **P2** |
| Personnalisation drag&drop | **P2** |
| Formation par rôle | **P2** |

### Questions ouvertes D

- **QO-D1** — Formation IA vs experts : Claude pour socle, humain pour spécialisation filière.
- **QO-D2** — Attestation formation Mefali : certificat téléchargeable après quiz 100 %, sans valeur juridique initiale.
- **QO-D3** — Extension Chrome (module 8 roadmap initiale) intégrée au dashboard : oui, même registre de blocs côté popup.
- **QO-D4** — Hybridation consultant (Option 3) : évolution **post-MVP**, porte ouverte — cas d'usage légitimes (bailleurs exigent validation certifiée, PME novice veut 2e opinion, cabinets partenaires marketplace).

### Idées Cluster D

11 blocs, 5 personas MVP, 5 rappels, 6 rôles formation, 5 priorités, 4 questions ouvertes.

---

# SYNTHÈSE FINALE — Roadmap et décisions

## Vue d'ensemble des 5 clusters

```
                 ┌─────────────────────────────────────────────┐
                 │  CUBE DE QUALIFICATION BAILLEUR (central)   │
                 │  Projet × Entreprise × Référentiel          │
                 └────────────────────┬────────────────────────┘
                                      │
       ┌──────────────┬───────────────┼───────────────┐
       │              │               │               │
   [A: PROJET]   [A': ENTREPRISE] [B: ESG]      [C: LIVRABLES]
   data model    jumeau           multi-        dépend A×A'×B
   racine P0     symétrique P1    contextuel    P1
                                  P0

                           [D: UX/Dashboard/Formation]
                           P1 (registre blocs) + P2 (reste)
                           parallèle, indépendant
```

## Roadmap séquencée

### Phase 0 — Dettes P1 transverses (prérequis)

1. Migration catalogues hard-codés → BDD + interface admin (signal 1)
2. Framework injection instructions unifié (signal 3)
3. Enforcement applicatif contexte actif — `active_project` + `active_module` + guards pré-tool (signal 2)
4. Registre blocs visuels extensible (signal 4)
5. Snapshot propre systématique (signal 5)
6. RAG transversal — extension aux 8 modules (signal 6)

### Phase 1 — P0 parallèle

- **A** — Modèle `Project`, `ProjectMembership`, `FundApplication`, `CompanyProjection`, `ProjectSnapshot`
- **B** — Architecture 3 couches (Faits → Critères → Verdicts), catalogue initial (IFC PS + EUDR)

### Phase 2 — P1

- **A'** — `AdminMaturityLevel`, `FormalizationPlan`, `BeneficiaryProfile`, `AdminMaturityRequirement`
- **C** — Premier lot templates : `GCF_funding_proposal`, `IFC_AIMM_report`, `EUDR_dds`, `EIES_bailleur_catB`

### Phase 3 — P1/P2

- **D** — Personas différenciées, nouveaux blocs visuels, dashboard enrichi
- **B** extension — certifs sectorielles (RSPO, Rainforest), ISO 14001, packs régionaux AO

### Phase 4 — P2

- **B** extension — GRI, TCFD, CDP, impact (AIMM, IRIS+), régional (RSE SN/CI)
- **D** extension — mobile/offline, drag&drop, formation par rôle, extension Chrome

### Phase 5 — Post-MVP optionnel

- Hybridation consultant (Option 3 — marketplace)
- Signatures eIDAS
- File Celery (génération longue)

## Priorité globale consolidée

| Cluster | Priorité | Justification |
|---|---|---|
| A — Projet | **P0** | Racine data, tout en dépend |
| B — ESG multi-contextuel | **P0** | Pilier scoring, parallèle à A |
| A' — Entreprise | **P1** | Bloquant 90 % PME AO mais pas racine |
| C — Livrables | **P1** | Dépend A+B |
| D (registre blocs) | **P1** | Prérequis architectural |
| D (reste) | **P2** | Non bloquant, parallèle |

## Dettes P1 transversales (signaux d'audit)

| Dette | Signal | Clusters bénéficiaires |
|---|---|---|
| Data-driven vs hard-coded | 1 | A, A', B, C |
| Framework injection instructions | 3 | A, B, D |
| Enforcement applicatif | 2 | A, B |
| Registre blocs extensibles | 4 | D, C |
| Snapshot propre | 5 | A, A', B, C |
| RAG transversal | 6 | B, C |

## Personas MVP consolidés

1. Entrepreneur mono-projet (rétro-compatible)
2. Entrepreneur multi-projets (sélecteur projet)
3. Porteur de consortium (coopérative, GIE, cluster)
4. Dirigeant / executive (vue synthétique)
5. Équipes fonctionnelles (HSE, RH, achats, financier, communication)
6. Admin Mefali (maintenance catalogues)

**Post-MVP :** Consultant multi-PME (Option 3 hybride, marketplace).

## Questions ouvertes transversales (à trancher PRD)

- **QT-1** — Multi-langue effective (FR principal, EN secondaire, langues locales onboarding ?)
- **QT-2** — Politique de rétention (IFC AIMM exige 5–10 ans)
- **QT-3** — Interopérabilité API (Mefali s'expose-t-il aux bailleurs ?)
- **QT-4** — Modèle économique (gratuit/freemium/payant)
- **QT-5** — Gouvernance du catalogue (process d'ajout référentiel, validation qualité)

## Statistiques finales

| Métrique | Valeur |
|---|---|
| Clusters | 5 (A, A', B, C, D) |
| Items initiaux consolidés | 16 → 5 clusters + 1 dissous (étude d'impact → B+C) |
| Décisions architecturales majeures | 20+ |
| Entités data nouvelles | ~25 |
| Dettes P1 bloquantes | 6 |
| Personas MVP | 6 (dont 3 nouveaux) |
| Questions ouvertes | ~30 (5 transversales + 25 par cluster) |
| Techniques facilitation | Morphological Analysis, Assumption Reversal, Attribute Listing, Five Whys, SCAMPER, propositions cadrées |
| Idées générées (estimation) | ~120 |

## Recommandation — suite

**Prochaine étape :** `/bmad-create-prd` en référençant ce document.

Structure PRD suggérée — **5 épics miroirs des clusters** + 1 épic transverse :

- **Épic 0** — Dettes P1 transverses (Phase 0 de la roadmap)
- **Épic A (P0)** — Modèle projet
- **Épic B (P0)** — ESG multi-contextuel (architecture 3 couches)
- **Épic A' (P1)** — Maturité entreprise
- **Épic C (P1)** — Moteur de livrables multi-destinataires
- **Épic D (P1/P2)** — UX, Dashboard, Formation






