# Story 10.21 : Setup Lucide + dossier icônes ESG custom + `ui/EsgIcon.vue` wrapper

Status: ready-for-dev

<!-- Note: Validation optionnelle. Exécuter `validate-create-story` pour un contrôle qualité avant `dev-story`. -->

> **Contexte** : 23ᵉ et **DERNIÈRE story Phase 0 Epic 10** — clôture des Fondations. 8ᵉ primitive `ui/` (après Button 10.15 + Input/Textarea/Select 10.16 + Badge 10.17 + Drawer 10.18 + Combobox/Tabs 10.19 + DatePicker 10.20) + **système iconographique projet unifié**. Sizing **S** (~45 min — 1 h) : pas de wrapper Reka UI (Lucide direct), pattern CCC-9 registry maîtrisé, migration mécanique shim pattern 10.6 rodée.
>
> Cette story livre **3 livrables atomiques** dans `frontend/app/` :
> 1. **Setup `lucide-vue-next` ^0.400+** en dépendance runtime tree-shakeable (named imports individuels, jamais `import * as`).
> 2. **Composant `ui/EsgIcon.vue`** — wrapper props-typé `<EsgIcon name="chevron-down" size="md" variant="default" />` avec registry frozen mapping `name → composant Lucide OU SVG custom`.
> 3. **≥ 6 SVG custom ESG métier** dans `frontend/app/assets/icons/esg/` (effluents, biodiversité, audit-social, mobile-money, taxonomie-uemoa, sges-beta-seal) + migration mécanique **≥ 15 SVG inline** des primitives 10.15-10.20 vers `<EsgIcon />`.
>
> **Signification spéciale** : Story 10.21 **clôt Epic 10 Phase 0 Fondations** (23 stories ≈ 6 semaines effort effectif vs 18 semaines sprint v1 → économie 12 semaines confirmée sprint v2). Déclenche transition **Epic 11 Phase 1 MVP Cluster A PME** (11.1-11.8). Retrospective Epic 10 recommandée à la Completion (méthodologie §4ter.bis→§4sexies capitalisée, pattern wrapper Reka UI byte-identique stabilisé, registry CCC-9 étendu 6 fois, 27 leçons cumulées, vélocité mesurée 60-75 % estimate L + 20-50 % estimate M).
>
> **État de départ — 7 primitives `ui/` livrées + 4 wrappers Reka UI + 27 leçons capitalisées** :
> - ✅ **Reka UI `^2.9.6`** (Story 10.14 · `frontend/package.json:30`) — 4 wrappers landed (Drawer 10.18, Combobox/Tabs 10.19, DatePicker 10.20). Pattern stabilisé byte-identique (5ᵉ itération = wrapper Lucide ne suit PAS le pattern Reka UI — Lucide expose des composants Vue directement, pas des primitives headless à composer).
> - ✅ **Tokens `@theme` livrés 10.14-10.17** — `brand-green #047857` AA post-darken + `brand-red #DC2626` AA + `surface-*`, `dark-*`. **Aucune modification `main.css` nécessaire**. Les variants `EsgIcon` consomment CSS `currentColor` Lucide natif + classes Tailwind `text-*` résolvant tokens `@theme`.
> - ✅ **Pattern CCC-9 frozen tuple** (10.8 + 10.14-10.20) — `registry.ts` déjà étendu 6 fois. Extension byte-identique **3 frozen tuples** : `ICON_SIZES`, `ICON_VARIANTS`, `ESG_ICON_NAMES` (registry exhaustif ≥ 30 entrées).
> - ✅ **Pattern compile-time enforcement `.test-d.ts`** (10.15 HIGH-1) — `vitest.config.ts typecheck.include: ['tests/**/*.test-d.ts']` actif. Baseline post-10.20 **≥ 99 assertions** (6 Button + 8 Input + 7 Select + 6 Textarea + 13 Badge + 15 Drawer + 6 Combobox + 6 Tabs + 6 DatePicker + 10 patches Option 0 + 16 historiques). Cible `EsgIcon.test-d.ts` ≥ 8 assertions.
> - ✅ **Pattern A DOM-only observable** (§4ter.bis + §4quinquies) — **PARTIELLEMENT APPLICABLE** : les icônes ne sont pas interactives (pas de `user-event` user-click sur pixel SVG). Les tests `test_esgicon_behavior.test.ts` utilisent :
>   - `screen.getByRole('img', {name: /calendar/i})` observable pour mode sémantique (prop `decorative={false}` AC7),
>   - `document.querySelector('[aria-hidden="true"] svg')` + `toHaveAttribute('aria-hidden','true')` pour mode décoratif (AC7),
>   - Rendering byte-identique assertions `expect(wrapper.html()).toContain('<svg')` + `expect(wrapper.find('svg').attributes('class')).toContain('text-brand-green')`.
>   - **Pas de `wrapper.vm.*`** ni `setValue` (Pattern A enforced strict).
> - ✅ **Pattern B comptage runtime Storybook** (§4ter.bis piège #26 10.17 + L22-23 §4quinquies 10.19 + L26 §4sexies 10.20) — `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-esgicon"))] | length' storybook-static/index.json` **OBLIGATOIRE AVANT Completion Notes**. Coverage **instrumentée c8** (H-5 10.19 post-review) ≥ 85 % lines/branches/functions/statements sur `EsgIcon.vue`.
> - ✅ **Pattern leçons §4sexies 10.20 (post-Option 0 Fix-All)** :
>   - **L25 — Wrapper Reka UI id custom = code mort** : N/A direct (EsgIcon n'est PAS un wrapper Reka UI slot-forwarded). **Principe généralisable** appliqué : `EsgIcon` ne doit PAS injecter de props dupliquant les props natives Lucide (`size`, `color`, `strokeWidth`). Les props Lucide natives sont forward-passed directement via `v-bind="$attrs"` OU via une allowlist stricte (pas de double-déclaration). Piège #46 capitalisé ci-dessous.
>   - **L26 — Délégation per-path explicite pas globale** : appliquée aux tests `EsgIcon`. Chaque `name` du registry n'est PAS testé individuellement dans Vitest (coût 30+ tests redondants) → **1 test paramétré** `describe.each(ESG_ICON_NAMES)('renders %s', ...)` + délégation visuelle story `UI/EsgIcon/Grid` (100+ icônes affichées) avec marker inline `// DELEGATED TO Storybook ui-esgicon--grid`.
>   - **L27 — Ordonnancement pièges cross-story continuité séquentielle** : scan `docs/CODEMAPS/ui-primitives.md` Task 1.1 → plus haut piège existant = **#45** (DatePicker range auto-swap 10.20). **Nouveaux pièges 10.21 = #46-#48** (pas #41+ comme parfois proposé par erreur). Test `test_docs_ui_primitives.test.ts` assert unicité + continuité `uniqueNumbers.size === matches.length` (pas seulement `length >= N`).
> - ✅ **Pattern leçons §4quinquies 10.19** :
>   - **L22 — displayValue trigger** : N/A (pas de trigger popover).
>   - **L23 — lifecycle close reset state** : N/A (pas de state interne).
>   - **L24 — ARIA attribute-strict pas proxy** : **DIRECTEMENT APPLICABLE** à l'AC7. Asserter `role="img"` + `aria-label={name}` **valeurs strictes** (pas `toHaveAttribute('role')` sans 2ᵉ arg) OU `aria-hidden="true"` strict (pas `aria-hidden=""` string vide qui passerait laxiste). Test observable L24 fixtures AC7.
> - ✅ **Pattern leçons §4quater 10.18** :
>   - **L20 — Écarts vs spec = Completion Notes obligatoires** : Task 7.4 appliquée proactivement. Si bundle size > 50 KB (AC3), documenter l'écart avec mesure exacte + décision (accepté / deferred / icônes retirées).
>   - **L21 — Tests observables ≠ smoke d'existence** : `expect(wrapper.find('svg').exists()).toBe(true)` interdit → remplacer par `expect(wrapper.find('svg[aria-label="calendar"]').exists()).toBe(true)` (observable strict).
> - ⚠️ **Pattern wrapper Lucide — DIFFÉRENT du pattern wrapper Reka UI** : Lucide expose chaque icône comme **composant Vue `.ts` pré-compilé** (`import { ChevronDown } from 'lucide-vue-next'` → `<ChevronDown />` utilisable directement). EsgIcon **n'est PAS un wrapper headless à composer** — c'est un **dispatcher par registry** : `<EsgIcon name="chevron-down" />` résout le nom vers le bon composant Lucide OU le bon SVG custom via `<component :is="resolved">`. Cohérence API : props `size`, `color`, `strokeWidth` forward-passed transparents vers Lucide natif (L25 généralisée).
> - ⚠️ **Pattern tree-shaking Lucide — CRITIQUE bundle size** : `import { ChevronDown, X, Calendar } from 'lucide-vue-next'` (named imports individuels) → tree-shaking effectif ~1.5 KB/icône gzipped. `import * as Lucide from 'lucide-vue-next'` OU `import Lucide from 'lucide-vue-next'` → bundle de **1400+ icônes = ~500 KB+** non tree-shaké. Piège #47 capitalisé.
> - ❌ **Aucun `ui/EsgIcon.vue` préexistant** — `grep EsgIcon frontend/app/components/ui/` → 0 hit attendu. Aucun dossier `frontend/app/assets/icons/esg/` existant — création Task 4. `grep "lucide"` dans `frontend/package.json` → 0 hit (first install Task 1).
> - ❌ **SVG inline existants à migrer** — grep `<svg` dans `frontend/app/components/ui/*.vue` → **≥ 15 hits** (Combobox 5, DatePicker 5, Button 1, Drawer 1, Input 1, Select 2, Textarea 1, FullscreenModal 1). Migration mécanique Task 5 shim pattern 10.6 byte-identique visuellement.
> - ✅ **Pattern migration byte-identique (shim 10.6)** — remplacer `<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" stroke="currentColor"><polyline points="6 9 12 15 18 9" /></svg>` par `<EsgIcon name="chevron-down" class="h-4 w-4" decorative />` — viewBox + stroke + fill identiques (convention Lucide ≡ SVG inline projet), dimensions pilotées par parent via classes Tailwind (pas prop `size` numérique qui casserait le sizing existant par flex container). Documenté §3.9 CODEMAP.
> - ✅ **Dépendances downstream Phase 1+** : non bloquantes (10.21 livre l'infra, Epic 11+ consomment). FundApplicationLifecycleBadge Epic 9 + ComplianceBadge Epic 10 + ReferentialComparisonView Epic 10 + ProjectStatusPill Epic 11 utiliseront `<EsgIcon name="verdict-pass" />` + `<EsgIcon name="lifecycle-ready" />`.
> - ✅ **SVG custom convention Lucide** : `viewBox="0 0 24 24"`, `stroke="currentColor"`, `stroke-width="2"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"`. **Cohérence visuelle avec Lucide** : pas de SVG filled, pas de gradient, uniquement line-art monochrome `currentColor`. Permet dark mode natif via hérédité `text-*` parent.
>
> **Livrable 10.21 — Setup Lucide + EsgIcon wrapper + ≥ 6 SVG custom + migration mécanique ≥ 15 SVG inline (~1 h)** :
>
> 1. **Extension `ui/registry.ts`** (pattern CCC-9) — ajouter **3 frozen tuples** :
>    ```ts
>    export const ICON_SIZES = Object.freeze(['xs', 'sm', 'md', 'lg', 'xl'] as const);
>    export const ICON_VARIANTS = Object.freeze(['default', 'brand', 'danger', 'success', 'muted'] as const);
>    export const ESG_ICON_NAMES = Object.freeze([
>      // Lucide mappés (chrevrons/close/check/calendar/alert/status/action)
>      'chevron-down', 'chevron-up', 'chevron-left', 'chevron-right',
>      'check', 'x', 'calendar', 'clock',
>      'alert-circle', 'alert-triangle', 'info', 'check-circle', 'x-circle',
>      'loader', 'search', 'plus', 'minus', 'edit', 'trash',
>      'eye', 'eye-off', 'download', 'upload', 'file-text', 'link', 'external-link',
>      // ESG custom (SVG dans assets/icons/esg/)
>      'esg-effluents', 'esg-biodiversite', 'esg-audit-social',
>      'esg-mobile-money', 'esg-taxonomie-uemoa', 'esg-sges-beta-seal',
>    ] as const);
>    ```
>    Invariants : length **5 / 5 / ≥ 30** · `Object.isFrozen === true` · dédoublonné (`Set.size === length`) · type dérivé `typeof TUPLE[number]`.
>
> 2. **Composant `frontend/app/components/ui/EsgIcon.vue`** (AC4-AC7) — dispatcher par registry :
>    - **Props typées strictes** : `name: EsgIconName` (literal union ≥ 30) + `size?: IconSize` (default `md`) + `variant?: IconVariant` (default `default`) + `decorative?: boolean` (default `false`) + `strokeWidth?: number` (default `2`, forward Lucide) + `class?: string` (merge Tailwind).
>    - **Mapping name → composant** via `ICON_MAP` : `Record<EsgIconName, Component>` à l'intérieur du `<script setup>` :
>      ```ts
>      import { ChevronDown, ChevronUp, /* … */ Calendar } from 'lucide-vue-next';
>      import EsgEffluents from '~/assets/icons/esg/effluents.svg?component';
>      // … 6 SVG custom via ?component (Nuxt 4 SVG loader)
>      const ICON_MAP: Record<EsgIconName, Component> = {
>        'chevron-down': ChevronDown,
>        /* … */
>        'esg-effluents': EsgEffluents,
>      };
>      ```
>    - **Fallback warn dev-only** (L25 + AC5) : `computed` `resolvedComponent` → si `name` absent de `ICON_MAP`, `console.warn` en DEV (`import.meta.env.DEV`) + rendu placeholder `<svg>` cercle barré viewBox 0 0 24 24. Pas de crash runtime.
>    - **ARIA strict (L24 + AC7)** : template `<component :is="resolvedComponent" v-bind="ariaAttrs" :class="finalClass" :stroke-width="strokeWidth" :size="pixelSize" />`. `ariaAttrs` computed :
>      - Si `decorative === true` → `{ 'aria-hidden': 'true' }` (valeur string `'true'` stricte, pas boolean `true`).
>      - Si `decorative === false` → `{ role: 'img', 'aria-label': name }` (pas de mélange).
>    - **Mapping `size → pixelSize`** : `{ xs: 12, sm: 16, md: 20, lg: 24, xl: 32 }` (cohérent Tailwind h-3/h-4/h-5/h-6/h-8). `size` prop passed to Lucide natif `size={pixelSize}`.
>    - **Mapping `variant → Tailwind class`** : `{ default: 'text-current', brand: 'text-brand-green dark:text-brand-green', danger: 'text-brand-red dark:text-brand-red', success: 'text-verdict-pass dark:text-verdict-pass', muted: 'text-surface-text/60 dark:text-surface-dark-text/60' }`. Couleur via CSS `currentColor` Lucide natif (pas de hex inline).
>    - **Respect `prefers-reduced-motion: reduce`** : pas d'animation par défaut. Si `name === 'loader'`, rotation via `<style>` scoped `@keyframes spin` + `motion-reduce:animate-none`.
>    - **Aucun `any` / `as unknown`** : `Record<EsgIconName, Component>` strict.
>
> 3. **SVG custom ESG `frontend/app/assets/icons/esg/`** (AC8) — **≥ 6 fichiers** :
>    - `effluents.svg` — gouttes + filtre (ODD 6 eau propre).
>    - `biodiversite.svg` — feuille + insecte (ODD 15 vie terrestre).
>    - `audit-social.svg` — document + checkmark + personnage (audit social ESG).
>    - `mobile-money.svg` — smartphone + symbole FCFA (inclusion financière UEMOA).
>    - `taxonomie-uemoa.svg` — sigle UEMOA stylisé 24×24 (ou carte Afrique Ouest simplifiée).
>    - `sges-beta-seal.svg` — sceau SGES BETA (rond + texte « SGES β » centré).
>    - **Convention stricte** : `viewBox="0 0 24 24"`, `stroke="currentColor"`, `stroke-width="2"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"`. Optimisés via SVGO (pas de metadata, pas de xmlns duplication).
>
> 4. **`frontend/app/components/ui/EsgIcon.stories.ts` co-localisée** (AC10) — CSF 3.0 avec **≥ 12 stories** :
>    - `Grid` : affichage matriciel **TOUTES les icônes du registry** (≥ 30) via loop `v-for="name in ESG_ICON_NAMES"` → délégation test L26 visuelle complète.
>    - `Sizes` : toutes les 5 tailles (xs/sm/md/lg/xl) de `ChevronDown`.
>    - `Variants` : toutes les 5 variants (default/brand/danger/success/muted) de `Check`.
>    - `Decorative` : `<EsgIcon name="x" decorative />` (pas d'aria-label).
>    - `WithLabel` : `<EsgIcon name="calendar" :decorative="false" />` (role=img + aria-label).
>    - `DarkMode` : decorator `html.classList.add('dark')` + grid miroir.
>    - `MappingRegistry` : rendu tabulaire registry complet (nom → aperçu SVG → source Lucide/custom).
>    - `LucideOnly` : 20+ icônes Lucide whitelist mappées uniquement.
>    - `EsgCustomOnly` : 6 icônes ESG custom uniquement (effluents, biodiversité, audit-social, mobile-money, taxonomie-uemoa, sges-beta-seal).
>    - `UnknownNameFallback` : `<EsgIcon name="does-not-exist" />` → placeholder cercle barré + console.warn (DEV) — story démo intégration.
>    - `StrokeWidth` : `strokeWidth=1` vs `strokeWidth=2` vs `strokeWidth=3`.
>    - `Spinner` : `<EsgIcon name="loader" class="animate-spin" />` + `motion-reduce:animate-none`.
>    - (cible réaliste **≥ 14** avec autodocs 1 page).
>
> 5. **Tests Vitest `frontend/tests/components/ui/`** (AC10) — **5 fichiers** :
>    - `test_esgicon_registry.test.ts` : **6 tests** (3 tuples × `length` + `Object.isFrozen` + dédoublonnement + ordre canonique `ICON_SIZES[2] === 'md'` + `ICON_VARIANTS[0] === 'default'` + `ESG_ICON_NAMES` contient les 6 prefixes `esg-*`).
>    - `test_esgicon_behavior.test.ts` : **≥ 12 tests** Pattern A observable :
>      - Rendering Lucide : `<EsgIcon name="chevron-down" />` → `wrapper.find('svg').exists() === true` + `svg.innerHTML` contient `polyline` Lucide.
>      - Rendering ESG custom : `<EsgIcon name="esg-effluents" />` → SVG contient `viewBox="0 0 24 24"` + `stroke="currentColor"`.
>      - Size mapping : `size="xs"` → `svg.getAttribute('width') === '12'` + `height === '12'`.
>      - Variant classes : `variant="brand"` → `svg.getAttribute('class')` contient `text-brand-green`.
>      - StrokeWidth forward : `strokeWidth={3}` → `svg.getAttribute('stroke-width') === '3'`.
>      - Fallback unknown name : `<EsgIcon name="unknown-xyz" />` + `vi.spyOn(console, 'warn')` → warn appelé 1 fois avec message mentionnant le nom + placeholder rendu.
>      - Decorative true : `decorative={true}` → `aria-hidden="true"` strict + pas de `role` + pas de `aria-label`.
>      - Decorative false (default) : `role="img"` strict + `aria-label="calendar"` strict.
>      - Class merge : `<EsgIcon class="h-4 w-4 text-red-500" />` → class merged (pas écrasé par variant).
>    - `test_esgicon_a11y.test.ts` : **≥ 6 tests** ARIA strict (L24 §4quinquies) :
>      - `expect(icon.getAttribute('aria-hidden')).toBe('true')` (pas `toHaveAttribute('aria-hidden')` sans 2ᵉ arg).
>      - `expect(icon.getAttribute('role')).toBe('img')` strict.
>      - `expect(icon.getAttribute('aria-label')).toBe('calendar')` strict.
>      - vitest-axe `toHaveNoViolations()` sur 1 grid rendu minimal.
>      - Contraste AA post-darken variants brand/danger/success délégués `// DELEGATED TO Storybook ui-esgicon--dark-mode` (L26).
>    - `test_no_hex_hardcoded_esgicon.test.ts` : **2 tests** scan `EsgIcon.vue` + `EsgIcon.stories.ts` → **0 hit hex** (tokens uniquement).
>    - `EsgIcon.test-d.ts` : **≥ 8 `@ts-expect-error`** :
>      ```ts
>      // @ts-expect-error name hors registry
>      const a = h(EsgIcon, { name: 'does-not-exist' });
>      // @ts-expect-error size hors ICON_SIZES
>      const b = h(EsgIcon, { name: 'check', size: 'xxl' });
>      // @ts-expect-error variant hors ICON_VARIANTS
>      const c = h(EsgIcon, { name: 'check', variant: 'rainbow' });
>      // @ts-expect-error decorative string au lieu de boolean
>      const d = h(EsgIcon, { name: 'check', decorative: 'true' });
>      // @ts-expect-error strokeWidth string au lieu de number
>      const e = h(EsgIcon, { name: 'check', strokeWidth: '2' });
>      // @ts-expect-error name manquant (required)
>      const f = h(EsgIcon, {});
>      // @ts-expect-error name boolean
>      const g = h(EsgIcon, { name: true });
>      // @ts-expect-error class: number
>      const h2 = h(EsgIcon, { name: 'check', class: 123 });
>      ```
>
> 6. **Migration mécanique ≥ 15 SVG inline** (AC9) — shim pattern 10.6 byte-identique :
>    - Combobox.vue : 5 SVG (chevron-down trigger + X cancel + check option + search icon + clear) → 5 × `<EsgIcon name="..." class="h-4 w-4" decorative />`.
>    - DatePicker.vue : 5 SVG (calendar trigger + ← prev + → next + x clear + check selected) → 5 × `<EsgIcon />`.
>    - Button.vue : 1 SVG (loader spinner) → `<EsgIcon name="loader" class="h-4 w-4 animate-spin" decorative />`.
>    - Drawer.vue : 1 SVG (close X) → `<EsgIcon name="x" class="h-5 w-5" decorative />`.
>    - Input.vue : 1 SVG (clear X en mode search type) → `<EsgIcon name="x" />`.
>    - Select.vue : 2 SVG (chevron-down + check selected) → 2 × `<EsgIcon />`.
>    - Textarea.vue : 1 SVG (counter warning) → `<EsgIcon name="alert-circle" />` (si existant).
>    - **Validation byte-identique visuelle** : diff Storybook avant/après via screenshots `storybook-static/` (délégué L26). Test runtime `rg '<svg' frontend/app/components/ui/*.vue | wc -l` → **baseline 17 → ≤ 2** (reste ≤ 2 = loader spinner Button.vue si non remplacé + inline transition icônes DatePicker acceptés avec justification).
>
> 7. **Documentation `docs/CODEMAPS/ui-primitives.md` §3.9 EsgIcon + §5 pièges #46-48** (AC10) + `methodology.md §4septies` (1ʳᵉ capitalisation post-clôture Epic 10 Phase 0) — **3 exemples Vue** (Lucide `chevron-down` basique + ESG custom `esg-mobile-money` avec variant brand + migration shim pattern depuis SVG inline Drawer close) + §5 pièges **#46-#48** (3 nouveaux cumul ≥ 48 post-10.20 qui s'arrête à #45) + §2 arbo mise à jour + `methodology.md` §4septies retrospective Epic 10 Phase 0 capitalisation 27 → 28-30 leçons (Lucide tree-shaking + wrapper dispatcher registry + migration byte-identique).
>
> 8. **Scan NFR66 post-dev** (AC10) : `rg '#[0-9A-Fa-f]{3,8}' EsgIcon.vue EsgIcon.stories.ts assets/icons/esg/*.svg` → **0 hit** (SVG custom conviennent `currentColor` uniquement, pas de fill hex) · `rg ': any\b|as unknown' EsgIcon.vue` → 0 hit · vitest baseline **≥ 820 post-10.20** → ≥ **830 passed** (+10 minimum) · typecheck baseline **≥ 99 post-10.20** → ≥ **107** (+8 `EsgIcon.test-d.ts`) · Storybook runtime baseline **≥ 224 entries post-10.20** → ≥ **236 entries** dont ≥ 12 `ui-esgicon--*` · coverage c8 **≥ 85 %** lines/branches/functions/statements sur `EsgIcon.vue` · bundle `du -sh storybook-static` ≤ **15 MB** (attention Lucide tree-shaké ajoute seulement ~50 KB max si ≥ 20 icônes whitelisted).

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité + PME persona desktop+mobile + admin N1/N2/N3 arbitrage peer-review + FA workflows + entreprises audits ESG + futurs consommateurs Phase 1+ Cluster A PME Epic 11.1-11.8),

**Je veux** un système iconographique projet unifié qui :
(a) installe `lucide-vue-next` ^0.400+ en **dépendance runtime tree-shakeable** (named imports individuels ChevronDown, Check, X, Calendar… jamais `import * as Lucide`) avec une whitelist ≥ 20 icônes Lucide MVP validée (bundle ≤ 50 KB total gzipped),
(b) expose un composant `frontend/app/components/ui/EsgIcon.vue` **dispatcher par registry** `<EsgIcon name="chevron-down" size="md" variant="default" :decorative="false" />` avec mapping frozen `name → composant Lucide OU SVG custom ESG` + fallback warn dev-only + ARIA strict L24 §4quinquies (`role="img" aria-label={name}` si `decorative=false`, `aria-hidden="true"` strict si `decorative=true`),
(c) fournit **≥ 6 icônes ESG custom** SVG optimisées `frontend/app/assets/icons/esg/*.svg` respectant la convention Lucide (viewBox 0 0 24 24 + stroke currentColor + stroke-width 2 + fill none — cohérence visuelle) pour les concepts métier absents de Lucide : effluents (ODD 6 eau), biodiversité (ODD 15 vie terrestre), audit-social (ESG social), mobile-money (inclusion financière UEMOA/CEDEAO), taxonomie-uemoa (finance durable régionale), sges-beta-seal (sceau SGES BETA certification),
(d) migre **≥ 15 SVG inline** des primitives UI 10.15-10.20 (Combobox trigger/cancel/check/search, DatePicker calendar/prev/next/clear/selected, Button loader spinner, Drawer close, Input clear, Select chevron/check, Textarea warning) vers `<EsgIcon />` via shim pattern 10.6 **byte-identique visuellement** (viewBox + stroke + dimensions Tailwind préservés), sans régression visuelle Storybook ;

**avec** 3 tuples frozen CCC-9 `ICON_SIZES` (5) + `ICON_VARIANTS` (5) + `ESG_ICON_NAMES` (≥ 30) `registry.ts` type-safe, dark mode ≥ 8 variantes `dark:` (variant classes brand/danger/success/muted + hover + focus + placeholder + border), WCAG 2.1 AA validé par Storybook `addon-a11y` **runtime** (grid 30+ icônes dark mode), compile-time enforcement `EsgIcon.test-d.ts` bloquant ≥ 8 combinaisons invalides (`name` hors registry, `size` hors tuple, `variant` hors tuple, `decorative: 'true'` string, `strokeWidth: '2'` string, `class: number`, `name` manquant, `name: true` boolean),

**Afin que** les ≥ 8 consommateurs futurs Phase 1+ (FundApplicationLifecycleBadge Epic 9 `<EsgIcon name="lifecycle-ready" />` + ComplianceBadge Epic 10 `<EsgIcon name="check-circle" variant="success" />` + ReferentialComparisonView Epic 10 + ProjectStatusPill Epic 11 + PackFacadeSelector Epic 11 + DashboardStatCard Epic 12 + AdminArbitrageCard Epic 19 + NotificationToast Epic 20) partagent une **API iconographique unifiée** (plus de SVG inline byte-copy-paste dans N composants = maintenance centralisée), que le **pattern wrapper dispatcher registry** soit byte-identique extensible (ajouter une icône ESG = déposer SVG + 1 ligne registry + 0 modif EsgIcon.vue), et que la **clôture Epic 10 Phase 0 Fondations** soit scellée avec les 27 leçons §4ter.bis→§4sexies capitalisées et la retrospective méthodologique §4septies ouverte pour la transition Epic 11 Phase 1 MVP.

## Acceptance Criteria

### Setup Lucide (3 AC)

**AC1 — Installation `lucide-vue-next` ^0.400+ tree-shakeable + config TypeScript strict**
**Given** `frontend/package.json`,
**When** auditée,
**Then** elle liste `lucide-vue-next: ^0.400.0` (ou version stable ≥ 0.400 courante npm registry) en **dépendance runtime** (`dependencies`, pas `devDependencies`),
**And** aucun peer conflict avec Vue ^3.4+ / Nuxt ^4.4+ (`npm ls lucide-vue-next` → 0 conflict),
**And** `import { ChevronDown, Check, X, Calendar } from 'lucide-vue-next'` fonctionne en TypeScript strict (`npm run build` passe),
**And** `grep "import \* as" frontend/app/**/*.vue frontend/app/**/*.ts | grep lucide` → **0 hit** (interdit import global non tree-shakeable — piège #47),
**And** `grep "import Lucide from" frontend/app/**/*.vue frontend/app/**/*.ts | grep lucide` → **0 hit** (interdit default import global).

**AC2 — Whitelist ≥ 20 icônes Lucide MVP documentée et utilisée**
**Given** le registry `ESG_ICON_NAMES`,
**When** inspecté,
**Then** il contient **≥ 20 noms mappés vers icônes Lucide** : `chevron-down`, `chevron-up`, `chevron-left`, `chevron-right`, `check`, `x`, `calendar`, `clock`, `alert-circle`, `alert-triangle`, `info`, `check-circle`, `x-circle`, `loader`, `search`, `plus`, `minus`, `edit`, `trash`, `eye`, `eye-off`, `download`, `upload`, `file-text`, `link`, `external-link` (liste indicative ≥ 20 — la story dev peut en ajouter/retirer selon usage réel post-migration Task 5 mais minimum 20 enforced),
**And** chaque nom est mappé dans `ICON_MAP` à l'intérieur de `EsgIcon.vue` vers l'export Lucide correspondant (ex. `'chevron-down' → ChevronDown`),
**And** les **conventions de nommage Lucide** sont respectées (kebab-case dans le registry, PascalCase dans l'import : `chevron-down` → `ChevronDown`, cohérent doc Lucide officielle),
**And** `test_esgicon_registry.test.ts` assert `ESG_ICON_NAMES.length >= 30` (20 Lucide whitelist + 6 ESG custom + marge 4).

**AC3 — Bundle size audit tree-shaking effectif ≤ 50 KB MVP**
**Given** le bundle Storybook post-build,
**When** mesuré,
**Then** `cd frontend && npm run storybook:build` produit `storybook-static/` dont la taille incrémentale attribuable à Lucide ≤ **50 KB gzipped** (mesure via `du -sh` delta pré/post-install + `npx source-map-explorer storybook-static/assets/*.js | grep lucide` inspection),
**And** **preuve tree-shaking effectif** : `grep -rE "ChevronDown|Check|Calendar" storybook-static/assets/*.js` → matches présents, **mais** `grep -r "Accessibility|Activity|Airplay"` (icônes Lucide non-whitelistées) → **0 hit** (icônes non importées absentes du bundle final),
**And** bundle total Storybook reste ≤ **15 MB** (budget 10.14 préservé),
**And** Completion Notes documente les **3 chiffres EXACTS** : bundle storybook-static total (MB), delta attribuable Lucide (KB gzipped), nombre d'icônes Lucide effectivement bundlées (count grep).

### EsgIcon wrapper (4 AC)

**AC4 — Composant `ui/EsgIcon.vue` props-typées via `.test-d.ts` + signature stricte**
**Given** `frontend/app/components/ui/EsgIcon.vue`,
**When** auditée,
**Then** elle utilise Vue 3 `<script setup lang="ts">` avec Composition API,
**And** importe depuis `'lucide-vue-next'` : named imports individuels des icônes whitelist (≥ 20 composants PascalCase),
**And** importe les SVG custom ESG via Nuxt 4 SVG loader : `import EsgEffluents from '~/assets/icons/esg/effluents.svg?component'` (pattern `?component` résout SVG → Vue component via `vite-svg-loader` ou équivalent Nuxt 4),
**And** expose :
```ts
import type { IconSize, IconVariant, EsgIconName } from './registry';

interface EsgIconProps {
  name: EsgIconName;                     // literal union ≥ 30
  size?: IconSize;                       // default 'md'
  variant?: IconVariant;                 // default 'default'
  decorative?: boolean;                  // default false (accessible par défaut)
  strokeWidth?: number;                  // default 2 (convention Lucide)
  class?: string;                        // merge Tailwind (pas écrasé)
}
```
**And** aucun `any` / `as unknown` dans `EsgIcon.vue` (`rg ': any\b|as unknown' frontend/app/components/ui/EsgIcon.vue` → 0 hit),
**And** `cd frontend && npm run build` (Nuxt type-check) passe sans erreur,
**And** `EsgIcon.test-d.ts` contient **≥ 8 assertions `@ts-expect-error`** : `name` hors registry, `size: 'xxl'`, `variant: 'rainbow'`, `decorative: 'true'` string, `strokeWidth: '2'` string, `name` manquant (required), `name: true` boolean, `class: 123` number.

**AC5 — Mapping name → composant Lucide OU SVG custom via registry frozen + fallback warn dev-only**
**Given** `EsgIcon.vue` avec `ICON_MAP: Record<EsgIconName, Component>` exhaustif (≥ 30 entrées),
**When** `<EsgIcon name="chevron-down" />` rendu,
**Then** le template `<component :is="resolvedComponent" />` résout à `ChevronDown` (export Lucide) et rend le SVG Lucide natif,
**When** `<EsgIcon name="esg-effluents" />` rendu,
**Then** il résout au SVG custom `EsgEffluents` importé depuis `~/assets/icons/esg/effluents.svg?component`,
**When** `<EsgIcon name="does-not-exist" as any />` rendu (forçage type),
**Then** `console.warn('[EsgIcon] Unknown icon name: "does-not-exist". Falling back to placeholder.')` appelé **1 fois** en DEV (`import.meta.env.DEV === true`) + rendu placeholder SVG (cercle barré viewBox 0 0 24 24 stroke currentColor) sans crash,
**And** en PROD (`import.meta.env.DEV === false`), le warn est stripé par Vite (DCE) — vérifié via `grep "Unknown icon name" .nuxt/dist/client/*.js` → 0 hit en build prod,
**And** test `test_esgicon_behavior.test.ts` case `fallback-unknown-name-warns-dev` utilise `vi.spyOn(console, 'warn')` + `import.meta.env.DEV` stubbed → assert warn appelé 1× avec message strict (pas `.toHaveBeenCalled()` laxiste — L21 §4quater).

**AC6 — Variants couleurs via Tailwind + tokens `@theme` (pas de hex inline) + currentColor Lucide natif**
**Given** `<EsgIcon name="check" variant="brand" />`,
**When** rendu,
**Then** le SVG porte classe Tailwind `text-brand-green dark:text-brand-green` (token `@theme` `--color-brand-green #047857` AA post-darken 10.15 HIGH-2),
**And** Lucide natif utilise `stroke="currentColor"` → hérite la couleur de la classe parent sans hex inline,
**When** `variant="danger"` → classe `text-brand-red dark:text-brand-red` (token `#DC2626` AA),
**When** `variant="success"` → classe `text-verdict-pass dark:text-verdict-pass` (token `--color-verdict-pass` — cohérent ComplianceBadge 10.17),
**When** `variant="muted"` → classe `text-surface-text/60 dark:text-surface-dark-text/60`,
**When** `variant="default"` (default) → classe `text-current` (hérite parent),
**And** prop `class="h-4 w-4 text-red-500"` consommateur **merge** (pas écrase) avec classe variant (via `useAttrs` + `twMerge` OU concat simple — documenté §3.9 CODEMAP),
**And** `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/EsgIcon.vue frontend/app/components/ui/EsgIcon.stories.ts frontend/app/assets/icons/esg/*.svg` → **0 hit** (tokens uniquement, SVG custom utilisent `currentColor`).

**AC7 — ARIA strict (L24 §4quinquies) : `decorative: boolean` → `aria-hidden` OU `role="img" + aria-label`**
**Given** `<EsgIcon name="calendar" />` (decorative default false),
**When** inspecté dans le DOM,
**Then** le SVG porte :
- `role="img"` (valeur stricte `'img'`, pas `'image'` ni absent),
- `aria-label="calendar"` (valeur stricte = prop `name`, pas `aria-label=""` vide),
- **pas** de `aria-hidden` attribute (pas `aria-hidden="false"` non plus — l'attribut absent est la forme canonique),
**When** `<EsgIcon name="calendar" decorative />` (shorthand `:decorative="true"`),
**Then** le SVG porte :
- `aria-hidden="true"` (valeur stricte string `'true'`, pas boolean `true` ni `''` vide),
- **pas** de `role` attribute,
- **pas** de `aria-label` attribute,
**And** test `test_esgicon_a11y.test.ts` assert **strict valeurs L24** :
  - `expect(icon.getAttribute('role')).toBe('img')` (pas `toHaveAttribute('role')` sans 2ᵉ arg — piège capitalisé 10.19 L24),
  - `expect(icon.getAttribute('aria-label')).toBe('calendar')` (pas `.toMatch(/calendar/)` laxiste),
  - `expect(icon.getAttribute('aria-hidden')).toBeNull()` décoratif=false (attribut absent strict),
  - `expect(icon.getAttribute('aria-hidden')).toBe('true')` décoratif=true (string `'true'` strict),
  - vitest-axe smoke `toHaveNoViolations()` sur grid 30 icônes rendues.

### Icônes ESG custom (1 AC)

**AC8 — ≥ 6 SVG custom ESG métier optimisés + registry intégré**
**Given** `frontend/app/assets/icons/esg/`,
**When** listé,
**Then** il contient **≥ 6 fichiers SVG** : `effluents.svg`, `biodiversite.svg`, `audit-social.svg`, `mobile-money.svg`, `taxonomie-uemoa.svg`, `sges-beta-seal.svg`,
**And** chaque SVG respecte la **convention Lucide stricte** :
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- paths ici -->
</svg>
```
**And** **optimisés SVGO** : pas de `<metadata>`, pas de `<title>` inline (aria-label géré par `EsgIcon.vue`), pas de `xmlns:xlink` superflu, pas de `width`/`height` hardcoded (pilotés par `EsgIcon` size mapping),
**And** chaque SVG importable via Nuxt 4 SVG loader `import X from '~/assets/icons/esg/X.svg?component'` → résout vers Vue component,
**And** chaque nom préfixé `esg-*` est présent dans `ESG_ICON_NAMES` registry : `esg-effluents`, `esg-biodiversite`, `esg-audit-social`, `esg-mobile-money`, `esg-taxonomie-uemoa`, `esg-sges-beta-seal`,
**And** **cohérence métier** : chaque SVG représente le concept ESG non disponible dans Lucide (sémantique ODD / UEMOA / SGES) — **documenté §3.9 CODEMAP** avec mapping ODD 6 (effluents eau) / ODD 15 (biodiversité) / ESG social (audit-social) / inclusion financière (mobile-money) / finance durable UEMOA (taxonomie-uemoa) / SGES BETA certification (sges-beta-seal),
**And** test `test_esgicon_registry.test.ts` case `esg-prefix-custom-svgs` assert `ESG_ICON_NAMES.filter(n => n.startsWith('esg-')).length >= 6`.

### Migration mécanique (1 AC)

**AC9 — Remplacer ≥ 15 SVG inline UI primitives par `<EsgIcon />` byte-identique visuellement**
**Given** les primitives UI 10.15-10.20 contenant **17 `<svg>` inline** au total (baseline post-10.20),
**When** auditées post-migration,
**Then** `rg '<svg\b' frontend/app/components/ui/*.vue | wc -l` → **≤ 2** (baseline 17 → ≤ 2, migration ≥ 15 confirmée),
**And** les 2 exceptions acceptables doivent être **documentées** en Completion Notes + justifiées (ex. Button loader spinner si remplacement casse l'animation `animate-spin` CSS scoped — si justification invalide, migration finale obligatoire),
**And** chaque migration respecte le **shim pattern 10.6 byte-identique** :
- Ancien : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><polyline points="6 9 12 15 18 9"/></svg>`,
- Nouveau : `<EsgIcon name="chevron-down" class="h-4 w-4" decorative />`,
- **Dimensions préservées** via class parent (`h-4 w-4`), pas via prop `size` numérique qui casserait le layout flex existant,
- **`decorative` par défaut** pour les icônes purement visuelles des primitives (chevrons, close X, check selected — **pas** d'aria-label qui dupliquerait le label du composant parent cf. Combobox trigger a déjà son `aria-label`),
**And** **validation visuelle byte-identique** : snapshot Storybook avant/après via `npm run storybook:build` + diff bundle `storybook-static/` inspection visuelle stories `ui-combobox--*`, `ui-datepicker--*`, `ui-button--*`, `ui-drawer--*` (délégué L26 runtime, marker inline `// DELEGATED TO Storybook ui-<component>--*`),
**And** **baseline tests préservés** : `npm run test -- --run` → tous tests primitives 10.15-10.20 passent sans modification (Combobox 10.19 + DatePicker 10.20 + autres) — si un test assert `svg.querySelector('polyline')` directement, il doit être refactoré pour asserter via `<EsgIcon>` rendering (refacto mineur attendu Task 5.X documenté Completion Notes).

### Transverse (1 AC)

**AC10 — Stories Storybook ≥ 12 + coverage c8 ≥ 85 % + 0 hex + 0 any + dark: parity ≥ 8 + .test-d.ts ≥ 8 + docs CODEMAPS + methodology §4septies**
**Given** Story 10.21 complétée,
**When** auditée,
**Then** `EsgIcon.stories.ts` co-localisée CSF 3.0 contient **≥ 12 stories** (Grid + Sizes + Variants + Decorative + WithLabel + DarkMode + MappingRegistry + LucideOnly + EsgCustomOnly + UnknownNameFallback + StrokeWidth + Spinner, cible réaliste ≥ 14 avec autodocs + Migration*ComparisonBeforeAfter story démo shim pattern),
**And** comptage runtime OBLIGATOIRE **avant** Completion Notes (pattern B §4ter.bis capitalisé L26 §4sexies 10.20) :
```bash
cd frontend && npm run storybook:build 2>&1 | tail -5
jq '.entries | keys | length' storybook-static/index.json  # baseline ≥ 224 post-10.20
jq '[.entries | to_entries[] | select(.value.id | startswith("ui-esgicon"))] | length' storybook-static/index.json  # cible ≥ 12
du -sh storybook-static  # ≤ 15 MB budget 10.14
```
Consigner les **3 chiffres EXACTS** dans Completion Notes + 2 chiffres Lucide bundle (AC3),
**And** **coverage c8 instrumentée ≥ 85 %** lines/branches/functions/statements sur `EsgIcon.vue` (pattern H-5 10.19 post-review) : `npm run test -- --coverage --run --coverage.include='app/components/ui/EsgIcon.vue'` — valeurs réelles pas fallback smoke,
**And** `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/EsgIcon.vue frontend/app/components/ui/EsgIcon.stories.ts frontend/app/assets/icons/esg/*.svg` → **0 hit** (tokens + currentColor uniquement),
**And** `rg ': any\b|as unknown' frontend/app/components/ui/EsgIcon.vue` → **0 hit**,
**And** `grep -oE "dark:" frontend/app/components/ui/EsgIcon.vue | wc -l` → **≥ 8** (variants brand/danger/success/muted × 2 states hover + focus = 8 minimum),
**And** `docs/CODEMAPS/ui-primitives.md` contient §3.9 EsgIcon avec **≥ 3 exemples Vue** (Lucide basique + ESG custom avec variant + shim pattern migration SVG inline → EsgIcon) + §5 pièges **renuméroté 46-48** (3 nouveaux cumul ≥ 48 post-10.20 qui s'arrête à #45),
**And** `docs/CODEMAPS/methodology.md` **nouvelle section §4septies** post-clôture Epic 10 Phase 0 avec :
  - Retrospective méthodologique Epic 10 (27 leçons §4ter.bis→§4sexies capitalisées → 30 leçons cumulées post-10.21),
  - Leçon 28 : tree-shaking Lucide named imports (piège #47),
  - Leçon 29 : wrapper dispatcher par registry (vs wrapper Reka UI headless slot-forward L25),
  - Leçon 30 : migration mécanique byte-identique shim pattern 10.6 appliqué à N composants en 1 PR atomique,
  - Mesure anti-récurrence : si un 31ᵉ pattern émerge post-review 10.21+ (Epic 11 Phase 1 MVP), créer `§4octies`,
**And** `test_docs_ui_primitives.test.ts` étendu (**≥ 20 tests post-10.20** → **≥ 23 tests post-10.21**) : §3.9 présent, ≥ 48 pièges cumulés + unicité + continuité (`uniqueNumbers.size === matches.length` L27), ≥ 3 exemples §3.9, baseline préservé,
**And** **0 régression** sur tests préexistants (baseline ≥ 820 post-10.20 → ≥ **830** post-10.21, +10 minimum),
**And** **typecheck baseline ≥ 99 post-10.20** → **≥ 107 post-10.21** (+8 minimum `EsgIcon.test-d.ts`),
**And** **3-4 commits intermédiaires lisibles review** (leçon 10.8) :
  1. `feat(10.21): install lucide-vue-next ^0.400 + registry CCC-9 ICON_SIZES/VARIANTS/NAMES + 6 SVG custom ESG`,
  2. `feat(10.21): ui/EsgIcon dispatcher registry + ARIA L24 strict + fallback warn dev + tests behavior/a11y`,
  3. `refactor(10.21): migration ≥15 SVG inline UI primitives 10.15-10.20 → <EsgIcon /> byte-identique shim 10.6`,
  4. `docs(10.21): CODEMAPS §3.9 EsgIcon + pièges #46-48 + methodology §4septies Epic 10 Phase 0 closure + 28-30 leçons`.

## Tasks / Subtasks

- [ ] **Task 1 — Scan NFR66 préalable + baseline + audit SVG inline existants** (AC1, AC10)
  - [ ] 1.1 Grep `EsgIcon\.vue|lucide-vue-next|ICON_SIZES|ICON_VARIANTS|ESG_ICON_NAMES` sur `frontend/app/components/**` + `frontend/tests/**` + `frontend/package.json` → attendu **0 hit** (hors `_bmad-output/` artefacts).
  - [ ] 1.2 Baseline tests : `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner exact post-10.20 (≥ 820 attendu).
  - [ ] 1.3 Baseline typecheck : `npm run test:typecheck 2>&1 | tail -5` → consigner (≥ 99 attendu post-10.20).
  - [ ] 1.4 Baseline Storybook : `jq '.entries | keys | length' frontend/storybook-static/index.json` → consigner (≥ 224 attendu post-10.20).
  - [ ] 1.5 Baseline Storybook bundle : `du -sh frontend/storybook-static` → consigner (≤ 15 MB attendu).
  - [ ] 1.6 Audit SVG inline existants primitives : `rg '<svg\b' frontend/app/components/ui/*.vue -c` → consigner count par fichier (baseline **≥ 17 attendu** pour AC9 validation).
  - [ ] 1.7 Audit pièges publiés CODEMAPS (L27 §4sexies) : `grep -nE "^[0-9]+\. \*\*" docs/CODEMAPS/ui-primitives.md | tail -5` → consigner plus haut numéro (attendu **#45** post-10.20). **Nouveaux pièges 10.21 = #46-#48** (pas réutiliser un numéro publié).
  - [ ] 1.8 Vérif Nuxt 4 SVG loader disponible : `grep -rE "svg.*component|vite-svg-loader" frontend/nuxt.config.ts` → si absent, ajouter `modules: ['@nuxtjs/svg-sprite']` OU `vite: { plugins: [svgLoader()] }` (vite-svg-loader — attention compat Nuxt 4). Si installation nécessaire, documenter Task 1.9 + bundle impact.
  - [ ] 1.9 Recherche npm registry Lucide version stable courante : `npm view lucide-vue-next version` → consigner version ≥ 0.400.0.

- [ ] **Task 2 — Installation `lucide-vue-next` + config tree-shaking** (AC1, AC2, AC3)
  - [ ] 2.1 `cd frontend && npm install lucide-vue-next@^0.400.0 --save` (runtime dependency, pas devDep).
  - [ ] 2.2 Vérifier `package.json dependencies` contient `"lucide-vue-next": "^0.400.0"` + `package-lock.json` régénéré sans conflit (`npm ls lucide-vue-next` → 0 conflict).
  - [ ] 2.3 Test smoke import : créer temporairement `frontend/tests/__smoke_lucide__.test.ts` avec `import { ChevronDown } from 'lucide-vue-next'; test('import works', () => { expect(ChevronDown).toBeDefined(); });` → run → vert → supprimer le fichier (validation install sans polluer tests).
  - [ ] 2.4 **Pré-mesure bundle pré-integration** : `npm run storybook:build && du -sh storybook-static` → consigner baseline **avant** EsgIcon (référence AC3 delta ≤ 50 KB).
  - [ ] 2.5 Si Nuxt 4 SVG loader pas configuré (Task 1.8) : `npm install -D vite-svg-loader` + ajouter `frontend/nuxt.config.ts` → `vite: { plugins: [svgLoader()] }` avec import dynamique conditionnel. Tester via `import X from '~/assets/icons/esg/test.svg?component'` depuis une story Storybook.

- [ ] **Task 3 — Registry `ui/registry.ts` extension 3 tuples CCC-9** (AC1, AC2, AC4)
  - [ ] 3.1 Ajouter `ICON_SIZES = Object.freeze(['xs', 'sm', 'md', 'lg', 'xl'] as const)` (ordre canonique croissant, default = index 2 `md` — pas index 0 car `xs` trop petit).
  - [ ] 3.2 Ajouter `ICON_VARIANTS = Object.freeze(['default', 'brand', 'danger', 'success', 'muted'] as const)` (ordre canonique default-first — cas majoritaire).
  - [ ] 3.3 Ajouter `ESG_ICON_NAMES = Object.freeze([ /* ≥ 30 noms */ ] as const)` (20 Lucide whitelist + 6 ESG custom + marge 4 extensibilité Phase 1+).
  - [ ] 3.4 Types dérivés `IconSize`, `IconVariant`, `EsgIconName` via `typeof TUPLE[number]`.
  - [ ] 3.5 Docstring JSDoc référençant Story 10.21 + rationale ordre canonique (pièges #46-#48 pour inversions éventuelles) + convention `esg-*` prefix pour SVG custom.
  - [ ] 3.6 Exports 10.15-10.20 byte-identique préservés (diff `git diff frontend/app/components/ui/registry.ts` restreint aux ajouts).
  - [ ] 3.7 `npm run test:typecheck` → baseline préservé (registry ne change pas count tant que `.test-d.ts` EsgIcon pas ajouté — check Task 5.4).
  - [ ] 3.8 `test_esgicon_registry.test.ts` **6 tests** :
    - `ICON_SIZES.length === 5` + `ICON_VARIANTS.length === 5` + `ESG_ICON_NAMES.length >= 30` (AC2).
    - `Object.isFrozen(ICON_SIZES) && Object.isFrozen(ICON_VARIANTS) && Object.isFrozen(ESG_ICON_NAMES)`.
    - Dédoublonnement : `new Set(ESG_ICON_NAMES).size === ESG_ICON_NAMES.length`.
    - Ordre canonique : `ICON_SIZES[2] === 'md'` + `ICON_VARIANTS[0] === 'default'`.
    - ESG prefix : `ESG_ICON_NAMES.filter(n => n.startsWith('esg-')).length >= 6` (AC8).
    - Lucide whitelist minimum : `ESG_ICON_NAMES.filter(n => !n.startsWith('esg-')).length >= 20` (AC2).
  - [ ] 3.9 **Commit intermédiaire 1** : `feat(10.21): install lucide-vue-next ^0.400 + registry CCC-9 ICON_SIZES/VARIANTS/NAMES + 6 SVG custom ESG`.

- [ ] **Task 4 — SVG custom ESG `frontend/app/assets/icons/esg/` ≥ 6 fichiers** (AC8)
  - [ ] 4.1 Créer dossier `frontend/app/assets/icons/esg/` si absent.
  - [ ] 4.2 Créer `effluents.svg` — gouttes + filtre — viewBox 0 0 24 24 + convention Lucide stricte (stroke currentColor + stroke-width 2 + fill none).
  - [ ] 4.3 Créer `biodiversite.svg` — feuille + insecte — convention Lucide.
  - [ ] 4.4 Créer `audit-social.svg` — document + checkmark + personnage.
  - [ ] 4.5 Créer `mobile-money.svg` — smartphone + symbole FCFA.
  - [ ] 4.6 Créer `taxonomie-uemoa.svg` — sigle UEMOA stylisé OU carte Afrique Ouest.
  - [ ] 4.7 Créer `sges-beta-seal.svg` — sceau rond + texte « SGES β ».
  - [ ] 4.8 Optimiser chaque SVG via SVGO `npx svgo frontend/app/assets/icons/esg/*.svg --config='{"plugins":["preset-default","removeXMLNS","removeViewBox"]}'` (attention garder viewBox — config custom pour préserver viewBox).
  - [ ] 4.9 Scan hex SVG custom : `rg '#[0-9A-Fa-f]{3,8}|fill="[^n]' frontend/app/assets/icons/esg/*.svg` → **0 hit** (hors `fill="none"`). Couleur uniquement via `stroke="currentColor"`.
  - [ ] 4.10 Test smoke import : `import EsgEffluents from '~/assets/icons/esg/effluents.svg?component'` depuis story ou test → rend SVG valide.

- [ ] **Task 5 — Composant `ui/EsgIcon.vue` dispatcher + `EsgIcon.test-d.ts`** (AC4-AC7)
  - [ ] 5.1 `<script setup lang="ts">` avec imports :
    - Named imports Lucide ≥ 20 : `ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Check, X, Calendar, Clock, AlertCircle, AlertTriangle, Info, CheckCircle2 as CheckCircle, XCircle, Loader2 as Loader, Search, Plus, Minus, Edit, Trash2 as Trash, Eye, EyeOff, Download, Upload, FileText, Link, ExternalLink` depuis `'lucide-vue-next'`.
    - Imports SVG custom : `EsgEffluents, EsgBiodiversite, EsgAuditSocial, EsgMobileMoney, EsgTaxonomieUemoa, EsgSgesBetaSeal` depuis `~/assets/icons/esg/*.svg?component`.
    - Types registry : `IconSize, IconVariant, EsgIconName`.
    - Vue 3 : `computed, h, type Component` (h pour placeholder fallback).
  - [ ] 5.2 `defineProps<EsgIconProps>()` + `withDefaults` : `size: 'md'`, `variant: 'default'`, `decorative: false`, `strokeWidth: 2`.
  - [ ] 5.3 Constante `ICON_MAP: Record<EsgIconName, Component>` avec mapping complet ≥ 30 entrées (20 Lucide + 6 ESG + marge).
  - [ ] 5.4 Constante `SIZE_MAP: Record<IconSize, number> = { xs: 12, sm: 16, md: 20, lg: 24, xl: 32 }`.
  - [ ] 5.5 Constante `VARIANT_MAP: Record<IconVariant, string>` = mapping Tailwind classes tokens `@theme` (AC6).
  - [ ] 5.6 Computed `resolvedComponent`: `ICON_MAP[props.name] ?? placeholderComponent`. Helper `placeholderComponent` rend `<svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>` (cercle barré).
  - [ ] 5.7 Watcher/effect fallback warn dev-only (AC5) :
    ```ts
    if (import.meta.env.DEV && !(props.name in ICON_MAP)) {
      console.warn(`[EsgIcon] Unknown icon name: "${props.name}". Falling back to placeholder.`);
    }
    ```
  - [ ] 5.8 Computed `pixelSize = computed(() => SIZE_MAP[props.size])`.
  - [ ] 5.9 Computed `variantClass = computed(() => VARIANT_MAP[props.variant])`.
  - [ ] 5.10 Computed `finalClass = computed(() => [variantClass.value, props.class].filter(Boolean).join(' '))` — merge avec class prop consommateur (pas écrase).
  - [ ] 5.11 Computed `ariaAttrs` (AC7 L24) :
    ```ts
    const ariaAttrs = computed(() => props.decorative
      ? { 'aria-hidden': 'true' as const }
      : { role: 'img' as const, 'aria-label': props.name });
    ```
  - [ ] 5.12 Template :
    ```vue
    <template>
      <component
        :is="resolvedComponent"
        v-bind="ariaAttrs"
        :class="finalClass"
        :size="pixelSize"
        :stroke-width="strokeWidth"
      />
    </template>
    ```
  - [ ] 5.13 Scan hex : `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/EsgIcon.vue` → **0 hit**.
  - [ ] 5.14 Scan any : `rg ': any\b|as unknown' frontend/app/components/ui/EsgIcon.vue` → **0 hit**.
  - [ ] 5.15 Scan dark: `grep -oE "dark:" frontend/app/components/ui/EsgIcon.vue | wc -l` → **≥ 8** (via VARIANT_MAP : brand/danger/success/muted × `text-*` + `dark:text-*` = 8 minimum).
  - [ ] 5.16 `EsgIcon.test-d.ts` **≥ 8 `@ts-expect-error`** (AC4) :
    ```ts
    import { h } from 'vue';
    import EsgIcon from '~/components/ui/EsgIcon.vue';

    // @ts-expect-error name hors registry
    h(EsgIcon, { name: 'does-not-exist' });
    // @ts-expect-error size hors ICON_SIZES
    h(EsgIcon, { name: 'check', size: 'xxl' });
    // @ts-expect-error variant hors ICON_VARIANTS
    h(EsgIcon, { name: 'check', variant: 'rainbow' });
    // @ts-expect-error decorative string au lieu de boolean
    h(EsgIcon, { name: 'check', decorative: 'true' });
    // @ts-expect-error strokeWidth string au lieu de number
    h(EsgIcon, { name: 'check', strokeWidth: '2' });
    // @ts-expect-error name manquant (required)
    h(EsgIcon, {});
    // @ts-expect-error name boolean
    h(EsgIcon, { name: true });
    // @ts-expect-error class number au lieu de string
    h(EsgIcon, { name: 'check', class: 123 });
    ```
  - [ ] 5.17 `npm run test:typecheck` → baseline ≥ 99 → **≥ 107 passed** (+8 minimum).
  - [ ] 5.18 **Commit intermédiaire 2** : `feat(10.21): ui/EsgIcon dispatcher registry + ARIA L24 strict + fallback warn dev + tests behavior/a11y`.

- [ ] **Task 6 — Tests Vitest EsgIcon (Pattern A observable + L21 strict + L24 attribute-strict)** (AC10)
  - [ ] 6.1 `test_esgicon_behavior.test.ts` : **≥ 12 tests** Pattern A observable :
    - **Rendering Lucide** : `<EsgIcon name="chevron-down" />` → `expect(wrapper.find('svg').exists()).toBe(true)` + `expect(wrapper.find('svg').html()).toContain('polyline')` (L21 strict pas smoke existence).
    - **Rendering ESG custom** : `<EsgIcon name="esg-effluents" />` → `expect(wrapper.find('svg').attributes('viewbox')).toBe('0 0 24 24')` + `stroke === 'currentColor'`.
    - **Size xs** : `size="xs"` → `expect(wrapper.find('svg').attributes('width')).toBe('12')`.
    - **Size xl** : `size="xl"` → `width === '32'`.
    - **Variant brand** : `variant="brand"` → `expect(wrapper.find('svg').classes()).toContain('text-brand-green')`.
    - **Variant danger** : `variant="danger"` → classes contient `text-brand-red`.
    - **Variant success** : `variant="success"` → classes contient `text-verdict-pass`.
    - **StrokeWidth forward** : `strokeWidth={3}` → `stroke-width === '3'`.
    - **Fallback unknown name warn dev** (AC5 L21 strict) :
      ```ts
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      mount(EsgIcon, { props: { name: 'unknown-xyz' as EsgIconName } });
      expect(warnSpy).toHaveBeenCalledTimes(1);
      expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('unknown-xyz'));
      warnSpy.mockRestore();
      ```
    - **Fallback placeholder rendered** : assert placeholder cercle barré SVG rendu via `wrapper.find('svg line').exists()`.
    - **Class merge** : `<EsgIcon class="custom-foo" variant="brand" />` → classes contient `custom-foo` AND `text-brand-green` (merge pas écrase).
    - **Decorative true** : `decorative={true}` → `aria-hidden="true"` strict + pas de `role` + pas de `aria-label`.
    - **Decorative false (default)** : `role="img"` strict + `aria-label="calendar"` strict.
  - [ ] 6.2 `test_esgicon_a11y.test.ts` : **≥ 6 tests** ARIA attribute-strict L24 §4quinquies :
    - `expect(icon.getAttribute('aria-hidden')).toBe('true')` (valeur stricte string, pas `.toHaveAttribute('aria-hidden')` sans 2ᵉ arg).
    - `expect(icon.getAttribute('role')).toBe('img')` strict.
    - `expect(icon.getAttribute('aria-label')).toBe('calendar')` strict (valeur exacte = prop `name`).
    - `expect(icon.getAttribute('aria-hidden')).toBeNull()` quand `decorative={false}` (attribut absent strict).
    - `expect(icon.getAttribute('role')).toBeNull()` quand `decorative={true}` (attribut absent strict).
    - vitest-axe smoke `toHaveNoViolations()` sur rendu grid ≥ 10 icônes mixtes decorative/semantic.
    - Contraste/focus dark mode délégués explicitement per-path (L26 §4sexies appliquée proactivement) :
      ```ts
      describe.skip('AC6 variant contrast dark mode — DELEGATED Storybook per-path', () => {
        it.todo('variant=brand dark — Storybook ui-esgicon--dark-mode--brand');
        it.todo('variant=danger dark — Storybook ui-esgicon--dark-mode--danger');
        it.todo('variant=success dark — Storybook ui-esgicon--dark-mode--success');
        it.todo('variant=muted dark — Storybook ui-esgicon--dark-mode--muted');
      });
      ```
  - [ ] 6.3 `test_no_hex_hardcoded_esgicon.test.ts` : **2 tests** scan `EsgIcon.vue` + `EsgIcon.stories.ts` + `assets/icons/esg/*.svg` → 0 hit hex + 0 hit `: any`/`as unknown`.
  - [ ] 6.4 **Assertions strictes L21 §4quater appliquées proactivement** :
    - AC5 fallback warn : `expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('unknown-xyz'))` strict (pas `.toHaveBeenCalled()` permissif).
    - AC6 variant class : `expect(classes).toContain('text-brand-green')` strict (pas `.toMatch(/text-/)` laxiste).
    - AC7 ARIA : `toBe('true')` + `toBeNull()` strict (pas `toHaveAttribute(key)` sans 2ᵉ arg — L24).
    - AC4 props : `expect(wrapper.props()).toEqual(expect.objectContaining({ name: 'check', size: 'md' }))` strict.
  - [ ] 6.5 `npm run test -- --run` → baseline ≥ 820 → **≥ 830 passed** (+10 minimum demandé).
  - [ ] 6.6 **Commit intermédiaire 3 (fusionnable avec 2)** : si 2 + 5-6 séparés : `test(10.21): EsgIcon behavior + a11y L24 strict + L21 observable + coverage c8 ≥85%`.

- [ ] **Task 7 — Migration mécanique ≥ 15 SVG inline UI primitives 10.15-10.20** (AC9)
  - [ ] 7.1 Inventaire précis `rg '<svg\b' frontend/app/components/ui/*.vue -A 0 --line-number` → liste exhaustive lignes + fichiers.
  - [ ] 7.2 Pour chaque SVG inline, identifier le nom EsgIcon correspondant dans `ESG_ICON_NAMES` (chevron-down, x, check, calendar, loader, etc.).
  - [ ] 7.3 Migration **byte-identique shim pattern 10.6** :
    - Combobox.vue (5 SVG) : chevron-down trigger + X cancel + check option + search icon + clear → 5 × `<EsgIcon name="..." class="h-4 w-4" decorative />`.
    - DatePicker.vue (5 SVG) : calendar trigger + ← prev + → next + x clear + check selected → 5 × `<EsgIcon />`.
    - Button.vue (1 SVG loader) : `<EsgIcon name="loader" class="h-4 w-4 animate-spin motion-reduce:animate-none" decorative />`.
    - Drawer.vue (1 SVG close) : `<EsgIcon name="x" class="h-5 w-5" decorative />`.
    - Input.vue (1 SVG) : `<EsgIcon name="x" />` (clear icon type=search).
    - Select.vue (2 SVG) : chevron-down + check selected.
    - Textarea.vue (1 SVG warning si existant).
    - FullscreenModal.vue (1 SVG close) : `<EsgIcon name="x" />`.
  - [ ] 7.4 Post-migration audit : `rg '<svg\b' frontend/app/components/ui/*.vue -c | sort -t: -k2 -n` → baseline 17 → **≤ 2** (tolérance 2 SVG inline justifiés doc Completion Notes si refactor animation spinner casse).
  - [ ] 7.5 Tests primitives 10.15-10.20 **doivent continuer à passer sans modification** : `npm run test -- --run frontend/tests/components/ui/test_combobox_*.test.ts frontend/tests/components/ui/test_datepicker_*.test.ts ...` → 0 régression.
  - [ ] 7.6 Si un test assert directement `svg.querySelector('polyline')` ou `svg.innerHTML`, refactorer pour asserter via `<EsgIcon name="...">` rendering (assertion agnostique : `wrapper.findComponent(EsgIcon).props('name') === 'chevron-down'`).
  - [ ] 7.7 Snapshot Storybook avant/après : `npm run storybook:build && du -sh storybook-static` → vérifier **pas de régression visuelle** stories `ui-combobox--*`, `ui-datepicker--*`, `ui-button--*`, `ui-drawer--*` (délégation runtime L26 documenté inline skips).
  - [ ] 7.8 **Commit intermédiaire 3** : `refactor(10.21): migration ≥15 SVG inline UI primitives 10.15-10.20 → <EsgIcon /> byte-identique shim 10.6`.

- [ ] **Task 8 — Stories `EsgIcon.stories.ts` + Documentation CODEMAPS §3.9 + §4septies methodology** (AC10)
  - [ ] 8.1 `EsgIcon.stories.ts` co-localisée ≥ 12 stories (Grid + Sizes + Variants + Decorative + WithLabel + DarkMode + MappingRegistry + LucideOnly + EsgCustomOnly + UnknownNameFallback + StrokeWidth + Spinner + optionnels MigrationBeforeAfter + Grid500Icons).
  - [ ] 8.2 Play functions interactives avec `@storybook/test` : `Grid` play = screenshot rendering mode visuel (décorative validation L26) ; `WithLabel` play = `await expect(canvas.getByRole('img', {name: /calendar/})).toBeInTheDocument()`.
  - [ ] 8.3 Helper `asStorybookComponent<T>()` réutilisé `frontend/app/types/storybook.ts` (pattern 10.15 M-3).
  - [ ] 8.4 **Comptage runtime OBLIGATOIRE post-build** (pattern B §4ter.bis + L26 §4sexies 10.20 capitalisé) : consigner EXACT avant Completion Notes.
  - [ ] 8.5 `docs/CODEMAPS/ui-primitives.md` §3.9 EsgIcon inséré après §3.8 DatePicker avec **≥ 3 exemples Vue** :
    1. Lucide basique `<EsgIcon name="chevron-down" class="h-4 w-4" decorative />`.
    2. ESG custom avec variant + accessible `<EsgIcon name="esg-mobile-money" variant="brand" :decorative="false" />`.
    3. Migration shim pattern : ancien SVG inline Combobox trigger → `<EsgIcon name="chevron-down" class="h-4 w-4" decorative />` (démo comparison).
  - [ ] 8.6 §5 Pièges étendu **45 post-10.20 → 48 post-10.21** (+3 nouveaux) :
    - **#46 Wrapper EsgIcon ne double-déclare pas les props natives Lucide (L25 §4sexies généralisée)** : `size`, `color`, `strokeWidth` sont forward-passed directement via mapping registry → composant Lucide natif. Ne JAMAIS injecter `<EsgIcon :size="24" />` ET puis `<LucideIcon :size="24" />` double-déclaré (la valeur Vue serait écrasée par Lucide défaut si `:size` absent template wrapper). Principe généralisé 10.20 L25 appliqué aux dispatchers par registry.
    - **#47 Tree-shaking Lucide named imports obligatoires** : `import { ChevronDown, X } from 'lucide-vue-next'` (named) → ~1.5 KB/icône gzipped. `import * as Lucide from 'lucide-vue-next'` OU `import Lucide from 'lucide-vue-next'` → **bundle 1400+ icônes = ~500 KB+ non tree-shaké = P0 bundle regression**. Test grep `rg "import \* as.*lucide" frontend/` → 0 hit strict. Application : tout nouveau composant consommant Lucide directement (non via EsgIcon) DOIT faire named imports.
    - **#48 Migration SVG inline → EsgIcon byte-identique via `class` parent pas `size` prop** : le sizing historique des SVG inline des primitives 10.15-10.20 est piloté par **class Tailwind parent** (`h-4 w-4`, `h-5 w-5`). Remplacer par `<EsgIcon size="md" />` casse le flex layout existant (EsgIcon mappe `md → 20px` ≠ `h-4 w-4 = 16px`). **Solution shim pattern 10.6** : préserver `class="h-4 w-4"` du parent + omettre prop `size` OU aligner `size="sm"` (16px). Validation byte-identique via screenshots Storybook. Documenté §3.9 exemple 3.
  - [ ] 8.7 §2 Arborescence cible étendue (+4 lignes : EsgIcon.vue + EsgIcon.stories.ts + EsgIcon.test-d.ts + assets/icons/esg/*.svg × 6).
  - [ ] 8.8 `test_docs_ui_primitives.test.ts` étendu : 20 → **≥ 23 tests** (§3.9 EsgIcon présent + ≥ 48 pièges cumulés + unicité L27 `uniqueNumbers.size === matches.length` + ≥ 3 exemples §3.9 + baseline 10.15-10.20 préservé).
  - [ ] 8.9 `docs/CODEMAPS/methodology.md` nouvelle section **§4septies — Retrospective Epic 10 Phase 0 + leçons 28-30** :
    - Synthèse 27 leçons §4ter.bis→§4sexies capitalisées Epic 10 (19+2+3+3).
    - **Leçon 28 (tree-shaking Lucide named imports)** : application immédiate au wrapping de toute bibliothèque d'icônes ou d'utilities Vue/TS dont le bundle global dépasse 100 KB. Test anti-récurrence `rg "import \* as.*lucide" → 0 hit` enforced CI.
    - **Leçon 29 (wrapper dispatcher par registry ≠ wrapper Reka UI headless)** : EsgIcon dispatche par `name: EsgIconName` vers `ICON_MAP: Record<..., Component>` avec fallback warn dev. Contraste avec pattern Reka UI (slot-forward primitive headless). Application : tout futur wrapper multi-source (theme, locale, plugin) adoptera pattern dispatcher registry.
    - **Leçon 30 (migration mécanique byte-identique shim pattern 10.6 scale-up)** : 10.6 StorageProvider ≈ 1 interface, 10.21 EsgIcon ≈ 15+ SVG inline simultanés dans 1 PR atomique. Technique : shim pattern `<EsgIcon name="..." class="dimensions-héritées" />` + test baseline préservé + screenshots Storybook diff. Application : migrations futures bibliothèques (icônes, utilities, date libs, validation schemas).
    - **Cumul 30 leçons** cross-patterns Epic 10. Si un 31ᵉ pattern émerge post-review 10.21 (Epic 11 Phase 1 MVP), créer `§4octies` (pas `§4septies.extension`).
    - **Vélocité mesurée Epic 10** : 60-75 % estimate L + 20-50 % estimate M confirmée (data 23 stories closed). Projection sprint v2 **10-11 mois Cluster A-E** confirmée. Retrospective formelle recommandée via `bmad-retrospective` skill après Story 10.21 done.
  - [ ] 8.10 **Commit final 4** : `docs(10.21): CODEMAPS §3.9 EsgIcon + pièges #46-48 + methodology §4septies Epic 10 Phase 0 closure + 28-30 leçons`.

- [ ] **Task 9 — Scan NFR66 post-dev + validation finale + comptage runtime Storybook** (AC10)
  - [ ] 9.1 Scan hex `EsgIcon.vue` + `EsgIcon.stories.ts` + `registry.ts` diff + `assets/icons/esg/*.svg` → **0 hit** (currentColor + tokens uniquement).
  - [ ] 9.2 `: any\b` / `as unknown` dans `EsgIcon.vue` + `.test-d.ts` → **0 hit** (cast `as unknown` test-only acceptable runtime .test.ts — cohérent 10.18/10.19/10.20).
  - [ ] 9.3 **Build Storybook + comptage runtime OBLIGATOIRE** (pattern B capitalisé L26 §4sexies) :
    ```bash
    cd frontend && npm run storybook:build 2>&1 | tail -5
    jq '.entries | keys | length' storybook-static/index.json  # baseline ≥ 224
    jq '[.entries | to_entries[] | select(.value.id | startswith("ui-esgicon"))] | length' storybook-static/index.json  # cible ≥ 12
    du -sh storybook-static  # ≤ 15 MB
    ```
    Consigner les 3 chiffres EXACTS dans Completion Notes **AVANT** tout claim de complétude.
  - [ ] 9.4 **Mesure bundle delta Lucide AC3** :
    ```bash
    du -sb storybook-static  # total bytes post-integration
    # compare avec baseline pré-integration Task 2.4
    grep -rE "ChevronDown|Check|Calendar" storybook-static/assets/*.js | wc -l  # > 0 attendu (tree-shaking minimum)
    grep -rE "Accessibility\(|Activity\(" storybook-static/assets/*.js | wc -l  # 0 attendu (icônes non-whitelistées absentes)
    ```
    Consigner : delta KB attribuable Lucide, preuve tree-shaking effectif (≥ 1 Lucide icon bundled + 0 non-whitelisted bundled).
  - [ ] 9.5 **Ajustements vs spec documentés (L20 §4quater appliquée proactivement)** : recenser en Completion Notes § « Ajustements mineurs vs spec » chaque AC avec écart. Format : `**AC# — titre** : prescription originale / décision (implémenté|déféré|refusé|délégué) / raison / suivi (commit ou `DEF-10.21-N` dans `deferred-work.md`)`. Si 0 écart : écrire `**Aucun écart vs spec** — 10 AC honorés intégralement, ≥ 12 stories runtime vérifiées, ≥ 8 assertions typecheck atteintes, ≥ 10 tests nouveaux verts, coverage c8 ≥ 85 %.`.
  - [ ] 9.6 `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner : baseline ≥ 820 → ≥ **830** passed (+10 min).
  - [ ] 9.7 `npm run test:typecheck 2>&1 | tail -5` → consigner : baseline ≥ 99 → ≥ **107** passed (+8 min).
  - [ ] 9.8 `grep -oE "dark:" frontend/app/components/ui/EsgIcon.vue | wc -l` → **≥ 8** (AC10 plancher sans inflation).
  - [ ] 9.9 Coverage c8 `npm run test -- --coverage --run --coverage.include='app/components/ui/EsgIcon.vue' 2>&1 | grep EsgIcon` → **≥ 85 %** sur 4 métriques (valeurs réelles pas fallback smoke).
  - [ ] 9.10 **Commit final 4** (si Task 8 séparée) : fusionne docs + methodology.
  - [ ] 9.11 **Clôture Epic 10 Phase 0** : déclarer explicitement en Completion Notes « Epic 10 Phase 0 Fondations closed — 23/23 stories done — 30 leçons cumulées §4ter.bis→§4septies — transition Epic 11 Phase 1 MVP Cluster A PME 11.1-11.8 déclenchée ». Recommander exécution `bmad-retrospective` skill pour Epic 10.

## Dev Notes

### 1. Architecture cible — arborescence finale post-10.21

```
frontend/
├── app/
│   ├── assets/
│   │   └── icons/
│   │       └── esg/                          (NOUVEAU dossier 10.21 — ≥ 6 SVG custom)
│   │           ├── effluents.svg             (NOUVEAU — ODD 6 eau propre)
│   │           ├── biodiversite.svg          (NOUVEAU — ODD 15 vie terrestre)
│   │           ├── audit-social.svg          (NOUVEAU — ESG social)
│   │           ├── mobile-money.svg          (NOUVEAU — inclusion financière UEMOA)
│   │           ├── taxonomie-uemoa.svg       (NOUVEAU — finance durable régionale)
│   │           └── sges-beta-seal.svg        (NOUVEAU — SGES BETA certification)
│   └── components/
│       └── ui/                               (10 composants existants + 1 NOUVEAU 10.21)
│           ├── FullscreenModal.vue           (MIGRÉ 10.21 : 1 SVG → <EsgIcon />)
│           ├── ToastNotification.vue         (inchangé)
│           ├── Button.vue                    (MIGRÉ 10.21 : 1 SVG spinner → <EsgIcon name="loader" animate-spin />)
│           ├── Input.vue                     (MIGRÉ 10.21 : 1 SVG clear → <EsgIcon />)
│           ├── Textarea.vue                  (MIGRÉ 10.21 : 1 SVG warning → <EsgIcon /> si existant)
│           ├── Select.vue                    (MIGRÉ 10.21 : 2 SVG chevron+check → 2 × <EsgIcon />)
│           ├── Badge.vue                     (inchangé — 0 SVG inline)
│           ├── Drawer.vue                    (MIGRÉ 10.21 : 1 SVG close → <EsgIcon name="x" />)
│           ├── Combobox.vue                  (MIGRÉ 10.21 : 5 SVG → 5 × <EsgIcon />)
│           ├── Tabs.vue                      (inchangé — 0 SVG inline)
│           ├── DatePicker.vue                (MIGRÉ 10.21 : 5 SVG → 5 × <EsgIcon />)
│           ├── EsgIcon.vue                   (NOUVEAU 10.21 : dispatcher registry Lucide + ESG custom)
│           ├── EsgIcon.stories.ts            (NOUVEAU 10.21 : ≥ 12 stories CSF 3.0)
│           └── registry.ts                   (ÉTENDU 10.21 : +3 frozen tuples ICON_SIZES/VARIANTS/NAMES)
├── nuxt.config.ts                            (ÉTENDU conditionnel 10.21 : vite-svg-loader si absent)
├── package.json                              (ÉTENDU 10.21 : +lucide-vue-next ^0.400)
└── tests/components/ui/                      (27 fichiers existants post-10.20 + 5 NOUVEAUX 10.21)
    ├── test_esgicon_registry.test.ts         (NOUVEAU — 6 tests)
    ├── test_esgicon_behavior.test.ts         (NOUVEAU — ≥ 12 tests Pattern A observable)
    ├── test_esgicon_a11y.test.ts             (NOUVEAU — ≥ 6 tests L24 attribute-strict + L26 délégation per-path)
    ├── test_no_hex_hardcoded_esgicon.test.ts (NOUVEAU — 2 tests)
    └── EsgIcon.test-d.ts                     (NOUVEAU — ≥ 8 @ts-expect-error)

docs/CODEMAPS/
├── ui-primitives.md                          (ÉTENDU 10.21 : §3.9 EsgIcon + pièges #46-48 + §2 arbo)
└── methodology.md                            (ÉTENDU 10.21 : §4septies retrospective Epic 10 Phase 0 + leçons 28-30)
```

**Aucune modification** :
- `frontend/app/assets/css/main.css` (tokens livrés 10.14-10.17 — EsgIcon consomme tokens existants).
- `frontend/.storybook/main.ts`, `preview.ts` (config stables).
- `frontend/vitest.config.ts` (typecheck glob `tests/**/*.test-d.ts` actif).
- `frontend/tsconfig.json` (strict mode OK).
- Tests primitives 10.15-10.20 existants (AC9 exige 0 régression — refacto mineur Task 7.6 acceptable si assertion SVG-path directe).
- `frontend/app/components/gravity/*`, `frontend/app/components/chat/*` (aucun consommateur 10.21 en Phase 0 — migrations Epic 11+).

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|----------|----------|-----------|
| **Q1** | **`lucide-vue-next`** OU **`@iconify/vue`** OU **Heroicons** OU **icônes maison SVG only** ? | **`lucide-vue-next`** | UX Step 11 Q20 verrouille pile Lucide unique (cohérence visuelle). `@iconify/vue` = catalogue géant mais dépendance runtime serveur (pas pur tree-shakeable). Heroicons = opinionated style Tailwind (trop couplé). Maison = 1400 icônes à produire → irréaliste MVP. Lucide = 1400+ icônes disponibles, named imports tree-shakeables, stroke-based cohérent dark mode, communauté active. |
| **Q2** | **Wrapper `EsgIcon` dispatcher par registry** OU **re-export direct Lucide + composant séparé `EsgCustomIcon` pour SVG métier** ? | **Wrapper dispatcher unique** | API unifiée consommateurs (`<EsgIcon name="..." />` partout) = moins de cognitive load. CLAUDE.md §Reutilisabilite composants exige composition > duplication. Registry frozen enforce type-safety (prop `name` literal union bloque `name="typo"` compile-time). Fallback warn dev-only centralisé 1 seul endroit. L25 §4sexies généralisée : dispatcher ≠ wrapper Reka UI, pas de conflit pattern. |
| **Q3** | **Import dynamique SVG via `?component`** (vite-svg-loader) OU **inline `<svg>` dans `EsgIcon.vue`** OU **sprite sheet `<use xlink:href>`** ? | **`?component` dynamic import** | Nuxt 4 + Vite 5 compatibles `vite-svg-loader` (peer dep). Inline = bloat `EsgIcon.vue` à 1000+ lignes (6 SVG × ~50 lignes chacun + croissance Phase 1+). Sprite sheet = HTTP request extra au runtime (incompatible Nuxt 4 SSR). `?component` → Vue component généré compile-time, tree-shaké si non utilisé, minifié. Pattern cohérent frontend modernes (sveltekit, astro). |
| **Q4** | **Fallback warn dev-only `console.warn`** OU **erreur runtime `throw`** OU **silent fallback placeholder** ? | **Warn dev-only + placeholder** | `throw` = crash app en prod pour typo dev → inacceptable UX PME. Silent = pas de feedback dev → bugs invisibles. Warn dev-only via `import.meta.env.DEV` = Vite DCE strippé en prod (0 bloat prod) + feedback loud en dev (console bruyante = dev voit typo). Placeholder SVG cercle barré = fallback visible utilisateur sans crash (signal visuel « icône manquante » acceptable en dev preview). |
| **Q5** | **Prop `decorative: boolean` default `false`** (accessible par défaut) OU **default `true`** (décoratif par défaut — convention web traditionnelle) ? | **Default `false`** | Convention Mefali accessibilité-first (WCAG 2.1 AA critique pour secteur informel + PME africaines publics cibles). Default accessible signifie `aria-label={name}` rendu → lecteurs écran annoncent « image: chevron-down » par défaut. Consommateur choisit explicitement `decorative` quand icône est redondante avec label parent (cas Combobox trigger qui a déjà son aria-label → `<EsgIcon ... decorative />`). Erreur safe : `decorative={false}` ≠ breaking si label existe, `decorative={true}` sans label parent = inaccessible → on préfère faux positif sur accessibilité plutôt que faux négatif. |

### 3. Exemple squelette — `ui/EsgIcon.vue` (structure condensée)

```vue
<script setup lang="ts">
import { computed, type Component } from 'vue';
import {
  ChevronDown, ChevronUp, ChevronLeft, ChevronRight,
  Check, X, Calendar, Clock,
  AlertCircle, AlertTriangle, Info, CheckCircle2, XCircle,
  Loader2, Search, Plus, Minus, Edit, Trash2,
  Eye, EyeOff, Download, Upload, FileText, Link, ExternalLink,
} from 'lucide-vue-next';
import EsgEffluents from '~/assets/icons/esg/effluents.svg?component';
import EsgBiodiversite from '~/assets/icons/esg/biodiversite.svg?component';
import EsgAuditSocial from '~/assets/icons/esg/audit-social.svg?component';
import EsgMobileMoney from '~/assets/icons/esg/mobile-money.svg?component';
import EsgTaxonomieUemoa from '~/assets/icons/esg/taxonomie-uemoa.svg?component';
import EsgSgesBetaSeal from '~/assets/icons/esg/sges-beta-seal.svg?component';
import type { IconSize, IconVariant, EsgIconName } from './registry';

interface EsgIconProps {
  name: EsgIconName;
  size?: IconSize;
  variant?: IconVariant;
  decorative?: boolean;
  strokeWidth?: number;
  class?: string;
}

const props = withDefaults(defineProps<EsgIconProps>(), {
  size: 'md',
  variant: 'default',
  decorative: false,
  strokeWidth: 2,
});

const ICON_MAP: Record<EsgIconName, Component> = {
  'chevron-down': ChevronDown,
  'chevron-up': ChevronUp,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  check: Check,
  x: X,
  calendar: Calendar,
  clock: Clock,
  'alert-circle': AlertCircle,
  'alert-triangle': AlertTriangle,
  info: Info,
  'check-circle': CheckCircle2,
  'x-circle': XCircle,
  loader: Loader2,
  search: Search,
  plus: Plus,
  minus: Minus,
  edit: Edit,
  trash: Trash2,
  eye: Eye,
  'eye-off': EyeOff,
  download: Download,
  upload: Upload,
  'file-text': FileText,
  link: Link,
  'external-link': ExternalLink,
  'esg-effluents': EsgEffluents,
  'esg-biodiversite': EsgBiodiversite,
  'esg-audit-social': EsgAuditSocial,
  'esg-mobile-money': EsgMobileMoney,
  'esg-taxonomie-uemoa': EsgTaxonomieUemoa,
  'esg-sges-beta-seal': EsgSgesBetaSeal,
};

const SIZE_MAP: Record<IconSize, number> = {
  xs: 12, sm: 16, md: 20, lg: 24, xl: 32,
};

const VARIANT_MAP: Record<IconVariant, string> = {
  default: 'text-current',
  brand: 'text-brand-green dark:text-brand-green',
  danger: 'text-brand-red dark:text-brand-red',
  success: 'text-verdict-pass dark:text-verdict-pass',
  muted: 'text-surface-text/60 dark:text-surface-dark-text/60',
};

// L25 §4sexies généralisée : fallback warn dev-only strippé en prod
if (import.meta.env.DEV && !(props.name in ICON_MAP)) {
  console.warn(`[EsgIcon] Unknown icon name: "${props.name}". Falling back to placeholder.`);
}

const PlaceholderIcon: Component = {
  render() {
    return h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 2,
    }, [
      h('circle', { cx: 12, cy: 12, r: 10 }),
      h('line', { x1: 4.93, y1: 4.93, x2: 19.07, y2: 19.07 }),
    ]);
  },
};

const resolvedComponent = computed<Component>(() => ICON_MAP[props.name] ?? PlaceholderIcon);
const pixelSize = computed(() => SIZE_MAP[props.size]);
const variantClass = computed(() => VARIANT_MAP[props.variant]);
const finalClass = computed(() => [variantClass.value, props.class].filter(Boolean).join(' '));

// L24 §4quinquies : ARIA attribute-strict valeurs littérales
const ariaAttrs = computed(() =>
  props.decorative
    ? { 'aria-hidden': 'true' as const }
    : { role: 'img' as const, 'aria-label': props.name },
);
</script>

<template>
  <component
    :is="resolvedComponent"
    v-bind="ariaAttrs"
    :class="finalClass"
    :size="pixelSize"
    :stroke-width="strokeWidth"
  />
</template>
```

### 4. Ancrage leçons héritées (27 → 30 leçons post-10.21)

| Leçon | Source | Applicabilité 10.21 | AC cible |
|-------|--------|---------------------|----------|
| **§4ter.bis Pattern A DOM observable** | 10.17+ | Partielle (icônes non-interactives) : `getByRole('img', {name})` + `querySelector('[aria-hidden="true"]')` | AC7 tests a11y |
| **§4ter.bis Pattern B count runtime Storybook** | 10.17+ | Directe : `jq` count `ui-esgicon--*` ≥ 12 | AC10 Task 9.3 |
| **§4ter.bis piège #26 count sans build** | 10.17 | Directe : exiger build OBLIGATOIRE avant jq | Task 9.3 |
| **L20 §4quater Écarts vs spec Completion Notes** | 10.18 | Directe : Task 9.5 § ajustements | Task 9.5 |
| **L21 §4quater Tests observables ≠ smoke** | 10.18 | Directe AC7 : `toBe('true')` strict vs `toHaveAttribute()` | Task 6.2 |
| **L22 §4quinquies displayValue trigger** | 10.19 | N/A (pas de trigger popover) | — |
| **L23 §4quinquies lifecycle close reset** | 10.19 | N/A (pas de state interne) | — |
| **L24 §4quinquies ARIA attribute-strict** | 10.19 | **Directe AC7** : `toBe('img')` + `toBe('true')` + `toBeNull()` strict | Task 6.2 |
| **L25 §4sexies Wrapper Reka UI id custom = code mort** | 10.20 | **Généralisée AC5** : dispatcher ne double-déclare pas props Lucide natives (piège #46) | Task 5, piège #46 |
| **L26 §4sexies Délégation per-path pas globale** | 10.20 | **Directe Task 6.2** : `describe.skip + it.todo` par variant dark mode | Task 6.2 AC10 |
| **L27 §4sexies Ordonnancement pièges cross-story** | 10.20 | **Directe Task 1.7 + 8.6** : pièges #46-48 (pas #41+) + test continuité | Task 1.7, 8.8 |
| **10.8 CCC-9 frozen tuple** | 10.8 | **Directe Task 3** : 3 tuples ICON_SIZES/VARIANTS/NAMES | Task 3 |
| **10.15 HIGH-1 `.test-d.ts` typecheck bloquant** | 10.15 | **Directe Task 5.16** : ≥ 8 `@ts-expect-error` | AC4 |
| **10.15 HIGH-2 tokens darken AA** | 10.15 | **Directe AC6** : brand-green/brand-red post-darken via CSS currentColor | AC6 |
| **10.17 piège #26 count sans build** | 10.17 | Directe Task 9.3 | Task 9.3 |
| **10.19 H-5 coverage c8 instrumentée ≥ 85 %** | 10.19 | **Directe Task 9.9** : valeurs réelles pas fallback smoke | Task 9.9 |
| **10.6 shim pattern byte-identique** | 10.6 | **Directe AC9 + Task 7** : migration SVG inline → EsgIcon dimensions héritées | AC9, Task 7 |

### 5. Risques identifiés + Mitigation

| Risque | Sévérité | Probabilité | Mitigation | Owner |
|--------|----------|-------------|------------|-------|
| **Lucide peer conflict Vue 3.4+ / Nuxt 4.4+** | MOYEN | Faible (Lucide stable ^0.400) | Task 2.2 `npm ls lucide-vue-next` check 0 conflict + CI green avant merge | Dev |
| **Bundle Lucide > 50 KB (tree-shaking raté)** | HAUT | Faible (named imports enforced) | Task 9.4 mesure EXACTE delta + grep tree-shaking effectif + piège #47 CI check | Dev |
| **Nuxt 4 SVG loader `?component` non configuré** | MOYEN | Modérée | Task 1.8 audit + Task 2.5 conditional install `vite-svg-loader` | Dev |
| **Migration SVG inline casse layout flex primitives** | HAUT | Faible (shim 10.6 maîtrisé) | AC9 Task 7.7 snapshot Storybook avant/après + dimensions `class` parent préservées | Dev |
| **Tests primitives 10.15-10.20 régressent (SVG-path assertions)** | MOYEN | Modérée | Task 7.5 + 7.6 refacto assertion agnostique via `findComponent(EsgIcon)` | Dev |
| **SVG custom ESG mal optimisés (metadata résiduelle)** | BAS | Modérée | Task 4.8 SVGO + Task 4.9 scan hex 0 hit | Dev |
| **Fallback warn non-strippé en prod (bloat)** | MOYEN | Faible (Vite DCE standard) | AC5 Task 5.7 `import.meta.env.DEV` + test `grep "Unknown icon" .nuxt/dist → 0 hit prod build` | Dev |
| **Coverage c8 < 85 % (branches fallback warn + placeholder)** | MOYEN | Modérée | Task 9.9 + tests case `fallback-unknown-name-warns-dev` couvre branche | Dev |

### 6. Ordre recommandé d'exécution (≈ 1 h)

1. **Task 1 (Scan baseline)** — 5 min — vérifier 0 hit + consigner 5 chiffres baseline (tests/typecheck/Storybook/bundle/SVG inline).
2. **Task 2 (Install Lucide + SVG loader)** — 5-10 min — dépendance runtime + validation tree-shaking.
3. **Task 3 (Registry CCC-9)** — 10 min — 3 tuples + tests registry 6 vert.
4. **Task 4 (SVG custom ESG)** — 10-15 min — 6 SVG convention Lucide + SVGO optimisation (peut être fait en parallèle Task 5).
5. **Task 5 (EsgIcon.vue + .test-d.ts)** — 15 min — dispatcher + ≥ 8 `@ts-expect-error` vert.
6. **Task 6 (Tests behavior + a11y)** — 10 min — ≥ 12 tests behavior + ≥ 6 tests a11y + L24 L26 appliquées.
7. **Task 7 (Migration ≥ 15 SVG inline)** — 10 min — shim pattern byte-identique + 0 régression tests primitives.
8. **Task 8 (Stories + Docs CODEMAPS + methodology §4septies)** — 10 min — ≥ 12 stories + §3.9 + §5 pièges #46-48 + §4septies retrospective.
9. **Task 9 (Scan final + validation)** — 5 min — count runtime + bundle delta + commit final.

**Total estimé** : **1 h 15** (10 min marge). Si coverage < 85 %, ajouter 10 min pour tests complémentaires (branche fallback + variants + class merge).

### 7. Dépendances et livrables aval Phase 1+

| Consommateur futur | Epic | Usage EsgIcon |
|--------------------|------|---------------|
| **FundApplicationLifecycleBadge** | 9 | `<EsgIcon name="loader" />` (état in_progress) + `<EsgIcon name="check-circle" variant="success" />` (submitted) + `<EsgIcon name="x-circle" variant="danger" />` (rejected) |
| **ComplianceBadge** | 10 | `<EsgIcon name="check-circle" variant="success" />` (verdict pass) + `<EsgIcon name="x-circle" variant="danger" />` (fail) + `<EsgIcon name="alert-triangle" />` (reported) |
| **ReferentialComparisonView** | 10 | `<EsgIcon name="esg-taxonomie-uemoa" />` colonne UEMOA + `<EsgIcon name="esg-biodiversite" />` critères E |
| **ProjectStatusPill** | 11 | `<EsgIcon name="clock" />` draft + `<EsgIcon name="check" variant="brand" />` ready + `<EsgIcon name="eye" />` published |
| **PackFacadeSelector** | 11 | `<EsgIcon name="esg-sges-beta-seal" variant="brand" />` sceau BETA |
| **DashboardStatCard** | 12 | `<EsgIcon name="download" />` export + `<EsgIcon name="upload" />` import + variants dynamiques |
| **AdminArbitrageCard** | 19 | `<EsgIcon name="alert-circle" variant="danger" />` criticity critical + `<EsgIcon name="info" />` moyen |
| **NotificationToast** | 20 | variants `success`/`danger`/`info` via `EsgIcon` mapping cohérent |
| **MobileMoneyConnector** | Phase 2 | `<EsgIcon name="esg-mobile-money" variant="brand" />` onboarding PME |
| **AuditSocialReport** | Phase 2 | `<EsgIcon name="esg-audit-social" />` entête rapport |
| **EffluentsCalculator** | Phase 2 | `<EsgIcon name="esg-effluents" />` label calculateur |

**Principe** : **aucune modification `EsgIcon.vue`** pour ajouter un consommateur. Extension = déposer SVG dans `assets/icons/esg/` + ligne registry + import `ICON_MAP`. **0 coupling architectural** consommateur → EsgIcon (prop `name` literal union type-safe + fallback warn = découverte immédiate).

### Project Structure Notes

- Alignment avec Nuxt 4 : `app/components/ui/EsgIcon.vue` auto-import global `<EsgIcon>` via `pathPrefix: false` (CLAUDE.md §Frontend Nuxt 4).
- Alignment avec CCC-9 frozen tuple : 7ᵉ extension `registry.ts` (10.8 + 10.14 + 10.15 + 10.16 + 10.17 + 10.18 + 10.19 + 10.20 + 10.21) — pattern rodé.
- Alignment avec §Reutilisabilite CLAUDE.md : dispatcher centralise 30+ icônes en 1 composant (vs 30+ composants séparés ou 17+ SVG inline dupliqués).
- Alignment avec §Dark Mode OBLIGATOIRE : 5 variants × 2 tokens (light/dark) = 10 occurrences `dark:` minimum dans VARIANT_MAP.
- Alignment avec §Conventions Français : prop `decorative` en anglais (API technique), labels utilisateur FR laissés aux consommateurs (`aria-label={name}` où `name` reste kebab-case anglais cohérent Lucide).

### References

- [Source: `_bmad-output/planning-artifacts/epics/epic-10.md#Story-10.21`] — AC1-AC8 epic (décliné en 10 AC story).
- [Source: `_bmad-output/implementation-artifacts/10-20-ui-datepicker-wrapper-reka-ui.md`] — patterns §4sexies 10.20 + CCC-9 + tests baseline.
- [Source: `docs/CODEMAPS/ui-primitives.md#§5-pièges`] — #45 actuel + #46-#48 à ajouter 10.21.
- [Source: `docs/CODEMAPS/methodology.md#§4sexies-post-review-10.20`] — leçons 25-27 cumulées + §4septies à créer 10.21.
- [Source: `frontend/app/components/ui/registry.ts`] — 6 extensions CCC-9 existantes (réutilisation byte-identique).
- [Source: Lucide docs `https://lucide.dev/guide/packages/lucide-vue-next`] — tree-shaking named imports ^0.400+.
- [Source: `@internationalized/date`] — référentiel conventions ARIA Date Picker pour cohérence Calendar 10.20 (pas reprise directe 10.21 icônes).
- [Source: CLAUDE.md §Dark Mode OBLIGATOIRE + §Reutilisabilite + §Frontend Nuxt 4] — conventions projet.

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (BMAD dev-story skill pipeline)

### Debug Log References

### Completion Notes List

### File List
