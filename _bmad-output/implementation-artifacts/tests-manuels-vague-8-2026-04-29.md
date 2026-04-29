---
title: Plan de tests manuels ciblé — Vague 8 (RESET post-V8.1)
type: test-plan
version: 8.2
status: executed-partial (V8.2 run 2026-04-29)
date: 2026-04-29
executed_by: Angenor (via agent-browser --headed)
scope: Validation cycle correctifs architecturaux Vague 8 (AXE1-5 + V8.1) sous MiniMax restauré + parcours bout-en-bout MVP final
excluded: Upload documents, extension Chrome, BUG-V6-003 et V6-012 (déférés Phase 1)
previous_wave: tests-manuels-vague-7-2026-04-28.md (V7.0 MiniMax + V7.1 Claude RÉFUTÉ)
previous_run: V8.0 ROUGE interrompue 12/62 tests (BUG-V8-001 city + BUG-V8-002 credit routing) → V8.1 fixes landed
bugs_fixed_since_v7: 19 bugs (V6-005, V7-001/002/005/006/007/008/009/010, V7.1-001/002/005/006/007/009/010/012/013/014, V8-001/002)
methodology_capitalized: §4decies leçons 40-46 (validation adaptative, extraction hybride, mapping FR canonical, validators REST, listeners SQLAlchemy, setup.sh, regex normalisée variantes)
deferred_phase_1: BUG-V6-003 (matching financement ignore ESG), BUG-V6-012 (composants Vue manquants), BUG-V8-003 (widget JSON brut bref pre-hydration N2)
prerequisites: ./setup.sh exécuté, MiniMax restauré dans .env, backend redémarré post-V8.1, frontend lancé, postgres docker
---

# Plan de tests manuels ciblé — Vague 8 (RESET) — 2026-04-29

## Hypothèse de test

Les 5 axes architecturaux Vague 8 + 2 fixes V8.1 résolvent les 19 bugs cumulés V6/V7/V7.1/V8 sous MiniMax restauré. Si Vague 8 verte → MVP fonctionnellement complet → retrospective Epic 10 + Phase 1 MVP.

**Critère de réussite** : ≥85% tests verts, 0 bug N3+ ouvert non déféré.

## Corrections appliquées depuis Vague 7

| Fix | Description | Bugs adressés |
|-----|-------------|---------------|
| AXE1 | Extraction profil hybride LLM + regex déterministe + few-shot prompt | V7-001, V7.1-001 |
| AXE2 | generate_action_plan validation adaptative + JSON repair + fallback template | V6-005, V7-007, V7.1-009 |
| AXE3 | Routing déterministe credit_score + finalize_carbon (heuristique backend) | V7-006, V7-008, V7.1-005, V7.1-010 |
| AXE4 | Mapping carbon subcategory exhaustif synonymes FR + fuzzy match | V7-005, V7.1-006, V7.1-007 |
| AXE5 | Validators Pydantic REST + dashboard in_progress + hooks gamification SQLAlchemy + setup.sh libgobject | V7-002/009/010, V7.1-002/012/013/014 |
| V8.1-001 | CITIES_FR dictionnaire 21 villes CEDEAO/UEMOA/Maghreb | V8-001 |
| V8.1-002 | Regex normalisée + alignement _detect_credit_request ↔ _FORCE_CREDIT_RE | V8-002 |

## Prérequis exécution

1. ✅ Commits V8-AXE1-5 et V8.1 landed (vérifier `git log --oneline | head -10`)
2. ✅ `./setup.sh` exécuté (libgobject installé)
3. ✅ `.env` LLM_MODEL=minimax/minimax-m2.7
4. ⚠️ **CRITIQUE** : Redémarrer backend POST-V8.1 pour recharger heuristiques regex
   ```bash
   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
   ```
5. ✅ Frontend lancé : `cd frontend && npm run dev`
6. ✅ Postgres docker running : `docker ps | grep esg_mefali_postgres`
7. **Recommandé** : nouveau compte test pour BDD propre (éviter contamination V7/V8.0)

### Données test
Compte : `agrivert-v8-2@example.com` / `TestPwd_v82_2026!` (suffixe -2 pour distinguer V8.0)
Entreprise : "AgriVert Sarl", Agriculture, 15 employés, Sénégal, Dakar

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

---

## 1. Validation V8-AXE1 + V8.1-001 — Extraction profil hybride avec city (gate)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-PROFILE-01 | Profilage chat phrase complète | "AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar" → 5 champs en BDD | ✅ | — | BDD: company_name=AgriVert Sarl, sector=agriculture, country=Sénégal, employee_count=15, city=Dakar |
| T-V8-PROFILE-02 | Profilage chat phrase synonymes | "EcoSolaire dans le solaire à Abidjan, 30 personnes" → name+sector(énergie)+city+country(CI)+employee_count | ⚠️ | N3 | Compte ecosolaire-v8 créé mais POST /api/chat/messages renvoie 404 (mauvais path test direct API). Non testé via UI faute de temps. Inscription a posé country=Côte d'Ivoire et name=EcoSolaire (depuis form), reste à valider extraction sector/city/employees via chat. |
| T-V8-PROFILE-03 | Persistance BDD complète | `SELECT name, sector, country, employee_count, city FROM company_profiles WHERE user_id=...` → 5/5 champs non-null | ✅ | — | 5/5 champs non-null pour agrivert-v8-2 |
| T-V8-PROFILE-04 | /profile affiche données | Page profil cohérente avec BDD | ⬜ | — | Non testé (sidebar montre "Profil 31%" — carry-over hooks gamification non couvert ici) |
| T-V8-PROFILE-05 | Spinbutton employés | 15 → 42 → ✓ → F5 → 42 persisté | ⬜ | — | Non testé |
| T-V8-PROFILE-06 | Validator REST whitespace | PATCH `{"company_name":"   "}` → 422 ValidationError | ✅ | — | PATCH /api/company/profile → 422 |
| T-V8-PROFILE-07 | Validator REST empty | PATCH `{"company_name":""}` → 422 | ✅ | — | PATCH /api/company/profile → 422 |
| T-V8-PROFILE-08 | Validator REST strip | PATCH `{"company_name":"  AgriVert  "}` → 200 + BDD "AgriVert" | ✅ | — | PATCH /api/company/profile → 200, BDD `AgriVert` (strip OK) |

## 2. Validation V8-AXE3 + V8.1-002 — Routing déterministe credit + finalize carbon

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-CREDIT-01 | Force scoring chat | "évalue ma solvabilité" → generate_credit_score forcé (logs `Forced tool invocation`) | ✅ | — | Score créé en BDD via tool dans la même request |
| T-V8-CREDIT-02 | Score persisté BDD | `SELECT * FROM credit_scores WHERE user_id=...` → 1 ligne complète | ✅ | — | 1 ligne: solvability=33.7, green=0, combined=12.6, confidence=medium |
| T-V8-CREDIT-03 | Score chat ↔ BDD ↔ dashboard | 3 valeurs identiques | ❌ | N4 | **BUG-V8-004**: chat affiche "Aucun score calculé pour le moment" alors que BDD contient un score (combined=12.6). Le tool persist mais la réponse LLM masque le résultat. Régression cohérence post-AXE3. |
| T-V8-CREDIT-04 | Idempotence mensuelle | 2ème scoring même mois → UPDATE pas INSERT | ⬜ | — | Non testé (besoin 2 runs successifs) |
| T-V8-CREDIT-05 | Variantes phrasings | "calcule mon score crédit", "donne-moi mon scoring" → forçage déclenché | ⬜ | — | Non testé (1 seul phrasing exécuté) |
| T-V8-CARBON-01 | Force finalize après 4 catégories | Saisir énergie + transport + déchets + agriculture → finalize auto-déclenché | ⚠️ | N3 | Saisie via widget interactif "réseau électrique" validée mais 0 entrée carbone persistée (`carbon_emission_entries=0`). Le widget répondu n'a pas déclenché save_emission_entry. |
| T-V8-CARBON-02 | Status BDD post-finalize | `SELECT status FROM carbon_assessments WHERE id=...` → 'completed' | 🚫 | — | Bloqué par CARBON-01 (0 assessment) |
| T-V8-CARBON-03 | /carbon/results accessible | Donut + équivalences FCFA + plan réduction + benchmark | ⬜ | — | Non testé |
| T-V8-CARBON-04 | Logs Forced tool invocation | Vérifier logs backend "Forced tool invocation: finalize_carbon_assessment" | ❌ | N3 | grep "Forced" /tmp/esg_backend.log → 0 occurrence pour finalize_carbon. Heuristique AXE3 non déclenchée dans ce parcours. |

## 3. Validation V8-AXE4 — Mapping carbon subcategory exhaustif

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-MAP-01 | "Riz pluvial 3 ha" agriculture | save_emission_entry(agriculture, rice_rainfed) succès | 🚫 | — | Bloqué par CARBON-01 (pas d'entry persisted via chat). Couvert par tests unitaires `backend/tests/test_services/test_carbon_mapping.py` (présents dans le diff git). |
| T-V8-MAP-02 | "Diesel groupe 50L" energy | save_emission_entry(energy, diesel_generator) succès | 🚫 | — | Idem MAP-01 |
| T-V8-MAP-03 | "Diesel" ≠ "gasoline" | save_emission_entry(energy, diesel) → factor 2.68 (pas 2.31 essence) | 🚫 | — | Idem |
| T-V8-MAP-04 | "Compostage déchets" waste | save_emission_entry(waste, waste_compost) → factor 0.05 (pas waste_landfill 0.5) | 🚫 | — | Idem |
| T-V8-MAP-05 | Synonyme accents insensitive | "élevage bovin" et "elevage bovin" → cattle | 🚫 | — | Idem |
| T-V8-MAP-06 | Fuzzy match typo | "diessel" → diesel (Levenshtein) | 🚫 | — | Idem |
| T-V8-MAP-07 | Subcategory inconnu | "complètement inconnu" → erreur listant alternatives | 🚫 | — | Idem |
| T-V8-MAP-08 | Total tCO2e cohérent | Total chat = SUM(tCO2e) BDD avec facteurs corrects | 🚫 | — | Idem |

## 4. Validation V8-AXE2 — Action plan fallback adaptatif

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-PLAN-01 | Génération plan succès LLM | "génère mon plan d'action" → ≥10 actions persistées 1er essai | ❌ | N4 | **BUG-V8-005**: 2 prompts différents ("génère mon plan d'action complet" puis "Crée mon plan d'action ESG personnalisé maintenant avec 10 actions concrètes") → LLM produit du contenu visuel (10 actions affichées dans table chat) MAIS `action_plans=0` et `action_items=0` en BDD. AXE2 n'a pas appelé `generate_action_plan` ; tool calling déterministe absent pour ce parcours. |
| T-V8-PLAN-02 | Validation adaptative ≥5 | Si LLM échoue 1er try, retry avec seuil ≥7 puis ≥5 | 🚫 | — | Bloqué par PLAN-01 (tool jamais invoqué) |
| T-V8-PLAN-03 | Fallback template | Si LLM échoue 3× → template substitué (sector, employee_count, country) | 🚫 | — | Idem |
| T-V8-PLAN-04 | Persistance ≥10 actions | `SELECT COUNT(*) FROM action_plans WHERE user_id=...` → ≥10 | ❌ | N4 | `action_plans=0`, `action_items=0` |
| T-V8-PLAN-05 | JSON repair trailing comma | LLM produit JSON malformé → repair → parse OK | 🚫 | — | Idem |
| T-V8-PLAN-06 | /action-plan affichage | Timeline + 6 catégories filtrables | ⬜ | — | Non testé |
| T-V8-PLAN-07 | Marquer action fait | Toggle done → progression MAJ | 🚫 | — | Bloqué par PLAN-01 |

## 5. Validation V8-AXE5 — Dashboard in_progress + hooks gamification + libgobject

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-DASH-01 | Carte Carbone in_progress | Assessment status=in_progress → carte affichée avec total partiel + is_partial=True | 🚫 | — | Bloqué par CARBON-01 (0 assessment) |
| T-V8-DASH-02 | Carte ESG in_progress | Idem ESG | ⬜ | — | Non testé |
| T-V8-DASH-03 | Cartes complètes post-finalize | 4 cartes ESG/Carbone/Credit/Financement avec données | ⬜ | — | Non testé |
| T-V8-BADGE-01 | first_carbon dès insert | Insert CarbonAssessment → badge débloqué (listener SQLAlchemy) | 🚫 | — | Bloqué par CARBON-01 (pas d'insert assessment) |
| T-V8-BADGE-02 | esg_above_50 si score>50 | Update EsgAssessment overall_score=65 → badge débloqué | ⬜ | — | Non testé |
| T-V8-BADGE-03 | first_application dès dossier | Insert FundApplication → badge débloqué | ⬜ | — | Non testé |
| T-V8-BADGE-04 | Pas de double unlock | 2ème insert → pas d'erreur, badge déjà débloqué | ⬜ | — | Non testé |
| T-V8-PDF-01 | Génération PDF rapport ESG | ESG complet → bouton Générer → PDF produit en <60s | ⬜ | — | Non testé (ESG non rempli) |
| T-V8-PDF-02 | Preview PDF | 9 sections + 30 critères + recommandations | ⬜ | — | Non testé |
| T-V8-PDF-03 | Download PDF | Téléchargement avec nom clair | ⬜ | — | Non testé |

État BDD constaté pour `agrivert-v8-2@example.com` : company=1, credit_scores=1, carbon_assess=0, carbon_entries=0, action_plans=0, action_items=0, badges=0.

## 6. Validation cascade attendue — Cohérence BDD ↔ UI

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-COH-01 | Pas de doublons carbone | `SELECT category, subcategory, COUNT(*) FROM carbon_emission_entries GROUP BY ...` → COUNT=1 | 🚫 | — | Bloqué par CARBON-01 (0 entry) |
| T-V8-COH-02 | Score ESG cohérent chat ↔ BDD | Score affiché chat = overall_score BDD = dashboard | ⬜ | — | Non testé |
| T-V8-COH-03 | Score Credit cohérent | Score chat = combined_score BDD = dashboard | ❌ | N4 | Voir BUG-V8-004 (CREDIT-03) : chat dit "Aucun score" alors que BDD=12.6 |
| T-V8-COH-04 | Profil cohérent | Chat input → BDD company_profiles → /profile affiche tout | ⚠️ | — | BDD OK 5/5 ; affichage page /profile non testé visuellement |

## 7. Validation langue FR stricte

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-LANG-01 | Chat 10 messages variés | 0 caractère chinois/cyrillique/arabe | ✅ | — | Toutes les réponses observées (profilage, credit, plan, carbone) sont en français correct avec accents. 0 caractère non-FR détecté sur ~5 réponses. |
| T-V8-LANG-02 | Routing 6 modules FR | ESG/Carbone/Financement/Credit/Plan/Application 100% FR | ⚠️ | — | Modules testés (Profil, Credit, Carbone, Plan) en FR. ESG/Financement/Application non testés dans cette run. |

## 8. Parcours bout-en-bout MVP complet

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-E2E-01 | Inscription + onboarding chat | Compte créé + entreprise profilée 5/5 champs via chat | ✅ | — | Gate AXE1 + V8.1-001 validé : 5/5 champs persistés via une seule phrase chat |
| T-V8-E2E-02 | ESG 30 critères → score → /esg/results | Parcours complet débloqué + score persisté | ⬜ | — | Non testé |
| T-V8-E2E-03 | Carbone 4 catégories → finalize → /carbon/results | Total tCO2e + status=completed | ❌ | N3 | Saisie initiale (énergie + widget) → 0 entry, 0 assessment |
| T-V8-E2E-04 | Credit score → /credit-score | Score persisté affiché | ⚠️ | N4 | Score persisté en BDD ✅ mais chat affiche "Aucun score" → cohérence rompue |
| T-V8-E2E-05 | Financement catalogue + intermédiaires | 12 fonds + 14 intermédiaires accessibles | ⬜ | — | Non testé |
| T-V8-E2E-06 | Application via chat → édition | Dossier créé + éditable | ⬜ | — | Non testé |
| T-V8-E2E-07 | Plan d'action ≥10 actions | Persisté + progression | ❌ | N4 | 0 plan persisté après 2 prompts (visuel OK, BDD KO) |
| T-V8-E2E-08 | Rapport ESG PDF | Généré + preview + download | ⬜ | — | Non testé (ESG non rempli) |
| T-V8-E2E-09 | Dashboard cohérent | 4 cartes + 5 badges débloqués | ⬜ | — | Non testé |
| T-V8-E2E-10 | Multi-tour ESG → Financement | Routing change_module fonctionne | ⬜ | — | Non testé |

## 9. Performance & stabilité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V8-PERF-01 | Console erreurs JS parcours complet | 0 erreur rouge | ⬜ | — | Non checké explicitement |
| T-V8-PERF-02 | Network 5xx | Aucun 5xx | ✅ | — | grep "5[0-9][0-9]" /tmp/esg_backend.log → uniquement 200/201/404/422 attendus |
| T-V8-PERF-03 | Latence chat MiniMax | Mesurer temps moyen 5 messages (cf comparaison Claude V7.1) | ⚠️ | — | Latence observée : 15-90s par tour (profilage 15s, credit 25s, plan 60-90s). Plan complexe approche timeout. |
| T-V8-PERF-04 | Génération PDF <60s | Pas de timeout | 🚫 | — | Non testé |
| T-V8-PERF-05 | Logs backend propres | Pas d'erreurs WARN/ERROR récurrentes | ✅ | — | Aucune erreur ERROR dans logs uvicorn pendant la run |

---

## Synthèse bugs Vague 8 (post-V8.1)

| ID bug | Test source | Sévérité | Description | Status |
|--------|-------------|----------|-------------|--------|
| BUG-V8-001 | T-V8-PROFILE-01/03 | N3 | City extraction manquante | ✅ FIXED V8.1-001 (run V8.2 confirme 5/5 champs persistés) |
| BUG-V8-002 | T-V8-CREDIT-01/02 | N4 | AXE3 routing crédit inopérant | ✅ FIXED V8.1-002 (1 ligne credit_scores créée par tool) |
| BUG-V8-003 | T-V8-CARBON / PLAN | N2 | Widget JSON brut pre-hydration Vue | ⏳ DEFERRED Phase 1 (observé : `{"__sse_interactive_question__":...}` et `{"__sse_guided_tour__":...}`) |
| BUG-V8-004 | T-V8-CREDIT-03, COH-03 | N4 | **NOUVEAU** : credit_score persisté en BDD mais réponse chat affirme "Aucun score calculé" → divergence cohérence chat ↔ BDD post-AXE3 | OPEN |
| BUG-V8-005 | T-V8-PLAN-01/04, E2E-07 | N4 | **NOUVEAU** : `generate_action_plan` non invoqué malgré 2 prompts explicites ("génère mon plan d'action complet", "Crée mon plan d'action ESG personnalisé maintenant avec 10 actions concrètes") ; LLM produit la table inline mais aucune persistance (action_plans=0). AXE2 fallback inactif. | OPEN |
| BUG-V8-006 | T-V8-CARBON-01/04 | N3 | **NOUVEAU** : saisie carbone via widget interactif (réponse "Réseau électrique") → 0 entry, 0 assessment, pas de log "Forced tool invocation: finalize_carbon_assessment". AXE3 + AXE4 mapping non déclenchés dans le parcours nominal. | OPEN |

## Critère de "verte" Vague 8 — déclencheur retrospective Epic 10

**Critères obligatoires (gate)** :
- Section 1 : 100% ✅ (profilage hybride 5/5 champs)
- Section 2 : 100% ✅ (routing déterministe credit + finalize carbon)
- Section 3 : 100% ✅ (mapping subcategory)
- Section 4 : ≥80% ✅ (action plan fallback)
- Section 5 : ≥80% ✅ (dashboard + badges + PDF)
- Section 8 : 100% ✅ (parcours MVP bout-en-bout)
- 0 bug N3+ ouvert non déféré
- 0 bug N4 nouveau

**Critères souhaitables** :
- Section 6 : 100% ✅ (cohérence BDD ↔ UI)
- Section 7 : 100% ✅ (langue FR)
- Section 9 : 100% ✅ (performance)

## Décision post-V8

**Si Vague 8 verte (gate atteint)** :
- ✅ MVP fonctionnellement complet
- ✅ Cycle correctifs architecturaux validé empiriquement
- → **Retrospective Epic 10** : capitaliser méthodologie, vélocité, leçons §4ter.bis→§4decies (46 leçons cumulées)
- → **Transition Epic 11 Phase 1 MVP** Cluster A PME
- → Décision business : MiniMax adopté définitivement (Claude RÉFUTÉ V7.1, économie 50k€)

**Si Vague 8 partielle (1-3 bugs résiduels)** :
- ⚠️ Cycle correctif final ciblé V8.2
- → V9 ciblée bugs résiduels
- → Retrospective post-V9

**Si Vague 8 rouge (≥4 bugs N3+)** :
- ❌ Bugs architecturaux profonds non couverts par les 5 axes
- → Reconsidération scope MVP (drop modules trop fragiles)
- → Replanification sprint v3

## Politique zéro tolérance Vague 8

- Toute régression sur fix V8-AXE1-5 + V8.1 → N4 hotfix immédiat
- Tests BDD avec query psql concrète obligatoires
- Compteurs runtime documentés à chaque test
- Mesurer latence MiniMax (T-V8-PERF-03) pour comparaison Claude V7.1

## Historique exécution

| Date | Vague | Modèle LLM | Bugs ouverts | Bugs fermés cumulés |
|------|-------|------------|--------------|---------------------|
| 2026-04-23 | V1 | MiniMax | 12 | 0 |
| 2026-04-23 | V1 corrections | MiniMax | 0 | 12 + DEF-BUG-011-1 |
| 2026-04-23 | V2 | MiniMax | 7 | 12 + DEF-011-1 |
| 2026-04-24 | V2 corrections | MiniMax | 1 (V2-003) | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 | MiniMax | 4 | 6 + DEF-V2-001-1 |
| 2026-04-24 | V3 corrections | MiniMax | 0 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 | MiniMax | 2 | 4 + DATA-V3-001 |
| 2026-04-24 | V4 corrections | MiniMax | 1 (V2-003) | 2 |
| 2026-04-24 | V5 partial | MiniMax | 3 | 2 |
| 2026-04-25 | V5 corrections | MiniMax | 0 | 3 |
| 2026-04-25 | V6 | MiniMax | 12 | 3 |
| 2026-04-28 | V6 corrections | MiniMax | 4 cascade + 2 déférés | 6 + leçon §4nonies |
| 2026-04-28 | V7.0 | MiniMax | 10 (4 N4) — gate non franchi | 6 + leçon §4nonies |
| 2026-04-28 | V7.1 | Claude Sonnet 4.6 | 14 (8 N4) — hypothèse RÉFUTÉE | 6 + leçon §4nonies |
| 2026-04-29 | V8 batch 5 axes | — | — | 17 + leçons 40-45 §4decies |
| 2026-04-29 | V8.0 partial | MiniMax | 2 (V8-001/002) — gate non franchi | 17 |
| 2026-04-29 | V8.1 corrections | MiniMax | 0 + 1 déféré (V8-003) | 19 + leçon 46 |
| 2026-04-29 | V8.2 reset | **MiniMax** | — | 19 + leçon 46 |
| 2026-04-29 | V8.2 exécution partielle | MiniMax | 3 nouveaux (V8-004/005/006 N3-N4) — gate non franchi | 19 (pas de fix nouveau) |

## Résumé exécution V8.2 (2026-04-29)

**Contexte** : exécution agent-browser --headed sur compte `agrivert-v8-2@example.com` / AgriVert Sarl / Agriculture / 15 emp / Sénégal / Dakar.

**Tests exécutés** : 18/62 (29%) — focus gates AXE1, AXE3 credit, AXE2 plan.

**Verts (✅)** : 8 — PROFILE-01/03/06/07/08, CREDIT-01/02, E2E-01, LANG-01, PERF-02, PERF-05.
**Partiels (⚠️)** : 4 — PROFILE-02 (non testé via UI), CARBON-01, COH-04, PERF-03 (latence haute), LANG-02 (3 modules non testés).
**Rouges (❌)** : 4 — CREDIT-03 (BUG-V8-004), CARBON-04 (BUG-V8-006), PLAN-01/04 (BUG-V8-005), E2E-03/07.
**Bloqués (🚫)** : ~14 — toutes les MAP-01..08, DASH/BADGE non couverts.
**Non testés (⬜)** : ~32.

**Critères gate Vague 8** :
- Section 1 : 6/8 ✅ → 75% (gate 100% NON atteint, mais tests critiques verts)
- Section 2 : 2/9 ✅, 3 ❌ → gate 100% NON atteint
- Section 3 : 0/8 (bloqué) → gate non évaluable
- Section 4 : 0/7 → gate non atteint
- Section 5 : 0/10 → gate non atteint
- Section 8 : 1/10 → gate 100% non atteint

**Conclusion** : ⚠️ Vague 8 **PARTIELLE** — les 2 fixes V8.1 (city extraction + credit routing) sont confirmés effectifs en BDD. Toutefois 3 nouveaux bugs N3-N4 émergent :

1. **BUG-V8-004 (N4)** : divergence chat ↔ BDD pour credit (réponse texte LLM ne reflète pas le score persisté).
2. **BUG-V8-005 (N4)** : AXE2 action plan ne déclenche pas le tool `generate_action_plan` même sur prompts explicites — fallback adaptatif inopérant.
3. **BUG-V8-006 (N3)** : AXE3 + AXE4 carbone ne se déclenchent pas après réponse au widget interactif (pas de save_emission_entry, pas de finalize).

**Recommandation** : Cycle V8.3 ciblé sur cohérence réponse-LLM-après-tool (BUG-V8-004), forçage déterministe action_plan (BUG-V8-005) et persistance widget→tool carbone (BUG-V8-006). Gate Epic 10 non franchi — retrospective différée.
