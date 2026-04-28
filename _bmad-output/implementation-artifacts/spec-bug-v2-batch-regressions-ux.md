---
title: 'BUG-V2-batch — DEF-V2-001-1 + V2-003/004/005/006/007 régressions et UX Vague 2'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
route: 'plan-code-review'
baseline_commit: '54559d77ee2a65cc56a8bdb7d6dbde4fff71eacb'
context:
  - '{project-root}/backend/app/graph/nodes.py'
  - '{project-root}/frontend/app/pages/financing/index.vue'
  - '{project-root}/frontend/app/pages/esg/index.vue'
  - '{project-root}/frontend/app/pages/esg/results.vue'
  - '{project-root}/frontend/app/pages/credit-score/index.vue'
  - '{project-root}/frontend/app/pages/reports/index.vue'
  - '{project-root}/frontend/app/pages/carbon/index.vue'
  - '{project-root}/frontend/app/pages/carbon/results.vue'
  - '{project-root}/frontend/app/components/profile/ProfileField.vue'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Après le commit 54559d7 (fix BUG-V2-001/002 chat regressions), six bugs restent ouverts dans la Vague 2 de tests manuels :
- **DEF-BUG-V2-001-1** (HIGH) : le rappel `RAPPEL FINAL — LANGUAGE_INSTRUCTION` corrige la régression langue MiniMax *uniquement* dans `chat_node`. Les 6 nœuds spécialistes (`esg_scoring_node`, `carbon_node`, `financing_node`, `credit_node`, `application_node`, `action_plan_node`) n'ont pas ce rappel ; les réponses post-tool calling de ces modules peuvent donc toujours contenir des caractères chinois.
- **BUG-V2-006** (CRITICAL) : l'erreur métier « Évaluation ESG requise » remontée par `fetchMatches` est stockée dans un champ `error` partagé du store financement et fuit dans les onglets « Tous les fonds » et « Intermédiaires » (template générique d'erreur capturé), bloquant tout le parcours financement.
- **BUG-V2-007** (HIGH) : les boutons ✎/✓/✕ du composant `ProfileField` n'ont pas de `type="button"` explicite ; certaines intégrations mobiles / lecteurs d'écran (spinbutton) déclenchent un submit implicite ou un comportement d'accessibilité dégradé.
- **BUG-V2-004** (LOW) + **BUG-V2-005** (MEDIUM) : accents français manquants sur 7 pages UI + texte italic profil.
- **BUG-V2-003** (MEDIUM) : chat ne scrollerait pas auto — investigation faite : logique scroll en place (`messages.length` + `streamingContent` watchers dans `FloatingChatWidget.vue`), bug non reproduit en code review.

**Approach :** Fix groupé Vague 2 — chaque bug est traité dans son propre fichier cible. Backend : extension du pattern `RAPPEL FINAL` aux 6 nœuds spécialistes dans `nodes.py` (DEF-BUG-V2-001-1). Frontend : (1) scope des 3 templates d'erreur financement à `activeTab === 'recommendations'` pour empêcher la fuite d'erreur ESG sur les autres onglets (BUG-V2-006), (2) ajout `type="button"` + `aria-label` sur les 3 boutons de `ProfileField` (BUG-V2-007), (3) batch correction accents sur 7 pages (BUG-V2-005), (4) constat que BUG-V2-004 est déjà résolu en amont, (5) BUG-V2-003 laissé ouvert avec note : code scroll présent, à re-tester côté QA.

## Boundaries & Constraints

**Always :**
- Conserver le pattern RAPPEL FINAL strictement identique à celui de `chat_node` (concaténation sur `full_prompt` juste avant `SystemMessage`).
- Tests d'invariant statique pour vérifier la présence du pattern dans les 7 nœuds.
- Accents français normalisés via caractères Unicode (pas d'entités HTML, pas d'ASCII).
- Scope les templates d'erreur financement au seul onglet `recommendations` — les onglets `funds`/`intermediaries` rendent leur propre contenu même en présence d'une `error` store leakée.

**Ask First :**
- Si un nœud spécialiste a une topologie différente (e.g. préfixe `full_prompt` construit dans un helper externe) nécessitant un refactoring → HALT.
- Si la suppression des templates erreur génère une régression UX (utilisateur sans feedback de l'erreur matches sur les autres onglets) → HALT pour décider entre per-tab-error dans le store vs notification toast.

**Never :**
- Ne jamais changer la signature des builders de prompts (`build_esg_prompt`, etc.) — le rappel est ajouté côté nœud, pas côté builder.
- Ne jamais modifier l'API backend `/financing/matches` ni son statut 428.
- Ne jamais modifier l'enveloppe du store financement (`error` partagé conservé — refactoring per-source reporté en epic 11).
- Ne jamais ajouter un fallback de détection post-génération regex CJK (rejeté par spec V2-001/002).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|----------|--------------|---------------------------|
| ESG scoring post-tool calling | User déclenche tool `save_esg_criterion` dans `esg_scoring_node` | Réponse française visible, zéro caractère CJK |
| Carbon bilan post-tool | Tool `save_carbon_entry` exécuté | Réponse française, visible |
| Financement matching post-tool | Tool `get_fund_matches` exécuté | Idem |
| Navigation financement sans ESG | `fetchMatches` → 428, onglet `funds` sélectionné | Contenu fonds rendu, pas de template d'erreur ESG |
| Navigation financement sans ESG, onglet `intermediaries` | Idem | Annuaire intermédiaires rendu, pas d'erreur |
| Navigation financement sans ESG, onglet `recommendations` | Idem | Template « Évaluation ESG requise » rendu (comportement conservé) |
| Profil edit inline employés | Clic ✎ → saisie spinbutton → clic ✓ | PATCH `/company/profile` émis, store mis à jour |
| Profil edit inline texte | Clic ✎ → saisie texte → clic ✓ | Idem |

</frozen-after-approval>

## Code Map

- `backend/app/graph/nodes.py` :
  - `esg_scoring_node` (L579) — append RAPPEL FINAL après ligne `full_prompt = system_prompt + tool_instructions + esg_state_context` (~L694)
  - `carbon_node` (L734) — idem après `full_prompt = system_prompt + carbon_state_context` (~L858)
  - `financing_node` (L908) — idem après `full_prompt = system_prompt + tool_instructions` (~L984)
  - `credit_node` (L1084) — idem après le bloc historique (~L1152)
  - `application_node` (L1271) — idem (~L1335)
  - `action_plan_node` (L1395) — idem (~L1531)
- `backend/tests/test_graph/test_specialists_language_reminder.py` — nouveau fichier, 8 tests d'invariant statique (1 global + 1 count + 6 paramétrisés).
- `frontend/app/pages/financing/index.vue` — scope de 3 templates d'erreur à `activeTab === 'recommendations'` (L194, L208, L222) + normalisation accents.
- `frontend/app/components/profile/ProfileField.vue` — ajout `type="button"` + `aria-label` sur les 3 boutons ✎ ✓ ✕.
- `frontend/app/pages/{esg,credit-score,reports,carbon}/**/*.vue` — normalisation accents batch.

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/graph/nodes.py` — Append `"\n\nRAPPEL FINAL — " + LANGUAGE_INSTRUCTION` dans les 6 nœuds spécialistes (ESG/Carbon/Financing/Credit/Application/ActionPlan).
- [x] `backend/tests/test_graph/test_specialists_language_reminder.py` — 8 tests d'invariant : `test_nodes_file_exists`, `test_rappel_final_count_covers_chat_plus_specialists` (>= 7 occurrences), + 6 tests paramétrisés `test_specialist_node_contains_language_reminder[node_name]`.
- [x] `frontend/app/pages/financing/index.vue` — Scoper les 3 templates d'erreur à `activeTab === 'recommendations'` (BUG-V2-006) + normaliser accents (Évaluation / Réaliser / Réessayer / Complétez / Régional / Marché / Accès / Intermédiaire / Suggéré / Intéressé / Accepté / Rejeté / À venir / Développement / Développeur) (BUG-V2-005).
- [x] `frontend/app/pages/esg/{index,results}.vue` — Normaliser accents (Évaluation / Évaluez / Démarrez / Démarrer / Première / Critères / Résultats / Terminée / Détail) (BUG-V2-005).
- [x] `frontend/app/pages/credit-score/index.vue` — Normaliser accents (Crédit / Solvabilité / Génération / Générer / Régénérer / Réessayer / Découvrir / Évaluation / Expiré / Généré / Évolution / Combiné) (BUG-V2-005).
- [x] `frontend/app/pages/reports/index.vue` — Normaliser accents (Généré / Générez / Résultats / Évaluations / Conformité / Prévisualiser / Télécharger) (BUG-V2-005).
- [x] `frontend/app/pages/carbon/{index,results}.vue` — Normaliser accents (Démarrez / Démarrer / Catégories / Émissions / Données / Terminé) (BUG-V2-005).
- [x] `frontend/app/components/profile/ProfileField.vue` — Ajouter `type="button"` et `aria-label` sur les 3 boutons ✎/✓/✕ (BUG-V2-007).
- [x] Mise à jour `_bmad-output/implementation-artifacts/tests-manuels-vague-2-2026-04-23.md` — marquer BUG-V2-004/005/006/007 + DEF-BUG-V2-001-1 FIXED, BUG-V2-003 OPEN avec note code review.
- [x] Mise à jour `_bmad-output/implementation-artifacts/deferred-work.md` — DEF-BUG-V2-001-1 marqué RÉSOLU.

**Acceptance Criteria :**
- Given une conversation avec tool call dans un nœud spécialiste, when le nœud renvoie sa réponse, then aucun caractère CJK n'apparaît et le texte est en français (validé via test statique de structure).
- Given un utilisateur sans évaluation ESG sur la page `/financing`, when il clique sur l'onglet « Tous les fonds » ou « Intermédiaires », then il voit la liste normalement, pas un écran d'erreur ESG ou générique.
- Given un utilisateur édite un champ du profil via le bouton ✎, when il clique sur ✓, then la requête PATCH part et la valeur persiste après F5.
- Given la suite backend complète, when elle est exécutée, then 1703 tests passent (1 flake `test_event_loop_not_blocked_local` non lié).

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_graph/test_specialists_language_reminder.py -v` → 8 tests verts (8/8 confirmé).
- `cd backend && source venv/bin/activate && pytest -q` → 1703 passed, 1 failed (flake timing non lié), 93 skipped.

**Manual checks :**
- Re-tester scenarios T-ESG-01, T-CARBON-01, T-FIN-09, T-APP-02, T-CREDIT-02, T-PLAN-02 — pas de caractère chinois.
- Naviguer `/financing` sans ESG — onglets « Tous les fonds » et « Intermédiaires » affichent leur contenu (T-FIN-01/07).
- Modifier un champ profil inline (T-PROFILE-02) — valider la persistance.
- Vérifier visuellement les accents sur les pages ESG, Financing, Credit, Reports, Carbon (T-ESG-12, T-FIN-01, T-CREDIT-01, T-REPORT-01).

## Design Notes

**Pourquoi append en queue dans le nœud plutôt que dans le builder :**
Les builders de prompts (`build_esg_prompt`, etc.) sont déjà enrichis par DEF-BUG-011-1 pour placer `LANGUAGE_INSTRUCTION` en **tête**. Le besoin Vague 2 est de le remettre en **queue** APRÈS les tool instructions et l'état dynamique (pour dominer un éventuel ToolMessage chinois). Faire cela côté builder nécessiterait de restructurer la signature pour distinguer « tête » de « queue » — alourdit l'API. Faire cela côté nœud reste une seule ligne pattern-par-pattern, auditable par grep.

**Pourquoi scoper les 3 templates d'erreur à `recommendations` :**
Le store financement partage un seul champ `error` pour 3 fetches indépendants (`matches`/`funds`/`intermediaries`). Quand `fetchMatches` échoue avec 428 (ESG requise), l'erreur persiste dans le store et fuit dans les templates des autres onglets. Refactoring propre = per-source-error (LOW-BUG008-1 dans deferred-work). Fix court = scoper les templates d'erreur à l'onglet où l'erreur matches a du sens (`recommendations`). Les onglets `funds`/`intermediaries` rendent leur contenu normalement même en présence d'une erreur store leakée. Si `fetchFunds` ou `fetchIntermediaries` échoue réellement, leur propre état vide est déjà géré (« Aucun fonds ne correspond », « Aucun intermédiaire »).

**Pourquoi `type="button"` sur ProfileField :**
Défense en profondeur contre un ancêtre `<form>` (non présent actuellement mais pourrait l'être à l'avenir) qui capturerait le click comme submit. Ajout d'`aria-label` pour accessibilité lecteur d'écran (le SVG seul sans label textuel est inaccessible).

**Pourquoi BUG-V2-003 reste OPEN sans fix :**
Code review montre que la logique scroll est présente et correcte dans `FloatingChatWidget.vue` (watchers `messages.length` L461 + `streamingContent` L471 + reset `userScrolledUp` à l'ouverture L481). Ajouter un `watch(messages, {deep:true})` coûterait en perf sans garantie de fix. Meilleure stratégie = re-QA manuel ; si reproduit, investigation ciblée sur l'événement déclencheur exact.

## Spec Change Log

_(vide — aucun bad_spec loopback)_

## Suggested Review Order

**Backend — extension rappel linguistique**

- `esg_scoring_node` : append ligne 694 [`nodes.py:694`](../../backend/app/graph/nodes.py#L694)
- `carbon_node` : L858 [`nodes.py:858`](../../backend/app/graph/nodes.py#L858)
- `financing_node` : L984 [`nodes.py:984`](../../backend/app/graph/nodes.py#L984)
- `credit_node` : L1152 [`nodes.py:1152`](../../backend/app/graph/nodes.py#L1152)
- `application_node` : L1335 [`nodes.py:1335`](../../backend/app/graph/nodes.py#L1335)
- `action_plan_node` : L1531 [`nodes.py:1531`](../../backend/app/graph/nodes.py#L1531)
- Tests d'invariant statique [`test_specialists_language_reminder.py`](../../backend/tests/test_graph/test_specialists_language_reminder.py)

**Frontend — BUG-V2-006 scope erreurs financement**

- Template ESG gate inchangé, déjà scopé (L194)
- Template profil gate scopé (L208) [`financing/index.vue:208`](../../frontend/app/pages/financing/index.vue#L208)
- Template générique scopé (L222) [`financing/index.vue:222`](../../frontend/app/pages/financing/index.vue#L222)

**Frontend — BUG-V2-007 ProfileField**

- Bouton ✓ avec `type="button"` [`ProfileField.vue:123`](../../frontend/app/components/profile/ProfileField.vue#L123)
- Bouton ✕ avec `type="button"` [`ProfileField.vue:133`](../../frontend/app/components/profile/ProfileField.vue#L133)
- Bouton ✎ avec `type="button"` [`ProfileField.vue:155`](../../frontend/app/components/profile/ProfileField.vue#L155)

**Frontend — BUG-V2-005 accents batch**

- financing, esg, credit-score, reports, carbon (voir section Code Map).

**Traçabilité**

- Tests manuels : [`tests-manuels-vague-2-2026-04-23.md:254`](./tests-manuels-vague-2-2026-04-23.md#L254)
- Deferred work : [`deferred-work.md:917`](./deferred-work.md#L917)
