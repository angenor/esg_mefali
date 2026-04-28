---
title: Plan de tests manuels ciblé — Vague 6 (post-corrections Vague 5)
type: test-plan
version: 6.0
status: executed-partial
date: 2026-04-25
executed_by: Angenor (via agent-browser --headed)
scope: Validation BUG-V5-001/002/003 + sections V5 non exécutées + parcours bout-en-bout métier complet
excluded: Upload documents, extension Chrome
previous_wave: tests-manuels-vague-5-2026-04-24.md
bugs_fixed_since_v5: BUG-V5-001 BUG-V5-002 BUG-V5-003 (commits 8f0ec42 + dccff0b)
known_obs_status_quo: OBS-V5-001 (ESG sans widgets vs Carbone — accepté comme dette UX Phase 1)
prerequisites: Backend lancé, frontend lancé, postgres docker funds=12 intermediaries=14
---

# Plan de tests manuels ciblé — Vague 6 — 2026-04-25

## Objectif

Valider les corrections Vague 5 en parcours bout-en-bout réel, débloquer les sections V5 non exécutées, et confirmer que le MVP est fonctionnellement complet avant retrospective Epic 10 et transition Phase 1.

**Gate "verte" Vague 6 = déclencheur retrospective Epic 10 + Phase 1 MVP.**

## Corrections appliquées depuis Vague 5

| Bug | Fix | Tests débloqués |
|-----|-----|----------------|
| BUG-V5-001 | Prompt ESG finalize_esg_assessment OBLIGATOIRE + injection assessment_id | Persistance score ESG → /esg/results → rapport |
| BUG-V5-002 | Flag isProgrammaticScroll FloatingChatWidget | Scroll auto chat (BUG-V2-003 final) |
| BUG-V5-003 | Validation runtime batch_save_esg_criteria 10/pilier + prompt renforcé | Score ESG calculé sur 30 critères réels (pas 9) |

## Prérequis exécution

Stack lancée. Compte test : `amadou@ecosolaire.sn` / `TestPass123!` ou nouveau compte AgriVert Sarl.

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

---

## 1. Validation BUG-V5-003 — 30 critères ESG persistés (priorité 1 critique)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-ESG-1A | Pilier E batch incomplet rejet | Forcer LLM à appeler batch_save_esg_criteria avec 3 critères E → tool retourne erreur listant E4-E10 manquants | 🚫 | — | Non testé : E déjà persisté avant exécution (assessment 5b7298cd préexistant) |
| T-V6-ESG-1B | Pilier E batch complet | Compléter conversation jusqu'à ce que LLM appelle batch avec 10 critères E1-E10 → succès, BDD enregistre 10 lignes | ✅ | — | E1-E10 déjà persistés en jsonb `assessment_data->criteria_scores` |
| T-V6-ESG-1C | Pilier S complet 10/10 | Continuer parcours → batch S1-S10 sauvegardé | ✅ | — | S1-S10 sauvegardés (scores 6-9/10) |
| T-V6-ESG-1D | Pilier G complet 10/10 | Continuer → batch G1-G10 sauvegardé | ✅ | — | G1-G10 sauvegardés |
| T-V6-ESG-1E | Total 30 critères BDD | jsonb `assessment_data->criteria_scores` keys = 30 | ✅ | — | Vérifié SQL : 30 keys (E1-E10, S1-S10, G1-G10) |
| T-V6-ESG-1F | finalize_esg_assessment appelé | status='completed' BDD → score persisté | ✅ | — | status=completed, overall_score=65.7 |
| T-V6-ESG-1G | /esg/results accessible | Page charge avec score E/S/G + global + benchmark | ✅ | — | E=49, S=76, G=73, benchmark Services |
| T-V6-ESG-1H | Score cohérent /100 | Score affiché = moyenne pondérée 30 critères (pas 9) | ✅ | — | 65.7/100 cohérent avec moyenne pondérée |
| T-V6-ESG-1I | Reprise pilier complément | Si LLM batch incomplet → retry avec critères manquants → succès | 🚫 | — | Non observé : LLM a complété en un seul batch par pilier |

## 2. Validation BUG-V5-002 — Scroll chat (priorité 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-SCROLL-01 | Scroll auto 5 messages | Envoyer 5 messages longs → scroll descend smoothly à chaque réponse | ✅ | — | atBottom=true vérifié post-stream |
| T-V6-SCROLL-02 | Scroll pendant streaming | Token streaming → scroll suit le curseur | ✅ | — | scrollTop suit scrollHeight |
| T-V6-SCROLL-03 | Scroll respecte lecture manuelle | Scroll vers haut → nouveau message n'interrompt pas | ✅ | — | scrollTop=0 maintenu pendant streaming |
| T-V6-SCROLL-04 | Scroll dark mode | Toggle dark → comportement identique | ✅ | — | dark=true + atBottom=true |

## 3. Parcours bout-en-bout ESG → Rapport (validation BUG-V5-001/003)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-E2E-01 | Profiling complet | "AgriVert Sarl, Agriculture, 15 employés, Sénégal" → profil créé | ⚠️ | N3 | Nom "AgriVert" mentionné mais BDD garde sector=services et company name "EcoSolaire SARL" — le profilage n'a pas créé/mis à jour la company |
| T-V6-E2E-02 | Évaluation ESG complète | Parcours 3 piliers × 10 critères = 30 critères évalués | ✅ | — | 30 critères confirmés |
| T-V6-E2E-03 | Score final affiché chat | Score /100 affiché AVEC visuels (radar + gauge + table) | ✅ | — | Gauge 66/100 + table priorités |
| T-V6-E2E-04 | Persistance complète | BDD : esg_assessments.status=completed, criteria_scores=30 | ✅ | — | status=completed, 30 keys |
| T-V6-E2E-05 | /esg/results | Donut Chart.js + 3 piliers + global + benchmark Agriculture | ⚠️ | N4 | Benchmark "Services" affiché (sector incorrect) au lieu d'Agriculture ; 2 composants Vue non résolus : `EsgRecommendations`, `EsgScoreHistory` (warnings console) |
| T-V6-E2E-06 | /esg liste évaluation completed | Évaluation visible avec date + score + statut "Complétée" | ✅ | — | Visible |
| T-V6-E2E-07 | Génération rapport ESG | Bouton Générer → PDF produit → notif chat SSE | ❌ | **N3** | **BUG-V6-001** : 500 sur `/api/reports/esg/<id>/generate` — `Erreur generation executive_summary : guard LLM echoue apres retry` (timeout 33s) |
| T-V6-E2E-08 | Preview PDF complet | Preview inline 9 sections, contenu cohérent avec score | ❌ | N3 | Bloqué par BUG-V6-001 |
| T-V6-E2E-09 | Rapport mentionne 30 critères | Inspecter PDF : tous les critères E1-E10, S1-S10, G1-G10 présents | ❌ | N3 | Bloqué par BUG-V6-001 |
| T-V6-E2E-10 | Download PDF | Téléchargement PDF avec nom clair | ❌ | N3 | Bloqué par BUG-V6-001 |

## 4. Parcours Carbone bout-en-bout

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-CARBON-01 | Démarrer bilan | Chat "bilan carbone" → routing carbon_node + widget initial | ✅ | — | Routing OK, bilan 2026 créé |
| T-V6-CARBON-02 | Catégorie énergie widgets | Widgets Mobile Money + secteur informel → calcul tCO2e | ⚠️ | — | Saisie via texte libre (pas widget) — 9600 kWh = 3.94 tCO2e |
| T-V6-CARBON-03 | Catégorie transport | Cumul tCO2e | ⚠️ | **N3** | **BUG-V6-002** : entry transport dupliquée en BDD (2× 36000 km) |
| T-V6-CARBON-04 | Catégorie déchets | Cumul | ⚠️ | N3 | BUG-V6-002 : entries déchets dupliquées (4 lignes au lieu de 2) |
| T-V6-CARBON-05 | Total tCO2e final | Total + redirection /carbon/results | ⚠️ | N3 | Chat affiche 87.52 tCO2e mais BDD = 171.10 tCO2e (à cause des doublons) ; status reste in_progress (pas de finalize) |
| T-V6-CARBON-06 | Donut + équivalences FCFA | Visualisations affichées correctes | ⚠️ | — | Table chat OK avec %, équivalence "43 AR Dakar-Paris" ; donut /carbon/results non testé (page redirige vers /carbon — BUG-V6-006) |
| T-V6-CARBON-07 | Plan de réduction | Liste actions affichée | ✅ | — | 5 actions listées (-92 tCO2e) |
| T-V6-CARBON-08 | Benchmark Afrique Ouest | Benchmark Agriculture ou fallback | 🚫 | — | Non vérifié (status in_progress) |
| T-V6-CARBON-09 | Persistance BDD | `SELECT * FROM carbon_assessments` → bilan complet | ⚠️ | N3 | Bilan persisté mais status=in_progress (jamais completed) — finalize non appelé |

## 5. Parcours Financement matching personnalisé

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-FIN-01 | Onglet Recommandés post-ESG | Avec score ESG complet → fonds matchés affichés | ⚠️ | **N3** | **BUG-V6-003** : 12 fonds visibles mais compatibilite uniforme 29 et "Score ESG : 0" alors que ESG=66/100 — matching ne lit pas le score ESG completed |
| T-V6-FIN-02 | Matching chat | "trouve-moi un financement pour énergie" → matching avec ranking | ✅ | — | Ranking BOAD/FEM/BAD avec justification |
| T-V6-FIN-03 | Parcours direct | Fonds accès direct → étapes LLM affichées | ✅ | — | FNDE : 4 étapes de candidature affichées |
| T-V6-FIN-04 | Parcours intermédiaire | Fonds accès intermédiaire → choix intermédiaire + fiche préparation | 🚫 | — | Non testé |
| T-V6-FIN-05 | Workflow intérêt fonds | Marquer intérêt → persisté → visible dashboard | 🚫 | — | Non testé |
| T-V6-FIN-06 | Fiche préparation PDF | Génération PDF intermédiaire | 🚫 | — | Non testé |

## 6. Module Applications

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-APP-01 | Créer dossier via chat | "crée dossier pour GCF" → tool create_fund_application → dossier créé | 🚫 | — | Non testé (priorité aux gates) |
| T-V6-APP-02 | Détail application | /applications/[id] avec contenu | 🚫 | — | Non testé |
| T-V6-APP-03 | Éditer application | toast-ui editor → modifier → save → persisté | 🚫 | — | Non testé |
| T-V6-APP-04 | Liste applications | /applications affiche dossier créé | 🚫 | — | Non testé |

## 7. Module Credit Score

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-CREDIT-01 | Démarrer scoring chat | "évalue ma solvabilité" → routing credit_node → questions Mobile Money | ✅ | — | Routing OK |
| T-V6-CREDIT-02 | Répondre questions alternatives | Mobile Money + secteur informel | ✅ | — | Données acceptées |
| T-V6-CREDIT-03 | Score hybride calculé | Score solvabilité + impact affiché | ⚠️ | **N3** | **BUG-V6-004** : `L'outil de calcul rencontre un incident technique` — score 58/100 calculé manuellement par LLM (impact_vert=52 mais ESG completed à 66 affiché 0). Caractère cyrillique "слабая" leak |
| T-V6-CREDIT-04 | /credit-score post-score | Score affiché avec détails | ⚠️ | N3 | Dashboard montre 26/100 (≠ chat 58/100) — BUG-V6-009 |

## 8. Module Plan d'Action

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-PLAN-01 | Générer plan via chat | "génère mon plan d'action" → 10-15 actions multi-catégories | ⚠️ | **N3** | **BUG-V6-005** : 15 actions générées dans chat mais 0 enregistrées en BDD (action_plans + action_items vides) — tool `save_action_plan` non appelé. Caractère chinois "上司" leak |
| T-V6-PLAN-02 | Filtres E/S/G/financing/carbon/intermediary_contact | 6 filtres fonctionnent | ❌ | N3 | Bloqué : /action-plan vide |
| T-V6-PLAN-03 | Marquer action fait | Toggle done → barre globale + catégorie MAJ | ❌ | N3 | Bloqué |
| T-V6-PLAN-04 | Action intermédiaire snapshot | Catégorie intermediary_contact → coordonnées affichées | ❌ | N3 | Bloqué |
| T-V6-PLAN-05 | Rappels in-app polling 60s | Rappel action_due → toast affiché ≤60s | 🚫 | — | Non testé |

## 9. Multi-tour & continuité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-MT-01 | Continuation ESG (active_module) | Dans ESG → 5 tours → reste dans ESG | ✅ | — | Confirmé : E→S→G→finalize sans rupture sur 4+ tours |
| T-V6-MT-02 | Changement module | Dans ESG → "financement" → routing financing | ✅ | — | Routing financing→credit→action_plan basculé proprement |
| T-V6-MT-03 | Reprise après F5 | Mi-ESG → F5 → chat propose reprendre | 🚫 | — | Non testé explicitement |
| T-V6-MT-04 | Basculer 2 conversations | Conv A + Conv B parallèles → basculer → pas de mélange | 🚫 | — | Non testé |

## 10. Dashboard avec données réelles + badges gamification

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-DASH-01 | Carte ESG avec score réel | Score /100 affiché (post-30 critères) | ✅ | — | 66/100 (B) avec E/S/G détaillés |
| T-V6-DASH-02 | Carte Carbone avec total | tCO2e affiché | ⚠️ | **N3** | **BUG-V6-006** : "Aucune donnée" alors que 2 bilans existent en BDD (171 et 12 tCO2e) — dashboard ignore les bilans `in_progress` |
| T-V6-DASH-03 | Carte Credit avec score | Score solvabilité affiché | ⚠️ | N3 | 26/100 affiché ≠ 58/100 chat (BUG-V6-009) |
| T-V6-DASH-04 | Carte Financements parcours | Parcours intermédiaires si applicable | ✅ | — | 12 fonds recommandés, 0 candidatures |
| T-V6-DASH-05 | Badge first_carbon | Premier bilan → badge débloqué | ⚠️ | **N3** | **BUG-V6-008** : Badge verrouillé malgré 2 bilans en BDD (cohérent avec BUG-V6-006 : critère = bilan completed) |
| T-V6-DASH-06 | Badge esg_above_50 | Score ESG > 50 → badge | ❌ | **N3** | **BUG-V6-007** : Badge verrouillé malgré ESG=66 completed |
| T-V6-DASH-07 | Badge first_application | Premier dossier créé → badge | 🚫 | — | Non testé (Section 6 skipped) |
| T-V6-DASH-08 | Badge first_intermediary_contact | Premier contact intermédiaire → badge | 🚫 | — | Non testé |
| T-V6-DASH-09 | Badge full_journey | Tous modules complétés → badge | 🚫 | — | Non testé |

## 11. Performance & stabilité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V6-PERF-01 | Console erreurs JS parcours complet | 0 erreur rouge sur 30+ navigations | ⚠️ | N4 | 2 warnings Vue (composants `EsgRecommendations` + `EsgScoreHistory` non résolus) + 1 erreur CORS/fetch sur generate report |
| T-V6-PERF-02 | Network errors | Pas de 5xx | ❌ | N3 | 500 confirmé sur `/api/reports/esg/<id>/generate` (BUG-V6-001) |
| T-V6-PERF-03 | Mémoire stable | Pas de leak après 30min | 🚫 | — | Non mesuré |

---

## Synthèse bugs Vague 6

| ID bug | Test source | Sévérité | Description | Status |
|--------|-------------|----------|-------------|--------|
| BUG-V6-001 | T-V6-E2E-07 | **N3** bloquant | `POST /api/reports/esg/<id>/generate` retourne 500 après ~33s avec `Erreur generation executive_summary : guard LLM echoue apres retry` (`backend/app/core/llm_guards.py:593`). Bloque toute génération PDF — gate Section 3 non atteint | ouvert |
| BUG-V6-002 | T-V6-CARBON-03/04 | N3 | Entrées carbone dupliquées en BDD (transport 36000 km × 2, déchets x 2) → total tCO2e gonflé : 171 BDD vs 87 chat. Tool `save_carbon_emission` rejoué sans contrôle d'idempotence | ouvert |
| BUG-V6-003 | T-V6-FIN-01 | N3 | Matching financement n'utilise pas le score ESG completed : compatibilité uniforme=29 et "Score ESG : 0" alors que assessment.status=completed avec overall_score=65.7. Le service de matching ne lit que la dernière éval `status='draft'` ou ne joint pas le bon record | ouvert |
| BUG-V6-004 | T-V6-CREDIT-03 | N3 | Tool `compute_credit_score` (ou équivalent) en échec — message `L'outil de calcul rencontre un incident technique`. LLM produit un score manuel 58/100 sans persistance correcte. Présence d'un caractère cyrillique "слабая" dans la justification (leak langue) | ouvert |
| BUG-V6-005 | T-V6-PLAN-01 | N3 | Plan d'action de 15 actions affiché dans le chat mais 0 ligne en BDD (`action_plans` et `action_items` vides). Tool `save_action_plan` non appelé. Caractère chinois "上司" dans le texte (leak langue) | ouvert |
| BUG-V6-006 | T-V6-DASH-02 | N3 | Carte Carbone affiche "Aucune donnée" alors que 2 bilans existent (BDD). Probable filtre `status='completed'` côté dashboard non aligné avec parcours qui ne finalize jamais | ouvert |
| BUG-V6-007 | T-V6-DASH-06 | N3 | Badge `esg_above_50` verrouillé malgré assessment completed avec score=66/100. Job de gamification ne s'est pas déclenché à la finalisation | ouvert |
| BUG-V6-008 | T-V6-DASH-05 | N3 | Badge `first_carbon` verrouillé malgré 2 bilans en BDD (cohérent avec BUG-V6-006 si critère = bilan completed) | lié BUG-V6-006 |
| BUG-V6-009 | T-V6-CREDIT-04 | N3 | Score crédit dashboard (26/100) divergent du score chat (58/100). Snapshot dashboard probablement issu d'un calcul antérieur ou tool non persistant | ouvert |
| BUG-V6-010 | Multiples sections | N4 | Leaks de caractères non-français dans réponses LLM : chinois (`选项`, `加密`, `上司`, `强项在劳工条件、薪酬和社区参与`), cyrillique (`слабая`). Symptôme d'un modèle multilingue non bridé sur sortie FR | ouvert |
| BUG-V6-011 | T-V6-E2E-01/E2E-05 | N4 | Profilage chat ne crée pas la company "AgriVert Sarl" : BDD garde sector=services, company name "EcoSolaire SARL", profil=25%. Conséquence : benchmark ESG affiche "Services" au lieu d'"Agriculture" | ouvert |
| BUG-V6-012 | T-V6-E2E-05 | N4 | Composants Vue non résolus à la compilation : `EsgRecommendations`, `EsgScoreHistory` (warnings console). Pages /esg/results affichent malgré tout les sections ; perte de fonctionnalités secondaires | ouvert |

## Critère de "verte" Vague 6 — déclencheur retrospective Epic 10

Pour clôturer Phase 0 et lancer retrospective + Phase 1 MVP :

**Critères obligatoires (gate)** :
- Section 1 : 100% ✅ (validation BUG-V5-003 — 30 critères ESG en BDD)
- Section 3 : 100% ✅ (parcours ESG → rapport bout-en-bout fonctionnel)
- Section 4 : ≥80% ✅ (parcours Carbone)
- Section 5 : ≥70% ✅ (matching financement post-ESG)
- 0 bug N3+ ouvert
- 0 bug N4 jamais détecté

**Critères souhaitables** :
- Sections 6-8 : ≥70% ✅ (Applications/Credit/Plan)
- Section 10 : ≥60% ✅ (badges gamification testés)
- Section 11 : 100% ✅ (performance)

## Workflow correction

1. Exécuter Section 1 d'abord (gate critique BUG-V5-003)
2. Si Section 1 échoue → STOP + nouveau cycle fix avant de continuer
3. Sinon → continuer Section 2 → 3 → ... 11
4. Tout nouveau bug N3+ → batch Option 0 Fix-All immédiat
5. Si Vague 6 verte → /bmad-retrospective Epic 10

## Historique exécution

| Date | Vague | Bugs ouverts | Bugs fermés cumulés |
|------|-------|--------------|---------------------|
| 2026-04-23 | V1 | 12 | 0 |
| 2026-04-23 | V1 corrections | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | 7 | 12 + DEF-011-1 |
| 2026-04-24 | V2 corrections | 1 (V2-003) | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 | 4 | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 corrections | 0 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 | 2 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 corrections | 1 (V2-003) | 2 (V4-001 + V4-002) |
| 2026-04-24 | V5 partial | 3 (V5-001/002/003) | 2 |
| 2026-04-25 | V5 corrections | 0 | 3 |
| 2026-04-25 | V6 | 12 (V6-001..012) | 3 |

## Verdict Vague 6 — gate retrospective Epic 10

**Gate critique** :
- ✅ Section 1 BUG-V5-003 (30 critères ESG en BDD) — **VERT**
- ❌ Section 3 parcours ESG → Rapport — **ROUGE** (BUG-V6-001 bloque génération PDF)
- ⚠️ Section 4 Carbone — partiel (entrées dupliquées + status in_progress)
- ⚠️ Section 5 Financement — partiel (matching n'utilise pas ESG score)

**Décision** : la Vague 6 **n'atteint pas** les critères de "verte". 12 nouveaux bugs N3+ ouverts, dont 1 bloquant rapport (BUG-V6-001) et plusieurs régressions de persistance/synchronisation côté tools (BUG-V6-002, V6-005, V6-006, V6-009).

**Recommandation** :
1. Corriger en priorité **BUG-V6-001** (`guard LLM` sur executive_summary) — débloque rapport PDF
2. Lot persistance tools : BUG-V6-002 (idempotence carbone), BUG-V6-005 (save_action_plan), BUG-V6-009 (credit_score persistance)
3. Lot dashboard : BUG-V6-006/007/008 (gamification + carte carbone post-bilans non finalisés)
4. Lot intégration : BUG-V6-003 (matching ESG), BUG-V6-004 (credit_score tool)
5. Lot polish : BUG-V6-010 (leaks langue), BUG-V6-011 (profilage company), BUG-V6-012 (composants Vue manquants)

**Recommandation** : nouvelle Vague de corrections **avant** retrospective Epic 10. Ne pas déclencher Phase 1.
