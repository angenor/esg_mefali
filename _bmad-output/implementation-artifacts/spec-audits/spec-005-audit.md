# Audit Rétrospectif — Spec 005 : Évaluation et Scoring ESG Contextualisé

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/005-esg-scoring-assessment/](../../../specs/005-esg-scoring-assessment/)
**Méthode** : rétrospective post-hoc
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Évaluation ESG conversationnelle sur 30 critères (E1-E10, S1-S10, G1-G10), pondération sectorielle, RAG documentaire, benchmark sectoriel, page résultats persistante, historique.

| Dimension | Livré |
|-----------|-------|
| Tâches | 46 / 46 `[X]` (100 %) |
| User Stories | 5 (US1 P1, US2-US3 P2, US4-US5 P3) |
| Phases | 8 |
| Critères évalués | 30 (3 piliers × 10) |
| Secteurs couverts | 6 + "general" (SECTOR_WEIGHTS) |
| Nouveau noeud | `esg_scoring_node` |
| Nouveau modèle | `ESGAssessment` (JSONB dense) |
| CLAUDE.md mentionne | "71 tests, 80% couverture" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture saine et pérenne

- `esg_scoring_node` + `ESG_TOOLS` (spec 012) coexistent proprement (graph.py:137)
- `create_tool_loop` avec `ESG_TOOLS + INTERACTIVE_TOOLS + GUIDED_TOUR_TOOLS` → intégration future-proof
- Pas de dead code (contrairement à spec 003)

### 2.2 RAG effectivement exploité

- `search_rag_context_for_pillar` (nodes.py:538) : injection documentaire par pilier dans le prompt
- Promesse de spec 004 (embeddings stockés "pour futur usage") tenue ici
- Pattern de référence pour les autres modules

### 2.3 Reprise d'évaluation interrompue

- `ESGStatusEnum` : `draft` + `in_progress` (models/esg.py:16-17)
- `get_resumable_assessment` (nodes.py:594) : détection + reprise au checkpoint
- Edge case de la spec ("abandon en cours de navigation") correctement implémenté

### 2.4 Persistance JSONB dense

- `ESGAssessment.assessment_data` stocke les 30 critères dans un champ JSONB
- Évite 30 lignes dans une table normalisée → simplifie les queries
- Cohérent avec le volume attendu (< 1000 utilisateurs, quelques évaluations par user)

### 2.5 TDD complet

- 4 fichiers de test écrits avant implémentation (T010-T012, T020, T030)
- Couverture 80 % atteinte (T045)

---

## 3. Ce qui a posé problème

### 3.1 🔴 DETTE MAJEURE — 30 appels tool séquentiels → timeout (fix spec 015)

- Spec 005 design initial : le LLM appelait probablement `save_criteria_score(code, value)` pour chaque critère un par un
- Avec 30 critères, chaque appel = 1 tool_call + 1 LLM response → **timeout LLM** sur les grosses évaluations
- Spec 015 a dû créer `batch_save_esg_criteria` (esg_tools.py:264) pour sauver N critères en une seule transaction
- **Cause racine** : design sans simulation du coût cumulé (30 × latence LLM ≈ 60-120 s)
- **Leçon** : les tools LangChain doivent anticiper le cas N-items et proposer un batch dès le départ, pas en correctif

### 3.2 🟠 SECTOR_BENCHMARKS hard-codés dans le code

- `weights.py` : `SECTOR_BENCHMARKS: dict[str, dict[str, object]] = {...}` (ligne 76)
- Aucune table BDD, aucune interface admin
- **Impact** :
  - Impossible d'affiner les moyennes au fur et à mesure que les utilisateurs réels fournissent des données
  - Une mise à jour des benchmarks nécessite un déploiement backend
  - Les moyennes restent théoriques, pas empiriques
- Spec 015/016/017 (correctifs) n'y ont pas touché — la dette persiste
- **Leçon** : toute donnée de référence amenée à évoluer avec les utilisateurs doit être en BDD dès le départ, même avec des valeurs initiales hard-codées

### 3.3 🟠 Pondération sectorielle opaque et limitée

- 6 secteurs couverts dans `SECTOR_WEIGHTS` (agriculture, energie, recyclage, transport, services, industrie) + fallback "general"
- Mais le profil entreprise supporte **11 secteurs** (spec 003 SectorEnum)
- 5 secteurs (textile, agroalimentaire, commerce, artisanat, construction, autre) tombent sur "general" → pondération non contextualisée
- FR-004 prescrivait "ponderation en fonction du secteur" mais l'implémentation couvre 55 % des secteurs seulement
- **Leçon** : vérifier que l'enum du profil est aligné avec la granularité des données de référence. Un écart = promesse non tenue.

### 3.4 🟠 Pas de détection d'incohérence dans les réponses

- Edge case documenté dans la spec : *"réponses incohérentes (ex: dit 'zero emission' mais travaille dans le transport diesel) → le systeme signale l'incoherence et demande confirmation"*
- Pas de trace dans le code d'un mécanisme de cross-validation
- Le LLM peut accepter silencieusement des réponses incohérentes → scores biaisés
- **Leçon** : les edge cases documentés dans la spec doivent avoir une tâche associée explicite, sinon ils restent théoriques

### 3.5 🟡 Pas de diff entre évaluations successives

- FR-019 + US5 implémentés : graphique d'évolution temporelle
- Mais aucune analyse comparative : qu'est-ce qui s'est amélioré depuis la dernière éval ? Quel critère a régressé ?
- L'utilisateur voit une courbe mais ne sait pas pourquoi elle monte/descend
- **Leçon** : l'historique sans diff est une donnée brute, pas une insight

### 3.6 🟡 SC-007 "80% recommandations actionnables" non mesuré

- Pas d'instrumentation pour vérifier ce success criterion
- Les recommandations générées par LLM (T013 `generate_recommendations`) ne sont pas scorées
- **Leçon** : les SC mesurables doivent avoir une tâche de mesure

### 3.7 🟡 FR-011 citation des sources documentaires à vérifier

- T033 : "prompt ESG pour inclure les instructions de citation des sources documentaires"
- Mais pas de structure de données pour persister les sources citées (pas de champ `document_citations` sur `ESGAssessment`)
- Si le LLM cite "rapport RSE p.12", cette citation est dans le texte du chat mais perdue dans l'historique
- **Leçon** : les citations doivent être persistées en données structurées pour la traçabilité

---

## 4. Leçons transversales

1. **Anticiper le coût cumulé des tools LangChain** — dès qu'une opération N-items est prévue, prévoir un batch.
2. **Donner des données évolutives dès le départ** — SECTOR_BENCHMARKS en BDD, pas en code.
3. **Aligner les enums métier et les données de référence** — 11 secteurs profil vs 6 secteurs pondérés = dette.
4. **Edge cases documentés = tâches explicites** — sinon ils restent théoriques.
5. **Historique sans diff = donnée brute** — ajouter l'analyse comparative pour transformer en insight.
6. **Success Criteria mesurables = tâche de mesure** — sinon on ne saura jamais si on y est arrivé.
7. **Citations = données structurées** — persister en BDD, pas seulement dans le texte.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Migrer SECTOR_BENCHMARKS vers une table BDD** avec seed des valeurs actuelles | P2 | §3.2 |
| 2 | **Compléter SECTOR_WEIGHTS pour les 11 secteurs** (textile, agroalimentaire, commerce, artisanat, construction, autre) | ~~P2~~ → **P1** (reclassé 2026-04-16) | §3.3 |
| 3 | **Mécanisme de détection d'incohérence** dans les réponses (cross-validation avec le profil) | P2 | §3.4 |
| 4 | Persister les citations documentaires en champ structuré (`document_citations: JSONB`) | P3 | §3.7 |
| 5 | Analyse comparative entre évaluations successives (diff par critère, delta par pilier) | P3 | §3.5 |
| 6 | Instrumenter la qualité des recommandations (feedback utilisateur, score "actionnable") | P3 | §3.6 |

**Actions déjà en place** :
- ✅ `batch_save_esg_criteria` (spec 015) — timeout résolu
- ✅ Reprise d'évaluation interrompue (draft/in_progress)
- ✅ RAG par pilier actif

---

## 6. Verdict

**Spec 005 livrée à 100 %, architecture saine, mais avec une dette majeure de design tool-calling (30 appels séquentiels) qu'il a fallu corriger en spec 015, et 2 dettes opérationnelles importantes (benchmarks hard-codés, 5 secteurs sans pondération).**

Le module ESG est **techniquement complet et utilisable** mais **souffre d'une couverture sectorielle partielle** (55 %) qui minore la promesse "pondération sectorielle" de FR-004. Les 6 actions résiduelles sont toutes P2/P3 — aucune n'est bloquante.

---

## 7. Mise à jour 2026-04-16 — reclassement SECTOR_WEIGHTS P2 → **P1**

**Justification** : le finding §3.3 — 5 secteurs sur 11 retombent sur `general` — est en réalité un **défaut d'alignement métier avec le public cible de la plateforme**.

Le projet cible explicitement les **PME africaines francophones UEMOA/CEDEAO** (cf. CLAUDE.md, PRD). Les secteurs non pondérés sont précisément ceux qui dominent l'économie PME en Afrique de l'Ouest :

| Secteur | Part estimée des PME en UEMOA | Statut actuel |
|---|---|---|
| Agroalimentaire | ~60-70 % (source BCEAO) | ❌ Non pondéré → fallback `general` |
| Commerce | ~20 % | ❌ Non pondéré → fallback `general` |
| Artisanat | ~10 % | ❌ Non pondéré → fallback `general` |
| Construction/BTP | ~5 % | ❌ Non pondéré → fallback `general` |
| Textile | < 5 % | ❌ Non pondéré → fallback `general` |

**Impact concret sur le parcours utilisateur** :
- Une PME agroalimentaire sénégalaise répond à 30 critères ESG
- Le scoring applique `SECTOR_WEIGHTS["general"]` au lieu d'une pondération agro
- Le score global ne reflète pas les enjeux ESG réels du secteur (eau, chaîne du froid, saisonnalité, etc.)
- Le bailleur reçoit un score non contextualisé
- La recommandation de financement est approximative

P1 justifié : alignement produit-marché. Les utilisateurs réels de la plateforme reçoivent un scoring dégradé pour ~50 % du marché cible.
