<!--
  ui/Badge.vue — primitive UI Phase 0 Story 10.17 (patch code-review 2026-04-22).
  Union discriminee variant x state : verdict (4) + lifecycle (9) + admin (3).
  3 signaux redondants OBLIGATOIRES (Regle 11 UX Step 12) : couleur + icone + texte.
  Non-interactif (affichage pur) : native <span>, role="img" (statique — pas live-region).
  Stubs SVG Lucide via slot #icon (remplacement Lucide Story 10.21 — zero dep bloquante).
  Tokens @theme exclusifs (AC6 scan 0 hex) — verdict-*/fa-*/admin-* livres 10.14+patch 10.17.

  Patches code-review 2026-04-22 :
  - CRITICAL-1/2 contraste AA : text = -strong (800) sur bg = -soft (100) en light mode,
    text = -soft (100) sur bg = base/20 en dark mode. Ratios AA calcules test pur JS.
  - HIGH-5 [&_svg] scope : sizing SVG porte par le wrapper icon, PAS la racine (no leak label).
  - HIGH-6 icon slot empty bypass : defense en profondeur via inspection DOM post-nextTick
    (non plus uniquement !slots.icon — un <template #icon></template> vide est detecte).
  - MEDIUM-1 role="status" : remplace par role="img" (Badge statique, pas live-region
    polite ; les dashboards denses ne saturent plus le screen reader).
  - MEDIUM-2 DRY labels : LABELS_FR importes depuis registry.ts.
  - MEDIUM-3 DRY types : BadgeProps importe depuis registry.ts.
  - MEDIUM-5 SSR guard : runtime checks conditionnes par import.meta.dev (client-only
    dev-only, silencieux en prod et en SSR).
-->
<script setup lang="ts">
import { computed, nextTick, onMounted, ref, useSlots } from 'vue';
import {
  VERDICT_LABELS_FR,
  LIFECYCLE_LABELS_FR,
  ADMIN_LABELS_FR,
  type BadgeProps,
} from './registry';

const props = withDefaults(defineProps<BadgeProps>(), {
  size: 'md',
});

const slots = useSlots();

// aria-label compose francais (AC8) — switch sur variant narrow `state` correctement
// en JS (piege #25 : le narrowing template Vue n'existe pas cross-block, passer par computed).
const ariaLabel = computed<string>(() => {
  switch (props.variant) {
    case 'verdict': {
      const suffix = props.conditional ? ' (conditionnel)' : '';
      return `Verdict ${VERDICT_LABELS_FR[props.state]}${suffix}`;
    }
    case 'lifecycle':
      return `Statut ${LIFECYCLE_LABELS_FR[props.state]}`;
    case 'admin':
      return `Criticité admin ${ADMIN_LABELS_FR[props.state]}`;
  }
});

// Mapping variant x state -> classes Tailwind tokens @theme (AC6 + patch CRITICAL 10.17).
// Pattern light : bg-*-soft (100) + text-*-strong (800) => AA >= 4.5:1 test JS pur.
// Pattern dark  : bg-base/20 + text-*-soft (100) => AA >= 10:1 sur dark bg.
const variantClasses = computed<string>(() => {
  switch (props.variant) {
    case 'verdict':
      return {
        pass: 'bg-verdict-pass-soft text-verdict-pass-strong dark:bg-verdict-pass/20 dark:text-verdict-pass-soft',
        fail: 'bg-verdict-fail-soft text-verdict-fail-strong dark:bg-verdict-fail/20 dark:text-verdict-fail-soft',
        reported: 'bg-verdict-reported-soft text-verdict-reported-strong dark:bg-verdict-reported/20 dark:text-verdict-reported-soft',
        na: 'bg-verdict-na-soft text-verdict-na-strong dark:bg-verdict-na/20 dark:text-verdict-na-soft',
      }[props.state];
    case 'lifecycle':
      return {
        draft: 'bg-fa-draft-soft text-fa-draft-strong dark:bg-fa-draft/20 dark:text-fa-draft-soft',
        snapshot_frozen: 'bg-fa-snapshot-frozen-soft text-fa-snapshot-frozen-strong dark:bg-fa-snapshot-frozen/20 dark:text-fa-snapshot-frozen-soft',
        signed: 'bg-fa-signed-soft text-fa-signed-strong dark:bg-fa-signed/20 dark:text-fa-signed-soft',
        exported: 'bg-fa-exported-soft text-fa-exported-strong dark:bg-fa-exported/20 dark:text-fa-exported-soft',
        submitted: 'bg-fa-submitted-soft text-fa-submitted-strong dark:bg-fa-submitted/20 dark:text-fa-submitted-soft',
        in_review: 'bg-fa-in-review-soft text-fa-in-review-strong dark:bg-fa-in-review/20 dark:text-fa-in-review-soft',
        accepted: 'bg-fa-accepted-soft text-fa-accepted-strong dark:bg-fa-accepted/20 dark:text-fa-accepted-soft',
        rejected: 'bg-fa-rejected-soft text-fa-rejected-strong dark:bg-fa-rejected/20 dark:text-fa-rejected-soft',
        withdrawn: 'bg-fa-withdrawn-soft text-fa-withdrawn-strong dark:bg-fa-withdrawn/20 dark:text-fa-withdrawn-soft',
      }[props.state];
    case 'admin':
      return {
        n1: 'bg-admin-n1-soft text-admin-n1-strong dark:bg-admin-n1/20 dark:text-admin-n1-soft',
        n2: 'bg-admin-n2-soft text-admin-n2-strong dark:bg-admin-n2/20 dark:text-admin-n2-soft',
        n3: 'bg-admin-n3-soft text-admin-n3-strong dark:bg-admin-n3/20 dark:text-admin-n3-soft',
      }[props.state];
  }
});

// Classes size base (root) — hauteur + texte + padding + gap.
// Q4 verrouillee — PAS touch target 44 px car Badge affichage pur (!= Button).
const sizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs min-h-[20px] max-h-[24px] px-1.5 py-0.5 gap-1';
    case 'md':
      return 'text-sm min-h-[24px] max-h-[28px] px-2 py-0.5 gap-1';
    case 'lg':
      return 'text-base min-h-[32px] max-h-[36px] px-3 py-1 gap-1.5';
  }
});

// Sizing du SVG porte UNIQUEMENT par le wrapper icon (patch HIGH-5 10.17).
// L'arbitrary selector `[&_svg]` reste descendant mais scope au wrapper → aucun
// leak vers les SVGs potentiels dans le slot default (label).
const iconWrapperSizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm':
      return '[&_svg]:h-3 [&_svg]:w-3';
    case 'md':
      return '[&_svg]:h-3.5 [&_svg]:w-3.5';
    case 'lg':
      return '[&_svg]:h-4 [&_svg]:w-4';
  }
});

// Italic si verdict conditionnel (AC4 FR40 — Q21 clarification Lot 4).
const conditionalClasses = computed<string>(() =>
  props.variant === 'verdict' && props.conditional ? 'italic' : '',
);

// Defense-in-depth runtime : Regle 11 UX enforcement (AC3 + patch HIGH-6/M5 10.17).
// Inspection post-mount via refs DOM : fast path + slow path uniformes pour icon ET label.
// Guard `import.meta.dev` : les warnings n'apparaissent qu'en developpement client
// (silencieux en SSR + silencieux en production — pas de bruit user-facing).
const iconRef = ref<HTMLSpanElement | null>(null);
const labelRef = ref<HTMLSpanElement | null>(null);

onMounted(async () => {
  // Short-circuit prod : drop tout le bloc en build optimise.
  // `import.meta.env.DEV` (Vite standard) = true en dev + true en test, false en prod build.
  if (!import.meta.env.DEV) return;

  await nextTick();

  // Icon : defense en profondeur sur DOM vide (slot absent OU slot `<template #icon></template>` vide).
  const iconEmpty = !slots.icon || (iconRef.value?.childElementCount ?? 0) === 0;
  if (iconEmpty) {
    // eslint-disable-next-line no-console
    console.error('[ui/Badge] slot #icon is REQUIRED (Regle 11 UX : couleur jamais seule porteuse).');
  }

  // Label : defense en profondeur sur DOM vide (slot absent OU slot sans texte).
  const labelEmpty =
    typeof slots.default !== 'function' ||
    !(labelRef.value?.textContent?.trim());
  if (labelEmpty) {
    // eslint-disable-next-line no-console
    console.warn('[ui/Badge] slot default (label FR) is REQUIRED for screen readers.');
  }
});
</script>

<template>
  <!--
    role="img" (MEDIUM-1 patch) : Badge = indicateur statique, pas live region.
    Un dashboard rendant N badges ne declenche plus N annonces polite au chargement.
    L'aria-label porte la semantique complete pour les lecteurs d'ecran.
  -->
  <span
    role="img"
    :aria-label="ariaLabel"
    :class="[
      'inline-flex items-center rounded font-medium whitespace-nowrap',
      variantClasses,
      sizeClasses,
      conditionalClasses,
    ]"
  >
    <!-- Slot icon : decoratif (aria-hidden), semantique portee par aria-label parent. -->
    <span
      ref="iconRef"
      data-testid="badge-icon-slot"
      aria-hidden="true"
      :class="['inline-flex items-center', iconWrapperSizeClasses]"
    >
      <slot name="icon" />
    </span>
    <!-- Slot default : label FR obligatoire (consommateur fournit texte complet Q3). -->
    <span ref="labelRef" data-testid="badge-label-slot">
      <slot />
    </span>
  </span>
</template>
