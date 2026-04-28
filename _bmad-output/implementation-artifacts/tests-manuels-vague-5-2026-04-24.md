---
title: Plan de tests manuels ciblé — Vague 5 (post-corrections Vague 4)
type: test-plan
version: 5.0
status: partial-run-2026-04-24
date: 2026-04-24
executed_by: Angenor (via agent-browser --headed)
scope: Validation BUG-V4-001/002 + sections V4 non exécutées + parcours bout-en-bout complet
excluded: Upload documents, extension Chrome
previous_wave: tests-manuels-vague-4-2026-04-24.md
bugs_fixed_since_v4: BUG-V4-001 BUG-V4-002 (commit 5d7dc27)
bugs_still_open_to_verify: BUG-V2-003 (chat scroll auto)
prerequisites: Backend lancé sur 8000, frontend sur 3000, postgres docker funds=12 intermediaries=14
---

# Plan de tests manuels ciblé — Vague 5 — 2026-04-24

## Objectif

Valider les corrections Vague 4 (widget cycle + spinbutton saisie) puis exécuter les sections V4 non couvertes (scroll, modules dépendants, multi-tour, dashboard avec données) plus un parcours utilisateur bout-en-bout complet pour confirmer la stabilité globale avant retrospective Epic 10.

## Corrections appliquées depuis Vague 4

| Bug | Fix | Tests débloqués |
|-----|-----|----------------|
| BUG-V4-001 | Widget cycle reset state + prompt ESG enchaînement piliers | Tout parcours ESG complet, modules dépendants chaînés |
| BUG-V4-002 | ProfileField emit Number(editValue.value) | Profil édition spinbutton |

## Prérequis exécution

Stack lancée et postgres seedé. Compte test : `amadou@ecosolaire.sn` / `TestPass123!` (EcoSolaire SARL, Sénégal) ou nouveau compte AgriVert Sarl.

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

---

## 1. Validation BUG-V4-001 + BUG-V4-002 (priorité 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-W-01 | Cycle widget E → S | Soumettre widget pilier E → 2ème widget pilier Social apparaît automatiquement | ⚠️ | N2 | ESG utilise format texte/table, pas widgets ; enchaînement E → S OK via texte |
| T-V5-W-02 | Cycle widget S → G | Soumettre Social → 3ème widget Gouvernance apparaît | ⚠️ | N2 | Cycle S → G OK via texte ; pas de widgets dans ESG |
| T-V5-W-03 | Input débloqué après widget | Soumettre widget → input texte redevient actif (pas verrouillé) | ✅ | — | Input actif entre chaque pilier |
| T-V5-W-04 | Pas de double widget | Un seul widget pending à la fois (jamais 2) | 🚫 | — | Non applicable (ESG sans widgets actuellement) |
| T-V5-W-05 | Widget après "Répondre autrement" | Widget A → "Répondre autrement" → texte libre → widget B suivant apparaît | 🚫 | — | Non applicable (ESG sans widgets) |
| T-V5-PROFILE-01 | Spinbutton employés saisie 42 | ✎ → input 42 → ✓ → devtools : PATCH body `employee_count: 42` (pas l'ancienne valeur) | ✅ | — | 42 persisté après F5 ; PATCH OK |
| T-V5-PROFILE-02 | Spinbutton année 2018 | ✎ année → 2018 → ✓ → F5 → 2018 persisté | ✅ | — | 2018 persisté après F5 |
| T-V5-PROFILE-03 | Edit successif sans F5 | ✎ → 30 → ✓ → ✎ → 50 → ✓ → valeur finale 50 | ✅ | — | 30 → 50 OK sans rechargement |

## 2. Chat scroll auto — BUG-V2-003 reprise (priorité 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-SCROLL-01 | Scroll auto nouveau message | Envoyer 5 messages longs → scroll descend à chaque réponse | ❌ | N2 | **BUG-V5-002** : scrollTop=0 après réponse, scrollHeight=1243px (non scrolled) ; puis scrollTop=777 après 2e message avec scrollHeight=1656px (n'a pas suivi) |
| T-V5-SCROLL-02 | Scroll pendant streaming | Message long streamé → scroll suit le curseur token par token | ❌ | N2 | Même root cause BUG-V5-002 |
| T-V5-SCROLL-03 | Scroll respecte lecture manuelle | Scroll vers haut → nouveau message n'interrompt pas la lecture | 🚫 | — | Non testé (scroll ne fonctionne pas de base) |
| T-V5-SCROLL-04 | Scroll dark mode | Toggle dark → scroll comportement identique | ⚠️ | — | Textbox dark OK (bg rgb(31,41,55)) mais scroll bug identique |

## 3. Parcours ESG bout-en-bout (validation cycle complet)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-E2E-ESG-01 | Démarrer évaluation | Chat → "évalue mon ESG" → widget pilier E | ⚠️ | N2 | ESG démarre avec tableau texte (E1-E3), pas widget |
| T-V5-E2E-ESG-02 | Compléter pilier E (5 critères) | Soumissions widgets E → progress E 100% | ⚠️ | — | 3 critères seulement (E1, E2, E3), pas 5. Scores enregistrés OK |
| T-V5-E2E-ESG-03 | Compléter pilier S (5 critères) | Widgets S → progress S 100% | ⚠️ | — | 3 critères (S1-S3), passage auto depuis E OK |
| T-V5-E2E-ESG-04 | Compléter pilier G (5 critères) | Widgets G → progress G 100% | ⚠️ | — | 3 critères (G1-G3), passage auto depuis S OK |
| T-V5-E2E-ESG-05 | Score final /100 | Score affiché chat + redirection /esg/results | ❌ | N3 | **BUG-V5-001** : Score textuel affiché ("6/10 équilibrés") mais aucune redirection, aucune persistance BDD |
| T-V5-E2E-ESG-06 | Page résultats | Donut Chart.js + scores E/S/G + global | ❌ | — | /esg/results inaccessible (évaluation in_progress, pas completed) |
| T-V5-E2E-ESG-07 | Benchmark sectoriel | Benchmark Agriculture (ou fallback) | 🚫 | — | Bloqué par BUG-V5-001 |
| T-V5-E2E-ESG-08 | Historique évaluations | /esg liste l'évaluation complétée | ⚠️ | — | Évaluation listée mais restée "En cours", non complétée |
| T-V5-E2E-ESG-09 | Dark mode résultats | Charts + cards stylés dark | 🚫 | — | Bloqué par BUG-V5-001 |

## 4. Parcours Carbone bout-en-bout

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-E2E-C-01 | Démarrer bilan via chat | "bilan carbone" → routing carbon_node → "consommation" pas "consumo" | ✅ | — | Routing OK, widget interactif affiché, texte "consommation" présent |
| T-V5-E2E-C-02 | Catégorie énergie | Widgets énergie → calcul tCO2e progressif | ⬜ | — | |
| T-V5-E2E-C-03 | Catégorie transport | Cumul tCO2e | ⬜ | — | |
| T-V5-E2E-C-04 | Catégorie déchets | Cumul | ⬜ | — | |
| T-V5-E2E-C-05 | Catégorie industriel/agricole | Selon secteur Agriculture | ⬜ | — | |
| T-V5-E2E-C-06 | Total tCO2e final | Total + redirection /carbon/results | ⬜ | — | |
| T-V5-E2E-C-07 | Donut + équivalences FCFA | Visualisations affichées | ⬜ | — | |
| T-V5-E2E-C-08 | Plan de réduction | Liste actions affichée | ⬜ | — | |
| T-V5-E2E-C-09 | Benchmark Afrique Ouest | Benchmark Agriculture ou fallback | ⬜ | — | |
| T-V5-E2E-C-10 | Contrainte unicité année | Tenter bilan même année → blocage avec message | ⬜ | — | |

## 5. Module Applications

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-APP-01 | Créer dossier via chat | Chat "crée dossier pour GCF" → tool create_fund_application → dossier créé | ⬜ | — | |
| T-V5-APP-02 | Détail application | Cliquer dossier → /applications/[id] avec contenu | ⬜ | — | |
| T-V5-APP-03 | Éditer application | toast-ui editor → modifier → save → persisté | ⬜ | — | |
| T-V5-APP-04 | Liste applications | /applications affiche dossier créé | ⬜ | — | |
| T-V5-APP-05 | Dark mode application | Éditeur + cards dark | ⬜ | — | |

## 6. Module Credit

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-CREDIT-01 | Démarrer scoring chat | "évalue ma solvabilité" → routing credit_node → questions Mobile Money | ⬜ | — | |
| T-V5-CREDIT-02 | Répondre questions alternatives | Widgets Mobile Money + secteur informel | ⬜ | — | |
| T-V5-CREDIT-03 | Score hybride calculé | Score solvabilité + impact affiché | ⬜ | — | |
| T-V5-CREDIT-04 | Page /credit-score post-score | Score affiché avec détails | ⬜ | — | |
| T-V5-CREDIT-05 | Dark mode credit | Éléments dark | ⬜ | — | |

## 7. Module Plan d'Action

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-PLAN-01 | Générer plan via chat | "génère mon plan d'action" → 10-15 actions multi-catégories | ⬜ | — | |
| T-V5-PLAN-02 | Filtre environment | Actions E filtrées | ⬜ | — | |
| T-V5-PLAN-03 | Filtre social | Actions S filtrées | ⬜ | — | |
| T-V5-PLAN-04 | Filtre governance | Actions G filtrées | ⬜ | — | |
| T-V5-PLAN-05 | Filtre financing | Actions financing filtrées | ⬜ | — | |
| T-V5-PLAN-06 | Filtre carbon | Actions carbon filtrées | ⬜ | — | |
| T-V5-PLAN-07 | Filtre intermediary_contact | Actions intermediary filtrées + coordonnées snapshot | ⬜ | — | |
| T-V5-PLAN-08 | Marquer action fait | Toggle done → barre progression globale MAJ | ⬜ | — | |
| T-V5-PLAN-09 | Progression par catégorie | Marquer action E → barre E spécifique MAJ | ⬜ | — | |
| T-V5-PLAN-10 | Rappels in-app polling 60s | Rappel action_due → toast affiché ≤60s | ⬜ | — | |
| T-V5-PLAN-11 | Toast variant intermediaire | Rappel intermediary_followup → toast bleu | ⬜ | — | |
| T-V5-PLAN-12 | Dark mode plan | Timeline + cards + filtres dark | ⬜ | — | |

## 8. Module Reports & Génération PDF

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-REPORT-01 | Générer rapport ESG | Avec score ESG → bouton Générer → PDF en cours | ⬜ | — | |
| T-V5-REPORT-02 | Notification chat post-génération | Notification SSE chat "Rapport généré" | ⬜ | — | |
| T-V5-REPORT-03 | Preview PDF inline | Cliquer preview → PDF affiché 9 sections | ⬜ | — | |
| T-V5-REPORT-04 | Télécharger PDF | Cliquer download → PDF téléchargé nom clair | ⬜ | — | |
| T-V5-REPORT-05 | Graphiques matplotlib SVG | Inspecter PDF → graphiques inclus | ⬜ | — | |
| T-V5-REPORT-06 | Résumé exécutif IA Claude | Inspecter PDF → résumé présent | ⬜ | — | |
| T-V5-REPORT-07 | Références UEMOA/BCEAO/ODD | Références réglementaires présentes | ⬜ | — | |
| T-V5-REPORT-08 | Génération simultanée 2 rapports | Lancer 2 rapides → pas de crash | ⬜ | — | Edge case |
| T-V5-REPORT-09 | Dark mode reports | Liste + preview dark | ⬜ | — | |

## 9. Module Financement matching personnalisé

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-FIN-01 | Onglet Recommandés post-ESG | Avec score ESG → onglet Recommandés affiche fonds matchés | ⬜ | — | |
| T-V5-FIN-02 | Matching chat | "trouve-moi un financement pour énergie" → matching avec ranking | ⬜ | — | |
| T-V5-FIN-03 | Parcours direct | Fonds accès direct → étapes LLM affichées | ⬜ | — | |
| T-V5-FIN-04 | Parcours intermédiaire | Fonds accès intermédiaire → choix intermédiaire + fiche préparation | ⬜ | — | |
| T-V5-FIN-05 | Workflow intérêt fonds | Marquer intérêt → persisté → visible dashboard | ⬜ | — | |
| T-V5-FIN-06 | Fiche préparation PDF | Génération PDF intermédiaire | ⬜ | — | |

## 10. Multi-tour & continuité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-MT-01 | Continuation ESG (active_module) | Dans ESG → 5 tours → reste dans ESG | ⬜ | — | |
| T-V5-MT-02 | Changement module | Dans ESG → "financement" → routing financing | ⬜ | — | |
| T-V5-MT-03 | Reprise après F5 | Mi-ESG → F5 → chat propose reprendre où laissé | ⬜ | — | |
| T-V5-MT-04 | Basculer 2 conversations | Conv A + Conv B parallèles → basculer → pas de mélange | ⬜ | — | |
| T-V5-MT-05 | Nouvelle conversation reset | Bouton + Nouvelle conv → historique vidé | ⬜ | — | |

## 11. Dashboard avec données réelles

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-DASH-01 | Carte ESG avec score | Score réel affiché (post-ESG complet) | ⬜ | — | |
| T-V5-DASH-02 | Carte Carbone avec total | tCO2e réel affiché | ⬜ | — | |
| T-V5-DASH-03 | Carte Credit avec score | Score solvabilité affiché | ⬜ | — | |
| T-V5-DASH-04 | Carte Financements parcours | Parcours intermédiaires si applicable | ⬜ | — | |
| T-V5-DASH-05 | Badge first_carbon | Premier bilan → badge débloqué | ⬜ | — | |
| T-V5-DASH-06 | Badge esg_above_50 | Score ESG > 50 → badge | ⬜ | — | |
| T-V5-DASH-07 | Badge first_application | Premier dossier créé → badge | ⬜ | — | |
| T-V5-DASH-08 | Badge first_intermediary_contact | Premier contact intermédiaire → badge | ⬜ | — | |
| T-V5-DASH-09 | Badge full_journey | Tous modules complétés → badge | ⬜ | — | |

## 12. Performance & Stabilité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V5-PERF-01 | Console erreurs JS parcours complet | 0 erreur rouge sur 30+ navigations | ⬜ | — | |
| T-V5-PERF-02 | Console warnings | Pas de warning Vue/Nuxt non-justifié | ⬜ | — | |
| T-V5-PERF-03 | Network errors | Pas de 5xx, 4xx attendus uniquement | ⬜ | — | |
| T-V5-PERF-04 | Mémoire stable parcours long | Pas de leak après 30min usage | ⬜ | — | Optionnel |

---

## Synthèse bugs Vague 5

| ID bug | Test source | Sévérité | Description | Status |
|--------|-------------|----------|-------------|--------|
| BUG-V5-001 | T-V5-E2E-ESG-05 | N3 | ESG : score textuel annoncé ("6/10 équilibrés") mais évaluation reste `in_progress` en BDD, aucune redirection vers /esg/results, dashboard reste "Aucune donnée". Le nœud ESG ne finalise pas l'évaluation après G3. | Ouvert |
| BUG-V5-002 | T-V5-SCROLL-01/02 | N2 | Chat scroll auto toujours cassé (reprise BUG-V2-003) : scrollTop reste à 0 après nouveau message, puis bloqué à position précédente lors de messages suivants (scrollTop=777 alors que scrollHeight=1656). | Ouvert |
| OBS-V5-001 | T-V5-W-01/02 | Info | ESG n'utilise pas les widgets interactifs (seulement tableau texte avec barèmes). Carbon utilise bien les widgets. Décision design ou régression à clarifier. | À arbitrer |
| OBS-V5-002 | T-V5-E2E-ESG-02/03/04 | Info | ESG présente 3 critères par pilier (E1-E3, S1-S3, G1-G3) au lieu des 5 annoncés dans le plan de test. Spec indique 30 critères totaux — à vérifier. | À arbitrer |

## Sections exécutées lors de la run 2026-04-24

- **Section 1** (validation V4) : 5/8 ✅, 2/8 ⚠️ (pas de widgets en ESG, non-bloquant), 2/8 🚫 non applicables
- **Section 2** (scroll) : 2/4 ❌ (BUG-V5-002), 1/4 ⚠️, 1/4 🚫
- **Section 3** (ESG E2E) : 4/9 ⚠️ (partiellement OK jusqu'à phase scoring), 2/9 ❌ (BUG-V5-001), 3/9 🚫
- **Section 4** (Carbon E2E) : 1/10 ✅ (démarrage OK, suite non exécutée par contrainte de temps)
- **Sections 5-12** : Non exécutées (stop après détection bugs N2/N3 dans sections prioritaires)

## Workflow correction

1. Exécuter tests dans l'ordre 1 → 12 (priorité décroissante)
2. Si Section 1 (validation V4) échoue : STOP et fixer avant de continuer
3. Noter tout nouveau bug BUG-V5-NNN avec ID, test source, sévérité
4. Si 0 bug N3+ et tous parcours bout-en-bout passent : Vague 5 verte → **déclencher retrospective Epic 10**
5. Si bugs N3+ : Option 0 Fix-All puis Vague 6

## Critère de "verte" Vague 5

Pour clôturer la phase de tests pré-retrospective :
- Section 1 : 100% ✅ (validation V4 obligatoire)
- Sections 3 + 4 : ≥80% ✅ (parcours ESG + Carbone bout-en-bout)
- Sections 5-8 : ≥70% ✅ (modules dépendants opérationnels)
- 0 bug N3+ ouvert
- BUG-V2-003 fermé (✅ ou confirmé non-reproductible)

## Historique exécution

| Date | Vague | Bugs ouverts | Bugs fermés |
|------|-------|--------------|-------------|
| 2026-04-23 | V1 | 12 | 0 |
| 2026-04-23 | V1 corrections | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | 7 | 12 + DEF-011-1 |
| 2026-04-24 | V2 corrections | 1 (V2-003) | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 | 4 | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 corrections | 0 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 | 2 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 corrections | 1 (V2-003) | 2 (V4-001 + V4-002) |
| 2026-04-24 | V5 | 2 (V5-001, V5-002) + 2 OBS | V4-001 partiel, V4-002 confirmé |
