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
├── ui-primitives.md                (ce fichier, 5 sections H2 + 10 pièges §5)
└── index.md                        (+1 ligne référence)
```

## 3. Utiliser `ui/Button` dans un composant

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

---

## Ressources

- [Story 10.15 spec complète](../../_bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md)
- [Storybook setup 10.14](./storybook.md)
- [UX spec — Button Hierarchy §1 Step 12](../../_bmad-output/planning-artifacts/ux-design-specification.md)
- [Tokens `@theme` main.css](../../frontend/app/assets/css/main.css)
