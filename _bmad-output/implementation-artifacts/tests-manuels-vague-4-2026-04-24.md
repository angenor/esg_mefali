---
title: Plan de tests manuels ciblé — Vague 4 (post-corrections Vague 3)
type: test-plan
version: 4.0
status: executed-partial
date: 2026-04-24
executed_by: Angenor (via agent-browser --headed)
scope: Tests débloqués par BUG-V3-001/002/003 + DATA-V3-001 + validation BUG-V2-003 scroll
excluded: Upload documents, extension Chrome
previous_wave: tests-manuels-vague-3-2026-04-24.md
bugs_fixed_since_v3: BUG-V3-001 BUG-V3-002 BUG-V3-003 DATA-V3-001
bugs_still_open_to_verify: BUG-V2-003 (chat scroll auto, non reproduit review)
prerequisites: alembic upgrade head exécuté (funds=12 intermediaries=14 confirmés)
---

# Plan de tests manuels ciblé — Vague 4 — 2026-04-24

## Objectif

Valider les corrections Vague 3 et débloquer les 46 tests 🚫 bloqués en cascade par BUG-V3-001 (widget JSON brut).

## Résumé exécution 2026-04-24 (agent-browser --headed)

- Nouveau compte créé (inscription UI) : `amadou@ecosolaire.sn` / `TestPass123!` — EcoSolaire SARL, Sénégal
- Sections testées : 1 (Widgets), 3 (Profil backend+UI), 4 (ESG partiel), 5 (Carbone partiel), 6 (Financement), 9 (Dashboard)
- Sections non exécutées (temps) : 2 (Scroll), 7 (Applications/Credit/Plan/Reports), 8 (Multi-tour)
- **Corrections Vague 3 validées** :
  - BUG-V3-001 : widgets rendus en composants ARIA (checkbox/radio), aucune fuite JSON ✅
  - BUG-V3-003 : "consommation" utilisé dans prompt carbone, aucun "consumo" ✅
  - DATA-V3-001 : 12 fonds et ≥14 intermédiaires visibles et cliquables ✅
  - BUG-V3-002 côté backend ✅ (coerce string, reject bool)
- **Nouveaux bugs Vague 4** :
  - BUG-V4-001 (N2) : input chat verrouillé après soumission widget — parcours ESG bloqué au pilier E. Cascade massive (ESG/rapports/matching/crédit/plan d'action tous bloqués)
  - BUG-V4-002 (N2) : régression spinbutton profil — UI envoie l'ancienne valeur au backend au lieu de la nouvelle saisie

## Corrections appliquées depuis Vague 3

| Bug | Fix | Tests débloqués |
|-----|-----|----------------|
| BUG-V3-001 | Regex anti-fuite JSON widget + prompt "INTERDIT ABSOLU" | T-V3-CHAT-03→07, T-V3-ESG-02, T-V3-CREDIT/APP/PLAN, etc. (46 tests) |
| BUG-V3-002 | Validator Pydantic coerce string→int + cast Number() ProfileField | T-V3-PROFILE-01/02 |
| BUG-V3-003 | Prompt carbon "VOCABULAIRE OBLIGATOIRE" bannit "consumo" | T-V3-CARBON-01 |
| DATA-V3-001 | Migrations 030→033 appliquées, 12 fonds + 14 intermédiaires seedés | T-V3-FIN-01→10 |

## Prérequis exécution

Terminal 1 — Backend :
```bash
cd /Users/mac/Documents/projets/2025/esg_mefali/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — Frontend :
```bash
cd /Users/mac/Documents/projets/2025/esg_mefali/frontend
npm run dev
```

Terminal 3 — Tests :
```bash
agent-browser --headed
```

### Données test
Compte : `amadou@ecosolaire.sn` / `TestPass123!` (EcoSolaire SARL) OU créer nouveau
Entreprise test : AgriVert Sarl, Agriculture, 15 employés, Sénégal

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

---

## 1. Widgets interactifs — validation BUG-V3-001 (priorité 1 critique)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-W-01 | Widget QCU rendu composant | Déclencher widget secteur → radios cliquables visibles, aucun JSON brut dans message IA | ✅ | — | Widget QCM rendu en composants (checkboxes ARIA), aucun JSON brut visible |
| T-V4-W-02 | Widget QCU soumission + réponse IA | Sélectionner "Agriculture" → soumettre → IA génère texte de suivi non-vide en français | ⚠️ | N2 | Soumission OK, l'IA répond en FR. Mais input reste verrouillé après (voir BUG-V4-001) |
| T-V4-W-03 | Widget QCM multi-select | Widget "quels ODD visez-vous" → cocher 3 options → soumettre → réponse IA | ✅ | — | 3 options cochées, IA produit E1-E10 batch puis message texte FR |
| T-V4-W-04 | Widget avec justification | Widget + textarea → saisir 50c → soumettre → réponse IA | ⬜ | — | Non déclenché (flow n'a pas présenté de widget justification) |
| T-V4-W-05 | Widget justification max 400c | Saisir 450c → input bloque à 400 | ⬜ | — | Non déclenché |
| T-V4-W-06 | Bouton "Répondre autrement" | Cliquer → widget masqué, input texte débloqué, saisir libre → réponse IA | ⬜ | — | Non testé |
| T-V4-W-07 | Enchaînement 3 widgets consécutifs | Répondre 3 widgets → pas de message vide entre | ❌ | N2 | Bloqué : après 1er widget ESG, aucun 2e widget n'apparaît pour pilier Social (voir BUG-V4-001) |
| T-V4-W-08 | Dark mode widget | Toggle dark → widgets stylés dark correctement | ✅ | — | `html.dark` activé, screenshot /tmp/v4-w08-darkmode.png |
| T-V4-W-09 | Pas de leak JSON dans le texte | Ouvrir devtools → inspecter DOM message → aucune fuite JSON visible même dans commentaires HTML | ✅ | — | Regex `__sse_interactive\|widget_type\|ask_interactive\|{"` → aucun match dans DOM |

## 2. Chat scroll auto — BUG-V2-003 validation

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-SCROLL-01 | Scroll auto nouveau message | Envoyer 5 messages longs → scroll descend à chaque réponse | ⬜ | — | Non exécuté (priorité secondaire — temps limité) |
| T-V4-SCROLL-02 | Scroll pendant streaming | Message long streamé → scroll suit le curseur | ⬜ | — | Non exécuté |
| T-V4-SCROLL-03 | Scroll respecte lecture manuelle | Scroll vers haut → nouveau message n'interrompt pas | ⬜ | — | Non exécuté |

## 3. Profil — BUG-V3-002 validation spinbutton

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-PROFILE-01 | Spinbutton employés sauvegarde | /profile → ✎ employés → 25 → ✓ → F5 → 25 persisté | ❌ | N2 | BUG-V4-002 : UI envoie l'ancienne valeur, pas la nouvelle saisie (ex. saisi 42, PATCH body `{"employee_count":25}`) |
| T-V4-PROFILE-02 | Spinbutton année création | ✎ année → 2018 → ✓ → F5 → 2018 persisté | ⬜ | — | Non testé (même composant spinbutton que PROFILE-01, probablement même bug) |
| T-V4-PROFILE-03 | Coercion string backend | Envoyer "15" string via devtools → backend accepte via validator Pydantic | ✅ | — | `PATCH {"employee_count":"15"}` → 200 OK, valeur 15 persistée |
| T-V4-PROFILE-04 | Rejet bool (validator) | Tenter PATCH avec true → rejet 422 | ✅ | — | `PATCH {"employee_count":true}` → 422 "Valeur numerique invalide" |
| T-V4-PROFILE-05 | Annuler édition ✕ | Modifier → ✕ → valeur originale restaurée | ⬜ | — | Non testé isolément |

## 4. Module ESG complet (débloqué BUG-V3-001)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-ESG-01 | Démarrer évaluation via chat | "évalue mon ESG" → routing esg_scoring_node → widget critères E | ✅ | — | Routing OK, widget pilier Environnement rendu avec 5 options QCM |
| T-V4-ESG-02 | Répondre 5 critères E via widgets | Soumissions successives, progress affiché | ⚠️ | N2 | 1 widget submit OK, puis IA produit batch E1-E10 (7,6,5,6,4,5,4,3,5,4). Mais plus aucun widget pour pilier Social (BUG-V4-001) |
| T-V4-ESG-03 | Répondre 5 critères S | Progress continue | ❌ | N2 | Bloqué par BUG-V4-001 — input verrouillé, aucun widget S après message "Commençons par les conditions de travail" |
| T-V4-ESG-04 | Répondre 5 critères G | Progress continue | 🚫 | — | Bloqué en amont |
| T-V4-ESG-05 | Finalisation score /100 | Score calculé, redirection /esg/results | 🚫 | — | Bloqué |
| T-V4-ESG-06 | Page résultats | Donut Chart.js + E/S/G + global | ⬜ | — | Non atteint |
| T-V4-ESG-07 | Benchmark sectoriel | Benchmark Agriculture affiché ou fallback | ⬜ | — | Non atteint |
| T-V4-ESG-08 | Reprise évaluation F5 | Quitter mid-ESG → F5 → chat propose reprendre | ⬜ | — | Non testé |
| T-V4-ESG-09 | Dark mode résultats | Charts + cards dark | ⬜ | — | Non atteint |
| T-V4-ESG-10 | Langue FR stricte | Aucun caractère chinois/anglais/pt/es dans messages ESG | ✅ | — | Tous messages ESG vus en FR pur (aucun mot étranger détecté) |

## 5. Module Carbone complet (débloqué BUG-V3-001 + BUG-V3-003)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-CARBON-01 | Démarrer bilan via chat | "bilan carbone" → routing carbon_node → "consommation" (pas "consumo") | ✅ | — | BUG-V3-003 validé : message "tes consommations d'électricité et de carburant", "consommation annuelle d'électricité" — aucun "consumo" |
| T-V4-CARBON-02 | Catégorie énergie widgets | Répondre conso électricité + carburant → calcul tCO2e | ⚠️ | — | Texte libre (pas widget). Q1 30000 kWh OK → Q2 générateur diesel |
| T-V4-CARBON-03 | Catégorie transport | Répondre flotte → cumul | ⬜ | — | Non exécuté complet |
| T-V4-CARBON-04 | Catégorie déchets | Cumul | ⬜ | — | Non exécuté |
| T-V4-CARBON-05 | Finalisation total tCO2e | Total calculé, redirection /carbon/results | ⬜ | — | Non atteint |
| T-V4-CARBON-06 | Équivalences parlantes FR | "X voitures/an" en français strict | ⬜ | — | Non atteint |
| T-V4-CARBON-07 | Plan de réduction | Liste actions affichée | ⬜ | — | Non atteint |
| T-V4-CARBON-08 | Benchmark Afrique Ouest | Benchmark ou fallback | ⬜ | — | Non atteint |
| T-V4-CARBON-09 | Langue FR stricte carbone | Aucun mot pt/es/zh/en dans les messages | ✅ | — | Tous messages carbone vus en FR pur |

## 6. Module Financement (DATA-V3-001 validation + BUG-V2-006 confirmation)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-FIN-01 | Onglet "Tous les fonds" sans ESG | ≥12 fonds affichés (GCF, FEM, BOAD, BAD, SUNREF, FNDE, ECREEE, BIDC, UEMOA, Proparco, BEI, Africa50) | ✅ | — | "Recommandations 12" + onglet "Tous les fonds" affiche GCF, FEM, Adaptation Fund, BOAD, BAD SEFA, BIDC, SUNREF, FNDE, IFC, BCEAO... (15+ marqueurs détectés) |
| T-V4-FIN-02 | Onglet Intermédiaires sans ESG | ≥14 intermédiaires affichés avec coordonnées | ✅ | — | Onglet Intermédiaires affiche ANDE, BAD, BOAD, SGBCI, SIB, Ecobank, PNUD, AFD, IFC, BCEAO, Banque Atlantique, etc. (≥14 détectés) |
| T-V4-FIN-03 | Onglet Recommandés sans ESG | Message "Évaluation ESG requise" visible (seul onglet qui doit bloquer) | ⚠️ | — | Onglet Recommandations affiche directement 12 fonds avec score compatibilité (pas de blocage ESG). Le score ESG=0 apparait comme critère à améliorer sur chaque fiche. Comportement à valider avec le PO |
| T-V4-FIN-04 | Filtre secteur fonds | "Énergie" → liste restreinte cohérente | ⬜ | — | Non testé (temps) |
| T-V4-FIN-05 | Filtre montant | Cohérent | ⬜ | — | Non testé |
| T-V4-FIN-06 | Filtre accès direct/intermédiaire | Cohérent | ⬜ | — | Non testé |
| T-V4-FIN-07 | Filtre statut | Ouvert/fermé cohérent | ⬜ | — | Non testé |
| T-V4-FIN-08 | Détail fonds | /financing/[id] charge avec détails complets | ✅ | — | Détail GCF OK : description, montant, durée, secteurs, score ESG min, documents requis, parcours accès |
| T-V4-FIN-09 | Filtre pays intermédiaire Sénégal | Intermédiaires sénégalais filtrés | ⬜ | — | Non testé |
| T-V4-FIN-10 | Matching chat post-ESG | Avec score ESG → chat "trouve-moi financement" → matching avec fonds réels | ⬜ | — | Bloqué : pas de score ESG (voir BUG-V4-001) |
| T-V4-FIN-11 | Langue FR stricte financement | Messages financing_node 100% FR | ⬜ | — | Non atteint via chat |

## 7. Modules dépendants (débloqués BUG-V3-001)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-APP-01 | Créer dossier via chat | "crée dossier pour GCF" → tool déclenché → dossier créé | ⬜ | — | |
| T-V4-APP-02 | Éditer dossier | /applications/[id] → toast-ui editor → save | ⬜ | — | |
| T-V4-CREDIT-01 | Score credit via chat | "évalue ma solvabilité" → questions Mobile Money → score | ⬜ | — | |
| T-V4-CREDIT-02 | Score hybride affichage | /credit-score → score + impact affichés | ⬜ | — | |
| T-V4-PLAN-01 | Générer plan action | "génère mon plan d'action" → 10-15 actions multi-catégories | ⬜ | — | |
| T-V4-PLAN-02 | Filtre environment | Actions E filtrées | ⬜ | — | |
| T-V4-PLAN-03 | Filtre financing | Actions financing filtrées | ⬜ | — | |
| T-V4-PLAN-04 | Progression action | Marquer fait → barre globale + catégorie MAJ | ⬜ | — | |
| T-V4-PLAN-05 | Action intermédiaire | Catégorie intermediary_contact → coordonnées snapshot | ⬜ | — | |
| T-V4-REPORT-01 | Générer rapport ESG | Avec score ESG → "Générer" → PDF produit + notif chat | ⬜ | — | |
| T-V4-REPORT-02 | Preview + download PDF | Preview inline 9 sections + download | ⬜ | — | |

## 8. Multi-tour & reprise

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-MT-01 | Continuation ESG | Dans ESG → 3 tours → reste dans ESG | ⬜ | — | active_module persistance |
| T-V4-MT-02 | Changement module | Dans ESG → "financement" → routing financing | ⬜ | — | |
| T-V4-MT-03 | Reprise après F5 | Mi-ESG → F5 → chat propose reprendre | ⬜ | — | |
| T-V4-MT-04 | Basculer conversation | 2 conversations parallèles → basculer → pas de mélange | ⬜ | — | |

## 9. Dashboard avec données réelles

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V4-DASH-01 | Cartes post-parcours complet | Scores ESG + carbone + credit + financement affichés | ⚠️ | — | 4 cartes présentes (ESG/Carbone/Crédit/Financement). ESG/Carbone/Crédit = "Aucune donnée" (parcours non complété à cause de BUG-V4-001). Financement : 12 fonds recommandés affichés |
| T-V4-DASH-02 | Badge first_carbon | Premier bilan → badge débloqué | ⬜ | — | Non atteint (bilan pas finalisé) |
| T-V4-DASH-03 | Badge esg_above_50 | Score ESG > 50 → badge | ⬜ | — | Non atteint |
| T-V4-DASH-04 | Badge full_journey | Tous modules complétés → badge | ⬜ | — | Non atteint. Les 5 badges sont visibles verrouillés |

---

## Synthèse bugs Vague 4

| ID bug | Test source | Sévérité | Description | Status |
|--------|-------------|----------|-------------|--------|
| BUG-V4-001 | T-V4-W-07, T-V4-ESG-02, T-V4-ESG-03 | **N2** | Après la soumission du premier widget ESG (pilier E), l'IA produit un batch de 10 scores E1-E10 puis envoie un message texte annonçant le pilier Social, mais aucun 2e widget n'est présenté et l'input texte reste **verrouillé** (textarea `disabled`). Le parcours ESG ne peut pas progresser au-delà du pilier E, bloquant toute la suite (ESG score, rapports, matching financement, crédit, plan d'action). Reproductible. | ouvert |
| BUG-V4-002 | T-V4-PROFILE-01 | **N2** | L'UI du champ spinbutton (ex. `Nombre d'employés`) envoie au backend l'**ancienne valeur** et non celle saisie. Reproduction : saisir 42 dans le champ édité → cliquer ✓ → body PATCH intercepté `{"employee_count":25}` (valeur précédente). Backend OK (`PATCH /api/company/profile {"employee_count":25}` → 200, `{"employee_count":"15"}` → 200, `{"employee_count":true}` → 422). Correction nécessaire côté frontend (v-model ou bind du composant ProfileField). | ouvert |

## Workflow correction

1. Exécuter tests dans l'ordre 1 → 9 (priorité décroissante)
2. Noter tout nouveau bug BUG-V4-NNN avec ID, test source, sévérité N1/N2/N3/N4
3. Si 0 bug N3+ : Vague 4 verte → déclencher retrospective Epic 10
4. Si bugs N3+ : batch Option 0 Fix-All puis Vague 5

## Historique exécution

| Date | Vague | Bugs ouverts | Bugs fermés |
|------|-------|--------------|-------------|
| 2026-04-23 | V1 | 12 | 0 |
| 2026-04-23 | V1 corrections | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | 7 | 12 + DEF-011-1 confirmés |
| 2026-04-24 | V2 corrections | 1 (V2-003) | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 | 4 | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 corrections | 0 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 | 2 (V4-001 N2 widget cascade, V4-002 N2 spinbutton UI) | BUG-V3-001 widget/JSON ✅, BUG-V3-003 consumo ✅, DATA-V3-001 fonds/intermédiaires ✅, BUG-V3-002 côté backend ✅ (côté frontend ❌ régression UI) |
