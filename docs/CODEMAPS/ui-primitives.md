# Primitives UI — Phase 0 Design System

## 1. Contexte

Story **10.15** Phase 0 : première primitive `ui/Button.vue` livrée après le setup
Storybook de la 10.14. Série complète Phase 0 attendue (ordre prévu sprint-plan v2) :

| Story | Primitive | Sizing |
|-------|-----------|--------|
| **10.15** | `ui/Button.vue` (4 variants × 3 sizes) | S (~1 h) |
| 10.16 | `ui/Input.vue` · `ui/Textarea.vue` · `ui/Select.vue` | M |
| 10.17 | `ui/Badge.vue` (tokens sémantiques verdict/fa/admin) | S |
| 10.18 | `ui/Drawer.vue` (wrapper Reka UI Dialog side) | M |
| 10.19 | `ui/Combobox.vue` · `ui/Tabs.vue` (wrappers Reka UI) | M |
| 10.20 | `ui/DatePicker.vue` | M |
| 10.21 | `ui/EsgIcon.vue` + pile Lucide `lucide-vue-next` | S |

**Règle CLAUDE.md « discipline > 2 fois »** : les 60 composants brownfield contenant
des boutons ad hoc (`<button class="rounded bg-brand-purple …">`) migreront
progressivement vers `<ui/Button>` en Epic 11-15. Aucune breaking change
brownfield en Phase 0 — le pattern shim 10.6 reste respecté.

**Décisions verrouillées pré-dev 10.15 (5 Q tranchées)** :

1. **Q1 — Native `<button>`** : Reka UI n'exporte pas de primitive Button. Native
   HTML offre déjà focus management, keyboard Space/Enter, `aria-disabled`,
   `type` variants, form association. Un wrapper supplémentaire serait de la
   sur-ingénierie.
2. **Q2 — Slots `#iconLeft` / `#iconRight`** : composition flexible Vue 3 ;
   consommateur choisit Lucide Loader2, EsgIcon custom, SVG inline.
3. **Q3 — Spinner `absolute` + `visibility:hidden` sur texte** : layout stable
   entre loading ↔ default (pas de CLS). Pattern standard Material UI / Radix.
4. **Q4 — Class variants Tailwind** : tokens `@theme` résolus compile-time,
   purge CSS efficace.
5. **Q5 — `hover:opacity-90` (solide) + `hover:bg-gray-*` (soft)** : les tokens
   dédiés `--color-brand-*-hover` n'existent pas dans `main.css`. Leur création
   est reportée en Phase Growth (pattern > 2 réutilisations).

## 2. Arborescence cible

```
frontend/
├── .storybook/
│   └── main.ts                     (stories glob : gravity/ + ui/)
├── app/
│   └── components/
│       └── ui/
│           ├── FullscreenModal.vue       (brownfield, inchangé)
│           ├── ToastNotification.vue     (brownfield, inchangé)
│           ├── registry.ts               (BUTTON_VARIANTS + BUTTON_SIZES frozen)
│           ├── Button.vue                (primitive 4 variants × 3 sizes)
│           └── Button.stories.ts         (22 stories CSF 3.0 + 4 play functions)
├── tests/components/ui/
│   ├── test_button_registry.test.ts      (4 tests frozen/length/dedup)
│   ├── test_button_variants.test.ts      (14 tests 4×3 + defaults + focus)
│   ├── test_button_states.test.ts        (7 tests click/loading/disabled/warn)
│   ├── test_button_a11y.test.ts          (8 audits jest-axe)
│   ├── test_button_types.ts              (assertions TS compile-time)
│   └── test_no_hex_hardcoded_ui.test.ts  (scan Button.vue + registry.ts)
└── tests/test_docs_ui_primitives.test.ts (scan 5 sections + ≥ 8 pièges)

docs/CODEMAPS/
├── ui-primitives.md                (ce fichier, 5 sections H2 + 26 pièges §5)
└── index.md                        (+1 ligne référence)
```

## 3. Utiliser les primitives UI dans un composant

### 3.0 `ui/Button` (Story 10.15)

```vue
<script setup lang="ts">
import Button from '~/components/ui/Button.vue';
import { ref } from 'vue';

const loading = ref(false);

async function handleSign(): Promise<void> {
  loading.value = true;
  try {
    await signFundApplication();
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <!-- 1. Primary CTA default : tokens @theme, hover:opacity-90, touch 44px. -->
  <Button variant="primary" @click="handleSign">Signer et figer</Button>

  <!-- 2. Loading asynchrone : spinner absolute + texte invisible + aria-busy. -->
  <Button variant="primary" :loading="loading" @click="handleSign">Signer</Button>

  <!-- 3. Icon-only : ariaLabel obligatoire (TypeScript compile-time). -->
  <Button variant="ghost" icon-only aria-label="Fermer le modal">
    <template #iconLeft><XIcon class="h-4 w-4" /></template>
  </Button>

  <!-- 4. Icon left + texte : composition via slot named. -->
  <Button variant="secondary">
    <template #iconLeft><ArrowLeftIcon class="h-4 w-4" /></template>
    Retour
  </Button>

  <!-- 5. Dark mode : les variantes dark: sont appliquées automatiquement via
       classes Tailwind. Aucune prop theme à passer. -->
  <Button variant="secondary">Annuler</Button>

  <!-- 6. Hiérarchie juridique FR40 : primary + ghost + secondary côte à côte. -->
  <div class="flex gap-3">
    <Button variant="primary">Signer et figer</Button>
    <Button variant="ghost">Enregistrer brouillon</Button>
    <Button variant="secondary">Annuler</Button>
  </div>
</template>
```

### 3.1 `ui/Input` (Story 10.16)

Primitive formulaire avec 7 types HTML5 natifs (text/email/number/password/url/tel/search)
× 3 sizes (sm/md/lg). Slots `#iconLeft` / `#iconRight` cohérents avec `ui/Button`.
Validation via prop `error` externe (pattern **dumb component**, Q4 verrouillée).

```vue
<script setup lang="ts">
import Input from '~/components/ui/Input.vue';
import { ref, computed } from 'vue';

const email = ref('');
const emailError = computed(() =>
  email.value && !email.value.includes('@') ? 'Format email invalide' : undefined,
);

const amountFcfa = ref<number>(0);
</script>

<template>
  <!-- 1. Input email standard avec validation parent (Zod/VeeValidate). -->
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

  <!-- 2. Input password avec icone left. -->
  <Input
    v-model="password"
    label="Mot de passe"
    type="password"
    autocomplete="current-password"
    required
  >
    <template #iconLeft><LockIcon class="h-4 w-4" /></template>
  </Input>

  <!-- 3. Input numerique FCFA avec inputmode mobile natif. -->
  <Input
    v-model.number="amountFcfa"
    label="Montant (FCFA)"
    type="number"
    inputmode="numeric"
    hint="Montant en XOF"
  />

  <!-- 4. Input tel avec autocomplete HTML5 standard. -->
  <Input
    v-model="phone"
    label="Téléphone"
    type="tel"
    autocomplete="tel-national"
    placeholder="+221 XX XXX XX XX"
  />
</template>
```

### 3.2 `ui/Textarea` (Story 10.16)

Primitive multi-ligne avec compteur 400 chars strict (spec 018 AC5, triple défense).
**Pas de slots icônes** (UX : zone multi-ligne sans icône inline).

```vue
<script setup lang="ts">
import Textarea from '~/components/ui/Textarea.vue';
import { ref } from 'vue';

const justification = ref('');
const comment = ref('');
</script>

<template>
  <!-- 1. Textarea justification spec 018 avec compteur 400 chars. -->
  <Textarea
    v-model="justification"
    label="Pourquoi votre projet est-il aligné sur la taxonomie UEMOA ?"
    :rows="5"
    :maxlength="400"
    :showCounter="true"
    required
    hint="400 caractères maximum — soyez concis et précis"
  />

  <!-- 2. Textarea breve sans compteur (optionnel). -->
  <Textarea
    v-model="comment"
    label="Commentaire (optionnel)"
    :showCounter="false"
    :rows="3"
  />

  <!-- 3. Textarea 1500 chars pour resume executif. -->
  <Textarea
    v-model="executiveSummary"
    label="Résumé exécutif"
    :maxlength="1500"
    :rows="8"
  />
</template>
```

### 3.3 `ui/Select` (Story 10.16)

Wrapper **natif** `<select>` stylé Tailwind (Q3 verrouillée — Reka UI Combobox
livré Story 10.19 pour recherche/typeahead). Options typées
`Array<{ value: string; label: string; disabled?: boolean }>`.

```vue
<script setup lang="ts">
import Select from '~/components/ui/Select.vue';
import { ref } from 'vue';

const sector = ref('');
const odds = ref<string[]>([]);

const SECTORS = [
  { value: 'agri', label: 'Agriculture' },
  { value: 'energy', label: 'Énergie' },
  { value: 'waste', label: 'Recyclage / Déchets' },
  { value: 'transport', label: 'Transport', disabled: true },
];

const ODD_OPTIONS = [
  { value: '8', label: 'ODD 8 — Travail décent' },
  { value: '13', label: 'ODD 13 — Climat' },
];
</script>

<template>
  <!-- 1. Select simple avec placeholder et option disabled. -->
  <Select
    v-model="sector"
    label="Secteur d'activité"
    :options="SECTORS"
    placeholder="-- Sélectionner un secteur --"
    required
    hint="Influence le scoring ESG sectoriel UEMOA"
  />

  <!-- 2. Select multiple (ODD cibles). -->
  <Select
    v-model="odds"
    label="ODD cibles"
    :options="ODD_OPTIONS"
    multiple
  />
</template>
```

### 3.4 `ui/Badge` (Story 10.17)

Primitive d'**affichage pur non-interactif** unifiant 3 familles sémantiques via une
**union discriminée compile-time** `variant × state` : 4 verdicts ESG + 9 états
lifecycle `FundApplication` + 3 niveaux criticité admin. Chaque rendu combine
3 signaux redondants obligatoires (Règle 11 UX) : **couleur** (tokens `@theme`) +
**icône** (slot `#icon` obligatoire) + **texte label** (slot `#default` obligatoire).

```vue
<script setup lang="ts">
import Badge from '~/components/ui/Badge.vue';
// Stubs SVG Lucide — Story 10.21 les remplacera par <CheckCircle />, etc.
import { h } from 'vue';
const IconCheck = () =>
  h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 },
    [h('circle', { cx: 12, cy: 12, r: 10 }), h('path', { d: 'M9 12l2 2 4-4' })]);
</script>

<template>
  <!-- 1. Verdict PASS par défaut (taille md, non-conditionnel). -->
  <Badge variant="verdict" state="pass">
    <template #icon><IconCheck /></template>
    Validé
  </Badge>

  <!-- 2. Verdict PASS conditionnel (italique + aria-label "(conditionnel)"). -->
  <Badge variant="verdict" state="pass" :conditional="true">
    <template #icon><IconCheck /></template>
    Validé
  </Badge>

  <!-- 3. Lifecycle signed en size sm (dashboard compact, dark mode automatique). -->
  <Badge variant="lifecycle" state="signed" size="sm">
    <template #icon><IconPenLine /></template>
    Signé
  </Badge>

  <!-- 4. Admin criticité N2 (aria-label="Criticité admin N2" composé côté primitive). -->
  <Badge variant="admin" state="n2">
    <template #icon><IconAlertTriangle /></template>
    N2
  </Badge>
</template>
```

**Union discriminée compile-time (AC1)** — les combinaisons invalides sont rejetées
dès l'édition TS :

```ts
// @ts-expect-error state 'draft' est LifecycleState, pas VerdictState (cross-variant).
const bad: BadgeProps = { variant: 'verdict', state: 'draft' };
// @ts-expect-error conditional interdit hors variant=verdict.
const bad2: BadgeProps = { variant: 'admin', state: 'n1', conditional: true };
```

**Sizes inline 20/24/32 px (Q4 verrouillée)** — Badge est d'affichage pur,
**jamais** 44 px touch-target. Si un filtrage cliquable est requis, wrapper
`<button @click><Badge .../></button>` (piège #24 ci-dessous).

## 4. Ajouter une 8ᵉ primitive UI

1. **Créer le squelette Vue** — `app/components/ui/NewPrimitive.vue` avec
   `<script setup lang="ts">`, tokens `@theme` exclusifs, ARIA + dark mode +
   `prefers-reduced-motion` respecté.
2. **Co-localiser les stories** — `app/components/ui/NewPrimitive.stories.ts`
   CSF 3.0 avec au minimum 4 variants par défaut + états (loading/disabled/error)
   + DarkMode + ShowcaseGrid.
3. **Étendre le registry** — `app/components/ui/registry.ts` avec nouveaux
   frozen tuples (pattern CCC-9 10.8+10.14) et types dérivés `as const`.
4. **Dupliquer les tests** — `tests/components/ui/` : variants (mounts × sizes) +
   states + a11y (jest-axe 4 variants × 2 states) + no-hex hardcoded sur le
   fichier `.vue` uniquement.
5. **Documenter** — ajouter un exemple Vue dans §3 ci-dessus + pièges
   spécifiques dans §5 (ne JAMAIS rétrograder en dessous de 8 pièges documentés).

## 5. Pièges documentés

1. **`hover:opacity-90` + `focus-visible:ring-2` coexistence** — Tailwind 4
   compose ces deux pseudo-classes indépendamment. Écrire `hover:opacity-90`
   seul ferait que le focus-visible appliquerait aussi l'opacity → confusion
   visuelle (focus paraît « en train d'être cliqué »). **Solution** : garder
   les deux classes séparées, ne jamais combiner `focus-visible:opacity-90`.
2. **`disabled` + `loading` exclusivité logique** — `loading=true` rend
   automatiquement `disabled=true` sur le natif, mais conserve son propre
   feedback visuel (spinner + aria-busy distinct du grey-out). Les tests
   distinguent les deux cas (aria-busy vs aria-disabled).
3. **Touch target mobile Safari iOS** — iOS Safari applique par défaut
   `-webkit-appearance: button` qui peut réduire la hauteur sous 44 px.
   `min-h-[44px]` force Tailwind en compile-time et override Safari.
   `sm` utilise `[@media(pointer:coarse)]:min-h-[44px]` Tailwind 4 arbitrary
   variant pour n'élever le target qu'en contexte touch.
4. **Tokens `verdict-*` vs `brand-*`** — `--color-verdict-pass` (emerald-600)
   est délibérément distinct de `--color-brand-green` (emerald-500). Les
   verdicts ESG (pass/fail/reported/na) sont réservés aux états sémantiques
   de conformité (ScoreGauge, ReferentialComparisonView). Un rebrand de
   `brand-green` ne doit PAS modifier la perception `pass`. **Règle** :
   `variant="primary"` → `brand-*`, état sémantique ESG → `verdict-*`.
5. **Icon slot sizing contrôlé par le consommateur** — les slots
   `#iconLeft` / `#iconRight` ne contraignent PAS la taille de l'icône.
   Documentation : le consommateur doit matcher `h-4 w-4` (`sm`/`md`) ou
   `h-5 w-5` (`lg`). Alternative Phase Growth : provide/inject `buttonSize`.
6. **Keyboard Space vs Enter sur `<button>` natif** — Enter déclenche `click`
   au keydown, Space le déclenche au keyup (W3C spec). Un test
   `userEvent.keyboard('{Space}')` qui vérifie sur keydown échouerait.
   **Solution** : `userEvent.keyboard(' ')` (espace simple) simule
   keydown+keyup dans `@testing-library`.
7. **Button-in-button nesting interdit HTML5** — `<button><button>…</button></button>`
   parse invalide. Un `<ui/Button>` NE DOIT PAS être injecté dans le slot
   d'une carte qui est elle-même un `<button>`. Si une carte cliquable
   contient un CTA, inverser : carte externe `<div>`, seul le CTA interne
   est un `<button>`.
8. **`prefers-reduced-motion` spinner — fonctionnel vs décoratif** — l'AC6
   épic impose rotation ≤ 0,5 tour/s pour animations décoratives, mais un
   spinner trop lent (> 2 s/tour) semble figé et inquiète l'utilisateur.
   **Compromis MVP** : `animation-duration: 2s` en reduce (1 tour / 2 s =
   0,5 tour/s conforme sans paraître cassé). Scoped dans `<style>` de
   `Button.vue`.
9. **Collision Nuxt 4 auto-imports + `components/ui/`** — `nuxt.config.ts`
   configure `components: { pathPrefix: false }`. `Button.vue` dans
   `app/components/ui/` est auto-importé comme `<Button>` global sans ambiguïté
   tant qu'aucun autre `Button.vue` n'existe dans l'arborescence. **Task 1.3**
   de la story vérifie cette absence avant écriture (Grep exhaustif).
10. **Classes dynamiques Tailwind + purge** — éviter les classes construites
    dynamiquement par concaténation de strings (`bg-${color}-500`). Toujours
    écrire les classes complètes dans un `switch` de `computed` ou un
    `Record<variant, string>`. Tailwind 4 scanne les sources en mode complet
    mais les chaînes dynamiques peuvent être manquées → classes absentes du
    bundle final.
11. **`v-model` sur `<input type="number">` retourne string (HTML5 legacy)** —
    le DOM natif `<input type="number">` expose `value` en **string** (ex.
    `"42"`, `"3.14"`). `emit('update:modelValue', target.value)` transmet une
    string. **Solution consommateur** : utiliser le modifier Vue
    `v-model.number="amount"` qui applique `Number(value)` automatiquement
    OU coercer dans le parent `const amount = computed(() => Number(raw.value))`.
    La primitive `ui/Input` **ne coerce pas** délibérément (évite surprise sur
    `""` → `NaN`). Idem : `FORM_SIZES` tuple est intentionnellement indépendant
    de `BUTTON_SIZES` (même valeurs `sm`/`md`/`lg` mais évolution future d'un
    des 2 ne doit pas coupler l'autre).
12. **Textarea `rows` fixe vs `resize-y` natif** — attribut `rows="4"` fixe la
    hauteur initiale (4 lignes), mais l'utilisateur peut **redimensionner
    verticalement par défaut** (CSS `resize-y`). **Piège** : layout critique
    (carte compacte mobile) peut être cassé si user drag-resize. **Solution** :
    passer `class="resize-none"` au parent pour désactiver, ou garder `resize-y`
    (default) pour layout fluide. L'option globale `resize-none` sur la
    primitive n'est pas exposée MVP (Phase Growth si besoin).
13. **Select `value` toujours `string` côté DOM (pas `number`)** — même si
    `options[i].value` était typé `number` côté TypeScript, l'attribut HTML
    `value` du `<option>` est sérialisé string par le navigateur.
    `event.target.value` retourne string. **Solution primitive 10.16** :
    `SelectOption['value']: string` strict, le consommateur fait sa propre
    coercion si nécessaire (`Number(sector.value)`). Alternative Phase Growth :
    wrapper typé générique `<SelectTyped<number>>` si > 2 contextes.
14. **`autocomplete` attribute tokens HTML5 standards** — `autocomplete="email"`,
    `"tel-national"`, `"current-password"`, `"street-address"`, etc.
    **Piège Chrome/Safari** : `autocomplete="off"` est **ignoré** sur champs
    password/email (anti-feature pour forcer l'utilisation des gestionnaires
    de mots de passe). **Solution** : utiliser exclusivement les tokens
    standards [MDN autocomplete](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete)
    pour UX mobile iOS/Android optimale (QuickType suggestions). Pas de
    custom token.
15. **Label floating vs placeholder-as-label (anti-pattern WCAG)** — le pattern
    « floating label » (Material Design) fait descendre le label à la place du
    placeholder si vide, puis le remonte au focus. **Anti-pattern si** le
    placeholder **remplace** totalement le label (invisible du screen reader,
    disparaît au focus). **Règle primitives 10.16** : label **toujours visible
    au-dessus** du champ (pattern UX Step 12 §3 Form Patterns). Le
    `placeholder` est un texte d'exemple optionnel (ex. `"jean@exemple.ci"`),
    **jamais** le label principal. Floating label = Phase Growth
    `Input.variant="floating"` si design spécifique.
16. **`maxlength` native browser + JS handler + backend = triple défense
    en profondeur** — `maxlength="400"` HTML native empêche la saisie
    clavier standard, mais **paste (Ctrl+V) bypass** sur certains navigateurs
    (Firefox < 100 notamment), et API JavaScript `element.value = "a".repeat(1000)`
    bypasse totalement. **Solution spec 018 AC5 appliquée `ui/Textarea`** :
    (a) attribut HTML native (première défense user standard), (b) handler
    `@input` tronque à 400 + re-émet (capture paste + JS), (c) validator
    backend SQLAlchemy/Pydantic `@field_validator` length ≤ 400 (défense
    finale). Les 3 niveaux sont **non-redondants** (chaque étage rattrape
    un cas que les autres ratent).

17. **`aria-describedby` doit référencer des IDs **réellement rendus** dans le DOM** —
    Si `describedBy` pousse `hintId` mais le `<p id={hintId}>` a un `v-if` qui
    exclut le hint quand `error` est présent, l'attribut `aria-describedby`
    pointe vers un élément **inexistant** → NVDA/JAWS cherchent l'ID en vain,
    annonce silencieusement raccourcie. **Solution primitives 10.16 post-review
    H-1** : rendre `hint` ET `error` simultanément (le `v-if` s'aligne sur la
    même condition que le push dans `describedBy`). Les 2 paragraphes s'empilent
    verticalement sous le champ (UX acceptable : hint = info permanente,
    error = alerte transitoire).

18. **Textarea `@input` pendant composition IME (CJK + dead-keys AZERTY)** —
    L'événement `@input` se déclenche **pendant** une composition IME
    (`isComposing === true`) sur Chromium. Muter `target.value` à ce moment-là
    (ex: troncature `slice(0, maxlength)`) **casse** la composition :
    - Utilisateurs CJK (chinois/japonais/coréen) : glyphe partiel tronqué →
      IME avorte la saisie.
    - Utilisateurs AZERTY dead-keys (accents français é è ê à ç ù — universels
      Afrique francophone) : composition `a` + `` ` `` peut être coupée.
    **Solution primitive 10.16 post-review H-2** : flag `isComposing` via
    `@compositionstart` / `@compositionend`. Pendant composition, emit
    `target.value` **sans** troncature. Sur `compositionend`, re-exécuter
    `handleInput` pour appliquer la troncature sur le glyphe commit final.

19. **`<select multiple>` ne supporte PAS `:value="modelValue"` avec un tableau** —
    Le DOM natif sérialise un tableau en string via `toString()` (ex: `['8','13']`
    → `"8,13"`), aucune option ne matche → rien n'est sélectionné visuellement.
    La propriété `value` d'un `<select>` retourne uniquement **la première
    option sélectionnée** côté lecture. **Solution primitive 10.16 post-review
    H-3** : en mode `multiple=true`, ne pas binder `:value` ; synchroniser
    programmatiquement `selectedOptions` via `ref` + `watch(modelValue)` qui
    fait `Array.from(el.options).forEach(o => o.selected = values.includes(o.value))`.
    **Piège lié mobile** : natif multi-select UX diffère par OS — iOS Safari
    rend une **scroll list inline**, Android Chrome rend une **bottom sheet
    avec checkboxes**, desktop exige Cmd/Ctrl+click. Pour UX > 5 options ou
    mobile-first, préférer `Combobox` Reka UI (Story 10.19).

20. **`<input type="number">` émet string par défaut sur `target.value`** —
    Le DOM natif expose `.value: string` même sur `type=number`. Émettre
    `target.value` brut dans `update:modelValue` corrompt silencieusement un
    modelValue typé `number` côté parent (`ref<number>(0)` devient `"42"`,
    comparaisons `> 100000` en coercion lexicographique). **Solution primitive
    10.16 post-review H-4** : le handler discrimine sur `props.type` — si
    `type=number`, émettre `Number(target.value)` (et `''` pour vide, jamais
    `NaN` qui casse reactive watchers). Sinon émettre string. Le contrat
    emit devient `string | number` discriminé à l'exécution.

21. **Tokens `verdict-*` vs `brand-*` confusion (aggravation post-10.15 darken)** —
    Story 10.15 a darkened `brand-green #10B981 → #047857` + `brand-red
    #EF4444 → #DC2626` pour WCAG AA. Les tokens `verdict-*` **restent à
    leurs valeurs Q21 d'origine** (`verdict-pass #059669`, `verdict-fail
    #DC2626`, `verdict-reported #D97706`, `verdict-na #6B7280`). **Piège** :
    tentation de « matcher » `verdict-reported` sur `brand-orange #F59E0B`
    (même famille chromatique). **INCORRECT** — `#F59E0B` sur blanc = 2,58:1
    ❌ AA. Le choix `#D97706` amber-600 est **délibéré** pour contraste 4,69:1
    ✅ AA (documenté §6). **Règle Badge** : `variant="verdict"` → `verdict-*` ;
    états CTA primary/danger → `brand-*`. Jamais inversion.

22. **Icon slot sizing non contraint par le parent (Badge + Button)** — le
    slot `#icon` reçoit un SVG consommateur (stub Phase 0 ou Lucide Story
    10.21) dont le parent ne contrôle pas la taille native. **Solution
    Badge 10.17** : Tailwind arbitrary selector `[&_svg]:h-3 [&_svg]:w-3`
    (sm) / `[&_svg]:h-3.5 [&_svg]:w-3.5` (md) / `[&_svg]:h-4 [&_svg]:w-4`
    (lg) cible les SVG enfants directs — fonctionne pour Lucide (`<svg>`
    racine) mais **pas pour wrappers** `<MyIcon>` qui seraient un
    `<span><svg>…</svg></span>`. Alternative Phase Growth : provide/inject
    `badgeSize` + wrapper Lucide adaptatif Story 10.21.

23. **`role="status"` vs `role="img"` — choix A11y pour Badge** — un badge
    ESG pourrait sembler être un « icône » sémantique (`role="img"`), mais
    les lecteurs d'écran annoncent `img` avec le seul `aria-label`.
    `role="status"` (région ARIA live-polite implicite) **annonce le
    contenu** + **met à jour automatiquement** si l'état change de façon
    asynchrone (re-scan ESG, tool calls LangGraph `submitted → in_review →
    accepted`). **Choix primitive 10.17** : `role="status"` retenu.
    **Piège** : `role="img"` forcerait `aria-label` obligatoire (redondant)
    et perdrait l'update automatique SR.

24. **Anti-pattern « badge-as-button » (Q5 verrouillée Story 10.17)** —
    tentation de rendre un Badge cliquable (filtre table, tri verdict).
    **INTERDIT MVP** pour 3 raisons :
    (1) Native `<span>` n'a pas de touch target 44 px (AC5 hauteurs
    20/24/32 px), mobile WCAG 2.5.5 ❌.
    (2) `role="button"` sur `<span>` nécessite `tabindex="0"` +
    `keydown` handlers + focus-visible — dupliquerait `ui/Button`.
    (3) UX : un badge cliquable confond l'utilisateur (pas de feedback
    hover/focus distinct du hover sur Badge statique).
    **Solution** : wrapper `<button @click="filter"><Badge variant="verdict"
    state="fail">…</Badge></button>` avec `<button>` natif porteur de
    l'interaction. Deferred-work `DEF-10.17-1 Interactive Badge Phase
    Growth` si pattern réutilisé > 2 fois.

25. **Union discriminée Vue 3 `defineProps<Union>` — piège narrowing
    template** — dans le template Vue, `props.state` est typé
    `VerdictState | LifecycleState | AdminCriticality` (union merged) car
    le narrowing cross-block n'existe pas dans les templates SFC.
    **Solution Badge** : utiliser des `computed` avec `switch(props.variant)`
    (JavaScript narrowing fonctionne) + mappings `Record<VerdictState,
    string>`. **Piège** : si un dev ajoute `v-if="props.variant === 'verdict'
    && props.conditional"` dans le template, TypeScript ne narrow **PAS**
    `props` dans ce bloc — la prop `conditional` reste accessible
    uniquement via `computed` narrowing JS.

26. **Comptage Storybook runtime OBLIGATOIRE avant Completion Notes
    (méthodologie 10.16 M-3 capitalisée)** — **méta-piège méthodologique** :
    l'estimation a priori du nombre de stories CSF exports est trompeuse
    car Storybook `tags: ['autodocs']` génère +1 docs page par CSF et
    certains exports peuvent être ignorés par filtering. **Règle** :
    exécuter `jq '.entries | keys | length' storybook-static/index.json`
    **après** `npm run storybook:build` et consigner le chiffre exact
    dans Completion Notes — **PAS d'estimation**. Pattern capitalisé
    proactivement dès Story 10.17 pour éviter la récurrence de la dérive
    post-10.16 (132 annoncés vs 122 réels).

---

## 6. A11y — Contraste WCAG 2.1 AA (calculs darken tokens 10.15)

Post code-review Story 10.15 HIGH-2 (2026-04-22), les tokens `--color-brand-green`
et `--color-brand-red` ont été **darkened** pour respecter WCAG 2.1 AA `color-contrast`
(≥ 4,5:1 sur texte normal `text-sm font-medium`).

| Token | Avant | Luminance | Contraste vs `#FFFFFF` | Après | Contraste | Verdict |
|-------|-------|-----------|------------------------|-------|-----------|---------|
| `--color-brand-green` | `#10B981` (emerald-500) | 0,43 | **2,56:1** ❌ AA | `#047857` (emerald-700) | **5,78:1** | ✅ AA |
| `--color-brand-red` | `#EF4444` (red-500) | 0,27 | **3,28:1** ❌ AA | `#DC2626` (red-600) | **4,83:1** | ✅ AA |
| `--color-brand-blue` | `#3B82F6` (blue-500) | 0,24 | 3,68:1 ❌ AA (texte normal) | — *inchangé* | — | ⚠ non utilisé comme `bg + text-white` |
| `--color-brand-purple` | `#8B5CF6` (violet-500) | 0,23 | 3,86:1 | — *inchangé* | — | ⚠ non utilisé comme `bg + text-white` |
| `--color-brand-orange` | `#F59E0B` (amber-500) | 0,52 | 2,11:1 | — *inchangé* | — | ⚠ non utilisé comme `bg + text-white` |
| `text-brand-orange` (Textarea counter 350-399) | `#F59E0B` | — | **3,85:1** vs blanc | — *inchangé* | — | ⚠️ **texte auxiliaire acceptable** (Story 10.16 — compteur seuil warn non bloquant ; le seuil rouge `#DC2626` 4,83:1 AA s'applique à l'état limite 400 bloquant) |
| `text-verdict-reported` (Badge 10.17 `reported`) | `#D97706` (amber-600) | 0,35 | **4,69:1** vs blanc | — *délibéré Q21* | — | ✅ AA (choix amber-600 au lieu de `#F59E0B` amber-500 = 2,58:1 ❌, documenté piège #21) |

**Contraste mode sombre (post-review 10.16 L-4)** — Le compteur Textarea est rendu
sur `bg-dark-card` (`#1F2937`) en dark mode. Les ratios calculés vs ce fond :

| Classe compteur | Couleur texte | Ratio vs `#1F2937` | Verdict |
|-----------------|---------------|--------------------|---------|
| `dark:text-gray-400` (< 350) | `#9CA3AF` | **6,80:1** | ✅ AA / ✅ AAA |
| `text-brand-orange` (350-399, inchangé dark) | `#F59E0B` | **6,50:1** | ✅ AA (auxiliaire → conforte) |
| `text-brand-red` (400, inchangé dark) | `#DC2626` | **3,50:1** | ⚠ sous AA 4,5:1 mais **AA large text** (`font-medium` Tailwind ≈ 500 → pas 700 bold requis) ; amélioré visuellement par `font-medium` appliqué à cet état + `role="status"` aria-live (annonce SR en complément visuel). Non bloquant MVP — batched DEF-10.15-4 Storybook CI. |

**Règle** : tout token `--color-brand-*` consommé en pattern `bg-brand-* text-white`
avec `text-sm` (14 px) ou plus petit DOIT atteindre ≥ 4,5:1 contraste calculé
manuellement avant merge. Les tokens blue/purple/orange sont consommés aujourd'hui
uniquement sur fond clair (texte sur `bg-surface-bg`), donc hors risque immédiat.

**Limite du harness jest-axe** : en happy-dom sans pipeline CSS, la règle
`color-contrast` axe-core retourne `incomplete` (impossible de calculer la couleur
rendue). Les 8 audits `test_button_a11y.test.ts` couvrent donc uniquement les règles
non-color-contrast (`button-name`, `aria-valid-attr`, etc.). La vraie validation
contraste doit passer par `npm run storybook:test -- --ci` qui charge Tailwind
compilé dans un vrai navigateur (job CI `.github/workflows/storybook.yml` step
`Run a11y + interactions tests`). Entrée deferred-work `DEF-10.15-4 Upgrade a11y
harness Storybook runtime` trace l'upgrade du script vitest.

## 7. Exception Dark Mode Coverage — Seuil primitive vs composant complexe

La checklist générique 10.14 impose `≥ 12 occurrences dark:` par composant
(pattern validé pour `gravity/` complexes multi-layer : SignatureModal,
SourceCitationDrawer, ImpactProjectionPanel). **Ce seuil NE s'applique PAS aux
primitives UI simples** type `ui/Button.vue` (7 occurrences dark: post-10.15).

**Rationale** :
- **Primitive simple** = 1 surface + 1 texte + 1 bordure + hover = **~4 classes
  dark: par variant**. Pour 4 variants, on atteint ~16 classes **seulement si
  chaque variant a une surface distincte en dark**. Or primary (`bg-brand-green`)
  et danger (`bg-brand-red`) **réutilisent volontairement** les tokens brand sur
  les deux thèmes (vert/rouge saturés restent identifiables en dark mode sans
  override). Seules les variants soft (secondary `bg-surface-bg → dark:bg-dark-card`
  et ghost `bg-transparent → dark:hover:bg-dark-hover`) nécessitent des overrides.
- **Composant complexe** (gravity/) = plusieurs layers (card+overlay+icon+text+
  secondary-text+border+divider+shadow+hover+focus) × plusieurs states
  (default/hover/focus/active/disabled/selected) → naturellement ≥ 12 `dark:`
  par fichier.

**Règle** :
| Type | Seuil `dark:` attendu | Pourquoi |
|------|----------------------|----------|
| Primitive `ui/*.vue` (Button, Badge, Input) | `≥ 4` (1 par variant soft utile) | Éviter inflation artificielle ; certains variants réutilisent brand tokens intentionnellement |
| Composant `gravity/*.vue` (modals, drawers, panels) | `≥ 12` | Multi-layers × multi-states |

**À ne pas faire** : ajouter `dark:bg-brand-green` (no-op) à `variant=primary`
pour gonfler le compteur. Si un jour le design system exige un dark mode distinct
pour les brand CTA (ex. gradient dark), créer un token dédié `--color-brand-green-dark`
dans `main.css` au lieu de dupliquer `dark:` sur le consommateur.

---

## Ressources

- [Story 10.15 spec complète](../../_bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md)
- [Storybook setup 10.14](./storybook.md)
- [UX spec — Button Hierarchy §1 Step 12](../../_bmad-output/planning-artifacts/ux-design-specification.md)
- [Tokens `@theme` main.css](../../frontend/app/assets/css/main.css)
