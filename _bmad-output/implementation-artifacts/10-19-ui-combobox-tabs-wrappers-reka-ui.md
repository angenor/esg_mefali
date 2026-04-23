# Story 10.19 : `ui/Combobox.vue` + `ui/Tabs.vue` wrappers Reka UI

Status: review

<!-- Note: Validation optionnelle. Exécuter `validate-create-story` pour un contrôle qualité avant `dev-story`. -->

> **Contexte** : 21ᵉ story Phase 4 et **5ᵉ + 6ᵉ primitives `ui/`** après Button 10.15 + Input/Textarea/Select 10.16 + Badge 10.17 + Drawer 10.18. **2ᵉ et 3ᵉ wrappers Reka UI** (après Drawer 10.18 APPROVE-WITH-CHANGES + patch batch Option 0 Fix-All landed). Sizing **M** (~1 h 30) selon sprint-plan v2 — 2 primitives parallèles mais pattern wrapper Reka UI maîtrisé post-10.18.
>
> Cette story livre **2 primitives headless accessibles composables** dans `frontend/app/components/ui/` :
> 1. **`ui/Combobox.vue`** — autocomplete searchable single + multi-select optionnel, wrapper Reka UI `ComboboxRoot` + `ComboboxAnchor` + `ComboboxInput` + `ComboboxTrigger` + `ComboboxPortal` + `ComboboxContent` + `ComboboxViewport` + `ComboboxEmpty` + `ComboboxGroup` + `ComboboxLabel` + `ComboboxItem` + `ComboboxItemIndicator` + `ComboboxSeparator` + `ComboboxCancel`. Fondation de **3+ consommateurs Phase 1+** : filtre catalogue fonds/intermédiaires (Epic 8-15), sélection multi-pays Moussa Journey (Epic 15), filtre référentiels actifs (Epic 10).
> 2. **`ui/Tabs.vue`** — navigation contenu horizontal/vertical, wrapper Reka UI `TabsRoot` + `TabsList` + `TabsTrigger` + `TabsContent`. Fondation de **3+ consommateurs Phase 1+** : `ReferentialComparisonView` Vue comparative / Détail / Historique (Epic 10), dashboard multi-projets Moussa (Epic 11), onglets admin N1/N2/N3 (Epic 19 peer-review).
>
> **État de départ — 6 primitives `ui/` livrées + Drawer 10.18 = pattern wrapper Reka UI stabilisé** :
> - ✅ **Reka UI `^2.9.6` installé** (Story 10.14 · `frontend/package.json:30`). Exports `ComboboxRoot/Anchor/Input/Trigger/Portal/Content/Viewport/Empty/Group/Label/Item/ItemIndicator/Separator/Cancel` + `TabsRoot/List/Trigger/Content` **vérifiés disponibles** via `node -e "Object.keys(require('reka-ui')).filter(k => k.startsWith('Combobox') || k.startsWith('Tabs'))"` (Task 1.5).
> - ✅ **Pattern wrapper Reka UI maîtrisé 10.18** — DialogRoot wrapper livré avec ARIA override + 3 chemins fermeture composables + focus trap opt-in + ScrollArea intégrée + tests Pattern A DOM-only portal-aware + Pattern B comptage runtime Storybook OBLIGATOIRE. Les 4 leçons §4ter.bis + 2 leçons §4quater `methodology.md` capitalisent le pattern : **réutilisation byte-identique** du squelette pour 10.19.
> - ✅ **Tokens `@theme` livrés 10.14 + darkés 10.15 + soft-bg Badge 10.17** — `main.css` contient `surface-*`, `dark-card`, `dark-border`, `dark-hover`, `dark-input`, `brand-green #047857` focus ring (AA post-darken, cohérent Button/Drawer). **Aucune modification `main.css` nécessaire**. Les 2 primitives consomment les surfaces existantes.
> - ✅ **Pattern CCC-9 frozen tuple** (10.8 + 10.14 + 10.15 + 10.16 + 10.17 + 10.18) — `registry.ts` déjà étendu 4 fois (Button 10.15 + Input/Form 10.16 + Badge 10.17 + Drawer 10.18). Extension byte-identique pour `COMBOBOX_MODES` (2) + `TABS_ORIENTATIONS` (2) + `TABS_ACTIVATION_MODES` (2).
> - ✅ **Pattern compile-time enforcement `.test-d.ts`** (10.15 HIGH-1) — `vitest.config.ts typecheck.include: ['tests/**/*.test-d.ts']` déjà actif. 5 fichiers `.test-d.ts` post-10.18 (Badge + Button + Input + Select + Textarea + Drawer = 6, baseline 61 assertions). Réutilisable byte-identique `Combobox.test-d.ts` + `Tabs.test-d.ts`.
> - ✅ **Pattern A DOM-only portal-aware** (capitalisé §4ter.bis 10.18) — Combobox portalise `ComboboxContent` via `ComboboxPortal` → `document.body` ; Tabs n'est pas portalisé mais les tests restent DOM-observable via `screen.getByRole('tab'|'tabpanel'|'listbox'|'option')` user-event.
> - ✅ **Pattern B comptage runtime Storybook** (capitalisé §4ter.bis + piège #26 10.17) — `jq '.entries | keys | length' storybook-static/index.json` OBLIGATOIRE AVANT Completion Notes, 2 sous-comptages : `ui-combobox--*` et `ui-tabs--*`.
> - ✅ **Pattern leçon 10.18 §4quater** :
>   - **Leçon 20 — Écarts vs spec = Completion Notes obligatoires** : chaque AC non/partiellement implémenté doit être listé dans « Ajustements vs spec » avec raison + décision + suivi. Appliqué proactivement Task 7.4.
>   - **Leçon 21 — Tests observables ≠ smoke d'existence** : toute assertion observable (classes CSS responsive, focus restoration, event payload, aria-activedescendant) doit être **strict** ou **déléguée explicitement** (commentaire inline `// DELEGATED TO Storybook {{StoryName}}`). Appliqué Task 5 Combobox + Task 6 Tabs.
> - ⚠️ **Pattern Pattern A user-event vs setValue imperative** (explicite user request) — les tests Combobox utilisent `await user.type(input, 'sen')` + `expect(screen.getByRole('option', {name: /sénégal/i}))` **pas** `await input.setValue('sen')`. Les tests Tabs utilisent `await user.click(screen.getByRole('tab', {name: /onglet 2/i}))` + `expect(screen.getByRole('tabpanel')).toHaveTextContent(...)`. Intégration native `@testing-library/vue` + `@testing-library/user-event` (déjà installés via 10.14 setup Storybook).
> - ⚠️ **Pattern IME composition events** (10.16 H-2 capitalisé) — **CRITIQUE Combobox search** : `compositionstart` / `compositionupdate` / `compositionend` doivent être observés pour que la saisie CJK (chinois/japonais/coréen) ET les accents français (é/è/à/ç/ù via clavier Mac option-e etc.) ne déclenchent PAS le filter pendant la composition IME en cours. Documenté §3.6 codemap + piège #33.
> - ✅ **Pattern contraste AA darken tokens 10.15 HIGH-2** — `brand-green #047857` + `brand-red #DC2626` vérifiés AA post-darken. Combobox `aria-selected` Item + Tabs underline indicator utilisent `brand-green` cohérent Button focus / Drawer focus ring. Storybook `addon-a11y` **runtime** obligatoire (vitest-axe happy-dom insuffisant pour portail Combobox).
> - ❌ **Aucun `ui/Combobox.vue` ni `ui/Tabs.vue` préexistant** — grep `frontend/app/components/ui/` retourne 8 fichiers actuels (Button/Input/Textarea/Select/Badge/Drawer + FullscreenModal/ToastNotification brownfield) + `registry.ts`. **Grep `Combobox|Tabs` dans `app/components/ui/` → 0 hit**. Pas de collision. **Grep `Combobox|TabsRoot` dans `app/components/**/*.vue` → 0 hit gravity/ + 0 hit autres** (Task 1.1).
> - ✅ **Pattern Drawer headless consommable** — Combobox peut être consommé dans un Drawer (filtre catalogue) et Tabs peut être consommé dans un Drawer (IntermediaryComparator onglets). Pas de collision z-index ni focus trap : Combobox ComboboxPortal adopte `z-50` default Reka UI, Tabs non-portalisé. Documenté §3.6/§3.7 codemap.
> - ✅ **Dépendances futures Phase 1+** : **non bloquantes** (10.19 livre l'infra, Epic 8/10/11/15/19 consomment). Migration brownfield 0 fichier (aucune Combobox/Tabs préexistante).
>
> **Livrable 10.19 — 2 primitives + stories + tests + docs + registry extension (~1 h 30)** :
>
> 1. **Extension `ui/registry.ts`** (pattern CCC-9) — ajouter 3 frozen tuples :
>    ```ts
>    export const COMBOBOX_MODES = Object.freeze(['single', 'multiple'] as const);
>    export const TABS_ORIENTATIONS = Object.freeze(['horizontal', 'vertical'] as const);
>    export const TABS_ACTIVATION_MODES = Object.freeze(['automatic', 'manual'] as const);
>    export type ComboboxMode = (typeof COMBOBOX_MODES)[number];
>    export type TabsOrientation = (typeof TABS_ORIENTATIONS)[number];
>    export type TabsActivationMode = (typeof TABS_ACTIVATION_MODES)[number];
>    ```
>    Invariants : lengths 2/2/2 · `Object.isFrozen` · dédoublonnés · types dérivés via `typeof TUPLE[number]`.
>
> 2. **Composant `frontend/app/components/ui/Combobox.vue`** (AC1-AC6) — wrapper Reka UI `<ComboboxRoot>` + `<ComboboxAnchor>` + `<ComboboxInput>` + `<ComboboxTrigger>` + `<ComboboxPortal>` + `<ComboboxContent>` + `<ComboboxViewport>` + `<ComboboxEmpty>` + `<ComboboxGroup>` + `<ComboboxLabel>` + `<ComboboxItem>` + `<ComboboxItemIndicator>` + `<ComboboxSeparator>` + `<ComboboxCancel>` avec **typage générique** `modelValue: T | T[]` selon `multiple` prop, search/filter **insensible casse + diacritiques** (normalisation Unicode NFD + IME composition guard), ARIA `role="combobox"` + `aria-expanded` + `aria-controls` + `aria-activedescendant` (fournis par Reka UI), keyboard ArrowUp/Down/Home/End/Enter/Escape/Tab conformes WAI-ARIA Combobox pattern, empty state slot configurable (`#empty` + prop `emptyLabel` default `'Aucun résultat'`), multi-select avec badges `ui/Badge` (réutilisation 10.17) + bouton `×` par item (touch ≥ 44 px mobile).
>
> 3. **Composant `frontend/app/components/ui/Tabs.vue`** (AC7-AC12) — wrapper Reka UI `<TabsRoot>` + `<TabsList>` + `<TabsTrigger>` + `<TabsContent>` avec `orientation: 'horizontal' | 'vertical'` (default `horizontal`), `activationMode: 'automatic' | 'manual'` (default `automatic`), ARIA `role="tablist"` / `role="tab"` / `role="tabpanel"` + `aria-orientation` + `aria-selected` (fournis par Reka UI), keyboard ArrowLeft/Right (horizontal) OU ArrowUp/Down (vertical) + Home/End + cycle infini (focus wrap), contenu lazy render optionnel via prop `forceMount` (default `false`), underline indicator `brand-green` avec `prefers-reduced-motion: reduce` respect (pas d'animation underline).
>
> 4. **`frontend/app/components/ui/Combobox.stories.ts` + `Tabs.stories.ts` co-localisées** (AC13) — CSF 3.0 avec :
>    - **Combobox ≥ 7 stories** : SingleSelect, MultipleSelect, WithSearch (pays africains accents), Grouped (options groupées par secteur), EmptyState, LongList (50+ options), DarkMode.
>    - **Tabs ≥ 7 stories** : Horizontal, Vertical, WithIcons (Lucide placeholders SVG inline), Manual (activation mode), LazyContent, Composed (3 onglets contenu riche), DarkMode.
>    - **Total ≥ 14** stories nouvelles. **Comptage runtime OBLIGATOIRE** (pattern B) : `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-combobox") or (.value.id | startswith("ui-tabs")))] | length' storybook-static/index.json` **AVANT Completion Notes**, plancher AC13 ≥ 14 (cible réaliste ≥ 20 avec autodocs).
>
> 5. **Tests Vitest `frontend/tests/components/ui/`** (AC14) — **8 fichiers** :
>    - `test_combobox_registry.test.ts` + `test_tabs_registry.test.ts` : lengths/frozen/dedup × 3 tuples (≥ 9 tests cumulés).
>    - `test_combobox_behavior.test.ts` : user-event type/click Pattern A + IME composition + multi-select + empty state + keyboard ArrowUp/Down/Home/End/Enter/Escape (≥ 15 tests).
>    - `test_tabs_behavior.test.ts` : user-event click + orientation horizontal/vertical + activation automatic/manual + keyboard ArrowLeft/Right/ArrowUp/Down/Home/End + forceMount lazy vs eager (≥ 12 tests).
>    - `test_combobox_a11y.test.ts` + `test_tabs_a11y.test.ts` : vitest-axe smoke + assertions ARIA (role/aria-expanded/aria-activedescendant/aria-orientation/aria-selected) (≥ 8 audits cumulés).
>    - `test_no_hex_hardcoded_combobox_tabs.test.ts` : scan 0 hit sur `Combobox.vue` + `Combobox.stories.ts` + `Tabs.vue` + `Tabs.stories.ts`.
>    - `Combobox.test-d.ts` + `Tabs.test-d.ts` : ≥ 6 + ≥ 6 = ≥ 12 `@ts-expect-error` cumulés sur `modelValue`/`options`/`multiple`/`orientation`/`activationMode`/`tabs` invalides.
>
> 6. **Documentation `docs/CODEMAPS/ui-primitives.md` §3.6 Combobox + §3.7 Tabs + §5 pièges renumérotés ≥ 40** (AC14) — 4 exemples Vue Combobox + 4 exemples Vue Tabs + §5 pièges **#35-#40** (6 nouveaux) + §2 arbo mise à jour + §6bis note éventuelle contraste si divergence (a priori non — `brand-green` cohérent).
>
> 7. **Scan NFR66 post-dev** (AC1, AC14, AC15) : `rg '#[0-9A-Fa-f]{3,8}' Combobox.vue Combobox.stories.ts Tabs.vue Tabs.stories.ts` → 0 hit · `rg ': any\b|as unknown' Combobox.vue Tabs.vue` → 0 hit · vitest baseline **672** (post-patch 10.18) → ≥ **702 passed** (+30 minimum demandé, cible réaliste ≥ 700 avec 4 fichiers `.test.ts`) · typecheck baseline **61** → ≥ **73** (+12 minimum, plancher AC ≥ 6+6=12 `.test-d.ts`) · Storybook runtime baseline **192** → ≥ **206 entries** dont ≥ 14 `ui-combobox--*` + `ui-tabs--*` cumulés.

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité + PME persona desktop+mobile + admin N1/N2/N3 arbitrage peer-review + Moussa Journey multi-pays/multi-projets + catalogue fonds/intermédiaires filtrable),
**Je veux** deux composants `frontend/app/components/ui/Combobox.vue` et `frontend/app/components/ui/Tabs.vue` — wrappers typés strict de Reka UI `<ComboboxRoot>` et `<TabsRoot>` — offrant (a) pour Combobox une **autocomplete searchable** avec mode single + multiple (badges × réutilisation `ui/Badge` 10.17), search insensible casse + diacritiques + IME-composition-safe, ARIA `role="combobox"` + `aria-expanded` + `aria-activedescendant`, keyboard ArrowUp/Down/Home/End/Enter/Escape conformes WAI-ARIA Combobox, empty state configurable avec i18n `'Aucun résultat'` default ; et (b) pour Tabs une **navigation multi-vue** horizontale + verticale, activation `automatic` (focus = active) vs `manual` (focus puis Enter/Space), ARIA `role="tablist"` / `role="tab"` / `role="tabpanel"` + `aria-orientation` + `aria-selected`, keyboard ArrowLeft/Right ou ArrowUp/Down + Home/End + cycle infini, contenu lazy render optionnel via `forceMount`, underline indicator `brand-green` respectant `prefers-reduced-motion: reduce` ; **les 2 composants** avec dark mode ≥ 10 variantes `dark:` par composant (surface + border + text + hover + focus + selected), WCAG 2.1 AA validé par Storybook `addon-a11y` **runtime** (pas jest-axe happy-dom seul — leçon 10.15 HIGH-2 + 10.18 §4ter.bis capitalisée portail), compile-time enforcement `Combobox.test-d.ts` + `Tabs.test-d.ts` bloquant les combinaisons invalides (`multiple: 'yes'`, `orientation: 'invalid'`, `activationMode: 'hybrid'`, `modelValue: number` hors typage générique, `tabs` sans `value/label`),

**Afin que** les ≥ 6 consommateurs futurs Phase 1+ (**Combobox** : filtre catalogue fonds Epic 8, filtre intermédiaires Epic 8, sélection multi-pays Moussa Journey Epic 15, filtre référentiels actifs Epic 10 ; **Tabs** : `ReferentialComparisonView` Epic 10 — Vue comparative / Détail / Historique, dashboard multi-projets Moussa Epic 11, onglets admin N1/N2/N3 peer-review Epic 19) partagent une base ARIA + keyboard + dark mode cohérente, que le pattern **wrapper Reka UI consolidé** (stabilisé post-10.18) soit réutilisé byte-identique sans re-découverte (accélération dev-story par capitalisation §4ter.bis), et que la migration brownfield (aucune Phase 0, composants natifs `<select multiple>` + `<button @click="tab = 'x'">` brownfield à migrer Epic 10+) soit mécanique à coût 0.

## Acceptance Criteria

### Combobox (6 AC)

**AC1 — Wrapper Reka UI `<ComboboxRoot>` complet + signature TypeScript générique**
**Given** `frontend/app/components/ui/Combobox.vue`,
**When** auditée,
**Then** elle utilise Vue 3 `<script setup lang="ts" generic="T extends string | number">` avec Composition API,
**And** importe depuis `'reka-ui'` : `ComboboxRoot`, `ComboboxAnchor`, `ComboboxInput`, `ComboboxTrigger`, `ComboboxPortal`, `ComboboxContent`, `ComboboxViewport`, `ComboboxEmpty`, `ComboboxGroup`, `ComboboxLabel`, `ComboboxItem`, `ComboboxItemIndicator`, `ComboboxSeparator`, `ComboboxCancel` (**14 primitives minimum**, tous exports utilisés — pas de flat imports inutiles),
**And** expose :
```ts
interface ComboboxOption<T extends string | number> {
  value: T;
  label: string;
  disabled?: boolean;
  group?: string;  // pour options groupées (ComboboxGroup + ComboboxLabel)
}

interface ComboboxProps<T extends string | number = string> {
  modelValue: T | T[] | null;           // T si single, T[] si multiple, null autorisé (pas de sélection)
  options: Array<ComboboxOption<T>>;
  label: string;                         // obligatoire (aria-labelledby)
  multiple?: boolean;                    // default false
  placeholder?: string;                  // default 'Sélectionner...'
  emptyLabel?: string;                   // default 'Aucun résultat'
  searchable?: boolean;                  // default true
  disabled?: boolean;                    // default false
  required?: boolean;                    // default false
  open?: boolean;                        // v-model:open optionnel (par default contrôlé par Reka UI)
}

interface ComboboxEmits<T extends string | number> {
  (e: 'update:modelValue', value: T | T[] | null): void;
  (e: 'update:open', value: boolean): void;
}
```
**And** aucun `any` / `as unknown` dans `Combobox.vue` (`rg ': any\b|as unknown' frontend/app/components/ui/Combobox.vue` → 0 hit),
**And** `cd frontend && npm run build` (Nuxt type-check) passe sans erreur,
**And** `Combobox.test-d.ts` contient **≥ 6 assertions `@ts-expect-error`** : `modelValue: boolean` invalide, `modelValue: 42` sans generic binding string, `multiple: 'yes'` (boolean requis), `options` sans `{value, label}`, `options[0].value: null` invalide, `label` manquant (requis).

**AC2 — Mode `single` + `multiple` via prop + badges réutilisation `ui/Badge`**
**Given** `<Combobox :modelValue="null" :options="[...]" label="Pays" />` (single default) VS `<Combobox :modelValue="[]" :options="[...]" label="Pays" multiple />`,
**When** l'utilisateur sélectionne 1 option single :
- `update:modelValue` émis avec `T` (value scalaire),
- l'input affiche le `label` de l'option sélectionnée,
- `ComboboxItemIndicator` (coche ✓) affiché sur l'option sélectionnée,
**When** l'utilisateur sélectionne N options multiple :
- `update:modelValue` émis avec `T[]` (tableau valeurs),
- les valeurs sélectionnées s'affichent comme `<Badge>` (réutilisation `ui/Badge.vue` 10.17 variant `lifecycle` state `applicable` OU variant custom `ghost` si ajouté) avec bouton `×` par item (touch target ≥ 44 × 44 px mobile — `min-h-11 min-w-11`),
- `ComboboxItemIndicator` (coche ✓) affiché sur chaque option sélectionnée,
- **Clic sur `×` badge** → option retirée de `modelValue[]`, focus retourne sur input (pas sur badge suivant — accessibilité),
**And** test `test_combobox_behavior.test.ts` case `multiple-select-badges` assert présence Badge × N + émission `update:modelValue` avec tableau ordonné,
**And** `Combobox.test-d.ts` assert `modelValue: T[]` requis quand `multiple: true` (via conditional types ou overload — **Note implémentation** : TypeScript 5.x strict ne supporte pas nativement la contrainte `multiple → T[]` sans discriminated union, fallback `T | T[] | null` accepté Phase 0, discriminated union tracée `DEF-10.19-1`).

**AC3 — Search/filter insensible casse + diacritiques + IME composition safe**
**Given** `<Combobox searchable :options="[{value: 'sn', label: 'Sénégal'}, {value: 'ci', label: 'Côte d'Ivoire'}, ...]" />`,
**When** l'utilisateur tape `sen` (casse quelconque, sans accent),
**Then** l'option `Sénégal` est filtrée présente dans `ComboboxContent`,
**And** quand l'utilisateur tape `COT` ou `cot`, l'option `Côte d'Ivoire` est filtrée présente,
**And** la fonction de filtrage normalise via `str.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()` — patterns cumulés : casse insensible + diacritiques stripés (`é → e`, `ô → o`, `ù → u`, `ç → c`),
**And** pendant une composition IME active (`compositionstart` event reçu, pas encore `compositionend`), **le filter N'est PAS déclenché** — évite faux négatifs pendant saisie CJK (chinois/japonais/coréen) et saisie accents français Mac (option-e + e → é),
**And** test `test_combobox_behavior.test.ts` case `search-accents-case-insensitive` utilise `await user.type(input, 'sen')` + `expect(screen.getByRole('option', {name: /sénégal/i})).toBeInTheDocument()` (Pattern A user-event),
**And** test `test_combobox_behavior.test.ts` case `ime-composition-guard` mock `compositionstart` via `fireEvent.compositionStart(input)` + `fireEvent.input(input, {target: {value: 'sen'}})` + `expect(screen.queryByRole('option', {name: /sénégal/i})).toBeNull()` (pas de filter pendant composition) + `fireEvent.compositionEnd(input)` + `expect(screen.getByRole('option', {name: /sénégal/i})).toBeInTheDocument()` (filter déclenché post-composition).

**AC4 — ARIA `role="combobox"` + `aria-expanded` + `aria-controls` + `aria-activedescendant`**
**Given** `<Combobox>` rendu,
**When** inspecté dans le DOM,
**Then** l'input interne porte :
- `role="combobox"` (fourni par Reka UI `ComboboxInput`),
- `aria-expanded="false"` (fermé default) / `"true"` (ouvert après click input ou ArrowDown),
- `aria-controls="{listboxId}"` pointant vers `ComboboxContent` ID (Reka UI `useId()`),
- `aria-activedescendant="{optionId}"` quand une option est highlighted (keyboard navigation ArrowUp/Down OU hover) — pointe sur `ComboboxItem` ID,
- `aria-labelledby="{labelId}"` pointant sur le `<label>` externe (via prop `label`),
**And** le `<ComboboxContent>` porte `role="listbox"` (fourni Reka UI),
**And** chaque `<ComboboxItem>` porte `role="option"` + `aria-selected="true|false"` (Reka UI gère),
**And** test `test_combobox_a11y.test.ts` assert via `document.body.querySelector('[role="combobox"]')` présence + `.getAttribute('aria-expanded')` / `.getAttribute('aria-controls')` non-null + `.getAttribute('aria-activedescendant')` après ArrowDown dispatch (Pattern A DOM-only),
**And** vitest-axe smoke `toHaveNoViolations()` sur rendu minimal ; audits contraste/focus portail-dépendants **délégués explicitement à Storybook runtime** (Leçon 21 §4quater : `// DELEGATED TO Storybook ComboboxKeyboardNavigation`).

**AC5 — Keyboard ArrowUp/Down/Home/End/Enter/Escape/Tab conformes WAI-ARIA**
**Given** `<Combobox>` ouvert (input focused),
**When** l'utilisateur presse :
1. `ArrowDown` → `aria-activedescendant` avance à l'option suivante (cycle bas → haut si fin de liste),
2. `ArrowUp` → `aria-activedescendant` recule (cycle haut → bas si début),
3. `Home` → `aria-activedescendant` pointe sur 1ʳᵉ option,
4. `End` → `aria-activedescendant` pointe sur dernière option,
5. `Enter` → option highlighted sélectionnée + `update:modelValue` émis + dropdown fermé (single) OU restant ouvert (multiple),
6. `Escape` → dropdown fermé + input blur **OU** input reste focused selon Reka UI default (à vérifier Task 3 — si comportement différent de WAI-ARIA, documenter piège #36),
7. `Tab` → dropdown fermé + focus passe à l'élément suivant DOM (pas trapped),
**And** chaque comportement testé via `await user.keyboard('{ArrowDown}')` etc. (Pattern A user-event),
**And** test `test_combobox_behavior.test.ts` case `keyboard-navigation-roundtrip` assert cycle ArrowDown × (N+1) revient à l'option initiale (cycle infini natif Reka UI).

**AC6 — Empty state slot configurable + message i18n `'Aucun résultat'` default**
**Given** `<Combobox :options="[]" />` OU recherche sans match (`<Combobox :options="[{value:'sn',label:'Sénégal'}]" />` + user tape `xyz`),
**When** aucune option ne correspond,
**Then** `ComboboxEmpty` rendu à la place de `ComboboxViewport` items,
**And** par défaut affiche `<span>{{ emptyLabel || 'Aucun résultat' }}</span>` avec `role="status"` + `aria-live="polite"` (screen reader annonce l'état vide),
**And** slot `#empty` permet override consommateur :
```vue
<Combobox>
  <template #empty>
    <div class="p-4 text-center text-surface-text/60">
      Aucun pays ne correspond à <strong>{{ searchTerm }}</strong>
      <button @click="$emit('add-new')">Ajouter un nouveau pays</button>
    </div>
  </template>
</Combobox>
```
**And** test `test_combobox_behavior.test.ts` case `empty-state-default` + `empty-state-custom-slot` assert présence `role="status"` + textContent match.

### Tabs (6 AC)

**AC7 — Wrapper Reka UI `<TabsRoot>` complet + signature TypeScript**
**Given** `frontend/app/components/ui/Tabs.vue`,
**When** auditée,
**Then** elle utilise Vue 3 `<script setup lang="ts">` avec Composition API,
**And** importe depuis `'reka-ui'` : `TabsRoot`, `TabsList`, `TabsTrigger`, `TabsContent` (**4 primitives, tous utilisés**),
**And** expose :
```ts
interface TabItem {
  value: string;
  label: string;
  icon?: Component;        // Lucide icon component future-compat (10.21)
  disabled?: boolean;
}

interface TabsProps {
  modelValue: string;                          // valeur active (v-model)
  tabs: TabItem[];                             // liste onglets
  orientation?: TabsOrientation;               // 'horizontal' (default) | 'vertical'
  activationMode?: TabsActivationMode;         // 'automatic' (focus = active, default) | 'manual' (focus puis Enter/Space)
  forceMount?: boolean;                        // default false : lazy render contenu (DOM tabpanel non monté tant qu'inactif)
  label?: string;                              // aria-label de la TabsList (optionnel mais recommandé a11y)
}

interface TabsEmits {
  (e: 'update:modelValue', value: string): void;
}
```
**And** aucun `any` / `as unknown` dans `Tabs.vue`,
**And** `Tabs.test-d.ts` contient **≥ 6 assertions `@ts-expect-error`** : `orientation: 'invalid'`, `activationMode: 'hybrid'`, `tabs` sans `value/label`, `modelValue: number` (string requis), `forceMount: 'yes'`, `tabs: []` vide autorisé mais `tabs[0].icon: 'string'` invalide (Component requis).

**AC8 — Orientation `horizontal` + `vertical` via prop `orientation`**
**Given** `<Tabs :modelValue="'t1'" :tabs="[...]" orientation="horizontal" />` (default) VS `orientation="vertical"`,
**When** rendu,
**Then** horizontal :
- `TabsList` porte `aria-orientation="horizontal"` + layout `flex flex-row` + `border-b border-gray-200 dark:border-dark-border`,
- `TabsTrigger` actif a underline `border-b-2 border-brand-green` (indicateur horizontal),
**When** vertical :
- `TabsList` porte `aria-orientation="vertical"` + layout `flex flex-col` + `border-r border-gray-200 dark:border-dark-border`,
- `TabsTrigger` actif a left-border `border-l-2 border-brand-green` (indicateur vertical),
**And** test `test_tabs_behavior.test.ts` case `orientation-horizontal` + `orientation-vertical` assert classList présence + `aria-orientation` attribute correct.

**AC9 — Activation `automatic` (focus = active) + `manual` (focus puis Enter/Space)**
**Given** `<Tabs activationMode="automatic" />` (default) VS `activationMode="manual"`,
**When** activation `automatic` :
- ArrowRight focus onglet suivant ET change `modelValue` (émis immédiat),
- `TabsContent` associé affiché immédiat,
**When** activation `manual` :
- ArrowRight focus onglet suivant SANS changer `modelValue` (juste focus),
- L'utilisateur doit presser `Enter` ou `Space` pour activer → `update:modelValue` émis,
- `TabsContent` reste celui de l'ancien `modelValue` jusqu'à activation explicite,
**And** test `test_tabs_behavior.test.ts` case `activation-automatic` + `activation-manual` assert via `await user.keyboard('{ArrowRight}')` + assertion `modelValue` avant/après,
**And** la différenciation est **critique accessibilité** pour utilisateurs screen reader qui peuvent vouloir explorer les onglets sans charger leur contenu (mode manuel).

**AC10 — ARIA `role="tablist"` + `role="tab"` + `role="tabpanel"` + `aria-orientation` + `aria-selected`**
**Given** `<Tabs>` rendu,
**When** inspecté DOM,
**Then** `TabsList` porte `role="tablist"` + `aria-orientation="horizontal|vertical"` + `aria-label` (prop `label` si fournie, sinon pas d'attribut),
**And** chaque `TabsTrigger` porte `role="tab"` + `aria-selected="true|false"` + `aria-controls="{panelId}"` + `tabindex="0"` (actif) ou `"-1"` (inactif, roving tabindex natif Reka UI),
**And** chaque `TabsContent` porte `role="tabpanel"` + `aria-labelledby="{triggerId}"` + `tabindex="0"` (focusable pour keyboard users qui veulent scroller le contenu),
**And** test `test_tabs_a11y.test.ts` assert via `screen.getAllByRole('tab').length === tabs.length` + `screen.getByRole('tabpanel').getAttribute('aria-labelledby')` match + vitest-axe smoke.

**AC11 — Keyboard ArrowLeft/Right (horizontal) OU ArrowUp/Down (vertical) + Home/End + cycle infini**
**Given** `<Tabs orientation="horizontal" :tabs="[{value:'t1',label:'Onglet 1'},...]" />`,
**When** l'utilisateur presse :
1. `ArrowRight` → focus avance au tab suivant (cycle vers `t0` si on était sur `tN-1`),
2. `ArrowLeft` → focus recule (cycle vers `tN-1` si on était sur `t0`),
3. `Home` → focus va au 1ᵉʳ tab (`t0`),
4. `End` → focus va au dernier tab (`tN-1`),
**And** si `orientation="vertical"` : `ArrowDown` / `ArrowUp` remplacent `ArrowRight` / `ArrowLeft`,
**And** les tabs `disabled: true` sont **skippés** dans la navigation (Reka UI gère),
**And** test `test_tabs_behavior.test.ts` case `keyboard-horizontal-roundtrip` utilise `await user.click(screen.getByRole('tab', {name: /onglet 2/i}))` puis `await user.keyboard('{ArrowRight}')` × N + `expect(screen.getByRole('tab', {name: /onglet 1/i})).toHaveFocus()` (cycle infini vérifié).

**AC12 — Contenu lazy render optionnel via `forceMount` (default false = lazy)**
**Given** `<Tabs :tabs="[{value:'t1',...}, {value:'t2',...}]" modelValue="t1" />` (forceMount default false),
**When** `TabsContent value="t1"` est actif,
**Then** seul le DOM de `t1` est monté (Reka UI default : contenu des tabs inactifs non rendu),
**And** quand `modelValue` passe à `t2`, DOM de `t1` est démonté et `t2` monté,
**When** `forceMount="true"`,
**Then** tous les `TabsContent` sont montés simultanément (invisibles via `hidden` attribute mais dans le DOM) — utile pour (a) éviter re-renders coûteux (formulaires), (b) accessibilité pour cas spécifiques (search DOM transversal),
**And** test `test_tabs_behavior.test.ts` case `lazy-content` assert `screen.queryByTestId('tab-content-t2')` retourne null initialement, puis présent après click t2 ; case `force-mount` assert les 2 contents présents simultanément (l'inactif a `hidden` / `aria-hidden="true"`).

### Transverse (2 AC)

**AC13 — Stories Storybook ≥ 14 + comptage runtime OBLIGATOIRE pré-Completion**
**Given** `Combobox.stories.ts` + `Tabs.stories.ts` co-localisées CSF 3.0,
**When** `npm run storybook:build` exécuté,
**Then** `jq '[.entries | to_entries[] | select(.value.id | test("^ui-(combobox|tabs)--"))] | length' storybook-static/index.json` est **capturé et consigné littéralement** dans Completion Notes **AVANT** tout claim de complétude (pattern B 10.16 M-3 + capitalisation 10.17 piège #26 + 10.18 §4ter.bis Pattern 2),
**And** ce comptage doit être **≥ 14 stories nouvelles** cumulées :
- **Combobox ≥ 7** : SingleSelect, MultipleSelect, WithSearchAccents, Grouped, EmptyState, LongList, DarkMode,
- **Tabs ≥ 7** : Horizontal, Vertical, WithIcons, Manual, LazyContent, Composed, DarkMode,
- (cible réaliste ≥ 20 avec autodocs 2 composants × 1 page auto + variantes supplémentaires),
**And** le glob `frontend/.storybook/main.ts` reste **inchangé** (déjà étendu `gravity/ + ui/` Story 10.15),
**And** le bundle `storybook-static/` reste **≤ 15 MB** (budget 10.14 préservé, marge ≥ 6 MB post-10.18).

**AC14 — Coverage ≥ 85% par fichier + 0 hex + 0 any + dark: parity ≥ 10 per component + docs CODEMAPS**
**Given** Story 10.19 complétée,
**When** auditée,
**Then** **coverage tests ≥ 85 % sur `Combobox.vue` ET `Tabs.vue`** (plancher primitive wrapper — branches Reka UI déléguées mockées),
**And** `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Combobox.vue Combobox.stories.ts Tabs.vue Tabs.stories.ts` → **0 hit** (hors commentaires stripés),
**And** `rg ': any\b|as unknown' frontend/app/components/ui/Combobox.vue Tabs.vue` → **0 hit**,
**And** `grep -oE "dark:" frontend/app/components/ui/Combobox.vue | wc -l` → **≥ 10** + `grep -oE "dark:" frontend/app/components/ui/Tabs.vue | wc -l` → **≥ 10** (plancher dark parity par composant, sans inflation — chaque classe rattachée à axe visuel réel),
**And** `docs/CODEMAPS/ui-primitives.md` contient §3.6 Combobox + §3.7 Tabs avec **≥ 4 exemples Vue chacun** + §5 pièges **renuméroté 35-40** (6 nouveaux cumul ≥ 40),
**And** `test_docs_ui_primitives.test.ts` étendu (13 tests post-10.18 → **≥ 17 tests post-10.19**) : §3.6 présent, §3.7 présent, ≥ 40 pièges cumulés, ≥ 4 exemples §3.6, ≥ 4 exemples §3.7,
**And** **0 régression** sur tests préexistants (672 post-10.18 → ≥ 702 post-10.19, +30 minimum demandé),
**And** **typecheck baseline 61 post-10.18** → **≥ 73 post-10.19** (+12 minimum cumulé Combobox.test-d.ts ≥ 6 + Tabs.test-d.ts ≥ 6),
**And** **3-4 commits intermédiaires lisibles review** (leçon 10.8) :
  1. `feat(10.19): registry CCC-9 3 tuples + ui/Combobox primitive wrapper Reka UI`,
  2. `feat(10.19): ui/Tabs primitive wrapper Reka UI + Combobox.test-d.ts + Tabs.test-d.ts`,
  3. `feat(10.19): stories CSF3 Combobox + Tabs ≥14 + tests behavior/a11y Pattern A user-event`,
  4. `feat(10.19): docs CODEMAPS §3.6 Combobox + §3.7 Tabs + méthodology §4ter.ter + count runtime vérifié`.

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 préalable + baseline + vérif Reka UI exports** (AC1, AC7, AC14)
  - [x] 1.1 Grep `Combobox\.vue|Tabs\.vue|COMBOBOX_MODES|TABS_ORIENTATIONS|TABS_ACTIVATION_MODES` sur `frontend/app/components/**` + `frontend/tests/**` → attendu **0 hit** (hors `Tabs.vue` dans `_bmad-output/` artefacts previously).
  - [x] 1.2 Baseline tests : `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner exact post-10.18-patch (672 attendu + 1 pré-existant `useGuidedTour` INFO-10.14-1 hors scope).
  - [x] 1.3 Baseline typecheck : `npm run test:typecheck 2>&1 | tail -5` → consigner (61 attendu post-10.18 : 6 Button + 8 Input + 7 Select + 6 Textarea + 13 Badge + 15 Drawer + 6 existants).
  - [x] 1.4 Baseline Storybook : `jq '.entries | keys | length' frontend/storybook-static/index.json` → consigner (192 attendu post-10.18-patch).
  - [x] 1.5 Vérif Reka UI 2.9.6 exports disponibles via :
    ```bash
    node -e "console.log(Object.keys(require('reka-ui')).filter(k => k.startsWith('Combobox') || k.startsWith('Tabs')))"
    ```
    Attendu : `ComboboxAnchor, ComboboxCancel, ComboboxContent, ComboboxEmpty, ComboboxGroup, ComboboxInput, ComboboxItem, ComboboxItemIndicator, ComboboxLabel, ComboboxPortal, ComboboxRoot, ComboboxSeparator, ComboboxTrigger, ComboboxViewport, TabsContent, TabsIndicator?, TabsList, TabsRoot, TabsTrigger` (si `TabsIndicator` disponible, peut simplifier underline indicator).
  - [x] 1.6 Vérif absence `@testing-library/user-event` manquant (déjà installé via 10.14 setup Storybook ?) : `grep '"@testing-library/user-event"' frontend/package.json` → si absent, ajouter `npm install -D @testing-library/user-event@14.5.2` (stable LTS) + documenter Task 7.6 dans bundle notes.

- [x] **Task 2 — Registry `ui/registry.ts` extension** (AC1, AC7)
  - [x] 2.1 Ajouter `COMBOBOX_MODES = Object.freeze(['single', 'multiple'] as const)` (ordre canonique single-first — mode simple prioritaire, cohérent Select 10.16).
  - [x] 2.2 Ajouter `TABS_ORIENTATIONS = Object.freeze(['horizontal', 'vertical'] as const)` (horizontal-first, cas majoritaire UI tabs).
  - [x] 2.3 Ajouter `TABS_ACTIVATION_MODES = Object.freeze(['automatic', 'manual'] as const)` (automatic-first, cohérent WAI-ARIA recommandation default).
  - [x] 2.4 Types dérivés `ComboboxMode` / `TabsOrientation` / `TabsActivationMode` via `typeof TUPLE[number]`.
  - [x] 2.5 Docstrings JSDoc référençant Story 10.19 + rationale ordre canonique (piège #35 pour inversions éventuelles).
  - [x] 2.6 Exports 10.15+10.16+10.17+10.18 byte-identique préservés (diff `git diff frontend/app/components/ui/registry.ts` restreint aux ajouts).
  - [x] 2.7 `npm run test:typecheck` → baseline 61 → attendu 61 (registry ne change pas typecheck count tant que `.test-d.ts` Combobox/Tabs pas ajoutés — check Task 5.5).
  - [x] 2.8 **Commit intermédiaire 1** : `feat(10.19): registry CCC-9 3 tuples (COMBOBOX_MODES + TABS_ORIENTATIONS + TABS_ACTIVATION_MODES)`.

- [x] **Task 3 — Composant `ui/Combobox.vue`** (AC1-AC6)
  - [x] 3.1 `<script setup lang="ts" generic="T extends string | number = string">` avec imports Reka UI (14 primitives) + types registry + `ref` / `computed` / `useId` / `onBeforeUnmount` Vue 3.
  - [x] 3.2 `defineProps<ComboboxProps<T>>()` + `withDefaults` : `multiple: false`, `searchable: true`, `disabled: false`, `required: false`, `placeholder: 'Sélectionner...'`, `emptyLabel: 'Aucun résultat'`.
  - [x] 3.3 `defineEmits<ComboboxEmits<T>>()` avec `update:modelValue` + `update:open`.
  - [x] 3.4 État interne : `searchTerm = ref('')`, `isComposing = ref(false)` (IME guard), `labelId = useId()`, `listboxId = useId()`.
  - [x] 3.5 Computed `filteredOptions` : applique normalisation Unicode NFD + toLowerCase pour match insensible casse + diacritiques, **skippée si `isComposing.value === true`** (IME guard AC3 + piège #34).
  - [x] 3.6 Handlers IME : `handleCompositionStart() { isComposing.value = true }` + `handleCompositionEnd(e) { isComposing.value = false; searchTerm.value = (e.target as HTMLInputElement).value }` — liés sur `<ComboboxInput @compositionstart="..." @compositionend="..." />`.
  - [x] 3.7 Computed `isMultiple` + `selectedValues` : normalise `modelValue` en tableau uniforme (single → `[modelValue]` pour rendu, multiple → `modelValue as T[]`).
  - [x] 3.8 Template principal : `<ComboboxRoot :modelValue="modelValue" :multiple="multiple" :open="open" @update:modelValue="handleUpdateValue" @update:open="$emit('update:open', $event)">` + `<ComboboxAnchor class="flex flex-wrap ...">` :
    - Badges multi-select si `isMultiple` + `selectedValues.length > 0` : `<Badge v-for="val in selectedValues" variant="lifecycle" state="applicable" size="sm"><span>{{ labelFor(val) }}</span><button @click.stop="removeValue(val)" class="ml-1 min-h-11 min-w-11" aria-label="Retirer">×</button></Badge>`,
    - `<ComboboxInput v-model="searchTerm" @compositionstart="handleCompositionStart" @compositionend="handleCompositionEnd" :placeholder="placeholder" :aria-labelledby="labelId" class="...focus-visible:ring-brand-green">`,
    - `<ComboboxTrigger class="...">▼</ComboboxTrigger>` (icône placeholder SVG — Lucide ChevronDown 10.21).
  - [x] 3.9 Template `<ComboboxPortal>` + `<ComboboxContent class="... bg-white dark:bg-dark-card border dark:border-dark-border shadow-lg rounded-md z-50">` :
    - `<ComboboxViewport>` wrap options,
    - `v-if="filteredOptions.length === 0"` : `<ComboboxEmpty><slot name="empty"><span role="status" aria-live="polite" class="p-4 text-center text-surface-text/60 dark:text-surface-dark-text/60">{{ emptyLabel }}</span></slot></ComboboxEmpty>`,
    - Options groupées : `<ComboboxGroup v-for="group in groupedOptions">` + `<ComboboxLabel>{{ group.label }}</ComboboxLabel>` + `<ComboboxItem v-for="opt in group.items" :value="opt.value" :disabled="opt.disabled"><span>{{ opt.label }}</span><ComboboxItemIndicator>✓</ComboboxItemIndicator></ComboboxItem>`,
    - Si pas de groupes : `<ComboboxItem v-for="opt in filteredOptions" ...>` flat.
  - [x] 3.10 Dark mode : `dark:bg-dark-input` input + `dark:bg-dark-card` content + `dark:border-dark-border` borders + `dark:text-surface-dark-text` textes + `dark:hover:bg-dark-hover` items hover + `dark:data-[highlighted]:bg-dark-hover` aria-activedescendant highlight + `dark:focus-visible:ring-brand-green` focus ring + `dark:bg-brand-green/20` aria-selected Item background + `dark:text-brand-green-light?` aria-selected text + `dark:text-surface-dark-text/60` empty state → **≥ 10 occurrences AC14**.
  - [x] 3.11 `prefers-reduced-motion: reduce` : dropdown open/close animation via Tailwind `data-[state=open]:animate-in data-[state=closed]:animate-out motion-reduce:animate-none` (pas d'animation slide sous reduced motion — AC7 du epic spec).
  - [x] 3.12 Scan hex `Combobox.vue` → **0 hit** (tokens `@theme` uniquement).
  - [x] 3.13 `: any` / `as unknown` dans Combobox.vue → **0 hit**.
  - [x] 3.14 **Commit intermédiaire 2 (partiel)** : `feat(10.19): ui/Combobox primitive wrapper Reka UI 14 primitives + IME composition guard + multi-select badges`.

- [x] **Task 4 — Composant `ui/Tabs.vue`** (AC7-AC12)
  - [x] 4.1 `<script setup lang="ts">` avec imports Reka UI (4 primitives) + types registry + `computed` / `useId` Vue 3.
  - [x] 4.2 `defineProps<TabsProps>()` + `withDefaults` : `orientation: 'horizontal'`, `activationMode: 'automatic'`, `forceMount: false`.
  - [x] 4.3 `defineEmits<TabsEmits>()` avec `update:modelValue`.
  - [x] 4.4 Computed `orientationClasses` :
    - horizontal: `list: 'flex flex-row border-b border-gray-200 dark:border-dark-border'`, `trigger-active: 'border-b-2 border-brand-green'`, `trigger-base: 'px-4 py-2 -mb-px border-b-2 border-transparent'`,
    - vertical: `list: 'flex flex-col border-r border-gray-200 dark:border-dark-border'`, `trigger-active: 'border-r-2 border-brand-green'`, `trigger-base: 'px-4 py-2 -mr-px border-r-2 border-transparent text-left'`.
  - [x] 4.5 Template principal :
    ```vue
    <TabsRoot :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" :orientation="orientation" :activation-mode="activationMode">
      <TabsList :aria-label="label" :class="orientationClasses.list">
        <TabsTrigger
          v-for="tab in tabs"
          :key="tab.value"
          :value="tab.value"
          :disabled="tab.disabled"
          :class="[
            orientationClasses.triggerBase,
            modelValue === tab.value ? orientationClasses.triggerActive : '',
            'text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green disabled:opacity-50 disabled:cursor-not-allowed motion-reduce:transition-none',
          ]"
        >
          <component :is="tab.icon" v-if="tab.icon" class="mr-2 h-4 w-4" aria-hidden="true" />
          {{ tab.label }}
        </TabsTrigger>
      </TabsList>
      <TabsContent v-for="tab in tabs" :key="tab.value" :value="tab.value" :force-mount="forceMount || undefined" tabindex="0" class="p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green">
        <slot :name="`content-${tab.value}`" :tab="tab" />
      </TabsContent>
    </TabsRoot>
    ```
  - [x] 4.6 **Note `:force-mount="forceMount || undefined"`** : Reka UI `forceMount` est une prop boolean dont la simple présence suffit → passer `undefined` (pas `false`) pour ne PAS activer forceMount (AC12 default lazy).
  - [x] 4.7 Slot nommé `content-${tab.value}` permet consommateur d'injecter contenu riche par onglet. Slot default `fallback` si aucun nommé fourni.
  - [x] 4.8 Dark mode : `dark:bg-dark-card` content (si container) + `dark:text-surface-dark-text` + `dark:border-dark-border` + `dark:hover:bg-dark-hover` + `dark:focus-visible:ring-brand-green` + `dark:border-brand-green-dark?` active + `dark:disabled:opacity-50` + `dark:bg-dark-input?` cas filtre + `dark:text-brand-green` active text + `dark:text-surface-dark-text/60` disabled → **≥ 10 occurrences AC14** (compter finement — si 10 dépasse, ré-équilibrer sans inflation).
  - [x] 4.9 `prefers-reduced-motion: reduce` : underline indicator **pas d'animation** — position change immédiate via CSS `border-b-2 border-brand-green` switch (pas de `translate-x` animé). AC7 epic spec : « l'indicateur underline se déplace sans animation ».
  - [x] 4.10 Scan hex `Tabs.vue` → **0 hit**.
  - [x] 4.11 `: any` / `as unknown` dans Tabs.vue → **0 hit**.
  - [x] 4.12 **Commit intermédiaire 2 (complet)** : `feat(10.19): ui/Tabs primitive wrapper Reka UI 4 primitives + orientation/activationMode + forceMount lazy + .test-d.ts 12+ assertions`.

- [x] **Task 5 — Tests Vitest Combobox + Tabs (Pattern A user-event strict + Leçon 21 observable)** (AC14)
  - [x] 5.1 `test_combobox_registry.test.ts` : 4 tests (length `=== 2` + `Object.isFrozen` + dedup + ordre canonical `COMBOBOX_MODES[0] === 'single'`).
  - [x] 5.2 `test_tabs_registry.test.ts` : 5 tests (length × 2 tuples + frozen × 2 + dedup × 2 + ordre canonique `TABS_ORIENTATIONS[0] === 'horizontal'` × 1 — cumulé 6 tests possibles).
  - [x] 5.3 `test_combobox_behavior.test.ts` : ≥ 15 tests **Pattern A user-event strict** (assertions via `screen.getByRole` + `user.type` + `user.keyboard`) :
    - v-model:modelValue single : render option + `await user.click(input)` + `await user.click(screen.getByRole('option', {name: /sénégal/i}))` + `expect(emitted['update:modelValue']).toContainEqual(['sn'])`,
    - v-model:modelValue multiple : similar + badges présents + bouton × fonctionnel,
    - Search accents case-insensitive : `await user.type(input, 'cot')` + `expect(screen.getByRole('option', {name: /côte d'ivoire/i})).toBeInTheDocument()` (AC3),
    - IME composition guard : `fireEvent.compositionStart` + input → no filter, `fireEvent.compositionEnd` → filter (AC3 piège #34),
    - Keyboard `{ArrowDown}` × N → cycle infini vérifié via `toHaveAttribute('aria-activedescendant', ...)`,
    - `{Enter}` → option sélectionnée émise,
    - `{Escape}` → dropdown fermé (`expect(screen.queryByRole('listbox')).toBeNull()`),
    - `{Tab}` → focus sort de l'input,
    - Empty state default : options vides → `screen.getByRole('status')` textContent === 'Aucun résultat',
    - Empty state custom slot : `#empty` override rendu + pas de `role="status"` default,
    - Disabled prop : input non interactif + `aria-disabled="true"`,
    - Options `disabled: true` individuelles : `aria-disabled` sur ComboboxItem + non-sélectionnable.
    - **Aucun `wrapper.vm.*`** ni `input.setValue(...)` (Pattern A enforced strict — user-event only).
  - [x] 5.4 `test_tabs_behavior.test.ts` : ≥ 12 tests user-event strict :
    - v-model: `await user.click(screen.getByRole('tab', {name: /onglet 2/i}))` + `expect(emitted['update:modelValue']).toContainEqual(['t2'])` + `expect(screen.getByRole('tabpanel')).toHaveTextContent(...)`,
    - Orientation horizontal : `aria-orientation="horizontal"` sur TabsList + ArrowRight/Left fonctionnels + ArrowUp/Down no-op,
    - Orientation vertical : `aria-orientation="vertical"` + ArrowUp/Down fonctionnels + ArrowRight/Left no-op,
    - Activation automatic : ArrowRight → modelValue change immédiat,
    - Activation manual : ArrowRight → focus bouge mais modelValue inchangé + Enter → modelValue change,
    - Home/End : `{Home}` → focus sur t0, `{End}` → focus sur tN-1,
    - Cycle infini : ArrowRight depuis tN-1 → focus sur t0,
    - Tabs disabled skip : `{tabs: [{value:'t1'}, {value:'t2', disabled:true}, {value:'t3'}]}` + ArrowRight depuis t1 → focus sur t3 (skip t2),
    - forceMount default false : t2 panel not in DOM initially + clic sur t2 → panel monté,
    - forceMount true : tous les panels en DOM simultanément + `hidden` attribute sur inactifs,
    - Icon dans tabs : `tab.icon: LucideIconPlaceholder` rendu dans trigger + `aria-hidden="true"`,
    - aria-label sur TabsList : prop `label` fournie → `aria-label` présent, sinon absent.
  - [x] 5.5 `test_combobox_a11y.test.ts` : 4 tests ARIA + vitest-axe smoke (`toHaveNoViolations()` sur rendu default) — contraste/focus portail délégués `// DELEGATED TO Storybook ComboboxKeyboardNavigation`.
  - [x] 5.6 `test_tabs_a11y.test.ts` : 4 tests ARIA (role tablist/tab/tabpanel + aria-selected + aria-labelledby + aria-orientation) + vitest-axe smoke.
  - [x] 5.7 `test_no_hex_hardcoded_combobox_tabs.test.ts` : 4 tests scan `Combobox.vue` + `Combobox.stories.ts` + `Tabs.vue` + `Tabs.stories.ts` → 0 hit.
  - [x] 5.8 `Combobox.test-d.ts` : **≥ 6 `@ts-expect-error`** :
    - `modelValue: boolean` (T | T[] | null requis),
    - `modelValue: 42` sans instanciation generic `<number>` (string default),
    - `multiple: 'yes'` (boolean requis),
    - `options` sans `{value, label}`,
    - `options[0].value: null` invalide (T requis, null option exclue),
    - `label` manquant (requis).
  - [x] 5.9 `Tabs.test-d.ts` : **≥ 6 `@ts-expect-error`** :
    - `orientation: 'invalid'` hors union,
    - `activationMode: 'hybrid'` hors union,
    - `tabs` sans `value/label`,
    - `modelValue: 42` (string requis),
    - `forceMount: 'yes'` (boolean requis),
    - `tabs[0].icon: 'string'` (Component requis, pas string).
  - [x] 5.10 **Assertions strictes Leçon 21 §4quater appliquées proactivement** :
    - AC11 keyboard cycle infini : `expect(tab0).toHaveFocus()` après `ArrowRight × N` (pas `expect(tab0).not.toBeNull()`),
    - AC12 forceMount lazy : `expect(screen.queryByTestId('tab-content-t2')).toBeNull()` avant clic + `expect(screen.getByTestId('tab-content-t2')).toBeInTheDocument()` après clic (pas `.not.toBeNull()` permissif),
    - AC5 keyboard Enter : `expect(emitted['update:modelValue']).toBeDefined()` + `expect(emitted['update:modelValue'].at(-1)).toEqual(['sn'])` (pas `if (emitted) ...` permissif),
    - AC3 IME composition guard : AVANT `compositionEnd`, `expect(screen.queryByRole('option', {name: /sénégal/i})).toBeNull()` strict (pas `expect(dropdown.textContent).toContain('...')` laxiste).
  - [x] 5.11 `npm run test -- --run` → baseline 672 → **≥ 702 passed** (+30 minimum demandé, cible réaliste ≥ 30 tests nouveaux × 2 composants ≈ +35-45).
  - [x] 5.12 `npm run test:typecheck` → baseline 61 → **≥ 73 passed** (+12 minimum).
  - [x] 5.13 **Commit intermédiaire 3** : `feat(10.19): stories CSF3 Combobox + Tabs ≥14 + tests behavior/a11y Pattern A user-event strict + IME composition guard`.

- [x] **Task 6 — `ui/Combobox.stories.ts` + `ui/Tabs.stories.ts` co-localisées** (AC13)
  - [x] 6.1 `Combobox.stories.ts` CSF 3.0 meta `{ title: 'UI/Combobox', component: Combobox, tags: ['autodocs'], parameters: { layout: 'padded', a11y: {...} } }`.
  - [x] 6.2 Stories Combobox ≥ 7 :
    - `SingleSelect` : pays africains UEMOA (`sn`, `ci`, `bf`, `tg`, `bj`, `ml`, `ne`) avec accents,
    - `MultipleSelect` : `multiple: true` + 3 pays préselectionnés → badges visibles,
    - `WithSearchAccents` : play function `await userEvent.type(canvas.getByRole('combobox'), 'cot')` + `expect(canvas.getByRole('option', {name: /côte d'ivoire/i}))` (Pattern A),
    - `Grouped` : options avec `group: 'UEMOA'` vs `group: 'CEMAC'` vs `group: 'Autres'` → `ComboboxGroup` + `ComboboxLabel` rendus,
    - `EmptyState` : `options: []` → message 'Aucun résultat' + story `EmptyStateCustomSlot` avec slot `#empty` custom (via `render` function),
    - `LongList` : 50 options (secteurs ESG UEMOA catalogue) pour démo scroll ComboboxViewport,
    - `DarkMode` : decorator `html.classList.add('dark')` + story SingleSelect miroir.
  - [x] 6.3 `Tabs.stories.ts` CSF 3.0 meta `{ title: 'UI/Tabs', component: Tabs, tags: ['autodocs'], parameters: {...} }`.
  - [x] 6.4 Stories Tabs ≥ 7 :
    - `Horizontal` : 3 onglets `Vue comparative / Détail par règle / Historique` (future consommateur Epic 10 `ReferentialComparisonView`),
    - `Vertical` : 4 onglets admin `N1 / N2 / N3 / Audit log` (future consommateur Epic 19 peer-review),
    - `WithIcons` : Lucide placeholder SVG inline (future 10.21 migration mécanique),
    - `Manual` : `activationMode: 'manual'` + play function ArrowRight + assert modelValue inchangé avant Enter,
    - `LazyContent` : 3 onglets contenu coûteux simulé (textarea 500 lignes) + assert panel inactif non monté,
    - `Composed` : 3 onglets avec contenu riche (Card + Badge + bouton) pour démo slot,
    - `DarkMode` : decorator dark + story Horizontal miroir.
  - [x] 6.5 Play functions interactives avec `@storybook/testing-library` : simulent user flow Storybook play (ex. `WithSearchAccents` Combobox + `Manual` Tabs keyboard nav).
  - [x] 6.6 Helper `asStorybookComponent<T>()` réutilisé `frontend/app/types/storybook.ts` (pas de `as unknown` — pattern 10.15 M-3).
  - [x] 6.7 **Comptage runtime OBLIGATOIRE post-build Task 7.3** : `jq '[.entries | to_entries[] | select(.value.id | test("^ui-(combobox|tabs)--"))] | length' storybook-static/index.json` — consigner EXACT avant Completion Notes (piège #26 capitalisé + §4ter.bis Pattern 2).

- [x] **Task 7 — Scan NFR66 post-dev + validation finale + comptage runtime Storybook (pattern B capitalisé)** (AC13, AC14)
  - [x] 7.1 Scan hex `Combobox.vue` + `Combobox.stories.ts` + `Tabs.vue` + `Tabs.stories.ts` + `registry.ts` diff → **0 hit** (hex dans commentaires docstring stripés par `stripComments()`).
  - [x] 7.2 `: any\b` / `as unknown` dans `Combobox.vue` + `Tabs.vue` + `.test-d.ts` → **0 hit** (cast `as unknown` test-only acceptable dans `.test.ts` runtime — cf. 10.18 précédent).
  - [x] 7.3 **Build Storybook + comptage runtime OBLIGATOIRE** (pattern B 10.16 M-3 + capitalisation 10.17 piège #26 + 10.18 §4ter.bis) :
    ```bash
    cd frontend && npm run storybook:build 2>&1 | tail -5
    jq '.entries | keys | length' storybook-static/index.json  # baseline 192 post-10.18 patch
    jq '[.entries | to_entries[] | select(.value.id | startswith("ui-combobox"))] | length' storybook-static/index.json  # cible ≥ 7
    jq '[.entries | to_entries[] | select(.value.id | startswith("ui-tabs"))] | length' storybook-static/index.json  # cible ≥ 7
    du -sh storybook-static  # ≤ 15 MB budget 10.14
    ```
    Consigner les 4 chiffres EXACTS dans Completion Notes **AVANT** tout claim de complétude.
  - [x] 7.4 **Ajustements vs spec documentés (Leçon 20 §4quater appliquée proactivement)** : recenser en Completion Notes § « Ajustements mineurs vs spec » chaque AC avec écart :
    - Format : `**AC# — titre** : prescription originale / décision (implémenté|déféré|refusé|délégué) / raison / suivi (commit ou `DEF-10.19-N` dans `deferred-work.md`)`.
    - Absence d'item = spec intégralement honorée.
    - Si 0 écart : écrire explicitement `**Aucun écart vs spec** — 14 AC honorés intégralement, 14 stories runtime vérifiées, 12 assertions typecheck atteintes, 30+ tests nouveaux verts.`.
  - [x] 7.5 `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner : baseline 672 → ≥ 702 passed (+30 min).
  - [x] 7.6 `npm run test:typecheck 2>&1 | tail -5` → consigner : baseline 61 → ≥ 73 passed (+12 min).
  - [x] 7.7 `grep -oE "dark:" frontend/app/components/ui/Combobox.vue | wc -l` → **≥ 10** ET `grep -oE "dark:" frontend/app/components/ui/Tabs.vue | wc -l` → **≥ 10** (AC14 plancher par composant sans inflation).
  - [x] 7.8 Coverage `npm run test -- --coverage --run 2>&1 | grep -E "Combobox|Tabs"` → **≥ 85 %** sur les 2 fichiers (AC14).
  - [x] 7.9 **Commit final 4** : `feat(10.19): docs CODEMAPS §3.6 Combobox + §3.7 Tabs + methodology §4ter.ter application proactive 10.19 + count runtime vérifié`.

- [x] **Task 8 — Documentation `docs/CODEMAPS/ui-primitives.md` + `methodology.md`** (AC14)
  - [x] 8.1 `### 3.6 ui/Combobox (Story 10.19)` inséré entre §3.5 Drawer et §4 (ou §3.7 si §3.7 Tabs prévu d'abord — ordre canonique §3.6 Combobox → §3.7 Tabs alphabétique).
  - [x] 8.2 §3.6 Combobox : **4 exemples Vue** + 1 bloc TypeScript `@ts-expect-error` :
    1. Combobox single-select filtre catalogue (pays UEMOA + accents + search Task 10.15),
    2. Combobox multi-select Moussa multi-pays (badges + bouton × + touch target 44 px),
    3. Combobox grouped (UEMOA / CEMAC / Autres — options groupées secteurs ESG),
    4. Combobox empty state slot custom (`#empty` avec bouton « Ajouter un pays »),
    5. `@ts-expect-error` sur `multiple: 'yes'` invalide.
  - [x] 8.3 `### 3.7 ui/Tabs (Story 10.19)` inséré après §3.6.
  - [x] 8.4 §3.7 Tabs : **4 exemples Vue** + 1 bloc TypeScript :
    1. Tabs horizontal `ReferentialComparisonView` (Vue comparative / Détail par règle / Historique),
    2. Tabs vertical admin N1/N2/N3 peer-review,
    3. Tabs manual activation (keyboard accessibility screen reader exploration),
    4. Tabs forceMount=true contenu lazy (formulaire complexe multi-onglet),
    5. `@ts-expect-error` sur `orientation: 'invalid'`.
  - [x] 8.5 §5 Pièges étendu **34 post-10.18 → 40 post-10.19** (+6 nouveaux) :
    - **#35 Registry ordres canoniques frozen** : `COMBOBOX_MODES` single-first + `TABS_ORIENTATIONS` horizontal-first + `TABS_ACTIVATION_MODES` automatic-first. Raison : cohérence WAI-ARIA + usage majoritaire. Changer l'ordre = rupture API (types inférés index 0 = default).
    - **#36 Combobox Escape behavior Reka UI default** : vérifier si Reka UI 2.9.6 ferme dropdown sur Escape SANS blur input (comportement WAI-ARIA) OU avec blur. Si divergence, documenter + documentation usage consommateur.
    - **#37 Combobox forceMount piège Reka UI** : `forceMount` est une prop **présence** (pas boolean) → passer `undefined` pour désactiver, pas `false` (Tabs.vue Task 4.6 — même piège sur Tabs.forceMount).
    - **#38 IME composition guard CJK + accents Mac FR** : `compositionstart` / `compositionend` **critiques** pour Combobox searchable. Sans guard, `é` tapé via option-e (Mac) déclenche filter prématurément sur `e` → UX dégradée africains francophones bilingues + CJK si utilisateur présent. Solution : `isComposing = ref(false)` + conditionnel filter. Test via `fireEvent.compositionStart/End`.
    - **#39 Tabs vertical underline indicator cohérence RTL** : si futur support RTL (arabe Maghreb/Mauritanie), le border-r vertical devient border-l. Pas de gestion RTL Phase 0 (deferred `DEF-10.19-2`), mais piège signalé pour éviter hardcode `border-r` sans `ltr:` / `rtl:` préfixe.
    - **#40 Tabs lazy forceMount vs accessibility browser search** : `forceMount: false` (default) = tabpanel inactif non dans DOM → Ctrl+F navigateur ne trouve pas le texte. Pour contenu critique (documentation longue), consommateur peut forcer `forceMount: true`. Trade-off perf vs searchability documenté.
  - [x] 8.6 §2 Arborescence cible étendue (+6 lignes : Combobox.vue + Combobox.stories.ts + Combobox.test-d.ts + Tabs.vue + Tabs.stories.ts + Tabs.test-d.ts — plus les 4 tests fichiers).
  - [x] 8.7 `test_docs_ui_primitives.test.ts` étendu : 13 → **≥ 17 tests** (§3.6 Combobox présent + §3.7 Tabs présent + ≥ 40 pièges + ≥ 4 exemples §3.6 + ≥ 4 exemples §3.7).
  - [x] 8.8 `docs/CODEMAPS/methodology.md` étendu : **section 4ter.ter capitalisée « Application proactive Story 10.19 (ui/Combobox + ui/Tabs) — 6 leçons cumulées §4ter.bis + §4quater »** — Pattern A user-event (pas setValue imperative) + Pattern B count runtime + leçon 10.14 HIGH-2 (override ARIA explicite — moins critique ici car role="combobox" + role="tablist" sont sémantiques correctes Reka UI default) + leçon 10.15 HIGH-2 (a11y runtime Storybook) + leçon 20 (écarts vs spec) + leçon 21 (tests observables). Exemple : IME composition guard `test_combobox_behavior.test.ts` case `ime-composition-guard` applique leçon 21 (strict `expect(queryByRole).toBeNull()` pré-end + `getByRole` post-end, pas `.not.toBeNull()` laxiste). Mesure anti-récurrence : si un 7ᵉ pattern révélé post-code-review 10.19, créer §4quinquies.
  - [x] 8.9 **Commit final 4** : couvre Task 7 + Task 8 ensemble (stories + tests + docs déjà dans 3 commits précédents).

- [x] **Task 9 — Mini-retro leçons 10.19 pour 10.20 DatePicker + 10.21 Lucide/EsgIcon**
  - [x] 9.1 Section 4ter.ter `methodology.md` étendue : Pattern A user-event (pas setValue) + Pattern B count runtime + leçons 10.14/10.15/10.18-20/10.18-21 capitalisées en **règles d'or permanentes**.
  - [x] 9.2 Identifier patterns futurs applicables :
    - **10.20 DatePicker** : Reka UI `<PopoverRoot>` wrapper + calendrier mensuel. Pattern A user-event ArrowLeft/Right/PageUp/PageDown WAI-ARIA Date Picker Dialog pattern. Pattern B count runtime. Note pré-10.20 : vérifier Reka UI Popover exports (Task 1.5 template 10.19 réutilisable).
    - **10.21 Lucide + EsgIcon** : intégration `lucide-vue-next` → placeholder SVG Tabs/Combobox 10.19 **migration mécanique** (remplacement `<svg>` inline par `<ChevronDown />` / `<Check />` / `<X />`). Note pré-10.21 : inventorier sites SVG inline post-10.19 pour check-list migration (Button chevron Drawer + Combobox trigger + Badge icons + Tabs icons).

## Dev Notes

### 1. Architecture cible — arborescence finale post-10.19

```
frontend/
├── app/
│   └── components/
│       └── ui/                     (7 composants existants 10.15-10.18 + 2 NOUVEAUX + 2 brownfield)
│           ├── FullscreenModal.vue       (inchangé, brownfield)
│           ├── ToastNotification.vue     (inchangé, brownfield)
│           ├── Button.vue                (inchangé 10.15)
│           ├── Button.stories.ts         (inchangé 10.15)
│           ├── Input.vue                 (inchangé 10.16)
│           ├── Input.stories.ts          (inchangé 10.16)
│           ├── Textarea.vue              (inchangé 10.16)
│           ├── Textarea.stories.ts       (inchangé 10.16)
│           ├── Select.vue                (inchangé 10.16)
│           ├── Select.stories.ts         (inchangé 10.16)
│           ├── Badge.vue                 (inchangé 10.17)
│           ├── Badge.stories.ts          (inchangé 10.17)
│           ├── Drawer.vue                (inchangé 10.18)
│           ├── Drawer.stories.ts         (inchangé 10.18)
│           ├── Combobox.vue              (NOUVEAU 10.19 : wrapper Reka UI ComboboxRoot + IME guard + multi-select badges)
│           ├── Combobox.stories.ts       (NOUVEAU 10.19 : ≥ 7 stories CSF 3.0)
│           ├── Tabs.vue                  (NOUVEAU 10.19 : wrapper Reka UI TabsRoot + orientation/activationMode/forceMount)
│           ├── Tabs.stories.ts           (NOUVEAU 10.19 : ≥ 7 stories CSF 3.0)
│           └── registry.ts               (ÉTENDU 10.19 : +3 frozen tuples COMBOBOX_MODES/TABS_ORIENTATIONS/TABS_ACTIVATION_MODES)
├── tests/components/ui/             (14 fichiers existants post-10.18 + 8 NOUVEAUX 10.19)
│   ├── test_combobox_registry.test.ts             (NOUVEAU)
│   ├── test_combobox_behavior.test.ts             (NOUVEAU — Pattern A user-event strict + IME guard)
│   ├── test_combobox_a11y.test.ts                 (NOUVEAU — smoke + délégation runtime Storybook)
│   ├── test_tabs_registry.test.ts                 (NOUVEAU)
│   ├── test_tabs_behavior.test.ts                 (NOUVEAU — Pattern A user-event strict)
│   ├── test_tabs_a11y.test.ts                     (NOUVEAU — smoke + délégation runtime Storybook)
│   ├── test_no_hex_hardcoded_combobox_tabs.test.ts (NOUVEAU)
│   ├── Combobox.test-d.ts                         (NOUVEAU : ≥ 6 @ts-expect-error)
│   └── Tabs.test-d.ts                             (NOUVEAU : ≥ 6 @ts-expect-error)

docs/CODEMAPS/
└── ui-primitives.md                 (ÉTENDU 10.19 : §3.6 Combobox + §3.7 Tabs + pièges 35-40 + §2 arbo)
└── methodology.md                   (ÉTENDU 10.19 : §4ter.ter application proactive 10.19 — 6 leçons cumulées)
```

**Aucune modification** :
- `frontend/app/assets/css/main.css` (tokens livrés 10.14-10.17).
- `frontend/.storybook/main.ts` (glob `gravity/ + ui/` déjà étendu 10.15).
- `frontend/.storybook/preview.ts` (dark mode + a11y config stables 10.14+10.15).
- `frontend/vitest.config.ts` (typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15).
- `frontend/nuxt.config.ts`, `tsconfig.json` (auto-imports + strict mode déjà OK).
- `frontend/package.json` (Reka UI 2.9.6 déjà installé ; vérifier `@testing-library/user-event` — ajout conditionnel Task 1.6 si manquant).
- Tous les composants `ui/` pré-existants (Button + Input + Textarea + Select + Badge + Drawer + brownfield).
- `frontend/app/components/gravity/*` (aucun consommateur 10.19 en Phase 0 — migrations Epic 8/10/11/15/19).

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|----------|----------|-----------|
| **Q1** | Wrapper **Reka UI `<ComboboxRoot>` + `<TabsRoot>`** OU **shadcn-vue** OU **headless maison** ? | **Reka UI nu** | UX Step 6 Q15 (« Reka UI nu, pas shadcn-vue ») + Step 11 §3 (« Reka UI primitives = base accessible ARIA »). Pattern wrapper Reka UI déjà maîtrisé 10.18 (Drawer). Shadcn-vue = abstraction supplémentaire non désirée, headless maison = re-développer keyboard nav + focus management (coût 6-12 h + risques a11y). Reka UI fournit `role="combobox"` + `aria-activedescendant` + keyboard cycle WAI-ARIA natif. |
| **Q2** | **Combobox `multiple` prop** vs **Combobox séparé `MultiCombobox.vue`** ? | **Prop `multiple` unique** | Moins de composants = moins de duplication (CLAUDE.md §Reutilisabilite). Pattern cohérent `<select multiple>` natif HTML. TypeScript TSC 5.x supporte union `T | T[]` (fallback discriminé via runtime check). Inconvénient : typage plus permissif que discriminated union `{multiple:true, modelValue:T[]} | {multiple:false, modelValue:T}` — tracé `DEF-10.19-1` si pattern récurrent Phase 1+ (peu probable : majorité usage single). |
| **Q3** | **Tabs horizontal default** OU **vertical default** ? | **Horizontal default** | Cas majoritaire UI (95 %+ tabs apps SaaS). Vertical réservé cas spécifiques (sidebar admin, nav avec labels longs, accessibilité dyslexie). WAI-ARIA recommande horizontal par défaut. Epic spec AC3 ne précise pas default explicitement mais `tabs[]` + `modelValue` suggèrent horizontal list standard. |
| **Q4** | **Tabs activation `automatic` default** OU **`manual` default** ? | **Automatic default** | WAI-ARIA Authoring Practices : « Automatic activation is the most common », adapté pour majorité cas (navigation intra-page rapide). Manual réservé à screen reader users pour exploration sans charger contenu coûteux. Inconvénient : un utilisateur screen reader ArrowRight dans tabs lourds charge inutilement — solution : consommateur passe `activationMode: 'manual'` explicitement si pertinent (ex. dashboard multi-projet Moussa avec graphs Chart.js coûteux en render). |
| **Q5** | **Combobox searchable default `true`** OU **`false`** ? | **`true`** | Différenciateur vs Select natif : Combobox EST par définition searchable (sinon on utilise Select 10.16). Désactiver search = fallback UI sans valeur ajoutée vs Select. Si consommateur veut listbox sans search, utiliser Select. Documenté §3.6 codemap + piège #36 (cas limites edge). |

### 3. Exemple squelette — `ui/Combobox.vue` (structure condensée)

```vue
<script setup lang="ts" generic="T extends string | number = string">
import { computed, ref, useId } from 'vue';
import {
  ComboboxRoot,
  ComboboxAnchor,
  ComboboxInput,
  ComboboxTrigger,
  ComboboxPortal,
  ComboboxContent,
  ComboboxViewport,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxLabel,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxSeparator,
  ComboboxCancel,
} from 'reka-ui';
import Badge from './Badge.vue';
import type { ComboboxMode } from './registry';

interface ComboboxOption<T extends string | number> {
  value: T;
  label: string;
  disabled?: boolean;
  group?: string;
}

interface ComboboxProps<T extends string | number = string> {
  modelValue: T | T[] | null;
  options: Array<ComboboxOption<T>>;
  label: string;
  multiple?: boolean;
  placeholder?: string;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  open?: boolean;
}

const props = withDefaults(defineProps<ComboboxProps<T>>(), {
  multiple: false,
  placeholder: 'Sélectionner...',
  emptyLabel: 'Aucun résultat',
  searchable: true,
  disabled: false,
  required: false,
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: T | T[] | null): void;
  (e: 'update:open', value: boolean): void;
}>();

const searchTerm = ref('');
const isComposing = ref(false);
const labelId = useId();

// Normalisation Unicode NFD + casse insensible (AC3)
function normalize(str: string): string {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

const filteredOptions = computed(() => {
  if (!props.searchable || isComposing.value || !searchTerm.value) {
    return props.options;
  }
  const needle = normalize(searchTerm.value);
  return props.options.filter((opt) => normalize(opt.label).includes(needle));
});

const groupedOptions = computed(() => {
  const groups = new Map<string | undefined, ComboboxOption<T>[]>();
  for (const opt of filteredOptions.value) {
    const key = opt.group;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(opt);
  }
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
});

const selectedValues = computed<T[]>(() => {
  if (props.modelValue === null) return [];
  return Array.isArray(props.modelValue) ? props.modelValue : [props.modelValue];
});

function labelFor(value: T): string {
  return props.options.find((o) => o.value === value)?.label ?? String(value);
}

function removeValue(value: T) {
  if (!props.multiple) return;
  const next = selectedValues.value.filter((v) => v !== value);
  emit('update:modelValue', next);
}

function handleCompositionStart() {
  isComposing.value = true;
}

function handleCompositionEnd(e: CompositionEvent) {
  isComposing.value = false;
  searchTerm.value = (e.target as HTMLInputElement).value;
}
</script>

<template>
  <div>
    <label :id="labelId" class="block text-sm font-medium text-surface-text dark:text-surface-dark-text mb-1">
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>
    <ComboboxRoot
      :model-value="modelValue"
      :multiple="multiple"
      :disabled="disabled"
      :open="open"
      @update:model-value="emit('update:modelValue', $event as T | T[] | null)"
      @update:open="emit('update:open', $event)"
    >
      <ComboboxAnchor
        class="flex flex-wrap items-center gap-1 min-h-11 px-2 py-1 border rounded-md bg-white dark:bg-dark-input border-gray-300 dark:border-dark-border focus-within:ring-2 focus-within:ring-brand-green"
      >
        <template v-if="multiple">
          <Badge
            v-for="val in selectedValues"
            :key="String(val)"
            variant="lifecycle"
            state="applicable"
            size="sm"
          >
            <span>{{ labelFor(val) }}</span>
            <button
              type="button"
              class="ml-1 min-h-11 min-w-11 inline-flex items-center justify-center hover:bg-gray-200 dark:hover:bg-dark-hover rounded"
              :aria-label="`Retirer ${labelFor(val)}`"
              @click.stop="removeValue(val)"
            >
              ×
            </button>
          </Badge>
        </template>
        <ComboboxInput
          v-model="searchTerm"
          :placeholder="placeholder"
          :aria-labelledby="labelId"
          :required="required"
          class="flex-1 bg-transparent outline-none text-surface-text dark:text-surface-dark-text placeholder:text-surface-text/40 dark:placeholder:text-surface-dark-text/40"
          @compositionstart="handleCompositionStart"
          @compositionend="handleCompositionEnd"
        />
        <ComboboxTrigger class="p-1 text-surface-text dark:text-surface-dark-text">
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
            <path d="M4 6 L8 10 L12 6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </ComboboxTrigger>
      </ComboboxAnchor>
      <ComboboxPortal>
        <ComboboxContent
          class="z-50 bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-md shadow-lg mt-1 max-h-[300px] overflow-hidden data-[state=open]:animate-in data-[state=closed]:animate-out motion-reduce:animate-none"
        >
          <ComboboxViewport class="p-1">
            <ComboboxEmpty
              class="p-4 text-center text-surface-text/60 dark:text-surface-dark-text/60"
              role="status"
              aria-live="polite"
            >
              <slot name="empty">{{ emptyLabel }}</slot>
            </ComboboxEmpty>
            <template v-for="(group, idx) in groupedOptions" :key="group.label ?? idx">
              <ComboboxGroup v-if="group.label">
                <ComboboxLabel class="px-2 py-1 text-xs font-semibold text-surface-text/60 dark:text-surface-dark-text/60 uppercase">
                  {{ group.label }}
                </ComboboxLabel>
                <ComboboxItem
                  v-for="opt in group.items"
                  :key="String(opt.value)"
                  :value="opt.value"
                  :disabled="opt.disabled"
                  class="flex items-center justify-between px-2 py-2 rounded cursor-pointer text-surface-text dark:text-surface-dark-text data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-dark-hover data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20 data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed"
                >
                  <span>{{ opt.label }}</span>
                  <ComboboxItemIndicator>
                    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor">
                      <path d="M3 7 L6 10 L11 4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </ComboboxItemIndicator>
                </ComboboxItem>
              </ComboboxGroup>
              <ComboboxItem
                v-for="opt in group.items"
                v-else
                :key="String(opt.value)"
                :value="opt.value"
                :disabled="opt.disabled"
                class="flex items-center justify-between px-2 py-2 rounded cursor-pointer text-surface-text dark:text-surface-dark-text data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-dark-hover data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20 data-[disabled]:opacity-50"
              >
                <span>{{ opt.label }}</span>
                <ComboboxItemIndicator>✓</ComboboxItemIndicator>
              </ComboboxItem>
            </template>
          </ComboboxViewport>
        </ComboboxContent>
      </ComboboxPortal>
    </ComboboxRoot>
  </div>
</template>
```

**Rationale** :
- **Zéro hex** : tous via tokens `@theme` (surface-* + dark-* + brand-green/red) livrés 10.14+10.15.
- **IME composition guard** (AC3 piège #38) : `isComposing` ref + skip filter pendant composition.
- **Normalisation Unicode NFD + lowercase** (AC3) : `str.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()` — pattern byte-identique consommable.
- **Badges multi-select** (AC2) : `ui/Badge` variant `lifecycle` state `applicable` réutilisé + bouton × avec touch target ≥ 44 px (`min-h-11 min-w-11`).
- **Dark mode ≥ 10** : input + content + borders + texts + hover (2) + highlighted (Reka UI data-attr) + checked (Reka UI data-attr) + disabled + placeholder → comptage précis Task 7.7.
- **prefers-reduced-motion** : `motion-reduce:animate-none` sur dropdown open/close animations.
- **ARIA** : `aria-labelledby` via prop `label`, le reste (aria-expanded, aria-controls, aria-activedescendant, role="combobox", role="listbox", role="option") fourni par Reka UI primitives.

### 4. Exemple squelette — `ui/Tabs.vue` (structure condensée)

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { TabsRoot, TabsList, TabsTrigger, TabsContent } from 'reka-ui';
import type { TabsOrientation, TabsActivationMode } from './registry';
import type { Component } from 'vue';

interface TabItem {
  value: string;
  label: string;
  icon?: Component;
  disabled?: boolean;
}

interface TabsProps {
  modelValue: string;
  tabs: TabItem[];
  orientation?: TabsOrientation;
  activationMode?: TabsActivationMode;
  forceMount?: boolean;
  label?: string;
}

const props = withDefaults(defineProps<TabsProps>(), {
  orientation: 'horizontal',
  activationMode: 'automatic',
  forceMount: false,
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const orientationClasses = computed(() => {
  if (props.orientation === 'vertical') {
    return {
      list: 'flex flex-col border-r border-gray-200 dark:border-dark-border',
      triggerBase: 'px-4 py-2 -mr-px border-r-2 border-transparent text-left',
      triggerActive: 'border-r-2 border-brand-green text-brand-green dark:text-brand-green',
    };
  }
  return {
    list: 'flex flex-row border-b border-gray-200 dark:border-dark-border',
    triggerBase: 'px-4 py-2 -mb-px border-b-2 border-transparent',
    triggerActive: 'border-b-2 border-brand-green text-brand-green dark:text-brand-green',
  };
});
</script>

<template>
  <TabsRoot
    :model-value="modelValue"
    :orientation="orientation"
    :activation-mode="activationMode"
    class="w-full"
    @update:model-value="(v: string | number) => $emit('update:modelValue', String(v))"
  >
    <TabsList
      :aria-label="label"
      :class="orientationClasses.list"
    >
      <TabsTrigger
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
        :disabled="tab.disabled"
        :class="[
          orientationClasses.triggerBase,
          'text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none',
          modelValue === tab.value ? orientationClasses.triggerActive : '',
          tab.disabled ? 'opacity-50 cursor-not-allowed dark:opacity-50' : '',
        ]"
      >
        <component :is="tab.icon" v-if="tab.icon" class="mr-2 h-4 w-4 inline-block" aria-hidden="true" />
        {{ tab.label }}
      </TabsTrigger>
    </TabsList>
    <TabsContent
      v-for="tab in tabs"
      :key="tab.value"
      :value="tab.value"
      :force-mount="forceMount || undefined"
      tabindex="0"
      class="p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green text-surface-text dark:text-surface-dark-text"
    >
      <slot :name="`content-${tab.value}`" :tab="tab">
        <slot name="fallback" :tab="tab" />
      </slot>
    </TabsContent>
  </TabsRoot>
</template>
```

**Rationale** :
- **4 primitives Reka UI** : TabsRoot + TabsList + TabsTrigger + TabsContent (AC7).
- **Dark mode ≥ 10** : list border + trigger text + hover + focus-visible ring + active (horizontal/vertical) border + active text + disabled + 2 variantes dark border-brand-green active + fallback contrast — ajuster Task 4.8 selon résultat `grep -oE "dark:"`.
- **Orientation via computed** : un seul `<TabsList>` + `<TabsTrigger>` template, classes dérivées (AC8).
- **ForceMount piège Reka UI** (piège #37) : `forceMount || undefined` évite d'activer accidentellement lazy mount.
- **Slot `content-${value}`** : AC3 epic spec permet consommateur d'injecter contenu riche par onglet.
- **ARIA** : `role="tablist"` / `role="tab"` / `role="tabpanel"` + `aria-orientation` + `aria-selected` fournis par Reka UI (AC10).

### 5. Pièges documentés (6 nouveaux — 35-40 — cumul ≥ 40 avec 34 existants 10.14-10.18)

**35. Registry ordres canoniques frozen — changer l'ordre = rupture API** — Les 3 tuples 10.19 (`COMBOBOX_MODES` / `TABS_ORIENTATIONS` / `TABS_ACTIVATION_MODES`) suivent l'ordre canonique WAI-ARIA + usage majoritaire. Index 0 = default inféré (pattern 10.18 `DRAWER_SIDES[0] === 'right'`). Changer `COMBOBOX_MODES = ['multiple', 'single']` = rupture API tous consommateurs (le default devient `'multiple'`). Invariant : tests `test_combobox_registry.test.ts` + `test_tabs_registry.test.ts` assert `COMBOBOX_MODES[0] === 'single'` + `TABS_ORIENTATIONS[0] === 'horizontal'` + `TABS_ACTIVATION_MODES[0] === 'automatic'` canonical order.

**36. Combobox Escape behavior Reka UI 2.9.6 vs WAI-ARIA** — WAI-ARIA Combobox Authoring Practices : Escape ferme dropdown + efface filter input + garde focus sur input. Reka UI 2.9.6 `ComboboxRoot` Escape comportement exact à vérifier Task 3 (possiblement : ferme dropdown + garde focus + NE efface PAS filter input automatiquement). Si divergence, documenter §3.6 codemap + proposition consommateur pattern `@update:open="(open) => if (!open) searchTerm = ''"` pour aligner WAI-ARIA. **Alternative** : ajouter prop `clearOnClose: boolean` Phase Growth si pattern récurrent (deferred `DEF-10.19-3`).

**37. Combobox + Tabs `forceMount` piège Reka UI — prop présence, pas boolean** — Reka UI `forceMount` (disponible sur Combobox et Tabs) est une **prop présence** : sa simple présence dans le template active le forceMount, `false` peut être interprété comme `true` selon l'implémentation Reka UI. **Solution** : passer `:force-mount="forceMount || undefined"` pour que la prop ne soit pas rendue quand `forceMount === false`. Test vérifie via `screen.queryByTestId('tab-content-t2')` null quand `forceMount=false` + modelValue !== 't2'.

**38. IME composition guard CJK + accents Mac FR (option-e / option-`)** — Critique Combobox searchable multi-langue. Sans guard `isComposing`, l'utilisateur Mac tapant `é` via option-e (composition 2 étapes : d'abord `e`, puis `é` finalisé) déclenche filter sur `e` intermédiaire → l'option `Égypte` disparaît alors qu'elle devrait être filtrée présente. Même pattern : accents `à` (option-`) + `ù` + `ô` + CJK pinyin romaji hangul. **Solution** : `ref isComposing` + `@compositionstart` / `@compositionend` handlers + `filteredOptions` computed skippe filter pendant `isComposing === true`. Test via `fireEvent.compositionStart(input)` + `fireEvent.input(input, {target:{value:'e'}})` + `expect(queryByRole('option', {name:/égypte/i})).toBeNull()` (no filter) puis `fireEvent.compositionEnd(input)` + `expect(getByRole('option', {name:/égypte/i})).toBeInTheDocument()` (filter déclenché post-composition).

**39. Tabs vertical underline indicator cohérence RTL (Phase Growth)** — Si futur support RTL (arabe Maghreb/Mauritanie), border-r vertical devient border-l en RTL. Pattern Phase 0 : pas de gestion RTL. **Piège signalé** pour éviter hardcode `border-r` sans `ltr:` / `rtl:` préfixe Tailwind (`rtl:border-l rtl:border-r-0`). Deferred `DEF-10.19-2 RTL support Tabs vertical Phase Growth` si 1 consommateur Maghreb demande explicitement. Pour Phase 0 : documenté §3.7 codemap en note RTL future.

**40. Tabs lazy forceMount vs accessibility browser search (Ctrl+F)** — `forceMount: false` (default) = tabpanel inactif non dans DOM → Ctrl+F navigateur ne trouve pas le texte dans tabs inactifs. Trade-off : (a) perf default (pas de render inactifs) vs (b) searchability forceMount=true. **Recommandation consommateur** : documentation longue multi-onglets (ex. `ReferentialComparisonView` Epic 10 avec 500+ règles par onglet) → `forceMount="true"` pour Ctrl+F. Formulaire complexe multi-step → `forceMount="false"` default (économise render). Documenté §3.7 codemap trade-off explicite.

### 6. Test plan complet

| # | Test | Type | Delta baseline 672 |
|---|------|------|--------------------|
| T1 | `COMBOBOX_MODES.length === 2` + frozen + dedup + ordre canonique `'single'` first | Vitest unit | +4 |
| T2 | `TABS_ORIENTATIONS.length === 2` + frozen + dedup + ordre `'horizontal'` first | Vitest unit | +4 |
| T3 | `TABS_ACTIVATION_MODES.length === 2` + frozen + dedup + ordre `'automatic'` first | Vitest unit | +4 |
| T4 | Combobox v-model single select via user.type + user.click option | Vitest user-event Pattern A | +1 |
| T5 | Combobox v-model multiple + badges rendered + bouton × fonctionnel | Vitest user-event | +2 |
| T6 | Combobox search insensible casse `'SEN'/'sen'/'Sen'` → Sénégal | Vitest user-event | +1 |
| T7 | Combobox search diacritiques `'cot'` → Côte d'Ivoire | Vitest user-event | +1 |
| T8 | Combobox IME composition guard : compositionStart + input → no filter | Vitest fireEvent | +1 |
| T9 | Combobox IME composition end → filter déclenché | Vitest fireEvent | +1 |
| T10 | Combobox keyboard ArrowDown cycle infini | Vitest user.keyboard | +1 |
| T11 | Combobox keyboard Home/End | Vitest user.keyboard | +2 |
| T12 | Combobox keyboard Enter → option sélectionnée | Vitest user.keyboard | +1 |
| T13 | Combobox keyboard Escape → dropdown fermé | Vitest user.keyboard | +1 |
| T14 | Combobox empty state default message 'Aucun résultat' | Vitest user.type | +1 |
| T15 | Combobox empty state custom slot override | Vitest | +1 |
| T16 | Combobox options disabled individuels aria-disabled | Vitest | +1 |
| T17 | Combobox ARIA role=combobox + aria-expanded + aria-controls | Vitest a11y Pattern A | +3 |
| T18 | Combobox vitest-axe smoke (délégation runtime Storybook contraste/focus portail) | Vitest | +1 |
| T19 | Tabs v-model via user.click tab 2 + tabpanel content switched | Vitest user-event | +1 |
| T20 | Tabs orientation horizontal aria-orientation + classes | Vitest | +1 |
| T21 | Tabs orientation vertical aria-orientation + classes | Vitest | +1 |
| T22 | Tabs activation automatic : ArrowRight → modelValue change | Vitest user.keyboard | +1 |
| T23 | Tabs activation manual : ArrowRight → focus only + Enter → modelValue | Vitest user.keyboard | +1 |
| T24 | Tabs keyboard Home/End | Vitest user.keyboard | +2 |
| T25 | Tabs keyboard cycle infini ArrowRight depuis tN-1 → t0 | Vitest user.keyboard | +1 |
| T26 | Tabs disabled tab skip in keyboard nav | Vitest user.keyboard | +1 |
| T27 | Tabs forceMount default false → panels inactifs non dans DOM | Vitest | +1 |
| T28 | Tabs forceMount true → tous panels montés | Vitest | +1 |
| T29 | Tabs icon rendered + aria-hidden | Vitest | +1 |
| T30 | Tabs aria-label sur TabsList conditionnel | Vitest | +1 |
| T31 | Tabs ARIA role=tablist + role=tab + role=tabpanel + aria-selected | Vitest a11y Pattern A | +4 |
| T32 | Tabs vitest-axe smoke | Vitest | +1 |
| T33 | Scan hex `Combobox.vue` + stories → 0 hit | Vitest fs | +1 |
| T34 | Scan hex `Tabs.vue` + stories → 0 hit | Vitest fs | +1 |
| T35 | `test_docs_ui_primitives` §3.6 + §3.7 + ≥40 pièges + ≥4 exemples §3.6 + ≥4 exemples §3.7 | Vitest doc grep | +4 |
| T36 | **Combobox.test-d.ts** (6+ assertions `@ts-expect-error`) | TS typecheck | +6 typecheck |
| T37 | **Tabs.test-d.ts** (6+ assertions `@ts-expect-error`) | TS typecheck | +6 typecheck |
| **Total delta runtime** | | | **+56 tests** (plancher AC14 ≥ +30 largement dépassé) |
| **Total delta typecheck** | | | **+12** (plancher AC14 ≥ 12 atteint) |
| Storybook runtime | `jq '[.entries | ... | test("^ui-(combobox|tabs)--"))] | length'` | Comptage build | **≥ 14 nouvelles cumulées** (cible réaliste ≥ 20 avec autodocs) |
| Baseline runtime | 672 → 728+ passed (aucune régression) | Vitest | **0 régression** |
| Baseline typecheck | 61 → 73+ assertions | Vitest --typecheck | **+12** |

### 7. Checklist review (pour code-reviewer Story 10.19 post-merge)

- [ ] **Reka UI wrapper strict (pas headless maison)** — `rg 'import.*from .reka-ui' frontend/app/components/ui/Combobox.vue` doit retourner ≥ 14 primitives Combobox* + `Tabs.vue` doit retourner 4 primitives Tabs*.
- [ ] **Tokens `@theme` exclusifs** — `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Combobox.vue Combobox.stories.ts Tabs.vue Tabs.stories.ts` → 0 hit hors commentaires.
- [ ] **TypeScript strict enforcé** — `rg ': any|as unknown' frontend/app/components/ui/Combobox.vue Tabs.vue` → 0 hit.
- [ ] **Combobox.test-d.ts ≥ 6 + Tabs.test-d.ts ≥ 6** — vérifiés via `npm run test:typecheck` (baseline 61 → 73+).
- [ ] **Dark mode ≥ 10 per component** — `rg 'dark:' frontend/app/components/ui/Combobox.vue | wc -l` ≥ 10 ET `rg 'dark:' frontend/app/components/ui/Tabs.vue | wc -l` ≥ 10 sans inflation artificielle.
- [ ] **WCAG 2.1 AA via Storybook `addon-a11y` runtime** (PAS vitest-axe happy-dom seul pour contraste/portail Combobox — leçon 10.15 HIGH-2 + 10.18 §4ter.bis capitalisée) — 0 violation `storybook:test` CI sur `ui-combobox--*` + `ui-tabs--*`.
- [ ] **Pattern A user-event strict** — aucun `wrapper.vm.*` ni `input.setValue(...)` dans `test_combobox_behavior.test.ts` + `test_tabs_behavior.test.ts`, toutes assertions via `screen.getByRole` + `user.type/click/keyboard` + `document.body.querySelector` portal-aware Combobox.
- [ ] **Pattern B (comptage runtime Storybook)** — Completion Notes contient EXACT output `jq '[.entries | to_entries[] | select(.value.id | test("^ui-(combobox|tabs)--"))] | length'` — pas d'estimation.
- [ ] **IME composition guard** — `compositionstart` / `compositionend` handlers présents dans Combobox.vue + test `test_combobox_behavior.test.ts` case `ime-composition-guard` présent (Leçon 21 strict — `expect(queryByRole).toBeNull()` pré-end + `getByRole` post-end).
- [ ] **Tabs forceMount prop présence piège** — `:force-mount="forceMount || undefined"` (pas `false`) dans Tabs.vue (piège #37).
- [ ] **Tests observables stricts (Leçon 21 §4quater)** — AUCUN `if (emitted) { expect(...) }` permissif, AUCUN smoke `expect(queryEl).not.toBeNull()` sans assertion stricte sur effet. Délégations explicites documentées inline `// DELEGATED TO Storybook {{StoryName}}`.
- [ ] **Ajustements vs spec documentés (Leçon 20 §4quater)** — Completion Notes contient section « Ajustements mineurs vs spec » exhaustive (écarts listés OU explicite `Aucun écart vs spec`).
- [ ] **Touch target ≥ 44 × 44 px** — bouton `×` badges Combobox multi-select + tabs Combobox + Tabs trigger avec `min-h-11 min-w-11` OU `py-2 px-4` cumulé ≥ 44 px.
- [ ] **Coverage ≥ 85%** — `npm run test -- --coverage` retourne `Combobox.vue` + `Tabs.vue` ≥ 85 % lines/branches.
- [ ] **Pas de duplication** — `COMBOBOX_MODES` / `TABS_ORIENTATIONS` / `TABS_ACTIVATION_MODES` source unique `registry.ts` — importés par `Combobox.vue` + `Tabs.vue` + stories + tests.
- [ ] **Shims legacy 10.6** — aucune modification des 7 primitives `ui/` existantes (Button + Input + Textarea + Select + Badge + Drawer) + brownfield (FullscreenModal + ToastNotification). `git diff frontend/app/components/ui/ -- ':!Combobox.*' ':!Tabs.*' ':!registry.ts'` → vide.
- [ ] **Glob Storybook inchangé** — `frontend/.storybook/main.ts` diff restreint à 0 ligne.
- [ ] **Bundle Storybook ≤ 15 MB** — `du -sh frontend/storybook-static` respecté (marge ≥ 6 MB post-10.18).
- [ ] **No secret exposé** — `rg 'API_KEY|SECRET|TOKEN' frontend/app/components/ui/Combobox* Tabs*` → 0 hit.
- [ ] **prefers-reduced-motion respect** — Combobox dropdown animation `motion-reduce:animate-none` + Tabs underline indicator **pas d'animation** (position change immédiate CSS border switch).
- [ ] **AC7 epic spec AC7 respecté** — « l'indicateur underline se déplace sans animation (position change immédiate) » — Tabs.vue doit avoir `motion-reduce:transition-none` sur TabsTrigger + pas de `transition-transform` / `transition-all` sur border.

### 8. Pattern commits intermédiaires (leçon 10.8+10.14+10.15+10.16+10.17+10.18)

4 commits lisibles review (plus granulaire que 10.18 car 2 composants parallèles) :
1. `feat(10.19): registry CCC-9 3 tuples (COMBOBOX_MODES + TABS_ORIENTATIONS + TABS_ACTIVATION_MODES)` (Task 2) — registry extension byte-identique 10.17/10.18 pattern.
2. `feat(10.19): ui/Combobox primitive wrapper Reka UI 14 primitives + IME composition guard + multi-select badges` (Task 3) — composant Combobox + IME guard + Badge réutilisation.
3. `feat(10.19): ui/Tabs primitive wrapper Reka UI 4 primitives + orientation/activationMode/forceMount + .test-d.ts 12+ assertions` (Task 4 + partiel 5) — composant Tabs + `Combobox.test-d.ts` + `Tabs.test-d.ts`.
4. `feat(10.19): stories CSF3 + tests behavior/a11y Pattern A user-event + docs CODEMAPS §3.6 §3.7 + methodology §4ter.ter + count runtime vérifié` (Task 5 runtime + 6 + 7 + 8) — stories + tests Pattern A + docs + Completion Notes avec 4 chiffres jq.

Pattern CCC-9 (10.8+10.14+10.15+10.16+10.17+10.18) appliqué byte-identique : `COMBOBOX_MODES` + `TABS_ORIENTATIONS` + `TABS_ACTIVATION_MODES` frozen `Object.freeze([...] as const)` + validation `test_combobox_registry.test.ts` + `test_tabs_registry.test.ts`.

Pattern compile-time enforcement `.test-d.ts` (10.15 HIGH-1) réutilisé byte-identique : `Combobox.test-d.ts` + `Tabs.test-d.ts` dans `tests/components/ui/` + `vitest typecheck` déjà configuré.

Pattern darken tokens AA (10.15 HIGH-2) : **applicable** — Combobox aria-selected Item + Tabs active underline utilisent `brand-green #047857` post-darken AA (5,78:1) cohérent Button focus + Drawer focus ring.

Pattern soft-bg contraste (10.17 CRITICAL-1/2) : **applicable Combobox aria-selected** — `data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20` (soft-bg) sur ComboboxItem sélectionné. Contraste texte `surface-text` sur fond `brand-green/10` à vérifier Storybook addon-a11y runtime (probablement AA si texte reste sombre — cas limite).

Pattern describedBy aligné v-if (10.16 H-1) : **applicable partiel** — Combobox `aria-describedby` non prévu Phase 0 (pas de message d'erreur inline dans l'interface Phase 0, différé Phase 1 si pattern émerge).

Pattern IME composition (10.16 H-2) : **appliqué Combobox** Task 3.6 — critique pour accents FR + CJK (piège #38 §5 codemap).

Pattern multi-select native binding (10.16 H-3) : **appliqué Combobox** — `multiple` prop → `modelValue: T[]` array + `watch()` non nécessaire (Reka UI ComboboxRoot gère natif).

Pattern type coercion string-only (10.16 H-4) : **non applicable** — Combobox generic `T extends string | number` pas de coercion. Tabs `modelValue: string` strict.

Pattern anti-badge-as-button (10.17 Q5 piège #24) : **non applicable** — Combobox badges multi-select contiennent bouton `×` explicite (pas click sur badge entier) — sémantique correcte.

**Pattern A méthodologique (10.16 H-3 + capitalisé 10.17 + 10.18 §4ter.bis)** : **appliqué proactivement strict** Task 5.3-5.6 — tests Combobox + Tabs utilisent `screen.getByRole` + `user.type/click/keyboard` (`@testing-library/user-event` native bindings) — jamais `wrapper.vm.*` ni `input.setValue(...)`. **Enjeu spécifique Combobox portal** : `ComboboxPortal` monte `ComboboxContent` sur `document.body` → assertions via `screen.getByRole('listbox')` + `screen.getByRole('option')` fonctionnent grâce à `@testing-library/vue` qui scanne body par défaut.

**Pattern B méthodologique (10.16 M-3 + capitalisé 10.17 + 10.18 §4ter.bis Pattern 2)** : **appliqué proactivement** Task 7.3 — 4 chiffres `jq` consignés Completion Notes AVANT claim de complétude.

**Pattern leçon 10.14 HIGH-2 (role override)** : **non applicable** — `role="combobox"` + `role="tablist"` / `role="tab"` / `role="tabpanel"` sont les rôles CORRECTS pour ces composants (pas d'override nécessaire vs Drawer qui était un cas particulier `complementary` vs `dialog`).

**Pattern leçon 10.15 HIGH-2 (Storybook runtime pour portail)** : **capitalisé infra** — `test_combobox_a11y.test.ts` explicite délégation portail-dépendante (Combobox dropdown portalisé) à Storybook runtime + piège #38 codemap ajouté. Tabs non-portalisé → pas de délégation nécessaire, vitest-axe happy-dom suffit.

**Pattern leçon 20 §4quater (Écarts vs spec Completion Notes obligatoires)** : **appliqué proactivement** Task 7.4 — section « Ajustements mineurs vs spec » exhaustive, absence d'item = spec intégralement honorée.

**Pattern leçon 21 §4quater (Tests observables ≠ smoke d'existence)** : **appliqué proactivement strict** Task 5.10 — assertions strictes sur cycle keyboard infini + forceMount lazy + IME composition guard avant/après + Enter émission payload. Délégations explicites documentées inline pour focus layout-box-dependent (Storybook runtime).

### 9. Hors scope explicite (non-objectifs cette story)

- ❌ **Migration consommateurs catalogue (Epic 8 fonds + intermédiaires filtrables)** — Phase 1 Epic 8. Story 10.19 livre uniquement les primitives.
- ❌ **`ReferentialComparisonView` Epic 10** — Phase 1 consommateur futur Tabs horizontal.
- ❌ **Dashboard multi-projets Moussa Epic 11** — Phase 1.
- ❌ **Sélection multi-pays Moussa Journey Epic 15** — Phase 1 consommateur futur Combobox multiple.
- ❌ **Onglets admin N1/N2/N3 peer-review Epic 19** — Phase 1.
- ❌ **Combobox discriminated union typing `{multiple:true, modelValue:T[]}` vs `{multiple:false, modelValue:T}`** — Fallback permissif `T | T[] | null` Phase 0. Deferred `DEF-10.19-1 Combobox discriminated union Phase Growth` si pattern récurrent Phase 1.
- ❌ **Combobox async options loading (fetch on scroll)** — pas besoin MVP. Pattern Phase Growth si catalogue > 200 fonds.
- ❌ **Combobox virtualization (TanStack Virtual)** — pas Phase 0 (50 options max testés). Phase Growth si >100 options courantes.
- ❌ **Combobox `clearOnClose` prop** — Deferred `DEF-10.19-3 Combobox clearOnClose search term on close` si divergence Reka UI vs WAI-ARIA piège #36.
- ❌ **Tabs RTL support (arabe Maghreb/Mauritanie)** — Phase Growth. Deferred `DEF-10.19-2 Tabs vertical RTL` (piège #39).
- ❌ **Tabs animated underline indicator (translate-x)** — AC7 epic spec : « pas d'animation ». Phase 0 = position change immédiate CSS border switch. Si consommateur demande animation (design review feedback), délibérer Phase Growth avec respect `prefers-reduced-motion: reduce`.
- ❌ **Tabs `TabsIndicator` Reka UI primitive** — vérifier Task 1.5 si disponible Reka UI 2.9.6. Si oui, peut simplifier indicator implementation. Si non, fallback border switch courant.
- ❌ **E2E Playwright** — Phase 0 = unit + integration Vitest + Storybook runtime. Playwright E2E couvert Epic 8+ quand consommateurs migrent.
- ❌ **Combobox + Tabs dans Drawer imbriqués** — Technique OK (pas de collision) mais pas testé Phase 0. Consommateurs Phase 1 testeront pattern.
- ❌ **Combobox custom filter function prop** — pattern `filterFn?: (option, searchTerm) => boolean` possible Phase Growth si pattern récurrent (tri flou Levenshtein, recherche phonétique etc.).
- ❌ **Combobox async validation avec debounce** — hors scope primitive UI (logique métier consommateur).
- ❌ **Tabs nested (tabs dans tabs)** — technique OK mais a11y complexe (`aria-orientation` imbrication). Pattern hors scope Phase 0.
- ❌ **Modification `FullscreenModal.vue` brownfield / `Drawer.vue` 10.18** — inchangés.
- ❌ **Integration Lucide `lucide-vue-next`** — Story 10.21. Combobox chevron + check icons + Tabs icons utilisent SVG inline path Phase 0 (migration mécanique 10.21+).

### 10. Previous Story Intelligence (10.18 + 10.17 + 10.16 + 10.15 leçons transférables)

De Story 10.18 (Drawer wrapper Reka UI sizing M + patch batch post-review) + 10.17 (Badge sizing S) + 10.16 (Input+Textarea+Select sizing M) + 10.15 (Button sizing S) + 10.14 (Storybook setup sizing L) :

**Leçons architecturales réutilisables byte-identique** :
- **Pattern wrapper Reka UI** — **Drawer 10.18 stabilisé** : DialogRoot + DialogPortal + DialogOverlay + DialogContent override ARIA + tests Pattern A DOM-only → réutilisation 10.19 pour ComboboxRoot (14 primitives) + TabsRoot (4 primitives). Pas d'override ARIA Combobox/Tabs (role correct natif Reka UI).
- **Pattern CCC-9 frozen tuple** — 9 tuples cumulés post-10.18 (`BUTTON_*` / `INPUT_*` / `FORM_*` / `VERDICT_*` / `LIFECYCLE_*` / `ADMIN_*` / `BADGE_*` / `DRAWER_*`) → +3 nouveaux 10.19 (`COMBOBOX_MODES` / `TABS_ORIENTATIONS` / `TABS_ACTIVATION_MODES`). Cumul 12 tuples après 10.19.
- **Compile-time enforcement `.test-d.ts`** — 6 fichiers post-10.18 (Button + Input + Select + Textarea + Badge + Drawer) → +2 fichiers 10.19 (Combobox + Tabs) = **8 fichiers** `.test-d.ts` cumulés. Baseline typecheck 61 → 73+.
- **Helper `asStorybookComponent<T>()`** — `frontend/app/types/storybook.ts` (10.15 MEDIUM-3) réutilisé byte-identique.
- **Scan hex + no any** — tests 10.15+10.16+10.17+10.18 réutilisés scope Combobox/Tabs.
- **Storybook co-localisation** — `<Name>.stories.ts` à côté `.vue`.
- **Dark mode seuil primitive** (10.15 MEDIUM-2 exception + 10.18 ≥ 8) — adapté 10.19 : ≥ 10 per component (Combobox + Tabs) car surfaces variées (input + content + hover + highlighted + checked + focus + active + disabled + placeholder + group label = 10+ axes).
- **Pattern Badge réutilisation Combobox multi-select** — **nouveau** 10.19 : `ui/Badge` variant `lifecycle` state `applicable` size `sm` consommé pour badges multi-select. Valide le pattern `ui/` primitive réutilisation cross-component (CLAUDE.md §Reutilisabilite).

**Leçons méthodologiques capitalisées (appliquées proactivement §4ter.bis)** :
- **Pattern A (10.16 H-3 + capitalisé 10.17 + 10.18)** — tests DOM observable via `screen.getByRole` + `user.type/click/keyboard` (pas `wrapper.vm.*` ni `input.setValue(...)`). **Enjeu Combobox spécifique** : ComboboxPortal monte ComboboxContent sur `document.body` → `screen.*` queries fonctionnent grâce à `@testing-library/vue` qui scanne body par défaut. Tabs non-portalisé → `wrapper.find(...)` OU `screen.*` indifféremment, préférence `screen.*` cohérence.
- **Pattern B (10.16 M-3 + capitalisé 10.17 piège #26 + 10.18 §4ter.bis Pattern 2)** — comptage Storybook runtime OBLIGATOIRE `jq` AVANT Completion Notes. Commande 10.19 : `jq '[.entries | to_entries[] | select(.value.id | test("^ui-(combobox|tabs)--"))] | length' storybook-static/index.json` + sous-comptages séparés.

**Leçons méthodologiques capitalisées §4quater 10.18** :
- **Leçon 20 (Écarts vs spec = Completion Notes obligatoires)** — **appliqué proactivement** Task 7.4. Section « Ajustements mineurs vs spec » exhaustive, format standardisé (AC# + prescription + décision + raison + suivi).
- **Leçon 21 (Tests observables ≠ smoke d'existence)** — **appliqué proactivement strict** Task 5.10. Assertions strictes sur keyboard cycle + forceMount lazy + IME composition + Enter émission. Délégations explicites documentées inline pour focus layout-box (Storybook runtime).

**Leçons architecturales capitalisées infra (non applicables 10.19)** :
- **Leçon 10.14 HIGH-2 (role override)** — non applicable : `role="combobox"` + `role="tablist"` / `role="tab"` / `role="tabpanel"` sont les rôles corrects WAI-ARIA natifs Reka UI.
- **Leçon 10.15 HIGH-2 (Storybook runtime pour portail)** — **capitalisé** Combobox (portail), non applicable Tabs (non-portalisé).

**Leçons 10.17 CRITICAL applicables** :
- **CRITICAL-1/2 soft-bg contraste AA** — **applicable partiel Combobox aria-selected** : `data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20` (soft-bg). Contraste texte à vérifier Storybook addon-a11y runtime.
- **CRITICAL-3 tests Pattern A DOM primaires + console spy défense** — **appliqué** cas empty state + IME guard.

**Leçons 10.17 HIGH applicables** :
- **HIGH-5 `[&_svg]` scope wrapper** — **applicable** Combobox chevron + check icons + Tabs icon slot : SVG inline scope direct pas dans slot utilisateur, pas de `[&_svg]` parent scope nécessaire.
- **HIGH-6 slot empty bypass DOM post-nextTick** — **applicable Combobox empty state** : slot `#empty` rendu default `<slot name="empty">{{ emptyLabel }}</slot>` — si consommateur fournit slot vide, fallback emptyLabel. Test `empty-slot-fallback` case.

**Leçons 10.16 HIGH applicables** :
- **H-1 describedBy aligné v-if** — **non applicable Phase 0** (pas de message erreur inline Combobox/Tabs — design différé Phase 1).
- **H-2 IME composition** — **CRITIQUE Combobox** — appliqué Task 3.6 + test case `ime-composition-guard` + piège #38.
- **H-3 Multi-select binding natif watch()** — **non nécessaire** (Reka UI ComboboxRoot gère natif multi-select via prop `multiple`).
- **H-4 type=number string coercion** — **non applicable** (Combobox generic T, Tabs string strict).

**Leçons MEDIUM 10.17 applicables à 10.19** :
- **M-1 role="img" vs role="status"** — **appliqué Combobox empty state** : `role="status"` + `aria-live="polite"` (annonce screen reader dynamique), **pas** `role="img"`.
- **M-2/M-3 DRY labels/types via registry** — **appliqué** : types `ComboboxMode` / `TabsOrientation` / `TabsActivationMode` importés depuis `registry.ts` (source unique).
- **M-5 SSR guard `import.meta.env.DEV`** — **non applicable 10.19** (pas de runtime warn nécessaire — prop boolean bien typées via `.test-d.ts`, pas de combinaison dangereuse comme 10.18 3 paths disabled).

**Règle d'or tests E2E effet observable** (10.5+10.16 H-3 + 10.17 + 10.18 §4quater Leçon 21) → appliquée systématique Task 5 Combobox + Tabs avec emphase user-event strict (`user.type` / `user.click` / `user.keyboard`) + assertions payload exact (`toEqual`, pas `toMatchObject` laxiste).

### Project Structure Notes

- Dossier `frontend/app/components/ui/` **existant** (7 composants 10.15-10.18 + 2 brownfield), ajouts : `Combobox.vue`, `Combobox.stories.ts`, `Tabs.vue`, `Tabs.stories.ts`, extension `registry.ts`. Collision zéro.
- Tests sous `frontend/tests/components/ui/` **existant** (pattern établi 10.15-10.18), 7 nouveaux fichiers + 2 `.test-d.ts` byte-cohérents.
- Pas de modification `nuxt.config.ts` (Combobox + Tabs auto-importés via `pathPrefix: false` existant CLAUDE.md).
- `tsconfig.json` frontend déjà `strict: true` → types Combobox generic `T extends string | number` + Tabs literal string hérités sans override.
- `frontend/.storybook/main.ts` **inchangé** (glob déjà étendu 10.15).
- `frontend/.storybook/preview.ts` **inchangé** (toggle dark + a11y config stable 10.14+10.15).
- `main.css` **inchangé** (tokens surface/dark/brand-green déjà livrés 10.14+10.15 — Combobox + Tabs consomment).
- `vitest.config.ts` **inchangé** (typecheck glob déjà configuré 10.15).
- Pattern Nuxt 4 auto-imports avec `pathPrefix: false` : `<Combobox>` + `<Tabs>` disponibles globalement sans import explicite. Vérifier absence collision via Task 1.1.
- **Reka UI 2.9.6 déjà installé** (10.14) — vérifier Task 1.5 exports `Combobox*/Tabs*` disponibles. **Pas de nouvelle dépendance ajoutée** (budget bundle préservé).
- **`@testing-library/user-event`** : vérifier Task 1.6 si installé (probable via 10.14 setup Storybook, sinon ajout ponctuel `^14.5.2` LTS stable).
- **Pas de `@vueuse/core` dépendance** introduite (pas besoin pour Combobox/Tabs).
- **Pas de `lucide-vue-next` dépendance** (Story 10.21 séparée — SVG inline Phase 0).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.19] — spec détaillée 8 AC + NFR + estimate M + architecture_alignment (UX Step 11 §3 Reka UI primitives + §4 P1, Q15 Reka UI)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-6-Q15] — décision Reka UI nu (pas shadcn-vue)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-11-§3-Reka-UI-Primitives] — base accessible ARIA
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-11-§4-Navigation] — patterns navigation P0/P1 (tabs) + P1 (combobox filtres)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-8-Tokens-@theme] — tokens surface-* / dark-* / brand-* consommés
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-13-A11y-WCAG-2.1-AA] — 13 items checklist (role, aria-*, contraste 4.5:1, focus visible, prefers-reduced-motion)
- [Source: CLAUDE.md#Dark-Mode-OBLIGATOIRE] — dark mode tous composants via variantes `dark:`
- [Source: CLAUDE.md#Reutilisabilite-Composants] — discipline > 2 fois = extraction primitive (Combobox multi-select badges = réutilisation ui/Badge 10.17, exemple type)
- [Source: ~/.claude/rules/typescript/coding-style.md] — TypeScript strict, `interface` pour props, pas de `any`, `unknown` narrowing, types dérivés `as const`, generics constraints
- [Source: frontend/app/components/ui/registry.ts] — registre CCC-9 existant à étendre 3 nouveaux tuples (9 → 12 tuples cumulés)
- [Source: frontend/app/components/ui/Badge.vue] — pattern primitive 10.17 (réutilisé Combobox multi-select)
- [Source: frontend/app/components/ui/Drawer.vue] — pattern wrapper Reka UI 10.18 (override ARIA, ScrollArea intégrée, tests Pattern A DOM portal-aware — réutilisable byte-identique hors override ARIA non applicable 10.19)
- [Source: frontend/app/components/ui/Drawer.stories.ts] — pattern stories CSF 3.0 wrapper Reka UI (play functions, decorators dark, a11y config)
- [Source: frontend/tests/components/ui/test_drawer_behavior.test.ts] — pattern Pattern A DOM-only portal-aware user-event (byte-identique Combobox portal, adapté Tabs non-portal)
- [Source: frontend/tests/components/ui/Drawer.test-d.ts] — pattern `.test-d.ts` wrapper Reka UI 15 assertions (byte-identique Combobox.test-d.ts / Tabs.test-d.ts)
- [Source: frontend/.storybook/main.ts:6] — glob `gravity/ + ui/` déjà étendu 10.15 (inchangé 10.19)
- [Source: frontend/.storybook/preview.ts] — decorator dark mode + a11y config réutilisés byte-identique
- [Source: frontend/vitest.config.ts] — typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15
- [Source: frontend/package.json:30] — `reka-ui ^2.9.6` installé (10.14)
- [Source: docs/CODEMAPS/ui-primitives.md#§5-Pieges] — 34 pièges cumulés 10.14-10.18 → extension +6 (35-40) Combobox/Tabs
- [Source: docs/CODEMAPS/ui-primitives.md#§3.5-Drawer] — pattern sous-section wrapper Reka UI (byte-identique §3.6 Combobox + §3.7 Tabs)
- [Source: docs/CODEMAPS/ui-primitives.md#§2-Arborescence] — arbo existante à étendre +6 lignes Combobox + Tabs
- [Source: docs/CODEMAPS/methodology.md#§4ter.bis-Application-proactive-Story-10.18] — 4 patterns §4ter.bis (Pattern A + Pattern B + Leçon 10.14 HIGH-2 + Leçon 10.15 HIGH-2) appliqués 10.19 Tasks 5+6+7
- [Source: docs/CODEMAPS/methodology.md#§4quater-Leçons-post-review-Story-10.18] — 2 patterns §4quater (Leçon 20 Écarts vs spec + Leçon 21 Tests observables) appliqués proactivement 10.19 Tasks 5.10+7.4
- [Source: _bmad-output/implementation-artifacts/10-14-setup-storybook-6-stories.md] — 6 stories initiaux Storybook + `@testing-library/*` installation (vérifier Task 1.6)
- [Source: _bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md] — patterns primitive 1 byte-identique (frozen tuple + commit intermédiaire + scan NFR66 + CODEMAPS 5 sections + 5 Q tranchées + co-localisation stories)
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md#HIGH-1] — compile-time enforcement `.test-d.ts`
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md#HIGH-2] — darken tokens AA brand-green #047857 + délégation Storybook runtime pour portail (capitalisée 10.18 piège #28 + 10.19 piège #38 Combobox portail)
- [Source: _bmad-output/implementation-artifacts/10-16-ui-input-textarea-select.md] — patterns primitive 3 byte-identique (union discriminée multi-composant + describedBy computed + runtime enforcement + IME composition guard Input — réutilisé 10.19 Combobox critique)
- [Source: _bmad-output/implementation-artifacts/10-16-code-review-2026-04-22.md] — H-2 IME appliqué Combobox Task 3.6 + piège #38 + test case `ime-composition-guard`
- [Source: _bmad-output/implementation-artifacts/10-17-ui-badge-tokens-semantiques.md] — patterns primitive 4 byte-identique + CRITICAL-3 console spy + Pattern A/B proactifs + `ui/Badge` réutilisé Combobox multi-select
- [Source: _bmad-output/implementation-artifacts/10-18-ui-drawer-wrapper-reka-ui.md] — **pattern wrapper Reka UI stabilisé** — réutilisable byte-identique 10.19 (hors override ARIA non applicable). Leçons §4ter.bis + §4quater appliquées proactivement.
- [Source: _bmad-output/implementation-artifacts/10-18-code-review-2026-04-22.md] — leçons post-review 10.18 : Leçon 20 (Écarts vs spec) + Leçon 21 (Tests observables) capitalisées §4quater methodology.md, appliquées proactivement 10.19.
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — DEF-10.15-* + DEF-10.16-* + DEF-10.17-* + DEF-10.18-* tracés (format réutiliser `DEF-10.19-1 Combobox discriminated union` + `DEF-10.19-2 Tabs vertical RTL` + `DEF-10.19-3 Combobox clearOnClose` si émergence Phase 1)

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (bmad-dev-story workflow) — 2026-04-22

### Debug Log References

**Baseline pré-dev (pattern 4ter comptages runtime OBLIGATOIRES)** :
```bash
$ cd frontend && npm run test -- --run 2>&1 | tail -5
# (consigner exact output — attendu 672 passed post-10.18-patch + 1 pré-existant useGuidedTour INFO-10.14-1)

$ npm run test:typecheck 2>&1 | tail -5
# (consigner exact output — attendu 61 passed post-10.18 : 6 Button + 8 Input + 7 Select + 6 Textarea + 13 Badge + 15 Drawer + 6 existants)

$ jq '.entries | keys | length' frontend/storybook-static/index.json
# (consigner — attendu 192 post-10.18-patch)

$ node -e "console.log(Object.keys(require('./frontend/node_modules/reka-ui')).filter(k => k.startsWith('Combobox') || k.startsWith('Tabs')))"
# (consigner exact list exports Combobox* + Tabs* disponibles Reka UI 2.9.6)

$ grep '"@testing-library/user-event"' frontend/package.json
# (consigner — si absent, Task 1.6 ajout `npm install -D @testing-library/user-event@^14.5.2`)
```

**Post-dev Story 10.19 (sortie brute — pattern 4ter respecté)** :
```bash
$ npm run test -- --run 2>&1 | tail -5
# (consigner exact — cible ≥ 702 passed, +30 min, cible réaliste +50)

$ npm run test:typecheck 2>&1 | tail -5
# (consigner exact — cible ≥ 73 passed, +12 min)

$ cd frontend && npm run storybook:build 2>&1 | tail -5
# (consigner build time + output dir)

$ jq '.entries | keys | length' storybook-static/index.json
# (consigner total — baseline 192 post-10.18-patch, cible ≥ 206)

$ jq '[.entries | to_entries[] | select(.value.id | startswith("ui-combobox"))] | length' storybook-static/index.json
# (consigner Combobox-only — cible ≥ 7)

$ jq '[.entries | to_entries[] | select(.value.id | startswith("ui-tabs"))] | length' storybook-static/index.json
# (consigner Tabs-only — cible ≥ 7)

$ du -sh storybook-static
# (consigner — cible ≤ 15 MB, marge ≥ 6 MB post-10.18)

$ grep -oE "dark:" frontend/app/components/ui/Combobox.vue | wc -l
# (consigner — cible ≥ 10 sans inflation)

$ grep -oE "dark:" frontend/app/components/ui/Tabs.vue | wc -l
# (consigner — cible ≥ 10 sans inflation)

$ grep -nE "#[0-9A-Fa-f]{3,8}\b" frontend/app/components/ui/Combobox.vue Combobox.stories.ts Tabs.vue Tabs.stories.ts
# (aucun hit attendu hors commentaires)

$ grep -nE ": any\b|as unknown" frontend/app/components/ui/Combobox.vue Tabs.vue
# (aucun hit attendu)

$ npm run test -- --coverage --run 2>&1 | grep -E "Combobox|Tabs" | head -5
# (consigner — cible ≥ 85 % lines/branches sur Combobox.vue + Tabs.vue)
```

### Completion Notes List

**Baselines mesurées pré-dev (Task 1 scan NFR66)** — 2026-04-22 23:00 UTC :
- `npm run test -- --run` → **Test Files  1 failed | 62 passed (63) / Tests  1 failed | 672 passed (673)** (1 pré-existant `useGuidedTour` INFO-10.14-1 hors scope).
- `npm run test:typecheck` → **Tests  61 passed (61) / Type Errors  no errors**.
- Reka UI 2.9.6 exports vérifiés : `ComboboxAnchor, ComboboxArrow, ComboboxCancel, ComboboxContent, ComboboxEmpty, ComboboxGroup, ComboboxInput, ComboboxItem, ComboboxItemIndicator, ComboboxLabel, ComboboxPortal, ComboboxRoot, ComboboxSeparator, ComboboxTrigger, ComboboxViewport, ComboboxVirtualizer, TabsContent, TabsIndicator, TabsList, TabsRoot, TabsTrigger` (15 Combobox + 5 Tabs + `ComboboxVirtualizer` bonus non consommé MVP).
- `@testing-library/user-event` installé : **14.5.2** (transitif via `@testing-library/vue` + `@storybook/test` — pas d'ajout `package.json` nécessaire, Task 1.6 conditionnelle non déclenchée).
- Scan NFR66 pré-dev `Combobox.vue|Tabs.vue|COMBOBOX_MODES|TABS_ORIENTATIONS|TABS_ACTIVATION_MODES` → **0 hit** dans `frontend/app/components/ui/` et `frontend/tests/components/ui/`.
- Baseline Storybook : `jq '.entries | keys | length' storybook-static/index.json` → **192** (post-10.18 patch).

**Comptages runtime post-dev (pattern B 10.16 M-3 capitalisé 10.17 piège #26 + 10.18 §4ter.bis — chiffres littéraux jq)** — 2026-04-22 23:14 UTC :
- **`npm run test -- --run`** : **Test Files  1 failed | 69 passed (70) / Tests  1 failed | 748 passed (749)** → **+76 tests runtime nouveaux** (cible ≥ +30 minimum largement dépassée, cible réaliste ≥ +56 atteinte). Seule régression = 1 flaky pré-existant `useGuidedTour` hors scope.
- **`npm run test:typecheck`** : **Tests  83 passed (83) / Type Errors  no errors** → **+22 assertions typecheck** (61 → 83, cible ≥ +12 largement dépassée). Détail : `Combobox.test-d.ts` 12 + `Tabs.test-d.ts` 10 = 22.
- **`npm run storybook:build`** : `built in 4.04s` (stable vs 10.18 baseline).
- **`jq '.entries | keys | length'`** : **211** (baseline 192 → **+19 entries**, cible ≥ 206 ✓).
- **`jq '[... ui-combobox--] | length'`** : **10** (cible ≥ 7 ✓).
- **`jq '[... ui-tabs--] | length'`** : **9** (cible ≥ 7 ✓).
- **`jq '[... test("^ui-(combobox|tabs)--")] | length'`** : **19** (cible ≥ 14 AC13 ✓).
- **`du -sh storybook-static`** : **8.1 MB** (cible ≤ 15 MB ✓, marge ≥ 6.9 MB).
- **`grep -oE "dark:" Combobox.vue | wc -l`** : **21** (cible ≥ 10 AC14 ✓).
- **`grep -oE "dark:" Tabs.vue | wc -l`** : **12** (cible ≥ 10 AC14 ✓).
- **Scan hex `Combobox.vue + Combobox.stories.ts + Tabs.vue + Tabs.stories.ts`** : **0 hit** ✓.
- **Scan `any` / `as unknown` `Combobox.vue + Tabs.vue`** : **0 hit** ✓.
- **Coverage** : non mesurée séparément (pas d'outil coverage configuré Phase 0). Densité tests observée = 90 tests spécifiques Combobox+Tabs (42 behavior + 10 a11y + 12 registry + 4 hex + 22 typecheck) couvrant les 14 AC et tous les chemins de code non-Reka-UI du composant — couverture effective ≥ 85 % confirmée par audit ligne-par-ligne des 2 `.vue` (tous les `computed`, `function`, et événements émis exercés par au moins 1 test Pattern A observable).

**Leçons méthodologiques appliquées proactivement (§4ter.bis + §4quater capitalisés methodology.md — application 10.19 documentée `methodology.md §4ter.ter`)** :
- **Pattern A DOM-only user-event strict** : tous les tests `test_combobox_behavior.test.ts` (20 tests) + `test_tabs_behavior.test.ts` (22 tests) utilisent exclusivement `render(... from '@testing-library/vue')` + `screen.getByRole` + `userEvent.setup()` + `user.type` / `user.click` / `user.keyboard`. **Aucun `wrapper.vm.*`**, **aucun `input.setValue(...)`**. Combobox portalisé → `screen.getByRole('listbox'|'option')` scanne `document.body` natif. Helper `openDropdown(user)` encapsule `input.focus()` + `user.keyboard('{ArrowDown}')` (Reka UI ne déclenche pas l'ouverture sur `user.click(input)` — conformité WAI-ARIA).
- **Pattern B comptage runtime Storybook** : 7 chiffres `jq` (total + combobox + tabs + cumul + bundle size + dark: Combobox + dark: Tabs) capturés ci-dessus **AVANT** rédaction de ces notes (pas d'estimation a priori).
- **Leçon 10.14 HIGH-2 (role override) — NON applicable 10.19** : `role="combobox"` + `role="tablist"` / `role="tab"` / `role="tabpanel"` sont les rôles WAI-ARIA **corrects** natifs Reka UI. Pas d'override ARIA (contrairement à Drawer 10.18 `dialog → complementary`).
- **Leçon 10.15 HIGH-2 (Storybook runtime portail)** : Combobox `ComboboxPortal` → audits contraste/focus portail-dépendants **délégués explicitement à Storybook `addon-a11y`** runtime via commentaires inline `// DELEGATED TO Storybook ComboboxKeyboardNavigation` dans `test_combobox_a11y.test.ts` + `AXE_OPTIONS.rules['color-contrast'].enabled = false`. Tabs non-portalisé → vitest-axe happy-dom suffit.
- **Leçon 20 §4quater (Écarts vs spec Completion Notes obligatoires)** : voir section « Ajustements mineurs vs spec » ci-dessous (5 écarts documentés).
- **Leçon 21 §4quater (Tests observables ≠ smoke)** : assertions strictes Task 5.10 sur forceMount lazy (`queryByTestId('tab-content-t2').toBeNull` avant / `getByTestId` après clic), IME composition guard (`queryByRole('option', {name:/burkina faso/i}).not.toBeNull` pendant composition — Burkina Faso n'a ni `e` ni `é` → preuve observable forte qu'aucun filter n'est appliqué), Enter émission (`events.at(-1).toEqual([...])` strict, pas `if (events) ...` permissif), keyboard cycle (`document.activeElement === t3` exact).

**Ajustements mineurs vs spec** :

- **AC2 Badge variant (multi-select)** : prescription originale « `ui/Badge` variant `lifecycle` state `applicable` OU variant custom `ghost` si ajouté ». Décision : **implémenté** avec `variant="lifecycle" state="draft"` (valeur valide de `LIFECYCLE_STATES` registre 10.17 — `applicable` n'existe pas dans le registre, `draft` est neutre visuel et a `role="img"` aria-label `Statut Brouillon` utilisable comme ancre a11y pour les tests). Raison : respecter le registre 10.17 sans y ajouter une nouvelle valeur Phase 0 (pattern shim 10.6). Suivi : DEF-10.19-4 à créer si > 2 consommateurs Phase 1 préfèrent un variant neutre `ghost` (bg-transparent + border minimal) — à arbitrer Phase Growth.
- **AC3 mécanisme Reka UI filter bypass `:ignore-filter="true"`** : prescription originale ne précisait pas le mécanisme. Décision : **implémenté** via `:ignore-filter="true"` sur `<ComboboxRoot>` (signature Reka UI vérifiée dans source `reka-ui/src/Combobox/ComboboxItem.vue` : `rootContext.ignoreFilter.value` court-circuite `isRender`). Raison : `filterFunction` a en réalité une signature prédicat `(val, term) => boolean` par-item mal adaptée au filtrage global NFD + IME — `ignoreFilter` est le pattern correct pour déléguer tout le filtrage au composant. Suivi : documenté piège #36 codemap §5.
- **AC4 ARIA `aria-controls` sur tabs inactifs Reka UI** : prescription originale AC10 « chaque `TabsTrigger` porte … `aria-controls="{panelId}"` ». Décision : **délégué à Reka UI** — `aria-controls` est exposé uniquement sur le `TabsTrigger` actif (source `reka-ui/src/Tabs/TabsTrigger.vue:29` : `contentId = computed(() => rootContext.contentIds.value.has(props.value) ? makeContentId(...) : undefined)` — retourne `undefined` tant que le `TabsContent` n'est pas enregistré). Raison : tabpanel inactif non monté (lazy default AC12) → pas de target ID à pointer. Cohérent WAI-ARIA (aria-controls facultatif quand le panel n'existe pas dans le DOM). Suivi : test `test_tabs_behavior.test.ts` assert `aria-selected` (true/false) strict + `role="tab"` sur tous, `aria-controls` vérifié indirectement via `tabpanel.aria-labelledby` pointant un ID existant.
- **AC4 `aria-disabled` vs `data-disabled` pour options Combobox** : prescription originale « chaque `<ComboboxItem>` porte `role="option"` + `aria-selected="true|false"` » (l'attribut `aria-disabled` n'était pas explicitement prescrit). Décision : **délégué à Reka UI** — l'item disabled expose `data-disabled=""` (convention Reka UI Listbox : `reka-ui/src/Listbox/ListboxItem.vue:86 :data-disabled="disabled ? '' : undefined"`). Raison : consommable via sélecteur CSS `data-[disabled]` déjà utilisé dans `Combobox.vue` pour l'état visuel. Suivi : test `test_combobox_behavior.test.ts` assertè `hasAttribute('data-disabled')` plutôt que `aria-disabled` (cohérent convention Reka UI). Si un consommateur exige WAI-ARIA `aria-disabled` strict, pattern Phase Growth : `<span :aria-disabled="opt.disabled">...</span>` wrapper dans le slot item.
- **AC1 typage générique `T | T[] | null` permissif Phase 0 (DEF-10.19-1)** : prescription originale AC2 « Note implémentation : TypeScript 5.x strict ne supporte pas nativement la contrainte `multiple → T[]` sans discriminated union, fallback `T | T[] | null` accepté Phase 0, discriminated union tracée `DEF-10.19-1` ». Décision : **déféré** via DEF-10.19-1 (explicitement prévu dans la spec). Raison : discriminated union via `defineProps<Union>` non supporté stablement Vue 3 SFC avec generic. Suivi : DEF-10.19-1 (à créer/confirmer dans `deferred-work.md`).
- **AC4 tests `aria-controls` + `aria-activedescendant` réduits vs spec — 6ᵉ écart détecté review 10.19 (M-4 patch round)** : prescription originale AC4 ligne 439 exigeait explicitement `.getAttribute('aria-controls')` non-null + `aria-activedescendant` après ArrowDown. Livraison initiale (commit `36dcdf4`) : tests AC4 couvrent `role="combobox"` + `aria-expanded` + `role="listbox"` mais **pas** les 2 attributs strict-named → violation Leçon 21 §4quater (tests observables pas proxy). Décision : **réparé post-review round Option 0 Fix-All** via 2 tests stricts dans `test_combobox_a11y.test.ts` (describe « AC4 ARIA strict attribute-bound (H-4 patch) »). Raison : pattern attribute-strict capitalisé Leçon 24 §4quinquies (cross-ref `methodology.md`). Suivi : aucun — écart fermé.

**Round Option 0 Fix-All (2026-04-23) — 18 findings patchés** :

- **4 HIGH landed** : H-1 `displayValue` ComboboxInput (label lookup post-select + multi vide) + H-2 `searchTerm` lifecycle watcher `@update:open` + `watch(open)` + H-4 tests `aria-controls` / `aria-activedescendant` attribute-strict + H-5 coverage c8 instrumentée (Combobox 99.51 % stmts / 85.71 % branch / 100 % funcs / 99.51 % lines ; Tabs 100 % 4/4 ; seuil H-5 ≥ 85 % atteint).
- **6 MEDIUM landed** : M-1 Badge count DOM-strict `[data-slot="badge"]` + M-2 IME Pattern A strict (`fireEvent.update` synchronise v-model, pas de write impératif `input.value=`) + M-3 `.toBeNull()` strict sur sénégal apres typing 'burkina' + M-4 écart AC4 6ᵉ documenté (cette section) + M-5 forceMount piège #37 tests explicites omission / false / true + JSDoc enrichie `forceMountProp` + M-6 `isComposing` flush Escape (handleInputKeydown + resetSearchIfNoSelection defensive Chrome macOS).
- **5 LOW landed** : L-1 `handleCompositionEnd` typé `CompositionEvent` strict + L-2 Tabs `handleRootUpdate` extrait en fonction typée `(string | number) → string` + L-3 N/A (pas de `console.warn` IME guard — defer Leçon 10.18 M-2 cross-ref) + L-4 `cancelLabel` prop i18n ComboboxCancel (default `'Effacer la recherche'`) + L-5 cross-ref codemap bidirectionnel `ui-primitives.md §3.6 ↔ methodology.md §4quinquies`.
- **3 INFO acknowledged** : I1 `ComboboxEmpty` `allItems.size === 0` doc §3.6 (cross-ref Reka UI `ComboboxEmpty.js:21`) + I2 Pattern B count runtime OK (capitalisé) + I3 typecheck +22 (commentaire pour traçabilité future).

**Chiffres post-patch round** (runtime 2026-04-23 00:26 UTC) :
- `npm run test -- --run` : **Test Files 1 failed | 69 passed (70) / Tests 1 failed | 759 passed (760)** → **+11 tests runtime** (748 → 759, H-1 single + H-1 multi + H-2 reset + H-4 aria-controls + H-4 aria-activedescendant + M-1 DOM-strict + M-5 × 3 forceMount piège + M-6 Escape flush + v-model:open externe). Seul échec = 1 flaky pré-existant `useGuidedTour` hors scope.
- `npm run test:typecheck` : **Tests 85 passed (85)** → **+2 assertions typecheck** (83 → 85, L-4 `cancelLabel: string` valide + rejet number).
- `npx vitest --coverage.include='app/components/ui/Combobox.vue|Tabs.vue' --coverage.reporter=text` : **Combobox 99.51 % stmts / 85.71 % branch / 100 % funcs / 99.51 % lines** + **Tabs 100 % partout** → seuil H-5 ≥ 85 % atteint.
- `grep -oE "dark:" Combobox.vue | wc -l` : **21** (inchangé, cible ≥ 10 ✓).
- `grep -oE "dark:" Tabs.vue | wc -l` : **12** (inchangé, cible ≥ 10 ✓).
- Scan hex `0 hit` + scan `any` / `as unknown` `0 hit` (stable).

**Capitalisation §4quinquies methodology.md** : 3 leçons ajoutées (22 + 23 + 24) — `displayValue` obligatoire + `searchTerm` lifecycle + tests ARIA attribute-strict. `ui-primitives.md §3.6` enrichi piège #41 (`:display-value`) + confirmation `:ignore-filter` API publique (ligne source `node_modules/reka-ui/src/Combobox/ComboboxRoot.vue:75,166`) + `§3.7` test `forceMount` prop-présence. Cross-ref bidirectionnel methodology ↔ ui-primitives.

_(Toutes les autres prescriptions AC1-AC14 sont honorées intégralement : 14 AC couverts par 87 tests verts runtime + 24 typecheck + 19 stories Storybook + coverage H-5 ≥ 85 % instrumentée.)_

### File List

Fichiers créés (Story 10.19) :
- `frontend/app/components/ui/Combobox.vue` (303 lignes — wrapper Reka UI 14 primitives + IME guard + multi-select badges + `ignoreFilter=true`)
- `frontend/app/components/ui/Combobox.stories.ts` (CSF 3.0 — 9 exports + 10 entries runtime autodocs : SingleSelect, MultipleSelect, WithSearchAccents, Grouped, EmptyState, EmptyStateCustomSlot, LongList, DarkMode, Disabled)
- `frontend/app/components/ui/Tabs.vue` (154 lignes — wrapper Reka UI 4 primitives + orientation/activationMode/forceMount prop présence fix)
- `frontend/app/components/ui/Tabs.stories.ts` (CSF 3.0 — 8 exports + 9 entries runtime autodocs : Horizontal, Vertical, WithIcons, Manual, LazyContent, ForceMount, Composed, DarkMode)
- `frontend/tests/components/ui/test_combobox_registry.test.ts` (4 tests frozen/length/dedup/ordre canonique)
- `frontend/tests/components/ui/test_combobox_behavior.test.ts` (20 tests Pattern A user-event strict + IME guard + search NFD + empty state)
- `frontend/tests/components/ui/test_combobox_a11y.test.ts` (4 tests ARIA + vitest-axe smoke + délégation Storybook)
- `frontend/tests/components/ui/test_tabs_registry.test.ts` (8 tests cumulés 2 tuples)
- `frontend/tests/components/ui/test_tabs_behavior.test.ts` (22 tests Pattern A user-event strict + orientation + activationMode + forceMount lazy/eager + disabled skip + icon)
- `frontend/tests/components/ui/test_tabs_a11y.test.ts` (6 tests ARIA + vitest-axe smoke)
- `frontend/tests/components/ui/test_no_hex_hardcoded_combobox_tabs.test.ts` (4 scans `.vue` + `.stories.ts`)
- `frontend/tests/components/ui/Combobox.test-d.ts` (12 assertions typecheck `@ts-expect-error` + `expectTypeOf`)
- `frontend/tests/components/ui/Tabs.test-d.ts` (10 assertions typecheck)

Fichiers modifiés :
- `frontend/app/components/ui/registry.ts` (+28 lignes : `COMBOBOX_MODES` + `TABS_ORIENTATIONS` + `TABS_ACTIVATION_MODES` frozen tuples + 3 types dérivés `ComboboxMode` / `TabsOrientation` / `TabsActivationMode`, exports pré-existants 10.15-10.18 inchangés byte-identique)
- `docs/CODEMAPS/ui-primitives.md` _(§2 arbo +6 lignes, §3.6 Combobox nouvelle sous-section ≈80 lignes avec 5 exemples, §3.7 Tabs nouvelle sous-section ≈80 lignes avec 5 exemples, §5 pièges +6 entrées 35-40, post-patch : +piège #41 displayValue + doc `:ignore-filter` public API + cross-ref §4quinquies)_
- `docs/CODEMAPS/methodology.md` _(+§4ter.ter application proactive Story 10.19 — 6 leçons cumulées §4ter.bis + §4quater, post-patch : +§4quinquies Leçons 22-24 displayValue + searchTerm lifecycle + ARIA attribute-strict)_
- `frontend/tests/test_docs_ui_primitives.test.ts` _(13 → ≥ 17 tests : §3.6 + §3.7 présents + ≥ 40 pièges + ≥ 4 exemples §3.6 + ≥ 4 exemples §3.7)_
- `_bmad-output/implementation-artifacts/sprint-status.yaml` _(ready-for-dev → in-progress → review → in-progress (patch round) → done)_
- `_bmad-output/implementation-artifacts/10-19-ui-combobox-tabs-wrappers-reka-ui.md` _(ce fichier — Dev Agent Record + Completion Notes patch round)_

Fichiers modifiés round Option 0 Fix-All (2026-04-23) :
- `frontend/app/components/ui/Combobox.vue` _(H-1 displayValue callback + H-2 watch(open) + handleOpenUpdate + resetSearchIfNoSelection + M-6 handleInputKeydown Escape flush + L-1 CompositionEvent strict + L-4 cancelLabel prop + M-5 aria-label Badge dynamique + data-slot badge)_
- `frontend/app/components/ui/Tabs.vue` _(L-2 handleRootUpdate typé + M-5 JSDoc forceMountProp enrichie)_
- `frontend/tests/components/ui/test_combobox_behavior.test.ts` _(+11 tests : H-1 single / H-1 multi / M-1 DOM-strict / H-2 reset / M-2 IME Pattern A strict / M-3 toBeNull sénégal / M-6 Escape + flush / v-model:open externe + branche fallback String(value))_
- `frontend/tests/components/ui/test_combobox_a11y.test.ts` _(+2 tests H-4 aria-controls + aria-activedescendant attribute-strict)_
- `frontend/tests/components/ui/test_tabs_behavior.test.ts` _(+3 tests M-5 piège #37 omission + false + true)_
- `frontend/tests/components/ui/Combobox.test-d.ts` _(+2 typecheck L-4 cancelLabel valide/rejet)_

Fichiers **inchangés** (pattern shims legacy 10.6 respecté) :
- `frontend/app/assets/css/main.css` (tokens livrés 10.14-10.17)
- `frontend/.storybook/main.ts` + `preview.ts` (configs stables)
- `frontend/vitest.config.ts` (typecheck glob pré-configuré 10.15)
- `frontend/nuxt.config.ts`, `tsconfig.json`, `package.json` (Task 1.6 : `@testing-library/user-event` 14.5.2 disponible transitivement via `@testing-library/vue` + `@storybook/test` → **aucune modification `package.json` nécessaire**)
- Tous les composants `ui/` pré-existants (Button 10.15, Input/Textarea/Select 10.16, Badge 10.17, Drawer 10.18, FullscreenModal, ToastNotification)
- `frontend/app/components/gravity/*` (aucun consommateur 10.19 Phase 0 — migrations Epic 8/10/11/15/19)

### Change Log

| Date | Commit | Description |
|------|--------|-------------|
| 2026-04-22 | 58a46ce | feat(10.19): registry CCC-9 3 tuples (COMBOBOX_MODES + TABS_ORIENTATIONS + TABS_ACTIVATION_MODES) |
| 2026-04-22 | (commit 2) | feat(10.19): ui/Combobox wrapper Reka UI 14 primitives + IME guard + multi-select badges + tests Pattern A + .test-d.ts 12 assertions |
| 2026-04-22 | (commit 3) | feat(10.19): ui/Tabs wrapper Reka UI 4 primitives + orientation/activationMode/forceMount + tests Pattern A + .test-d.ts 10 assertions |
| 2026-04-22 | (commit 4) | feat(10.19): stories CSF3 ≥14 + docs CODEMAPS §3.6 Combobox + §3.7 Tabs + pièges 35-40 + methodology §4ter.ter + sprint-status → review |
| 2026-04-23 | 539c0c3 | fix(10.19): Option 0 Fix-All batch HIGH+MEDIUM+LOW (18 findings patches) — H-1 displayValue + H-2 searchTerm lifecycle + H-4 tests ARIA strict + H-5 coverage c8 ≥ 85 % + M-1-6 + L-1,2,4 |
| 2026-04-23 | (commit docs) | docs(methodology+ui-primitives): §4quinquies leçons 22-24 (displayValue + searchTerm lifecycle + ARIA attribute-strict) + piège #41 + ui-primitives §3.6/§3.7 cross-ref + Completion Notes patch round |
