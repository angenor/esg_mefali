---
title: 'BUG-V5-003 — Validation runtime ESG : forcer 10 critères par pilier dans batch_save_esg_criteria'
type: 'bugfix'
created: '2026-04-24'
status: 'done'
baseline_commit: '8f0ec423d42eba20f82190ea7a9bbab70ff2d334'
context:
  - '{project-root}/backend/app/modules/esg/criteria.py'
  - '{project-root}/backend/app/graph/tools/esg_tools.py'
  - '{project-root}/backend/app/prompts/esg_scoring.py'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem :** Le LLM (MiniMax) n'évalue que 3 critères par pilier (E1-E3, S1-S3, G1-G3) au lieu des 10 prévus (grille E1-E10, S1-S10, G1-G10). Le tool `batch_save_esg_criteria` n'a aucune validation de complétude, donc l'évaluation est finalisée sur 9/30 critères — score ESG faux, rapport PDF mensonger, matching financement biaisé, plan d'action inadapté.

**Approach :** Ajouter une garde runtime à `batch_save_esg_criteria` : pour chaque pilier touché par l'appel, calculer l'union des codes de la requête et de ceux déjà persistés. Si un pilier reste incomplet (< 10 codes), n'écrire rien en BDD et retourner une chaîne d'erreur explicite listant les codes manquants. Transforme une consigne de prompt (ignorée) en contrainte d'API (impossible à ignorer).

## Boundaries & Constraints

**Always :**
- La validation s'applique pilier par pilier, indépendamment, à partir du préfixe du code (`E*`, `S*`, `G*`).
- Compter `union(critères_dans_appel ∪ critères_déjà_évalués_pour_ce_pilier)` — autoriser la complétion progressive en plusieurs appels.
- Si validation échoue : aucune écriture BDD (idempotence) ; retourner une chaîne d'erreur en français nommant le pilier, les codes attendus et les codes manquants.
- Codes dédupliqués dans la requête (le LLM peut envoyer des doublons) avant validation.
- Source de vérité des codes : `app.modules.esg.criteria.PILLAR_CRITERIA` (E1-E10, S1-S10, G1-G10).
- Préserver la rétrocompatibilité du schéma d'inputs LangChain (mêmes champs, mêmes types).

**Ask First :** aucun — correction critique (score ESG invalide en production).

**Never :**
- Ne pas modifier `save_esg_criterion_score` (1 critère) — il reste utilisable et hors scope de la validation.
- Ne pas bloquer `finalize_esg_assessment` (peut être appelé même si certains piliers incomplets — le LLM doit avoir la sortie pour résoudre, mais c'est traité ailleurs).
- Ne pas imposer un ordre strict E→S→G (le routage reste piloté par le prompt).
- Ne pas changer la signature publique du tool (compatibilité bindings LangChain).
- Ne pas faire d'écriture partielle si validation échoue.
- Ne pas rejeter un appel multi-pilier (E+S+G) tant que chaque pilier touché est complet via l'union.

## I/O & Edge-Case Matrix

| Scénario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Pilier complet en un appel | criteria=[E1..E10], BDD vide | Sauvegarde + retour `10 criteres enregistres...` | N/A |
| Pilier incomplet, BDD vide | criteria=[E1, E2, E3] | **Aucune écriture**, retour `ERREUR : pilier E incomplet. Codes manquants : E4, E5, E6, E7, E8, E9, E10. ...` | LLM relance avec critères manquants |
| Complétion progressive | criteria=[E4..E10], déjà persistés [E1..E3] | Sauvegarde + retour OK (union = E1..E10) | N/A |
| Multi-pilier complet | criteria=[E1..E10, S1..S10] | Sauvegarde des 20 critères en une transaction | N/A |
| Multi-pilier incomplet | criteria=[E1..E10, S1..S3] | Aucune écriture ; erreur listant manquants S4..S10 | LLM corrige |
| Codes dupliqués | criteria=[E1, E1, E2..E10] | Dédup par code (dernière justification gagne), validation OK, sauvegarde | N/A |
| Code invalide (préfixe inconnu) | criteria=[X1, E1..E10] | Erreur `Codes invalides : X1` (avant validation pilier) | LLM corrige |
| Liste vide | criteria=[] | Erreur existante `liste de criteres est vide` (inchangée) | inchangé |
| Assessment introuvable | assessment_id inconnu | Erreur existante `evaluation ESG ... introuvable` | inchangé |

</frozen-after-approval>

## Code Map

- `backend/app/graph/tools/esg_tools.py` — tool `batch_save_esg_criteria` à corriger ; cible principale du patch
- `backend/app/modules/esg/criteria.py` — source de vérité `PILLAR_CRITERIA` (E1-E10, S1-S10, G1-G10) à importer pour la validation
- `backend/app/prompts/esg_scoring.py` — prompt ESG à aligner avec le nouveau message d'erreur runtime (ligne 31-36)
- `backend/tests/test_tools/test_esg_tools.py` — fichier de tests existant pour les tools ESG ; ajouter une nouvelle classe `TestBatchSaveEsgCriteria` couvrant la matrice I/O

## Tasks & Acceptance

**Execution :**
- [x] `backend/app/graph/tools/esg_tools.py` — helper `_validate_pillar_completeness` ajouté ; intégré en tête de `batch_save_esg_criteria` avant toute écriture BDD.
- [x] `backend/tests/test_tools/test_esg_tools.py` — classes `TestValidatePillarCompleteness` (7 cas) + `TestBatchSaveEsgCriteria` (8 cas) couvrant la matrice I/O ; idempotence vérifiée via `mock_update.assert_not_awaited()`.
- [x] `backend/app/prompts/esg_scoring.py` — paragraphe `## SAUVEGARDE PAR LOT` enrichi d'un bloc `**CONTROLE RUNTIME**` annonçant le refus du tool en cas de pilier incomplet ; golden snapshot `tests/test_prompts/golden/esg_scoring.txt` régénéré en conséquence.

**Acceptance Criteria :**
- Given une assessment vide, when le LLM appelle `batch_save_esg_criteria(criteria=[E1, E2, E3])`, then le tool ne persiste rien (aucun appel à `update_assessment`) et retourne une chaîne contenant `ERREUR`, le pilier `E` et les codes manquants `E4..E10`.
- Given une assessment où `evaluated_criteria=["E1","E2","E3"]`, when le LLM appelle `batch_save_esg_criteria(criteria=[E4..E10])`, then les scores E4..E10 sont persistés et le retour de tool indique `Criteres evalues : 10/30`.
- Given un appel multi-pilier `criteria=[E1..E10, S1..S3]` sur assessment vide, when invoqué, then aucune écriture, et l'erreur liste exclusivement les codes manquants du pilier S (S4..S10).
- Given un code invalide `X1` mêlé à un pilier complet, when invoqué, then erreur `Codes invalides : X1` avant toute écriture.
- Given un appel valide, when invoqué, then les comportements existants (dédup BDD, calcul progress, scores partiels, status `in_progress`) restent inchangés.
- Tests : `pytest backend/tests/test_tools/test_esg_tools.py -v` passe ; aucun test existant ESG ne régresse (`pytest backend/tests/ -k esg -v`).

## Spec Change Log

- **2026-04-25 — Review patches (no spec change)** — 3 patches appliqués sur recommandation des reviewers (Blind hunter, Edge case hunter, Acceptance auditor) sans toucher au `<frozen-after-approval>` :
  1. Ajout d'un helper `_normalize_code(raw)` (`.strip().upper()`, tolérant aux non-string) appelé en tête de `_validate_pillar_completeness` pour les codes de la requête ET les codes persistés (défense en profondeur). Évite les boucles d'erreur LLM sur `'e1'`, `' E1 '`, ainsi qu'un `IndexError` sur empty string ou `TypeError` sur `int`.
  2. Propagation de `_normalize_code` dans `batch_save_esg_criteria` lors de l'écriture (`criteria_scores`, `evaluated_criteria`, `last_code`, `saved_codes`) : aucun code lower-case ne peut traverser jusqu'à la BDD.
  3. Ajout de 5 tests dans la suite : `test_normalizes_case_and_whitespace`, `test_normalizes_persisted_codes_too`, `test_non_string_code_treated_as_invalid`, `test_duplicate_code_last_write_wins` (E2E sur le tool, vérifie que la dernière occurrence gagne dans `assessment_data`), `test_lowercase_codes_normalized_before_persistence`.
  - **Findings deferred** : 7 entrées ajoutées à `deferred-work.md` (DEF-BUG-V5-3-1..7) — bornes score, critère corrompu, race condition, `MAX_TOOL_CALLS_PER_TURN`, `current_pillar`, `KeyError`, test cohérence prompt/tool. Tous pré-existants ou hors scope strict du bugfix.
  - **KEEP instructions** : la garde runtime doit toujours retourner `None`/string et ne JAMAIS lever d'exception (pour ne pas être rejouée par `with_retry`). L'union avec persisté est non-négociable. L'idempotence (no-op BDD si validation échoue) est l'invariant central.

## Design Notes

**Union avec les déjà-persistés** : le LLM peut appeler le tool plusieurs fois par pilier (retry, évaluation en passes). La complétude se mesure sur l'état de l'assessment, pas sur l'appel isolé.

**Chaîne d'erreur (pas exception)** : `with_retry` masquerait une exception ; une chaîne explicite est lue par le LLM qui peut corriger.

**Format d'erreur (golden) :**
```
ERREUR : pilier E incomplet (3/10). Codes manquants : E4, E5, E6, E7, E8, E9, E10. Tu DOIS évaluer les 10 critères E1-E10 avant de passer au pilier suivant. Rappelle batch_save_esg_criteria avec les critères manquants (les déjà sauvés sont conservés).
```

## Verification

**Commands :**
- `cd backend && source venv/bin/activate && pytest tests/test_tools/test_esg_tools.py -v` — attendu : tous les tests (existants + nouveaux) passent
- `cd backend && source venv/bin/activate && pytest tests/ -k esg -v` — attendu : aucune régression sur la suite ESG complète
- `cd backend && source venv/bin/activate && pytest tests/test_prompts/test_esg_scoring_prompt.py tests/test_prompts/test_esg_tools.py -v` — attendu : les tests de prompt passent toujours après l'ajout de la phrase

## Suggested Review Order

**Logique de validation (cœur du fix)**

- Helper de normalisation tolérante (casse/whitespace/non-string) — entrée si tu veux comprendre l'intent.
  [`esg_tools.py:19`](../../backend/app/graph/tools/esg_tools.py#L19)

- Garde runtime : invalides → erreur tôt, puis union par pilier vs codes attendus.
  [`esg_tools.py:26`](../../backend/app/graph/tools/esg_tools.py#L26)

- Source de vérité : map lettre→pilier construite depuis `PILLAR_CRITERIA`.
  [`esg_tools.py:13`](../../backend/app/graph/tools/esg_tools.py#L13)

**Intégration dans le tool (idempotence + propagation normalisée)**

- Appel de la garde avant toute écriture ; aucun `update_assessment` si erreur.
  [`esg_tools.py:353`](../../backend/app/graph/tools/esg_tools.py#L353)

- Codes normalisés à l'écriture (`criteria_scores`, `evaluated_criteria`, retour).
  [`esg_tools.py:364`](../../backend/app/graph/tools/esg_tools.py#L364)

**Cohérence prompt LLM**

- Bloc « CONTROLE RUNTIME » ajouté à la règle `## SAUVEGARDE PAR LOT`.
  [`esg_scoring.py:36`](../../backend/app/prompts/esg_scoring.py#L36)

**Tests (matrice I/O + AC + patches review)**

- 10 tests purs du helper (complétude, union, multi-pilier, dédup, normalisation).
  [`test_esg_tools.py:502`](../../backend/tests/test_tools/test_esg_tools.py#L502)

- Tests E2E critiques : pilier incomplet bloqué (idempotence), complétion progressive, multi-pilier mixte.
  [`test_esg_tools.py:661`](../../backend/tests/test_tools/test_esg_tools.py#L661)

- Tests post-review : last-write-wins doublons, normalisation casse persistée.
  [`test_esg_tools.py:860`](../../backend/tests/test_tools/test_esg_tools.py#L860)

**Snapshot du prompt**

- Régénéré pour absorber l'ajout `CONTROLE RUNTIME`.
  [`esg_scoring.txt:1`](../../backend/tests/test_prompts/golden/esg_scoring.txt#L1)
