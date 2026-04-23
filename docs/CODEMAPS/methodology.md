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
