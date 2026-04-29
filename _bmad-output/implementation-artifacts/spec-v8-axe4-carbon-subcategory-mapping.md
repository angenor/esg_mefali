---
title: 'V8-AXE4 — Mapping subcategory carbone exhaustif backend'
type: 'bugfix'
created: '2026-04-29'
status: 'done'
baseline_commit: '26c7e86'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/tests-manuels-vague-7-2026-04-28.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-v8-axe3-routing-credit-carbon-finalize.md'
  - '{project-root}/CLAUDE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le tool `save_emission_entry` rejette systématiquement quand `subcategory=null` ou retourne un facteur d'émission incorrect quand le LLM fournit un libellé français non canonique. Régressions identiques sous MiniMax et Claude Sonnet 4.6 — switch LLM réfuté, c'est architectural backend.

- **BUG-V7-005 (MiniMax):** agriculture « riz pluvial » → `subcategory=null` → erreur "Aucun facteur d'emission trouve" (catégorie agriculture absente d'EMISSION_FACTORS).
- **BUG-V7.1-006 (Claude):** 4/4 appels avec `subcategory=null` → fallback heuristique inadapté.
- **BUG-V7.1-007:** mauvais mapping backend (« diesel » → premier match alphabétique = `gasoline` essence ; « compostage » → `waste_landfill` enfouissement) → facteurs émission incorrects → bilan carbone faussé.

**Root cause:** (1) le tool dépend du LLM pour fournir un `subcategory` canonique alors que les deux providers échouent ; (2) le backend n'a pas de dictionnaire synonymes français → codes canoniques ; (3) l'heuristique fallback prend le premier match alphabétique au lieu d'un match sémantique ; (4) les catégories `agriculture` / `industrial` n'ont aucun facteur d'émission défini.

**Approach:** Service déterministe `carbon_mapping.resolve_subcategory(category, raw_text)` avec dictionnaire FR→canonique exhaustif (3 niveaux : exact lowercase+sans accents, substring, fuzzy difflib cutoff 0.75) + extension d'`EMISSION_FACTORS` aux codes canoniques manquants (agriculture, industriel, transport étendu, énergies renouvelables, déchets recyclage/compost). Intégration dans `save_emission_entry` AVANT le lookup `EMISSION_FACTORS` : on tente d'abord `subcategory` brut, puis `resolve_subcategory(category, subcategory or source_description)`, puis fallback historique (premier code de la catégorie).

## Boundaries & Constraints

**Always:**
- Service pur dans `backend/app/services/carbon_mapping.py` (pas de dépendance DB, pas d'appel LLM).
- Normalisation : lowercase + strip + suppression accents Unicode (`unicodedata.NFKD`).
- 3 stratégies de match dans cet ordre : (1) exact normalisé, (2) substring, (3) fuzzy difflib cutoff 0.75.
- Si `category` non couvert par `SUBCATEGORY_SYNONYMS` → `(None, [])`.
- Si `raw_text` vide ou aucun match → `(None, alternatives)` où `alternatives` = liste codes canoniques de la catégorie.
- Tous les codes canoniques référencés dans `SUBCATEGORY_SYNONYMS` DOIVENT exister dans `EMISSION_FACTORS` (invariant testé).
- L'intégration dans `save_emission_entry` reste rétrocompatible : si le LLM fournit déjà un `subcategory` valide existant dans `EMISSION_FACTORS`, on l'utilise tel quel sans passer par le mapping (chemin rapide).

**Ask First:** Si la couverture des synonymes < 70% sur 50 messages utilisateur réels en production (mesure via logs `Subcategory unresolved`), revoir le dictionnaire avec accord humain.

**Never:** Modifier la signature publique du tool `save_emission_entry` (le LLM continue d'être encouragé à fournir `subcategory`) ; appeler un LLM dans `resolve_subcategory` (déterministe pur) ; déplacer la logique dans `nodes.py` ou `prompts/` ; supprimer ou renommer des codes canoniques existants (`electricity_ci`, `diesel_generator`, `butane_gas`, `gasoline`, `diesel_transport`, `waste_landfill`, `waste_incineration`).

## I/O & Edge-Case Matrix

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Match exact | `category="agriculture"`, `raw_text="riz pluvial"` | `("rice_rainfed", [])` |
| Match exact avec accents | `category="energy"`, `raw_text="électricité"` | `("grid_electricity", [])` |
| Match substring | `category="energy"`, `raw_text="groupe électrogène diesel ancien"` | `("diesel_generator", [])` |
| Match fuzzy | `category="waste"`, `raw_text="compostag"` (typo) | `("waste_compost", [])` |
| Échec mapping | `category="energy"`, `raw_text="cheval-vapeur"` | `(None, [<codes canoniques energy>])` |
| Catégorie inconnue | `category="finance"`, `raw_text="prêt vert"` | `(None, [])` |
| Texte vide | `category="energy"`, `raw_text=""` | `(None, [<codes canoniques energy>])` |
| Tool BUG-V7-005 fix | `save_emission_entry(category="agriculture", subcategory=None, source_description="500 kg de riz pluvial")` | `status=success` avec `subcategory="rice_rainfed"`, facteur 1.45 kgCO2e/kg appliqué |
| Tool BUG-V7.1-007 fix diesel | `save_emission_entry(category="energy", subcategory="diesel", quantity=200)` | `status=success` avec `subcategory="diesel_generator"` (PAS `gasoline`) |
| Tool BUG-V7.1-007 fix compost | `save_emission_entry(category="waste", subcategory="compostage", quantity=50)` | `status=success` avec `subcategory="waste_compost"` (PAS `waste_landfill`) |
| Rétrocompatibilité chemin rapide | `subcategory="electricity_ci"` directement valide | `subcategory="electricity_ci"` utilisé sans passer par `resolve_subcategory` |

</frozen-after-approval>

## Code Map

- `backend/app/services/carbon_mapping.py` — **NOUVEAU**. Constante `SUBCATEGORY_SYNONYMS` (5 catégories × ~10-15 synonymes FR), helpers `_normalize(text)` et `resolve_subcategory(category, raw_text) -> tuple[str | None, list[str]]`.
- `backend/app/modules/carbon/emission_factors.py` — étendre `EMISSION_FACTORS` avec les codes canoniques manquants référencés par `SUBCATEGORY_SYNONYMS` :
  - **agriculture (nouveau)** : `rice_rainfed` (1.45), `rice_irrigated` (3.0), `wheat` (0.8), `maize` (0.6), `cattle` (15.0/animal/an), `goats` (1.8/animal/an), `compost` (0.05/kg), `nitrogen_fertilizer` (5.4/kg).
  - **energy (extension)** : `diesel` (alias direct = 2.68), `lpg` (3.0), `grid_electricity` (alias = 0.41), `solar_pv` (0.041), `coal` (2.42/kg), `biomass` (0.39/kg).
  - **transport (extension)** : `truck` (0.92/km), `car` (0.18/km), `motorcycle` (0.07/km), `flight` (0.255/km), `ship` (0.04/km), `train` (0.06/km), `bus` (0.10/km).
  - **waste (extension)** : `waste_compost` (0.05/kg), `waste_recycling` (0.02/kg).
  - **industrial (nouveau)** : `cement` (0.93/kg), `steel` (1.85/kg), `aluminum` (8.14/kg), `glass` (0.85/kg), `paper` (1.1/kg), `plastic` (2.5/kg).
  - Mettre à jour `EMISSION_CATEGORIES[*].subcategories` pour inclure les nouveaux codes obligatoires (énergie/transport/déchets) ; `agriculture` et `industrial` reçoivent leurs propres listes `subcategories`.
- `backend/app/graph/tools/carbon_tools.py` — `save_emission_entry` (l. 68-194) : entre la lookup `factor_key in EMISSION_FACTORS` (l. 105) et le fallback "premier match catégorie" (l. 109), insérer un appel à `resolve_subcategory(category, subcategory or source_description)` ; logger en INFO le code résolu ; logger en WARNING si non résolu et fallback déclenché.
- `backend/tests/test_services/test_carbon_mapping.py` — **NOUVEAU**. ~15 tests couvrant chaque scenario de la matrice.
- `backend/tests/test_tools/test_carbon_tools.py` — étendre avec 3 tests régression (BUG-V7-005 riz pluvial, BUG-V7.1-007 diesel, BUG-V7.1-007 compostage). Existants à ajuster : `test_save_emission_entry_fallback_category` reste vrai (`gasoline` premier match transport sans hint sémantique).

## Design Notes

- **Pourquoi déterministe :** la cause racine n'est pas un défaut de capacité LLM mais une absence de référentiel backend. Mapper côté serveur garantit reproductibilité, testabilité, et indépendance du provider.
- **Pourquoi 3 stratégies :** exact = cas idéal LLM cite synonyme connu. Substring = LLM verbeux ("groupe électrogène diesel ancien"). Fuzzy = robustesse aux typos / accents partiels. Cutoff 0.75 évite les faux positifs sans être trop strict (testé sur "compostag", "diesell").
- **Pourquoi étendre EMISSION_FACTORS :** sans facteur, le mapping résout vers un code... inutilisable. L'invariant "tout code canonique du mapping a un facteur" est explicite dans les tests.
- **Valeurs des facteurs :** dérivées ADEME / IPCC AR6 / GHG Protocol, ajustées contexte Afrique de l'Ouest (mix électrique fossile dominant déjà reflété par 0.41 CI). Les valeurs nouvelles sont choisies conservatrices et clairement référencées en commentaire dans `emission_factors.py`.
- **Rétrocompatibilité :** chemin rapide preservé (`if factor_key and factor_key in EMISSION_FACTORS`) — les tests existants restent verts.
- **Pas de modification des prompts :** les prompts `prompts/carbon.py` continuent à demander un `subcategory` canonique au LLM, mais le backend ne dépend plus de cette qualité.

## Tasks

- [x] T1. Créer `backend/app/services/carbon_mapping.py` avec `SUBCATEGORY_SYNONYMS` + `_normalize` + `resolve_subcategory`.
- [x] T2. Étendre `backend/app/modules/carbon/emission_factors.py` : ajouter les codes canoniques manquants (agriculture, industrial, transport étendu, énergies renouvelables, déchets recyclage/compost).
- [x] T3. Mettre à jour `EMISSION_CATEGORIES[*].subcategories` pour `agriculture` et `industrial`.
- [x] T4. Modifier `save_emission_entry` dans `backend/app/graph/tools/carbon_tools.py` : intégrer `resolve_subcategory` avant le fallback "premier match catégorie".
- [x] T5. Créer `backend/tests/test_services/test_carbon_mapping.py` avec ~15 tests (matrice + invariant "tous codes canoniques existent dans EMISSION_FACTORS").
- [x] T6. Étendre `backend/tests/test_tools/test_carbon_tools.py` : 3 tests régression (BUG-V7-005, BUG-V7.1-007 diesel, BUG-V7.1-007 compostage).
- [x] T7. Lancer `pytest backend/tests/test_services/test_carbon_mapping.py backend/tests/test_tools/test_carbon_tools.py` et vérifier zéro régression.

## Spec Change Log

- 2026-04-29 — Spec initiale rédigée. Statut : in-progress.
