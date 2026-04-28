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
  `[data-testid="badge-label-slot"]` text pour **31/33 tests** rendu visuel.
- Pattern B (comptage runtime obligatoire) : Task 8 exécute
  `jq '.entries | keys | length' frontend/storybook-static/index.json`
  **avant** Completion Notes et consigne le chiffre exact. Piège #26 du
  codemap `ui-primitives.md` capitalise la règle pour les stories suivantes.

**Extension Pattern A post-code-review 10.17 (CRITICAL-3)** — les tests de
**runtime enforcement** (`console.error`/`console.warn` émis par `onMounted`
quand un slot manque) ont initialement asserté **uniquement** le console spy —
ce qui est un side-effect observable mais **PAS** du DOM. Un reviewer a pointé
que la vraie question utilisateur est « est-ce que l'icône/label apparaissent
dans le DOM ? » — pas « est-ce qu'un log est émis ? ». **Règle durcie** : un
test d'invariant UX doit asserter **le DOM observable en premier** (wrapper
vide, childElementCount, textContent), et le console spy en **défense en
profondeur** (pas en assertion primaire). Applicable aux futures primitives
avec guards `onMounted` (piège méthodologique post-10.17).

**Extension Pattern B post-code-review 10.17 (CRITICAL-1/2 soft-bg)** — le
contraste AA documenté dans `§6 ui-primitives.md` était calculé « texte vs
blanc » mais le render effectif était « texte sur `-soft` background ». La
documentation induisait une fausse conformité. **Règle durcie** : tout ratio
WCAG documenté doit préciser `text #X on bg #Y` avec les **deux** hex, jamais
`X vs white` isolé. Ajout test pur JS `test_badge_contrast.test.ts` qui lit
`main.css` et calcule le ratio sur les **vrais** combos émis par
`variantClasses` — filet de sécurité indépendant de `jest-axe` happy-dom.

La capitalisation en règle d'or permanente (pas seulement incident review)
raccourcit la boucle : review Story 10.17 ne devrait plus remonter ni H-3
ni M-3 (ou alors sur un autre axe qu'une répétition 10.16).

### 4ter.bis Application proactive Story 10.18 (ui/Drawer) — 4 leçons cumulées

Story 10.18 (20ᵉ dev-story Phase 4, 1ʳᵉ primitive `ui/` wrapper Reka UI)
applique **avant code review** les 4 patterns capitalisés :

1. **Pattern A (DOM observable, portal-aware)** — 10.16 H-3 + 10.17. Le
   `DialogPortal` Reka UI monte le drawer hors de la racine du composant.
   Les tests `test_drawer_behavior.test.ts` + `test_drawer_a11y.test.ts`
   utilisent **exclusivement** `document.body.querySelector('[role=
   "complementary"]')` — jamais `wrapper.vm.open` ni `wrapper.find(...)`
   sur la racine (qui serait vide post-portal). `w.attachTo(document.body)`
   + `await nextTick(); await nextTick();` avant assertion (double tick
   nécessaire pour Reka UI DialogRoot → DialogPortal resolution).
2. **Pattern B (comptage Storybook runtime OBLIGATOIRE)** — 10.16 M-3 +
   10.17 piège #26. Task 7.3 capture `jq '[.entries | to_entries[] |
   select(.value.id | startswith("ui-drawer"))] | length'` **AVANT** de
   rédiger les Completion Notes du story file. Pas d'estimation a priori.
3. **Leçon 10.14 HIGH-2 capitalisée infra (`role="complementary"`
   override)** — ARIA override = **architecture par défaut** du composant,
   pas correction post-hoc. Le piège #29 codemap documente la dérogation
   `aria-allowed-attr` axe-core (axe ARIA 1.2 stricte réserve `aria-modal`
   à `role="dialog"`) — désactivée uniquement dans le smoke vitest-axe,
   validation runtime déléguée à Storybook.
4. **Leçon 10.15 HIGH-2 capitalisée infra (Storybook runtime pour
   portail)** — délégation explicite portail-dépendants à
   `addon-a11y` runtime dans `test_drawer_a11y.test.ts`. Anti-fix
   interdit : désactiver `color-contrast` axe-core pour masquer un
   problème réel. Les seules règles désactivées sont documentées avec la
   raison happy-dom (pas de layout box + portals multiples).

Mesure anti-récurrence : si un 5ᵉ pattern émerge post-code-review 10.18,
créer `§4quater`. Les 4 patterns ci-dessus sont **stables et permanents**
pour les wrappers Reka UI futurs (10.19 Combobox/Tabs, 10.20 DatePicker).

### 4quater Leçons post-review Story 10.18 (patches Option 0 Fix-All) — 2 patterns de traçabilité

Les 2 HIGH remontés en code review 10.18 (APPROVE-WITH-CHANGES) portent
tous les deux sur la **traçabilité** plutôt que sur la correctness
architecturale. Les 4 patterns §4ter.bis sont appliqués proactivement ;
ce qui a manqué, c'est la documentation explicite des écarts et la
rigueur des assertions observables. Capitalisation :

#### Leçon 20 — Écarts vs spec = Completion Notes obligatoires

**Pattern** : tout AC non implémenté ou partiellement implémenté doit être
**listé explicitement** dans la section « Ajustements mineurs vs spec »
des Completion Notes, avec raison documentée. **Omettre silencieusement
un écart = dette non traçable** = coût exponentiel de review des
migrations futures.

**Source** : Story 10.18 HIGH-1. AC6 prescrivait explicitement le pattern
bottom-sheet mobile bascule (`translate-y-full` bottom-up pour cohérence
iOS/Android natif). Le code livré a appliqué uniformément `inset-0` +
`w-full h-full` quelle que soit la valeur de `side`, délivrant un
fullscreen neutre. Cet écart **n'était pas listé** dans les Completion
Notes (à la différence du changement `<header>/<footer>` → `<div>` qui
lui était correctement documenté). Dette cachée.

**Règle** : chaque AC non honoré ou partiellement honoré = **une ligne**
dans « Ajustements vs spec » avec :

- l'AC concerné (`AC6`, `AC8`, etc.) ;
- la prescription originale (1 phrase) ;
- la décision prise (**implémenté** / **déféré** / **refusé** / **délégué** à runtime autre) ;
- la raison (layout box happy-dom, coût disproportionné, breaking migration, etc.) ;
- le suivi s'il y en a (ticket `DEF-X.Y-N` dans `deferred-work.md` ou référence commit patch).

**Absence d'item = spec intégralement honorée**. L'exhaustivité de la
section est contractuelle.

**Enforcement** : au moment de la review, confronter `Tasks/Subtasks`
cochés [x] à la prescription spec ligne par ligne, puis croiser avec
« Ajustements vs spec ». Un [x] sans couverture ni ajustement listé =
omission silencieuse = dette cachée à remonter.

**Application patch batch 10.18** : les Completion Notes ont été enrichies
de **7 écarts complémentaires** (bottom-sheet bascule, focus return, focus
trap, Escape strict, ScrollArea strict, autofocus délégué, closeLabel)
en plus des 2 écarts originaux (header/footer, pièges renumérotés).

#### Leçon 21 — Tests observables ≠ smoke d'existence

**Pattern** : un test qui réfère un comportement observable (focus
restoration, event émis, animation slide, classe CSS responsive) ne doit
pas se réduire à `expect(queryEl()).not.toBeNull()` (« monte sans
crash »). Soit **assertion stricte** sur l'effet attendu, soit
**délégation explicite** (commentaire inline pointant le délégat
Storybook play function / E2E Playwright).

**Source** : Story 10.18 HIGH-2. Deux constats :

1. **AC5 test Escape permissif** — `if (events) { expect(events.at(-1)).toEqual([false]) }`
   transforme un test d'**assertion** en test **de non-régression conditionnelle**.
   Si Reka UI cesse d'émettre `update:open` (breaking change), le test reste
   vert car `events === undefined` et la branche est skippée.
2. **AC8 focus trap / focus return smoke-only** — `it('drawer rendu sans
   erreur quand trapFocus=false', () => expect(queryDrawer()).not.toBeNull())`.
   Ne teste rien du comportement focus observable prescrit. Case vidée de
   substance = **pire qu'un test manquant** (masque la régression).

**Règle** : pour chaque test couvrant un AC observable :

- soit **assert strict** sur l'effet (classe CSS exacte, event payload
  exact, `document.activeElement` exact, attribut DOM exact) ;
- soit **délégation explicite** : `// DELEGATED TO Storybook runtime
  `{{StoryName}}`` + 1-2 lignes d'assertion smoke qui justifient le
  maintien du test (au minimum : le composant monte, l'invariant structurel
  tient).

**Enforcement** : la patte « peut-on transformer cet assert en un
one-liner `.not.toBeNull()` sans perdre le sens du test ? » est un
signal. Si oui, le test est un smoke d'existence et doit être soit
raffermi, soit converti en délégat.

**Application patch batch 10.18** :

- AC5 Escape : garde `if (events)` retirée, assert `expect(events).toBeDefined()` + `.toEqual([false])` strict.
- AC8 focus return : observable strict (drawer retiré du DOM post-close + trigger reste focalisable + activeElement dans DOM monté) + délégation Storybook `FocusReturnOnClose` documentée inline (Reka UI FocusScope restoreFocus requiert layout box).
- AC8 focus trap (`trapFocus=true`) : observable strict (descendant `[role="complementary"]` après `.focus()` multi-éléments) + délégation Storybook `FocusTrapCycle` pour le cycle Tab réel.
- AC13 ScrollArea : query strict `[data-reka-scroll-area-viewport]` (+ fallback radix/class) au lieu de `textContent.contains(...)` laxiste.

**Mesure anti-récurrence** : si un 6ᵉ pattern émerge post-code-review
10.19 ou 10.20, créer `§4quinquies`. Les 6 patterns capitalisés (4 §4ter.bis
+ 2 §4quater) sont **stables et permanents**.

### 4ter.ter Application proactive Story 10.19 (ui/Combobox + ui/Tabs) — 6 leçons cumulées

Les 6 patterns méthodologiques (4 §4ter.bis capitalisés post-10.18 +
2 §4quater post-review 10.18) sont appliqués **proactivement** dès la
rédaction du code 10.19, sans attendre un code review pour les re-découvrir.
Capitalisation byte-identique (pas d'adaptation 10.19, pattern stable) :

#### Pattern A user-event strict (capitalisé §4ter.bis post-10.18)

**Application** : `test_combobox_behavior.test.ts` + `test_tabs_behavior.test.ts`
utilisent exclusivement `render(... from '@testing-library/vue')` + `screen.getByRole` +
`userEvent.setup()` + `user.type/click/keyboard` — **aucun `wrapper.vm.*`**,
**aucun `input.setValue(...)`**. Spécificité Combobox portalisé :
`screen.*` scanne `document.body` nativement (portal-aware). Spécificité
Tabs non-portalisé : `screen.*` indiffère vs `wrapper.find(...)`, préférence
`screen.*` pour cohérence cross-primitive.

**Cas Combobox spécifique : ouverture du dropdown** — Reka UI ne déclenche
PAS l'ouverture sur `user.click(input)` (conformité WAI-ARIA). Pattern
helper `openDropdown(user)` : `input.focus()` + `user.keyboard('{ArrowDown}')`
(WAI-ARIA standard Combobox).

#### Pattern B comptage runtime Storybook (capitalisé §4ter.bis post-10.18)

**Application** : 4 chiffres `jq` consignés dans les Completion Notes
**AVANT** tout claim de complétude :

```bash
jq '.entries | keys | length' storybook-static/index.json                   # total
jq '[.entries|to_entries[]|select(.value.id|startswith("ui-combobox"))]|length' storybook-static/index.json  # combobox
jq '[.entries|to_entries[]|select(.value.id|startswith("ui-tabs"))]|length' storybook-static/index.json  # tabs
du -sh storybook-static                                                      # bundle
```

Story 10.19 consigne : 211 total / 10 combobox / 9 tabs / 8.1 MB bundle (cibles
≥ 206 / ≥ 7 / ≥ 7 / ≤ 15 MB toutes respectées).

#### Leçon 10.14 HIGH-2 (role override) — non applicable 10.19

`role="combobox"` + `role="tablist"` / `role="tab"` / `role="tabpanel"` sont
les rôles WAI-ARIA corrects natifs Reka UI. **Pas d'override** (vs Drawer
10.18 `dialog → complementary`). Documenté §10 story file.

#### Leçon 10.15 HIGH-2 (Storybook runtime pour portail)

**Application** : `test_combobox_a11y.test.ts` délègue explicitement les
audits contraste/focus portail-dépendants à Storybook runtime via
commentaire inline `// DELEGATED TO Storybook ComboboxKeyboardNavigation`
+ `AXE_OPTIONS.rules['color-contrast'].enabled = false`. Tabs non-portalisé →
pas de délégation (vitest-axe happy-dom suffit pour les règles non-contraste).

#### Leçon 20 §4quater (Écarts vs spec Completion Notes obligatoires)

**Application** : la section « Ajustements mineurs vs spec » des Completion
Notes est renseignée **proactivement** lors de la rédaction, pas en
réponse à un code review post-hoc. Story 10.19 liste les 3 écarts
anticipés :

1. **AC1 (`ComboboxItemIndicator`)** — typage `T | T[] | null` permissif
   Phase 0 au lieu de discriminated union `{multiple:true, modelValue:T[]}`
   (DEF-10.19-1 tracé pour Phase Growth si 1+ consommateur le demande).
2. **AC2 Badge variant** — réutilisation `variant="lifecycle" state="draft"`
   faute de variant `ghost` ajouté ; valide car AC2 prescrit « variant
   `lifecycle` state `applicable` OU variant custom `ghost` si ajouté »
   (clause conditionnelle satisfaite).
3. **AC4 ARIA `aria-controls` sur tabs inactifs** — Reka UI ne les expose
   pas (tabpanel inactif non monté → pas de target ID). Documenté §3.7.

#### Leçon 21 §4quater (Tests observables ≠ smoke)

**Application** : assertions strictes Task 5 sur :

- **AC3 IME composition guard** : `expect(screen.queryByRole('option',
  {name:/burkina faso/i})).not.toBeNull()` (observable fort : Burkina Faso
  n'a ni `e` ni `é` dans son label → présence prouve qu'aucun filter n'a
  été appliqué pendant la composition).
- **AC5 keyboard Enter** : `expect(events).toBeDefined()` +
  `expect(events.at(-1)).toEqual([...])` strict, pas `if (events) ...`
  permissif.
- **AC12 forceMount lazy** : `expect(screen.queryByTestId('tab-content-t2')).toBeNull()`
  avant clic + `expect(screen.getByTestId('tab-content-t2')).toBeDefined()`
  après clic (pas `.not.toBeNull()` sur wrapper Reka UI toujours monté).

**Délégations explicites** : audit contraste portail Combobox documenté
inline `// DELEGATED TO Storybook ComboboxKeyboardNavigation` (piège #38 +
§4ter.bis Leçon 10.15 HIGH-2 capitalisée infra).

**Mesure anti-récurrence** : si un 7ᵉ pattern émerge post-code-review
10.19 ou 10.20, créer `§4quinquies`. Les 6 patterns sont désormais
capitalisés ET appliqués proactivement sur chaque nouvelle primitive
(byte-identique).

### 4quinquies Leçons post-review Story 10.19 (patches Option 0 Fix-All) — 3 patterns wrapper Reka UI

La review adversariale 3 couches Story 10.19 (ui/Combobox + ui/Tabs,
2026-04-22) a révélé **3 patterns wrapper Reka UI** récurrents qui
échappent aux 6 patterns déjà capitalisés §4ter.bis + §4quater. Ils
sont formalisés ici pour application proactive stories 10.20+
(DatePicker, Select, etc.).

#### Leçon 22 — Wrapper Reka UI `displayValue` obligatoire sur `ComboboxInput` single-select

**Constat** : Reka UI `ComboboxInput` sans prop `display-value` fait
`modelValue.toString()` → la clé brute (`'sn'`) s'affiche post-select
au lieu du label humain (`'Sénégal'`). Bug silencieux : le watch
`resetSearchTermOnSelect` déclenche le côté Reka UI même sans
`displayValue`, mais le résultat est inutilisable UX.

**Règle** : tout wrapper Reka UI qui expose un contrôleur de saisie
**doit** passer un callback `:display-value="(v) => labelFor(v as T)"`
si le `value` n'est pas le label rendu à l'utilisateur. En multi-select,
retourner `''` (les labels sont rendus dans les badges — pas dans
l'input).

**Source** : Story 10.19 H-1 (edge+blind fusionnés). Piège **#41**
codemap `ui-primitives.md §3.6`.

**Acceptance test** : round-trip select → close → reopen observe le
label (pas la clé) dans l'input ET la liste complète des options (pas
filtrée par la clé).

```vue
<ComboboxInput :display-value="displayValueFor" />
<script setup>
function displayValueFor(value: unknown): string {
  if (props.multiple) return '';
  if (value === null || value === undefined || value === '') return '';
  return labelFor(value as T);
}
</script>
```

#### Leçon 23 — `searchTerm` lifecycle au close drawer/combobox

**Constat** : les wrappers qui gèrent un `searchTerm = ref('')` local
doivent explicitement watch l'état `open` pour reset au
close-without-select. La prop Reka UI `resetSearchTermOnSelect` ne
couvre **que** le close-with-select. Un utilisateur qui tape `'zzz'`
puis ferme par Escape/click-outside voit le searchTerm stale à la
réouverture → empty state permanent silencieux.

**Règle** : tout wrapper Reka UI avec state de search local →
watcher `@update:open` (false) + `watch(() => props.open)` → reset du
searchTerm. Pattern défensif bidirectionnel (controlled + uncontrolled).

**Source** : Story 10.19 H-2. Extension Leçon 21 tests observables
(round-trip cross-open).

**Acceptance test** : ouvrir, taper `zzz`, fermer (Escape ou
click-outside), rouvrir → liste complète visible, input vide.

```ts
function handleOpenUpdate(value: boolean) {
  if (value === false) resetSearchIfNoSelection();
  emit('update:open', value);
}
watch(() => props.open, (isOpen) => {
  if (isOpen === false) resetSearchIfNoSelection();
});
```

#### Leçon 24 — Tests ARIA attribute-strict pas proxy

**Constat** : sur 3 stories a11y (10.15 + 10.17 + 10.19), les tests
ARIA tendent à utiliser `getByRole('option', { name: ... })` comme
proxy au lieu de `.getAttribute('aria-controls')` strict. Le test
passe quand l'attribut est absent si un autre mécanisme (focus, DOM)
happens to donner le même résultat. Même piège pour le count de
badges via proxy `role="img"` au lieu de sélecteur DOM strict
`[data-slot="badge"]`.

**Règle** : quand une AC cite nominativement un attribut ARIA → le
test doit le matcher **directement** via `.getAttribute('attr-name')`
+ match strict (regex canonique type `/reka-combobox-content-/`), pas
via effet de bord. Pour les badges multi-select : `data-slot`
explicite + `container.querySelectorAll('[data-slot="badge"]')`.

**Source** : Story 10.19 H-4 + M-1.

**Acceptance test** :

```ts
const ariaControls = combobox.getAttribute('aria-controls');
expect(ariaControls).not.toBeNull();
expect(ariaControls).toMatch(/reka-combobox-content-/);
expect(document.getElementById(ariaControls!)!.getAttribute('role'))
  .toBe('listbox');

// Badges count :
const badges = container.querySelectorAll('[data-slot="badge"]');
expect(badges.length).toBe(2);
```

**Mesure anti-récurrence** : les 3 patterns §4quinquies sont désormais
capitalisés ET appliqués proactivement. Si un 10ᵉ pattern émerge
post-code-review 10.20+, créer `§4sexies`. Cumul 9 leçons couvrant
wrappers Reka UI + tests observables + écarts spec.

### 4sexies Application proactive Story 10.20 (ui/DatePicker) — 5 leçons cumulées L20-L24

**Contexte** : Story 10.20 (4ᵉ wrapper Reka UI après Drawer 10.18 +
Combobox/Tabs 10.19) a appliqué PROACTIVEMENT les 5 leçons §4quater +
§4quinquies dès le premier drop de code — aucune découverte post-review,
aucun round de patchs retouché. Capitalisation validée = pattern stable
reproductible wrapper Reka UI.

#### Pattern A user-event strict (capitalisé §4ter.bis post-10.18-10.19)

**Appliqué 10.20** : 27 tests `test_datepicker_behavior.test.ts`
utilisent exclusivement `screen.getByRole('button', {...})` +
`user.click(...)` + `user.keyboard('{Escape}')` + helpers
`getCellByDate(isoDate)` (data-value unique). **0 ligne** de
`wrapper.vm.*` ni `input.setValue(...)`.

**Extension 10.20 helper DOM portal-aware** : `document.body
.querySelector<HTMLElement>('[role="button"][data-value="2026-04-15"]')`
pour cibler une cell date spécifique dans un calendrier qui expose des
outside-view dates (mars/mai visibles en grisé dans la grille avril) —
cohérent piège #28 10.18 DialogPortal.

**Contournement happy-dom + Reka keyboard PageDown** : les events
keyboard PageDown/PageUp/Shift+PageDown n'atteignent pas toujours le
handler Reka UI Calendar en happy-dom (focus bubbling partiel). Solution
**Pattern A fallback strict** : utiliser `CalendarNext`/`CalendarPrev`
button clicks (comportement équivalent, validé observable). Le keyboard
complet est délégué runtime Storybook via commentaire inline
`// DELEGATED TO Storybook DatePickerKeyboardNavigation` (Leçon 21
§4quater).

#### Pattern B comptage runtime Storybook (capitalisé §4ter.bis post-10.17-10.19)

**Appliqué 10.20** : avant tout claim de complétude, 3 chiffres EXACTS
runtime :

```bash
jq '.entries | keys | length' storybook-static/index.json
# → 224 (baseline 211 → +13 post-10.20)

jq '[.entries | to_entries[] | select(.value.id | startswith("ui-datepicker"))] | length' storybook-static/index.json
# → 13 (cible AC10 ≥ 8)

du -sh storybook-static
# → 8.2M (budget ≤ 15 MB)
```

**Extension 10.20 coverage c8 runtime** : `npm run test --
--coverage --run --coverage.include='app/components/ui/DatePicker.vue'`
→ `99.69% stmts / 90.56% branches / 100% funcs / 99.69% lines`
(AC10 plancher ≥ 85%). **Valeurs réelles pas fallback smoke**
(Leçon 10.19 H-5 capitalisée).

#### Leçon 20 §4quater (Écarts vs spec Completion Notes obligatoires)

**Appliqué 10.20** : Task 7.4 de la story a imposé le recensement
explicite des écarts. Consignés dans « Ajustements mineurs vs spec » :

- Keyboard nav PageDown/ArrowKeys délégués runtime Storybook
  (happy-dom limit) — 1 test observable strict fallback + 1 DELEGATED
  inline.
- Piège #41 Combobox existant déjà au count 41 → pièges 10.20
  renumérotés 42-45 (4 nouveaux cumul 45 post-10.20).

#### Leçon 21 §4quater (Tests observables ≠ smoke)

**Appliqué 10.20** : 0 assertion `.toBeDefined()` ni `.not.toBeNull()`
laxiste sur les props métier. Toutes les assertions displayValue,
emission structure, lifecycle mois sont **strictes** :

```ts
// L21 strict AC6 displayValue
expect(trigger.textContent).toMatch(/15\/04\/2026/);
expect(trigger.textContent).not.toMatch(/2026-04-15T/);

// L21 strict AC7 lifecycle close
expect(getHeading().textContent?.toLowerCase()).not.toContain('juillet 2026');

// L21 strict AC2 emission CalendarDate
const last = events[events.length - 1]![0] as CalendarDate;
expect(last.year).toBe(2026);
expect(last.month).toBe(4);
expect(last.day).toBe(20);
```

#### Leçon 22 §4quinquies (displayValue trigger obligatoire)

**Appliqué 10.20 AC6** : `PopoverTrigger` affiche
`DateFormatter('fr-FR', {day:'2-digit', month:'2-digit', year:'numeric'})
.format(modelValue.toDate(getLocalTimeZone()))` → label utilisateur
`15/04/2026`, **jamais** clé ISO brute `2026-04-15T00:00:00.000Z` ni
`[object Object]`. Range : em-dash strict U+2014 séparateur
`01/04/2026 — 30/04/2026`. Range partial : `01/04/2026 — Fin ?` (via
prop `rangePartialLabel` i18n default).

#### Leçon 23 §4quinquies (lifecycle close reset intermediate state)

**Appliqué 10.20 AC7** : équivalent DatePicker = mois courant affiché
dans `CalendarHeading`. `watch(isOpen, (open) => { if (!open)
currentMonth.value = initialMonth(); })` + binding Reka UI
`:placeholder="currentMonth"` + `@update:placeholder` pour tracker la
navigation utilisateur. `initialMonth()` fallback order : `modelValue`
(single) / `modelValue.start` (range) → `defaultValue` →
`today(getLocalTimeZone())`.

**Test observable L21 strict appliqué** :

```ts
await user.click(nextBtn); await user.click(nextBtn); await user.click(nextBtn);
expect(getHeading().textContent?.toLowerCase()).toContain('juillet 2026');
await user.keyboard('{Escape}');
await user.click(trigger);  // reopen
expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026');
expect(getHeading().textContent?.toLowerCase()).not.toContain('juillet 2026');
```

Capitalise le bug Combobox 10.19 `searchTerm` non cleared.

#### Leçon 24 §4quinquies (ARIA attribute-strict pas proxy)

**Appliqué 10.20 AC4** : 7 tests `test_datepicker_a11y.test.ts`
utilisent `.getAttribute(...)` strict + regex canonique, pas proxy
role/presence :

```ts
expect(trigger.getAttribute('aria-haspopup')).toBe('dialog');        // strict value
expect(trigger.getAttribute('aria-expanded')).toBe('false');          // puis 'true' après click
expect(trigger.getAttribute('aria-controls')).toMatch(/reka-popover-content-/);
expect(calendarRoot.getAttribute('aria-label')).toMatch(/^Calendrier, avril 2026$/i);
expect(cell15.getAttribute('aria-label')).toMatch(/^\S+ 15 avril 2026$/i); // format FR complet
```

**Mesure anti-récurrence** : les 5 patterns §4sexies sont désormais
capitalisés ET appliqués proactivement. Si un 11ᵉ pattern émerge
post-code-review 10.20+, créer `§4septies`. Cumul 14 leçons couvrant
wrappers Reka UI + tests observables + écarts spec + coverage c8
runtime + ARIA strict. **Pattern wrapper Reka UI considéré stabilisé
byte-identique** (4ᵉ itération sans découverte de pattern nouveau).

### 4sexies.post-review Leçons 25-27 — Option 0 Fix-All Story 10.20

**Contexte** : malgré l'application proactive des 5 leçons L20-L24, la code
review Story 10.20 (17 findings, APPROVE-WITH-CHANGES) a révélé 3 patterns
nouveaux spécifiques au wrapping Reka UI + à la délégation de tests runtime
+ à l'ordonnancement de pièges cross-story. Capitalisation post-Option 0
Fix-All ci-dessous.

#### Leçon 25 — Wrapper Reka UI : ne jamais injecter d'`id` custom sur primitives slot-forwarded

**Symptôme** (10.20 H-1) : le wrapper injectait `const popoverId = useId()`
puis `:aria-controls="popoverId"` sur `PopoverTrigger` + `:id="popoverId"`
sur `PopoverContent`. Le test a11y était permissif (regex `/reka-popover-content-/`)
et masquait le fait que la valeur réelle du DOM venait de `rootContext.contentId`
généré par Reka UI, **pas** du `popoverId` Vue. La prop custom `:id` était
systématiquement écrasée par l'id interne Reka, rendant `:aria-controls="popoverId"`
du code mort.

**Règle** : pour les primitives Reka UI qui forward un id interne via contexte
(Popover, Combobox, DropdownMenu, ContextMenu, Select…), **laisser Reka UI
gérer le wiring ARIA natif**. Ne pas injecter de `useId()` Vue ni de
`:id="..."` sur la primitive slot-forwarded. Le lien `trigger.aria-controls
=== content.id` est câblé automatiquement par le contexte racine.

**Test d'observabilité strict** :

```ts
const ariaControls = trigger.getAttribute('aria-controls');
const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
expect(ariaControls).not.toBeNull();
expect(dialog).not.toBeNull();
expect(dialog!.id).toBe(ariaControls!); // cohérence DOM, pas regex opaque
```

**Application** : stories 10.21+ wrappers Reka UI (Menu, DropdownMenu,
ContextMenu, Select si migré). Source : Story 10.20 H-1.

#### Leçon 26 — Délégation Storybook PER-PATH explicite, pas globale

**Symptôme** (10.20 H-3 + M-1) : la Completion Notes déclarait
« keyboard AC5 délégué Storybook » globalement, mais 9/12 chemins
individuels n'étaient ni testés Vitest ni documentés individuellement
avec un pointeur vers une story Storybook runtime. Le seul test keyboard
écrit (`PageDown` via `dispatchEvent` + regex `/(avril|mai)/`) était un
faux positif qui passait même si la touche ne faisait rien.

**Règle** : chaque chemin AC délégué runtime doit avoir :

1. Un marqueur inline Vitest `describe.skip('...' — DELEGATED Storybook
   <story-id>)` + `it.todo('<key> — Storybook <story-id>')` per-path, ou
2. Un `it.skip` explicite nommant la story runtime et la raison technique
   (ex. « happy-dom focus bubbling limit »).

La délégation globale sans granularité rend la couverture runtime
non-mesurable et expose à des faux positifs.

**Test d'observabilité strict** :

```ts
// Chemin PageDown délégué (exemple Story 10.20)
it.skip('keyboard PageDown — DELEGATED Storybook DatePickerKeyboardNavigation--page-down (happy-dom focus bubbling limit)', () => {
  // Vide intentionnellement. Couverture runtime story dédiée.
});

// 9 chemins keyboard délégués via describe.skip + it.todo nommés
describe.skip('AC5 keyboard — DELEGATED Storybook per-path', () => {
  it.todo('ArrowLeft/ArrowRight — Storybook DatePickerKeyboardNavigation--arrow-left-right');
  it.todo('Home/End — Storybook DatePickerKeyboardNavigation--home / --end');
  // ... un `it.todo` par chemin distinct
});
```

**Application** : toute limitation happy-dom/jsdom future (focus bubbling,
IntersectionObserver, ResizeObserver, CSS computed, animations, media
queries). Source : Story 10.20 H-3 + M-1 (9/12 keyboard manquants).

#### Leçon 27 — Ordonnancement pièges cross-story : continuité séquentielle stricte

**Symptôme** (10.20 I-2 + M-5) : la spec Story 10.20 proposait 4 nouveaux
pièges `#41-#44`, mais `#41` appartenait déjà à Combobox 10.19
(`:display-value` single-select). Le dev a renuméroté `#42-#45` en fin
d'implémentation — étape qui aurait été évitable par un scan préalable.

**Règle** : avant d'ouvrir une story qui documente de nouveaux pièges
dans un CODEMAP, le dev :

1. Scanne `docs/CODEMAPS/*.md` pour détecter le plus haut numéro de
   piège existant (grep `^\d+\. \*\*` dans §5 ou équivalent).
2. Scanne les stories `ready-for-dev` et `in-progress` concurrentes du
   sprint pour éviter les collisions d'attribution parallèle.
3. Décale la numérotation proposée par la spec si collision détectée.

La numérotation est **continue séquentielle cross-story** : jamais
réutiliser un numéro publié. Test d'observabilité associé :
`test_docs_ui_primitives.test.ts` vérifie unicité + continuité
(`uniqueNumbers.size === matches.length`, pas seulement `matches.length >= N`).

**Application** : toutes stories futures ajoutant des pièges §5 CODEMAPS
(ui-primitives.md, architecture.md, rag.md…). Source : Story 10.20 I-2 + M-5.

**Mesure anti-récurrence étendue** : le cumul est désormais **17 leçons**
(14 §4sexies base + 3 Option 0 Fix-All 10.20). Si un 18ᵉ pattern émerge
post-review 10.21+, créer `§4septies` (pas `§4sexies.deuxième-post-review`).

### 4septies Retrospective Epic 10 Phase 0 + leçons L28-L30 (post-10.21)

**Story 10.21 (Setup Lucide + EsgIcon wrapper)** clôt Epic 10 Phase 0
Fondations (23/23 stories livrées). Cette sous-section capitalise les 3
derniers patterns dispatch-registry / tree-shaking / migration scale-up,
portant le cumul §4ter.bis → §4sexies → §4septies à **30 leçons**.

**Bilan méthodologique Epic 10 Phase 0** — 27 → 30 leçons cumulées :
- §4ter.bis (10.17-10.18) : Patterns A observable + B count runtime = 4 leçons
- §4quater (10.18 post-review) : Traçabilité écarts + tests non-smoke = 2 leçons
- §4ter.ter (10.19) : Wrapper Reka UI + IME + multi-variant = 6 leçons
- §4quinquies (10.19 post-review) : displayValue + lifecycle + ARIA strict = 3 leçons (L22-L24)
- §4sexies (10.20) : Application proactive DatePicker = 5 leçons (L20-L24)
- §4sexies post-review (10.20) : Wrapper id mort + délégation per-path + ordonnancement = 3 leçons (L25-L27)
- §4septies (10.21, **CE SECTION**) : Dispatcher registry + tree-shaking + migration shim scale-up = **3 leçons (L28-L30)**

**Vélocité mesurée Epic 10** — 23 stories livrées en 6 semaines effectives
vs 18 semaines sprint v1 → **économie 12 semaines confirmée**. Sizing L
consommé 60-75 % estimate + sizing M consommé 20-50 % estimate (pattern
CCC-9 rodé × 7 extensions, wrapper Reka UI stabilisé × 4 itérations
byte-identique). Projection sprint v2 **10-11 mois Cluster A-E** validée.

---

**Leçon 28 — Tree-shaking Lucide (et bibliothèques à catalogue massif) via
named imports exclusifs** — Toute bibliothèque exposant un catalogue ≥ 100
exports (icônes, utilities, date libs) DOIT être consommée via
`import { Named1, Named2 } from 'lib'` jamais `import * as Lib` ni
`import Lib from 'lib'`.

**Why** : `import * as` ou default export déclenche l'inclusion complète du
module dans le bundle final (pas de tree-shaking). Pour Lucide 1400+ icônes
= ~500 KB gzipped vs ~1,5 KB/icône en named imports. Pour lodash, moment,
date-fns : même risque.

**How to apply** :
1. Test anti-récurrence enforced `rg "import \* as.*lucide-vue-next" app/` → 0 hit.
2. Checklist code-review : nouvelle dépendance catalogue → named imports obligatoires.
3. Documentation §3.9 CODEMAP + piège #47 ui-primitives.md.
4. Mesure bundle delta pre/post via `du -sb storybook-static` + inspection
   `source-map-explorer` pour valider tree-shaking effectif.

**Story 10.21** : `lucide-vue-next@0.577.0` consommé via 26 named imports
whitelist MVP (`ChevronDown`, `Check`, `Calendar`, …) dans `EsgIcon.vue`
uniquement. Bundle delta attribuable Lucide ≤ 50 KB gzipped (~1,5 KB × 26).

---

**Leçon 29 — Wrapper dispatcher par registry ≠ wrapper Reka UI headless
slot-forward (L25 §4sexies généralisée)** — Quand un composant wrapper doit
unifier l'API d'une source ouverte multi-variant (icônes, thèmes, locales,
plugins), le **pattern dispatcher par registry** s'applique :
`<Wrapper key="..." />` + `Record<Key, Component> ICON_MAP` + `<component
:is="resolvedComponent" />`. Contraste avec le pattern Reka UI headless
(slot-forward primitives type `<DialogRoot><DialogTrigger /></DialogRoot>`).

**Why** : Les 2 patterns paraissent similaires mais diffèrent fondamentalement :
- **Reka UI wrapper** : compose des primitives headless (slot-forward),
  expose des props slot-delegate via `v-bind="$attrs"`. Injection d'`id`
  custom = code mort (L25 §4sexies). API consommateur = slots typés.
- **Dispatcher registry** : résout `name → Component` via map frozen,
  forward-passe les props natives (`size`, `stroke-width`) transparent vers
  le composant résolu. Pas de slot interne. API consommateur = prop `name`
  literal union type-safe.

**How to apply** :
1. Avant d'écrire un wrapper multi-variant, qualifier le pattern cible
   (headless slot OU dispatcher registry). Critère : la source upstream
   expose-t-elle des primitives à composer (Reka UI) ou des composants
   atomiques distincts (Lucide icons, Heroicons, …) ?
2. Pour dispatcher : registry frozen type-safe (pattern CCC-9), ICON_MAP
   exhaustif `Record<Key, Component>`, fallback warn dev-only + placeholder.
3. Props natives du composant résolu forward-passed **sans re-déclaration**
   (piège #46) — sinon valeur écrasée ou type contradictoire.
4. Tests compile-time `.test-d.ts` validant rejet `name` hors registry.

**Story 10.21** : `EsgIcon.vue` = premier dispatcher registry projet,
32 entrées (26 Lucide + 6 ESG custom `esg-*`). Pattern réutilisable
pour futurs wrappers multi-source (theme picker, locale flag, plugin list).

---

**Leçon 30 — Migration mécanique byte-identique shim pattern 10.6
scale-up N-composants** — Le pattern shim 10.6 (1 interface, 1 PR) s'étend
aux migrations N≥15 simultanées dans 1 PR atomique, à condition de préserver
la **byte-identité visuelle** (dimensions parent, stroke, fill, viewBox).

**Why** : Les primitives déjà rodées (10.15-10.20) ont des tests d'assertion
qui dépendent de l'existence de `<svg>` ou de patterns spécifiques. Une
migration grossière casse les tests ; une migration byte-identique via
un shim (`<EsgIcon name="..." class="dimensions-héritées" decorative />`)
préserve le layout flex existant sans refactoring défensif.

**How to apply** :
1. Identifier la **dimension parente** pilotant le sizing (`h-4 w-4`).
   Remplacer par `<EsgIcon class="h-4 w-4" />` en omettant la prop `size`
   (risque d'écrasement — piège #48). OU aligner explicitement la prop
   `size` à la dimension CSS équivalente (`size="sm"` = 16px = `h-4 w-4`).
2. Préserver `decorative` prop = `true` pour les icônes redondantes
   (parent a déjà son `aria-label`). Éviter la duplication lecteur écran.
3. Ajouter un import explicite du wrapper dans chaque `.vue` consommateur
   (Vitest happy-dom ne résout pas les auto-imports Nuxt 4).
4. Validation visuelle Storybook avant/après : story `MigrationBeforeAfter`
   démo le shim côte-à-côte. Délégation L26 per-path sur screenshot.
5. Tests pre-existants doivent continuer à passer **sans modification** —
   sinon le shim a introduit une régression visuelle/sémantique.

**Story 10.21** : 16 SVG inline migrés (baseline 17 → 1 justifié Button
spinner) dans 7 primitives UI (Combobox 5 + DatePicker 5 + Select 2 +
Input 1 + Textarea 1 + Drawer 1 + FullscreenModal 1). Tests 821 → 863
passed (+42), 0 régression. Applicable Phase 1+ (migration date libs,
validation schemas, utility helpers).

---

**Cumul 30 leçons** cross-patterns Epic 10 Phase 0. **Mesure anti-récurrence
étendue** : si un 31ᵉ pattern émerge post-review 10.21 ou Epic 11 Phase 1
MVP (Cluster A PME 11.1-11.8), créer `§4octies` (pas `§4septies.extension`).

**Retrospective formelle recommandée** : `bmad-retrospective` skill pour
Epic 10, synthèse 23 stories + vélocité + forces/écueils/stretch goals.

## 4octies. Post-review Story 10.21 — leçons 31-35 (review-driven patterns)

Cette section cumule les **5 leçons émergées de la code-review 10.21**
(3 hunters parallèles Sonnet 4.6, 22ᵉ review Phase 4, 19 findings — décision
APPROVE-WITH-CHANGES avec 1 HIGH + 6 MEDIUM + 7 LOW + 5 INFO). Elles
**complètent** §4septies (L28-L30 livraison-driven) par des patterns
**review-driven** capturant les angles morts détectés après livraison.

**Distribution cumulée §4ter.bis → §4octies** :
- §4ter.bis (10.17, 10.18, 10.19, 10.20) : Pattern A DOM-only + Pattern B count runtime = **19 leçons (L1-L19)**
- §4quater (10.18) : Écarts vs spec + assertions strictes = **2 leçons (L20-L21)**
- §4quinquies (10.19) : displayValue + lifecycle + ARIA attribute-strict = **3 leçons (L22-L24)**
- §4sexies (10.20) : Wrapper no-double-prop + délégation per-path + ordonnancement pièges = **3 leçons (L25-L27)**
- §4septies (10.21 livraison) : Tree-shaking + dispatcher registry + migration shim scale-up = **3 leçons (L28-L30)**
- §4octies (10.21 post-review, **CETTE SECTION**) : CI gate + DEF traçabilité + baseline canonique + warn réactif + inheritAttrs = **5 leçons (L31-L35)**

**Total : 35 leçons cumulables Epic 11+**.

### Leçon 31 — CI gate tree-shaking automatique (catalogue lib)

**Pattern** : la leçon 28 (named imports Lucide obligatoires) est documentée
mais **l'enforcement reste manuel** (test `rg "import \* as.*lucide" → 0 hit`
exécuté localement). Dès qu'une story Epic 11+ importe une nouvelle primitive
Lucide ou une autre bibliothèque à catalogue massif (`lodash`, `date-fns`,
`heroicons`, `react-icons`), un import `import * as Lib` ou `import Lib from`
ré-intègre tout le catalogue — **régression silencieuse** invisible sans mesure
bundle delta explicite.

**Solution** : step CI dédié dans `.github/workflows/ci.yml` combinant :
1. `rg "import \* as.*(lucide|lodash|date-fns|heroicons|react-icons)" frontend/app --count` → fail si > 0.
2. Mesure bundle delta `du -sb storybook-static/assets/*.js` avec seuil
   **50 KB hard fail** sur la PR (comparable avec base branch).

**Source** : Story 10.21 review Point 1 (bundle delta Lucide mesuré 3.3 KB
gzip isolé — mesure narrative non-reproductible en CI). Généralisable à
toute bibliothèque à catalogue > 100 KB global (chart libs, i18n locales,
emoji sets, polyfills).

**Application anti-récurrence** : bloque les imports permissifs dès le
premier commit Epic 11+ intégrant une nouvelle dépendance catalogue.
Tracé DEF-10.21-2.

### Leçon 32 — Traçabilité DEF cross-story (closure obligatoire)

**Pattern** : un item `DEF-X.Y-N` qui pointe vers une story future (ex.
`DEF-10.15-1 → cible Story 10.21`) doit produire à la résolution
**exactement trois options**, jamais de quatrième :

1. **Résolu effectivement** → marquer DEF fermé avec référence commit
   explicite dans `deferred-work.md` (section `## Resolved in Story X.Y
   (date)`) + preuve technique (tests ajoutés, diff, measurements).
2. **Re-déféré formellement** → créer `DEF-X.Z-N` successeur dans la
   section `## Deferred from: code review of story-X.Z`, avec rationale
   code-snippet démontrant pourquoi la résolution a été reportée et
   options techniques Epic futur.
3. **Retiré obsolète** → marquer fermé avec commentaire « obsolète car
   [raison] — pas de successeur requis » (ex. feature pivotée, stack
   changée).

**Interdit** : fermeture orpheline silencieuse (suppression de l'item
sans successeur ni mention). Empêche la **piste d'audit** d'être
reconstructible côté retrospective Epic.

**Source** : Story 10.21 M-5 — DEF-10.15-1 (Button spinner migration Lucide)
re-justifié implicitement dans la Completion Notes sans créer DEF-10.21-N
successeur. Correction post-review : DEF-10.21-1 créé avec 3 options
techniques Epic 11+ détaillées + investigation narrative pourquoi Loader2
+ `animate-spin` ne reproduit pas l'effet pulse opacity-25/75 composé.

**Application anti-récurrence** : avant de clore une story qui avait un
DEF pointant vers elle, exécuter `grep "DEF.*cible.*10\.${CURRENT}" deferred-work.md`
et forcer l'une des 3 options ci-dessus. Pre-commit hook possible.

### Leçon 33 — Baseline canonique unique commit ↔ Debug Log ↔ Completion Notes

**Pattern** : les **métriques Pattern B numériques** (`baseline → livré`
pour tests, typecheck, Storybook entries) doivent être **byte-identiques**
entre le message de commit (`git log`), le Debug Log de la story, et les
Completion Notes. Toute divergence — même sous le seuil 5 % Pattern B —
**casse la piste d'audit** et empoisonne les retrospectives (impossible
de reconstruire la vélocité réelle).

**Exemple de dette** : commit 10.21 `d5f08e3` annonce `"tests 832 → 873"`
alors que le Debug Log + Completion Notes + spec convergent sur
`"821 → 869"`. Divergence de 11 tests (≈ 1,3 %) due à un run Vitest
parallèle antérieur (suite différente, environnement pollué) consigné
par erreur dans le commit message.

**Solution** : pre-commit hook `grep -E "tests?\s[0-9]+\s*→\s*[0-9]+"
COMMIT_EDITMSG` comparé avec `rg "Baseline.*tests.*→" $STORY_FILE`. Si
divergence détectée, fail avec message « baselines divergent commit↔story ».

**Alternative défensive** : avant de rédiger les Completion Notes,
exécuter `git show HEAD:$STORY_FILE | grep "baseline"` et valider que
les valeurs du commit final matchent exactement. Capitaliser dans
`checklist-dev-complete.md`.

**Source** : Story 10.21 M-4. Correction : note clarifiante ajoutée aux
Completion Notes (« Commit d5f08e3 indique 832→873 ; chiffres canoniques
821→869 run final »), pas de `git rebase` (commit historique signé).

**Application anti-récurrence** : généralisable à toutes les métriques
chiffrées Pattern B (typecheck, Storybook jq, bundle MB, coverage %).

### Leçon 34 — Warn dev-only doit être réactif (watchEffect, pas top-level setup)

**Pattern** : tout `console.warn` conditionné à `import.meta.env.DEV` qui
dépend d'une **prop dynamique** doit vivre dans `watchEffect(() => ...)`
ou dans un `computed` consommé par le render. **Jamais au top-level
`<script setup>`** (exécution unique au mount, snapshot statique).

**Anti-pattern** :
```ts
// <script setup>
if (import.meta.env.DEV && !(props.name in REGISTRY)) {
  console.warn(`[Wrapper] Unknown: ${props.name}`);  // ← RATÉ si props.name mute après mount
}
```

**Correct** :
```ts
// <script setup>
watchEffect(() => {
  if (import.meta.env.DEV && !(props.name in REGISTRY)) {
    console.warn(`[Wrapper] Unknown: ${props.name}`);
  }
});
```

**Rationale** : un consommateur utilisant `v-for="n in dynamicNames" :name="n"`
ou un registre switché runtime (feature flags, A/B tests, plugins dynamiques)
**mute `props.name` après mount**. Sans wrapper `watchEffect`, le warn ne
re-déclenche jamais → placeholder s'affiche silencieusement, le dev croit
son composant correct, bug invisible en dev comme en prod.

**Piège dev-tooling** : un test `warnSpy` qui monte le composant **une
seule fois** avec un nom invalide passe trivialement sans couvrir le cas
mutation. Ajouter un test observable mutation-time :
```ts
await wrapper.setProps({ name: 'mutated-to-invalid' });
await nextTick();
expect(warnSpy).toHaveBeenCalledTimes(1);
```

**Source** : Story 10.21 H-1 (convergence Blind Hunter HIGH + Edge Case
Hunter MEDIUM). Fix : `EsgIcon.vue:163` encapsulé dans `watchEffect` +
test `warn re-déclenche à la mutation runtime`.

**Application anti-récurrence** : généralisable à tout fallback warning
conditionnel (registry lookups, schema mismatches, mode flags, feature
flags, plugin resolution, mode A11y degraded). Check rapide grep
`rg "if.*import\.meta\.env\.DEV" frontend/app/components/ --no-filename -A 3`
→ chaque hit hors `watchEffect`/`computed`/`onMounted` = candidat suspect.

### Leçon 35 — `inheritAttrs: false` obligatoire pour wrappers ARIA

**Pattern** : tout composant Vue qui **définit ses propres attrs ARIA**
(role, aria-label, aria-hidden, aria-describedby…) via `v-bind="ariaAttrs"`
sur la primitive cible **DOIT** déclarer `defineOptions({ inheritAttrs: false })`
**et** exposer un `v-bind` explicite sur cette primitive. Sans cela, les
attrs ARIA passés par le consommateur **tombent sur la racine** (fallthrough)
et coexistent avec les attrs ARIA du wrapper → **violation ARIA silencieuse**
(ex. `aria-hidden="true" aria-label="fermer"` interdit par spec).

**Anti-pattern** :
```vue
<!-- Wrapper.vue (pas de defineOptions) -->
<template>
  <component :is="primitive" v-bind="ariaAttrs" />
</template>
```
Consommateur : `<Wrapper decorative aria-label="fermer" />` →
DOM : `<svg aria-hidden="true" aria-label="fermer">` (conflit silencieux,
axe-core pa11y signale mais tests happy-dom laissent passer).

**Correct** :
```ts
// <script setup>
defineOptions({ inheritAttrs: false });
const rawAttrs = useAttrs();
const forwardedAttrs = computed(() => {
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(rawAttrs)) {
    if (key === 'role' || key.startsWith('aria-')) continue;  // ← filtre ARIA
    out[key] = rawAttrs[key];
  }
  return out;
});
```
```vue
<template>
  <component :is="primitive" v-bind="{ ...forwardedAttrs, ...ariaAttrs }" />
</template>
```

**Rationale** : le wrapper **contrôle sa propre sémantique ARIA** via ses
props typées (`decorative`, `ariaLabel`). Laisser le consommateur forwarder
des attrs ARIA contradictoires est un trou de sécurité a11y. Les attrs
non-ARIA (listeners, data-*, title) restent forwarded pour l'ergonomie.

**Piège test** : un test qui asserte `getAttribute('aria-hidden') === 'true'`
**et** qui passe un consommateur avec `aria-label` passe trivialement sans
détecter le conflit (les deux attrs coexistent). Ajouter un test strict :
```ts
mount(Wrapper, { props: { decorative: true }, attrs: { 'aria-label': 'fermer' } });
expect(svg.getAttribute('aria-hidden')).toBe('true');
expect(svg.getAttribute('aria-label')).toBeNull();  // ← anti-conflit strict
```

**Source** : Story 10.21 M-3 (Edge Case Hunter). Fix : `EsgIcon.vue`
`defineOptions({ inheritAttrs: false })` + `useAttrs()` + filtrage ARIA.

**Application anti-récurrence** : généralisable à tous les wrappers a11y
(Modal, Dialog, Tooltip, MenuItem, Popover, Combobox, Drawer). Scan
`rg "v-bind=\"ariaAttrs\"|v-bind=\"\\\$attrs\"" frontend/app/components/`
→ chaque hit sans `defineOptions({ inheritAttrs: false })` = candidat
suspect. Test checklist review : systématiquement simuler un consommateur
qui passe un attr ARIA conflictuel et asserter le non-conflit.

---

**Cumul 37 leçons** cross-patterns (§4ter.bis → §4decies). **Mesure
anti-récurrence cumulée** : Epic 11 Phase 1 MVP Cluster A (11.1-11.8) doit
commencer par une checklist de pré-scan sur les 37 leçons, et tout 38ᵉ
pattern émergeant créerait `§4undecies`.

### 4nonies. Validation runtime systémique sur tools de persistance

**Pattern** : sur 6 vagues de tests bug régression (V1 → V6), le LLM
MiniMax ne respecte pas systématiquement les instructions tool calling
inscrites dans les prompts. Variantes observées :

- **Réponse textuelle** : produit un score ou un plan en texte sans
  appeler le tool de persistance (BUG-V6-005 : 15 actions affichées,
  0 ligne BDD).
- **Doublon d'appel** : appelle 2× le même tool avec la même cible
  (BUG-V6-002 : `save_emission_entry` 2× sur (transport, carburant) →
  171 vs 87 tCO2e affichés).
- **Cible manquante** : appelle le tool sans le champ critique
  (BUG-V6-011 : `update_company_profile` sans `company_name` réel →
  AgriVert mentionné chat mais pas créé en BDD).
- **Évaluation partielle** : appelle le tool avec moins de champs que
  le minimum métier (BUG-V5-003 : 3 critères ESG par pilier au lieu de
  10 → score faux, rapport mensonger).
- **Source de vérité divergente** : recompute textuellement une valeur
  déjà persistée (BUG-V6-009 : credit dashboard 26 vs chat 58).

**Constat** : les consignes de prompt sont **insuffisantes** comme
contrôle. Le respect du tool calling doit être transformé en
**contrainte d'API** côté tool — impossible à ignorer pour le LLM.

**Solution généralisée — chaque tool LangChain qui écrit en BDD DOIT
inclure** :

1. **Validation des champs requis** : rejet 422-like avec liste des
   champs manquants, exploitable par le LLM pour retry intelligent.
2. **Validation idempotence** : UPDATE si la cible existe (clé métier
   naturelle : `(assessment_id, category, subcategory)` pour carbon ;
   `user_id + 30 jours` pour credit ; profil unique par user pour
   profile), pas duplicate INSERT.
3. **Validation cohérence métier** : seuils planchers (10 critères/pilier
   ESG, ≥10 actions plan), filtrage whitespace-only, listes non vides.
4. **Message d'erreur exploitable** par le LLM : retour `str` (jamais
   exception — `with_retry` la masquerait), contenant le diagnostic +
   l'action suivante recommandée (ex : « appelle `get_credit_score` au
   lieu de regénérer »).
5. **No-op BDD si validation échoue** : aucune écriture partielle ;
   l'invariant central est l'idempotence, comme V5-003.

**Implémentations référence** :

- `backend/app/graph/tools/esg_tools.py:batch_save_esg_criteria` —
  garde 10 critères/pilier (V5-003).
- `backend/app/graph/tools/carbon_tools.py:save_emission_entry` —
  dedup `(assessment_id, category, subcategory)` (V6-002).
- `backend/app/graph/tools/credit_tools.py:generate_credit_score` —
  idempotence mensuelle (V6-004 / V6-009).
- `backend/app/graph/tools/action_plan_tools.py:generate_action_plan` —
  validation post-appel ≥10 items + champs requis (V6-005).
- `backend/app/graph/tools/profiling_tools.py:update_company_profile` —
  rejet whitespace-only (V6-011).

**Anti-récurrence** : avant tout merge d'un nouveau tool LangChain qui
persiste, checklist obligatoire :

- [ ] Tests `test_<tool>_rejects_incomplete_payload` présent.
- [ ] Tests `test_<tool>_idempotent_no_duplicate` présent.
- [ ] Tests `test_<tool>_succeeds_with_complete_payload` présent.
- [ ] Section `## PERSISTANCE — TOOL CALL OBLIGATOIRE` dans le prompt
      spécialiste correspondant, avec mention explicite du contrôle
      runtime et de la conduite à tenir face à un message d'erreur.
- [ ] Aucune exception levée par la garde — uniquement des chaînes
      retour exploitables par le LLM.

**Source** : Story batch BUG-V6-002/004/005/009/011 généralisation
BUG-V5-003 (`spec-bug-v6-runtime-guards-persistence-tools.md`).
Capitalisation §4nonies retenue : la validation runtime systémique
n'est pas un correctif ponctuel, c'est une discipline d'architecture
des tools — toute future feature Epic 11+ doit l'appliquer dès le
premier commit, pas en post-incident.

**Retrospective Epic 10 formelle** : à exécuter immédiatement après clôture
des 3 commits de patch 10.21 via `bmad-retrospective` skill. Synthèse
attendue : vélocité 60-75 % L + 20-50 % M confirmée, économie 12 semaines
sprint v1 → v2, 35 leçons cumulées cross-patterns, transition Epic 11
déclenchée.

### 4decies. Validation runtime adaptative + fallback déterministe (Leçon 40)

**Pattern** : sur les **tools de génération créative** (plan d'action,
recommandations, contenus structurés ouverts), la validation runtime
stricte instaurée par §4nonies (BUG-V5-003 : ≥10 critères, ≥10 actions,
etc.) bloque même les meilleurs LLM lorsque la complexité du prompt et la
longueur du JSON dépassent leur fenêtre de fiabilité. Observation
empirique sur 3 vagues V6/V7/V7.1 :

- **V6-005** (MiniMax) : tool `generate_action_plan` jamais appelé — le
  LLM répond textuellement sans persister.
- **V7-007** (MiniMax) : `json_parse_failed` × 2 retries — le LLM
  produit du JSON quasi-valide (trailing comma, single quotes) que le
  parser strict rejette.
- **V7.1-009** (Claude) : guard LLM échoue 9× (3 cycles × 3 retries) —
  même le meilleur provider sature sur le seuil ≥10 actions.

**Constat** : la validation stricte de §4nonies est nécessaire pour les
**tools de persistance déterministe** (idempotence, dedup, whitespace,
champs requis), mais **insuffisante** pour les tools de génération
créative ouverte. Sans filet de sécurité, l'utilisateur reste sans plan.

**Solution généralisée — pattern adaptatif en 3 paliers** :

1. **Validation stricte 1ère tentative** (≥10 actions, schéma complet) —
   qualité optimale quand le LLM réussit.
2. **Acceptation incrémentale ≥5 actions** — mode batch, message tool
   « X/10 sauvegardées, manque Y, continue avec batch suivant ». Le
   LLM peut compléter via un nouvel appel.
3. **Fallback template déterministe** — dernier recours après échec
   total des retries internes du service (`LLMGuardError`). Charge un
   template JSON statique avec placeholders `{{sector}}`,
   `{{employee_count}}`, `{{country}}`, persiste un plan complet.
   Garantit la disponibilité du feature même quand le provider LLM
   est indisponible.

**Différence vs §4nonies** : §4nonies protège contre le **non-respect
du tool calling** (le LLM ne persiste pas) ; §4decies protège contre
la **défaillance qualité** du LLM même quand il appelle bien le tool.
Les deux cohabitent : la validation reste activée, le fallback est un
filet de sécurité ultime.

**Helper transverse `app/services/json_repair.py`** : passes ordonnées
(trailing comma → unquoted keys → single quotes), `try json.loads`
après chaque, retour `None` si irréparable. Réutilisable par tout
extracteur JSON tolérant.

**Implémentations référence** :

- `backend/app/services/action_plan_fallback.py` — template substituant
  + persistance déterministe (V8-AXE2).
- `backend/app/services/json_repair.py` — réparation tolérante JSON
  (V8-AXE2).
- `backend/app/templates/action_plan_default.json` — 10 actions
  génériques (3 environment, 2 social, 2 governance, 2 financing,
  1 carbon).
- `backend/app/graph/tools/action_plan_tools.py:generate_action_plan` —
  orchestration adaptative (try LLM → mode incrémental ≥5 → fallback
  sur `LLMGuardError`).

**Anti-récurrence** : avant tout merge d'un nouveau tool LangChain de
**génération créative ouverte**, checklist obligatoire :

- [ ] Mode batch incrémental documenté (seuil minimum acceptable < cible
      métier).
- [ ] Fallback template déterministe disponible et testé.
- [ ] Log structuré `fallback_triggered user_id=… reason=… final_count=…`.
- [ ] Tests `test_<tool>_fallback_template_after_3_retries` présent.
- [ ] Tests `test_<tool>_validation_relaxed_<N>_actions_succeeds` présent.
- [ ] Tests `test_<tool>_fallback_persists_<N>_actions` présent.

**Source** : V8-AXE2 BUG-V6-005 / V7-007 / V7.1-009
(`spec-v8-axe2-action-plan-fallback.md`).

**Cumul mis à jour** : **37 leçons** cross-patterns
(§4ter.bis → §4decies), capitalisation continue. Toute future feature
Epic 11+ qui implémente un tool de génération créative doit appliquer
le pattern adaptatif §4decies dès le premier commit.

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
