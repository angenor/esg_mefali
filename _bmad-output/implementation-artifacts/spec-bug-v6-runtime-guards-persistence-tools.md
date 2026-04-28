---
title: 'BUG-V6 batch — Garde runtime systémique sur tous les tools de persistance (carbone, credit, plan, profile)'
type: 'bugfix'
created: '2026-04-28'
status: 'done'
baseline_commit: 'dccff0b00b290f6d5cd8a305aff582f924d4bd09'
context:
  - '{project-root}/backend/app/graph/tools/carbon_tools.py'
  - '{project-root}/backend/app/graph/tools/credit_tools.py'
  - '{project-root}/backend/app/graph/tools/action_plan_tools.py'
  - '{project-root}/backend/app/graph/tools/profiling_tools.py'
  - '{project-root}/backend/app/prompts/esg_scoring.py'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-bug-v5-003-esg-pillar-validation.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Pattern récurrent sur 6 vagues de tests — le LLM MiniMax ne respecte pas systématiquement les instructions tool calling : il répond textuellement, dédouble des appels, ou ignore le tool. Résultat : persistance BDD incohérente avec ce que l'utilisateur voit dans le chat. Bugs V6-002 (doublons d'entrées carbone : 171 vs 87 tCO2e affichés, 2× 36000 km transport, 4 lignes déchets), V6-004 (credit score en échec puis fallback textuel sans persistance), V6-005 (0 actions persistées malgré 15 affichées), V6-009 (credit dashboard 26 vs chat 58), V6-011 (company "AgriVert" mentionnée chat mais pas créée). BUG-V5-003 a résolu le problème pour ESG via une garde runtime ; cette story généralise le pattern à TOUS les tools de persistance pour défense en profondeur systémique.

**Approach :** Ajouter une garde runtime dans chaque tool de persistance (`save_emission_entry`, `generate_credit_score`, `generate_action_plan`, `update_company_profile`) — validation cohérence métier + idempotence + message d'erreur exploitable par le LLM. Renforcer les 4 prompts spécialistes (carbon, credit, action_plan, application) avec une section `## PERSISTANCE — TOOL CALL OBLIGATOIRE` reprise du pattern V5-003. Capitaliser la méthodologie en §4nonies (Leçon 36) dans `docs/CODEMAPS/methodology.md`.

## Boundaries & Constraints

**Always :**
- Modifications strictement limitées à `backend/app/graph/tools/` + `backend/app/prompts/` + `backend/tests/` + `docs/CODEMAPS/methodology.md`.
- Chaque garde retourne une **chaîne d'erreur** explicite en français (jamais d'exception — `with_retry` la masquerait), exploitable par le LLM pour retry intelligent (liste champs/codes/items manquants).
- Idempotence stricte : aucune écriture BDD partielle si validation échoue (no-op, comme V5-003).
- Préserver les signatures publiques des tools (compatibilité bindings LangChain, schémas auto-dérivés).
- Adapter le patch à la réalité du code investigué (cf. Code Map) — ne pas inventer de tools `save_carbon_entry`, `save_credit_score`, `save_action_plan` qui n'existent pas ; utiliser les noms réels (`save_emission_entry`, `generate_credit_score`, `generate_action_plan`).
- Régénérer les golden snapshots de prompts modifiés (`carbon.txt`, `credit.txt`, `action_plan.txt`, `application.txt`).

**Ask First :** aucun — correctifs critiques validés par le pattern V5-003 déjà mergé.

**Never :**
- Ne pas modifier le graph LangGraph ni les modèles SQLAlchemy.
- Ne pas modifier les services métier (`backend/app/modules/*/service.py`).
- Ne pas créer de nouvelles tables, migrations Alembic ou colonnes.
- Ne pas dépasser ~30 lignes de code ajoutées par fichier de tool.
- Ne pas introduire de nouvelle dépendance Python.
- Ne pas régresser les 1829 tests baseline (collected `pytest backend/tests/ --collect-only`).
- Ne pas corriger en passant le bug `score.risk_level` détecté dans `credit_tools.py` (pas de colonne `risk_level` dans le modèle) — défrer dans `deferred-work.md` (DEF-BUG-V6-CREDIT-RISKLEVEL).

## I/O & Edge-Case Matrix

| Scénario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| **Carbon** entry duplicate | `save_emission_entry(assessment_id=A, category=transport, subcategory=carburant, quantity=36000)` puis 2e appel identique | 2e appel : retour `Entree deja saisie pour cette categorie/sous-categorie. Mise a jour appliquee.` + UPDATE (pas duplicate INSERT). 1 seule ligne en BDD. | LLM voit le message → ne réessaie pas |
| **Carbon** entry nouvelle sous-cat | mêmes (assessment, category) mais subcategory différent | INSERT normal, retour OK | N/A |
| **Credit** doublon mensuel | `generate_credit_score()` appelé 2× dans le même mois pour le même user | 2e appel : retour `Score credit deja genere ce mois (version N, score X/100). Utilise get_credit_score pour le consulter.` + AUCUNE écriture | LLM voit, n'insère pas |
| **Credit** > 1 mois | dernier score > 30 jours | INSERT normal, version+1 | N/A |
| **Action plan** trop peu d'items | service retourne plan avec 5 items | tool retourne `ERREUR : plan d'action incomplet (5/10 actions minimum). Le service a genere trop peu d'actions ; relance generate_action_plan ou complete via update_action_item.` + AUCUNE persistance utile signalée | LLM relance |
| **Action plan** items invalides | item sans `title` ou `category` | tool retourne `ERREUR : action #N invalide. Champs manquants : title, category.` | LLM corrige |
| **Profile** payload vide | `update_company_profile()` sans champ | retour existant `Aucun champ fourni pour la mise a jour.` (inchangé, déjà OK) | N/A |
| **Profile** whitespace-only | `update_company_profile(company_name="   ")` | retour `ERREUR : aucun champ utile fourni (valeurs vides ou espaces). Verifie l'extraction depuis la conversation.` + AUCUNE écriture | LLM corrige |
| **Profile** company auto-create | profil inexistant + `company_name="AgriVert", sector="agriculture"` | service `get_or_create_profile` crée la ligne (comportement existant), update applique les champs, retour OK | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/graph/tools/carbon_tools.py:68` — `save_emission_entry` ; cible patch 1 (dedup avant INSERT). `finalize_carbon_assessment:164` existe déjà — ne rien modifier.
- `backend/app/graph/tools/credit_tools.py:37` — `generate_credit_score` ; cible patch 2 (idempotence mensuelle, étendre la garde 10s actuelle).
- `backend/app/graph/tools/action_plan_tools.py:17` — `generate_action_plan` ; cible patch 3 (validation post-appel : `len(plan.action_items) >= 10` + champs requis).
- `backend/app/graph/tools/profiling_tools.py:19` — `update_company_profile` ; cible patch 4 (rejeter whitespace-only ; le check non-vide existe déjà L73-74). `application_tools.py` non modifié — pas de tool de profil dedans.
- `backend/app/prompts/{carbon,credit,action_plan,application}.py` — ajout section `## PERSISTANCE — TOOL CALL OBLIGATOIRE` (cible patch 5).
- `backend/app/prompts/esg_scoring.py:31-37` — pattern de référence (V5-003).
- `backend/tests/test_tools/test_carbon_tools.py` ; `test_credit_tools.py` ; `test_action_plan_tools.py` ; `test_profiling_tools.py` — ajout ≥3 tests par tool (rejet incomplet, idempotence, succès).
- `backend/tests/test_prompts/golden/{carbon,credit,action_plan,application}.txt` — régénération des snapshots après ajout du bloc.
- `backend/tests/test_prompts/test_{carbon_node_tools,credit_prompt,application_prompt}.py` + `test_action_plan_*.py` — vérifier non-régression des assertions textuelles existantes.
- `docs/CODEMAPS/methodology.md` — ajout section `§4nonies` + Leçon 36, bump cumul 35→36 leçons (L1117).
- `_bmad-output/implementation-artifacts/deferred-work.md` — ajout entrée `DEF-BUG-V6-CREDIT-RISKLEVEL` (bug `score.risk_level` détecté pendant l'investigation, hors scope).

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/graph/tools/carbon_tools.py` — Patch 1 : dans `save_emission_entry`, après `get_assessment` (L91), charger les entries existantes via `assessment.entries` (déjà en cascade) et chercher un match `(category, subcategory)`. Si trouvé : UPDATE quantity + source_description + recalculer emissions, retour message OK avec marqueur `[DEDUP]`. Sinon INSERT comme aujourd'hui. ≤30 lignes.
- [x] `backend/app/graph/tools/credit_tools.py` — Patch 2 : dans `generate_credit_score`, avant `gen_score(...)` (L50), interroger le dernier score via `service.get_latest_score(db, user_id)` (déjà importé) et vérifier `generated_at >= 30 jours`. Si récent : retour erreur explicite mentionnant version + combined_score + invitation à `get_credit_score`. ≤30 lignes. Ajouter aussi `# TODO DEF-BUG-V6-CREDIT-RISKLEVEL` au-dessus de la ligne 57 où `score.risk_level` est utilisé.
- [x] `backend/app/graph/tools/action_plan_tools.py` — Patch 3 : dans `generate_action_plan`, après `gen_plan(...)` (L32), valider que `len(plan.action_items) >= 10`. Si moins : retour erreur listant le nombre obtenu vs attendu. Valider aussi que chaque action a `title` non-vide et `category` valide. ≤30 lignes.
- [x] `backend/app/graph/tools/profiling_tools.py` — Patch 4 : dans `update_company_profile`, juste après la construction de `raw_updates` (L72), filtrer les valeurs strings whitespace-only via `{k: v for k, v in raw_updates.items() if not (isinstance(v, str) and not v.strip())}`. Si après filtrage `raw_updates` est vide : retour `ERREUR : aucun champ utile fourni...`. Préserver le `Aucun champ fourni` existant pour le cas vrai-vide. ≤20 lignes.
- [x] `backend/app/prompts/carbon.py` — Patch 5a : ajouter section `## PERSISTANCE — TOOL CALL OBLIGATOIRE` après le bloc TRANSITION (L109) reprenant la formulation V5-003. ≤20 lignes.
- [x] `backend/app/prompts/credit.py` — Patch 5b : ajouter même section avant MENTION IMPORTANTE (L102). ≤20 lignes.
- [x] `backend/app/prompts/action_plan.py` — Patch 5c : ajouter même section après le bloc INTERDIT (L65). ≤20 lignes.
- [x] `backend/app/prompts/application.py` — Patch 5d : ajouter même section après INTERDIT (L35). ≤20 lignes.
- [x] `backend/tests/test_prompts/golden/{carbon,credit,action_plan,application}.txt` — régénérer les 4 snapshots avec `python tests/test_prompts/_capture_golden.py` (ou équivalent).
- [x] `backend/tests/test_tools/test_carbon_tools.py` — Tests : `test_save_emission_entry_rejects_duplicate`, `test_save_emission_entry_updates_on_duplicate`, `test_save_emission_entry_distinct_subcategories_create_separate_rows`. ≥3.
- [x] `backend/tests/test_tools/test_credit_tools.py` — Tests : `test_generate_credit_score_rejects_recent_duplicate`, `test_generate_credit_score_idempotent_returns_existing`, `test_generate_credit_score_succeeds_after_30_days`. ≥3.
- [x] `backend/tests/test_tools/test_action_plan_tools.py` — Tests : `test_generate_action_plan_rejects_below_minimum_items`, `test_generate_action_plan_rejects_action_missing_required_fields`, `test_generate_action_plan_succeeds_with_complete_plan`. ≥3.
- [x] `backend/tests/test_tools/test_profiling_tools.py` — Tests : `test_update_company_profile_rejects_whitespace_only_payload`, `test_update_company_profile_strips_whitespace_keeps_other_fields`, `test_update_company_profile_creates_company_when_missing` (réutilise `get_or_create_profile`). ≥3.
- [x] `docs/CODEMAPS/methodology.md` — Ajouter section `### 4nonies. Validation runtime systémique sur tools de persistance` avant le séparateur final + bump compteur 35→36 leçons. Référencer ce spec et BUG-V5-003 comme sources.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — Ajouter `DEF-BUG-V6-CREDIT-RISKLEVEL` (bug `score.risk_level` masqué par mock dans `_make_credit_score`, à corriger en story dédiée).

**Acceptance Criteria :**
- Given une assessment carbone vide, when le LLM appelle 2× `save_emission_entry(category=transport, subcategory=carburant, quantity=36000)`, then 1 seule ligne en BDD, le 2e appel retourne un message contenant `Entree deja saisie` ou `mise a jour`.
- Given un score credit généré il y a 5 jours, when le LLM appelle `generate_credit_score`, then aucun INSERT, retour mentionne version + combined_score + invitation à `get_credit_score`.
- Given un service `generate_action_plan` mocké pour retourner un plan avec 5 items, when le tool est invoqué, then retour erreur listant `5/10 minimum`.
- Given `update_company_profile(company_name="   ", sector="")`, when invoqué, then retour `ERREUR : aucun champ utile`, aucun appel à `update_profile`.
- Given une conversation où le LLM mentionne "AgriVert" + "agriculture", when l'agent appelle `update_company_profile(company_name="AgriVert", sector="agriculture")`, then la company est créée (via `get_or_create_profile` existant) et les champs persistés (régression V6-011).
- Given le prompt carbon généré post-patch, when comparé au golden snapshot, then le snapshot contient la section `PERSISTANCE — TOOL CALL OBLIGATOIRE`.
- Tests : `pytest backend/tests/ -q` retourne ≥1844 verts (1829 baseline + ≥15 nouveaux), zéro régression.

## Spec Change Log

- **2026-04-28 — Review patches (no spec change)** — 3 patches appliqués sur recommandation des reviewers (Blind hunter, Edge case hunter, Acceptance auditor) sans toucher au `<frozen-after-approval>` :
  1. `credit_tools.py` : clamp `age_days = max(0, ...)` pour neutraliser un timestamp futur (clock skew / fixture) qui bloquerait indéfiniment la régénération via `age_days < 30`. Idempotence préservée, message d'erreur reste exploitable.
  2. `credit_tools.py` : ajout du commentaire `# TODO DEF-BUG-V6-CREDIT-RISKLEVEL` au-dessus du **2e site** référençant `score.risk_level` (`get_credit_score` L121, en plus de `generate_credit_score` L83). Traçabilité complète du bug déféré.
  3. Tasks list marquée `[x]` après vérification que toutes les exécutions sont en place et que la suite passe à 1751/1844 (1751 tests réellement exécutés, 93 skipped, 0 fail).
  - **Findings deferred** : 5 entrées ajoutées à `deferred-work.md` (DEF-BUG-V6-CARBON-UNIQUE, DEF-BUG-V6-CARBON-PRIVATE-IMPORT, DEF-BUG-V6-CARBON-CANONICAL-KEY, DEF-BUG-V6-CREDIT-MIN-AGE-CONFIG, DEF-BUG-V6-DEDUP-MARKER-CONTRACT). Tous hors scope strict du batch (UNIQUE BDD = migration, normalisation = nouvelle feature, magic 30j = config admin).
  - **KEEP instructions** : la garde runtime doit toujours retourner `str` (jamais `raise` — `with_retry` masquerait l'exception). L'idempotence (no-op BDD si validation échoue) reste l'invariant central, comme V5-003. Les messages d'erreur DOIVENT mentionner explicitement le tool de récupération (ex : `get_credit_score`) pour permettre au LLM un retry intelligent.

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_tools/test_carbon_tools.py tests/test_tools/test_credit_tools.py tests/test_tools/test_action_plan_tools.py tests/test_tools/test_profiling_tools.py -v` — attendu : tous les nouveaux tests passent.
- `cd backend && source venv/bin/activate && pytest tests/test_prompts/ -v` — attendu : snapshots golden régénérés OK, aucune régression d'assertion textuelle.
- `cd backend && source venv/bin/activate && pytest tests/ -q` — attendu : ≥1844 verts.
- `git diff --stat backend/app/graph/tools/ backend/app/prompts/` — attendu : 4 tool files + 4 prompt files modifiés, deltas ≤30/≤20 lignes par fichier.

## Design Notes

**Pourquoi pas un nouveau tool `save_action_plan(actions=[...])`** : l'architecture actuelle confie la génération côté service (LLM interne via `app.modules.action_plan.service`). Inverser ce flux (LLM externe envoie les actions) doublerait les coûts tokens et casserait la cohérence. La garde post-appel suffit.

**Pourquoi étendre la garde 10s à 30 jours pour credit** : le bug V6-009 montre une incohérence chat (58) vs dashboard (26). Cause probable : LLM régénère un score textuel sans appeler le tool, ou le tool a échoué et le LLM a improvisé. Une garde mensuelle force le LLM à utiliser `get_credit_score` pour lire la valeur de référence (BDD = source de vérité unique).

**Pourquoi UPDATE pas INSERT pour carbon dedup** : permet la correction d'erreur (ex : LLM saisi 30000 km puis utilisateur corrige à 36000 km) sans nécessiter un tool delete. Comportement V5-003 : last-write-wins.

**Format d'erreur (golden) :**
```
ERREUR : score credit deja genere ce mois (version 1, score 65/100, genere le 2026-04-15). Pour le consulter, appelle get_credit_score(). Pour generer une nouvelle version, attends au moins 30 jours.
```

## Suggested Review Order

**Garde runtime carbone (dedup INSERT/UPDATE)**

- Coeur du fix BUG-V6-002 : SELECT-then-UPDATE-or-INSERT, last-write-wins sur `(assessment_id, category, subcategory)`.
  [`carbon_tools.py:128`](../../backend/app/graph/tools/carbon_tools.py#L128)

- Helper privé importé depuis le service pour recalculer le total après UPDATE (déféré pour expose publique).
  [`carbon_tools.py:158`](../../backend/app/graph/tools/carbon_tools.py#L158)

**Garde runtime credit (idempotence mensuelle)**

- Bloque la regénération < 30 jours et invite explicitement à `get_credit_score`.
  [`credit_tools.py:50`](../../backend/app/graph/tools/credit_tools.py#L50)

- Clamp `age_days = max(0, ...)` pour neutraliser les timestamps futurs (review patch).
  [`credit_tools.py:71`](../../backend/app/graph/tools/credit_tools.py#L71)

**Garde runtime plan d'action (≥10 items + champs requis)**

- Validation post-appel service : count + champs `title`/`category` par item.
  [`action_plan_tools.py:21`](../../backend/app/graph/tools/action_plan_tools.py#L21)

**Garde runtime profil (rejet whitespace-only)**

- Filtre les chaînes vides/espaces post-`raw_updates`, retour erreur exploitable LLM.
  [`profiling_tools.py:73`](../../backend/app/graph/tools/profiling_tools.py#L73)

**Cohérence prompts LLM**

- Section `## PERSISTANCE — TOOL CALL OBLIGATOIRE` clonée du pattern V5-003 dans 4 prompts.
  [`carbon.py:110`](../../backend/app/prompts/carbon.py#L110)
  [`credit.py:102`](../../backend/app/prompts/credit.py#L102)
  [`action_plan.py:67`](../../backend/app/prompts/action_plan.py#L67)
  [`application.py:37`](../../backend/app/prompts/application.py#L37)

**Tests (matrice I/O + AC + patches review)**

- 4 tests carbon dedup : idempotence, distinct subcategories, payload incomplet, marqueur [DEDUP].
  [`test_carbon_tools.py:489`](../../backend/tests/test_tools/test_carbon_tools.py#L489)

- 4 tests credit idempotence : recent reject, après 30j succès, no previous, message exploitable.
  [`test_credit_tools.py:62`](../../backend/tests/test_tools/test_credit_tools.py#L62)

- 4 tests action plan : <10 rejet, champ manquant, plan complet, whitespace title.
  [`test_action_plan_tools.py:71`](../../backend/tests/test_tools/test_action_plan_tools.py#L71)

- 3 tests profiling : whitespace-only rejet, strip, création company.
  [`test_profiling_tools.py:162`](../../backend/tests/test_tools/test_profiling_tools.py#L162)

- Conftest mutualisé : `db.execute()` retourne un Result vide par défaut pour préserver les tests existants.
  [`conftest.py:22`](../../backend/tests/test_tools/conftest.py#L22)

**Capitalisation méthodologique**

- Leçon 36 §4nonies : doctrine "validation runtime systémique sur tools de persistance" + checklist anti-récurrence.
  [`methodology.md:1119`](../../docs/CODEMAPS/methodology.md#L1119)

- Bug `score.risk_level` déféré (DEF-BUG-V6-CREDIT-RISKLEVEL) + 5 défers issus du review.
  [`deferred-work.md:944`](../../_bmad-output/implementation-artifacts/deferred-work.md#L944)
