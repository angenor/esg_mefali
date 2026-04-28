---
title: Plan de tests manuels ciblé — Vague 3 (post-corrections Vague 2)
type: test-plan
version: 3.0
status: executed-blocked
execution_date: 2026-04-24
executor_agent: Claude Opus 4.7 via agent-browser --headed
blocker: BUG-V3-001 (widget JSON brut) bloque la majorité des tests chat / parcours modules
date: 2026-04-24
executed_by: Angenor (via agent-browser --headed)
scope: Tests ciblés débloqués par BUG-V2-001/002/005/006/007 + DEF-BUG-V2-001-1 + validation BUG-V2-003 scroll
excluded: Upload documents, extension Chrome, tests déjà ✅ en Vague 2 (sauf régression suspectée)
previous_wave: tests-manuels-vague-2-2026-04-23.md
bugs_fixed_since_v2: BUG-V2-001 BUG-V2-002 BUG-V2-004 BUG-V2-005 BUG-V2-006 BUG-V2-007 DEF-BUG-V2-001-1
bugs_still_open_to_verify: BUG-V2-003 (chat scroll auto, code en place mais non reproduit review)
---

# Plan de tests manuels ciblé — Vague 3 — 2026-04-24

## Résumé exécutif (2026-04-24)

**Statut global : 🔴 VAGUE 3 ROUGE — 2 bugs N1 bloquants détectés.**

| Métrique | Valeur |
|---------|--------|
| Tests exécutés effectivement | 13 / 60 |
| ✅ OK | 7 |
| ⚠️ OK partiel | 4 |
| ❌ Bug bloquant | 3 (BUG-V3-001 × multiples, BUG-V3-002 × 2) |
| 🚫 Non-testés (bloqués) | 46 |

**Bugs critiques nouveaux :**
- **BUG-V3-001 (N1)** — Widget interactif JSON affiché en texte brut → tout le chat conversationnel inutilisable post-welcome.
- **BUG-V3-002 (N1)** — ProfileField spinbutton : édition inline numérique non persistée (BUG-V2-007 réouvert).
- BUG-V3-003 (N3) — « consumo » (pt/es) dans message carbone.
- DATA-V3-001 (env) — Tables funds/intermediaries vides → bloque T-V3-FIN-01/02/04…10.

**Corrections Vague 2 confirmées tenues :**
- BUG-V2-001 langue FR chat welcome ✅
- BUG-V2-006 gate ESG scopée à Recommandations uniquement ✅
- BUG-V2-004 accents profil ✅
- BUG-V2-005 accents ESG ✅
- Routing multi-modules chat_node → esg/carbon/financing ✅ (changement module OK)

**Recommandation :** Option 0 Fix-All de BUG-V3-001 (widget) + BUG-V3-002 (ProfileField) + seed DATA-V3-001 avant lancement Vague 4.

## Objectif

Vérifier que les corrections Vague 2 tiennent en conditions réelles :
- Langue française stable dans chat + 6 modules spécialistes (BUG-V2-001 + DEF-BUG-V2-001-1)
- IA répond avec texte après soumission widget interactif (BUG-V2-002)
- ESG gate Financement restreinte au seul onglet recommendations (BUG-V2-006)
- Profil spinbutton inline sauvegarde (BUG-V2-007)
- Accents corrigés sur tous modules (BUG-V2-004 + BUG-V2-005)
- Scroll chat automatique (BUG-V2-003 à valider)

Débloquer les tests 🔒 des Vagues précédentes pour couvrir les parcours ESG/Carbone/Financement/Plan complets.

## Corrections appliquées depuis Vague 2

| Bug | Fix | Tests débloqués |
|-----|-----|----------------|
| BUG-V2-001 | RAPPEL FINAL + LANGUAGE_INSTRUCTION en queue chat_node | T-CHAT-02/04/08 langue FR |
| BUG-V2-002 | Puce post-tool response dans tool_instructions chat_node | T-CHAT-04/08/09/12/14 widgets + tool flow |
| DEF-BUG-V2-001-1 | RAPPEL FINAL sur 6 nœuds spécialistes | T-ESG-01/T-CARBON-01/T-FIN-09/T-CREDIT-02/T-APP-02/T-PLAN-02 |
| BUG-V2-006 | Gate ESG scopée à activeTab === 'recommendations' | T-FIN-01/02/03/04/05/06/07/08 |
| BUG-V2-007 | ProfileField.vue type="button" + aria-label | T-PROFILE-02/03 |
| BUG-V2-004 + BUG-V2-005 | 17 corrections accents + sections profil | T-ESG-12, T-PROFILE-01, T-FIN-01, T-CREDIT-01, T-REPORT-01, T-CARBON labels |

## Prérequis exécution

Terminal 1 — Backend :
```bash
cd /Users/mac/Documents/projets/2025/esg_mefali/backend
source venv/bin/activate
alembic upgrade head
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
Compte : réutiliser compte Vague 2 ou nouveau — entreprise "AgriVert Sarl", Agriculture, 15 employés, Sénégal

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

---

## 1. Chat — Langue & Widgets (priorité 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-CHAT-01 | Langue réponse simple | "Bonjour" → réponse 100% FR, aucun caractère chinois/anglais/arabe | ✅ | — | Texte réponse 100% FR. BUG-V2-001 corrigé confirmé. |
| T-V3-CHAT-02 | Profiling multi-champ | "AgriVert Sarl, Agriculture, 15 employés, Sénégal" → profil créé + message FR de suivi | 🚫 | — | Profil déjà existant (AgriVert Sarl) — non re-testé |
| T-V3-CHAT-03 | Widget QCU soumission | Déclencher widget QCU → sélectionner option → soumettre → IA génère texte visible non-vide | ❌ | N1 | **BUG-V3-001** JSON widget `{"question_type":"qcu",...}` affiché en texte brut dans le message, aucune UI widget rendue. Input chat désactivé → utilisateur bloqué. /tmp/v3-chat-01.png |
| T-V3-CHAT-04 | Widget QCM multi-select | Widget QCM → cocher 2+ options → soumettre → IA génère texte de suivi | ❌ | N1 | Bloqué par BUG-V3-001 (widget QCM idem brut) |
| T-V3-CHAT-05 | Widget avec justification | Widget + textarea justification → saisir texte (max 400c) → soumettre → réponse IA | ❌ | N1 | Bloqué par BUG-V3-001 |
| T-V3-CHAT-06 | Widget "Répondre autrement" | Cliquer "Répondre autrement" → input débloqué → saisir texte libre → réponse IA | ❌ | N1 | Bloqué par BUG-V3-001 (aucun bouton rendu) |
| T-V3-CHAT-07 | Enchaînement 3 widgets | Répondre 3 widgets consécutifs → pas de message vide entre | ❌ | N1 | Bloqué par BUG-V3-001 |
| T-V3-CHAT-08 | Scroll auto nouveau message | Envoyer 5 messages longs → scroll se déplace vers bas à chaque réponse | 🚫 | — | Non-testé (input bloqué par BUG-V3-001) |
| T-V3-CHAT-09 | Scroll auto streaming | Pendant streaming long → scroll suit le curseur | 🚫 | — | Non-testé (input bloqué par BUG-V3-001) |
| T-V3-CHAT-10 | Scroll respecte manuel | Scroll manuel vers haut → nouveau message n'interrompt pas lecture | 🚫 | — | Non-testé (input bloqué par BUG-V3-001) |

## 2. Modules spécialistes — Langue FR (priorité 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-ESG-01 | Routing ESG FR | Chat → "évalue mon ESG" → routing esg_scoring_node → premier message 100% FR | ✅ | — | "Pour démarrer ton évaluation ESG, je vais t'accompagner sur l'interface dédiée." 100% FR. Widget JSON leak séparé (BUG-V3-001). |
| T-V3-ESG-02 | Question ESG E FR | Répondre critère E → question suivante 100% FR | 🚫 | — | Non-testé — bloqué par BUG-V3-001 (widget JSON) |
| T-V3-CARBON-01 | Routing Carbone FR | Chat → "bilan carbone" → carbon_node → message 100% FR | ⚠️ | N3 | Routing OK + texte FR mais **BUG-V3-003** résiduel : mot "consumo" (pt/es) dans « Quel est ton consumo électrique mensuel » |
| T-V3-FIN-chat-01 | Routing Financement FR | Chat → "je cherche un financement" → financing_node → 100% FR | ✅ | — | Routing + redirection `/financing` OK, guided tour FR s'ouvre |
| T-V3-CREDIT-chat-01 | Routing Credit FR | Chat → "évalue ma solvabilité" → credit_node → 100% FR | 🚫 | — | Non-testé — input chat bloqué par widget JSON pending (BUG-V3-001) |
| T-V3-APP-chat-01 | Routing Application FR | Chat → "crée dossier GCF" → application_node → 100% FR | 🚫 | — | Non-testé — idem BUG-V3-001 |
| T-V3-PLAN-chat-01 | Routing Plan FR | Chat → "génère mon plan d'action" → action_plan_node → 100% FR | 🚫 | — | Non-testé — idem BUG-V3-001 |

## 3. Parcours ESG complet

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-ESG-03 | Répondre 5 critères E | Sauvegarde + progress affiché | 🚫 | — | Non-testé — bloqué BUG-V3-001 (widget ESG idem brut) |
| T-V3-ESG-04 | Répondre 5 critères S | Progress continue | 🚫 | — | Non-testé — idem |
| T-V3-ESG-05 | Répondre 5 critères G | Progress continue | 🚫 | — | Non-testé — idem |
| T-V3-ESG-06 | Finalisation score /100 | Redirection /esg/results avec score | 🚫 | — | Non-testé — idem |
| T-V3-ESG-07 | Page résultats | Donut Chart.js + E/S/G + score global | 🚫 | — | Non-testé — pas de score calculé |
| T-V3-ESG-08 | Benchmark sectoriel | Benchmark secteur Agriculture (ou fallback) | 🚫 | — | Non-testé — idem |
| T-V3-ESG-09 | Reprise évaluation | Quitter mid-ESG → F5 → chat propose reprendre | 🚫 | — | Non-testé — idem |
| T-V3-ESG-10 | Dark mode résultats | Charts + cards stylés dark | 🚫 | — | Non-testé — idem |
| T-V3-ESG-11 | Accents page ESG | "Évaluation", "critères", "Démarrez" accentués | ✅ | — | Tous présents (regex sur page /esg) |

## 4. Parcours Carbone complet

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-CARBON-02 | Catégorie énergie | Calcul tCO2e progressif | 🚫 | — | Non-testé — bloqué BUG-V3-001 (widget carbone JSON brut) |
| T-V3-CARBON-03 | Catégorie transport | Cumul | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-04 | Catégorie déchets | Cumul | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-05 | Finalisation bilan | Total tCO2e + redirection /carbon/results | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-06 | Page résultats | Donut + équivalences FCFA | 🚫 | — | Non-testé — pas de bilan complété |
| T-V3-CARBON-07 | Équivalences FR | "X voitures/an", "X foyers/an" en français | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-08 | Plan réduction | Liste actions | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-09 | Benchmark Afrique Ouest | Benchmark secteur (ou fallback) | 🚫 | — | Non-testé — idem |
| T-V3-CARBON-10 | Accents carbone | "Énergie", "déchets", "équivalences", "réduction" | 🚫 | — | Non-testé — page /carbon (liste) n'affiche que "Empreinte Carbone" (pas de bilan pour valider labels) |

## 5. Financement — onglets catalogue & intermédiaires (régression BUG-V2-006)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-FIN-01 | Onglet "Tous les fonds" sans ESG | ≥12 fonds affichés même sans score ESG | ⚠️ | N2 | Gate ESG absent ✅ (BUG-V2-006 code fix OK) MAIS API `GET /api/financing/funds?` renvoie `{items:[],total:0}` → **DATA-V3-001** BDD vide (seeds fonds manquants) |
| T-V3-FIN-02 | Onglet "Intermédiaires" sans ESG | ≥14 intermédiaires affichés | ⚠️ | N2 | Gate ESG absent ✅ MAIS API `GET /api/financing/intermediaries?` renvoie `{items:[],total:0}` → DATA-V3-001 BDD vide |
| T-V3-FIN-03 | Onglet "Recommandés" sans ESG | Message "Évaluation ESG requise" visible (seul onglet qui doit bloquer) | ✅ | — | "Réaliser mon évaluation ESG" affiché UNIQUEMENT sur cet onglet. BUG-V2-006 confirmé corrigé. |
| T-V3-FIN-04 | Filtre secteur fonds | Filtrer "Énergie" → liste cohérente | 🚫 | — | Non-testable — BDD vide (DATA-V3-001) |
| T-V3-FIN-05 | Filtre montant | Filtrage cohérent | 🚫 | — | Idem DATA-V3-001 |
| T-V3-FIN-06 | Filtre accès direct/intermédiaire | Filtrage cohérent | 🚫 | — | Idem DATA-V3-001 |
| T-V3-FIN-07 | Détail fonds | /financing/[id] charge avec détails complets | 🚫 | — | Idem — aucun fonds pour tester le détail |
| T-V3-FIN-08 | Filtre pays intermédiaire | Filtrer Sénégal → intermédiaires sénégalais | 🚫 | — | Idem DATA-V3-001 |
| T-V3-FIN-09 | Matching chat après ESG | Avoir score ESG → chat "trouve-moi financement" → matching | 🚫 | — | Bloqué BUG-V3-001 + DATA-V3-001 |
| T-V3-FIN-10 | Accents financement | "Évaluation", "Réaliser", "Accès", "Intermédiaire", "Suggéré", "Développement" | ⚠️ | N4 | "Évaluation", "Réaliser", "Intermédiaires" présents. "Accès", "Suggéré", "Développement" absents de la page car les données sont vides (DATA-V3-001) — non-bloquant |

## 6. Profil — inline edit spinbutton (BUG-V2-007)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-PROFILE-01 | Éditer nombre employés (spinbutton) | ✎ → modifier valeur → ✓ → F5 → valeur persistée | ❌ | N1 | **BUG-V3-002** ProfileField spinbutton : PATCH envoyé mais `employee_count` reste null après 2 essais (27 puis 99) via UI. PATCH direct API `/api/company/profile` avec `{employee_count:42}` fonctionne (status 200, valeur persistée). → Régression v-model ou formData côté ProfileField.vue pour champs numériques. BUG-V2-007 NON corrigé. |
| T-V3-PROFILE-02 | Éditer année création (spinbutton) | Même flow → persisté | ❌ | N1 | Non re-testé mais même composant ProfileField → bug présumé identique BUG-V3-002 |
| T-V3-PROFILE-03 | Annuler édition ✕ | Cliquer ✕ → valeur originale restaurée | 🚫 | — | Non-testé (focus mis sur BUG-V3-002) |
| T-V3-PROFILE-04 | Validation champ vide | Vider champ nom → ✓ → erreur validation | 🚫 | — | Non-testé |
| T-V3-PROFILE-05 | Accents profil | "Identité", "employés", "Complétez", "personnalisés", "énergétique", "déchets" | ✅ | — | 6/6 accents présents (regex sur /profile). BUG-V2-004 confirmé corrigé. |

## 7. Modules dépendants (débloqués par BUG-V2-002)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-APP-01 | Créer dossier via chat | Chat "crée dossier GCF" → tool déclenché → dossier créé | 🚫 | — | Non-testé — input chat bloqué (BUG-V3-001) |
| T-V3-APP-02 | Éditer dossier | /applications/[id] → éditer via toast-ui → save | 🚫 | — | Non-testé |
| T-V3-CREDIT-01 | Score credit via chat | "évalue ma solvabilité" → questions Mobile Money → score | 🚫 | — | Non-testé — BUG-V3-001 |
| T-V3-PLAN-01 | Générer plan action | "génère mon plan" → 10-15 actions multi-catégories | 🚫 | — | Non-testé — BUG-V3-001 |
| T-V3-PLAN-02 | Filtre environment | Filtrer → actions E visibles | 🚫 | — | Non-testé — pas de plan généré |
| T-V3-PLAN-03 | Progression action | Marquer fait → barre MAJ | 🚫 | — | Non-testé — idem |
| T-V3-REPORT-01 | Générer rapport ESG | Avoir score ESG → bouton Générer → PDF produit | 🚫 | — | Non-testé — pas de score ESG (BUG-V3-001 bloque parcours ESG) |
| T-V3-REPORT-02 | Preview + download PDF | Preview inline + download PDF | 🚫 | — | Non-testé |

## 8. Multi-tour & reprise

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-MT-01 | Continuation ESG | Dans ESG → répondre 2 critères → 3ème tour reste dans ESG | 🚫 | — | Non-testé — BUG-V3-001 |
| T-V3-MT-02 | Changement module | Dans ESG → "je veux un financement" → routing financing | ⚠️ | — | Observé : dans la même conversation après routing ESG puis "bilan carbone" → routing carbon OK (active_module commute). Puis "je cherche un financement" → routing financing OK (redirection /financing). ✅ transitions module. Mais widget JSON bloque le follow-up. |
| T-V3-MT-03 | Reprise après F5 | Mi-ESG → F5 → chat propose reprendre où laissé | 🚫 | — | Non-testé |
| T-V3-MT-04 | Basculer conversation | 2 conversations parallèles → basculer → pas de mélange | 🚫 | — | Non-testé |

## 9. Dashboard avec données

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V3-DASH-01 | Cartes post-données ESG + Carbone | Cartes affichent scores réels | 🚫 | — | Non-testé — pas de données (ESG/Carbone non-complétés suite BUG-V3-001) |
| T-V3-DASH-02 | Badge first_carbon | Premier bilan complété → badge débloqué | 🚫 | — | Non-testé — idem |
| T-V3-DASH-03 | Badge esg_above_50 | Score ESG > 50 → badge débloqué | 🚫 | — | Non-testé — idem |
| T-V3-DASH-04 | Badge full_journey | Tous modules complétés → badge | 🚫 | — | Non-testé — idem |

---

## Synthèse bugs Vague 3

| ID bug | Test source | Sévérité | Description | Status |
|--------|-------------|----------|-------------|--------|
| **BUG-V3-001** | T-V3-CHAT-03/04/05/06/07, T-V3-ESG-02, T-V3-CARBON-02, T-V3-APP/CREDIT/PLAN | **N1 bloquant** | Widget interactif : le payload JSON `{"question_type":"qcu\|qcm",...}` s'affiche en texte brut dans le message de l'IA au lieu d'être intercepté et rendu en composant widget cliquable. Observé sur chat_node (welcome profiling), esg_scoring_node (démarrage éval), carbon_node (catégorie énergie). Input chat désactivé car pending question existe → utilisateur complètement bloqué. Hypothèse : le tool `ask_interactive_question` n'est pas appelé par le LLM ; au lieu de cela, le LLM retourne la structure JSON inline dans son contenu texte. Le marker SSE `<!--SSE:{"__sse_interactive_question__":true,...}-->` n'est jamais produit. Régression Epic 018 / BUG-V2-002. Preuve : /tmp/v3-chat-01.png | open |
| **BUG-V3-002** | T-V3-PROFILE-01/02 | **N1 bloquant** | ProfileField inline edit (spinbutton) : le PATCH est envoyé au backend mais `employee_count` reste `null` en base (2 essais via UI). PATCH direct `/api/company/profile` avec `{employee_count:42}` fonctionne (status 200, persisté en base). Donc le backend est OK, le bug est dans ProfileField.vue — probable régression v-model / binding pour inputs numériques. BUG-V2-007 NON corrigé malgré fix v2 `type="button"` + `aria-label`. | open |
| **BUG-V3-003** | T-V3-CARBON-01 | N3 mineur | Fuite de langue : le message de démarrage Carbone contient le mot « consumo » (pt/es) dans « Quel est ton consumo électrique mensuel facturé ? (kWh sur ta facture) ». Reste du texte 100% FR. Le prompt carbon.py ou le LLM glisse ponctuellement un mot étranger malgré le RAPPEL FINAL. | open |
| **DATA-V3-001** | T-V3-FIN-01/02/04/05/06/07/08/10 | N2 environnement | BDD de développement : tables `funds` et `intermediaries` vides (0 lignes). Les endpoints `GET /api/financing/funds?` et `GET /api/financing/intermediaries?` retournent `{items:[],total:0}`. Les seeds attendues (12 fonds, 14 intermédiaires) ne sont pas en place. Non-bloquant pour validation du code (BUG-V2-006 confirmé corrigé — gate scopée à recommendations) mais bloquant pour la couverture fonctionnelle des onglets catalogue/intermédiaires. Action : relancer `alembic upgrade head` + script de seed ou vérifier scripts de seed. | open |

## Workflow correction

1. Exécuter tests dans l'ordre 1 → 9 (priorité décroissante)
2. Noter tout nouveau bug BUG-V3-NNN avec ID, test source, sévérité N1/N2/N3/N4
3. Si 0 bug N3+ : Vague 3 verte → déclencher retrospective Epic 10
4. Si bugs N3+ : batch Option 0 Fix-All puis Vague 4

## Historique exécution

| Date | Vague | Bugs ouverts | Bugs fermés |
|------|-------|--------------|-------------|
| 2026-04-23 | V1 | 12 | 0 |
| 2026-04-23 | V1 corrections | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | 7 | 12 + DEF-011-1 confirmés |
| 2026-04-24 | V2 corrections | 1 open (V2-003) | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 | 3 N1-N3 (BUG-V3-001/002/003) + 1 DATA | Confirmés : BUG-V2-001 (chat FR), BUG-V2-006 (gate recommandations), BUG-V2-004 (accents profil), BUG-V2-005 (accents ESG) |
