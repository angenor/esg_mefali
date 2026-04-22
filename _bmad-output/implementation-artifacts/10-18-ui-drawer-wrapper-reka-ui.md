# Story 10.18 : `ui/Drawer.vue` wrapper Reka UI Dialog (variant side)

Status: ready-for-dev

> **Contexte** : 20ᵉ story Phase 4 et **4ᵉ primitive `ui/`** après Button 10.15 + Input/Textarea/Select 10.16 + Badge 10.17. **1ʳᵉ primitive `ui/` avec wrapper Reka UI** (vs natifs `<button>`/`<input>`/`<span>` précédents). Sizing **M** (~1 h) selon sprint-plan v2.
>
> Cette story livre `frontend/app/components/ui/Drawer.vue` — panneau latéral accessible fondation de **3 consommateurs Phase 1+** :
> 1. `SourceCitationDrawer` (FR71 Perplexity-style sources RAG) — 480 px desktop / fullscreen mobile — squelette livré 10.14 à migrer Phase 1 Epic 13.
> 2. `IntermediaryComparator` (Moussa Journey 2 — comparaison 2-3 intermédiaires côte à côte) — 560 px desktop / fullscreen mobile — Epic 15.
> 3. `PeerReviewThreadedPanel` (admin N2 GitHub PR-style review) — 480 px desktop / fullscreen mobile — Epic 19.
>
> **Drawer ≠ Modal** (distinction fondatrice issue leçon 10.14 HIGH-2) : drawer = **consultation contextuelle parallèle** (role="complementary"), pas dialogue modal bloquant (role="dialog"). L'utilisateur doit pouvoir parcourir le contenu du drawer tout en continuant à lire / interagir avec le contenu principal. Conséquences ARIA + focus + fermeture spécifiques documentées §2 Q1-Q5 + §4 pièges #27-#32.
>
> **État de départ — Reka UI + Reka ScrollArea déjà utilisés, pattern drawer natif pas encore wrappé** :
> - ✅ **Reka UI `^2.9.6` installé** (Story 10.14 · `frontend/package.json:30`). Exports `DialogRoot` / `DialogPortal` / `DialogContent` / `DialogOverlay` / `DialogClose` + `ScrollAreaRoot` / `ScrollAreaViewport` / `ScrollAreaScrollbar` / `ScrollAreaThumb` disponibles.
> - ✅ **2 usages préexistants de Reka UI Dialog/ScrollArea** : `frontend/app/components/gravity/SignatureModal.vue` (DialogRoot + center modal — **role="dialog"** conservé, c'est bien un modal) + `frontend/app/components/gravity/SourceCitationDrawer.vue` (squelette natif `<aside role="complementary">` + ScrollAreaRoot, **PAS Dialog** — consommateur futur de `ui/Drawer`).
> - ⚠️ **Leçon 10.14 HIGH-2 appliquée à l'envers dans SourceCitationDrawer squelette** : le squelette a été corrigé vers `<aside role="complementary">` natif (pas Dialog) pour respecter la sémantique drawer. Story 10.18 rétablit l'infra : `ui/Drawer.vue` wrap Reka UI DialogRoot (focus trap + Escape + overlay) **avec `role="complementary"` override + `aria-modal="false"`** (AC3 + piège #27). SourceCitationDrawer sera migré Phase 1 Epic 13 vers `<Drawer>` byte-identique.
> - ❌ **Aucun `ui/Drawer.vue` préexistant** — `frontend/app/components/ui/` contient 6 composants (Button 10.15 + Input/Textarea/Select 10.16 + Badge 10.17 + FullscreenModal brownfield + ToastNotification brownfield) + `registry.ts`. **Grep `Drawer` dans `app/components/ui/` → 0 hit**. Pas de collision.
> - ⚠️ **`FullscreenModal.vue` brownfield ≠ Drawer** — 62 lignes, pattern modal plein écran mobile (pas side panel desktop). Hors scope migration (conservé tel quel, pattern shim 10.6 appliqué).
> - ✅ **Tokens `@theme` livrés Story 10.14 + darkés 10.15 + soft-bg Badge 10.17** — `main.css` contient `surface-*` / `dark-card` / `dark-border` / `dark-hover` + `brand-green #047857` focus ring (AA post-darken 10.15). **Aucune modification main.css nécessaire**. Drawer consomme les surfaces existantes.
> - ✅ **Pattern CCC-9 frozen tuple** (10.8 + 10.14 + 10.15 + 10.16 + 10.17) — `registry.ts` déjà étendu 3 fois (Button 10.15 + Input/Form 10.16 + Badge 10.17). Extension byte-identique pour `DRAWER_SIDES` (4) + `DRAWER_SIZES` (3).
> - ✅ **Pattern compile-time enforcement `.test-d.ts`** (10.15 HIGH-1) — `vitest.config.ts typecheck.include: ['tests/**/*.test-d.ts']` déjà actif. Réutilisable byte-identique `Drawer.test-d.ts`.
> - ✅ **Pattern darken tokens AA 10.15** — focus ring Drawer utilise `brand-green #047857` (5,78:1 ✅ AA post-darken, cohérent Button).
> - ✅ **Pattern co-localisation stories 10.14+10.15** — `<Name>.stories.ts` à côté de `.vue` dans `components/ui/` (glob `frontend/.storybook/main.ts` déjà étendu `gravity/ + ui/`).
> - ✅ **Pattern leçons méthodologiques post-10.17** :
>   - **Pattern A (10.16 H-3 + capitalisé 10.17 Task 5)** : tests DOM observable pas state interne — assert `wrapper.find('[role="complementary"]').exists()`, `document.body.querySelector('[data-state="open"]')`, `attributes('aria-label')`, **JAMAIS** `wrapper.vm.isOpen`. **Enjeu particulier Drawer** : v-model:open → tester via mutation DOM (portal body-attached via Reka UI) pas ref.value.
>   - **Pattern B (10.16 M-3 + capitalisé 10.17 Task 7)** : **comptage runtime Storybook obligatoire via `jq '.entries | keys | length' storybook-static/index.json` AVANT Completion Notes**. Pas d'estimation a priori.
>   - **Pattern leçon 10.14 HIGH-2** : `role="complementary"` OVERRIDE (pas le `role="dialog"` Reka UI natif), `aria-modal="false"`, focus trap opt-in (pas default). Drawer consultatif ≠ Modal bloquant.
>   - **Pattern leçon 10.15 HIGH-2 (a11y runtime Storybook vs jest-axe happy-dom)** : pour vérifier contraste/ARIA avec portail, l'audit **Storybook `addon-a11y` runtime** est plus fiable que `vitest-axe` en happy-dom. Drawer portalisé via Reka UI DialogPortal → **Storybook a11y runtime prioritaire** pour AC10. `vitest-axe` conservé en plancher smoke DOM.
> - ✅ **Dépendance Epic 13** : `SourceCitationDrawer` squelette 10.14 = consommateur futur. Migration mécanique Phase 1 (remplacement `<aside role="complementary">...</aside>` par `<Drawer :open="isOpen" @update:open="..." side="right" size="md" title="Sources" role-override="complementary">...</Drawer>`). **Non bloquante** (10.18 livre l'infra, 13.x migre).
>
> **Livrable 10.18 — `ui/Drawer.vue` + stories + tests + docs + registry extension (~1 h)** :
>
> 1. **Extension `ui/registry.ts`** (pattern CCC-9) — ajouter 2 frozen tuples :
>    ```ts
>    export const DRAWER_SIDES = Object.freeze(['right', 'left', 'top', 'bottom'] as const);
>    export const DRAWER_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);
>    export type DrawerSide = (typeof DRAWER_SIDES)[number];
>    export type DrawerSize = (typeof DRAWER_SIZES)[number];
>    ```
>    Invariants : lengths 4/3 · `Object.isFrozen` · dédoublonné.
>
> 2. **Composant `frontend/app/components/ui/Drawer.vue`** (AC1-AC10) — wrapper Reka UI `<DialogRoot>` + `<DialogPortal>` + `<DialogOverlay>` + `<DialogContent>` avec **override ARIA `role="complementary"` + `aria-modal="false"`**, 4 positions `side`, 3 sizes `size` (320 / 480 / 560 px desktop), fullscreen auto `<md` (768 px), focus trap opt-in, 3 chemins de fermeture (Escape + overlay click + close button), `<ScrollAreaRoot>` intégrée, slots `#default` + `#header` + `#footer`.
>
> 3. **`frontend/app/components/ui/Drawer.stories.ts` co-localisée** (AC12) — CSF 3.0 avec matrice 4 sides × 2 sizes + états open/closed + DarkMode + A11yFocusTrap + Scroll Long Content + Mobile Fullscreen + Composed Examples (Source Citation, Intermediary Comparator, Peer Review). **Comptage runtime OBLIGATOIRE** (pattern B 10.17 piège #26) : `jq '.entries | keys | length' storybook-static/index.json` **AVANT Completion Notes**, plancher AC12 ≥ 16.
>
> 4. **Tests Vitest `frontend/tests/components/ui/`** (AC11) — 4 fichiers :
>    - `test_drawer_registry.test.ts` : lengths/frozen/dedup × 2 tuples (≥ 6 tests).
>    - `test_drawer_behavior.test.ts` : v-model:open + 3 chemins fermeture + Pattern A DOM-only + focus restoration (≥ 14 tests).
>    - `test_drawer_a11y.test.ts` : vitest-axe smoke + assertions `role="complementary"` + `aria-modal="false"` + `aria-labelledby` (≥ 6 audits).
>    - `test_no_hex_hardcoded_drawer.test.ts` : scan 0 hit.
>    - `Drawer.test-d.ts` : ≥ 10 `@ts-expect-error` sur `side` / `size` / props obligatoires (`title`).
>
> 5. **Documentation `docs/CODEMAPS/ui-primitives.md` §3.5 Drawer + pièges cumulés ≥ 32** (AC14) — 4 exemples Vue + §5 pièges 27-32 (≥ 26 → ≥ 32) + §2 arbo mise à jour + §6bis note drawer (pas nouvelle ligne contraste car surfaces identiques Badge/Button).
>
> 6. **Scan NFR66 post-dev** (AC1, AC11, AC12) : `rg '#[0-9A-Fa-f]{3,8}' Drawer.vue Drawer.stories.ts` → 0 hit · `rg ': any\b|as unknown' Drawer.vue` → 0 hit · vitest baseline 555 → ≥ 569 (+14 minimum) · typecheck 40 → ≥ 50 (+10 minimum) · Storybook runtime ≥ 16 stories `ui-drawer--*`.

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité PME persona mobile + admin N2 arbitrage peer-review + Moussa Journey comparaison intermédiaires),
**Je veux** un composant `frontend/app/components/ui/Drawer.vue` wrapper typé strict de Reka UI `<DialogRoot>` qui **override la sémantique ARIA** (`role="complementary"` au lieu de `role="dialog"`, `aria-modal="false"` au lieu de `"true"`) pour matérialiser le pattern **drawer consultatif parallèle** — permettant à l'utilisateur de parcourir une information contextuelle (sources RAG FR71, fiches comparatives intermédiaires, threads peer-review admin) **tout en continuant à lire** le contenu principal sans blocage modal — avec 4 positions (`right` default / `left` / `top` / `bottom`), 3 tailles desktop (`sm` 320 px / `md` 480 px / `lg` 560 px), **fullscreen automatique mobile `<md` 768 px** (préservation règle tap-target + contexte mobile natif iOS/Android sheet), **focus trap opt-in** (pas default — drawer doit permettre navigation DOM externe sauf si formulaire critique), 3 chemins de fermeture composables indépendamment (Escape / overlay click / close button), ScrollArea Reka UI intégrée pour contenu scrollable, WCAG 2.1 AA validé par Storybook `addon-a11y` **runtime** (pas jest-axe happy-dom — leçon 10.15 HIGH-2 portail Teleport), dark mode ≥ 8 variantes `dark:` (overlay + surface + border + close button states), compile-time enforcement `Drawer.test-d.ts` bloquant les combinaisons invalides (`side` hors union, `size` hors union, `title` manquant — requis pour aria-labelledby),
**Afin que** les 3 consommateurs futurs Phase 1+ (`SourceCitationDrawer` Epic 13 · `IntermediaryComparator` Epic 15 · `PeerReviewThreadedPanel` Epic 19) partagent une base ARIA + responsive + dark mode cohérente, que le pattern drawer consultatif vs modal bloquant soit **enforcé architecturalement** au lieu de reposer sur une convention (leçon 10.14 HIGH-2 évite récurrence ambiguïté dialog/complementary), et que les migrations brownfield (aucune Phase 0, `SourceCitationDrawer` squelette 10.14 migré Epic 13) soient mécaniques à coût 0.

## Acceptance Criteria

**AC1 — Signature TypeScript strict + wrapper Reka UI DialogRoot**
**Given** `frontend/app/components/ui/Drawer.vue`,
**When** auditée,
**Then** elle utilise Vue 3 `<script setup lang="ts">` avec Composition API,
**And** importe `DialogRoot`, `DialogPortal`, `DialogOverlay`, `DialogContent`, `DialogClose` depuis `'reka-ui'`,
**And** expose :
```ts
interface DrawerProps {
  open: boolean;                       // v-model:open (two-way binding)
  title: string;                       // aria-labelledby obligatoire (AC3)
  description?: string;                // aria-describedby optionnel
  side?: DrawerSide;                   // default 'right'
  size?: DrawerSize;                   // default 'md' (480 px)
  trapFocus?: boolean;                 // default false (Q4 verrouillée)
  closeOnEscape?: boolean;             // default true
  closeOnOverlayClick?: boolean;       // default true
  showCloseButton?: boolean;           // default true
}
interface DrawerEmits {
  (e: 'update:open', value: boolean): void;
}
```
**And** aucune `any` / `as unknown` dans `Drawer.vue` (`rg ': any\b|as unknown' frontend/app/components/ui/Drawer.vue` → 0 hit),
**And** `cd frontend && npm run build` (Nuxt type-check) passe sans erreur,
**And** `Drawer.test-d.ts` contient **≥ 10 assertions `@ts-expect-error`** vérifiant que les combinaisons invalides (`side: 'invalid'`, `size: 'xl'`, `title` manquant, `trapFocus: 'yes'`, `open: 'true'`) ne compilent PAS,
**And** `npm run test:typecheck` (baseline 40 post-10.17) retourne **≥ 50 assertions typecheck** (+10 minimum).

**AC2 — Registry CCC-9 frozen tuple × 2 extensions**
**Given** `frontend/app/components/ui/registry.ts`,
**When** auditée,
**Then** elle contient **2 nouveaux exports** :
- `DRAWER_SIDES` (length `=== 4`, valeurs `'right'` / `'left'` / `'top'` / `'bottom'` dans cet ordre canonique),
- `DRAWER_SIZES` (length `=== 3`, valeurs `'sm'` / `'md'` / `'lg'`),

**And** les 2 tuples satisfont `Object.isFrozen(tuple) === true`,
**And** les 2 tuples sont dédoublonnés (`new Set(tuple).size === tuple.length`),
**And** les 2 types dérivés `DrawerSide` / `DrawerSize` sont exportés via `typeof TUPLE[number]`,
**And** les exports **préexistants** 10.15/10.16/10.17 (`BUTTON_VARIANTS`, `BUTTON_SIZES`, `INPUT_TYPES`, `FORM_SIZES`, `TEXTAREA_DEFAULT_MAX_LENGTH`, `VERDICT_STATES`, `LIFECYCLE_STATES`, `ADMIN_CRITICALITIES`, `BADGE_SIZES`, `VERDICT_LABELS_FR`, `LIFECYCLE_LABELS_FR`, `ADMIN_LABELS_FR`, `BadgeProps`) sont **inchangés byte-identique** (`git diff` restreint aux ajouts).

**AC3 — ARIA override `role="complementary"` + `aria-modal="false"` (leçon 10.14 HIGH-2 appliquée)**
**Given** `<Drawer>` ouvert (open="true"),
**When** inspecté dans le DOM (portalisé via Reka UI DialogPortal),
**Then** l'élément DialogContent porte explicitement :
- **`role="complementary"`** (override du `role="dialog"` par défaut Reka UI — drawer = consultation parallèle, pas modal bloquant),
- **`aria-modal="false"`** (permet l'interaction DOM externe — l'utilisateur peut scroller / cliquer le contenu principal pendant que le drawer est ouvert),
- **`aria-labelledby="{titleId}"`** pointant vers le `<h2 id="{titleId}">` du header (Reka UI `useId()` ou `useId` Vue 3 — génère ID stable SSR-safe),
- **`aria-describedby="{descId}"`** pointant vers le bloc description si prop `description` fournie (optionnel),

**And** le `<DialogOverlay>` est présent mais **NE bloque pas les clics externes** (CSS `pointer-events: none` sur le main content est **PAS appliqué** — piège #27),
**And** un test `test_drawer_a11y.test.ts` assert via `document.body.querySelector('[role="complementary"]')` l'existence de l'élément + `.getAttribute('aria-modal') === 'false'` + `.getAttribute('aria-labelledby')` non-null (Pattern A DOM-only),
**And** **aucun test n'utilise `wrapper.vm.*`** pour vérifier l'override (Pattern A leçon 10.16 H-3 + capitalisation 10.17).

**AC4 — `v-model:open` two-way binding fonctionnel**
**Given** un composant parent utilisant `<Drawer v-model:open="isOpen" title="Test">...</Drawer>`,
**When** `isOpen` passe `false → true` dans le parent,
**Then** le DialogContent est monté dans le body (portal Reka UI) + `<DialogOverlay>` visible,
**And** quand l'utilisateur clique le close button / presse Escape / clique l'overlay, l'évènement `update:open` est émis avec payload `false`,
**And** le parent observe `isOpen === false` après le tick Vue,
**And** un test `test_drawer_behavior.test.ts` vérifie via **mutations DOM portal body-attached** (Pattern A) :
```ts
await mount(Parent, { props: { initialOpen: false } });
expect(document.body.querySelector('[role="complementary"]')).toBeNull();
await wrapper.setProps({ initialOpen: true });
await nextTick();
expect(document.body.querySelector('[role="complementary"]')).not.toBeNull();
```
**And** **aucune assertion `wrapper.vm.open`** ou manipulation directe de state interne (Pattern A enforcé).

**AC5 — 3 chemins de fermeture composables (Escape + overlay click + close button)**
**Given** `<Drawer>` ouvert avec props default (`closeOnEscape: true`, `closeOnOverlayClick: true`, `showCloseButton: true`),
**When** l'utilisateur :
1. presse `Escape` → `update:open` émis avec `false` (géré par Reka UI DialogRoot natif),
2. clique le `<DialogOverlay>` → `update:open` émis avec `false` (géré par Reka UI natif),
3. clique le `<button aria-label="Fermer le panneau">` dans le header (DialogClose Reka UI) → `update:open` émis avec `false`,

**Then** chaque chemin ferme le drawer indépendamment,
**And** quand `closeOnEscape: false`, Escape ne ferme **PAS** (test `test_drawer_behavior.test.ts` case `escape-disabled`),
**And** quand `closeOnOverlayClick: false`, click overlay ne ferme **PAS** (test case `overlay-click-disabled`),
**And** quand `showCloseButton: false`, aucun bouton fermeture rendu (test case `no-close-button` + scan DOM `querySelector('button[aria-label="Fermer le panneau"]')` → null),
**And** **au moins 1 chemin de fermeture reste disponible** si le consommateur désactive les 3 (runtime `console.warn` en dev — defense-in-depth) — piège #32 documenté.

**AC6 — Mobile fullscreen automatique `<md` breakpoint (768 px)**
**Given** viewport `< 768 px` (mobile/sm-breakpoint Tailwind),
**When** `<Drawer size="sm|md|lg" side="right">` est rendu,
**Then** quelle que soit la valeur `size`, la largeur passe à `100vw` ET la hauteur à `100vh` (fullscreen natif cohérent pattern iOS/Android sheet),
**And** l'animation slide-in bascule sur `translate-y-full` (bottom-up) au lieu de `translate-x-full` (right-slide) pour cohérence UX mobile native (pattern bottom-sheet),
**And** les props `size` + `side` sont **ignorées** en viewport mobile (documenté §3.5 codemap + piège #29),
**And** **viewport `>= 768 px`** respecte `size` (320 / 480 / 560 px) + `side` (right / left / top / bottom),
**And** un test `test_drawer_behavior.test.ts` case `mobile-fullscreen` vérifie via `window.matchMedia('(min-width: 768px)')` mock + classList scan sur le DialogContent : `'w-full h-full'` actif en `< 768`, `'w-[480px] h-full'` actif en `>= 768` (md default).

**AC7 — 3 sizes desktop `sm` (320) / `md` (480) / `lg` (560)**
**Given** viewport `>= 768 px` desktop,
**When** chaque size rendu avec `side="right"`,
**Then** les largeurs exactes sont :
- `sm` → `w-[320px]` (drawer compact, usage filtre / panneau latéral info courte),
- `md` → `w-[480px]` (default, usage SourceCitationDrawer / PeerReviewThreadedPanel),
- `lg` → `w-[560px]` (usage IntermediaryComparator — comparaison 2-3 colonnes intermédiaires),

**And** pour `side="left"` : mêmes largeurs, position `left-0` au lieu de `right-0`,
**And** pour `side="top"` / `side="bottom"` : hauteurs 320/480/560 + `w-full` + position haute/basse,
**And** **aucune size desktop ne dépasse 50 vw desktop** (garde-fou UX — si `lg` = 560 px et viewport = 1000 px alors 56% largeur, acceptable ; si < 1120 px, fallback fullscreen via `max-w-[50vw]` ou `w-[min(560px,50vw)]`) — piège #30 documenté,
**And** un test assert `wrapper.find('[role="complementary"]').classes()` contient `w-[320px]` pour `sm`, `w-[480px]` pour `md`, `w-[560px]` pour `lg` (viewport desktop mocké `>= 768`).

**AC8 — Focus trap **opt-in** via prop `trapFocus` default `false` (différence drawer vs modal)**
**Given** `<Drawer open="true" trapFocus="false">...</Drawer>` (default),
**When** l'utilisateur presse `Tab` dans le drawer,
**Then** le focus **PEUT quitter le drawer** (navigation DOM externe autorisée) — Reka UI DialogRoot Child `<DialogContent :trapFocus="false">` ou équivalent prop passé,
**And** quand `trapFocus="true"`, focus trap Reka UI natif actif (Tab cycle dans le drawer uniquement),
**And** le focus initial à l'ouverture est sur le close button (premier focusable — cohérent SignatureModal) OU sur `[data-autofocus]` si présent dans le slot #header/#default (override consommateur),
**And** à la fermeture, focus restauré sur le déclencheur (gestion Reka UI natif via FocusTrap sous-jacent),
**And** un test `test_drawer_behavior.test.ts` case `focus-trap-disabled` vérifie que `document.activeElement` peut matcher un élément hors `[role="complementary"]` après Tab (Pattern A — test effet observable),
**And** un test `test_drawer_behavior.test.ts` case `focus-trap-enabled` vérifie que `document.activeElement` reste dans le drawer après 3 Tab consécutifs.

**AC9 — Dark mode ≥ 8 `dark:` variantes (overlay + surface + border + close button states)**
**Given** la classe `dark` appliquée sur `<html>`,
**When** `<Drawer>` rendu en dark mode,
**Then** le fichier `Drawer.vue` contient **≥ 8 occurrences `dark:`** rattachées à des axes visuels réels :
- `dark:bg-dark-card` sur le DialogContent (surface drawer),
- `dark:border-dark-border` sur les séparateurs header/footer,
- `dark:text-surface-dark-text` sur titre + description,
- `dark:text-surface-dark-text/70` sur description (atténué lisible),
- `dark:bg-black/70` sur DialogOverlay (overlay dark plus sombre),
- `dark:hover:bg-dark-hover` sur close button hover,
- `dark:text-surface-dark-text` sur close button default,
- `dark:focus-visible:ring-brand-green` sur close button focus (même token `#047857` post-darken 10.15 AA),

**And** contraste texte/fond dark mode ≥ 4,5:1 (WCAG 1.4.3 AA) validé par **1 audit Storybook addon-a11y runtime** en mode dark (AC10) — PAS vitest-axe happy-dom seul (portail + dark CSS var non matérialisés de façon fiable, leçon 10.15 HIGH-2),
**And** **aucune inflation artificielle** (pattern 10.15 MEDIUM-2 exception) — les `dark:` sont rattachées à des axes visuels réels (overlay + surface + border + 2 textes + 3 états close button = 8 minimum cohérent).

**AC10 — A11y WCAG 2.1 AA : 0 violation Storybook addon-a11y **runtime** + vitest-axe smoke**
**Given** les stories `ui-drawer--*` buildées en `storybook-static`,
**When** `npm run storybook:test` (test-runner Storybook avec addon-a11y runtime) exécuté en CI,
**Then** **0 violation WCAG 2.1 AA** sur les 16+ stories Drawer (role, aria-*, contraste, focus-visible, keyboard navigation),
**And** un test `test_drawer_a11y.test.ts` vitest-axe en **smoke DOM** (les limites happy-dom Teleport/portail documentées §5 codemap piège #28) vérifie :
1. `role="complementary"` présent (`document.body.querySelector('[role="complementary"]')`),
2. `aria-modal="false"` présent,
3. `aria-labelledby` pointe sur un ID non-null qui existe dans le DOM (`document.getElementById(id)` non-null + `.textContent === props.title`),
4. `vitest-axe.toHaveNoViolations()` sur les configurations qui fonctionnent en happy-dom (portail résolu par Reka UI DialogPortal → `document.body` accessible),

**And** la couverture portail-dépendante (focus trap runtime, keyboard navigation, animation slide) est **déléguée explicitement à Storybook runtime** — documenté §5 codemap piège #28 (capitalisation leçon 10.15 HIGH-2),
**And** **AUCUN masquage sélectif** de règles axe-core (`color-contrast` reste activé côté Storybook — seul happy-dom désactive faute de layout CSS complet).

**AC11 — Tests Vitest ≥ 14 nouveaux + baseline 555 → ≥ 569**
**Given** `frontend/tests/components/ui/test_drawer_*.test.ts` (4 fichiers + 1 `.test-d.ts`),
**When** `cd frontend && npm run test` exécuté,
**Then** minimum **14 tests runtime nouveaux verts** répartis :
1. `test_drawer_registry.test.ts` : length × 2 tuples + `Object.isFrozen` × 2 + dedup × 2 + ordre canonique `DRAWER_SIDES[0] === 'right'` = **≥ 7 tests**,
2. `test_drawer_behavior.test.ts` : v-model:open × 2 (mount open/closed + toggle via setProps), 3 chemins fermeture × 4 cases (Escape enabled/disabled + overlay enabled/disabled + close button show/hide + fallback warn), focus-trap × 2 (enabled + disabled), mobile fullscreen × 2 (viewport mock `<md` + `>=md`), size × 3 (sm/md/lg classes), side × 4 (right/left/top/bottom position classes) = **≥ 17 tests**,
3. `test_drawer_a11y.test.ts` : 4 assertions ARIA (`role="complementary"` + `aria-modal="false"` + `aria-labelledby` + `aria-describedby` conditionnel) + 2 audits vitest-axe smoke (open default + open with description) = **≥ 6 tests**,
4. `test_no_hex_hardcoded_drawer.test.ts` : scan `Drawer.vue` + `Drawer.stories.ts` = **2 tests**,

**And** baseline 555 tests (post-10.17) → **≥ 569 passed** (+14 minimum, cible réaliste ≥ 32 avec 3 fichiers),
**And** typecheck baseline 40 (post-10.17) → **≥ 50 assertions** (`Drawer.test-d.ts` ≥ 10),
**And** **0 régression** sur tests préexistants (Pattern A DOM-only enforcé — aucun `wrapper.vm.*`),
**And** coverage `Drawer.vue` ≥ 85 % (plancher primitive wrapper — branches Reka UI déléguées mockées).

**AC12 — Storybook CSF 3.0 co-localisée — comptage runtime OBLIGATOIRE pré-Completion**
**Given** `frontend/app/components/ui/Drawer.stories.ts` co-localisée,
**When** `npm run storybook:build` exécuté,
**Then** `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length' storybook-static/index.json` est **capturé et consigné littéralement** dans la section « Completion Notes » du story file **AVANT** tout claim de complétude (pattern B 10.16 M-3 + capitalisation 10.17 piège #26),
**And** ce comptage doit être **≥ 16 stories nouvelles Drawer** (plancher conservateur couvrant : 4 sides × 2 sizes open-state = 8 + DarkMode × 4 sides = 4 + MobileFullscreen = 1 + FocusTrapEnabled = 1 + FocusTrapDisabled = 1 + LongScrollContent = 1 + AllClosingPathsDisabledWarn = 1 + ComposedSourceCitation + ComposedIntermediaryComparator + ComposedPeerReview = 3 ; soit **≥ 20 CSF exports réalistes**, plancher ≥ 16 avec docs autodocs),
**And** le glob `frontend/.storybook/main.ts` reste **inchangé** (déjà étendu `gravity/ + ui/` Story 10.15),
**And** le bundle `storybook-static/` reste **≤ 15 MB** (budget 10.14 préservé).

**AC13 — `<ScrollArea>` Reka UI intégrée pour contenu scrollable**
**Given** `<Drawer>` avec contenu dépassant la hauteur du drawer (> `100vh - header - footer`),
**When** l'utilisateur scrolle dans le drawer,
**Then** la zone scrollable est wrappée dans `<ScrollAreaRoot>` + `<ScrollAreaViewport>` + `<ScrollAreaScrollbar orientation="vertical">` + `<ScrollAreaThumb>` (cohérent pattern SourceCitationDrawer squelette + ImpactProjectionPanel 10.14),
**And** le header (slot `#header` OU titre + close button default) reste **sticky top**,
**And** le footer (slot `#footer` optionnel) reste **sticky bottom** si présent,
**And** **la scrollbar native `<body>` reste utilisable** (drawer ne verrouille pas le body scroll — cohérent role="complementary" AC3 — piège #27) SAUF si `trapFocus="true"` (consommateur form critique) qui peut implémenter son propre lock via emit,
**And** un test `test_drawer_behavior.test.ts` case `scroll-area-rendered` assert `wrapper.find('[data-reka-scroll-area-root]').exists() === true` (ou fallback `.scroll-area-root` selon Reka UI DOM),
**And** styles scrollbar : `w-2 bg-gray-200 dark:bg-dark-border` + thumb `bg-gray-400 dark:bg-dark-hover rounded` (pattern byte-identique SourceCitationDrawer l.139-140).

**AC14 — Documentation `docs/CODEMAPS/ui-primitives.md` §3.5 Drawer + ≥ 32 pièges cumulés**
**Given** `docs/CODEMAPS/ui-primitives.md`,
**When** auditée,
**Then** elle contient une nouvelle sous-section `### 3.5 ui/Drawer (Story 10.18)` avec **≥ 4 exemples Vue** :
1. Drawer right md default (SourceCitationDrawer usage Epic 13 — template migration byte-identique),
2. Drawer right lg avec focusTrap="true" (IntermediaryComparator usage Epic 15),
3. Drawer left sm avec slot #footer actions (filtres catalogue hypothétique),
4. Drawer avec viewport mobile fullscreen bottom (responsive showcase),
5. **Bonus** : exemple TypeScript `side` invalide (`@ts-expect-error`),

**And** §5 Pièges contient **≥ 32 pièges** cumulés (26 existants post-10.17 + 6 nouveaux Drawer détaillés §4 Dev Notes ci-dessous : #27 role="complementary" override vs Reka UI default dialog + aria-modal=false, #28 portail Teleport/DialogPortal happy-dom limitations vitest-axe → Storybook runtime, #29 mobile fullscreen breakpoint `<md` 768 px responsive-first, #30 ScrollArea cohérence tokens + max-w-50vw garde-fou large desktop, #31 overlay backdrop-filter blur perf mobile + pointer-events drawer consultatif, #32 Escape + beforeclose intercept — unsaved changes pattern),
**And** §2 Arborescence cible étendue avec `Drawer.vue` + `Drawer.stories.ts` + `Drawer.test-d.ts` + 3 fichiers tests,
**And** §6bis ou §6ter : ajout éventuel ligne token spécifique drawer **ou** pas de nouvelle entrée si les tokens consommés sont déjà documentés (surface-* brand-green post-darken),
**And** un test `test_docs_ui_primitives.test.ts` (existant 10.17) est **étendu** pour asserter présence §3.5 Drawer + ≥ 32 pièges + ≥ 4 exemples dans §3.5 (5 → 9 tests post-10.17 → **≥ 13 tests post-10.18**).

**AC15 — Baseline tests → cible +14 runtime + +10 typecheck + 0 régression + 2 commits traçabilité**
**Given** la baseline post-10.17,
**When** Story 10.18 est complétée,
**Then** :
- **Tests runtime** : 555 passed (1 pré-existant useGuidedTour failed hors scope) → **≥ 569 passed** (+14 minimum, cible réaliste 555 → 590+ avec 3 fichiers × ≥ 10 tests chacun),
- **Typecheck** : 40 passed → **≥ 50 assertions** (Drawer.test-d.ts ≥ 10),
- **Storybook runtime** : 168 entries → **≥ 184 entries** dont **≥ 16 `ui-drawer--*`** (mesure littérale pattern B),
- **Bundle Storybook** : ≤ 15 MB préservé (marge 7 MB post-10.17),
- **0 régression** sur les 555 tests verts + 40 typecheck post-10.17,
- **2 commits intermédiaires lisibles review** (leçon 10.8) :
  1. `feat(10.18): ui/Drawer primitive + registry CCC-9 2 tuples + role=complementary override`,
  2. `feat(10.18): Drawer stories CSF3 + tests behavior/a11y + docs CODEMAPS §3.5 + count runtime vérifié`.

## Tasks / Subtasks

- [ ] **Task 1 — Scan NFR66 préalable + baseline** (AC1, AC11)
  - [ ] 1.1 Grep `Drawer\.vue|DRAWER_SIDES|DRAWER_SIZES` sur `frontend/app/components/ui/` → attendu **0 hit** (hors FullscreenModal brownfield + SourceCitationDrawer gravity/).
  - [ ] 1.2 Baseline tests : `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner exact post-10.17 (555 attendu + 1 failed pré-existant useGuidedTour).
  - [ ] 1.3 Baseline typecheck : `npm run test:typecheck 2>&1 | tail -5` → consigner (40 attendu post-10.17 : 6 Button + 8 Input + 7 Select + 6 Textarea + 13 Badge).
  - [ ] 1.4 Collision brownfield : vérifier `NotificationBadge.vue` + `FullscreenModal.vue` + `SourceCitationDrawer.vue` (gravity/) ≠ `Drawer.vue` nom-distinct. Pas de migration Phase 0.
  - [ ] 1.5 Vérifier installation `reka-ui ^2.9.6` dans `frontend/package.json` + exports `DialogRoot`/`DialogPortal`/`DialogOverlay`/`DialogContent`/`DialogClose` disponibles via Node `node -e "console.log(Object.keys(require('reka-ui')).filter(k => k.startsWith('Dialog')))"`.

- [ ] **Task 2 — Registry `ui/registry.ts` extension** (AC2)
  - [ ] 2.1 Ajouter `DRAWER_SIDES = Object.freeze(['right', 'left', 'top', 'bottom'] as const)` (ordre canonique `right` default first).
  - [ ] 2.2 Ajouter `DRAWER_SIZES = Object.freeze(['sm', 'md', 'lg'] as const)`.
  - [ ] 2.3 Types dérivés `DrawerSide` / `DrawerSize` via `typeof TUPLE[number]`.
  - [ ] 2.4 Docstring JSDoc référençant Story 10.18 + rationale ordre `right` first (piège #27 sémantique side-right par défaut comme SourceCitationDrawer/IntermediaryComparator/PeerReviewThreadedPanel).
  - [ ] 2.5 Exports 10.15+10.16+10.17 byte-identique préservés (diff `git diff frontend/app/components/ui/registry.ts` restreint aux ajouts).
  - [ ] 2.6 `npm run test:typecheck` → baseline 40 → attendu 40 (registry ne change pas typecheck count tant que Drawer.test-d.ts non ajouté — check Task 5.5).

- [ ] **Task 3 — Composant `ui/Drawer.vue`** (AC1, AC3-AC9, AC13)
  - [ ] 3.1 `<script setup lang="ts">` avec imports Reka UI + types registry + `useId` Vue 3 (génération ID stable SSR).
  - [ ] 3.2 `defineProps<DrawerProps>()` + `withDefaults` : `side: 'right'`, `size: 'md'`, `trapFocus: false`, `closeOnEscape: true`, `closeOnOverlayClick: true`, `showCloseButton: true`.
  - [ ] 3.3 `defineEmits<DrawerEmits>()` avec `(e: 'update:open', value: boolean): void`.
  - [ ] 3.4 `titleId` + `descId` via `useId()` — liés `aria-labelledby` + `aria-describedby` conditionnel.
  - [ ] 3.5 Computed `sideClasses` : map `side → { position, translate, anim-classes }` (right: `right-0 top-0 h-full translate-x-0`, left: `left-0 top-0 h-full`, top: `top-0 left-0 w-full`, bottom: `bottom-0 left-0 w-full`).
  - [ ] 3.6 Computed `sizeClasses` : map `size + side → { width OR height }` avec garde-fou `max-w-[50vw]` desktop large (piège #30).
  - [ ] 3.7 Computed `mobileClasses` : via `useMediaQuery('(min-width: 768px)')` OR CSS-only `md:` prefix — fallback `w-full h-full bottom-0` sur viewport `<md` (AC6 piège #29). **Préférence CSS-only** (pas de useMediaQuery composable — évite dépendance `@vueuse/core` si absente ; vérifier package.json ; fallback CSS Tailwind `md:w-[480px] md:h-full md:bottom-auto`).
  - [ ] 3.8 Template principal : `<DialogRoot :open="open" @update:open="$emit('update:open', $event)">` + `<DialogPortal>` + `<DialogOverlay class="fixed inset-0 bg-black/50 dark:bg-black/70 [prefers-reduced-motion:reduce]:transition-none">` + `<DialogContent :aria-labelledby="titleId" :aria-describedby="description ? descId : undefined">`.
  - [ ] 3.9 **Override ARIA** (piège #27 + AC3) : sur DialogContent ajouter `role="complementary"` + `aria-modal="false"` explicites (Reka UI DialogContent accepte les attributs HTML passés via attrs — sinon wrap le contenu dans un `<aside role="complementary" aria-modal="false">` enfant).
  - [ ] 3.10 Header avec slot `#header` (override consommateur) OU default : `<h2 :id="titleId">{{ title }}</h2>` + optionnel `<p :id="descId">{{ description }}</p>` + `<DialogClose v-if="showCloseButton" aria-label="Fermer le panneau">✕</DialogClose>`.
  - [ ] 3.11 Contenu scrollable wrappé dans `<ScrollAreaRoot>` + `<ScrollAreaViewport>` + scrollbar vertical (AC13 pattern SourceCitationDrawer byte-identique).
  - [ ] 3.12 Slot `#footer` optionnel sticky bottom avec `border-t border-gray-200 dark:border-dark-border`.
  - [ ] 3.13 Focus trap opt-in : passer `:trap-focus="trapFocus"` à Reka UI DialogContent (ou prop équivalent `<FocusTrap>` wrapper). **Vérifier API exacte Reka UI 2.9.6** : la prop peut être `disable-outside-pointer-events` + gestion manuelle trap — à confirmer via docs ou inspection `node_modules/reka-ui/dist/`.
  - [ ] 3.14 Close paths configurables : `:force-mount="true"` si besoin persistent mount, `@escape-key-down="closeOnEscape ? undefined : $event.preventDefault()"`, `@pointer-down-outside="closeOnOverlayClick ? undefined : $event.preventDefault()"`.
  - [ ] 3.15 Runtime defense-in-depth (dev only via `import.meta.env.DEV`) : si `!closeOnEscape && !closeOnOverlayClick && !showCloseButton` → `console.warn('[ui/Drawer] 3 chemins fermeture désactivés — risque utilisateur piégé. Au moins 1 doit rester actif.')`.
  - [ ] 3.16 `prefers-reduced-motion: reduce` : animation slide remplacée par fade opacity via classes Tailwind `motion-reduce:transition-none motion-reduce:animate-fade-in` (≤ 200 ms).
  - [ ] 3.17 Dark mode : `dark:bg-dark-card` surface + `dark:border-dark-border` séparateurs + `dark:text-surface-dark-text` textes + `dark:hover:bg-dark-hover` close button + `dark:bg-black/70` overlay + `dark:focus-visible:ring-brand-green` focus ≥ 8 occurrences (AC9).
  - [ ] 3.18 Scan hex `Drawer.vue` → **0 hit** (toutes couleurs via tokens @theme).
  - [ ] 3.19 `: any` / `as unknown` dans Drawer.vue → **0 hit**.
  - [ ] 3.20 **Commit intermédiaire 1** : `feat(10.18): ui/Drawer primitive + registry CCC-9 2 tuples + role=complementary override`.

- [ ] **Task 4 — `ui/Drawer.stories.ts` co-localisée** (AC12)
  - [ ] 4.1 `Drawer.stories.ts` CSF 3.0 meta `{ title: 'UI/Drawer', component: Drawer, tags: ['autodocs'], parameters: { layout: 'fullscreen', a11y: { config: {...} } } }`.
  - [ ] 4.2 Template parent wrapper : pattern consommateur avec `const isOpen = ref(false)` + bouton trigger visible par défaut (stories interactives).
  - [ ] 4.3 Stories matrice `side × size` (4 × 3 = 12 permutations avec `open: true` par default pour visibilité) — mais réalistes : **`SideRightSm` / `SideRightMd` / `SideRightLg` / `SideLeftMd` / `SideTopMd` / `SideBottomMd`** = 6 base stories.
  - [ ] 4.4 Story `DarkMode` avec decorator `html.classList.add('dark')` + side=right + size=md.
  - [ ] 4.5 Story `FocusTrapEnabled` (form critique simulé) + `FocusTrapDisabled` (consultation default).
  - [ ] 4.6 Story `LongScrollContent` avec ScrollArea — 50 paragraphes lorem pour montrer scrollbar Reka UI stylée.
  - [ ] 4.7 Story `MobileFullscreen` avec `parameters.viewport: { defaultViewport: 'iphone6' }`.
  - [ ] 4.8 Story `CloseOnEscapeDisabled` + `CloseOnOverlayClickDisabled` + `NoCloseButton` (3 cas isolés fermetures).
  - [ ] 4.9 Story `AllClosingPathsDisabledWarn` (console warn runtime défense) — documente le piège #32.
  - [ ] 4.10 3 stories composées consommateurs Phase 1+ :
    - `ComposedSourceCitation` (Epic 13 FR71 — Perplexity-style right md avec liste sources RAG).
    - `ComposedIntermediaryComparator` (Epic 15 Moussa — right lg avec 3 colonnes cards intermédiaires).
    - `ComposedPeerReviewThread` (Epic 19 admin N2 — right md avec thread GitHub PR-style).
  - [ ] 4.11 Helper `asStorybookComponent<T>()` réutilisé de `frontend/app/types/storybook.ts` (pas de `as unknown` — pattern 10.15 M-3).
  - [ ] 4.12 Play functions pour stories interactives : `CloseOnEscape`, `CloseOnOverlayClick`, `CloseOnButtonClick` — user-event Tab + Escape + click (Pattern A DOM-observable via `document.body.querySelector`).
  - [ ] 4.13 **Comptage runtime OBLIGATOIRE post-build Task 7.3** : `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length' storybook-static/index.json` — consigner EXACT avant Completion Notes (piège #26 capitalisé).

- [ ] **Task 5 — Tests Vitest** (AC11)
  - [ ] 5.1 `test_drawer_registry.test.ts` : 7 tests (length × 2 + frozen × 2 + dedup × 2 + `DRAWER_SIDES[0] === 'right'` canonical order × 1).
  - [ ] 5.2 `test_drawer_behavior.test.ts` : ≥ 17 tests **Pattern A DOM-only** (assertions via `document.body.querySelector('[role="complementary"]')` — Reka UI DialogPortal portalise sur body) :
    - v-model:open open/close toggle × 2 (initial + setProps),
    - Close paths × 4 cases Escape enabled/disabled + overlay click enabled/disabled + close button show/hide,
    - Runtime warn fallback 3 paths disabled × 1 (`vi.spyOn(console, 'warn')`),
    - Focus trap enabled/disabled × 2 cases,
    - Mobile fullscreen × 2 (viewport mock `matchMedia` OR classList scan),
    - Sizes × 3 (sm/md/lg classes présentes),
    - Sides × 4 (right/left/top/bottom position classes).
    - **Aucun `wrapper.vm.*`** (Pattern A enforcé strict).
  - [ ] 5.3 `test_drawer_a11y.test.ts` : 6 tests — 4 assertions ARIA (role/aria-modal/aria-labelledby/aria-describedby conditionnel) + 2 audits `vitest-axe.toHaveNoViolations()` smoke (open default + open with description). **Note explicite** : audits portail-dépendants (focus trap keyboard, animation) **délégués à Storybook runtime AC10** — documenté §5 codemap piège #28.
  - [ ] 5.4 `test_no_hex_hardcoded_drawer.test.ts` : 2 tests scan `Drawer.vue` + `Drawer.stories.ts` → 0 hit (hors commentaires stripés par `stripComments()` existant).
  - [ ] 5.5 `Drawer.test-d.ts` : **≥ 10 `@ts-expect-error` assertions** :
    - `side: 'invalid'` hors union,
    - `size: 'xl'` hors union,
    - `title` manquant (requis),
    - `trapFocus: 'yes'` (boolean requis),
    - `open: 'true'` (boolean requis),
    - `closeOnEscape: 1` (boolean requis),
    - `description: 123` (string requis),
    - `size: 'SM'` casse (minuscule requis),
    - `side: 'center'` (position invalide pour drawer — drawer est toujours bord),
    - `showCloseButton: null` (boolean strict pas null).
  - [ ] 5.6 `npm run test -- --run` → baseline 555 → **≥ 569 passed** (+14 minimum, cible réaliste ≥ 32 avec 3 fichiers).
  - [ ] 5.7 `npm run test:typecheck` → baseline 40 → **≥ 50 passed** (+10 minimum).

- [ ] **Task 6 — Documentation `docs/CODEMAPS/ui-primitives.md`** (AC14)
  - [ ] 6.1 `### 3.5 ui/Drawer (Story 10.18)` inséré entre §3.4 Badge et §4.
  - [ ] 6.2 4 exemples Vue numérotés + 1 bloc TypeScript union `@ts-expect-error` :
    1. Drawer right md default (SourceCitationDrawer Epic 13 migration template),
    2. Drawer right lg avec `trapFocus="true"` (IntermediaryComparator Epic 15),
    3. Drawer left sm avec slot #footer actions,
    4. Drawer mobile fullscreen (responsive showcase),
    5. `@ts-expect-error` sur `side: 'center'` invalide.
  - [ ] 6.3 Pièges §5 étendu 26 → **32 entrées** :
    - **#27 role="complementary" override vs Reka UI DialogContent default role="dialog"** — leçon 10.14 HIGH-2 capitalisée infra. `aria-modal="false"` conjoint. Impact : interaction DOM externe non-bloquée, screen reader annonce « panneau complémentaire » (pas « dialogue »). Solution : override explicite dans Drawer.vue sur le DialogContent + test DOM `getAttribute('role') === 'complementary'`.
    - **#28 Portail Teleport/DialogPortal happy-dom limitations → Storybook runtime prioritaire** — leçon 10.15 HIGH-2 capitalisée. vitest-axe en happy-dom ne matérialise pas de façon fiable les portails (Teleport to="body" + Reka UI DialogPortal). Solution : assertions DOM explicites via `document.body.querySelector` (Pattern A) + délégation audits contraste/focus runtime à Storybook addon-a11y test-runner. Ne pas désactiver sélectivement `color-contrast` — préférer test runtime.
    - **#29 Mobile fullscreen breakpoint `<md` 768 px responsive-first (pas `<sm` 640 px)** — Tailwind standard `md:768px`. Rationale : en dessous de 768 px, largeur drawer (320/480/560) saturerait ≥ 50 % viewport → UX dégradée. Solution : CSS-only Tailwind `w-full h-full bottom-0 md:w-[480px] md:h-full md:bottom-auto md:right-0` (pas useMediaQuery — évite hydration mismatch SSR). Piège : JSDOM tests happy-dom n'évaluent pas media queries par défaut → test via classList scan + `window.matchMedia` mock.
    - **#30 ScrollArea tokens cohérents + garde-fou `max-w-[50vw]` desktop ultra-large** — Reka UI ScrollArea styles scrollbar byte-identique SourceCitationDrawer (`w-2 bg-gray-200 dark:bg-dark-border` + thumb `bg-gray-400 dark:bg-dark-hover`). Piège : sur écran `>= 1920 px` avec `size="lg"` (560 px) = 29 % viewport OK. Sur écran 1000 px = 56 % NOT OK. Solution : `w-[min(560px,50vw)]` OR media query `2xl:w-[560px] xl:w-[min(560px,50vw)]`.
    - **#31 Overlay `backdrop-filter: blur()` perf mobile + `pointer-events` drawer consultatif** — Tentation d'ajouter `backdrop-blur-sm` sur DialogOverlay : **INTERDIT mobile** (GPU faible drain battery + repaint cascade). Pour `role="complementary"` + `aria-modal="false"` : overlay doit avoir `pointer-events: auto` uniquement si `closeOnOverlayClick: true` (sinon `pointer-events: none` pour permettre interaction DOM dessous). Piège : si overlay `pointer-events: none` + bouton derrière activable, l'utilisateur peut fermer involontairement via click sur main content. Solution : documenter clairement la sémantique drawer (parallèle non-bloquant).
    - **#32 Escape + beforeclose intercept (unsaved changes pattern Phase Growth)** — Si consommateur form critique (IntermediaryComparator = consultation pas form ; PeerReviewThreadedPanel = textarea threaded) a des modifications non sauvegardées, l'Escape ne doit pas fermer sans confirmation. Solution MVP : consommateur écoute `@update:open="handleClose"` et intercepte `if (hasUnsavedChanges && !confirm('Fermer sans sauvegarder ?')) return emit('update:open', true)`. Pas d'API `beforeClose` Phase 0 (deferred `DEF-10.18-1` si pattern > 2 fois).
  - [ ] 6.4 §2 Arborescence cible étendue (+4 lignes : Drawer.vue + Drawer.stories.ts + Drawer.test-d.ts + 3 tests).
  - [ ] 6.5 `test_docs_ui_primitives.test.ts` étendu : 9 → **≥ 13 tests** (§3.5 Drawer présent + ≥ 32 pièges + ≥ 4 exemples §3.5 + exemple TS @ts-expect-error présent).
  - [ ] 6.6 `docs/CODEMAPS/methodology.md` étendu : **section 4ter capitalisée « Application proactive Story 10.18 (ui/Drawer) »** — Pattern A + Pattern B + leçon 10.14 HIGH-2 (role complementary) + leçon 10.15 HIGH-2 (a11y runtime Storybook) appliqués **avant code review**, pas en réaction. Exemple : test_drawer_a11y.test.ts délègue explicitement portail contraint à runtime Storybook (pas de désactivation règle axe), ScrollArea styles byte-identique SourceCitationDrawer (pas de bikeshedding tokens), trap-focus default false (pas default true Reka UI). Mesure anti-récurrence : si un 3ᵉ pattern révélé post-code-review 10.18, créer §4quater.

- [ ] **Task 7 — Scan NFR66 post-dev + validation finale + comptage runtime Storybook (pattern B capitalisé)** (AC2, AC11, AC12, AC15)
  - [ ] 7.1 Scan hex `Drawer.vue` + `Drawer.stories.ts` + `registry.ts` diff → **0 hit** (hex dans commentaires docstring stripés par `stripComments()`).
  - [ ] 7.2 `: any\b` / `as unknown` dans `Drawer.vue` + `Drawer.test-d.ts` → **0 hit**.
  - [ ] 7.3 **Build Storybook + comptage runtime OBLIGATOIRE** (pattern B 10.16 M-3 + capitalisation 10.17 piège #26) :
    ```bash
    cd frontend && npm run storybook:build 2>&1 | tail -5
    jq '.entries | keys | length' storybook-static/index.json  # baseline 168 post-10.17
    jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length' storybook-static/index.json  # cible ≥ 16
    du -sh storybook-static  # ≤ 15 MB budget 10.14
    ```
    Consigner les 3 chiffres EXACTS dans Completion Notes **AVANT** tout claim de complétude.
  - [ ] 7.4 `cd frontend && npm run test -- --run 2>&1 | tail -5` → consigner : baseline 555 → ≥ 569 passed (+14 min, cible ≥ 32).
  - [ ] 7.5 `npm run test:typecheck 2>&1 | tail -5` → consigner : baseline 40 → ≥ 50 passed (+10 min).
  - [ ] 7.6 `grep -oE "dark:" frontend/app/components/ui/Drawer.vue | wc -l` → **≥ 8** (AC9 plancher + sans inflation — chaque classe rattachée à axe visuel réel).
  - [ ] 7.7 **Commit final 2** : `feat(10.18): Drawer stories CSF3 + tests behavior/a11y + docs CODEMAPS §3.5 + count runtime vérifié`.

- [ ] **Task 8 — Mini-retro leçons 10.18 pour 10.19 Combobox/Tabs**
  - [ ] 8.1 Section 4ter `methodology.md` étendue : Pattern A (DOM test via `document.body.querySelector` portal-aware) + Pattern B (count runtime) + leçon 10.14 HIGH-2 (ARIA override explicite) + leçon 10.15 HIGH-2 (a11y Storybook runtime prioritaire sur vitest-axe happy-dom pour portail) capitalisés en **règles d'or permanentes appliquées proactivement pas post-review**.
  - [ ] 8.2 Identifier patterns futurs applicables 10.19 Combobox (Reka UI `<ComboboxRoot>` wrapper — multi-select + aria-activedescendant + virtualization option) et 10.20 DatePicker (Reka UI pas de primitive — decision : `vue-cal` OR custom ? Capitaliser en §4ter note pré-10.20).

## Dev Notes

### 1. Architecture cible — arborescence finale post-10.18

```
frontend/
├── app/
│   └── components/
│       └── ui/                     (6 composants existants 10.15+10.16+10.17 + 1 NOUVEAU + 2 brownfield)
│           ├── FullscreenModal.vue       (inchangé, brownfield — modal fullscreen mobile ≠ Drawer)
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
│           ├── Drawer.vue                (NOUVEAU 10.18 : wrapper Reka UI DialogRoot + role=complementary override)
│           ├── Drawer.stories.ts         (NOUVEAU 10.18 : ≥ 16 stories CSF 3.0)
│           └── registry.ts               (ÉTENDU 10.18 : +2 frozen tuples DRAWER_SIDES/SIZES)
├── tests/components/ui/             (10 fichiers existants + 4 NOUVEAUX + 1 .test-d.ts NOUVEAU)
│   ├── test_drawer_registry.test.ts            (NOUVEAU)
│   ├── test_drawer_behavior.test.ts            (NOUVEAU — Pattern A DOM-only strict)
│   ├── test_drawer_a11y.test.ts                (NOUVEAU — smoke + délégation runtime Storybook)
│   ├── test_no_hex_hardcoded_drawer.test.ts    (NOUVEAU)
│   └── Drawer.test-d.ts                        (NOUVEAU : ≥ 10 @ts-expect-error)

docs/CODEMAPS/
└── ui-primitives.md                 (ÉTENDU 10.18 : §3.5 Drawer + pièges 27-32 + §2 arbo)
└── methodology.md                   (ÉTENDU 10.18 : §4ter application proactive 10.18)
```

**Aucune modification** :
- `frontend/app/assets/css/main.css` (tokens surface/brand/dark déjà livrés 10.14 + darkés 10.15 — Drawer consomme).
- `frontend/.storybook/main.ts` (glob `gravity/ + ui/` déjà étendu 10.15).
- `frontend/.storybook/preview.ts` (dark mode + a11y config stables).
- `frontend/vitest.config.ts` (typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15).
- `frontend/app/components/gravity/SourceCitationDrawer.vue` (migration Phase 1 Epic 13 — hors scope 10.18 qui livre l'infra).
- `frontend/app/components/gravity/SignatureModal.vue` (reste modal `role="dialog"` — correct car dialogue bloquant signature).

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|----------|----------|-----------|
| **Q1** | Wrapper **Reka UI `<DialogRoot>`** OU **vue-custom headless** (aria manuel + Teleport + focus-trap manuel) ? | **Wrapper Reka UI `<DialogRoot>`** | Cohérent UX Step 6 Q15 (« Reka UI nu, pas shadcn-vue ») + Step 11 §3 (« Reka UI primitives = base accessible ARIA »). Le squelette SourceCitationDrawer 10.14 utilise déjà ScrollAreaRoot Reka UI. Développer un headless maison = dupliquer focus trap + portal + keyboard nav (6-8 h de dev + risques a11y). Reka UI fournit tout ça testé + maintenu. **Override ARIA** (`role="complementary"` + `aria-modal="false"`) couvre notre cas d'usage drawer consultatif (AC3 + piège #27). |
| **Q2** | `role="complementary"` override OU `role="dialog"` (Reka UI default) ? | **`role="complementary"` override** | **Leçon 10.14 HIGH-2 capitalisée infra** : drawer = consultation parallèle, modal = interaction bloquante. Utilisateur doit pouvoir continuer à lire le contenu principal (sources RAG Epic 13, comparaison intermédiaires Epic 15, thread peer-review Epic 19). `role="dialog"` forcerait l'utilisateur à fermer avant d'interagir avec le reste. Conséquence : `aria-modal="false"` (Q3) + focus trap opt-in (Q4) cohérents. SignatureModal reste `role="dialog"` car c'est vraiment un modal bloquant signature. |
| **Q3** | `aria-modal="false"` (interaction DOM externe permise) OU `aria-modal="true"` (Reka UI default) ? | **`aria-modal="false"`** | Cohérent Q2 : si `role="complementary"` alors `aria-modal="true"` serait incohérent (impliquerait modalité). `aria-modal="false"` explicite est la bonne signalétique screen reader : « panneau complémentaire, contenu externe reste accessible ». Reka UI force `aria-modal="true"` par défaut → override explicite dans Drawer.vue via attribut HTML sur DialogContent. |
| **Q4** | Focus trap **default `true`** (Reka UI natif) OU **opt-in via prop `trapFocus` default `false`** ? | **Opt-in via prop `trapFocus` default `false`** | Cohérent Q2+Q3 : drawer consultatif = navigation libre. Si l'utilisateur veut Tab vers le contenu principal pour lire en parallèle, il doit pouvoir. **MAIS** si un drawer contient un formulaire critique (ex. IntermediaryComparator v2 avec sélection multi-pays + submit), le consommateur passe `trapFocus="true"` explicitement pour éviter que Tab sorte accidentellement (UX form). Équilibre : consultation = default libre, form critique = opt-in lock. Documenté §3.5 codemap + piège #32 (Escape + beforeclose future API). |
| **Q5** | Mobile fullscreen breakpoint **`<md` 768 px** OU **`<sm` 640 px** ? | **`<md` 768 px** | Tailwind standard `md: 768px`. En dessous de 768 px, drawer `size="md"` (480 px) occuperait ≥ 50 % viewport sur la majorité des mobiles (viewport ≤ 414 px iPhone 14 Pro Max portrait = 100 % + viewport 640-767 tablettes portrait = 63-75 %) → UX dégradée côte à côte content principal coupé. À 768 px et plus (iPad portrait, laptops 1024+), la géométrie devient drawer = 25-47 % viewport → OK. Cohérent Tailwind responsive discipline Wave Q12 (Step 11 responsive-first desktop ≥ md). **Aligné pattern SourceCitationDrawer squelette 10.14** (qui utilise 420 px fixe mais squelette sera refactorisé consommateur sur ui/Drawer `md` = 480 px Phase 1 Epic 13 — Léger agrandissement UX décidé Step 12 §9 SourceCitationDrawer = 480 px). |

### 3. Exemple squelette complet — `ui/Drawer.vue`

```vue
<!--
  ui/Drawer.vue — primitive UI Phase 0 Story 10.18 (1ere wrapper Reka UI).
  Wrapper Reka UI DialogRoot + DialogPortal + DialogOverlay + DialogContent.
  Drawer CONSULTATIF (role="complementary", aria-modal="false") != Modal bloquant (SignatureModal).
  Lecon 10.14 HIGH-2 capitalisee infra : override ARIA explicite sur DialogContent.
  4 sides x 3 sizes desktop + mobile fullscreen auto < md (768 px).
  Focus trap opt-in (default false — drawer permet navigation DOM externe).
  3 chemins fermeture composables (Escape + overlay click + close button).
  ScrollArea Reka UI integree pour contenu scrollable (AC13).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import {
  DialogRoot,
  DialogPortal,
  DialogOverlay,
  DialogContent,
  DialogClose,
  DialogTitle,
  DialogDescription,
  ScrollAreaRoot,
  ScrollAreaViewport,
  ScrollAreaScrollbar,
  ScrollAreaThumb,
} from 'reka-ui';
import type { DrawerSide, DrawerSize } from './registry';

interface DrawerProps {
  open: boolean;
  title: string;
  description?: string;
  side?: DrawerSide;
  size?: DrawerSize;
  trapFocus?: boolean;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
}

const props = withDefaults(defineProps<DrawerProps>(), {
  side: 'right',
  size: 'md',
  trapFocus: false,
  closeOnEscape: true,
  closeOnOverlayClick: true,
  showCloseButton: true,
});

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
}>();

const titleId = useId();
const descId = useId();

// Side classes (desktop) — position + anim-slide
const sidePositionClasses = computed<string>(() => {
  switch (props.side) {
    case 'right':  return 'md:right-0 md:top-0 md:h-full';
    case 'left':   return 'md:left-0 md:top-0 md:h-full';
    case 'top':    return 'md:top-0 md:left-0 md:w-full';
    case 'bottom': return 'md:bottom-0 md:left-0 md:w-full';
  }
});

// Size classes (desktop) — width pour right/left, height pour top/bottom
// Garde-fou max-w-[50vw] desktop large (piege #30)
const sideIsHorizontal = computed(() => props.side === 'right' || props.side === 'left');
const sizeClasses = computed<string>(() => {
  const dim = sideIsHorizontal.value ? 'w' : 'h';
  const cap = sideIsHorizontal.value ? 'max-w-[50vw]' : 'max-h-[50vh]';
  switch (props.size) {
    case 'sm': return `md:${dim}-[320px] ${cap}`;
    case 'md': return `md:${dim}-[480px] ${cap}`;
    case 'lg': return `md:${dim}-[560px] ${cap}`;
  }
});

// Mobile fullscreen auto < md — CSS-only, pas useMediaQuery (evite SSR hydration)
const mobileFullscreenClasses = 'w-full h-full bottom-0 left-0';

// Runtime defense : 3 paths disabled (dev only — piege #32)
if (import.meta.env.DEV) {
  if (!props.closeOnEscape && !props.closeOnOverlayClick && !props.showCloseButton) {
    // eslint-disable-next-line no-console
    console.warn(
      '[ui/Drawer] 3 chemins fermeture desactives — risque utilisateur piege. ' +
      'Au moins 1 (closeOnEscape / closeOnOverlayClick / showCloseButton) doit rester actif.'
    );
  }
}

function handleOpenChange(value: boolean) {
  emit('update:open', value);
}

function handleEscapeKeyDown(e: Event) {
  if (!props.closeOnEscape) {
    e.preventDefault();
  }
}

function handlePointerDownOutside(e: Event) {
  if (!props.closeOnOverlayClick) {
    e.preventDefault();
  }
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <!-- Overlay : dark:bg-black/70 pour dark mode, motion-reduce fade -->
      <DialogOverlay
        class="fixed inset-0 z-40 bg-black/50 dark:bg-black/70 motion-reduce:transition-none"
        :style="props.closeOnOverlayClick ? 'pointer-events: auto' : 'pointer-events: none'"
      />
      <!--
        DialogContent : OVERRIDE ARIA (AC3 + piege #27).
        role="complementary" remplace role="dialog" Reka UI default.
        aria-modal="false" explicite (drawer != modal bloquant).
        trap-focus passe au Reka UI natif (opt-in Q4).
      -->
      <DialogContent
        role="complementary"
        aria-modal="false"
        :aria-labelledby="titleId"
        :aria-describedby="description ? descId : undefined"
        :trap-focus="trapFocus"
        class="fixed z-50 bg-white dark:bg-dark-card shadow-xl border-gray-200 dark:border-dark-border flex flex-col motion-reduce:transition-none"
        :class="[mobileFullscreenClasses, sidePositionClasses, sizeClasses]"
        @escape-key-down="handleEscapeKeyDown"
        @pointer-down-outside="handlePointerDownOutside"
      >
        <!-- Header sticky top -->
        <header class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-border">
          <slot name="header">
            <div class="flex-1">
              <DialogTitle
                :id="titleId"
                class="text-base font-semibold text-surface-text dark:text-surface-dark-text"
              >
                {{ title }}
              </DialogTitle>
              <DialogDescription
                v-if="description"
                :id="descId"
                class="mt-1 text-sm text-surface-text/70 dark:text-surface-dark-text/70"
              >
                {{ description }}
              </DialogDescription>
            </div>
            <DialogClose
              v-if="showCloseButton"
              aria-label="Fermer le panneau"
              class="ml-2 rounded p-1 text-surface-text dark:text-surface-dark-text hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-green"
            >
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4 4 L12 12 M12 4 L4 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </DialogClose>
          </slot>
        </header>

        <!-- Contenu scrollable ScrollArea Reka UI -->
        <ScrollAreaRoot class="flex-1 overflow-hidden">
          <ScrollAreaViewport class="h-full w-full p-4">
            <slot />
          </ScrollAreaViewport>
          <ScrollAreaScrollbar orientation="vertical" class="w-2 bg-gray-200 dark:bg-dark-border">
            <ScrollAreaThumb class="bg-gray-400 dark:bg-dark-hover rounded" />
          </ScrollAreaScrollbar>
        </ScrollAreaRoot>

        <!-- Footer sticky bottom (optionnel) -->
        <footer
          v-if="$slots.footer"
          class="border-t border-gray-200 dark:border-dark-border p-4"
        >
          <slot name="footer" />
        </footer>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
```

**Rationale** :
- **Zéro hex** : tous via tokens `@theme` (`surface-*`, `dark-*`, `brand-green`) livrés 10.14+10.15 (AC1).
- **Override ARIA explicite** : `role="complementary"` + `aria-modal="false"` sur DialogContent (AC3 + piège #27 + leçon 10.14 HIGH-2 capitalisée).
- **Focus trap opt-in** : `:trap-focus="trapFocus"` (default false — Q4). Reka UI DialogContent supporte cette prop via son API de primitive nu (vs shadcn-vue qui impose trap).
- **Dark mode** : `dark:bg-dark-card` + `dark:border-dark-border` + `dark:text-surface-dark-text` + `dark:bg-black/70` + `dark:hover:bg-dark-hover` + `dark:focus-visible:ring-brand-green` ≥ 8 occurrences AC9.
- **Mobile fullscreen CSS-only** : `w-full h-full bottom-0 md:w-[...] md:h-full md:bottom-auto md:right-0` — pas useMediaQuery (évite hydration mismatch SSR Nuxt).
- **Garde-fou max-w-50vw** : empêche drawer de saturer viewport sur desktop moyen (piège #30).
- **ScrollArea integree** : pattern SourceCitationDrawer 10.14 byte-identique (`w-2 bg-gray-200 dark:bg-dark-border` scrollbar).
- **Runtime defense 3 paths disabled** : console.warn dev-only (piège #32).
- **DialogTitle + DialogDescription Reka UI** : a11y natif `aria-labelledby` + `aria-describedby` — l'override `role="complementary"` conserve la sémantique titre/description (screen reader annonce bien « Panneau complémentaire Sources documentaires »).

### 4. Pièges documentés (6 nouveaux — 27-32 — cumul ≥ 32 avec 26 existants 10.14-10.17)

**27. `role="complementary"` OVERRIDE vs Reka UI DialogContent default `role="dialog"` + `aria-modal="true"`** — Reka UI DialogRoot/DialogContent imposent par défaut `role="dialog"` + `aria-modal="true"` (comportement modal bloquant). Pour un drawer consultatif (SourceCitationDrawer FR71 + IntermediaryComparator Moussa + PeerReviewThreadedPanel admin N2), cette sémantique est **incorrecte** : l'utilisateur doit pouvoir continuer à lire/interagir avec le contenu principal tout en consultant le drawer. **Solution architecturale** : override explicite `role="complementary"` + `aria-modal="false"` sur le `<DialogContent>` via attributs HTML (Reka UI laisse passer les attrs non-reconnus). Conséquences : (a) screen reader annonce « panneau complémentaire » au lieu de « dialogue », (b) AT peut quitter le drawer sans le fermer, (c) le contenu principal reste interactif. **Leçon 10.14 HIGH-2 capitalisée infra** : ce n'est pas une correction post-hoc mais l'architecture par défaut de `ui/Drawer`. Test DOM explicite `document.body.querySelector('[role="complementary"]').getAttribute('aria-modal') === 'false'`.

**28. Portail Teleport/DialogPortal happy-dom limitations → Storybook `addon-a11y` runtime prioritaire** — `vitest-axe` en happy-dom (`@vitest/browser: false`) ne matérialise pas de façon fiable : (a) les portails `Teleport to="body"` natifs Vue, (b) les portails Reka UI DialogPortal, (c) les CSS custom properties dark mode sans adoptedStyleSheets, (d) le layout box (pour règle axe `color-contrast`). **Conséquence** : `toHaveNoViolations()` peut produire faux négatifs (violations manquées) ou faux positifs (éléments non visibles signalés). **Solution en deux temps** (leçon 10.15 HIGH-2 capitalisée) : (1) **vitest-axe en smoke** pour assertions ARIA simples (`role` / `aria-*` présents sur DOM accessible), (2) **Storybook `addon-a11y` test-runner en CI** pour audits contraste/focus/keyboard portail-dépendants. **Ne JAMAIS désactiver** sélectivement `color-contrast` pour faire passer vitest-axe (masque régression) — préférer délégation runtime documentée. Piège lié : les tests `vitest-axe` 10.17 contournent le problème sur Badge car Badge n'est pas portalisé — Drawer l'est → délégation runtime obligatoire.

**29. Mobile fullscreen breakpoint `<md` 768 px responsive-first (pas `<sm` 640 px, pas `useMediaQuery` JS)** — Tentation d'utiliser breakpoint `<sm` (640 px) pour "préserver" drawer sur tablette portrait. **INCORRECT** : à 640-767 px, drawer `size="md"` (480 px) = 63-75 % viewport → content principal illisible. **Solution** : breakpoint `<md` (768 px) — au-dessus de ce seuil, drawer = 25-47 % viewport (OK). **Deuxième piège** : implémenter via `useMediaQuery` (`@vueuse/core`) ou `window.matchMedia` côté JS génère **hydration mismatch SSR Nuxt** (serveur rend desktop, client bascule mobile après mount → flash visuel + layout shift). **Solution** : Tailwind CSS-only `w-full h-full md:w-[480px] md:h-full` — SSR rend le même HTML partout, CSS résout le breakpoint côté client sans JS. Tests Vitest : mock `window.matchMedia` ou assertions via `classList.contains('md:w-[480px]')` (classes Tailwind toujours présentes, le breakpoint est CSS).

**30. ScrollArea tokens cohérents + garde-fou `max-w-[50vw]` desktop ultra-large** — Reka UI ScrollArea ne style pas la scrollbar par défaut (headless). Pour cohérence design, reprendre byte-identique le pattern `SourceCitationDrawer` 10.14 : `<ScrollAreaScrollbar orientation="vertical" class="w-2 bg-gray-200 dark:bg-dark-border">` + `<ScrollAreaThumb class="bg-gray-400 dark:bg-dark-hover rounded">`. **Deuxième piège** (spécifique Drawer vs SourceCitationDrawer fixe 420 px) : avec `size="lg"` (560 px) sur écran étroit `1000 px`, drawer = 56 % viewport → content principal coupé. **Solution** : garde-fou `max-w-[50vw]` sur DialogContent — sur grand écran (≥ 1120 px) largeur reste 560 px, sur écran moyen (1000 px) plafonne à 500 px. Alternative `w-[min(560px,50vw)]` équivalente. Documenté §3.5 codemap avec breakpoints chiffrés.

**31. Overlay `backdrop-filter: blur()` perf mobile + `pointer-events` drawer consultatif vs modal** — **Premier piège** : tentation d'ajouter `backdrop-blur-sm` sur `<DialogOverlay>` pour effet « moderne » — **INTERDIT mobile** (GPU faible drain batterie + repaint cascade à chaque animation scroll body). Solution : opacité seule `bg-black/50 dark:bg-black/70` (pattern byte-identique SignatureModal 10.14). **Deuxième piège** (spécifique drawer consultatif Q2+Q3) : si `aria-modal="false"` + overlay `pointer-events: auto` classique, l'overlay capture les clics → le contenu principal devient non-interactif (contradiction sémantique drawer consultatif). **Solution** : overlay `pointer-events: auto` UNIQUEMENT si `closeOnOverlayClick: true` (l'utilisateur clique pour fermer), sinon `pointer-events: none` (l'utilisateur peut interagir avec le contenu dessous). Attention : si `closeOnOverlayClick: false` + `pointer-events: none`, l'utilisateur peut fermer involontairement via click sur main content. Documenter clairement dans §3.5 codemap + rendre la sémantique consultative explicite dans les stories Storybook.

**32. Escape + beforeclose intercept (unsaved changes pattern — Phase Growth)** — Un consommateur peut avoir des modifications non sauvegardées dans le drawer (hypothèse future : `IntermediaryComparator` v2 avec sélection multi-pays + submit, ou `PeerReviewThreadedPanel` avec textarea threaded en cours de rédaction). **Escape ne doit pas fermer sans confirmation** UX. Piège : naïvement passer `closeOnEscape={false}` en permanence désactive aussi la fermeture intentionnelle. **Solution MVP Phase 0** : consommateur écoute `@update:open="handleClose"` et intercepte :
```ts
function handleClose(nextOpen: boolean) {
  if (!nextOpen && hasUnsavedChanges.value) {
    if (!confirm('Fermer sans sauvegarder ?')) {
      return; // ne pas propager — drawer reste ouvert car parent ne met pas à jour isOpen
    }
  }
  isOpen.value = nextOpen;
}
```
**Phase Growth** : API `beforeClose?: () => boolean | Promise<boolean>` prop optionnelle qui bloque la fermeture si retourne false. Tracé `DEF-10.18-1 beforeClose API` si pattern > 2 occurrences Phase 1 (Epic 13 SourceCitationDrawer = lecture pure pas de changes, Epic 15 IntermediaryComparator v1 = sélection simple, Epic 19 PeerReviewThreadedPanel = sujet à évaluation). Complément `#32.b` : **3 chemins fermeture tous désactivés** (`closeOnEscape: false`, `closeOnOverlayClick: false`, `showCloseButton: false`) → **utilisateur piégé**. Runtime `console.warn` dev-only (defense-in-depth AC5 step 3.15).

### 5. Test plan complet

| # | Test | Type | Delta baseline 555 |
|---|------|------|--------------------|
| T1 | `DRAWER_SIDES.length === 4` + frozen + dedup + ordre `right` first | Vitest unit | +4 |
| T2 | `DRAWER_SIZES.length === 3` + frozen + dedup | Vitest unit | +3 |
| T3 | v-model:open mount false → body.querySelector('[role="complementary"]') null | Vitest @vue/test-utils + Pattern A | +1 |
| T4 | v-model:open setProps true → body.querySelector non-null | Vitest Pattern A | +1 |
| T5 | Escape closes drawer (closeOnEscape default true) | Vitest user-event | +1 |
| T6 | Escape disabled (closeOnEscape false) — press Escape → drawer reste ouvert | Vitest | +1 |
| T7 | Overlay click closes (closeOnOverlayClick true) | Vitest | +1 |
| T8 | Overlay click disabled — drawer reste ouvert | Vitest | +1 |
| T9 | Close button click closes | Vitest | +1 |
| T10 | showCloseButton=false → button absent | Vitest querySelector null | +1 |
| T11 | 3 paths disabled → console.warn fallback | Vitest vi.spyOn | +1 |
| T12 | Focus trap disabled (default) → Tab peut sortir | Vitest focus + Pattern A | +1 |
| T13 | Focus trap enabled → Tab cycle reste dans drawer | Vitest | +1 |
| T14 | Mobile fullscreen via matchMedia mock `< 768` + classList `w-full h-full` | Vitest | +1 |
| T15 | Desktop `>= 768` + size=md + classList `md:w-[480px]` | Vitest | +1 |
| T16 | Sizes × 3 classes présentes (sm/md/lg) | Vitest | +3 |
| T17 | Sides × 4 classes présentes (right/left/top/bottom) | Vitest | +4 |
| T18 | role="complementary" présent (pas "dialog") | Vitest a11y Pattern A | +1 |
| T19 | aria-modal="false" présent | Vitest | +1 |
| T20 | aria-labelledby pointe sur titleId existant + textContent === props.title | Vitest | +1 |
| T21 | aria-describedby conditionnel — absent si pas de description | Vitest | +1 |
| T22 | vitest-axe smoke × 2 (open default + open avec description) | Vitest a11y | +2 |
| T23 | Scan hex `Drawer.vue` → 0 hit | Vitest fs | +1 |
| T24 | Scan hex `Drawer.stories.ts` → 0 hit | Vitest fs | +1 |
| T25 | ScrollArea rendered (test_drawer_behavior scroll-area-rendered) | Vitest | +1 |
| T26 | `test_docs_ui_primitives` §3.5 présent + ≥ 32 pièges + ≥ 4 exemples §3.5 | Vitest doc grep | +4 |
| T27 | **Drawer.test-d.ts** (10+ assertions `@ts-expect-error`) | TS typecheck | +10 typecheck |
| **Total delta runtime** | | | **+37 tests** (plancher AC11 ≥ 14 largement dépassé) |
| **Total delta typecheck** | | | **+10** (plancher AC11 ≥ 10 atteint) |
| Storybook runtime | `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length'` | Comptage build | **≥ 16 nouvelles Drawer** (mesuré exact Task 7.3) |
| Baseline runtime | 555 → 592+ passed (aucune régression) | Vitest | **0 régression** |
| Baseline typecheck | 40 → 50+ assertions | Vitest --typecheck | **+10** |

### 6. Checklist review (pour code-reviewer Story 10.18 post-merge)

- [ ] **role="complementary" override présent** — `document.body.querySelector('[role="complementary"]').getAttribute('aria-modal') === 'false'` assertions présentes dans tests (PAS `role="dialog"`).
- [ ] **Tokens `@theme` exclusifs** — `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Drawer.vue frontend/app/components/ui/Drawer.stories.ts` → 0 hit hors commentaires.
- [ ] **TypeScript strict enforcé** — `rg ': any|as unknown' frontend/app/components/ui/Drawer.vue frontend/tests/components/ui/Drawer.test-d.ts` → 0 hit.
- [ ] **Drawer.test-d.ts ≥ 10 `@ts-expect-error`** vérifiés via `npm run test:typecheck` (baseline 40 → 50+).
- [ ] **Dark mode ≥ 8 `dark:`** — `rg 'dark:' frontend/app/components/ui/Drawer.vue | wc -l` ≥ 8 sans inflation artificielle (chaque classe rattachée à axe visuel).
- [ ] **WCAG 2.1 AA via Storybook `addon-a11y` runtime** (PAS vitest-axe happy-dom seul pour contraste/portail — leçon 10.15 HIGH-2 capitalisée) — 0 violation `storybook:test` CI sur `ui-drawer--*`.
- [ ] **Pattern A strict** — aucun `wrapper.vm.*` dans `test_drawer_behavior.test.ts`, toutes assertions via `document.body.querySelector` portal-aware.
- [ ] **Pattern B (comptage runtime Storybook)** — Completion Notes contient EXACT output `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length'` — pas d'estimation.
- [ ] **3 chemins fermeture composables** — tests `closeOnEscape` + `closeOnOverlayClick` + `showCloseButton` × enabled/disabled cases × 4 min.
- [ ] **Runtime warn 3 paths disabled** — `console.warn` déclenché dev-only, test `vi.spyOn(console, 'warn')` présent.
- [ ] **Focus trap opt-in default false** — test `trapFocus` default + opt-in cases via `document.activeElement` assertions.
- [ ] **Mobile fullscreen CSS-only** — pas de `useMediaQuery` / `window.matchMedia` dans le composant (hydration SSR safe) ; tests via classList scan.
- [ ] **Garde-fou `max-w-[50vw]`** présent pour `lg` desktop (piège #30).
- [ ] **ScrollArea intégrée** — tests assert `[data-reka-scroll-area-root]` ou équivalent DOM présent (AC13).
- [ ] **Pas de `backdrop-blur-sm`** sur overlay (piège #31 perf mobile).
- [ ] **Pointer-events overlay conditionnel** `closeOnOverlayClick ? auto : none` (piège #31 sémantique consultatif).
- [ ] **Pas de duplication** — `DRAWER_SIDES` / `DRAWER_SIZES` source unique `registry.ts` — importés par `Drawer.vue` + stories + tests.
- [ ] **Wrapper Reka UI pas headless maison** — `rg 'import.*from .reka-ui' frontend/app/components/ui/Drawer.vue` doit retourner `DialogRoot`, `DialogPortal`, `DialogOverlay`, `DialogContent`, `DialogClose`, `DialogTitle`, `DialogDescription`, `ScrollAreaRoot`, `ScrollAreaViewport`, `ScrollAreaScrollbar`, `ScrollAreaThumb`.
- [ ] **Shims legacy 10.6** — aucune modification des 60 brownfield + 6 gravity/ + 5 primitives `ui/` existantes (Button + Input + Textarea + Select + Badge) + FullscreenModal + ToastNotification. `git diff frontend/app/components/ui/ -- ':!Drawer.vue' ':!Drawer.stories.ts' ':!registry.ts'` → vide.
- [ ] **Glob Storybook inchangé** — `frontend/.storybook/main.ts` diff restreint à 0 ligne.
- [ ] **Bundle Storybook ≤ 15 MB** — `du -sh frontend/storybook-static` respecté.
- [ ] **No secret exposé** — `rg 'API_KEY|SECRET|TOKEN' frontend/app/components/ui/Drawer*` → 0 hit.
- [ ] **Pattern leçon 10.14 HIGH-2 capitalisée infra** — `role="complementary"` + `aria-modal="false"` = ARCHITECTURE par défaut du composant, documenté §3.5 codemap + §4ter methodology.md.
- [ ] **Pattern leçon 10.15 HIGH-2 capitalisée infra** — délégation runtime Storybook addon-a11y pour portail explicitée dans `test_drawer_a11y.test.ts` + §5 codemap piège #28.

### 7. Pattern commits intermédiaires (leçon 10.8+10.14+10.15+10.16+10.17)

2 commits lisibles review :
1. `feat(10.18): ui/Drawer primitive + registry CCC-9 2 tuples + role=complementary override` (Task 2 + 3) — wrapper Reka UI + override ARIA + tokens + dark mode ≥ 8 + runtime warn 3 paths + registry.ts extension.
2. `feat(10.18): Drawer stories CSF3 + tests behavior/a11y + docs CODEMAPS §3.5 + count runtime vérifié` (Task 4 + 5 + 6 + 7) — 16+ stories CSF + tests Pattern A DOM-only + vitest-axe smoke + délégation runtime + §3.5 codemap + pièges 27-32.

Pattern CCC-9 (10.8+10.14+10.15+10.16+10.17) appliqué byte-identique : `DRAWER_SIDES` + `DRAWER_SIZES` frozen `Object.freeze([...] as const)` + validation `test_drawer_registry.test.ts`.

Pattern compile-time enforcement `.test-d.ts` (10.15 HIGH-1) réutilisé byte-identique : `Drawer.test-d.ts` dans `tests/components/ui/` + `vitest typecheck` déjà configuré.

Pattern darken tokens AA (10.15 HIGH-2) : **applicable partiel** — focus ring Drawer utilise `brand-green #047857` post-darken AA (5,78:1) cohérent Button focus.

Pattern soft-bg contraste (10.17 CRITICAL-1/2) : **non applicable** — Drawer utilise `surface-*` + `dark-card` (surfaces neutres pas teintées), pas de verdict/fa/admin colorés.

Pattern describedBy aligné v-if (10.16 H-1) : **appliqué** — `aria-describedby` conditionnel sur `description` prop (piège #27 alignement sémantique).

Pattern IME composition (10.16 H-2) : **non applicable** — Drawer n'est pas un input.

Pattern multi-select native binding (10.16 H-3) : **non applicable** — Drawer n'est pas un Select.

Pattern type coercion string-only (10.16 H-4) : **non applicable** — Drawer émit `update:open: boolean` (pas de coercion nécessaire, boolean strict).

Pattern anti-badge-as-button (10.17 Q5 piège #24) : **non applicable** — Drawer n'a pas d'ambiguïté interactive (c'est conteneur, pas indicateur).

**Pattern A méthodologique (10.16 H-3 + capitalisé 10.17)** : **appliqué proactivement** Task 5.2 — `test_drawer_behavior.test.ts` assert `document.body.querySelector('[role="complementary"]')`, `attributes('aria-modal')`, `getAttribute('aria-labelledby')`, `document.activeElement` — jamais `wrapper.vm.open`. **Enjeu spécifique Drawer portal** : les assertions doivent scanner `document.body` (portalisation Reka UI DialogPortal) et non `wrapper.element` (racine composant vide post-portal).

**Pattern B méthodologique (10.16 M-3 + capitalisé 10.17 piège #26)** : **appliqué proactivement** Task 7.3 — le chiffre `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length'` consigné Completion Notes AVANT claim de complétude.

**Pattern leçon 10.14 HIGH-2 (role complementary)** : **capitalisé infra** — ARIA override = architecture par défaut, pas correction post-hoc. Tests enforce `role === 'complementary'` strict.

**Pattern leçon 10.15 HIGH-2 (Storybook runtime pour portail)** : **capitalisé infra** — `test_drawer_a11y.test.ts` explicite délégation portail-dépendante à Storybook runtime + piège #28 codemap. Évite pattern anti-fix de désactiver `color-contrast` axe-core.

### 8. Hors scope explicite (non-objectifs cette story)

- ❌ **Migration `SourceCitationDrawer` 10.14 squelette vers `<ui/Drawer>`** — Phase 1 Epic 13 (FR71 Perplexity-style sources RAG). Story 10.18 livre **uniquement l'infra**, pas la migration.
- ❌ **`IntermediaryComparator` Moussa Journey 2** — Phase 1 Epic 15 (consommateur futur `<Drawer size="lg">`).
- ❌ **`PeerReviewThreadedPanel` admin N2 GitHub PR-style** — Phase 1 Epic 19 (consommateur futur).
- ❌ **API `beforeClose?: () => boolean | Promise<boolean>`** — Deferred `DEF-10.18-1 beforeClose API Phase Growth` si > 2 occurrences Phase 1. MVP : consommateur intercepte via `@update:open` (piège #32).
- ❌ **Multi-drawer empilés (drawer dans drawer)** — interdit UX (règle transversale Step 12 §9). Pas d'API `stack` / `zIndex` modulaire Phase 0.
- ❌ **Drawer détachable/ancrable (DOM portal custom target)** — pas besoin MVP, `document.body` suffit.
- ❌ **Animation custom slide/fade override** — Reka UI gère via CSS classes Tailwind + `prefers-reduced-motion`. Pas de prop `animation` Phase 0.
- ❌ **Drawer fullscreen desktop** — contradiction avec size/side (= modal alors, voir `FullscreenModal.vue` brownfield pour ce cas).
- ❌ **Props `center` side** — drawer est toujours bord (`right`/`left`/`top`/`bottom`), pas centré. Piège #32 TS `side: 'center'` → `@ts-expect-error`.
- ❌ **Integration tests E2E** — Playwright E2E couvert Epic 13+ quand consommateurs migrent. Phase 0 = unit + integration Vitest + Storybook runtime.
- ❌ **Smoke test auto-import Nuxt `<Drawer>`** — intégré au pattern global pathPrefix: false, pas spécifique Drawer. Scope global Phase 1.
- ❌ **Variant Sheet/BottomSheet séparé (iOS/Android native feel)** — Phase 0 : mobile fullscreen side=bottom CSS-only suffit. Variant dédié Phase Growth si design UX le demande.
- ❌ **Stacking avec notifications ToastNotification** — z-index pattern global, pas spécifique Drawer.
- ❌ **Integration Lucide `lucide-vue-next`** — Story 10.21. Le close button utilise SVG inline path (cohérent Badge stubs 10.17, migration mécanique Phase 0+).
- ❌ **Modification `FullscreenModal.vue` brownfield** — inchangé (pattern shim 10.6). Sert cas modal fullscreen mobile, différent de Drawer consultatif.

### 9. Previous Story Intelligence (10.17 + 10.14 leçons transférables)

De Story 10.17 (Badge sizing S) + 10.16 (Input+Textarea+Select sizing M) + 10.15 (Button sizing S) + 10.14 (Storybook setup sizing L) :

**Leçons architecturales réutilisables byte-identique** :
- **Pattern CCC-9 frozen tuple** — `VERDICT_STATES` / `LIFECYCLE_STATES` / `ADMIN_CRITICALITIES` / `BADGE_SIZES` (10.17) + `INPUT_TYPES` / `FORM_SIZES` (10.16) + `BUTTON_VARIANTS` / `BUTTON_SIZES` (10.15) → 2 nouveaux tuples Drawer (`DRAWER_SIDES` / `DRAWER_SIZES`).
- **Compile-time enforcement `.test-d.ts`** — `Badge.test-d.ts` (10.17) + `Input/Textarea/Select.test-d.ts` (10.16) + `Button.test-d.ts` (10.15) → `Drawer.test-d.ts` 10+ assertions.
- **Helper `asStorybookComponent<T>()`** — `frontend/app/types/storybook.ts` (10.15 MEDIUM-3) réutilisé byte-identique.
- **Scan hex + no any** — tests 10.15+10.16+10.17 réutilisés scope `Drawer.vue` uniquement.
- **Storybook co-localisation** — `<Name>.stories.ts` à côté `.vue`.
- **Dark mode seuil primitive** (10.15 MEDIUM-2 exception) — adapté Drawer : ≥ 8 occurrences (overlay + surface + border + 2 textes + 3 états close button) sans inflation.
- **ScrollArea pattern** — `SourceCitationDrawer.vue` (10.14 squelette) + `ImpactProjectionPanel.vue` (10.14) → Drawer.vue byte-identique (w-2 bg-gray-200 dark:bg-dark-border thumb).

**Leçons méthodologiques capitalisées (appliquées proactivement)** :
- **Pattern A (10.16 H-3 + capitalisé 10.17 Task 5)** — tests DOM observable via `document.body.querySelector` (portal-aware pour Reka UI DialogPortal). **Enjeu Drawer spécifique** : `wrapper.find(...)` sur racine composant = vide post-portal → utiliser `document.body.querySelector('[role="complementary"]')`. Documenté §3.5 codemap.
- **Pattern B (10.16 M-3 + capitalisé 10.17 piège #26)** — comptage Storybook runtime OBLIGATOIRE `jq` AVANT Completion Notes. Commande Drawer : `jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length' storybook-static/index.json`.

**Leçons architecturales capitalisées infra (Drawer spécifique)** :
- **Leçon 10.14 HIGH-2 capitalisée infra (role complementary override)** — PAS post-hoc correction mais architecture par défaut. `role="complementary"` + `aria-modal="false"` explicites dans Drawer.vue sur DialogContent. Test enforce strict. Évite récurrence ambiguïté dialog/complementary pour les 3 consommateurs Phase 1+.
- **Leçon 10.15 HIGH-2 capitalisée infra (Storybook runtime pour portail)** — délégation explicite portail-dépendants à Storybook addon-a11y runtime dans test_drawer_a11y.test.ts. Évite anti-fix « désactiver color-contrast axe-core » qui masquerait régression.

**Leçons 10.17 CRITICAL applicables** :
- **CRITICAL-1/2 soft-bg contraste AA** — NON APPLICABLE Drawer (surfaces neutres `surface-*` + `dark-card`, pas de verdict/fa/admin teintés).
- **CRITICAL-3 tests Pattern A DOM primaires + console spy défense** — APPLIQUÉ Task 5.2 : 3 paths disabled warn utilise DOM primary assertions + `vi.spyOn(console, 'warn')` défense en profondeur.

**Leçons 10.17 HIGH applicables** :
- **HIGH-5 `[&_svg]` scope wrapper** — NON APPLICABLE Drawer (SVG close button direct pas dans slot utilisateur).
- **HIGH-6 slot empty bypass DOM post-nextTick** — NON APPLICABLE Drawer (pas de slot obligatoire runtime-check — title prop compile-time suffit).

**Leçons 10.16 HIGH applicables** :
- **H-1 describedBy aligné v-if** — **APPLIQUÉ** Task 3.4 : `aria-describedby="{descId}"` conditionnel sur `description ? descId : undefined` (alignement exact).
- **H-2 IME composition** — NON APPLICABLE Drawer (pas d'input).
- **H-3 Multi-select binding natif watch()** — NON APPLICABLE Drawer (pas de Select).
- **H-4 type=number string coercion** — NON APPLICABLE Drawer (émet boolean strict).

**Leçons MEDIUM 10.17 applicables à Drawer** :
- **M-1 role="img" vs role="status"** — APPLIQUÉ analogue : `role="complementary"` choix délibéré vs `role="dialog"` Reka UI default. Piège #27 documenté.
- **M-2/M-3 DRY labels/types via registry** — APPLIQUÉ : types `DrawerSide` / `DrawerSize` importés depuis `registry.ts` (source unique).
- **M-5 SSR guard `import.meta.env.DEV`** — APPLIQUÉ Task 3.15 (runtime warn 3 paths disabled dev-only, silencieux SSR + prod).

**Règle d'or tests E2E effet observable** (10.5+10.16 H-3 + 10.17) → appliquée systématique Task 5.2 Drawer avec emphase portal-aware `document.body`.

### Project Structure Notes

- Dossier `frontend/app/components/ui/` **existant** (6 composants 10.15+10.16+10.17 + 2 brownfield), ajouts : `Drawer.vue`, `Drawer.stories.ts`, extension `registry.ts`. Collision zéro.
- Tests sous `frontend/tests/components/ui/` **existant** (pattern établi 10.15+10.16+10.17), 4 nouveaux fichiers + 1 `.test-d.ts` byte-cohérents.
- Pas de modification `nuxt.config.ts` (Drawer auto-importé via `pathPrefix: false` existant CLAUDE.md).
- `tsconfig.json` frontend déjà `strict: true` → types Drawer hérités sans override.
- `frontend/.storybook/main.ts` **inchangé** (glob déjà étendu 10.15).
- `frontend/.storybook/preview.ts` **inchangé** (toggle dark + a11y config stable 10.14+10.15).
- `main.css` **inchangé** (tokens surface/dark/brand-green déjà livrés 10.14+10.15 — Drawer consomme).
- `vitest.config.ts` **inchangé** (typecheck glob déjà configuré 10.15).
- Pattern Nuxt 4 auto-imports avec `pathPrefix: false` : `<Drawer>` disponible globalement sans import explicite. Vérifier absence collision via Task 1.4 (brownfield `FullscreenModal.vue` + `SourceCitationDrawer.vue` gravity/ ≠ `Drawer.vue` — nom-distinct).
- **Reka UI 2.9.6 déjà installé** (10.14) — vérifier Task 1.5 les exports `DialogRoot/Portal/Overlay/Content/Close/Title/Description` + `ScrollAreaRoot/Viewport/Scrollbar/Thumb` disponibles. **Pas de nouvelle dépendance ajoutée** (budget bundle préservé).
- **Pas de `@vueuse/core` dépendance** introduite (mobile fullscreen CSS-only évite `useMediaQuery`).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.18] — spec détaillée 8 AC + NFR + estimate M + architecture_alignment (UX Step 11 §4 P0, Q15 Reka UI, UX spec SourceCitationDrawer)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-6-Q15] — décision Reka UI nu (pas shadcn-vue)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-11-§4-Navigation] — patterns navigation P0/P1
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-12-§9-Drawer-Latéral-Patterns] — 3 usages drawer (SourceCitationDrawer 480 px, IntermediaryComparator 560 px, PeerReviewThreadedPanel 480 px) + règles transversales (ouverture explicite, fermeture 3 chemins, role="complementary", focus trap optionnel, ScrollArea, pas drawer-in-drawer)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-8-Tokens-@theme] — tokens surface-* / dark-* / brand-* consommés
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-13-A11y-WCAG-2.1-AA] — 13 items checklist (role, aria-*, contraste 4.5:1, focus visible, prefers-reduced-motion)
- [Source: CLAUDE.md#Dark-Mode-OBLIGATOIRE] — dark mode tous composants via variantes `dark:`
- [Source: CLAUDE.md#Reutilisabilite-Composants] — discipline > 2 fois = extraction primitive (3 consommateurs Drawer = justifiation forte)
- [Source: ~/.claude/rules/typescript/coding-style.md] — TypeScript strict, `interface` pour props, pas de `any`, `unknown` narrowing, types dérivés `as const`
- [Source: frontend/app/components/ui/registry.ts] — registre CCC-9 existant à étendre 2 nouveaux tuples
- [Source: frontend/app/components/ui/Badge.vue] — pattern primitive 10.17 (script setup + computed + slots + tokens @theme + runtime checks dev-only + soft-bg contraste AA)
- [Source: frontend/app/components/ui/Button.vue] — pattern primitive 10.15 (focus-visible ring-brand-green post-darken)
- [Source: frontend/app/components/gravity/SourceCitationDrawer.vue] — squelette 10.14 consommateur futur (ScrollAreaRoot pattern byte-identique à reprendre)
- [Source: frontend/app/components/gravity/SignatureModal.vue] — modal Reka UI DialogRoot (pattern CONTRASTE : role="dialog" pour SignatureModal bloquant vs role="complementary" pour Drawer consultatif — distinction architecturale)
- [Source: frontend/app/components/gravity/ImpactProjectionPanel.vue] — autre usage ScrollArea (pattern stable)
- [Source: frontend/.storybook/main.ts:6] — glob `gravity/ + ui/` déjà étendu 10.15 (inchangé 10.18)
- [Source: frontend/.storybook/preview.ts] — decorator dark mode + a11y config réutilisés byte-identique
- [Source: frontend/vitest.config.ts] — typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15
- [Source: frontend/package.json:30] — `reka-ui ^2.9.6` installé (10.14)
- [Source: docs/CODEMAPS/ui-primitives.md#§5-Pieges] — 26 pièges cumulés 10.14-10.17 → extension +6 (27-32) Drawer
- [Source: docs/CODEMAPS/ui-primitives.md#§2-Arborescence] — arbo existante à étendre +4 lignes Drawer
- [Source: docs/CODEMAPS/methodology.md#§4ter-Comptages-runtime-OBLIGATOIRES] — Pattern A + Pattern B capitalisés à appliquer proactivement, extension §4ter application 10.18
- [Source: _bmad-output/implementation-artifacts/10-14-setup-storybook-6-stories.md] — 6 stories initiaux + SourceCitationDrawer squelette (consommateur futur Drawer)
- [Source: _bmad-output/implementation-artifacts/10-14-code-review-2026-04-21.md#HIGH-2] — leçon `role="complementary"` vs `role="dialog"` (drawer consultatif != modal) capitalisée infra 10.18
- [Source: _bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md] — patterns primitive 1 byte-identique (frozen tuple + commit intermédiaire + scan NFR66 + CODEMAPS 5 sections + 5 Q tranchées + co-localisation stories)
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md#HIGH-1] — compile-time enforcement `.test-d.ts`
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md#HIGH-2] — darken tokens AA brand-green #047857 + **délégation Storybook runtime pour portail** (capitalisée infra 10.18 piège #28)
- [Source: _bmad-output/implementation-artifacts/10-16-ui-input-textarea-select.md] — patterns primitive 3 byte-identique (union discriminée multi-composant + describedBy computed + runtime enforcement)
- [Source: _bmad-output/implementation-artifacts/10-16-code-review-2026-04-22.md] — H-1 describedBy aligné v-if (APPLIQUÉ Drawer Task 3.4) + H-2 IME + H-3 multi-binding + H-4 type coercion + M-3 Storybook count runtime (Pattern B capitalisé) + Pattern A (DOM pas state)
- [Source: _bmad-output/implementation-artifacts/10-17-ui-badge-tokens-semantiques.md] — patterns primitive 4 byte-identique + CRITICAL-3 console spy + Pattern A/B proactifs (capitalisé 10.18)
- [Source: _bmad-output/implementation-artifacts/10-17-code-review-2026-04-22.md (si existant)] — leçons post-merge 10.17 à consulter pour patterns bonus ; sinon référence 10.16 code-review comme fallback
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — DEF-10.15-* + DEF-10.16-* + DEF-10.17-* tracés (format réutiliser `DEF-10.18-1 beforeClose API Phase Growth` si émergence)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

**Baseline pré-dev (pattern 4ter comptages runtime OBLIGATOIRES)** :
```bash
$ cd frontend && npm run test -- --run 2>&1 | tail -5
# (consigner exact output — attendu 555 passed post-10.17 + 1 pré-existant useGuidedTour hors scope)

$ npm run test:typecheck 2>&1 | tail -5
# (consigner exact output — attendu 40 passed post-10.17 : 6 Button + 8 Input + 7 Select + 6 Textarea + 13 Badge)

$ node -e "console.log(Object.keys(require('reka-ui')).filter(k => k.startsWith('Dialog') || k.startsWith('ScrollArea')))"
# (consigner exact list exports Dialog* + ScrollArea* disponibles Reka UI 2.9.6)
```

**Post-dev Story 10.18 (sortie brute — pattern 4ter respecté)** :
```bash
$ npm run test -- --run 2>&1 | tail -4
# (consigner exact — cible ≥ 569 passed)

$ npm run test:typecheck 2>&1 | tail -4
# (consigner exact — cible ≥ 50 passed)

$ cd frontend && npm run storybook:build 2>&1 | tail -5
# (consigner build time + output dir)

$ jq '.entries | keys | length' storybook-static/index.json
# (consigner total — baseline 168 post-10.17, cible ≥ 184)

$ jq '[.entries | to_entries[] | select(.value.id | startswith("ui-drawer"))] | length' storybook-static/index.json
# (consigner Drawer-only — cible ≥ 16)

$ du -sh storybook-static
# (consigner — cible ≤ 15 MB)

$ grep -oE "dark:" frontend/app/components/ui/Drawer.vue | wc -l
# (consigner — cible ≥ 8 sans inflation)

$ grep -nE "#[0-9A-Fa-f]{3,8}\b" frontend/app/components/ui/Drawer.vue frontend/app/components/ui/Drawer.stories.ts
# (aucun hit attendu hors commentaires)

$ grep -nE ": any\b|as unknown" frontend/app/components/ui/Drawer.vue
# (aucun hit attendu)
```

### Completion Notes List

{{completion notes rédigées par dev agent après exécution — consigner EXACT comptages runtime Storybook pattern B pré-claim complétude}}

### File List

{{file list rédigé par dev agent post-implémentation}}

### Change Log

| Date | Commit | Description |
|------|--------|-------------|
| {{YYYY-MM-DD}} | {{hash}} | feat(10.18): ui/Drawer primitive + registry CCC-9 2 tuples + role=complementary override |
| {{YYYY-MM-DD}} | {{hash}} | feat(10.18): Drawer stories CSF3 + tests behavior/a11y + docs CODEMAPS §3.5 + count runtime vérifié |
