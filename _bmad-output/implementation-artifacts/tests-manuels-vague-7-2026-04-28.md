---
title: Plan de tests manuels ciblé — Vague 7 (réexécution post-switch LLM Claude Sonnet 4.6)
type: test-plan
version: 7.1
status: completed (gate non franchi, hypothèse RÉFUTÉE)
date: 2026-04-28
executed_by: Angenor (via agent-browser --headed)
scope: Validation BUG-V6-001/002/004/005/009/011 + cascade V6-006/007/008/010 + parcours bout-en-bout MVP — RÉEXÉCUTION sous Claude Sonnet 4.6
excluded: Upload documents, extension Chrome, BUG-V6-003 et V6-012 (déférés Phase 1)
previous_wave: tests-manuels-vague-6-2026-04-25.md
previous_run: V7.0 (MiniMax) — 10 bugs ouverts dont 4 N4 — gate non franchi (archivé section finale)
bugs_fixed_since_v6: BUG-V6-001 BUG-V6-002 BUG-V6-004 BUG-V6-005 BUG-V6-009 BUG-V6-011 (commits cd98ff9 + 0862abd + a6843e7 + c94c778 + 8ddc842)
methodology_capitalized: §4nonies leçon 36 (validation runtime systémique tools persistance)
deferred_phase_1: BUG-V6-003 (matching financement ignore ESG), BUG-V6-012 (composants Vue EsgRecommendations/EsgScoreHistory manquants)
prerequisites: Backend lancé, frontend lancé, postgres docker funds=12 intermediaries=14, .env LLM_MODEL=anthropic/claude-sonnet-4.6
llm_change: switch MiniMax → Claude Sonnet 4.6 (test hypothèse "bugs causés par provider LLM faible")
---

# Plan de tests manuels ciblé — Vague 7 (RESET) — 2026-04-28

## Hypothèse de test

V7.0 sous **MiniMax** a révélé 10 bugs dont 4 N4. Pattern récurrent : LLM extrait mal les arguments structurés depuis le langage naturel (args null, JSON parse failed, mapping subcategory échoué, divergence prompt vs comportement).

**Hypothèse à valider V7.1** : ces bugs sont causés par la fiabilité tool calling du provider MiniMax. Sous **Claude Sonnet 4.6** (référence industrie pour tool calling), ces bugs disparaissent.

**Si Vague 7.1 verte sous Claude** → décision business : MiniMax abandonné pour modules métier critiques, accepter coût LLM +10x.
**Si Vague 7.1 toujours rouge** → bugs sont architecturaux (prompts, tools, validation), provider non causal.

## Corrections appliquées depuis Vague 6 (rappel)

| Bug | Fix |
|-----|-----|
| BUG-V6-001 | request_timeout=120s + fallback template résumé exécutif |
| BUG-V6-002 | Dedup runtime save_emission_entry carbone |
| BUG-V6-004 | Idempotence mensuelle generate_credit_score |
| BUG-V6-005 | Validation ≥10 actions + champs requis |
| BUG-V6-009 | Idempotence credit (UPDATE pas INSERT) |
| BUG-V6-011 | Rejet whitespace-only update_company_profile |
| §4nonies leçon 36 | Validation runtime systémique tous tools persistance |

## Prérequis exécution

1. Vérifier `.env` : `LLM_MODEL=anthropic/claude-sonnet-4.6` (ou équivalent OpenRouter `anthropic/claude-sonnet-4.6`)
2. Vérifier que `LLM_BASE_URL` et `LLM_API_KEY` correspondent au provider Claude (OpenRouter ou Anthropic direct)
3. Redémarrer le backend pour recharger `.env` : `uvicorn app.main:app --reload`
4. **Recommandé** : nouveau compte test pour BDD propre (éviter contamination V7.0)
5. Stack lancée : backend port 8000, frontend port 3000, postgres docker funds=12 intermediaries=14

### Données test
Compte : nouveau (suggéré `agrivert-claude-test@example.com` / `TestPwd_v71_2026!`)
Entreprise : "AgriVert Sarl", Agriculture, 15 employés, Sénégal, Dakar

## Légende statuts

| Statut | Signification |
|--------|---------------|
| ⬜ | Non testé |
| ✅ | OK |
| ⚠️ | OK partiel |
| ❌ | Bug bloquant |
| 🚫 | N/A |

## Note env

⚠️ **BUG-V7-003 libgobject (env macOS)** identifié sous V7.0 — **ne dépend pas du LLM**. Avant lancement V7.1, exécuter :
```bash
brew install pango cairo gdk-pixbuf libffi
# OU
brew install weasyprint
```
Sinon Section 1 sera bloquée indépendamment du switch LLM.

---

## 1. Validation BUG-V6-001 — Génération PDF rapport ESG (gate critique)

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-PDF-01 | ESG complet → bouton Générer | Génération démarre + PDF produit en <60s | ❌ | N4 (env) | **BUG-V7.1-012 (BUG-V7-003 confirmé)** : `weasyprint` lève `OSError: cannot load library 'libgobject-2.0-0'`. macOS — `brew list` montre seulement `cairo` et `pango`, manquent `gdk-pixbuf`, `libffi`, `glib`. NON lié au LLM. Préreq env documenté en plan mais NON appliqué avant V7.1. |
| T-V7-PDF-02 | Notification chat SSE | "Rapport généré" dans chat | 🚫 | — | Bloqué par PDF-01. |
| T-V7-PDF-03 | Preview PDF inline | Preview affiché 9 sections | 🚫 | — | Bloqué par PDF-01. |
| T-V7-PDF-04 | Contenu PDF cohérent | Score ESG, 30 critères, recommandations présents | 🚫 | — | Bloqué par PDF-01. |
| T-V7-PDF-05 | Download PDF | Téléchargement avec nom clair | 🚫 | — | Bloqué par PDF-01. |
| T-V7-PDF-06 | Fallback template | Si simul timeout LLM → template fallback, pas de 500 | 🚫 | — | Bloqué par PDF-01. Le test du fallback BUG-V6-001 ne peut pas être validé tant que WeasyPrint n'est pas opérationnel. |

## 2. Validation BUG-V6-002 — Carbone sans doublons

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-C-01 | Bilan complet 4 catégories | énergie + transport + déchets + industriel/agricole | ❌ | N4 | **BUG-V7.1-004** : `save_emission_entry(category="agriculture", subcategory=null)` → erreur backend "Aucun facteur d'emission trouve pour categorie 'agriculture' et sous-categorie 'None'". Claude HALLUCINE alors une fausse justification à l'utilisateur : "L'agriculture n'est pas applicable pour votre secteur (services)" — alors que (a) le secteur déclaré est "Agriculture" et (b) le user a mentionné "3 ha riz pluvial". Régression CONFIRMÉE. |
| T-V7-C-02 | Pas de doublons BDD | `SELECT category, subcategory, COUNT(*) FROM carbon_emission_entries GROUP BY ...` → COUNT=1 | ✅ | — | 3 entries (energy, transport, waste), chacune unique. Pas de doublon. |
| T-V7-C-03 | Total tCO2e cohérent chat ↔ BDD | Total chat = SUM(tCO2e) BDD | ✅ | — | Chat 16.87 tCO2e ↔ BDD 16.866 tCO2e (cohérent). Mais sur 3 catégories au lieu de 4 attendues. |
| T-V7-C-04 | finalize_carbon_assessment | status='completed' BDD post-conversation | ❌ | N4 | **BUG-V7.1-005 (régression BUG-V7-006)** : Après "Oui, finalise ce bilan", Claude affiche un plan de réduction MAIS n'appelle JAMAIS le tool `finalize_carbon_assessment`. BDD reste `status='in_progress'`, `completed_categories=[]`, `sector=null`. Régression CONFIRMÉE — switch LLM ne résout PAS. |
| T-V7-C-05 | /carbon/results accessible | Donut + équivalences FCFA + plan réduction + benchmark | ⚠️ | N3 | Page accessible MALGRÉ status=in_progress. Affiche 16.9 tCO2e/an, donut 70/25/5%, équivalences (14.1 vols Paris-Dakar, 7 années conduite, 674.6 arbres). MAIS pas d'équivalences FCFA, pas de plan de réduction, pas de benchmark sectoriel. Attendu : équivalences FCFA + plan + benchmark — manquants. |
| T-V7-C-06 | Re-saisie même catégorie | Tool retourne erreur "déjà saisie" ou UPDATE pas duplicate | 🚫 | — | Non testé (assessment non finalisé) |
| **BUG-V7.1-006** | save_emission_entry subcategory null systématique | Tous les 4 appels avec `subcategory=null`. Backend mappe via heuristique ("riz pluvial" → null = échec, "diesel" → "gasoline", "compost" → "waste_landfill"). | ❌ | N4 | Régression BUG-V7-005 CONFIRMÉE sous Claude. |
| **BUG-V7.1-007** | Mauvais mapping subcategory | "diesel" mappé sur "gasoline" (essence) ; "compostage" mappé sur "waste_landfill" (décharge) — facteurs d'émission incorrects. | ❌ | N3 | Affecte fiabilité du bilan. |
| **BUG-V7.1-008** | Year 2025 au lieu de 2026 | `create_carbon_assessment(year=2025)` alors que current_date=2026-04-28. | ⚠️ | N3 | Mineur mais traçable. |

## 3. Validation BUG-V6-005 — Plan d'action persisté

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-PLAN-01 | Générer plan via chat | "génère mon plan d'action" → ≥10 actions | ❌ | N4 | **BUG-V7.1-009 (régression BUG-V7-007)** : `generate_action_plan` appelé 9× (3 cycles × 3 retries) tous en erreur 500 "guard LLM echoue apres retry". Claude affiche message "Le service rencontre une erreur technique persistante (500)". Sous MiniMax = json_parse_failed ; sous Claude = guard LLM échoue. Bug architectural CONFIRMÉ : la validation runtime ≥10 actions + champs requis force des contraintes que même Claude ne peut satisfaire. |
| T-V7-PLAN-02 | Persistance BDD | `SELECT COUNT(*) FROM action_plans WHERE user_id=...` → ≥10 lignes | ❌ | N4 | `SELECT COUNT(*) FROM action_plans → 0`. Aucune action persistée. |
| T-V7-PLAN-03 | Tool valide ≥10 actions | LLM force batch complet ≥10 sinon erreur | ❌ | N4 | Validation runtime §4nonies REJETTE systématiquement les sorties Claude (3 retries) — le seuil est trop strict pour le LLM. |
| T-V7-PLAN-04 | Champs requis tous présents | title, category, due_date, priority pour chaque action | 🚫 | — | Bloqué (aucune action générée). |
| T-V7-PLAN-05 | /action-plan affiche actions | Timeline + 6 catégories filtrables | 🚫 | — | Bloqué. |
| T-V7-PLAN-06 | Marquer action fait | Toggle done → progression MAJ globale + catégorie | 🚫 | — | Bloqué. |
| T-V7-PLAN-07 | Action intermediary_contact | Coordonnées intermédiaire snapshot affichées | 🚫 | — | Bloqué. |

## 4. Validation BUG-V6-004 + V6-009 — Credit score

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-CREDIT-01 | Démarrer scoring chat | "évalue ma solvabilité" → routing credit_node | ⚠️ | N3 | Routing semble OK (réponse contextualisée crédit) mais Claude refuse d'invoquer le tool. |
| T-V7-CREDIT-02 | Tool generate_credit_score appelé | Pas de fallback manuel | ❌ | N4 | **BUG-V7.1-010 (régression BUG-V7-008)** : Claude prétend "Cette fonctionnalité n'est pas disponible via mon interface", "outil dédié qui n'est pas inclus dans mes outils actuels", redirige vers /credit-score. AUCUN appel à `generate_credit_score` (0 tool_call_logs). Régression CONFIRMÉE — switch LLM ne résout PAS. |
| T-V7-CREDIT-03 | Score persisté BDD | `SELECT * FROM credit_scores WHERE user_id=...` → 1 ligne complète | ❌ | N4 | `SELECT COUNT(*) FROM credit_scores → 0`. |
| T-V7-CREDIT-04 | Score chat ↔ BDD ↔ dashboard | 3 valeurs identiques (pas 26 vs 58) | 🚫 | — | Bloqué (aucun score). |
| T-V7-CREDIT-05 | Idempotence mensuelle | 2ème scoring même mois → UPDATE pas INSERT | 🚫 | — | Bloqué. |
| T-V7-CREDIT-06 | /credit-score affichage | Score solvabilité + impact + détails | ⚠️ | — | Page accessible mais affiche état vide "Pas encore de score" — bouton "Générer mon score" présent. À tester manuellement. |
| **BUG-V7.1-011** | Leak caractères cyrilliques | "outil dédié qui n'est pas **включен** dans mes outils actuels" — mot russe (вкл = "inclus") au lieu de "inclus" en FR. | ❌ | N4 | **Régression BUG-V6-010 SOUS CLAUDE** — la note V7.1 disait "Claude natif multilingue, leaks attendus = 0". RÉFUTÉ. |

## 5. Validation BUG-V6-011 — Profilage company

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-PROFILE-01 | Profiling chat AgriVert | "AgriVert Sarl, Agriculture, 15 employés, Sénégal" → company créée | ⚠️ | N3 | **BUG-V7.1-001** : Claude Sonnet 4.6 appelle `update_company_profile` 3× avec extraction partielle. Seul `employee_count=15` extrait (2/3 appels). `sector="Agriculture"` et `city="Dakar"` MENTIONNÉS EXPLICITEMENT mais NON extraits (null). Hypothèse "switch LLM résout extraction NLP" partiellement RÉFUTÉE — Claude ne fait pas mieux que MiniMax sur sector/city. Bug architectural prompt update_company_profile. |
| T-V7-PROFILE-02 | BDD company | `SELECT name, sector, country FROM companies WHERE user_id=...` → AgriVert/Agriculture/Sénégal | ⚠️ | N3 | BDD réelle : `company_profiles` (pas `companies`). `name=AgriVert Sarl` ✅, `country=Sénégal` ✅ (signup form), `employee_count=15` ✅ (tool), MAIS `sector=null` ❌, `city=null` ❌. |
| T-V7-PROFILE-03 | /profile affiche bonnes données | Page profil cohérente avec BDD | ✅ | — | Page /profile cohérente avec BDD : AgriVert Sarl, Sénégal, 15 employés affichés. Sector "Non renseigné" cohérent avec null. Progression 19% global, 38% Identité, 0% ESG. |
| T-V7-PROFILE-04 | Rejet whitespace-only | PATCH `{"company_name":"   "}` → erreur validation | ❌ | N4 | **BUG-V7.1-003 (régression BUG-V6-011)** : `PATCH /api/company/profile` accepte `"   "` ET `""` avec HTTP 200, écrase la valeur "AgriVert Sarl" → "". Le fix BUG-V6-011 ne s'applique qu'au tool LLM, pas à l'endpoint REST. Schéma Pydantic `CompanyProfileUpdate` ne valide pas whitespace/empty. |
| T-V7-PROFILE-05 | Spinbutton employés | Modifier 25 → 42 → ✓ → F5 → 42 persisté | ✅ | — | UI : 15 → 42 ✓, F5, valeur 42 affichée + persistée en BDD (`SELECT employee_count → 42`). |

## 6. Validation cascade attendue — Dashboard avec données

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-DASH-01 | Carte ESG avec score réel | Score /100 affiché | ❌ | N3 | "—" / Aucune donnée. Aucune évaluation ESG n'a pu être complétée (cascade bugs LLM). |
| T-V7-DASH-02 | Carte Carbone avec total | tCO2e affiché (cascade post-V6-002 + V7-006) | ⚠️ | N3 | Carte affiche `17/100` et "Bilan 2025 — 16.9 tCO2e" MALGRÉ status=in_progress en BDD. Dashboard tolère et affiche, mais incohérent : "Bilan carbone complété" en activité récente alors que `status='in_progress'` BDD. |
| T-V7-DASH-03 | Carte Credit avec score | Score affiché | ❌ | N3 | "—" / Aucune donnée (cascade BUG-V7.1-010). |
| T-V7-DASH-04 | Badge first_carbon | Premier bilan → badge débloqué | ❌ | N4 | **BUG-V7.1-013 (régression BUG-V7-010)** : Bilan existe en BDD mais badge "Premier bilan carbone" 🔒 Verrouillé. Hook gamification ne déclenche pas pour status=in_progress. |
| T-V7-DASH-05 | Badge esg_above_50 | Score > 50 → badge | 🚫 | — | Bloqué (pas d'ESG). |
| T-V7-DASH-06 | Badge first_application | Premier dossier → badge | 🚫 | — | Bloqué (pas de dossier). |
| T-V7-DASH-07 | Badge first_intermediary_contact | Premier contact → badge | 🚫 | — | Bloqué (pas de contact). |
| T-V7-DASH-08 | Badge full_journey | Tous modules complétés → badge | 🚫 | — | Bloqué. |
| **BUG-V7.1-014** | Cohérence "Bilan complété" vs BDD in_progress | Activité récente affiche "Bilan carbone complété" mais BDD `status='in_progress'` (BUG-V7.1-005). Dashboard se base sur la présence de total_emissions_tco2e ; il faut un check sur status. | ❌ | N3 | Cascade BUG-V7.1-005. |

## 7. Validation cascade attendue — BUG-V6-010 leaks langue

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-LANG-01 | Chat 10 messages variés | 100% FR, 0 caractère chinois/cyrillique/arabe | ❌ | N4 | Scan messages : 1 mot cyrillique détecté ("включен"). Hypothèse "Claude natif → 0 leak" RÉFUTÉE. |
| T-V7-LANG-02 | Routing ESG langue | Messages ESG 100% FR | 🚫 | — | Pas testé (cascade ESG bloquée). |
| T-V7-LANG-03 | Routing Carbone langue | Messages Carbone 100% FR | ✅ | — | Réponses carbone 100% FR, pas de leak. |
| T-V7-LANG-04 | Routing Financement langue | Messages Financement 100% FR | 🚫 | — | Non testé. |
| T-V7-LANG-05 | Routing Credit langue | Messages Credit 100% FR | ❌ | N4 | Réponse credit_node contient "включен" (cyrillique). Voir BUG-V7.1-011. |
| T-V7-LANG-06 | Routing Plan langue | Messages Plan 100% FR | ✅ | — | Message d'erreur 500 plan d'action 100% FR (mais c'est un message backend technique, pas LLM). |

## 8. Parcours bout-en-bout MVP complet

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-E2E-01 | Inscription + onboarding | Compte créé + entreprise profilée via chat | ⚠️ | N3 | Compte créé OK. Profil extraction NLP partielle (BUG-V7.1-001) — sector, city manqués. |
| T-V7-E2E-02 | ESG 30 critères → score → /esg/results | Parcours complet débloqué | 🚫 | — | Bloqué — 30 critères via chat trop coûteux à exécuter dans le contexte des bugs LLM cumulatifs. |
| T-V7-E2E-03 | Carbone bilan complet → /carbon/results | Total tCO2e + visualisations | ⚠️ | — | Page accessible avec données partielles (3/4 catégories, status in_progress, équivalences FCFA/plan/benchmark manquants — voir T-V7-C-05). |
| T-V7-E2E-04 | Credit score → /credit-score | Score persisté affiché | ❌ | N4 | Bloqué (BUG-V7.1-010 : Claude refuse d'invoquer le tool). |
| T-V7-E2E-05 | Financement catalogue + intermédiaires | 12 fonds + 14 intermédiaires accessibles | ✅ | — | 12 fonds visibles (GCF, FEM, BOAD, BIDC, SUNREF, FNDE, IFC, BCEAO, etc.), score compatibilité uniforme à 50 (pas de matching personnalisé car ESG=null). |
| T-V7-E2E-06 | Application via chat → édition | Dossier créé + éditable | ⚠️ | N3 | **BUG-V7.1-015** : Claude prétend "Je ne trouve pas SUNREF dans les résultats de recherche automatique" alors que SUNREF est PRÉSENT en BDD et visible sur /financing. Outil RAG/recherche fonds défaillant. Question interactive affichée mais radios `disabled=true` — UX bloquée. |
| T-V7-E2E-07 | Plan d'action ≥10 actions | Persisté + progression | ❌ | N4 | Bloqué (BUG-V7.1-009). |
| T-V7-E2E-08 | Rapport ESG PDF | Généré + preview + download | ❌ | N4 | Bloqué (BUG-V7.1-012 libgobject env). |
| T-V7-E2E-09 | Dashboard cohérent | 4 cartes + 5 badges | ❌ | N3 | 1/4 cartes avec données (Carbone seul, partiel), 0/5 badges débloqués (cascade BUG-V7.1-013). |
| T-V7-E2E-10 | Multi-tour ESG → Financement | Routing change_module fonctionne | ⚠️ | — | Multi-tour observé OK (carbone → plan → credit → application = 4 modules transitionnés). MAIS plusieurs noeuds échouent à invoquer leurs tools. |

## 9. Performance & stabilité

| ID | Test | Résultat attendu | Statut | Sévérité | Notes |
|----|------|------------------|--------|----------|-------|
| T-V7-PERF-01 | Console erreurs JS parcours complet | 0 erreur rouge sur 30+ navigations | ⚠️ | — | 1 erreur 404 ("Failed to load resource"), 3 warnings Vue Router "No match for /chat". Console relativement propre (warnings expérimentaux ignorables). |
| T-V7-PERF-02 | Network 5xx | Aucun 5xx (sauf simul) | ❌ | N4 | **9 erreurs HTTP 500** observées sur `/api/chat/messages` cycle `generate_action_plan` (cascade BUG-V7.1-009). Non-simul. |
| T-V7-PERF-03 | Génération PDF <60s | Pas de timeout production | 🚫 | — | Bloqué (env libgobject). |
| T-V7-PERF-04 | Latence chat Claude vs MiniMax | Mesurer temps moyen réponse 5 messages | ℹ️ | — | Latence côté tool calls (BDD) : avg 35 ms, max 117 ms (13 appels success). Latence chat E2E (LLM streaming) : ~8-30s par réponse, inclut multiples retries génération. Observation qualitative : Claude PLUS LENT que MiniMax sur réponses longues — coût LLM ~10x supérieur sans amélioration de qualité (cf. bugs persistants). |

---

## Synthèse bugs Vague 7.1 — exécution 2026-04-28

| ID bug | Test source | Sévérité | Description | Causal LLM ? | Status |
|--------|-------------|----------|-------------|--------------|--------|
| BUG-V7.1-001 | T-V7-PROFILE-01 | N3 | Extraction NLP profil partielle (employee_count OK, sector/city/manqués) sous Claude. Régression BUG-V7-001. | OUI (prompt) | ouvert |
| BUG-V7.1-002 | T-V7-PROFILE-04 | N4 | `PATCH /api/company/profile` accepte whitespace/empty company_name. Régression BUG-V6-011 côté REST. | NON (Pydantic) | ouvert |
| BUG-V7.1-004 | T-V7-C-01 | N4 | Claude HALLUCINE "secteur=services" pour rejeter agriculture, alors qu'AgriVert est en Agriculture et le user mentionne "riz pluvial". | OUI (LLM) | ouvert |
| BUG-V7.1-005 | T-V7-C-04 | N4 | finalize_carbon_assessment JAMAIS appelé même après "Oui finalise". Régression BUG-V7-006. | OUI (LLM ignore tool) | ouvert |
| BUG-V7.1-006 | T-V7-C-01 | N4 | save_emission_entry subcategory=null systématique (4/4 appels). Régression BUG-V7-005. | OUI (LLM) | ouvert |
| BUG-V7.1-007 | T-V7-C-01 | N3 | Mauvais mapping subcategory côté backend ("diesel"→"gasoline", "compostage"→"waste_landfill"). | NON (heuristique) | ouvert |
| BUG-V7.1-008 | T-V7-C-01 | N3 | Year=2025 alors que current_date=2026. | OUI (LLM) | ouvert |
| BUG-V7.1-009 | T-V7-PLAN-01 | N4 | generate_action_plan échoue 9× "guard LLM echoue apres retry". Régression BUG-V7-007. | NON (validation trop stricte) | ouvert |
| BUG-V7.1-010 | T-V7-CREDIT-02 | N4 | Claude refuse d'invoquer generate_credit_score, prétend "outil non disponible". Régression BUG-V7-008. | OUI (LLM) | ouvert |
| BUG-V7.1-011 | T-V7-LANG-05 | N4 | Leak cyrillique "включен" dans réponse FR Claude credit_node. Régression BUG-V6-010 censée résolue. | OUI (LLM) | ouvert |
| BUG-V7.1-012 | T-V7-PDF-01 | N4 (env) | OSError libgobject-2.0-0 WeasyPrint macOS. Régression BUG-V7-003 (préreq env non appliqué). | NON (env système) | ouvert |
| BUG-V7.1-013 | T-V7-DASH-04 | N4 | Badge `first_carbon` non débloqué malgré bilan carbone existant (status in_progress). Régression BUG-V7-010. | NON (gamification) | ouvert |
| BUG-V7.1-014 | T-V7-DASH-02 | N3 | Dashboard affiche "Bilan complété" pour assessment status=in_progress. Cascade BUG-V7.1-005. | NON (logique) | ouvert |
| BUG-V7.1-015 | T-V7-E2E-06 | N3 | Claude prétend ne pas trouver SUNREF en BDD alors que présent + visible /financing. Outil RAG/recherche fonds défaillant. | OUI (RAG/LLM) | ouvert |

## Critère de "verte" Vague 7.1 — déclencheur retrospective Epic 10

**Critères obligatoires (gate)** :
- Section 1 : 100% ✅ (PDF généré — dépend env libgobject)
- Section 8 : 100% ✅ (parcours MVP bout-en-bout)
- Section 6 : ≥80% ✅ (dashboard cascade)
- Section 7 : 100% ✅ (langue FR stricte)
- 0 bug N3+ ouvert non déféré
- 0 bug N4 nouveau

## Critères décisionnels post-V7.1

**Si V7.1 verte** :
- ✅ Hypothèse confirmée : MiniMax était le facteur causal
- → Adopter Claude Sonnet 4.6 pour MVP, ajuster budget LLM (+10x vs MiniMax = 5000€/mois cap au lieu de 500€)
- → Retrospective Epic 10 + transition Phase 1
- → Capitaliser leçon §4decies : "Provider LLM critique pour tool calling — tester en early stage"

**Si V7.1 toujours rouge (≥3 bugs persistent)** :
- ❌ Hypothèse réfutée : bugs sont architecturaux (prompts, tools, validation, schémas)
- → Cycle correctifs architecturaux (extraction NLP backend déterministe, fallback templates, etc.)
- → Reconsidérer scope MVP (drop modules trop fragiles)
- → Replanifier sprint v3

**Si V7.1 partielle (1-2 bugs persistent)** :
- ⚠️ Hypothèse partiellement confirmée
- → Identifier bugs résiduels, corriger ciblé
- → V7.2 validation finale

---

## VERDICT V7.1 — exécuté 2026-04-28 par agent-browser --headed

**Résultat : ROUGE — Gate non franchi, Hypothèse RÉFUTÉE.**

### Comparaison V7.0 (MiniMax) vs V7.1 (Claude Sonnet 4.6)

| Bug V7.0 | Status sous Claude V7.1 | Décision |
|----------|-------------------------|----------|
| BUG-V7-001 (extraction NLP profil) | ❌ PERSISTE (BUG-V7.1-001) | Bug architectural |
| BUG-V7-002 (validator Pydantic whitespace) | ❌ PERSISTE (BUG-V7.1-002) | Bug backend (attendu) |
| BUG-V7-003 (libgobject env) | ❌ PERSISTE (BUG-V7.1-012) | Env système (attendu) |
| BUG-V7-004 (schéma défensif report) | non testé (cascade) | — |
| BUG-V7-005 (subcategory=null) | ❌ PERSISTE (BUG-V7.1-006) | Bug architectural |
| BUG-V7-006 (finalize jamais appelé) | ❌ PERSISTE (BUG-V7.1-005) | Bug architectural |
| BUG-V7-007 (action plan json_parse) | ❌ MUTATION (BUG-V7.1-009) | Validation runtime trop stricte |
| BUG-V7-008 (credit guided_tour) | ❌ MUTATION (BUG-V7.1-010) | Bug architectural |
| BUG-V7-009 (dashboard ignore in_progress) | ❌ PERSISTE (BUG-V7.1-014) | Bug logique backend (attendu) |
| BUG-V7-010 (badge esg_above_50) | ❌ PERSISTE (BUG-V7.1-013) | Bug gamification (attendu) |

**Bugs LLM-causaux attendus comme résolus sous Claude (5/10) : 0 résolus.**
**Nouveaux bugs sous Claude (5)** :
- BUG-V7.1-004 hallucination secteur "services"
- BUG-V7.1-007 mapping subcategory côté backend
- BUG-V7.1-008 year=2025 au lieu de 2026
- BUG-V7.1-011 leak cyrillique "включен" (RÉGRESSION cf. note plan "Claude natif → 0 leak")
- BUG-V7.1-015 SUNREF non trouvé par RAG/recherche fonds

### Conclusion business

❌ **Hypothèse "MiniMax = facteur causal" RÉFUTÉE.**

Claude Sonnet 4.6 ne fait PAS mieux que MiniMax sur les bugs LLM-causaux :
- Extraction NLP : partielle dans les deux cas
- Tool calling : Claude a aussi de gros refus (refus d'appeler generate_credit_score, hallucination secteur, finalize jamais appelé)
- Production JSON validateur : échec systématique sous Claude (validation runtime §4nonies trop stricte)
- Multilinguisme : Claude leak du cyrillique malgré nature "native multilingue"

**Décisions recommandées Phase 1** :
1. NE PAS adopter Claude Sonnet 4.6 comme remplacement MiniMax — coût 10× sans bénéfice qualité.
2. **Cycle correctifs architecturaux** prioritaire :
   - Refactor extraction profil : déterministe NLP backend OU prompt few-shot ultra-explicite
   - Relâcher validation runtime action_plan (≥10 → ≥5 ou validation post-batch incrémentale)
   - Forcer tool calling credit_score via routing déterministe (pas via décision LLM)
   - Mapping subcategory carbone côté backend exhaustif (riz_pluvial, compost, diesel, etc.)
   - Validator Pydantic whitespace côté REST (BUG-V6-002 cible REST en plus du tool)
3. Préreq env libgobject à intégrer dans `setup.sh` ou docker-compose.
4. Reconsidérer scope MVP — drop modules trop fragiles ou les marquer "expérimental".
5. Replanifier sprint v3 avec les 14 bugs ouverts comme backlog.

### Métriques exécution V7.1

- Tests exécutés : ~50/56 (6 bloqués cascade)
- ✅ verts : 6
- ⚠️ partiels : 9
- ❌ rouges : 17
- 🚫 bloqués : 18
- Bugs ouverts : 14 (8 N4)
- Couverture modules : Profile, Carbone, Plan, Credit, Dashboard, Langue, Financement (catalogue), Application (chat) — ESG et PDF non couverts (cascade).

## Politique zéro tolérance Vague 7.1

- Toute régression sur fix antérieur → N4 automatique (hotfix immédiat)
- Tests BDD avec query psql concrète obligatoires
- Compteurs runtime documentés à chaque test
- **Mesurer latence Claude** (T-V7-PERF-04) pour décision business coût/perf

---

## ARCHIVE — Résultats V7.0 (MiniMax) — 2026-04-28

**Bugs détectés sous MiniMax (10 ouverts, 4 N4)** — archivés pour comparaison V7.1 :

| ID bug | Sévérité | Description | Causal LLM ? |
|--------|----------|-------------|--------------|
| BUG-V7-001 | N4 | LLM update_company_profile 4× args null | OUI (extraction NLP) |
| BUG-V7-002 | N3 | Validator whitespace côté schema Pydantic manquant | NON (backend) |
| BUG-V7-003 | N4 (env) | OSError libgobject WeasyPrint macOS | NON (env système) |
| BUG-V7-004 | N3 | Service report 'int' object no attribute 'get' | NON (schéma défensif backend) |
| BUG-V7-005 | N3 | save_emission_entry agriculture subcategory=null | OUI (mapping LLM) |
| BUG-V7-006 | N3 | finalize_carbon_assessment jamais appelé | OUI (LLM ignore tool) |
| BUG-V7-007 | N4 | Plan d'action json_parse_failed × 2 retries | OUI (JSON malformé LLM) |
| BUG-V7-008 | N3 | credit_node guided_tour au lieu de scoring | OUI (LLM divergence prompt) |
| BUG-V7-009 | N3 | Dashboard ignore in_progress (cascade V7-006) | NON (logique backend) |
| BUG-V7-010 | N3 | Badge esg_above_50 hook gamification | NON (logique backend) |

**Si bugs causal LLM disparaissent sous Claude (V7.1)** :
- BUG-V7-001 ✅
- BUG-V7-005 ✅
- BUG-V7-006 ✅
- BUG-V7-007 ✅
- BUG-V7-008 ✅
→ 5/10 bugs résolus par switch provider = **hypothèse confirmée**

**Bugs résiduels attendus même sous Claude (architecturaux)** :
- BUG-V7-002 (validator Pydantic)
- BUG-V7-003 (env libgobject)
- BUG-V7-004 (schéma défensif)
- BUG-V7-009 (logique dashboard)
- BUG-V7-010 (hook gamification)
→ 5/10 bugs nécessitent fix architectural indépendamment du LLM

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
| 2026-04-24 | V4 corrections | MiniMax | 1 (V2-003) | 2 (V4-001 + V4-002) |
| 2026-04-24 | V5 partial | MiniMax | 3 (V5-001/002/003) | 2 |
| 2026-04-25 | V5 corrections | MiniMax | 0 | 3 |
| 2026-04-25 | V6 | MiniMax | 12 | 3 |
| 2026-04-28 | V6 corrections | MiniMax | 4 cascade + 2 déférés | 6 + leçon §4nonies |
| 2026-04-28 | V7.0 | MiniMax | 10 (4 N4) — gate non franchi | 6 + leçon §4nonies |
| 2026-04-28 | V7.1 reset | **Claude Sonnet 4.6** | 14 (8 N4) — gate non franchi, hypothèse RÉFUTÉE | 6 + leçon §4nonies |
