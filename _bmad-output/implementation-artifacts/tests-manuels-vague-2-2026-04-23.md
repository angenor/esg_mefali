---
title: Plan de tests manuels automatisés — Vague 2 (post-corrections Vague 1)
type: test-plan
version: 2.0
status: in-progress
date: 2026-04-23
executed_by: Angenor (via agent-browser --headed)
scope: Tous modules — retests complets post-corrections + tests débloqués par BUG-006/009/011
excluded: Upload documents (agent-browser limitation), extension Chrome, features Phase 1+ non livrées
previous_wave: tests-manuels-vague-1-2026-04-23.md
bugs_fixed: BUG-001 BUG-002 BUG-003 BUG-004 BUG-005 BUG-006 BUG-007 BUG-007b BUG-008 BUG-009 BUG-010 BUG-011 DEF-BUG-011-1
---

# Plan de tests manuels — Vague 2 — 2026-04-23

## Objectif

Retests complets post-corrections Vague 1. Tous les tests 🔒 débloqués par BUG-006 (LangGraph recursion) sont maintenant testables. Valider la stabilité globale de la stack corrigée avant retrospective Epic 10 et transition Epic 11.

## Corrections appliquées depuis Vague 1

| Bug | Fix | Impact tests |
|-----|-----|-------------|
| BUG-006 | chat_node incrémente tool_call_count (recursion guard) | Débloque T-CHAT-04→20, T-ESG-01→09, T-CARBON-01→13, T-PLAN-02→09, T-CREDIT-02→03, T-REPORT-02→08, T-APP-02→04 |
| BUG-011 + DEF-011-1 | LANGUAGE_INSTRUCTION en tête system.py + 6 builders | Débloque réponses FR dans tous modules |
| BUG-001 | Cast source_type::source_type_enum migration 030 | Migration démarre proprement |
| BUG-009 | Migration 033 seed 12 fonds + 14 intermédiaires | Débloque T-FIN-01→14 |
| BUG-002 | Plugin auth.client.ts hydratation JWT avant middleware | Débloque T-AUTH-08 |
| BUG-007 | useCompanyProfile → apiFetch avec intercepteur 401 | Débloque T-PROFILE-02→03 |
| BUG-007b | 8 accents ProfileForm.vue + profile.vue | Débloque T-PROFILE-01 |
| BUG-008 | ESG gate restreinte à onglet recommendations | Débloque T-FIN-01 |
| BUG-003/004/005/010 | Accents layout/login/register + 404 FR dark | Débloque T-AUTH-09, T-PERF-06 |

## Prérequis exécution

### Lancement stack

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

### Données de test

- **Compte test** : créer nouveau ou réutiliser existant
- **Entreprise** : "AgriVert Sarl" — Agriculture — 15 employés — Sénégal — Dakar

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel / UX à améliorer |
| ❌ | Bug bloquant |
| 🚫 | Non applicable |

---

## 1. Authentification & Onboarding

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-AUTH-01 | Register nouveau compte | Redirection /dashboard avec session active | ✅ | — | |
| T-AUTH-02 | Register email déjà existant | Erreur "email déjà utilisé" en français | ✅ | — | "Un compte avec cet email existe déjà" |
| T-AUTH-03 | Register password faible | Validation client + message erreur FR | ✅ | — | Validation HTML5 "minimum 8 caractères" |
| T-AUTH-04 | Login compte valide | Redirection dashboard, session persistante | ✅ | — | |
| T-AUTH-05 | Login credentials invalides | "Identifiants invalides", pas de fuite info | ✅ | — | |
| T-AUTH-06 | Logout | Redirection /login + bouton "Déconnexion" avec accent (BUG-003) | ✅ | — | BUG-003 confirmé corrigé |
| T-AUTH-07 | Accès protégé sans session | Redirection /login | ✅ | — | |
| T-AUTH-08 | Persistance session F5 | Session maintenue après reload (BUG-002) | ✅ | — | BUG-002 confirmé corrigé |
| T-AUTH-09 | Dark mode page login | Toggle fonctionne, sous-titre "à votre compte" (BUG-004) | ✅ | — | Dark login visible après logout |
| T-AUTH-10 | Page register accents | "Déjà", "Créer", "caractères" corrects (BUG-005) | ✅ | — | BUG-005 confirmé corrigé |

## 2. Chat conversationnel (Module 1)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-CHAT-01 | Accueil chat vide | Message d'accueil IA en français, invite profiling | ✅ | — | "Bienvenue sur ESG Mefali" en FR |
| T-CHAT-02 | Envoi message texte simple | Réponse IA streamée en français | ⚠️ | HIGH | FR OK mais caractères chinois "基本信息" → BUG-V2-001 |
| T-CHAT-03 | Streaming token SSE | Tokens progressifs visibles (pas de bloc final) | ✅ | — | Streaming progressif confirmé |
| T-CHAT-04 | Profiling onboarding | "AgriVert Sarl, Agriculture, 15 employés, Sénégal" → profil créé, réponse 100% FR (BUG-006 + BUG-011) | ⚠️ | HIGH | Secteur sauvegardé (outil), mais IA envoie message vide après widget → BUG-V2-002 |
| T-CHAT-05 | Historique conversations | 3 messages → F5 → historique restauré intégral | ✅ | — | Accessible via bouton "Historique des conversations" |
| T-CHAT-06 | Nouvelle conversation | Historique archivé, chat vidé | ✅ | — | "+ Nouvelle conversation" présent |
| T-CHAT-07 | Basculer entre conversations | Contenu correct restauré, pas de mélange | ✅ | — | |
| T-CHAT-08 | Widget interactif QCU | Widget radio affiché, sélection → soumission → réponse IA | ⚠️ | HIGH | Widget affiché et soumis OK, mais pas de réponse IA après → BUG-V2-002 |
| T-CHAT-09 | Widget interactif QCM | Widget checkboxes, sélection multiple → soumission | ⬜ | — | Bloqué par BUG-V2-002 |
| T-CHAT-10 | Widget "Répondre autrement" | Widget masqué, input débloqué, IA accepte réponse libre | ✅ | — | Bouton "Repondre autrement" visible |
| T-CHAT-11 | Verrouillage input widget | Input texte désactivé pendant widget pending | ✅ | — | Textbox absente pendant widget actif |
| T-CHAT-12 | Widget avec justification | Textarea visible, max 400 caractères enforcement | ⬜ | — | Non testé |
| T-CHAT-13 | Tool call indicator | Indicateur "Recherche en cours…" en français | ⚠️ | LOW | Notification "Profil mis à jour" visible, pas de "Recherche en cours..." |
| T-CHAT-14 | Changement de module | Après profiling → "évalue mon ESG" → routing ESG | ⬜ | — | Bloqué par BUG-V2-002 |
| T-CHAT-15 | Continuation module | Reste dans module ESG entre les tours | ⬜ | — | Non testé |
| T-CHAT-16 | Reprise module interrompu | Reprise exacte où laissé (active_module persisté) | ⬜ | — | Non testé |
| T-CHAT-17 | Style concis post-onboarding | Réponses courtes, pas de listes à rallonge | ⬜ | — | Bloqué par BUG-V2-002 |
| T-CHAT-18 | Accents français input | "é è à ç ù" saisis et affichés correctement | ✅ | — | |
| T-CHAT-19 | Markdown rendu IA | Listes, gras, code rendus proprement | ⬜ | — | Non testé (réponses IA vides) |
| T-CHAT-20 | Dark mode chat | Bulles user/IA, widgets, toolcall indicator tous dark | ✅ | — | |

## 3. Profil entreprise

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-PROFILE-01 | Consulter profil | Données entreprise affichées, labels accentués (BUG-007b) | ✅ | — | BUG-007b confirmé corrigé ; accents OK sur tous labels |
| T-PROFILE-02 | Modifier champ inline ✓ | Valeur persistée après F5 (BUG-007) | ❌ | HIGH | Bouton ✓ ne sauvegarde pas (API PATCH échoue silencieusement) → BUG-V2-007 |
| T-PROFILE-03 | Validation champs requis | Erreur validation si nom vide | ⬜ | — | Non testé |
| T-PROFILE-04 | Dark mode profil | Formulaire stylé dark complet | ✅ | — | |

## 4. Module ESG

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-ESG-01 | Démarrer évaluation ESG | Routing esg_scoring_node, réponse 100% FR (DEF-BUG-011-1) | ⬜ | — | Bloqué par BUG-V2-002 |
| T-ESG-02 | Répondre critères E | Sauvegarde critères ESG, progress affiché | ⬜ | — | Non testé |
| T-ESG-03 | Répondre critères S | Sauvegarde + progress | ⬜ | — | Non testé |
| T-ESG-04 | Répondre critères G | Sauvegarde + progress | ⬜ | — | Non testé |
| T-ESG-05 | Finalisation scoring | Score /100 calculé, redirection /esg/results | ⬜ | — | Non testé |
| T-ESG-06 | Page résultats ESG | Donut/barres Chart.js, scores E/S/G + global | ⬜ | — | Non testé |
| T-ESG-07 | Benchmark sectoriel | Benchmark secteur affiché (ou fallback) | ⬜ | — | Non testé |
| T-ESG-08 | Historique évaluations | Liste évaluations passées sur /esg | ✅ | — | Page /esg charge, état vide correct, sans crash |
| T-ESG-09 | Reprise évaluation interrompue | Chat propose reprendre | ⬜ | — | Non testé |
| T-ESG-11 | Dark mode page ESG | Charts + cards stylés dark | ⬜ | — | Non testé (pas de données) |
| T-ESG-12 | Accents labels critères | Aucun accent manquant | ❌ | MEDIUM | "Evaluation", "Demarrez", "criteres" sans accents → BUG-V2-005 |

## 5. Module Carbone

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-CARBON-01 | Démarrer bilan carbone | Routing carbon_node, questionnaire énergie, réponse FR (DEF-BUG-011-1) | ⬜ | — | Bloqué par BUG-V2-002 |
| T-CARBON-02 | Catégorie énergie | Calcul tCO2e progressif | ⬜ | — | Non testé |
| T-CARBON-03 | Catégorie transport | Calcul cumulé | ⬜ | — | Non testé |
| T-CARBON-04 | Catégorie déchets | Calcul cumulé | ⬜ | — | Non testé |
| T-CARBON-06 | Finalisation bilan | Total tCO2e, redirection /carbon/results | ⬜ | — | Non testé |
| T-CARBON-07 | Page résultats carbone | Donut, barres, équivalences FCFA | ⬜ | — | Non testé |
| T-CARBON-08 | Équivalences parlantes | Style "X voitures/an" en français | ⬜ | — | Non testé |
| T-CARBON-09 | Plan de réduction | Liste actions réduction affichée | ⬜ | — | Non testé |
| T-CARBON-10 | Benchmark sectoriel | Benchmark Afrique Ouest (ou fallback) | ⬜ | — | Non testé |
| T-CARBON-12 | Contrainte unicité année | "bilan existe déjà" si même année | ⬜ | — | Non testé |
| T-CARBON-13 | Reprise bilan interrompu | Reprise questionnaire | ⬜ | — | Non testé |
| T-CARBON-14 | Dark mode carbon | Charts + cards stylés dark | ⬜ | — | Non testé (pas de données) |
| T-CARBON-15 | Liste bilans | /carbon charge, état vide correct | ✅ | — | Page charge, "Aucun bilan carbone" correct |

## 6. Module Financement

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-FIN-01 | Liste fonds | ≥12 fonds réels affichés sans blocage ESG (BUG-008 + BUG-009) | ❌ | CRITICAL | ESG gate active sur tous les onglets → BUG-V2-006 (régression BUG-008) |
| T-FIN-02 | Filtre secteur | Liste restreinte cohérente | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-03 | Filtre montant | Liste restreinte cohérente | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-04 | Filtre accès | Direct vs intermédiaire | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-05 | Filtre statut | Ouvert/fermé | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-06 | Détail fonds | Page /financing/[id] avec détails | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-07 | Annuaire intermédiaires | ≥14 intermédiaires avec coordonnées | ❌ | CRITICAL | ESG gate active sur onglet Intermédiaires aussi → BUG-V2-006 |
| T-FIN-08 | Filtre pays intermédiaire | Filtre Sénégal fonctionne | ⬜ | — | Bloqué par BUG-V2-006 |
| T-FIN-09 | Matching chat | Routing financing_node, réponse FR (DEF-BUG-011-1) | ⬜ | — | Bloqué par BUG-V2-002 |
| T-FIN-13 | Dark mode financing | Cards + filtres + détail dark | ⬜ | — | Non testé (page non accessible) |

## 7. Module Applications

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-APP-01 | Liste applications | /applications charge, état vide correct | ✅ | — | "Aucun dossier" sans crash |
| T-APP-02 | Créer application via chat | Tool create_fund_application déclenché | ⬜ | — | Bloqué par BUG-V2-002 |
| T-APP-05 | Dark mode application | Éditeur + cards dark | ⬜ | — | Non testé |

## 8. Module Credit Score

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-CREDIT-01 | Page credit-score | /credit-score charge, état vide correct | ✅ | — | "Pas encore de score" sans crash |
| T-CREDIT-02 | Démarrer scoring chat | Routing credit_node, réponse FR (DEF-BUG-011-1) | ⬜ | — | Bloqué par BUG-V2-002 |
| T-CREDIT-03 | Score hybride | Score solvabilité + impact calculé | ⬜ | — | Non testé |
| T-CREDIT-04 | Dark mode credit | Éléments dark | ⬜ | — | Non testé |

## 9. Module Plan d'Action

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-PLAN-01 | Page plan d'action | /action-plan charge, état vide + bouton générer | ✅ | — | "Aucun plan d'action" + filtre 12 mois visible |
| T-PLAN-02 | Générer plan | 10-15 actions multi-catégories, réponse FR (DEF-BUG-011-1) | ⬜ | — | Bloqué par BUG-V2-002 |
| T-PLAN-03 | Filtre environment | Actions filtrées | ⬜ | — | Non testé |
| T-PLAN-05 | Barre progression globale | Marquer action → progression MAJ | ⬜ | — | Non testé |
| T-PLAN-10 | Dark mode plan | Timeline + cards dark | ⬜ | — | Non testé |

## 10. Dashboard

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-DASH-01 | Accueil dashboard | 4 cartes ESG/carbone/credit/financement | ✅ | — | |
| T-DASH-02 | Carte ESG | Redirection /esg | ✅ | — | "Démarrer l'évaluation →" présent |
| T-DASH-03 | Carte carbone | Redirection /carbon | ✅ | — | "Calculer mon empreinte →" présent |
| T-DASH-06 | Badges gamification | first_carbon + esg_above_50 après données | ⬜ | — | Non testé (pas de données) |
| T-DASH-08 | État vide nouveau compte | Pas de crash | ✅ | — | |
| T-DASH-09 | Dark mode dashboard | 4 cartes + badges dark | ✅ | — | |

## 11. Reports

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-REPORT-01 | Liste rapports | /reports charge, état vide correct | ✅ | — | "Aucun rapport généré" sans crash |
| T-REPORT-02 | Générer rapport ESG | PDF généré, notification chat | ⬜ | — | Non testé (nécessite évaluation ESG) |
| T-REPORT-03 | Prévisualiser rapport | PDF inline 9 sections | ⬜ | — | Non testé |
| T-REPORT-04 | Télécharger rapport | PDF téléchargé, nom clair | ⬜ | — | Non testé |
| T-REPORT-09 | Dark mode reports | Liste + preview dark | ⬜ | — | Non testé |

## 12. Documents

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-DOC-01 | Liste documents | /documents charge, état vide correct | ✅ | — | |
| T-DOC-02 | État vide | "Aucun document" sans crash | ✅ | — | Zone upload visible |
| T-DOC-03 | Dark mode documents | Liste dark | ⬜ | — | Non testé |
| T-DOC-04 | Upload | — | 🚫 | — | Exclu agent-browser |

## 13. Navigation & Layout

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-NAV-01 | Menu principal | Tous liens présents | ✅ | — | Tableau de bord, Plan d'action, Évaluation ESG, Empreinte Carbone, Financement, Crédit Vert, Rapports, Documents, Profil |
| T-NAV-05 | Toggle dark mode | Persiste localStorage | ✅ | — | |
| T-NAV-06 | Persistance dark mode reload | Dark conservé après F5 | ✅ | — | |
| T-NAV-07 | Cohérence dark tous modules | Aucune page fond blanc résiduel | ✅ | — | Sauf page 404 (sans layout) |

## 14. Composants UI & Performance

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-UI-01 | ui/Button variantes | Contrastes AA visibles | ⬜ | — | Non testé |
| T-UI-09 | ui/Tabs financing | Clic tab bascule contenu | ✅ | — | Tabs présentes (Recommandations / Tous les fonds / Intermédiaires) |
| T-UI-11 | ui/EsgIcon | Icônes rendues correctement | ✅ | — | Icônes ESG, carbone visibles dans dashboard |
| T-PERF-01 | Console erreurs JS | Aucune erreur rouge | ✅ | — | Warning "[Vue Router warn]: No match for /chat" (route inexistante, non bloquant) |
| T-PERF-06 | Page 404 | "Page introuvable" FR + dark mode (BUG-010) | ⚠️ | LOW | "Page introuvable" FR ✅ ; dark mode non appliqué (page error sans layout) |

---

## Synthèse bugs Vague 2

| ID bug | Test source | Sévérité | Description | Fichier(s) | Status |
|--------|-------------|----------|-------------|------------|--------|
| BUG-V2-001 | T-CHAT-02 | HIGH | Caractères chinois "基本信息" dans réponse chat_node (régression BUG-011) | backend/app/graph/nodes.py : chat_node | FIXED — spec-bug-v2-001-002-chat-regressions.md (LANGUAGE_INSTRUCTION appendue en fin de prompt) |
| BUG-V2-002 | T-CHAT-04/08 | HIGH | IA envoie message vide après soumission widget — tool call s'exécute mais aucun texte de suivi n'est généré | backend/app/graph/nodes.py, frontend/useChat.ts | FIXED — spec-bug-v2-001-002-chat-regressions.md (puce « jamais de réponse vide après tool call » ajoutée à tool_instructions) |
| BUG-V2-003 | T-CHAT-02→08 | MEDIUM | Chat ne scroll pas automatiquement vers le bas après chaque nouvelle réponse | frontend/app/components/Chat*.vue | OPEN — non reproduit en inspection code : logique scroll en place (FloatingChatWidget lignes 434-475, watchers `messages.length` + `streamingContent`). A re-tester côté QA ; si reproduit, DEFERRED vers investigation ciblée (peut-être spécifique à un événement post-widget) |
| BUG-V2-004 | T-PROFILE-01 | LOW | Texte italic profil sans accents "Completez...personnalises" | frontend/app/pages/profile.vue | FIXED — déjà corrigé en amont (ligne 35 : « Complétez votre profil pour recevoir des conseils ESG personnalisés. ») |
| BUG-V2-005 | T-ESG-12, T-FIN-01, T-CREDIT-01, T-REPORT-01 | MEDIUM | Accents manquants sur multiples pages : "Evaluation" → "Évaluation", "Demarrez" → "Démarrez", "criteres" → "critères", "genere" → "généré", "solvabilite" → "solvabilité", "Realiser" → "Réaliser" | frontend/app/pages/esg/{index,results}.vue, financing/index.vue, credit-score/index.vue, reports/index.vue, carbon/{index,results}.vue | FIXED — spec-bug-v2-batch-regressions-ux.md (batch accents 7 pages) |
| BUG-V2-006 | T-FIN-01/07 | CRITICAL | ESG gate régression — onglets "Tous les fonds" et "Intermédiaires" bloqués par gate ESG (BUG-008 non appliqué) | frontend/app/pages/financing/index.vue | FIXED — spec-bug-v2-batch-regressions-ux.md (scope des 3 templates erreurs à `activeTab === 'recommendations'`) |
| BUG-V2-007 | T-PROFILE-02 | HIGH | Profil inline edit ne sauvegarde pas — bouton ✓ n'appelle pas le PATCH API correctement (spinbutton) | frontend/app/components/profile/ProfileField.vue | FIXED — spec-bug-v2-batch-regressions-ux.md (ajout `type="button"` explicite sur les 3 boutons ✎/✓/✕ + `aria-label` ; évite tout submit implicite d'un form ancêtre) |
| DEF-BUG-V2-001-1 | T-ESG/CARBON/FIN/APP/CREDIT/PLAN-xx | HIGH | Rappel linguistique « RAPPEL FINAL » absent des 6 nœuds spécialistes (extension de BUG-V2-001) | backend/app/graph/nodes.py : esg/carbon/financing/credit/application/action_plan_node | FIXED — spec-bug-v2-batch-regressions-ux.md (pattern appliqué aux 6 nœuds + 8 tests statiques verts) |

## Historique exécution

| Date | Vague | Bugs ouverts | Bugs fermés |
|------|-------|--------------|-------------|
| 2026-04-23 | V1 | 12 | 0 |
| 2026-04-23 | V1 corrections | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | 7 | 0 (BUG-001→010 + DEF-BUG-011-1 confirmés) |
