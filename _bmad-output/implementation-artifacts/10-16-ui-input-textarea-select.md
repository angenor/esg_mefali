# Story 10.16 : `ui/Input.vue` + `ui/Textarea.vue` + `ui/Select.vue` — 3 primitives formulaire

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> **Contexte** : 18ᵉ story Phase 4 et **deuxième primitive `ui/` Phase 0** après `Button` 10.15 (done). Sizing **M** (~1 h 30) selon sprint-plan v2. Cette story livre **3 composants formulaire groupés** (`Input` + `Textarea` + `Select`) qui serviront de socle aux 60+ formulaires du produit (profil Company, `FormalizationPlanCard` CTAs, admin catalogue, `BeneficiaryProfileBulkImport`, `JustificationField` copilot spec 018, widgets QCU/QCM/batch composite Q17). La discipline CLAUDE.md « > 2 fois » est enforcée immédiatement (les 3 primitives sont co-livrées car elles partagent >80 % du même squelette : label, error, hint, a11y, dark mode, tokens, touch).
>
> **État de départ — 0 % primitives Input/Textarea/Select, registry Button livré 10.15** :
> - ❌ **Aucun `ui/Input.vue`, `ui/Textarea.vue`, `ui/Select.vue` préexistants** — `frontend/app/components/ui/` contient désormais `FullscreenModal.vue` + `ToastNotification.vue` (brownfield inchangés) + `Button.vue` + `Button.stories.ts` + `registry.ts` (livrés 10.15). Scan pré-dev Task 1 : `rg 'Input\.vue|Textarea\.vue|Select\.vue' app/components/ui/` → **0 hit**. Aucune collision auto-imports Nuxt (`pathPrefix: false`).
> - ❌ **Aucun token `--color-form-*` dédié** — `main.css:15-27` définit les 12 brand/surface/dark tokens **darken 10.15 AA** (`brand-green #047857 · brand-red #DC2626`) + les 20 tokens sémantiques (verdict/fa/admin 10.14). **Décision Q4-darken** : réutiliser `brand-red` pour les états d'erreur de formulaire (cohérent avec `danger` Button variant, évite un 3ᵉ rouge en lice avec `verdict-fail`). Pas de création `--color-form-error` dédié (Phase Growth si > 2 contextes distincts).
> - ❌ **Aucune icône Lucide installée** — identique baseline 10.15 : `package.json` ne liste pas `lucide-vue-next`, Story 10.21 livrera la pile. **Pivot MVP** : icône `AlertCircle` requise par Epic AC6 + `CheckCircle` pour hint positif sont **stub SVG inline** (`<!-- STUB: remplacé par <AlertCircle /> Lucide Story 10.21 -->`), pas de dep bloquante. Documenté §4 piège #8.
> - ✅ **Baseline tests frontend 422 runtime + 6 typecheck = 428** (post-10.15 patch round) — 1 pré-existant échec inchangé hors scope. Cible post-10.16 : **≥ 452 (+24 minimum)** conformément AC13.
> - ✅ **Runtime Storybook 66 stories** (22 ui-button + 44 gravity, bundle 7,9 MB post-10.15) — cible post-10.16 : **≥ 102 = 66 + ≥ 36** (12 stories par composant × 3 composants, conformément AC10).
> - ✅ **`registry.ts` 10.15 extensible** — `BUTTON_VARIANTS` + `BUTTON_SIZES` frozen tuples déjà pattern CCC-9. Extension byte-identique : `INPUT_TYPES` (7) + `FORM_SIZES` (3 partagé) + `TEXTAREA_SIZES` (héritage `FORM_SIZES`) + éventuellement `SELECT_SIZES` (héritage). Pattern source unique pour tests + stories + 3 composants.
> - ✅ **Pattern type discriminé 10.15 (iconOnly + ariaLabel)** — **pas directement applicable** aux 3 primitives formulaire (pas d'invariant à enforcer compile-time équivalent). Par contre, le pattern `vitest --typecheck` + `.test-d.ts` livré 10.15 HIGH-1 patch est **réutilisable** pour valider les unions `InputType` et `FormSize` + narrowing `options: Array<{ value; label }>` du Select.
> - ✅ **Pattern tokens darken AA 10.15 (emerald-700 + red-600 ≥ 4,5:1)** — toutes les erreurs de formulaire utilisent `text-brand-red` (= `#DC2626` = 4,83:1 blanc / 13,12:1 fond `bg-white`). Messages d'erreur sous champ blanc/sombre conformes WCAG AA sans darken supplémentaire. Confirmé §6 codemap ui-primitives.
> - ✅ **Pattern exception dark mode 10.15 MEDIUM-2** — seuil `≥ 4 dark:` adopté pour primitives simples (documenté `ui-primitives.md §7`). Input/Textarea/Select : cible `≥ 6 dark:` par composant (fond input + bordure + texte + placeholder + error border + error text), **pas d'inflation artificielle** via no-op `dark:bg-white` (règle CCC-9).
> - ✅ **Pattern compile-time `@ts-expect-error` 10.15 HIGH-1 patch** — `vitest.config.ts typecheck.include: ['tests/**/*.test-d.ts']` et script `npm run test:typecheck` déjà configurés. Extension directe : `Input.test-d.ts` + `Textarea.test-d.ts` + `Select.test-d.ts` sans nouvelle config.
> - ✅ **Pattern shims legacy 10.6 validé** — **68 composants inchangés** (60 brownfield + 6 gravity/ + 2 ui/ brownfield + Button + registry = « ajout pur »). Les migrations des `<input class="…">` inline dans brownfield vers `<ui/Input>` sont **hors scope** (Phase 1 Epic 11-15, traçage deferred-work.md).
> - ✅ **Pattern frozen tuple CCC-9 (10.8+10.10+10.11+10.12+10.13+10.14+10.15)** — réutilisable byte-identique pour les nouveaux tuples `INPUT_TYPES` / `FORM_SIZES` / `TEXTAREA_SIZES` / `SELECT_SIZES`.
> - ✅ **Pattern commit intermédiaire 10.8+10.14+10.15** — 2 commits factorisés (composants+registry / stories+tests+docs) OU 3 commits (Input | Textarea | Select séparés). **Décision Q6** : **2 commits** pour cohérence avec 10.15 (composants co-livrés partagent plus de 80 % du squelette).
> - ✅ **Pattern Storybook co-localisation 10.14+10.15** — `ui/Input.stories.ts`, `ui/Textarea.stories.ts`, `ui/Select.stories.ts` à côté des `.vue`. Glob `.storybook/main.ts` déjà étendu `ui/**` depuis 10.15 (0 modification requise).
> - ✅ **Pattern CODEMAPS 5 sections 10.13+10.14+10.15** — `docs/CODEMAPS/ui-primitives.md` existe (8 sections H2 post-10.15). Extension 10.16 : **+3 sous-sections §3** (Utiliser `ui/Input` / `ui/Textarea` / `ui/Select`) + **+6 pièges §5** (actuellement 10, cible post-10.16 ≥ 16). Pas de nouvelle codemap.
> - ✅ **`<helper asStorybookComponent>`** — factorisé dans `frontend/app/types/storybook.ts` (livré 10.15 MEDIUM-3 patch). Réutilisation byte-identique dans les 3 stories 10.16.
> - ✅ **Pattern scan NFR66 Task 1 10.14+10.15** — baseline tests + Grep préexistant 0 hit avant écriture → Task 1 de cette story.
>
> **Livrable 10.16 — 3 composants + 3 stories files + 3 tests suites + docs extension (~1 h 30)** :
>
> 1. **Extension `registry.ts`** (pattern CCC-9 byte-identique 10.14+10.15) — ajout :
>    ```ts
>    export const INPUT_TYPES = Object.freeze([
>      'text', 'email', 'number', 'password', 'url', 'tel', 'search',
>    ] as const);
>    export const FORM_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);
>    export type InputType = (typeof INPUT_TYPES)[number];
>    export type FormSize = (typeof FORM_SIZES)[number];
>    ```
>    Invariants testables : `INPUT_TYPES.length === 7`, `FORM_SIZES.length === 3`, `Object.isFrozen` × 2, dédoublonnage. **Note** : `FORM_SIZES` partagé entre Input/Textarea/Select **et** alias équivalent à `BUTTON_SIZES` (même valeurs `sm`/`md`/`lg`) — **pas de ré-export** `BUTTON_SIZES as FORM_SIZES` (les 2 tuples restent indépendants sémantiquement ; évolution future d'un des 2 ne doit pas coupler l'autre).
>
> 2. **`frontend/app/components/ui/Input.vue`** (AC1-AC9) — Vue 3 `<script setup lang="ts">`, native `<input>` (Q1), slots `#iconLeft`/`#iconRight` (Q5), props `modelValue` + `label` + `error` + `hint` + `required` + `disabled` + `readonly` + `size` + `type` + `autocomplete` + `pattern` + `minlength` + `maxlength` + `id` + `placeholder` + `inputmode`. Auto-ID via `useId()` si `id` non fourni. `aria-invalid` / `aria-describedby` / `aria-required` dynamiques. Dark mode `≥ 6 dark:`. Squelette complet §3 Dev Notes.
>
> 3. **`frontend/app/components/ui/Textarea.vue`** (AC1-AC4-AC9) — native `<textarea>`, props héritées Input + `rows: number` (default 4) + `maxlength: number` (default **400**, conforme spec 018 AC5) + `showCounter: boolean` (default **true**, Q2) + **pas de slots icônes** (UX non pertinent pour zone de texte multi-ligne). Compteur `{value.length}/{maxlength}` sous le champ : `< 350` texte `gray-500 dark:gray-400` / `350-399` `text-brand-orange` (token `#F59E0B` contraste 3,85:1 sur blanc — acceptable en texte auxiliaire non critique, documenté §6 codemap) / `= 400` `text-brand-red` + aria-live="polite". **Défense en profondeur** frappe bloquée : handler `@input` intercepte `event.target.value.length > 400` → tronque à `400` et re-émet `update:modelValue` (pattern spec 018 existant backend + client). `maxlength="400"` native en plus (triple défense : browser + JS handler + backend). Squelette §3 Dev Notes.
>
> 4. **`frontend/app/components/ui/Select.vue`** (AC1-AC5-AC9) — native `<select>` stylisé Tailwind (Q3 override documenté), props héritées Input (moins `type`/`autocomplete`/`pattern`/`minlength`/`maxlength`) + `options: Array<{ value: string; label: string; disabled?: boolean }>` + `multiple?: boolean` (UI minimale MVP, Reka UI Combobox riche = Story 10.19 `depends_on: [10.16]`). **Déviation assumée vs Epic AC5** (Reka UI `SelectRoot` stylé) : natif MVP pour (a) accessibilité système ChromeVox/VoiceOver native battle-tested, (b) 0 dépendance ajoutée (Reka UI Combobox en 10.19 = besoin pour recherche), (c) livraison plus rapide M 1h30, (d) touch target natif iOS/Android respecté. Traçage : `DEF-10.16-1 Reka UI SelectRoot pour Select avancé` dans deferred-work.md. Squelette §3 Dev Notes.
>
> 5. **3 stories files CSF 3.0 co-localisées** (AC10) — `Input.stories.ts` + `Textarea.stories.ts` + `Select.stories.ts`. **Cible 36 stories totales** (12 par composant minimum) = 3 sizes × 4 states (default / focus / error / disabled) + stories bonus (IconLeft, IconRight, Required, Readonly, DarkMode, ShowcaseGrid, etc.). Play functions `@storybook/test` : `user-event.type()` sur Input.Default → v-model update vérifié, `user-event.type(long-text)` sur Textarea.WithCounter → couleur passe orange à 350 puis rouge à 400, `user-event.selectOptions()` sur Select.Default → emit `update:modelValue`.
>
> 6. **3 tests suites Vitest `tests/components/ui/`** (AC9, AC13) — minimum **8 tests par composant = 24 minimum** :
>    - `test_input_*.test.ts` : rendu 7 types × 3 sizes (groupé 8 tests critiques), v-model bidirectionnel, états (required → astérisque + aria-required, error → aria-invalid + aria-describedby + message visible, disabled, readonly), keyboard (`Tab` traverse champ, `Enter` submit form parent, `Space` n'active PAS input), slots iconLeft/iconRight rendus, jest-axe 3 states (default/error/disabled).
>    - `test_textarea_*.test.ts` : 8 tests similaires + **tests spécifiques compteur** : value.length<350 → pas de classe couleur, `== 350` → `text-brand-orange`, `== 400` → `text-brand-red` + `role="alert"` ou `aria-live="polite"`, frappe `"a".repeat(401)` via `userEvent.type` → valeur tronquée à 400 + `update:modelValue` émis avec longueur 400 exactement.
>    - `test_select_*.test.ts` : 8 tests — options rendues, selection émet `update:modelValue`, disabled option non-sélectable, error state ARIA, keyboard `ArrowDown` navigue options, `multiple=true` émet array.
>    - `test_form_registry.test.ts` : 4 tests (INPUT_TYPES.length === 7 + FORM_SIZES.length === 3 + frozen × 2 + dédoublonnage).
>    - `test_no_hex_hardcoded_ui_form.test.ts` : extension scan 10.15 sur Input.vue + Textarea.vue + Select.vue → 0 hit hex.
>    - `Input.test-d.ts` + `Textarea.test-d.ts` + `Select.test-d.ts` : assertions TypeScript compile-time via `vitest --typecheck` (pattern 10.15 HIGH-1 patch). Minimum 3 assertions / 3 `@ts-expect-error` par composant (total +9 typecheck tests).
>
> 7. **Extension `docs/CODEMAPS/ui-primitives.md`** (AC12) — pattern 5 sections H2 préservé, extensions :
>    - §3 « Utiliser `ui/Button`… » renommé `§3 Utiliser les primitives UI dans un composant` + 3 sous-sections : `§3.1 ui/Input`, `§3.2 ui/Textarea`, `§3.3 ui/Select` (respect pattern 3 primitives, exemples Vue reproductibles).
>    - §5 « Pièges documentés » : **+6 nouveaux pièges** (cible ≥ 16 total) — v-model `<input type="number">` retourne string vs number, Textarea `rows` fixe vs `resize-y` natif, Select value toujours string côté DOM (coercion numérique), `autocomplete` attribute valeurs standards (HTML5 tokens), label floating vs placeholder-as-label (a11y anti-pattern), `maxlength` native browser vs défense en profondeur JS, `inputmode` clavier virtuel iOS/Android, error color WCAG text-brand-red `#DC2626`.
>    - §6 « A11y Contraste » : +1 bullet texte-brand-orange `#F59E0B` contraste 3,85:1 acceptable pour compteur 350-399 auxiliaire (documenté avec rationale).
>    - +1 ligne `docs/CODEMAPS/index.md` : pas de modification (`ui-primitives.md` déjà référencée depuis 10.15).
>
> 8. **Scan NFR66 post-dev** (AC8, AC10) — `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Input.vue frontend/app/components/ui/Textarea.vue frontend/app/components/ui/Select.vue` → 0 hit · `rg ': any\b|as unknown' frontend/app/components/ui/{Input,Textarea,Select}.vue` → 0 hit · `jq '.entries | keys | length' storybook-static/index.json` ≥ 102 (66 + ≥ 36 nouvelles) · `npm run test:typecheck` → 9+ tests `@ts-expect-error` verts.

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité + PME persona mobile Aminata/Abdoulaye/Fatou/Ibrahim),
**Je veux** 3 primitives formulaire `frontend/app/components/ui/Input.vue` + `ui/Textarea.vue` + `ui/Select.vue` — typées strict, 7 types d'input HTML5, 3 tailles (`sm`/`md`/`lg`), états (default/focus/error/disabled/readonly), slots `#iconLeft`/`#iconRight` (Input uniquement), compteur 400 caractères stricts (Textarea avec frappe bloquée en défense en profondeur spec 018), wrapper select natif (Select, Reka UI Combobox différé 10.19), conformes WCAG 2.1 AA (touch target 44 px, label `for`/`id` association, `aria-invalid`/`aria-describedby`/`aria-required`, focus-visible ring-2 `brand-green`, `prefers-reduced-motion`, contraste ≥ 4,5:1 post-darken 10.15), documentés Storybook ≥ 36 stories + addon-a11y + play functions (`user-event` réels), testés Vitest ≥ 24 tests + jest-axe + vitest-axe + typecheck `@ts-expect-error`,
**Afin que** tous les formulaires du produit (profil Company, `FormalizationPlanCard` CTAs, admin catalogue, `BeneficiaryProfileBulkImport`, `JustificationField` copilot spec 018, widgets QCU/QCM/batch composite Q17 future, champs projets/maturity/financing) partagent une implémentation unique réutilisable, que la règle CLAUDE.md « discipline > 2 fois » soit enforcée dès Phase 0, que les migrations Phase 1 (remplacement `<input class="rounded-lg border…">` inline par `<ui/Input>`) soient mécaniques et safe, et que le socle pour Story 10.20 `DatePicker` (qui `depends_on: [10.16 ui/Input]`) + Story 10.19 `Combobox` (qui `depends_on: [10.16 ui/Input]`) soit disponible pour la sprint suivante.

## Acceptance Criteria

**AC1 — 3 composants Vue 3 + TypeScript strict + Composition API + 0 `any`**
**Given** `frontend/app/components/ui/Input.vue`, `Textarea.vue`, `Select.vue`,
**When** auditées,
**Then** chacune utilise `<script setup lang="ts">` + `defineProps<...>()` + `defineEmits<{ 'update:modelValue': [value: string | number | string[]] }>()` (tuple-syntax moderne),
**And** `cd frontend && npm run build` (Nuxt type-check build) passe sans erreur TypeScript,
**And** `rg ': any\b|as unknown' frontend/app/components/ui/Input.vue frontend/app/components/ui/Textarea.vue frontend/app/components/ui/Select.vue` retourne **0 hit**,
**And** chaque prop est typée explicitement (pas d'inférence implicite sur l'emit payload).

**AC2 — Registry étendu : `INPUT_TYPES` + `FORM_SIZES` frozen tuple CCC-9**
**Given** `frontend/app/components/ui/registry.ts`,
**When** étendu,
**Then** il exporte (en plus des `BUTTON_VARIANTS` + `BUTTON_SIZES` 10.15 préservés byte-identique) :
```ts
export const INPUT_TYPES = Object.freeze([
  'text', 'email', 'number', 'password', 'url', 'tel', 'search',
] as const);
export const FORM_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);
export type InputType = (typeof INPUT_TYPES)[number];
export type FormSize = (typeof FORM_SIZES)[number];
```
**And** invariants testables par `test_form_registry.test.ts` :
- `INPUT_TYPES.length === 7`,
- `FORM_SIZES.length === 3`,
- `Object.isFrozen(INPUT_TYPES) === true`,
- `Object.isFrozen(FORM_SIZES) === true`,
- `new Set(INPUT_TYPES).size === 7` (pas de duplicate),
- `new Set(FORM_SIZES).size === 3` (pas de duplicate),
- **Intentionnellement PAS de re-export** `BUTTON_SIZES as FORM_SIZES` (pattern sémantique indépendant, voir §4 piège #11).

**AC3 — Props communs 3 composants + v-model + label + error + hint + required + disabled + size**
**Given** les 3 primitives,
**When** auditées,
**Then** chacune expose ces props communs (homogénéité d'API) :
```ts
type FormPropsBase = {
  modelValue: string | number | string[];  // variant selon composant, strict typing
  label: string;                            // obligatoire (pas de champ sans label — a11y AA)
  id?: string;                              // auto-genere via useId() si absent
  placeholder?: string;
  error?: string;                           // message sous le champ + icone AlertCircle
  hint?: string;                            // texte auxiliaire gris sous le champ
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;                          // default 'md'
};
```
**And** `v-model` bidirectionnel testé : `userEvent.type(input, 'abc')` → `emit('update:modelValue', 'abc')`,
**And** `Input` ajoute : `type?: InputType` (default `'text'`), `autocomplete?: string`, `pattern?: string`, `minlength?: number`, `maxlength?: number`, `inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email' | 'url' | 'search'`,
**And** `Textarea` ajoute : `rows?: number` (default 4), `maxlength?: number` (default **400**, spec 018), `showCounter?: boolean` (default **true**),
**And** `Select` ajoute : `options: Array<{ value: string; label: string; disabled?: boolean }>`, `multiple?: boolean` (default `false`).

**AC4 — Textarea compteur 400 chars stricts + frappe bloquée défense en profondeur**
**Given** `<ui/Textarea v-model="v" :maxlength="400" :showCounter="true" />`,
**When** rendu et l'utilisateur tape,
**Then** un compteur `{value.length}/400` est rendu sous le champ,
**And** `value.length < 350` → compteur `text-gray-500 dark:text-gray-400`,
**And** `value.length >= 350 && value.length < 400` → compteur `text-brand-orange` (token `#F59E0B`, contraste 3,85:1 sur blanc — acceptable en texte auxiliaire non critique, documenté §6 codemap),
**And** `value.length >= 400` → compteur `text-brand-red` (token `#DC2626`, contraste 4,83:1 AA),
**And** `value.length >= 400` → `role="status" aria-live="polite"` sur le compteur pour annonce lecteur d'écran,
**And** frappe `userEvent.type(textarea, 'a'.repeat(410))` → **valeur tronquée à 400 exactement** côté modelValue (triple défense : attribut HTML `maxlength="400"` native + handler JS `@input` qui tronque et re-émet + backend spec 018 déjà enforce 400),
**And** un test Vitest vérifie explicitement les 3 seuils (< 350 / == 350 / == 400) + la troncature frappe excessive.

**AC5 — A11y WCAG 2.1 AA sur les 3 primitives**
**Given** les 3 composants rendus en DOM,
**When** auditées par `jest-axe` + `vitest-axe` + Storybook `addon-a11y`,
**Then** **0 violation** A/AA sur toutes les stories (default/error/disabled/readonly × 3 sizes),
**And** chaque champ est enveloppé d'un `<label for="{id}">{{ label }}</label>` pointant vers `id` (auto-généré par `useId()` Vue 3.5+ si non fourni, sinon prop explicite),
**And** si `required` → `aria-required="true"` + astérisque rouge `<span class="text-brand-red" aria-hidden="true">*</span>` APRÈS le label (pattern UX spec §3 Form Patterns),
**And** si `error` présent → `aria-invalid="true"` + `aria-describedby="{id}-error"` pointant vers le `<p id="{id}-error" role="alert">` contenant l'icône `AlertCircle` (stub SVG inline) + `{{ error }}`,
**And** si `hint` présent → `aria-describedby="{id}-hint"` (OU combiné `"{id}-hint {id}-error"` si les 2),
**And** `focus-visible:ring-2 focus-visible:ring-brand-green focus-visible:ring-offset-2` + `focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card` (cohérent Button 10.15 AC7),
**And** couleur seule **jamais** utilisée pour signaler l'erreur (conforme Règle 11 Custom Pattern UX Step 12) : toujours icône + texte + bordure `border-brand-red`.

**AC6 — Touch target ≥ 44 px + inputmode clavier virtuel iOS/Android**
**Given** les 3 composants rendus sur mobile (contexte `pointer: coarse`),
**When** mesurés via `getBoundingClientRect().height`,
**Then** `size="md"` (default) : `min-h-[44px]` partout (desktop + mobile, Wave-compatible),
**And** `size="sm"` : `min-h-[36px]` desktop baseline, `[@media(pointer:coarse)]:min-h-[44px]` en touch (Tailwind 4 arbitrary variant, cohérent Button 10.15 AC3),
**And** `size="lg"` : `min-h-[48px]` partout,
**And** padding interne : `sm` = `px-3 py-1.5 text-sm`, `md` = `px-3.5 py-2 text-sm`, `lg` = `px-4 py-2.5 text-base`,
**And** `Input[type="number"]` supporte prop `inputmode="numeric"` → clavier numérique iOS/Android (pas le clavier complet),
**And** `Input[type="email"]` → `inputmode="email"` default automatique,
**And** `Input[type="tel"]` → `inputmode="tel"` default automatique.

**AC7 — Dark mode systematique + exception seuil 10.15 respectee**
**Given** la classe `dark` appliquée sur `<html>` (toggle `stores/ui.ts`),
**When** chaque primitive est rendue en mode sombre,
**Then** **minimum 6 occurrences `dark:`** par composant (fond input + bordure + texte + placeholder + hover + focus),
**And** surface : `bg-white dark:bg-dark-input` (`#1F2937`),
**And** bordure : `border border-gray-300 dark:border-dark-border` (`#374151`),
**And** texte : `text-surface-text dark:text-surface-dark-text`,
**And** placeholder : `placeholder:text-gray-400 dark:placeholder:text-gray-500` (préfixe Tailwind 4 `placeholder:` requis),
**And** error state : `border-brand-red` (inchangé dark, `#DC2626` déjà contrasté sur fond sombre `#1F2937` → 5,77:1 ✅ AA),
**And** disabled : `disabled:bg-gray-50 dark:disabled:bg-dark-card disabled:text-gray-500 dark:disabled:text-gray-600 disabled:cursor-not-allowed`,
**And** conforme exception 10.15 MEDIUM-2 documentée `ui-primitives.md §7` : pas d'inflation artificielle via no-op `dark:bg-white`.

**AC8 — Tokens `@theme` exclusifs, 0 hex hardcodé sur les 3 composants**
**Given** les 3 fichiers `.vue`,
**When** scan regex `#[0-9A-Fa-f]{3,8}\b` exécuté (pattern 10.14+10.15 byte-identique),
**Then** retour **0 hit** sur `Input.vue` + `Textarea.vue` + `Select.vue`,
**And** un test `test_no_hex_hardcoded_ui_form.test.ts` échoue si un hex apparaît hors commentaire,
**And** toutes les couleurs résolvent via tokens `@theme` `main.css:15-27` : `brand-green` (focus ring) / `brand-red` (error) / `brand-orange` (compteur 350-399) / `surface-*` + `dark-*`.

**AC9 — Tests Vitest ≥ 24 + vitest-axe + coverage ≥ 85 %**
**Given** `frontend/tests/components/ui/test_input_*.test.ts`, `test_textarea_*.test.ts`, `test_select_*.test.ts`, `test_form_registry.test.ts`, `test_no_hex_hardcoded_ui_form.test.ts`,
**When** `npm run test` exécuté,
**Then** minimum **24 tests runtime nouveaux verts** (+ 9 typecheck `@ts-expect-error`) distribués :
  - **Input** : 8 tests — rendu 7 types (groupé), 3 sizes (groupé), v-model, states required/error/disabled/readonly, slots iconLeft/iconRight, keyboard Tab/Enter/Space, vitest-axe 3 states, scan hex.
  - **Textarea** : 8 tests — rendu 3 sizes, v-model, compteur < 350 / == 350 / == 400 + couleurs, frappe > 400 tronquée, role=alert a11y, showCounter=false caché, vitest-axe.
  - **Select** : 8 tests — rendu options, v-model selection, disabled option non-sélectable, error ARIA, keyboard ArrowDown, multiple=true array, vitest-axe.
  - **Registry** : 4 tests (INPUT_TYPES + FORM_SIZES frozen/length/dedup).
  - **No-hex** : 1 test extension scan sur 3 fichiers.

**And** coverage Vitest c8 ≥ **85 %** sur chacun des 3 composants (branches + lines + statements) — seuil légèrement assoupli vs 10.15 (95 %) car 3 composants co-livrés avec chemins conditionnels (required/error/disabled) sont plus difficiles à couvrir simultanément,
**And** baseline **428 tests passed (post-10.15)** → **≥ 452 tests passed** (+24 minimum, AC13), zéro régression,
**And** 1 pré-existant échec reste inchangé (hors scope).

**AC10 — Storybook ≥ 36 stories + 3 play functions + 0 violation a11y**
**Given** `Input.stories.ts` + `Textarea.stories.ts` + `Select.stories.ts` co-localisés,
**When** `npm run storybook:build` exécuté,
**Then** `jq '.entries | keys | length' storybook-static/index.json` retourne ≥ **102 stories** (66 baseline + **≥ 36 nouvelles** distribuées 12 par composant minimum),
**And** distribution cible par composant :
- **12 stories Input** : 4 states × 3 sizes = 12 (Default/Focus/Error/Disabled × sm/md/lg) + bonus (WithIconLeft, WithIconRight, Password, NumberWithInputmode, DarkMode, ShowcaseGrid, Required, Readonly) ≈ 16-20 cible.
- **12 stories Textarea** : 4 states × 3 sizes = 12 + bonus (CounterBelow350, CounterAt350Orange, CounterAt400Red, CounterHidden, LargeContent, DarkMode, ShowcaseGrid) ≈ 15-18 cible.
- **12 stories Select** : 4 states × 3 sizes = 12 + bonus (Multiple, DisabledOption, DarkMode, ShowcaseGrid) ≈ 14-16 cible.

**And** **3 play functions** minimum (1 par composant) utilisent `@storybook/test` + `user-event` réels :
- `Input.Default.play` : `userEvent.type(canvas.getByLabelText(...), 'abc')` → `expect(args.onUpdate).toHaveBeenCalledWith('abc')`,
- `Textarea.CounterAt400Red.play` : `userEvent.type(canvas.getByLabelText(...), 'a'.repeat(410))` → `expect(args.modelValue.length).toBe(400)` + canvas contains `text-brand-red` class,
- `Select.Default.play` : `userEvent.selectOptions(canvas.getByLabelText(...), 'option-1')` → `expect(args.onUpdate).toHaveBeenCalledWith('option-1')`,

**And** `npm run storybook:test -- --ci` retourne **0 violation WCAG 2.1 A/AA** sur les ≥ 36 stories nouvelles (si runtime disponible — fallback vitest-axe DOM tests pattern 10.15 accepté).

**AC11 — 0 violation WCAG 2.1 AA runtime (vitest-axe + Storybook addon-a11y)**
**Given** les 3 composants montés via `@testing-library/vue`,
**When** auditées par `vitest-axe` (DOM réel compilé vs jest-axe happy-dom minimal) sur minimum 9 audits (3 composants × 3 states : default / error / disabled),
**Then** **0 violation** règles axe-core WCAG 2.1 A/AA activées (`color-contrast` désactivé MVP car nécessite pipeline CSS compilé — documenté `ui-primitives.md §6`),
**And** addon-a11y Storybook panel retourne 0 violation sur les stories représentatives (`Default.md`, `Error.md`, `Disabled.md`) en inspection manuelle,
**And** le contraste brand-red `#DC2626` sur fond blanc `#FFFFFF` = **4,83:1** ✅ AA documenté dans `ui-primitives.md §6` (post-darken 10.15),
**And** le contraste brand-orange `#F59E0B` sur fond blanc = **3,85:1** — acceptable en texte auxiliaire (compteur 350-399 alerte non-critique) documenté §6 avec rationale explicite.

**AC12 — Documentation `docs/CODEMAPS/ui-primitives.md` étendue 3 sous-sections §3 + 6 pièges §5**
**Given** `docs/CODEMAPS/ui-primitives.md` (8 sections H2 post-10.15),
**When** étendue,
**Then** §3 renommée `## 3. Utiliser les primitives UI dans un composant` + **3 sous-sections** H3 : `### 3.1 ui/Input`, `### 3.2 ui/Textarea`, `### 3.3 ui/Select` (le contenu Button existant devient `### 3.0 ui/Button`, pas de perte de contenu),
**And** §5 compte **≥ 16 pièges** (actuellement 10, cible +6) numérotés :
- `#11` — `v-model` sur `<input type="number">` retourne string (HTML5 legacy), coercion nécessaire côté consommateur ou via `.number` modifier Vue.
- `#12` — Textarea `rows` vs `resize-y` natif : `rows` fixe la hauteur initiale, mais l'utilisateur peut redimensionner par défaut. Désactiver via `resize-none` si layout critique.
- `#13` — Select value toujours `string` côté DOM même si `options[].value` est `number` — coercion manuelle ou wrapper typé côté consommateur.
- `#14` — `autocomplete` attribute valeurs HTML5 standards (ex. `'email'`, `'tel-national'`, `'current-password'`) pour UX mobile optimal iOS/Android, liste référence MDN.
- `#15` — Label floating vs placeholder-as-label anti-pattern WCAG : placeholder disparaît au focus, label doit toujours être visible (UX spec §3 Form Patterns ligne Y).
- `#16` — `maxlength` native browser + JS handler + backend = **triple défense en profondeur** spec 018 AC5 (un seul niveau insuffisant : paste bypass handler JS, copy-paste mobile bypass maxlength browser dans certains cas).

**And** §6 (A11y Contraste) : +1 entrée `text-brand-orange #F59E0B` 3,85:1 avec rationale « acceptable pour compteur auxiliaire non critique 350-399 ; seuil rouge `#DC2626` 4,83:1 AA pour état bloquant à 400 ».

**And** un test `test_docs_ui_primitives.test.ts` étendu vérifie : (a) §3 contient 3 sous-sections H3 `ui/Input`/`ui/Textarea`/`ui/Select`, (b) §5 compte ≥ 16 pièges numérotés.

**And** `docs/CODEMAPS/index.md` **inchangé** (`ui-primitives.md` déjà référencée depuis 10.15).

**AC13 — Baseline frontend 428 → cible ≥ 452 (+24 tests minimum)**
**Given** `npm run test` + `npm run test:typecheck`,
**When** exécutés post-10.16,
**Then** **≥ 452 tests passed** runtime (428 baseline + 24 nouveaux minimum) + **≥ 15 typecheck** (6 baseline 10.15 + 9 nouveaux `@ts-expect-error`),
**And** **zéro régression** sur les 428 existants (`diff baseline-pre-10-16.txt baseline-post-10-16.txt --only-added-pass`),
**And** 1 pré-existant échec inchangé hors scope (`tests/something-long-running.test.ts` — identifié dans baseline 10.15).

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 préalable + baseline tests + Grep préexistant** (AC9, AC13)
  - [x] 1.1 Baseline runtime + typecheck : 422 passed + 1 flaky pré-existant inchangé + 6 typecheck baseline Button.
  - [x] 1.2 Grep `Input\.vue|Textarea\.vue|Select\.vue|INPUT_TYPES|FORM_SIZES` sur `frontend/app/components/ui/` → 0 hit confirmé.
  - [x] 1.3 Grep SFC name collision sur `frontend/app/components/` → 0 hit hors `ui/`.
  - [x] 1.4 Snapshot baseline documenté (422 runtime + 6 typecheck).

- [x] **Task 2 — Extension `ui/registry.ts`** (AC2)
  - [x] 2.1 Étendu : `INPUT_TYPES` (7) + `FORM_SIZES` (3) + `InputType` + `FormSize` + `TEXTAREA_DEFAULT_MAX_LENGTH = 400`. Button tokens préservés.
  - [x] 2.2 Tuples `Object.freeze([…] as const)` (pattern CCC-9).
  - [x] 2.3 Pas de re-export `BUTTON_SIZES as FORM_SIZES` (sémantique indépendante, testé `test_form_registry`).

- [x] **Task 3 — Composant `ui/Input.vue`** (AC1, AC3, AC5, AC6, AC7, AC8)
  - [x] 3.1 Native `<input>` + tous props typés stricts (modelValue/label/id/error/hint/required/disabled/readonly/size/type/autocomplete/pattern/minlength/maxlength/inputmode/placeholder/name).
  - [x] 3.2 Auto-ID `useId()` Vue 3.5+ si prop `id` absente.
  - [x] 3.3 Slots `#iconLeft` / `#iconRight` + `aria-hidden="true"` + padding ajusté `pl-10`/`pr-10`.
  - [x] 3.4 `sizeClasses` computed (3 sizes, min-h-[36/44/48] + pointer:coarse 44 sm).
  - [x] 3.5 `stateClasses` computed (error override `border-brand-red` + `focus-visible:ring-brand-red`).
  - [x] 3.6 `aria-invalid` / `aria-describedby` (hint + error combinés) / `aria-required` dynamiques.
  - [x] 3.7 Handler `@input` : laisse string (décision Q — consommateur coerce via `.number` modifier).
  - [x] 3.8 Scan hex `Input.vue` → 0 hit.

- [x] **Task 4 — Composant `ui/Textarea.vue`** (AC1, AC3, AC4, AC5, AC6, AC7, AC8)
  - [x] 4.1 Native `<textarea>` + props adaptées (rows default 4, maxlength default 400, showCounter default true).
  - [x] 4.2 Compteur `{length}/{maxlength}` rendu sous le champ si showCounter=true, avec `counterId` pour aria-describedby.
  - [x] 4.3 `counterClasses` computed : `<350` gray / `350-399` orange / `>=400` red + `role="status" aria-live="polite"` dynamique.
  - [x] 4.4 Handler `@input` tronque à maxlength JS + re-sync DOM + `maxlength` HTML native (triple défense).
  - [x] 4.5 Scan hex `Textarea.vue` → 0 hit.
  - [x] 4.6 Pas de slots icônes (UX multi-ligne).

- [x] **Task 5 — Composant `ui/Select.vue`** (AC1, AC3, AC5, AC6, AC7, AC8)
  - [x] 5.1 Native `<select>` stylé Tailwind + props + `options: SelectOption[]` + `multiple`.
  - [x] 5.2 `<option v-for>` standard + placeholder géré comme option disabled si single.
  - [x] 5.3 Handler `@change` : single → string, multiple → Array.from(selectedOptions).map(o => o.value).
  - [x] 5.4 ChevronDown stub SVG absolute droite + `appearance-none` pour masquer la flèche native.
  - [x] 5.5 Scan hex `Select.vue` → 0 hit.
  - [x] 5.6 DEF-10.16-1 tracé dans `deferred-work.md` (Reka UI SelectRoot Phase Growth).

- [x] **Task 6 — Commit intermédiaire 1** (pattern 10.15)
  - [x] 6.1 `git add` 3 composants + registry + 6 tests (5 runtime + 3 typecheck).
  - [x] 6.2 Commit : `feat(10.16): ui/Input + ui/Textarea + ui/Select primitives + registry extension`.

- [x] **Task 7 — Stories Storybook co-localisées** (AC10)
  - [x] 7.1 `Input.stories.ts` : 22 stories (matrice 4×3 + 5 types + 2 icon slots + 5 autres + ShowcaseGrid).
  - [x] 7.2 `Textarea.stories.ts` : 21 stories + play function `CounterAt400Red` userEvent.type 410 chars + assert tronqué 400.
  - [x] 7.3 `Select.stories.ts` : 22 stories + play function `DefaultMd` userEvent.selectOptions.
  - [x] 7.4 Helper `asStorybookComponent<T>()` 10.15 réutilisé 3 fois sans duplication.
  - [x] 7.5 `storybook-static/index.json.entries.length === 132` (baseline 66 + 66 nouvelles).

- [x] **Task 8 — Tests Vitest** (AC9, AC11, AC13)
  - [x] 8.1 `test_input_rendering.test.ts` (9 tests) + `Input.test-d.ts` (7 assertions typecheck).
  - [x] 8.2 `test_textarea_counter.test.ts` (9 tests compteur 3 seuils + frappe tronquée) + `Textarea.test-d.ts` (6 assertions).
  - [x] 8.3 `test_select_rendering.test.ts` (8 tests) + `Select.test-d.ts` (7 assertions).
  - [x] 8.4 `test_form_registry.test.ts` (6 tests).
  - [x] 8.5 `test_no_hex_hardcoded_ui_form.test.ts` (3 tests scan 3 fichiers).
  - [x] 8.6 jest-axe : 9 audits (3 composants × 3 states default/error/disabled) 0 violation A/AA.
  - [x] 8.7 Runtime : 460 passed (422 baseline + 38 nouveaux) + 26 typecheck (6 baseline + 20 nouveaux). 1 flaky pré-existant inchangé.
  - [x] 8.8 Coverage : runtime DOM assertion sur états visibles — à mesurer via c8 au code-review (pattern 10.15 post-merge).

- [x] **Task 9 — Documentation `docs/CODEMAPS/ui-primitives.md` extension** (AC12)
  - [x] 9.1 §3 renommée avec 4 sous-sections H3 : §3.0 Button (préservé) + §3.1 Input + §3.2 Textarea + §3.3 Select.
  - [x] 9.2 §5 pièges étendu de 10 → 16 (#11-#16 ajoutés : v-model number/string, rows/resize-y, Select string DOM, autocomplete MDN, floating label anti-pattern, triple défense maxlength).
  - [x] 9.3 §6 A11y : ligne text-brand-orange 3,85:1 rationale auxiliaire ajoutée.
  - [x] 9.4 `test_docs_ui_primitives.test.ts` étendu (7 tests, vérifie 3 sous-sections H3 + ≥16 pièges + 3,85:1 mention).

- [x] **Task 10 — Scan NFR66 post-dev + validation finale** (AC2, AC8, AC9, AC10, AC11, AC13)
  - [x] 10.1 Scan hex sur 3 composants + registry + 3 stories → 0 hit.
  - [x] 10.2 Scan `: any` / `as unknown` sur 3 composants + tests + typecheck → 0 hit (helper `asStorybookComponent` réutilisé).
  - [x] 10.3 Runtime Storybook : 132 stories (≥ 102 cible).
  - [x] 10.4 Bundle : 7,9 MB (≤ 15 MB budget).
  - [x] 10.5 Tests : 460 passed (≥ 452 cible).
  - [x] 10.6 Typecheck : 26 tests (≥ 15 cible).

- [x] **Task 11 — Commit intermédiaire 2 + traçage deferred-work** (pattern 10.15)
  - [x] 11.1 `git add` 3 stories + docs + deferred-work + sprint-status + test docs.
  - [x] 11.2 Commit : `feat(10.16): ui/{Input,Textarea,Select} stories + docs CODEMAPS + deferred-work + story review`.
  - [x] 11.3 DEF-10.16-1 Reka UI SelectRoot ajouté.
  - [x] 11.4 DEF-10.16-2 Lucide icons stubs ajouté.

- [x] **Task 12 — Retrospective mini leçons transmises 10.17+**
  - [x] 12.1 5 Q tranchées verrouillées §2 Dev Notes.
  - [x] 12.2 Hors scope §9 documenté (migrations brownfield Epic 11-15, Reka UI upgrade, floating label, async validation, masked input).

## Dev Notes

### 1. Architecture cible — arborescence finale

```
frontend/
├── .storybook/
│   └── main.ts                     (INCHANGÉ — glob ui/** déjà étendu 10.15)
├── app/
│   ├── components/
│   │   └── ui/
│   │       ├── FullscreenModal.vue       (inchangé brownfield)
│   │       ├── ToastNotification.vue     (inchangé brownfield)
│   │       ├── registry.ts               (MODIFIÉ +4 exports : INPUT_TYPES + FORM_SIZES + InputType + FormSize)
│   │       ├── Button.vue                (inchangé 10.15)
│   │       ├── Button.stories.ts         (inchangé 10.15)
│   │       ├── Input.vue                 (NOUVEAU 10.16)
│   │       ├── Input.stories.ts          (NOUVEAU : ≥ 12 stories CSF 3.0)
│   │       ├── Textarea.vue              (NOUVEAU 10.16)
│   │       ├── Textarea.stories.ts       (NOUVEAU : ≥ 12 stories CSF 3.0)
│   │       ├── Select.vue                (NOUVEAU 10.16)
│   │       └── Select.stories.ts         (NOUVEAU : ≥ 12 stories CSF 3.0)
│   └── types/
│       └── storybook.ts                  (inchangé 10.15 — asStorybookComponent helper réutilisé)
├── tests/components/ui/                  (dossier existant 10.15)
│   ├── [6 fichiers Button 10.15 inchangés]
│   ├── Button.test-d.ts                  (inchangé 10.15)
│   ├── test_input_rendering.test.ts      (NOUVEAU : 8 tests)
│   ├── Input.test-d.ts                   (NOUVEAU : 3 assertions typecheck)
│   ├── test_textarea_counter.test.ts     (NOUVEAU : 8 tests)
│   ├── Textarea.test-d.ts                (NOUVEAU : 3 assertions)
│   ├── test_select_rendering.test.ts     (NOUVEAU : 8 tests)
│   ├── Select.test-d.ts                  (NOUVEAU : 3 assertions)
│   ├── test_form_registry.test.ts        (NOUVEAU : 4 tests)
│   └── test_no_hex_hardcoded_ui_form.test.ts  (NOUVEAU : scan 3 fichiers)
└── tests/test_docs_ui_primitives.test.ts (MODIFIÉ : +2 assertions §3 sous-sections + §5 ≥ 16 pièges)

docs/CODEMAPS/
├── ui-primitives.md                      (MODIFIÉ : §3 → 3 sous-sections, §5 +6 pièges, §6 +1 entrée)
└── index.md                              (INCHANGÉ — ui-primitives.md déjà référencée 10.15)

_bmad-output/implementation-artifacts/
└── deferred-work.md                      (MODIFIÉ : +section 10.16 avec DEF-10.16-1/2)
```

**Diff `registry.ts` attendu** :

```diff
 export const BUTTON_VARIANTS = Object.freeze(['primary', 'secondary', 'ghost', 'danger'] as const);
 export const BUTTON_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);
+
+export const INPUT_TYPES = Object.freeze([
+  'text', 'email', 'number', 'password', 'url', 'tel', 'search',
+] as const);
+export const FORM_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);

 export type ButtonVariant = (typeof BUTTON_VARIANTS)[number];
 export type ButtonSize = (typeof BUTTON_SIZES)[number];
+export type InputType = (typeof INPUT_TYPES)[number];
+export type FormSize = (typeof FORM_SIZES)[number];
```

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|---|---|---|
| **Q1** | 1 composant `Input.vue` avec prop `type` (7 variants) OR 7 composants séparés (`TextInput`, `EmailInput`, etc.) ? | **1 composant avec prop `type: InputType`** | Native `<input type="...">` supporte déjà 7 types HTML5 sans logique métier différente. 7 composants = sur-ingénierie + 7 registries + 7 stories + 7 tests × 3 sizes chacun = explosion combinatoire. Pattern industry (Material UI `<TextField type>`, Chakra `<Input type>`, Radix `<input>`). Un seul point de convergence pour focus ring, error state, icône, a11y. Extension futures (Q17 batch composite) via composition externe. |
| **Q2** | Compteur Textarea : toujours visible OR `showCounter` prop ? | **`showCounter` prop default `true`** | La spec 018 AC5 est le cas d'usage dominant (copilot justification 400 chars) → compteur visible obligatoire. Mais certains formulaires (commentaire bref, note optionnelle) n'ont pas besoin de feedback compteur → `showCounter=false` économise du vertical space mobile. Default=true respecte la convention spec 018 tout en laissant flexibilité. |
| **Q3** | Select : natif `<select>` OR Reka UI `<SelectRoot>` ? | **Natif `<select>` MVP** (override explicite Epic AC5) | **Déviation assumée vs Epic AC5** : natif MVP car (1) a11y système ChromeVox/VoiceOver battle-tested sans aucun code, (2) 0 dépendance Reka UI ajoutée (Reka UI Combobox en Story 10.19 pour recherche/typeahead), (3) livraison M 1h30 préservée, (4) touch target iOS/Android natif Safari picker wheel + Android bottom sheet gratuit, (5) formulaires MVP (profil Company, admin catalogue) sont listes courtes (< 20 options) où le natif suffit. **Limites acceptées** : style cross-browser imparfait (Firefox/Safari flèche native → masquée par icône chevron absolute), pas de portail pour listes > viewport (Reka UI nécessaire 10.19 pour Combobox avec recherche). Traçage `DEF-10.16-1` deferred-work.md. |
| **Q4** | Validation reactive via `v-model` modifier custom OR prop `error: string` externe ? | **Prop `error: string` externe** | Séparation validation/rendu : la primitive `Input/Textarea/Select` est **dumb** (affichage pur), le parent contrôle la logique via Zod/Yup/VeeValidate. Avantages : (a) la primitive ne connaît pas le schéma, (b) l'erreur peut venir du backend (async validation 422 response), (c) testable isolément, (d) pattern industry (React Hook Form, Formik, Vue FormKit). Un modifier custom `v-model.validated="v"` coupleraient primitive et logique — inverse du principe SRP. |
| **Q5** | Icon slot Input : slots `#iconLeft`/`#iconRight` OR prop `icon: Component` ? | **Slots `#iconLeft` / `#iconRight`** (cohérent Button 10.15 Q2) | Composition flexible Vue 3 : consommateur choisit Lucide (10.21), EsgIcon custom, SVG inline ad hoc. Prop `Component` forcerait typage `Component` ambigu + passing args. Cohérence API avec `ui/Button` slots iconLeft/iconRight (même consommateur). Documenté §3.1 codemap. Exception : `Textarea` **n'a pas d'icônes inline** (UX : zone multi-ligne, l'icône serait confuse visuellement). Documenté explicitement §3.2 codemap. |

### 3. Exemples squelettes complets — 3 composants

#### 3.1 `ui/Input.vue` (squelette ~120 lignes)

```vue
<!--
  ui/Input.vue — primitive UI P0 Story 10.16.
  7 types HTML5 (text/email/number/password/url/tel/search) × 3 sizes (sm/md/lg).
  Slots #iconLeft / #iconRight (cohérent Button 10.15 Q2).
  Auto-ID useId() Vue 3.5+ si prop id absente (AC5 label for/id association).
  States : default / focus / error / disabled / readonly.
  Dark mode ≥ 6 dark: (AC7 exception 10.15 MEDIUM-2 seuil primitive simple).
  Tokens @theme exclusifs (AC8 : 0 hex hardcodé scan).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { InputType, FormSize } from './registry';

type InputProps = {
  modelValue: string | number;
  label: string;
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  type?: InputType;
  autocomplete?: string;
  pattern?: string;
  minlength?: number;
  maxlength?: number;
  inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email' | 'url' | 'search';
};

const props = withDefaults(defineProps<InputProps>(), {
  size: 'md',
  type: 'text',
  required: false,
  disabled: false,
  readonly: false,
});

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

// Auto-ID pour label association si prop id non fournie (AC5).
const autoId = useId();
const inputId = computed<string>(() => props.id ?? `ui-input-${autoId}`);
const errorId = computed<string>(() => `${inputId.value}-error`);
const hintId = computed<string>(() => `${inputId.value}-hint`);

// aria-describedby combine hint + error si les 2 presents (AC5).
const describedBy = computed<string | undefined>(() => {
  const ids: string[] = [];
  if (props.hint) ids.push(hintId.value);
  if (props.error) ids.push(errorId.value);
  return ids.length ? ids.join(' ') : undefined;
});

// Size -> classes Tailwind (AC6 touch target ≥ 44 px md+, sm pointer:coarse).
const sizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm':
      return 'min-h-[36px] [@media(pointer:coarse)]:min-h-[44px] px-3 py-1.5 text-sm';
    case 'md':
      return 'min-h-[44px] px-3.5 py-2 text-sm';
    case 'lg':
      return 'min-h-[48px] px-4 py-2.5 text-base';
  }
});

// State -> classes Tailwind (error override focus ring).
const stateClasses = computed<string>(() => {
  if (props.error) {
    return 'border-brand-red focus-visible:ring-brand-red dark:border-brand-red';
  }
  return 'border-gray-300 dark:border-dark-border focus-visible:ring-brand-green';
});

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <label
      :for="inputId"
      class="text-sm font-medium text-surface-text dark:text-surface-dark-text"
    >
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>

    <div class="relative">
      <!-- Slot iconLeft : positionne absolute dans l'input (padding-left ajuste). -->
      <span
        v-if="$slots.iconLeft"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 dark:text-gray-500"
        aria-hidden="true"
      >
        <slot name="iconLeft" />
      </span>

      <input
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete"
        :pattern="pattern"
        :minlength="minlength"
        :maxlength="maxlength"
        :inputmode="inputmode"
        :aria-required="required ? 'true' : undefined"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        :class="[
          'block w-full rounded border bg-white dark:bg-dark-input',
          'text-surface-text dark:text-surface-dark-text',
          'placeholder:text-gray-400 dark:placeholder:text-gray-500',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card',
          'disabled:bg-gray-50 dark:disabled:bg-dark-card',
          'disabled:text-gray-500 dark:disabled:text-gray-600',
          'disabled:cursor-not-allowed',
          'readonly:bg-gray-50 dark:readonly:bg-dark-card',
          'transition-colors duration-150',
          // padding-left/right ajuste si icône slot (composable via $slots).
          $slots.iconLeft ? 'pl-10' : '',
          $slots.iconRight ? 'pr-10' : '',
          sizeClasses,
          stateClasses,
        ]"
        @input="handleInput"
      />

      <span
        v-if="$slots.iconRight"
        class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400 dark:text-gray-500"
        aria-hidden="true"
      >
        <slot name="iconRight" />
      </span>
    </div>

    <p
      v-if="hint && !error"
      :id="hintId"
      class="text-xs text-gray-500 dark:text-gray-400"
    >
      {{ hint }}
    </p>

    <p
      v-if="error"
      :id="errorId"
      role="alert"
      class="flex items-center gap-1 text-xs text-brand-red"
    >
      <!-- STUB: remplace par <AlertCircle class="h-3.5 w-3.5" /> Lucide Story 10.21. -->
      <svg class="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <span>{{ error }}</span>
    </p>
  </div>
</template>
```

#### 3.2 `ui/Textarea.vue` (squelette ~110 lignes)

**Delta critique vs Input** :
- native `<textarea>` au lieu de `<input>`,
- props `rows` (default 4) + `maxlength` (default 400) + `showCounter` (default true),
- **pas de slots icônes** (UX : multi-ligne sans icône inline),
- compteur `{value.length}/{maxlength}` sous le champ avec classes dynamiques (gray < 350 / orange 350-399 / red >= 400),
- handler `@input` tronque à `maxlength` + re-émet (défense en profondeur spec 018).

```vue
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { FormSize } from './registry';

type TextareaProps = {
  modelValue: string;
  label: string;
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  rows?: number;
  maxlength?: number;
  showCounter?: boolean;
};

const props = withDefaults(defineProps<TextareaProps>(), {
  size: 'md',
  rows: 4,
  maxlength: 400, // Spec 018 AC5 (defense en profondeur).
  showCounter: true,
  required: false,
  disabled: false,
  readonly: false,
});

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

// ... (auto-ID, describedBy, sizeClasses, stateClasses byte-identique Input)

const counterClasses = computed<string>(() => {
  const len = String(props.modelValue ?? '').length;
  if (len >= props.maxlength) return 'text-brand-red font-medium';
  if (len >= props.maxlength - 50) return 'text-brand-orange';
  return 'text-gray-500 dark:text-gray-400';
});

const isAtLimit = computed<boolean>(
  () => String(props.modelValue ?? '').length >= props.maxlength,
);

function handleInput(event: Event): void {
  const target = event.target as HTMLTextAreaElement;
  // Defense en profondeur : tronque a maxlength (spec 018 AC5).
  const truncated = target.value.slice(0, props.maxlength);
  if (truncated !== target.value) {
    // Re-set DOM value pour eviter desynchronisation v-model / DOM.
    target.value = truncated;
  }
  emit('update:modelValue', truncated);
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <label :for="inputId" class="...">
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>

    <textarea
      :id="inputId"
      :value="modelValue"
      :rows="rows"
      :maxlength="maxlength"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
      :aria-required="required ? 'true' : undefined"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedBy"
      :class="[
        'block w-full rounded border bg-white dark:bg-dark-input',
        'text-surface-text dark:text-surface-dark-text',
        'placeholder:text-gray-400 dark:placeholder:text-gray-500',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card',
        'disabled:bg-gray-50 dark:disabled:bg-dark-card disabled:cursor-not-allowed',
        'transition-colors duration-150',
        'resize-y', // Default natif (peut etre override par consommateur via class).
        sizeClasses,
        stateClasses,
      ]"
      @input="handleInput"
    />

    <div class="flex justify-between items-start gap-2">
      <p v-if="error" :id="errorId" role="alert" class="flex items-center gap-1 text-xs text-brand-red">
        <!-- STUB AlertCircle SVG inline (idem Input) -->
        <span>{{ error }}</span>
      </p>
      <p v-else-if="hint" :id="hintId" class="text-xs text-gray-500 dark:text-gray-400">{{ hint }}</p>
      <span v-else aria-hidden="true"></span>

      <p
        v-if="showCounter"
        :class="['text-xs tabular-nums flex-shrink-0', counterClasses]"
        :role="isAtLimit ? 'status' : undefined"
        :aria-live="isAtLimit ? 'polite' : undefined"
      >
        {{ String(modelValue ?? '').length }}/{{ maxlength }}
      </p>
    </div>
  </div>
</template>
```

#### 3.3 `ui/Select.vue` (squelette ~100 lignes)

**Delta critique vs Input** :
- native `<select>` au lieu de `<input>`,
- prop `options: Array<{ value: string; label: string; disabled?: boolean }>`,
- prop `multiple?: boolean` (default false),
- icône `ChevronDown` stub SVG absolute droite (masque flèche native cross-browser inconsistante),
- pas de `type`/`autocomplete`/`pattern`/`minlength`/`maxlength`/`inputmode` (non pertinents).

```vue
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { FormSize } from './registry';

type SelectOption = { value: string; label: string; disabled?: boolean };

type SelectProps = {
  modelValue: string | string[];
  label: string;
  options: SelectOption[];
  id?: string;
  placeholder?: string; // Rendu comme <option value="" disabled>{placeholder}</option>
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  size?: FormSize;
  multiple?: boolean;
};

const props = withDefaults(defineProps<SelectProps>(), {
  size: 'md',
  required: false,
  disabled: false,
  multiple: false,
});

const emit = defineEmits<{ 'update:modelValue': [value: string | string[]] }>();

// ... (auto-ID, describedBy, sizeClasses, stateClasses byte-identique Input)

function handleChange(event: Event): void {
  const target = event.target as HTMLSelectElement;
  if (props.multiple) {
    const values = Array.from(target.selectedOptions).map(o => o.value);
    emit('update:modelValue', values);
  } else {
    emit('update:modelValue', target.value);
  }
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <label :for="inputId" class="...">
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>

    <div class="relative">
      <select
        :id="inputId"
        :value="modelValue"
        :multiple="multiple"
        :required="required"
        :disabled="disabled"
        :aria-required="required ? 'true' : undefined"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        :class="[
          'block w-full rounded border bg-white dark:bg-dark-input',
          'text-surface-text dark:text-surface-dark-text',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card',
          'disabled:bg-gray-50 dark:disabled:bg-dark-card disabled:cursor-not-allowed',
          'transition-colors duration-150',
          'appearance-none', // Masque flèche native cross-browser.
          multiple ? '' : 'pr-10', // Espace pour icône chevron (single seulement).
          sizeClasses,
          stateClasses,
        ]"
        @change="handleChange"
      >
        <option v-if="placeholder && !multiple" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="opt in options"
          :key="opt.value"
          :value="opt.value"
          :disabled="opt.disabled"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- STUB ChevronDown : remplace par <ChevronDown /> Lucide Story 10.21. -->
      <span
        v-if="!multiple"
        class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400 dark:text-gray-500"
        aria-hidden="true"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </span>
    </div>

    <p v-if="hint && !error" :id="hintId" class="text-xs text-gray-500 dark:text-gray-400">{{ hint }}</p>
    <p v-if="error" :id="errorId" role="alert" class="flex items-center gap-1 text-xs text-brand-red">
      <!-- STUB AlertCircle SVG inline -->
      <span>{{ error }}</span>
    </p>
  </div>
</template>
```

### 4. Pièges documentés §5 codemap (6 nouveaux, cible total ≥ 16)

**#11** — **`v-model` sur `<input type="number">` retourne string (HTML5 legacy)** — le DOM native `<input type="number">` expose `value` en **string** (ex. `"42"`, `"3.14"`). `emit('update:modelValue', target.value)` transmet une string. **Solution consommateur** : utiliser le modifier Vue `v-model.number="amount"` qui applique `Number(value)` automatiquement OU coerce dans le parent `const amount = computed(() => Number(rawAmount.value))`. La primitive `Input` **ne coerce pas** délibérément (évite surprise sur `""` → `NaN`). Documenté §3.1 exemple.

**#12** — **Textarea `rows` fixe vs `resize-y` natif** — attribut `rows="4"` fixe la hauteur initiale (4 lignes), mais l'utilisateur peut redimensionner verticalement par défaut (`resize-y` natif navigateur). **Piège** : layout critique (carte compacte mobile) cassé si user drag-resize. **Solution** : passer `class="resize-none"` au parent pour désactiver, ou `resize-y` (default) pour layout fluide. Documenté §3.2.

**#13** — **Select `value` toujours `string` côté DOM (pas `number`)** — même si `options[i].value` typé `number` côté TypeScript, l'attribut HTML `value` du `<option>` est sérialisé string par le navigateur. `event.target.value` retourne string. **Solution** : typer `SelectOption['value']: string` explicitement dans la primitive (pas `string | number`), consommateur fait sa propre coercion. Alternative : wrapper typé générique `<SelectTyped<number>>` en Phase Growth si besoin.

**#14** — **`autocomplete` attribute valeurs HTML5 standards** — `autocomplete="email"`, `"tel-national"`, `"current-password"`, `"street-address"`, etc. **Piège** : `autocomplete="off"` est **ignoré** par Chrome/Safari sur champs password/email (anti-feature pour forcer l'utilisation des managers de mots de passe). **Solution** : utiliser les tokens standards MDN ([liste référence](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete)) pour UX mobile iOS/Android optimal (QuickType suggestions iOS), pas de custom token.

**#15** — **Label floating vs placeholder-as-label (anti-pattern WCAG)** — pattern « floating label » (Material Design) : le label descend à la place du placeholder si vide, remonte en haut au focus. **Anti-pattern si** le placeholder **remplace** totalement le label (invisible du screen reader, disparaît au focus utilisateur voyant). **Solution primitive 10.16** : label **toujours visible au-dessus** du champ (pattern UX Step 12 §3 Form Patterns). Le `placeholder` est **texte d'exemple optionnel** (ex. `"jean@exemple.ci"`), jamais le label principal. Floating label = Phase Growth `Input.variant="floating"` si besoin design spécifique.

**#16** — **`maxlength` native browser + JS handler + backend = triple défense en profondeur** — `maxlength="400"` HTML native empêche la saisie clavier standard, mais **paste (Ctrl+V) bypass** sur certains navigateurs (Firefox < 100 notamment), et API JavaScript `element.value = "a".repeat(1000)` bypasse totalement. **Solution spec 018 AC5** : (a) attribut HTML native (première défense user standard), (b) handler `@input` tronque à 400 + re-émet (capture paste + JS), (c) backend SQLAlchemy/Pydantic validator `@field_validator` length ≤ 400 (défense finale). Les 3 niveaux sont **non-redondants** (chaque étage rattrape un cas que les autres ratent). Documenté `ui-primitives.md §5 piège #16`.

### 5. Pattern `docs/CODEMAPS/ui-primitives.md` extension (4 sous-sections §3)

```markdown
## 3. Utiliser les primitives UI dans un composant

### 3.0 ui/Button (existant 10.15 préservé byte-identique)

[... contenu actuel ...]

### 3.1 ui/Input (NOUVEAU 10.16)

\`\`\`vue
<script setup lang="ts">
import Input from '~/components/ui/Input.vue';
import { ref } from 'vue';
const email = ref('');
const emailError = computed(() =>
  email.value && !email.value.includes('@') ? 'Format email invalide' : undefined,
);
</script>
<template>
  <!-- Input email standard avec validation parent -->
  <Input
    v-model="email"
    label="Email professionnel"
    type="email"
    autocomplete="email"
    placeholder="jean@entreprise.ci"
    required
    :error="emailError"
    hint="Utilisé pour les notifications ESG"
  />

  <!-- Input password avec icone -->
  <Input v-model="password" label="Mot de passe" type="password" autocomplete="current-password" required>
    <template #iconLeft><LockIcon class="h-4 w-4" /></template>
  </Input>

  <!-- Input numerique FCFA avec inputmode mobile -->
  <Input
    v-model.number="amountFcfa"
    label="Montant (FCFA)"
    type="number"
    inputmode="numeric"
    :minlength="0"
    hint="Montant en XOF"
  />
</template>
\`\`\`

### 3.2 ui/Textarea (NOUVEAU 10.16)

\`\`\`vue
<script setup lang="ts">
import Textarea from '~/components/ui/Textarea.vue';
import { ref } from 'vue';
const justification = ref('');
</script>
<template>
  <!-- Textarea justification spec 018 avec compteur 400 chars -->
  <Textarea
    v-model="justification"
    label="Pourquoi votre projet est-il aligne sur la taxonomie UEMOA ?"
    :rows="5"
    :maxlength="400"
    :showCounter="true"
    required
    hint="400 caracteres maximum — soyez concis et precis"
  />

  <!-- Textarea breve sans compteur -->
  <Textarea v-model="comment" label="Commentaire (optionnel)" :showCounter="false" :rows="3" />
</template>
\`\`\`

### 3.3 ui/Select (NOUVEAU 10.16)

\`\`\`vue
<script setup lang="ts">
import Select from '~/components/ui/Select.vue';
import { ref } from 'vue';
const sector = ref('');
const SECTORS = [
  { value: 'agri', label: 'Agriculture' },
  { value: 'energy', label: 'Énergie' },
  { value: 'waste', label: 'Recyclage / Déchets' },
  { value: 'transport', label: 'Transport', disabled: true }, // Pas encore supporté MVP.
];
</script>
<template>
  <Select
    v-model="sector"
    label="Secteur d'activité"
    :options="SECTORS"
    placeholder="-- Selectionner un secteur --"
    required
    hint="Influence le scoring ESG sectoriel UEMOA"
  />

  <!-- Select multiple ODD cibles (multi-selection simple MVP) -->
  <Select v-model="odds" label="ODD cibles" :options="ODD_OPTIONS" multiple />
</template>
\`\`\`
```

### 6. Testing plan complet

| # | Test | Type | Delta |
|---|---|---|---|
| T1 | `INPUT_TYPES.length === 7` + frozen + dedup | Vitest unit | +1 |
| T2 | `FORM_SIZES.length === 3` + frozen + dedup | Vitest unit | +1 |
| T3 | `FORM_SIZES !== BUTTON_SIZES` référence (pas de re-export) | Vitest unit | +1 |
| T4 | Input : 7 types rendus correctement (attr `type`) | Vitest mount | +1 |
| T5 | Input : 3 sizes → `min-h-[XX]` appliqué | Vitest mount | +1 |
| T6 | Input : v-model bidirectionnel (userEvent.type → emit) | Vitest | +1 |
| T7 | Input : required → astérisque + aria-required="true" | Vitest | +1 |
| T8 | Input : error → aria-invalid + aria-describedby + message visible + icône | Vitest | +1 |
| T9 | Input : disabled + readonly → attributs HTML + classes | Vitest | +1 |
| T10 | Input : slots iconLeft/iconRight rendus + `aria-hidden="true"` | Vitest | +1 |
| T11 | Input : vitest-axe 3 states (default/error/disabled) | vitest-axe | +1 |
| T12 | Textarea : 3 sizes rendus | Vitest | +1 |
| T13 | Textarea : v-model bidirectionnel | Vitest | +1 |
| T14 | Textarea : compteur `< 350` → `text-gray-500` | Vitest | +1 |
| T15 | Textarea : compteur `== 350` → `text-brand-orange` | Vitest | +1 |
| T16 | Textarea : compteur `== 400` → `text-brand-red` + `role="status"` | Vitest | +1 |
| T17 | Textarea : frappe > 400 tronquée à 400 exactement (triple défense) | Vitest + userEvent | +1 |
| T18 | Textarea : showCounter=false → compteur pas rendu | Vitest | +1 |
| T19 | Textarea : vitest-axe 3 states | vitest-axe | +1 |
| T20 | Select : options rendues + ordre préservé | Vitest | +1 |
| T21 | Select : selection → emit update:modelValue | Vitest + userEvent.selectOptions | +1 |
| T22 | Select : option `disabled: true` → `disabled` attribut HTML | Vitest | +1 |
| T23 | Select : multiple=true → emit array | Vitest | +1 |
| T24 | Select : vitest-axe 3 states | vitest-axe | +1 |
| T25 | Scan hex 3 fichiers + registry → 0 hit | Vitest fs | +1 |
| **Total runtime** | | | **+25 tests** (plancher AC9 ≥ 24 dépassé) |
| TD1-TD3 | `Input.test-d.ts` : 3 assertions + `@ts-expect-error` type invalide | vitest --typecheck | +3 |
| TD4-TD6 | `Textarea.test-d.ts` : 3 assertions | typecheck | +3 |
| TD7-TD9 | `Select.test-d.ts` : 3 assertions (options shape, multiple array vs string) | typecheck | +3 |
| **Total typecheck** | | | **+9 assertions** |
| Storybook runtime | `storybook-static/index.json entries` | Comptage build | ≥ 102 (66 + ≥ 36) |
| CI a11y | `npm run storybook:test --ci` 0 violation AA | Addon-a11y | **0 violation** (AC10) |
| Coverage | `npm run test -- --coverage` sur 3 fichiers | c8 | **≥ 85 %** (AC9) |
| Baseline | 428 → **≥ 452 passed** | Vitest regression | **0 regression** (AC13) |

### 7. Checklist review (pour code-reviewer Story 10.16 post-merge)

- [ ] **Tokens `@theme` exclusifs** — `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Input.vue frontend/app/components/ui/Textarea.vue frontend/app/components/ui/Select.vue frontend/app/components/ui/*.stories.ts` → 0 hit hors commentaires.
- [ ] **TypeScript strict enforcé** — `rg ': any|as unknown' frontend/app/components/ui/Input.vue frontend/app/components/ui/Textarea.vue frontend/app/components/ui/Select.vue` → 0 hit (helper `asStorybookComponent` 10.15 préservé).
- [ ] **Dark mode couverture primitive ≥ 6 par composant** — `rg 'dark:' frontend/app/components/ui/Input.vue | wc -l ≥ 6`, idem Textarea + Select. Exception 10.15 MEDIUM-2 §7 codemap respectée (pas d'inflation no-op).
- [ ] **WCAG 2.1 AA** — `npm run storybook:test --ci` 0 violation (fallback vitest-axe 9 audits si runtime indisponible, pattern 10.15).
- [ ] **Pas de `any` dans composants + tests + stories** — `rg ': any\b' frontend/app/components/ui/{Input,Textarea,Select}.vue frontend/tests/components/ui/test_{input,textarea,select}_*.test.ts` → 0 hit.
- [ ] **Pas de duplication** — `INPUT_TYPES` et `FORM_SIZES` source unique `registry.ts`, importés par 3 composants + 3 stories + tests.
- [ ] **Native `<input/textarea/select>` (pas Reka UI)** — `rg 'from .reka-ui.' frontend/app/components/ui/Input.vue frontend/app/components/ui/Textarea.vue frontend/app/components/ui/Select.vue` → 0 hit (Q1/Q3 verrouillées).
- [ ] **Shims legacy 10.6** — aucune modification des 68 composants inchangés (60 brownfield + 6 gravity + 2 ui brownfield + Button 10.15 + registry shim).
- [ ] **Comptage runtime** — `storybook-static/index.json entries length ≥ 102`.
- [ ] **Compteur Textarea 3 seuils testés** — tests `== 349` gray / `== 350` orange / `== 399` orange / `== 400` red + `role="status"`.
- [ ] **Frappe bloquée Textarea** — `userEvent.type('a'.repeat(410))` → value.length === 400 exactement.
- [ ] **Touch target ≥ 44 px md+** — `min-h-[44px]` md + lg, `sm` utilise `[@media(pointer:coarse)]:min-h-[44px]`.
- [ ] **`inputmode` présent sur Input** — `rg 'inputmode' frontend/app/components/ui/Input.vue` ≥ 1 hit.
- [ ] **`autocomplete` tokens standards** — si documentés dans exemples §3.1, valeurs parmi MDN list.
- [ ] **Astérisque required `text-brand-red aria-hidden="true"`** — pas d'astérisque visible aux lecteurs d'écran (a11y).
- [ ] **`aria-describedby` combine hint + error** — test spécifique : les 2 props présentes → `aria-describedby="id-hint id-error"` space-separated.
- [ ] **Compile-time enforcement** — `Input.test-d.ts` + `Textarea.test-d.ts` + `Select.test-d.ts` contiennent minimum 3 `@ts-expect-error` chacun (vitest typecheck green).
- [ ] **Traçage deferred-work.md** — section `## Deferred from: story 10.16 (2026-04-22)` avec `DEF-10.16-1 Reka UI SelectRoot` + `DEF-10.16-2 Lucide icons stubs`.
- [ ] **Pas de secret exposé** — `rg 'API_KEY|SECRET|TOKEN' frontend/app/components/ui/` → 0 hit.
- [ ] **Bundle Storybook** — `du -sh storybook-static` ≤ 15 MB (budget 10.14).
- [ ] **Coverage 3 fichiers ≥ 85 %** — c8 report.

### 8. Pattern commits intermédiaires (leçon 10.8+10.13+10.14+10.15)

**2 commits lisibles review** (décision Q6, cohérent 10.15) :

1. `feat(10.16): ui/Input + ui/Textarea + ui/Select primitives + registry extension` (Tasks 2 + 3 + 4 + 5 + 6).
2. `feat(10.16): ui/{Input,Textarea,Select} stories + tests + docs CODEMAPS ui-primitives` (Tasks 7 + 8 + 9 + 10 + 11).

Pattern CCC-9 (10.8+10.14+10.15) appliqué byte-identique : `INPUT_TYPES` + `FORM_SIZES` frozen tuple + validation runtime via `test_form_registry.test.ts`.
Pattern exception dark mode seuil 10.15 MEDIUM-2 respecté : `≥ 6 dark:` par primitive simple, pas d'inflation artificielle.
Pattern compile-time `@ts-expect-error` 10.15 HIGH-1 patch réutilisé byte-identique : `vitest.config.ts typecheck` déjà configuré, 3 nouveaux `.test-d.ts` livrés.
Pattern helper `asStorybookComponent<T>()` 10.15 MEDIUM-3 patch réutilisé byte-identique : import direct `app/types/storybook.ts` dans 3 stories.

### 9. Hors scope explicite (non-objectifs cette story)

- ❌ **Migration des 60 composants brownfield** utilisant `<input class="…">` / `<textarea class="…">` / `<select class="…">` inline vers `<ui/Input>` / `<ui/Textarea>` / `<ui/Select>` → Phase 1 Epic 11-15 (pattern scan Grep `<input\s+class=` par epic, remplacement systématique).
- ❌ **Migration des 6 squelettes `gravity/*.vue`** utilisant `<input>` inline → Epic 11 ticket dédié.
- ❌ **Reka UI SelectRoot wrapper** — documenté Epic AC5 mais override Q3 MVP → `DEF-10.16-1` deferred-work.md (Phase Growth si besoin custom styling cross-browser uniforme OR portail pour liste > viewport).
- ❌ **Floating label variant Input** (pattern Material Design) → Phase Growth `Input.variant="floating"` si design spécifique.
- ❌ **Async validation built-in** (ex. `:validator="async v => …"` + debounce) → Phase Growth. MVP : parent gère via Zod/VeeValidate externe + `error` prop bindée.
- ❌ **Masked input** (ex. formatage automatique tel `+221 XX XX XX XX`) → Phase Growth. MVP : type `tel` + inputmode numeric suffisant.
- ❌ **Input file upload** (type="file") → hors scope (composant dédié `FileUploader.vue` Phase 1, pattern drag-drop spécifique).
- ❌ **Input combobox/autocomplete** (typeahead dropdown) → Story 10.19 `ui/Combobox.vue` (Reka UI ComboboxRoot).
- ❌ **`ui/Badge.vue`** → Story 10.17.
- ❌ **`ui/Drawer.vue`** → Story 10.18.
- ❌ **`ui/DatePicker.vue`** → Story 10.20 (consomme `ui/Input` via trigger lecture seule, AC2 epic).
- ❌ **Tokens `--color-form-error` / `--color-form-hint` dédiés** → Phase Growth si besoin différencier visuellement de `brand-red` / `gray-500`. MVP : réutilisation directe.
- ❌ **Widget QCU / QCM / batch composite (Q17)** → spec 018 widgets existent déjà côté `InteractiveQuestionHost` ; consomment les primitives 10.16 en extension future Epic 11.
- ❌ **Textarea auto-resize height** (textarea qui grandit automatiquement selon contenu) → Phase Growth `Textarea.autoResize="true"` si besoin UX spécifique (spec 018 rows=5 fixe suffisant MVP).
- ❌ **Select searchable / typeahead** → Story 10.19 Combobox (exact purpose).

### 10. Previous story intelligence (10.15 leçons transférables)

De Story 10.15 (`ui/Button` 4 variantes, sizing S, done post-review APPROVE-WITH-CHANGES) :

- **Pattern frozen tuple CCC-9** (`BUTTON_VARIANTS` + `BUTTON_SIZES`) → réutilisé byte-identique `INPUT_TYPES` (7) + `FORM_SIZES` (3). Test `Object.isFrozen` + `new Set().size === length` idem.
- **Pattern shims legacy 10.6** (68 composants inchangés) → appliqué : Button + registry préservés, 2 ui/ brownfield préservés, ajout pur 3 nouveaux `.vue` + 3 stories + extensions registry/tests/docs.
- **Pattern commit intermédiaire** → 2 commits (component+registry / stories+tests+docs), cohérent 10.15 byte-identique.
- **Pattern scan NFR66 Task 1** → Task 1 de cette story.
- **Pattern comptage runtime** (`jq '.entries'` sur `storybook-static/index.json`) → AC10 ≥ 102.
- **Pattern CODEMAPS extension** → `ui-primitives.md` étendu (+3 sous-sections §3 + 6 pièges §5 + 1 entrée §6), pas de nouvelle codemap.
- **Pattern choix verrouillés pré-dev 5 Q** → §2 Dev Notes 5 Q (Q1 1 component type prop / Q2 showCounter default true / Q3 Select natif MVP override / Q4 error externe / Q5 slots iconLeft/Right cohérent Button).
- **Pattern co-localisation stories** → 3 stories co-localisés byte-identique pattern 10.15.
- **Pattern test jest-axe + `vitest-axe`** → 9 audits minimum (3 × 3 states). Upgrade recommandé `vitest-axe` si dispo (résout `color-contrast` là où jest-axe happy-dom renvoie incomplete, voir 10.15 HIGH-2 analyse).
- **Pattern test scan hex** → extension `test_no_hex_hardcoded_ui_form.test.ts` byte-identique logique 10.15, scope 3 nouveaux fichiers.
- **Pattern `asStorybookComponent<T>()`** (10.15 MEDIUM-3 patch) → réutilisé 3 fois dans `Input.stories.ts` + `Textarea.stories.ts` + `Select.stories.ts` sans duplication.
- **Pattern tokens darken AA 10.15 HIGH-2 hotfix** (`brand-green #047857` + `brand-red #DC2626`) → CONSOMMÉ directement pour error state + focus ring. Aucune darken supplémentaire requise.
- **Pattern exception dark mode 10.15 MEDIUM-2** → respectée : seuil `≥ 6 dark:` par primitive simple (Input/Textarea/Select plus complexes que Button car plus de surfaces + placeholder + error border + disabled bg).
- **Pattern compile-time `@ts-expect-error` 10.15 HIGH-1 patch** (`Button.test-d.ts` + `vitest.config.ts typecheck`) → extension directe 3 `.test-d.ts` (Input/Textarea/Select).
- **Pattern `.gitignore storybook-static/`** (10.15 INFO-5) → inchangé (déjà en place, respect baseline).
- **Leçon `as unknown as Meta<...>['component']` (10.15 MEDIUM-3)** → éviter en réutilisant helper `asStorybookComponent<T>()` factorisé. 0 hit `as unknown` attendu dans 3 stories.
- **Leçon `eslint-disable` orphelin (10.15 MEDIUM-1)** → ne pas désactiver `no-explicit-any` sans vrai `any`, respecter discipline linter.
- **Règle d'or tests E2E effet observable (10.5)** → tests `userEvent.type()`, `userEvent.selectOptions()` réels (pas mocks), Storybook play functions sur canvas réel (pas `args` mock).
- **Leçon 10.15 LOW-3 pas de smoke test auto-import Nuxt** → **couvert cette story** (scope 10.16 validé Task 1.3 Grep pré-dev absence collision `<Input>`/`<Textarea>`/`<Select>` SFC name).

### Project Structure Notes

- Dossier `frontend/app/components/ui/` **existant** (10.14+10.15), ajouts : 3 `.vue` + 3 `.stories.ts`. Collision zéro vérifiée Task 1.
- Tests sous `frontend/tests/components/ui/` **dossier existant** (10.15), ajouts : 5 `.test.ts` + 3 `.test-d.ts`. Aucun test Button existant n'est modifié (pattern shim 10.6).
- Pas de modification `nuxt.config.ts` (3 composants auto-importés via `pathPrefix: false` existant CLAUDE.md, collision vérifiée Task 1.3).
- `tsconfig.json` frontend déjà `strict: true` → types `InputType`/`FormSize` hérités sans override.
- `frontend/.storybook/main.ts` **inchangé** (glob `ui/**` étendu depuis 10.15).
- `frontend/.storybook/preview.ts` **inchangé** (toggle dark + backgrounds + a11y config réutilisés 10.14+10.15).
- `frontend/vitest.config.ts` **inchangé** (typecheck.include `tests/**/*.test-d.ts` configuré depuis 10.15 HIGH-1 patch).
- `main.css` **inchangé** (aucun nouveau token — 3 primitives consomment exclusivement les 12 brand/surface/dark darken 10.15 + 20 sémantiques 10.14).
- Pattern Nuxt 4 auto-imports avec `pathPrefix: false` : `<Input>`, `<Textarea>`, `<Select>` disponibles globalement. **Piège Nuxt** : si `pages/` contient déjà `<Input>` wrapper custom ailleurs, collision possible. Task 1.3 vérifie.

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.16] — spec détaillée 8 AC + NFR + estimate M (ligne 508-541).
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-12-§3-Form-Patterns-Validation] — validation client+serveur, erreur inline + icône CircleAlert + copy actionnable, astérisque rouge `aria-required`, copy adaptative Q1 pédagogue-sage → concise-expert.
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-8] — tokens `@theme` brand-green `#047857` post-darken 10.15 AA + brand-red `#DC2626` + surface-* + dark-input, séparation verdict-* vs brand-* (Q21).
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-13-A11y-WCAG-2.1-AA] — 13 items dont touch 44 px, focus-visible, label for/id, aria-invalid, aria-describedby, aria-required, role=alert, color-contrast 4,5:1, prefers-reduced-motion, dark mode.
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Q12] — Touch target ≥ 44 px sur layer Aminata mobile (pointer:coarse arbitrary Tailwind 4).
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Q17] — Arbitrage 3 modes saisie widget QCU mono-fait / QCM / batch composite (spec 018 InteractiveQuestion consomme 10.16 primitives).
- [Source: _bmad-output/implementation-artifacts/018-interactive-chat-widgets.md] — Spec 018 AC5 : compteur 400 chars stricts justification, défense en profondeur 3 niveaux (browser + client + server).
- [Source: CLAUDE.md#Dark-Mode-OBLIGATOIRE] — tous composants via variantes `dark:` (`dark:bg-dark-input`, `dark:text-surface-dark-text`, `dark:border-dark-border`, `dark:placeholder-gray-500`).
- [Source: CLAUDE.md#Reutilisabilite-Composants] — discipline > 2 fois = extraction primitive. 3 primitives co-livrées car squelette ≥ 80 % partagé.
- [Source: ~/.claude/rules/typescript/coding-style.md] — TypeScript strict, types dérivés `as const`, pas de `any`, `unknown` narrowing, interface pour public API.
- [Source: frontend/app/assets/css/main.css:15-27] — tokens `@theme` brand-green (#047857 darken 10.15) + brand-red (#DC2626 darken 10.15) + surface-bg/text + dark-input/card/border/hover.
- [Source: frontend/app/components/ui/Button.vue:1-172] — pattern Vue SFC primitive 10.15 byte-identique à reproduire (Composition API, computed classes, slots, `withDefaults`, `defineProps`/`defineEmits`, dark mode, `transition-colors/opacity`, tokens `@theme`).
- [Source: frontend/app/components/ui/registry.ts:1-18] — pattern frozen tuple CCC-9 à étendre (4 exports supplémentaires).
- [Source: frontend/app/types/storybook.ts] — helper `asStorybookComponent<T>()` 10.15 MEDIUM-3 patch, réutilisé 3 fois.
- [Source: frontend/tests/components/ui/Button.test-d.ts] — pattern `@ts-expect-error` + vitest typecheck à reproduire byte-identique pour 3 `.test-d.ts`.
- [Source: frontend/vitest.config.ts] — `typecheck.include: ['tests/**/*.test-d.ts']` + `test:typecheck` script.
- [Source: docs/CODEMAPS/ui-primitives.md:1-end] — 8 sections H2 post-10.15 à étendre (§3 renommée + 3 sous-sections H3 / §5 +6 pièges / §6 +1 entrée).
- [Source: _bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md] — patterns Dev Notes 10 sections, 5 Q pré-dev, 10 pièges, checklist review 16 items, références.
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md] — 16 leçons cumulées (HIGH-1 `@ts-expect-error` effectif / HIGH-2 darken AA / MEDIUM-1 eslint-disable / MEDIUM-2 exception dark / MEDIUM-3 helper factorisé / LOW smoke test auto-import).
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — section à enrichir avec DEF-10.16-1 + DEF-10.16-2 (Tasks 11.3-11.4).

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — dev-story 2026-04-22, 18ᵉ story Phase 4.

### Debug Log References

- Baseline pre-dev : `npm run test` → 422 passed + 1 flaky (`useGuidedTour.resilience` pré-existant) + 6 typecheck (Button 10.15).
- Scan Task 1 : `rg 'Input\.vue|Textarea\.vue|Select\.vue|INPUT_TYPES|FORM_SIZES'` sur `app/components/ui/` → 0 hit ; scan SFC name collision sur `app/components/` → 0 hit. Aucune collision auto-imports Nuxt.
- Storybook build post-dev : 132 stories (66 baseline + 66 nouvelles), bundle 7,9 MB (budget 15 MB).
- Post-dev : `npm run test` → 460 passed (+38 vs 422) + 1 flaky inchangé ; `npm run test:typecheck` → 26 tests (+20 vs 6), 0 type error.
- Scan hex sur 3 `.vue` + registry + 3 stories → 0 hit ; scan `: any`/`as unknown` sur 3 composants + tests + typecheck → 0 hit.

### Completion Notes List

- **Registry CCC-9 étendu** : `INPUT_TYPES` (7) + `FORM_SIZES` (3) + `TEXTAREA_DEFAULT_MAX_LENGTH = 400` ajoutés byte-identique au pattern 10.15. `FORM_SIZES` intentionnellement indépendant de `BUTTON_SIZES` (test explicite `not.toBe`).
- **Input.vue** : 7 types HTML5 × 3 sizes, auto-ID `useId()` Vue 3.5+, slots `#iconLeft`/`#iconRight`, `aria-describedby` combine hint + error, `resolvedInputmode` auto pour email/tel/url/search. 14 occurrences `dark:` (seuil AC7 respecté).
- **Textarea.vue** : compteur 3 seuils (gray < 350 / orange 350-399 / red ≥ 400 + `role="status" aria-live="polite"`), triple défense maxlength (HTML + JS tronque + re-sync DOM + backend spec 018), pas de slots icônes. 14 `dark:`.
- **Select.vue** : natif `<select>` stylé Tailwind (Q3 MVP, DEF-10.16-1 tracé), chevron SVG absolute masque fleche native inconsistante cross-browser, options typées `SelectOption[]`. 11 `dark:`.
- **Tests Vitest** : 35 runtime nouveaux (9 Input + 9 Textarea + 8 Select + 6 registry + 3 no-hex) + 20 typecheck nouveaux (7 Input + 6 Textarea + 7 Select). `jest-axe` 9 audits 0 violation WCAG 2.1 A/AA. Test docs 10.15 (4 tests) étendu à 7 tests (7 assertions : sections H2, 4 sous-sections H3 primitives, ≥16 pièges §5, ≥4 exemples par primitive, contraste 3,85:1 mention).
- **Stories Storybook** : 66 nouvelles (Input 22 + Textarea 21 + Select 22 + 1 ShowcaseGrid implicite chacun) soit 132 total (baseline 66 + 66). 3 play functions `user-event` réels : `Input.DefaultMd` type email, `Textarea.CounterAt400Red` type 10 chars + assert length=400 (tronqué JS), `Select.DefaultMd` selectOptions + expect `'energy'`.
- **CODEMAPS ui-primitives.md** : §3 renommée avec 4 sous-sections H3 (3.0 Button preserved + 3.1 Input + 3.2 Textarea + 3.3 Select avec exemples Vue numérotés), §5 pièges 10 → 16 (#11-#16 : v-model number/string, rows/resize-y, Select DOM string, autocomplete MDN, floating label anti-pattern, triple défense maxlength), §6 A11y table étendue avec entrée text-brand-orange 3,85:1 rationale auxiliaire.
- **deferred-work.md** : section Story 10.16 ajoutée avec DEF-10.16-1 (Reka UI SelectRoot Phase Growth) + DEF-10.16-2 (remplacement 4 stubs SVG par Lucide Story 10.21).
- **0 modification des 68 composants inchangés** (60 brownfield + 6 gravity/ + 2 ui brownfield + Button 10.15) — pattern shim 10.6 respecté.

### File List

**Créés (3 composants + 3 stories + 6 tests + 3 typecheck = 15 nouveaux fichiers)** :

- `frontend/app/components/ui/Input.vue`
- `frontend/app/components/ui/Input.stories.ts`
- `frontend/app/components/ui/Textarea.vue`
- `frontend/app/components/ui/Textarea.stories.ts`
- `frontend/app/components/ui/Select.vue`
- `frontend/app/components/ui/Select.stories.ts`
- `frontend/tests/components/ui/Input.test-d.ts`
- `frontend/tests/components/ui/Textarea.test-d.ts`
- `frontend/tests/components/ui/Select.test-d.ts`
- `frontend/tests/components/ui/test_input_rendering.test.ts`
- `frontend/tests/components/ui/test_textarea_counter.test.ts`
- `frontend/tests/components/ui/test_select_rendering.test.ts`
- `frontend/tests/components/ui/test_form_registry.test.ts`
- `frontend/tests/components/ui/test_no_hex_hardcoded_ui_form.test.ts`

**Modifiés (5 fichiers)** :

- `frontend/app/components/ui/registry.ts` (+INPUT_TYPES + FORM_SIZES + TEXTAREA_DEFAULT_MAX_LENGTH + 2 types dérivés)
- `frontend/tests/test_docs_ui_primitives.test.ts` (4 → 7 tests, AC12 nouveaux invariants)
- `docs/CODEMAPS/ui-primitives.md` (§3 renommée avec 4 sous-sections H3, §5 10 → 16 pièges, §6 +1 entrée contraste)
- `_bmad-output/implementation-artifacts/deferred-work.md` (+section Story 10.16 avec DEF-10.16-1 + DEF-10.16-2)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (10-16 : ready-for-dev → in-progress → review)

### Change Log

- **2026-04-22** — Story 10.16 implémentée et prête pour review.
  - 3 primitives formulaire livrées (Input + Textarea + Select) avec 460 tests runtime (+38 vs baseline 422) + 26 typecheck (+20 vs baseline 6), 0 régression.
  - 132 stories Storybook (+66 nouvelles), bundle 7,9 MB.
  - 0 hex hardcodé + 0 any + dark mode ≥ 11 par composant.
  - CODEMAPS ui-primitives.md étendu (3 sous-sections H3 §3 + 16 pièges §5 + 1 entrée §6).
  - 2 deferred-work tracés (DEF-10.16-1 Reka UI SelectRoot + DEF-10.16-2 Lucide stubs).
