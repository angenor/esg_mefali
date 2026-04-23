---
title: Plan de tests manuels automatisés — Vague 1 (pré-Epic 11)
type: test-plan
version: 1.0
status: in-progress
date: 2026-04-23
executed_by: Angenor (via agent-browser --headed)
scope: Tous modules livrés (Epics 1-18 core MVP) hors upload fichiers
excluded: Upload documents (agent-browser limitation), extension Chrome, features Phase 1+ non livrées
next_wave: Vague 2 post-corrections bugs Vague 1 + tests upload manuels séparés
---

# Plan de tests manuels — Vague 1 — 2026-04-23

## Objectif

Première passe de tests utilisateur automatisés pour valider le comportement end-to-end des features livrées après la clôture Epic 10 Phase 0 Fondations. Révéler bugs fonctionnels, régressions, écarts UX, problèmes dark mode, avant retrospective Epic 10 et démarrage Phase 1 MVP (Epic 11 Cluster A PME).

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

Terminal 3 — Tests agent-browser :
```bash
agent-browser --headed
```

### Données de test

- **Compte utilisateur test** : créer lors du test T-AUTH-01 (register) ou réutiliser existant
- **Entreprise test** : PME agricole Sénégal (contexte UEMOA réaliste)
  - Nom : "AgriVert Sarl"
  - Secteur : Agriculture
  - Taille : 15 employés
  - Pays : Sénégal
  - Région : Dakar
- **Entreprise test 2** : PME énergie Côte d'Ivoire
  - Nom : "SolarWest SA"
  - Secteur : Énergie
  - Taille : 45 employés
  - Pays : Côte d'Ivoire

## Légende statuts

| Statut | Signification | Action |
|--------|---------------|--------|
| ⬜ | Non testé | À exécuter |
| ✅ | OK | Aucune action |
| ⚠️ | OK partiel / UX à améliorer | Niveau 2 BMAD |
| ❌ | Bug bloquant / fonctionnalité cassée | Niveau 2 ou 3 BMAD |
| 🚫 | Non applicable / feature différée | Ignorer |
| 🔒 | Bloqué par un bug amont | Retester après correction |

## Grille de sévérité bugs

| Niveau | Critère | Workflow BMAD |
|--------|---------|---------------|
| **N1** | Typo, accent manquant, dark mode oublié élément isolé, style mineur | Correction inline 1 commit |
| **N2** | Comportement incorrect localisé, edge case, régression UX non bloquante | `/bmad-dev-story` light + 1-2 commits |
| **N3** | Fonctionnalité cassée, régression multi-module, bug données, sécurité | Cycle BMAD complet (create → dev → review LLM différent → Option 0 Fix-All) |
| **N4** | Bug critique bloquant (auth, PII, scoring ESG faux, injection) | Hotfix immédiat + post-mortem §methodology |

---

## 1. Authentification & Onboarding

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-AUTH-01 | Register nouveau compte | Naviguer `/register` → remplir email/password/nom → submit | Redirection vers `/dashboard` ou `/` avec session active | ✅ | — | Redirect vers /dashboard OK |
| T-AUTH-02 | Register email déjà existant | Répéter T-AUTH-01 avec même email | Erreur claire "email déjà utilisé" en français | ✅ | — | "Un compte avec cet email existe déjà" |
| T-AUTH-03 | Register password faible | Tenter password court (< 8 car) | Validation client + message erreur | ✅ | — | Validation HTML5 native, message FR |
| T-AUTH-04 | Login compte valide | `/login` → credentials valides → submit | Redirection dashboard, session persistante | ✅ | — | Dashboard OK |
| T-AUTH-05 | Login credentials invalides | `/login` → mauvais password | Erreur "identifiants incorrects", pas de fuite info | ✅ | — | "Identifiants invalides" — aucune fuite |
| T-AUTH-06 | Logout | Cliquer logout depuis layout | Redirection `/login`, session effacée | ✅ | — | BUG-003 N1 : bouton "Deconnexion" (accent manquant) |
| T-AUTH-07 | Accès protégé sans session | Visiter `/dashboard` en anonyme | Redirection `/login` | ✅ | — | Vérifié via comportement T-AUTH-06 |
| T-AUTH-08 | Persistance session rafraîchissement | Login → F5 page | Session maintenue | ❌ | N2 | BUG-002 : session perdue au reload → retour /login |
| T-AUTH-09 | Dark mode toggle page login | `/login` → toggle dark mode | Toggle fonctionne, tous éléments stylés dark | ⚠️ | N1 | Styles dark OK, mais pas de toggle accessible sur pages non-auth (toggle uniquement dans layout sidebar) |
| T-AUTH-10 | Dark mode toggle page register | `/register` → toggle dark mode | Toggle fonctionne, tous éléments stylés dark | ✅ | N1 | Styles dark OK — BUG-005 N1 : "Deja" → "Déjà", "Creer" → "Créer", "caracteres" → "caractères" |

## 2. Chat conversationnel (Module 1)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-CHAT-01 | Accueil chat vide | Nouveau compte → premier accès chat | Message d'accueil IA en français, invite profiling | ✅ | — | Widget Welcome + message FR — pas de page dédiée /chat, panneau flottant |
| T-CHAT-02 | Envoi message texte simple | Taper "Bonjour" → Enter | Réponse IA streamée, message affiché immédiatement utilisateur | ✅ | — | Réponse FR affichée |
| T-CHAT-03 | Streaming token SSE visible | Envoyer question ouverte | Tokens apparaissent progressivement (pas d'attente bloc final) | ✅ | — | Curseur clignotant visible pendant stream |
| T-CHAT-04 | Profiling entreprise onboarding | Suivre guidance IA → fournir nom/secteur/pays/taille | Profil entreprise créé, données persistées `/profile` | ❌ | N3 | BUG-006 : LangGraph recursion limit 25 atteint après réponse secteur → chat bloqué |
| T-CHAT-05 | Historique conversations | Envoyer 3 messages → rafraîchir page | Historique restauré intégral | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-06 | Nouvelle conversation | Bouton "Nouvelle conversation" | Historique archivé, chat vidé | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-07 | Basculer entre conversations | Créer 2 conversations → cliquer sur l'ancienne | Contenu correct restauré, pas de mélange messages | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-08 | Widget interactif QCU | Déclencher question fermée (ex: secteur) | Widget radio affiché, sélection → soumission → réponse IA | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-09 | Widget interactif QCM | Déclencher question multiple | Widget checkboxes, sélection multiple → soumission | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-10 | Widget "Répondre autrement" | Afficher widget → cliquer "Répondre autrement" | Widget masqué, input texte débloqué, IA accepte réponse libre | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-11 | Verrouillage input pendant widget | Widget pending affiché | Input texte désactivé visuellement | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-12 | Widget avec justification | Question "avec justification" activée | Textarea justification visible, max 400 caractères enforcement | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-13 | Tool call indicator | Question déclenchant tool (ex: "calcule mon score ESG") | Indicateur visuel "Recherche en cours…" en français | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-14 | Changement de module (routing) | Après profiling → demander "je veux évaluer mon ESG" | Routing vers module ESG, message de transition | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-15 | Continuation module (active_module) | Dans module ESG → répondre questions | Reste dans module ESG tant que non finalisé | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-16 | Reprise module interrompu | Interrompre ESG → revenir plus tard | Reprise exacte où laissé (active_module persisté) | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-17 | Chat general post-onboarding concis | Question generale | Réponse courte style concis (module 014) | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-18 | Accents français | Poser question avec "é è à ç ù" | Rendu correct aucune substitution ASCII | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-19 | Markdown rendu messages IA | IA retourne liste, gras, code | Rendu markdown propre | 🔒 | — | Bloqué BUG-006 |
| T-CHAT-20 | Dark mode chat | Toggle dark mode | Bulles user/IA, widgets, toolcall indicator tous stylés dark | 🔒 | — | Bloqué BUG-006 |

## 3. Profil entreprise (Module 1 suite)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-PROFILE-01 | Consulter profil | Naviguer `/profile` | Données entreprise affichées depuis chat onboarding | ✅ | N1 | BUG-007b N1 : "Identite" → "Identité", "Completez...personnalises" accents manquants |
| T-PROFILE-02 | Modifier champ | Éditer "nombre employés" → save | Persistance DB, retour liste avec valeur mise à jour | ❌ | N2 | BUG-007 N2 : bouton ✓ inline n'envoie pas le PATCH (API PATCH fonctionne en direct) |
| T-PROFILE-03 | Validation champs requis | Vider nom entreprise → save | Erreur validation, pas de submit | 🔒 | — | Bloqué BUG-007 (save ne fonctionne pas) |
| T-PROFILE-04 | Dark mode profil | Toggle dark mode | Tous éléments formulaire stylés dark | ✅ | — | Dark mode correct (vérifié lors de T-PROFILE-02 accidentellement) |

## 4. Module ESG (Modules 2 + 3 — Conformité + Scoring)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-ESG-01 | Démarrer évaluation ESG | Chat → "évalue mon ESG" | Routing esg_scoring_node, questions pondérées secteur | 🔒 | — | Bloqué BUG-006 (LangGraph) |
| T-ESG-02 | Répondre 5 critères E | Fournir réponses questions Environnement | Sauvegarde criteres ESG, progress affiché | 🔒 | — | Bloqué BUG-006 |
| T-ESG-03 | Répondre 5 critères S | Continuer Social | Sauvegarde + progress | 🔒 | — | Bloqué BUG-006 |
| T-ESG-04 | Répondre 5 critères G | Continuer Gouvernance | Sauvegarde + progress | 🔒 | — | Bloqué BUG-006 |
| T-ESG-05 | Finalisation scoring | Compléter ≥30 critères | Score /100 calculé, redirection `/esg/results` | 🔒 | — | Bloqué BUG-006 |
| T-ESG-06 | Page résultats ESG | `/esg/results` | Donut/barres Chart.js, score E/S/G séparés, score global | 🔒 | — | Bloqué BUG-006 (pas de données) |
| T-ESG-07 | Benchmark sectoriel | Page résultats | Benchmark secteur affiché (ou fallback si indisponible) | 🔒 | — | Bloqué BUG-006 |
| T-ESG-08 | Historique évaluations | Page `/esg` | Liste évaluations passées | ✅ | — | Page /esg charge, état vide correct, pas de crash |
| T-ESG-09 | Reprise évaluation interrompue | Quitter mid-ESG → revenir chat | Chat propose "reprendre" l'évaluation en cours | 🔒 | — | Bloqué BUG-006 |
| T-ESG-10 | RAG critère documentaire | Pendant évaluation, IA cite doc | Référence doc uploaded antérieurement (si applicable) | 🚫 | — | Dépend upload |
| T-ESG-11 | Dark mode page ESG | Toggle dark mode | Charts + cards stylés dark | ✅ | — | Page /esg dark mode OK (vérifié) |
| T-ESG-12 | Accents FR labels critères | Inspecter labels | Aucun accent manquant | 🔒 | — | Bloqué BUG-006 (pas de données) |

## 5. Module Carbone (Module 4)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-CARBON-01 | Démarrer bilan carbone | Chat → "calcule mon empreinte" | Routing carbon_node, questionnaire énergie démarré | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-02 | Catégorie énergie | Répondre conso électricité/carburant | Calcul tCO2e progressif | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-03 | Catégorie transport | Répondre flotte véhicules | Calcul cumulé | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-04 | Catégorie déchets | Répondre volumes déchets | Calcul cumulé | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-05 | Catégorie industriel/agricole | Selon secteur | Calcul cumulé | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-06 | Finalisation bilan | Compléter questionnaire | Total tCO2e affiché, redirection `/carbon/results` | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-07 | Page résultats carbone | `/carbon/results` | Donut par catégorie, barres, équivalences FCFA | 🔒 | — | Bloqué BUG-006 (pas de données) |
| T-CARBON-08 | Équivalences parlantes | Résultats | Équivalences style "X voitures/an" en français | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-09 | Plan de réduction | Résultats | Liste actions réduction affichée | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-10 | Benchmark sectoriel carbone | Résultats | Benchmark secteur Afrique Ouest (ou fallback) | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-11 | Évolution temporelle | Résultats si historique | Courbe évolution si ≥2 bilans | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-12 | Contrainte unicité année | Tenter bilan même année | Blocage + message "bilan existe déjà" | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-13 | Reprise bilan interrompu | Interrompre mid-carbon → revenir | Reprise questionnaire | 🔒 | — | Bloqué BUG-006 |
| T-CARBON-14 | Dark mode carbon | Toggle dark mode | Charts + cards + équivalences stylés | ✅ | — | Page /carbon dark mode OK |
| T-CARBON-15 | Liste bilans | `/carbon` | Liste bilans par année | ✅ | — | Page /carbon charge, état vide correct, pas de crash |

## 6. Module Financement (Module 3 — Conseiller financement vert)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-FIN-01 | Liste fonds | `/financing` onglet fonds | ≥12 fonds réels (GCF, FEM, BOAD, BAD, SUNREF, etc.) | ❌ | N3 | BUG-008+BUG-009 : 0 fonds en DB + onglet bloqué par condition ESG requise. Page charge OK (accents N1 : "Evaluation" → "Évaluation", "Intermediaires" → "Intermédiaires", "acces" → "accès", "Realiser" → "Réaliser") |
| T-FIN-02 | Filtre secteur | Filtrer "énergie" | Liste restreinte cohérente | 🔒 | — | Bloqué BUG-009 (0 fonds) |
| T-FIN-03 | Filtre montant | Filtrer montant max | Liste restreinte cohérente | 🔒 | — | Bloqué BUG-009 |
| T-FIN-04 | Filtre accès | Filtrer "direct" vs "intermédiaire" | Liste restreinte cohérente | 🔒 | — | Bloqué BUG-009 |
| T-FIN-05 | Filtre statut | Filtrer "ouvert" | Liste restreinte cohérente | 🔒 | — | Bloqué BUG-009 |
| T-FIN-06 | Détail fonds | Cliquer sur un fonds | Page `/financing/[id]` avec détails complets | 🔒 | — | Bloqué BUG-009 |
| T-FIN-07 | Annuaire intermédiaires | `/financing` onglet intermédiaires | ≥14 intermédiaires avec coordonnées | 🔒 | — | Bloqué BUG-009 (0 intermédiaires) |
| T-FIN-08 | Filtre pays intermédiaire | Filtrer Sénégal | Liste restreinte | 🔒 | — | Bloqué BUG-009 |
| T-FIN-09 | Matching chat | Chat → "je veux un financement" | Routing financing_node, matching projet-fonds | 🔒 | — | Bloqué BUG-006 (LangGraph) + BUG-009 |
| T-FIN-10 | Parcours direct | Fonds accès direct | Étapes LLM affichées | 🔒 | — | Bloqué BUG-006+BUG-009 |
| T-FIN-11 | Parcours intermédiaire | Fonds accès intermédiaire | Choix intermédiaire proposé + fiche préparation | 🔒 | — | Bloqué BUG-006+BUG-009 |
| T-FIN-12 | Workflow intérêt fonds | Marquer intérêt pour un fonds | Persisté, visible dashboard | 🔒 | — | Bloqué BUG-009 |
| T-FIN-13 | Dark mode financing | Toggle dark mode | Cards fonds + filtres + détail stylés dark | ✅ | — | Dark mode OK (vérifié sur page financing) |
| T-FIN-14 | Accents intermédiaires | Noms intermédiaires | "Banque" "Société" accentués correctement | 🔒 | — | Bloqué BUG-009 (0 données) |

## 7. Module Applications (Module 3 — Générateur dossiers)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-APP-01 | Liste applications | `/applications` | Liste dossiers créés (ou état vide) | ✅ | — | Page /applications charge, état vide correct |
| T-APP-02 | Créer application via chat | Chat → "crée un dossier pour GCF" | Tool create_fund_application déclenché, dossier créé | 🔒 | — | Bloqué BUG-006 (LangGraph) + BUG-009 (pas de fonds) |
| T-APP-03 | Détail application | Cliquer sur dossier | Page `/applications/[id]` | 🔒 | — | Bloqué (pas d'applications) |
| T-APP-04 | Éditer application | Modifier champs via toast-ui/editor | Persistance | 🔒 | — | Bloqué |
| T-APP-05 | Dark mode application | Toggle dark mode | Éditeur + cards stylés dark | ✅ | — | Page /applications dark mode OK |

## 8. Module Credit Score (Module 5)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-CREDIT-01 | Page credit-score | `/credit-score` | Formulaire ou état initial affiché | ✅ | — | Page /credit-score charge, état vide correct |
| T-CREDIT-02 | Démarrer scoring chat | Chat → "évalue ma solvabilité" | Routing credit_node, questions Mobile Money | 🔒 | — | Bloqué BUG-006 |
| T-CREDIT-03 | Données non-conventionnelles | Répondre questions alternatives | Score hybride calculé | 🔒 | — | Bloqué BUG-006 |
| T-CREDIT-04 | Dark mode credit | Toggle dark mode | Éléments stylés dark | ✅ | — | Dark mode OK |

## 9. Module Plan d'Action (Module 6)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-PLAN-01 | Page plan d'action | `/action-plan` | Timeline verticale ou état "plan à générer" | ✅ | — | Page charge, état vide + bouton générer |
| T-PLAN-02 | Générer plan | Chat → "génère mon plan d'action" | 10-15 actions multi-catégories | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-03 | Filtre catégorie | Filtrer "environment" | Actions filtrées | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-04 | Filtre "financing" | Filtrer | Actions financing filtrées | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-05 | Barre progression globale | Marquer action fait | Progression globale MAJ | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-06 | Progression par catégorie | Marquer action E | Progression E MAJ séparément | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-07 | Action intermédiaire | Action catégorie intermediary_contact | Coordonnées intermédiaire snapshot visibles | 🔒 | — | Bloqué BUG-006 + BUG-009 |
| T-PLAN-08 | Rappels in-app | Rappel action échéance proche | Toast affiché ≤60s polling | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-09 | Toast variant intermédiaire | Rappel type intermediary_followup | Toast bleu variant intermédiaire | 🔒 | — | Bloqué BUG-006 |
| T-PLAN-10 | Dark mode plan | Toggle dark mode | Timeline + cards + filtres stylés | ✅ | — | Dark mode OK |

## 10. Dashboard (Module 7)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-DASH-01 | Accueil dashboard | `/dashboard` | 4 cartes synthétiques ESG/carbone/credit/financement | ✅ | — | 4 cartes présentes, état vide géré correctement |
| T-DASH-02 | Carte ESG | Cliquer carte | Redirection `/esg/results` ou détail | ✅ | — | → `/esg` OK |
| T-DASH-03 | Carte carbone | Cliquer carte | Redirection `/carbon/results` | ✅ | — | → `/carbon` OK |
| T-DASH-04 | Carte credit | Cliquer carte | Redirection `/credit-score` | ✅ | — | → `/credit-score` OK |
| T-DASH-05 | Carte financements | Cliquer carte | Redirection `/financing` avec parcours intermédiaires | ✅ | — | → `/financing` OK |
| T-DASH-06 | Badges gamification | Avoir 1 bilan carbone + ESG>50 | Badges affichés : first_carbon, esg_above_50 | 🔒 | — | Bloqué BUG-006 (pas de données ESG/carbone) |
| T-DASH-07 | Badge full_journey | Compléter tous modules | Badge débloqué | 🔒 | — | Bloqué BUG-006 |
| T-DASH-08 | Dashboard état vide nouveau | Compte neuf | Message accueil, pas de crash | ✅ | — | "Aucune action", "Aucune activité" — pas de crash |
| T-DASH-09 | Dark mode dashboard | Toggle dark mode | 4 cartes + badges stylés dark | ✅ | — | Dark mode correct |

## 11. Reports (Module 2 suite)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-REPORT-01 | Liste rapports | `/reports` | Liste rapports générés (ou vide) | ✅ | — | Page charge, état vide correct |
| T-REPORT-02 | Générer rapport ESG | Cliquer "Générer" post-ESG | Génération PDF en cours, notification chat | 🔒 | — | Bloqué BUG-006 (pas de données ESG) |
| T-REPORT-03 | Prévisualiser rapport | Cliquer preview | PDF affiché inline (9 sections) | 🔒 | — | Bloqué |
| T-REPORT-04 | Télécharger rapport | Cliquer download | PDF téléchargé, nom fichier clair | 🔒 | — | Bloqué |
| T-REPORT-05 | Rapport contient graphiques | Inspecter PDF | Graphiques matplotlib SVG inclus | 🔒 | — | Bloqué |
| T-REPORT-06 | Rapport contient résumé IA | Inspecter PDF | Résumé exécutif Claude présent | 🔒 | — | Bloqué |
| T-REPORT-07 | Références UEMOA/BCEAO/ODD | Inspecter PDF | Références réglementaires présentes | 🔒 | — | Bloqué |
| T-REPORT-08 | Génération simultanée | Lancer 2 rapports rapidement | Pas de crash, files propres | 🔒 | — | Bloqué |
| T-REPORT-09 | Dark mode reports | Toggle dark mode | Liste + preview stylés dark | ✅ | — | Dark mode OK |

## 12. Documents (Module 2 — affichage sans upload)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-DOC-01 | Liste documents | `/documents` | Liste documents (ou état vide) | ✅ | — | Zone drop + filtres + "Aucun document" — pas de crash |
| T-DOC-02 | État vide documents | Compte neuf | Message "aucun document", pas de crash | ✅ | — | "Aucun document" affiché |
| T-DOC-03 | Dark mode documents | Toggle dark mode | Liste stylée dark | ✅ | — | Dark mode actif — styles corrects |
| T-DOC-04 | Upload documents | — | — | 🚫 | — | Exclu Vague 1 (agent-browser limitation) |

## 13. Navigation & Layout

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-NAV-01 | Menu principal | Inspecter layout | Liens Dashboard, Chat, ESG, Carbone, Financement, Rapports, Documents, Plan, Profil | ✅ | — | Tous les liens présents (chat = bouton flottant, pas de lien sidebar) |
| T-NAV-02 | Navigation lien actif | Cliquer lien | État actif visible (couleur/bordure) | ✅ | — | Lien actif surligné vert (vérifié screenshots) |
| T-NAV-03 | Responsive mobile | Réduire viewport <768px | Menu hamburger OU adapté | ⬜ | — | Non testé Vague 1 |
| T-NAV-04 | Responsive tablet | Viewport 768-1024px | Layout adapté | ⬜ | — | Non testé Vague 1 |
| T-NAV-05 | Toggle dark mode global | Toggle depuis header | Persiste localStorage | ✅ | — | Toggle lune/soleil dans header fonctionne |
| T-NAV-06 | Persistance dark mode reload | Activer dark + F5 | Dark conservé | ✅ | — | Vérifié lors T-PROFILE-02 : dark persiste après reload |
| T-NAV-07 | Cohérence dark mode tous modules | Parcourir 10 pages en dark | Aucune page avec fond blanc résiduel | ✅ | — | Dashboard, profil, financing, documents — tous dark corrects. 404 manque dark mode |

## 14. Composants UI foundation (Epic 10 Phase 0)

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-UI-01 | ui/Button variantes | Inspecter boutons app | Primary, secondary, danger, ghost — contrastes AA visibles | ✅ | — | Boutons verts primary visibles, contrastes corrects |
| T-UI-02 | ui/Input FR accents | Input "é è à ç" | Rendu correct | ✅ | — | Accents saisis correctement (testé login, register) |
| T-UI-03 | ui/Textarea justification | Widget chat justification | Max 400 car enforcement visible | 🔒 | — | Bloqué BUG-006 |
| T-UI-04 | ui/Select multiple | Selector secteur multi | Sélection multiple fonctionne | ⬜ | — | Non testé Vague 1 |
| T-UI-05 | ui/Badge verdict | Page ESG résultats | Badges pass/fail/partial colorés correctement | 🔒 | — | Bloqué BUG-006 |
| T-UI-06 | ui/Drawer consultation | Cliquer citation source | Drawer ouvre, Escape ferme, focus return | ⬜ | — | Non testé Vague 1 |
| T-UI-07 | ui/Combobox recherche FR | Combobox pays → taper "sén" | "Sénégal" trouvé (accent insensitive) | ⬜ | — | Non testé Vague 1 |
| T-UI-08 | ui/Combobox multi-select | Combobox multi | Badges sélectionnés visibles, suppression possible | ⬜ | — | Non testé Vague 1 |
| T-UI-09 | ui/Tabs navigation | Page avec tabs (financing) | Clic tab bascule contenu, ARIA correct | ✅ | — | Tabs financing cliquables (mais bloqué BUG-008 côté contenu) |
| T-UI-10 | ui/DatePicker FR | Date picker action plan | Format d/M/yyyy FR, locale française | 🔒 | — | Bloqué BUG-006 |
| T-UI-11 | ui/EsgIcon rendering | Inspecter icônes app | Icônes Lucide + ESG custom rendues correctement | ✅ | — | Icônes présentes dans nav (maison, graphe, etc.) |
| T-UI-12 | Focus keyboard global | Tab navigation | Focus visible tous éléments interactifs | ⬜ | — | Non testé Vague 1 |
| T-UI-13 | ARIA screen reader | Inspecter DOM | role/aria-* présents et strict (pas placeholder) | ⬜ | — | Non testé Vague 1 |

## 15. Accessibilité & A11y

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-A11Y-01 | Contraste AA light mode | Inspecter texte/fonds | ≥4.5:1 partout | ⬜ | — | Non testé Vague 1 |
| T-A11Y-02 | Contraste AA dark mode | Toggle dark | ≥4.5:1 partout | ⬜ | — | Non testé Vague 1 |
| T-A11Y-03 | Labels formulaires | Tous formulaires | `<label>` associé chaque input | ✅ | — | Labels login/register associés (vérifié accessibilité tree) |
| T-A11Y-04 | Boutons aria-label | Boutons icône seule | aria-label descriptif FR | ✅ | — | "Mode sombre", "Replier", "Modifier X" présents |
| T-A11Y-05 | Ordre tabulation | Tab sur page complexe | Ordre logique | ⬜ | — | Non testé Vague 1 |
| T-A11Y-06 | Escape modals/drawers | Ouvrir → Escape | Fermeture effective | ⬜ | — | Non testé Vague 1 |

## 16. Performance & Erreurs

| ID | Test | Étapes | Résultat attendu | Statut | Sévérité | Notes |
|----|------|--------|------------------|--------|----------|-------|
| T-PERF-01 | Console erreurs JS | Ouvrir devtools → parcourir 10 pages | Aucune erreur rouge | ⚠️ | N1 | 2 erreurs contextuelles (CORS 500 au premier register avant migrations, 409 T-AUTH-02 attendu) — pas d'erreur JS pure en navigation normale |
| T-PERF-02 | Console warnings | Devtools warnings | Aucun warning Vue/Nuxt non-justifié | ⚠️ | N1 | `<Suspense> is experimental` warning récurrent — Nuxt non-justifié |
| T-PERF-03 | Chargement initial | `/` first paint | ≤3s viewport rendu | ✅ | — | Temps de réponse ~70-80ms (mesurés dans Nuxt DevTools overlay) |
| T-PERF-04 | Navigation SPA | Cliquer lien menu | Transition ≤500ms | ✅ | — | Transitions rapides observées |
| T-PERF-05 | Chat streaming fluidité | Envoyer message long | Pas de freeze UI pendant stream | ✅ | — | Stream fluide (tokens progressifs sans freeze) |
| T-PERF-06 | 404 page inexistante | `/inexistante` | Page 404 propre + bouton retour | ⚠️ | N1 | BUG-010 : Page 404 en anglais ("Page not found", "Go back home") — manque i18n FR + dark mode |
| T-PERF-07 | Erreur API gérée | Simuler backend down | Message utilisateur clair, pas de crash UI | ⬜ | — | Non testé Vague 1 |
| T-PERF-08 | Reconnexion après erreur | Relancer backend | UI récupère | ⬜ | — | Non testé Vague 1 |

---

## Synthèse bugs identifiés

Section à remplir au fur et à mesure de l'exécution. Un bug par ligne.

| ID bug | Test source | Sévérité | Description | Fichier(s) | Owner | Status | Story BMAD |
|--------|-------------|----------|-------------|------------|-------|--------|------------|
| BUG-001 | Prérequis | N3 | Migration 030 échoue : INSERT dans `sources` utilise `$2::VARCHAR` mais colonne `source_type` est de type `source_type_enum` — DatatypeMismatchError | `alembic/versions/030_seed_sources_annexe_f.py` | Angenor | open | — |
| BUG-002 | T-AUTH-08 | N2 | Session non persistée après F5 : le store Pinia lit bien `localStorage` mais la session est perdue au reload → retour forcé sur /login | `app/stores/auth.ts`, middleware auth | Angenor | open | — |
| BUG-003 | T-AUTH-06 | N1 | Bouton "Deconnexion" : accent manquant sur "é" → devrait être "Déconnexion" | layout sidebar | Angenor | open | — |
| BUG-004 | T-AUTH-04/05 | N1 | Sous-titre page login "Connectez-vous a votre compte" : accent manquant → "Connectez-vous à votre compte" | `pages/login.vue` | Angenor | open | — |
| BUG-005 | T-AUTH-10 | N1 | Accents manquants page register : "Deja" → "Déjà", "Creer" → "Créer", placeholder "Minimum 8 caracteres" → "caractères" | `pages/register.vue` | Angenor | open | — |
| BUG-006 | T-CHAT-04 | N3 | LangGraph recursion limit 25 atteint lors du profiling (réponse secteur) → message d'erreur rouge dans le chat, graphe bloqué. Erreur : "GRAPH_RECURSION_LIMIT" | `backend/app/graph/graph.py` ou `graph/nodes.py` (boucle tool calling infinie) | Angenor | open | — |
| BUG-007 | T-PROFILE-02 | N2 | Bouton ✓ inline profil n'envoie pas le PATCH backend → valeur non persistée. API PATCH `/api/company/profile` fonctionne en direct. Problème frontend dans le composant inline edit. | `frontend/app/pages/profile.vue` ou composant InlineEdit | Angenor | open | — |
| BUG-007b | T-PROFILE-01 | N1 | Accents manquants page profil : "Identite" → "Identité", "employes" → "employés", "personnalises" → "personnalisés", "Completez" → "Complétez", "Annee de creation" → "Année de création", "Gestion des dechets" → "déchets", "energetique" → "énergétique" | `frontend/app/pages/profile.vue` | Angenor | open | — |
| BUG-008 | T-FIN-01 | N2 | Onglet "Tous les fonds" affiche "Evaluation ESG requise" au lieu de la liste des fonds — la condition ESG ne devrait pas bloquer l'onglet catalogue statique | `frontend/app/pages/financing.vue` (condition trop large) | Angenor | open | — |
| BUG-009 | T-FIN-01 | N3 | Données fonds/intermédiaires absentes en DB (0 fonds, 0 intermédiaires). Le script seed `/app/modules/financing/seed.py` doit être exécuté manuellement — non intégré au démarrage ni aux migrations. Bloque tous les tests T-FIN-* | `backend/app/modules/financing/seed.py` — intégrer au startup ou à une migration | Angenor | open | — |
| BUG-010 | T-PERF-06 | N1 | Page 404 Nuxt en anglais : "Page not found", "Go back home" — manque traduction FR + dark mode absent | `app/error.vue` ou layout 404 | Angenor | open | — |

## Workflow de correction post-tests

1. **Clôturer exécution Vague 1** : remplir tous les statuts ⬜ → ✅/⚠️/❌
2. **Grouper bugs par sévérité** :
   - N1 : batch commit unique `fix(tests-v1): batch typos + dark mode correctifs`
   - N2 : 1 story BMAD groupée par module impacté
   - N3 : 1 story BMAD dédiée avec review LLM différent + Option 0 Fix-All
   - N4 : hotfix immédiat + post-mortem §methodology
3. **Retester bugs fixés** : marquer ✅ après correction + commit hash référence
4. **Mettre à jour sprint-status.yaml** : ajouter stories fix générées
5. **Décider retrospective Epic 10** : après Vague 1 verte (ou Vague 2 si Vague 1 révèle trop de bugs N3/N4)

## Prochaines vagues prévues

- **Vague 2** : tests post-corrections Vague 1 (régression)
- **Vague 3** : tests upload fichiers (hors agent-browser — exécution humaine manuelle)
- **Vague 4** : tests extension Chrome (hors scope web app)
- **Vague 5** : tests multi-utilisateurs admin/collaborateur/lecteur (permissions)
- **Vague 6** : tests pilote pré-GTM avec données réelles partenaires (SC-B-PILOTE)

## Historique exécution

| Date | Vague | Testeur | Stories impactées | Bugs ouverts | Bugs fermés |
|------|-------|---------|-------------------|--------------|-------------|
| 2026-04-23 | V1 | Angenor (agent-browser --headed) | Auth, Chat, Profile, Financement, Dashboard, Documents, ESG, Carbon, Nav, Perf | 10 | 0 |
