# Méthodologie — patterns transverses BMAD dev-stories

Ce document capitalise les patterns méthodologiques récurrents détectés lors
des code reviews Phase 4 (stories 10.x). Complément du CLAUDE.md racine,
orienté workflow dev-story + review plutôt que code applicatif.

## 1. Scan NFR66 Task 1 révèle dette cachée

**Pattern** : le scan exhaustif NFR66 en Task 1 d'une story d'abstraction
peut révéler **plus de sites de consommation** que la spec n'avait projeté.

**Exemple Story 10.13** : la spec annonçait 2 hits `OpenAIEmbeddings(`
(`documents/service.py:525, 530`) — le scan Task 1 en a trouvé **6 hits / 3
fichiers** (+ `financing/seed.py:851` + `financing/service.py:170`).

**Leçon** : systématiser en Task 1 le scan **par symbole absolu**
(`OpenAIEmbeddings(|text-embedding-3-small|ChatOpenAI\(`) plutôt que se
limiter aux callers documentés spec. Le scan remonte la dette cachée
avant que le sizing ne soit figé.

**Check-list Task 1 d'une story d'abstraction** :

```bash
# 1. Symboles vendor à remplacer (exhaustif, pas limité à la spec)
rg -n "<VendorClass>\(|<vendor_model_name>" backend/ \
    --glob '!backend/tests/**' \
    --glob '!backend/app/core/<new_abstraction>/**'

# 2. Colonnes ORM avec dimensions figées (si migration schéma requise)
rg -n "Vector\(<dim>\)" backend/app/models/ backend/alembic/

# 3. Appelants de la signature publique (shims legacy 10.6)
rg -n "<public_function>\(" backend/

# 4. Baseline pytest + coverage avant Task 2
source venv/bin/activate && pytest --collect-only -q | tail -1

# 5. Dry-run deps (évite pivot mi-story)
pip install --dry-run "<new-dep>>=<ver>"
```

Les résultats sont documentés dans Completion Notes §Scan NFR66 avec
comparaison attendu/réalisé — si écart > 0, **remonter la discussion scope
AVANT Task 2** plutôt que déférer silencieusement.

## 2. Pivot dépendance — dry-run précoce

**Pattern** : une version de dep spécifiée spec peut échouer à s'installer
(Python runtime moderne, conflits langchain-*, etc.). Détection en Task 1.5
par `pip install --dry-run` évite les pivots mi-story.

**Exemple Story 10.13** : spec exigeait `voyageai>=0.3.4`, dry-run résout
`voyageai-0.2.3` (dernière version PyPI compatible Python 3.14). Pivot
documenté Debug Log avec impact API surface (`voyageai.error.*`).

**Bonne pratique complémentaire** : pour chaque vendor SDK ajouté, créer un
test smoke `test_<vendor>_sdk_surface_compat` qui vérifie la présence des
attributs utilisés runtime. Fail-fast au prochain bump.

## 3. Calibration sizing XL infra vs XL temps réel

**Pattern** : une story XL (6-8 h projetés) d'**infrastructure provider**
(abstraction ABC + factory + migration + shim) se livre souvent en **1h30-2h**
réels car les patterns byte-identique 10.6 réduisent l'effort d'invention.

**Leçon** : ne pas confondre **XL scope** (nb de fichiers, surface couverte)
avec **XL temps réel** (complexité cognitive). Les stories XL de refactor
provider/ports-and-adapters sont souvent calibrables en L ou M si :

- Pattern parent existe (storage/ pour embeddings/, embeddings/ pour llm/).
- 8+ Q tranchées pré-dev (aucune décision durant impl).
- Tests unit mockés (pas E2E infra lourde).

**Signal d'alerte** : si la durée réelle est ≤ 30 % du sizing, vérifier
que les raccourcis pris (bench non exécuté, shim non branché, corpus
réduit) n'ont pas dégradé la satisfaction d'AC — sinon rectifier Completion
Notes honnêtement et déférer proprement.

## 4. Golden corpus + expected_ids validation

**Pattern** : tout test de qualité RAG (`recall@5`, `mrr`, `ndcg`) sur
corpus fixture doit inclure un **meta-test structurel** qui asserte :

1. Le corpus contient le nombre attendu de chunks (pas `>=`, mais `==`).
2. Les chunk IDs sont uniques.
3. **Chaque `expected_top5_chunk_ids` référence un chunk réel**.

Sans (3), un corpus désynchronisé de ses annotations ground-truth produit
des scores biaisés silencieusement (le recall est plafonné artificiellement
— e.g. 1/5 si un seul expected chunk existe).

**Implémentation référence** : `backend/tests/test_core/test_embeddings_quality.py::test_corpus_structure_is_valid`
(Story 10.13 post-review CRITICAL-1 2026-04-21).

## 4bis. Règle d'or tests E2E DOM (pas state interne) — anti-tautologie

**Pattern** : un test qui **mute l'état interne** d'un composant (élément DOM,
`wrapper.vm`, `setData`) puis vérifie cet état ne teste rien — il lit ce qu'il
a écrit. C'est une tautologie qui **masque les bugs de binding**.

**Exemple Story 10.16 (H-3, 2026-04-22)** — Select multi-select :

```ts
// ❌ ANTI-PATTERN : mutation imperative puis assert sur emit dérivé
Array.from(el.options).forEach((o) => {
  o.selected = o.value === '8' || o.value === '13';
});
await sel.trigger('change');
expect(emitted?.[0]?.[0]).toEqual(['8', '13']);
```

Ce test passait. Mais le composant **ne synchronisait jamais** `modelValue: ['8','13']`
passé en prop vers `selectedOptions` DOM (`:value="modelValue"` ignore les tableaux
sur `<select multiple>` natif). Le bug est resté invisible jusqu'à la review.

**Règle** :

- Tests **prop → DOM** (binding parent→enfant) : passer via `mount({ props })` ou
  `setProps()`, puis lire depuis le **DOM rendu** (`selectedOptions`, `.value`,
  `attributes()`, `classes()`, `getByRole`). Jamais depuis `wrapper.vm.xxx`.
- Tests **emit enfant→parent** : déclencher un événement utilisateur réaliste
  (`trigger('input')`, `userEvent.type()`), jamais mutation directe de
  `element.value` suivie d'un assert sur `emitted` de la même valeur.
- Exception : tests de side-effects (stores, observers) peuvent mock la dépendance,
  mais l'assertion finale reste **observable depuis l'extérieur** (DOM ou emit).

**Check pré-merge** :
- [ ] Aucun test : `Array.from(el.options).forEach(o => o.selected = ...)` + assert
      sur `emitted` identique.
- [ ] Aucun `wrapper.setData({...})` + assert sur état interne.
- [ ] Chaque prop testée passe par `mount()` ou `setProps()`.

## 4ter. Comptages runtime OBLIGATOIRES avant Completion Notes

**Pattern** : les métriques du dev-report (`+38 tests`, `132 stories`,
`14/14/11 dark:`) sont **non-vérifiées** si elles ne proviennent pas d'une
commande reproductible exécutée **au moment du commit final**.

**Exemple Story 10.16 (M-3, 2026-04-22)** : dev-report annonçait `132 stories
(66 + 66 nouvelles)`. Review reality : 21 Button + 63 form + 38 gravity = **122
exports CSF**. La dérive (+10) venait de (a) confusion exports CSF vs pages
autodocs, (b) copie du pattern 10.15 sans re-exécution.

**Règle** : avant de rédiger Completion Notes, exécuter et coller la sortie
**brute** :

```bash
# Tests runtime
npm run test -- --run 2>&1 | tail -5
# Typecheck
npm run test:typecheck 2>&1 | tail -3
# Stories CSF (comptage exports)
grep -rE "^export const [A-Z]\w+: Story" frontend/app/components/ | wc -l
# Dark mode occurrences par composant modifie
for f in frontend/app/components/ui/*.vue; do
  echo "$f: $(grep -c 'dark:' "$f") dark:"
done
# Baseline/commits
git log --oneline <baseline>..HEAD
```

**Check pré-merge** :
- [ ] Chaque métrique du dev-report a une commande bash associée.
- [ ] Sortie brute collée dans le story file (pas l'interprétation).
- [ ] Reviewer re-exécute ≥ 3 commandes et confronte aux claims.
- [ ] Si un chiffre diverge > 5 %, rectifier **avant** merge (pas de
      "on corrigera plus tard").

**Exception légitime** : coverage c8 peut être batched post-merge (pattern
10.15), mais doit être tracé dans `deferred-work.md` (ex: `DEF-10.16-4`).

**Application proactive Story 10.17 (ui/Badge)** — les deux patterns A et B
ci-dessus sont **appliqués proactivement** dès la rédaction des tests (pas
après code-review) :

- Pattern A (DOM ≠ state interne) : `test_badge_variants.test.ts` assert
  `wrapper.find('span').classes()` + `attributes('aria-label')` +
  `[data-testid="badge-label-slot"]` text — **jamais** `wrapper.vm.variant`.
- Pattern B (comptage runtime obligatoire) : Task 8 exécute
  `jq '.entries | keys | length' frontend/storybook-static/index.json`
  **avant** Completion Notes et consigne le chiffre exact. Piège #26 du
  codemap `ui-primitives.md` capitalise la règle pour les stories suivantes.

La capitalisation en règle d'or permanente (pas seulement incident review)
raccourcit la boucle : review Story 10.17 ne devrait plus remonter ni H-3
ni M-3 (ou alors sur un autre axe qu'une répétition 10.16).

## 5. Règle 10.5 no-duplication : scan AST-aware

**Pattern** : le scan `rg "VendorClass\("` pour enforce l'unicité
d'instantiation peut flaguer des **docstrings historiques** qui mentionnent
le vendor sans le réinstantier. Faux positif.

**Solution** : test Python qui parse l'AST, identifie les plages de
docstrings (`ast.Expr` + `ast.Constant` str de type module/function/class),
et scanne uniquement le code exécutable.

**Implémentation référence** : `test_financing_service_uses_embedding_provider`
(Story 10.13 post-review HIGH-3 2026-04-21).

## Références

- [Story 10.13 code review](../../_bmad-output/implementation-artifacts/10-13-code-review-2026-04-21.md)
- [CLAUDE.md](../../CLAUDE.md) — conventions dev globales
- [rag.md §6](./rag.md) — pattern corpus validation (détails techniques)
