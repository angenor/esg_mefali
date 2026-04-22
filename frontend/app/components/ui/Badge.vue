<!--
  ui/Badge.vue — primitive UI Phase 0 Story 10.17.
  Union discriminee variant x state : verdict (4) + lifecycle (9) + admin (3).
  3 signaux redondants OBLIGATOIRES (Regle 11 UX Step 12) : couleur + icone + texte.
  Non-interactif (affichage pur) : native <span>, role="status", aria-label compose.
  Stubs SVG Lucide via slot #icon (remplacement Lucide Story 10.21 — zero dep bloquante).
  Tokens @theme exclusifs (AC6 scan 0 hex) — verdict-* / fa-* / admin-* livres Story 10.14.
  Dark mode >= 6 dark: par famille variante (AC7 seuil primitive 10.15 MEDIUM-2 adapte).
-->
<script setup lang="ts">
import { computed, nextTick, onMounted, ref, useSlots } from 'vue';
import type {
  VerdictState,
  LifecycleState,
  AdminCriticality,
  BadgeSize,
} from './registry';

// Union discriminee compile-time (AC1 + Badge.test-d.ts enforcement).
// La discrimination sur `variant` garantit que `state` est coherent : le compilateur
// rejette `{ variant: 'verdict', state: 'draft' }` (piege #21). La prop `conditional`
// n'est autorisee QUE sur la variante `verdict` (AC4).
type BadgePropsBase = { size?: BadgeSize };
type BadgeProps =
  | (BadgePropsBase & { variant: 'verdict'; state: VerdictState; conditional?: boolean })
  | (BadgePropsBase & { variant: 'lifecycle'; state: LifecycleState })
  | (BadgePropsBase & { variant: 'admin'; state: AdminCriticality });

const props = withDefaults(defineProps<BadgeProps>(), {
  size: 'md',
});

const slots = useSlots();

// Labels FR par state (composition aria-label AC8). Mapping centralise pour faciliter
// i18n future (Phase Growth : externaliser vers `useI18n()` si > 2 langues).
const VERDICT_LABELS_FR: Record<VerdictState, string> = {
  pass: 'Validé',
  fail: 'Non conforme',
  reported: 'À documenter',
  na: 'Non applicable',
};
const LIFECYCLE_LABELS_FR: Record<LifecycleState, string> = {
  draft: 'Brouillon',
  snapshot_frozen: 'Figé',
  signed: 'Signé',
  exported: 'Exporté',
  submitted: 'Soumis',
  in_review: 'En revue',
  accepted: 'Accepté',
  rejected: 'Refusé',
  withdrawn: 'Retiré',
};
const ADMIN_LABELS_FR: Record<AdminCriticality, string> = {
  n1: 'N1',
  n2: 'N2',
  n3: 'N3',
};

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

// Mapping variant x state -> classes Tailwind tokens @theme (AC6).
// Pattern fond soft + texte solid pour verdict (contraste AA prouve §6 codemap) ;
// pattern fond /10 + texte solid pour lifecycle + admin (opacite Tailwind 4).
const variantClasses = computed<string>(() => {
  switch (props.variant) {
    case 'verdict':
      return {
        pass: 'bg-verdict-pass-soft text-verdict-pass dark:bg-verdict-pass/20 dark:text-verdict-pass-soft',
        fail: 'bg-verdict-fail-soft text-verdict-fail dark:bg-verdict-fail/20 dark:text-verdict-fail-soft',
        reported: 'bg-verdict-reported-soft text-verdict-reported dark:bg-verdict-reported/20 dark:text-verdict-reported-soft',
        na: 'bg-verdict-na-soft text-verdict-na dark:bg-verdict-na/20 dark:text-verdict-na-soft',
      }[props.state];
    case 'lifecycle':
      return {
        draft: 'bg-fa-draft/10 text-fa-draft dark:bg-fa-draft/20 dark:text-fa-draft',
        snapshot_frozen: 'bg-fa-snapshot-frozen/10 text-fa-snapshot-frozen dark:bg-fa-snapshot-frozen/20 dark:text-fa-snapshot-frozen',
        signed: 'bg-fa-signed/10 text-fa-signed dark:bg-fa-signed/20 dark:text-fa-signed',
        exported: 'bg-fa-exported/10 text-fa-exported dark:bg-fa-exported/20 dark:text-fa-exported',
        submitted: 'bg-fa-submitted/10 text-fa-submitted dark:bg-fa-submitted/20 dark:text-fa-submitted',
        in_review: 'bg-fa-in-review/10 text-fa-in-review dark:bg-fa-in-review/20 dark:text-fa-in-review',
        accepted: 'bg-fa-accepted/10 text-fa-accepted dark:bg-fa-accepted/20 dark:text-fa-accepted',
        rejected: 'bg-fa-rejected/10 text-fa-rejected dark:bg-fa-rejected/20 dark:text-fa-rejected',
        withdrawn: 'bg-fa-withdrawn/10 text-fa-withdrawn dark:bg-fa-withdrawn/20 dark:text-fa-withdrawn',
      }[props.state];
    case 'admin':
      return {
        n1: 'bg-admin-n1/10 text-admin-n1 dark:bg-admin-n1/20 dark:text-admin-n1',
        n2: 'bg-admin-n2/10 text-admin-n2 dark:bg-admin-n2/20 dark:text-admin-n2',
        n3: 'bg-admin-n3/10 text-admin-n3 dark:bg-admin-n3/20 dark:text-admin-n3',
      }[props.state];
  }
});

// Classes size (AC5) — hauteurs 20/24/32 px adaptees affichage inline non-interactif
// (Q4 verrouillee — PAS touch target 44 px car Badge != Button).
// Arbitrary selector `[&_svg]` cible le SVG enfant direct du slot icon (piege #22 atténué).
const sizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs min-h-[20px] px-1.5 py-0.5 gap-1 [&_svg]:h-3 [&_svg]:w-3';
    case 'md':
      return 'text-sm min-h-[24px] px-2 py-0.5 gap-1 [&_svg]:h-3.5 [&_svg]:w-3.5';
    case 'lg':
      return 'text-base min-h-[32px] px-3 py-1 gap-1.5 [&_svg]:h-4 [&_svg]:w-4';
  }
});

// Italic si verdict conditionnel (AC4 FR40 — Q21 clarification Lot 4).
const conditionalClasses = computed<string>(() =>
  props.variant === 'verdict' && props.conditional ? 'italic' : '',
);

// Defense-in-depth runtime : Regle 11 UX enforcement (AC3).
// Inspection post-mount via ref DOM plutot qu'invocation slots.default() dans
// onMounted (evite warning Vue "Slot invoked outside render function").
const labelRef = ref<HTMLSpanElement | null>(null);

onMounted(async () => {
  if (!slots.icon) {
    // eslint-disable-next-line no-console
    console.error('[ui/Badge] slot #icon is REQUIRED (Regle 11 UX : couleur jamais seule porteuse).');
  }
  // Fast path : slot default absent (non fourni par le consommateur).
  if (typeof slots.default !== 'function') {
    // eslint-disable-next-line no-console
    console.warn('[ui/Badge] slot default (label FR) is REQUIRED for screen readers.');
    return;
  }
  // Slow path : slot fourni mais potentiellement vide — inspecter le DOM rendu.
  await nextTick();
  const text = labelRef.value?.textContent?.trim() ?? '';
  if (!text) {
    // eslint-disable-next-line no-console
    console.warn('[ui/Badge] slot default (label FR) is REQUIRED for screen readers.');
  }
});
</script>

<template>
  <span
    role="status"
    :aria-label="ariaLabel"
    :class="[
      'inline-flex items-center rounded font-medium whitespace-nowrap',
      variantClasses,
      sizeClasses,
      conditionalClasses,
    ]"
  >
    <!-- Slot icon : decoratif (aria-hidden), la semantique est portee par aria-label parent. -->
    <span data-testid="badge-icon-slot" aria-hidden="true" class="inline-flex items-center">
      <slot name="icon" />
    </span>
    <!-- Slot default : label FR obligatoire (consommateur fournit texte complet Q3). -->
    <span ref="labelRef" data-testid="badge-label-slot">
      <slot />
    </span>
  </span>
</template>
