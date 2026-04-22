<!--
  ui/Button.vue — primitive UI P0 Story 10.15.
  4 variants (primary/secondary/ghost/danger) × 3 sizes (sm/md/lg).
  Slots #iconLeft / #iconRight pour Lucide (10.21) ou SVG inline.
  Loading = absolute spinner + visibility:hidden sur texte (layout stable Q3).
  prefers-reduced-motion : opacity step uniquement, spinner rotation ralentie (AC6).
-->
<script setup lang="ts">
import { computed, onMounted, useSlots } from 'vue';
import type { ButtonVariant, ButtonSize } from './registry';

// Type discrimine : iconOnly=true force ariaLabel (AC5 compile-time enforcement).
type ButtonPropsBase = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
};
type ButtonProps =
  | (ButtonPropsBase & { iconOnly?: false | undefined; ariaLabel?: string })
  | (ButtonPropsBase & { iconOnly: true; ariaLabel: string });

const props = withDefaults(defineProps<ButtonProps>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
  type: 'button',
});

const emit = defineEmits<{ click: [event: MouseEvent] }>();

// Variant -> classes Tailwind (AC2 : tokens @theme exclusivement).
const variantClasses = computed<string>(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-brand-green text-white hover:opacity-90 focus-visible:ring-brand-green';
    case 'secondary':
      return 'bg-surface-bg dark:bg-dark-card text-surface-text dark:text-surface-dark-text border border-gray-300 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-hover focus-visible:ring-brand-blue';
    case 'ghost':
      return 'bg-transparent text-surface-text dark:text-surface-dark-text hover:bg-gray-100 dark:hover:bg-dark-hover focus-visible:ring-gray-400';
    case 'danger':
      return 'bg-brand-red text-white hover:opacity-90 focus-visible:ring-brand-red';
  }
});

// Size -> classes Tailwind (AC3 : touch target >= 44 px md+, sm pointer:coarse).
const sizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm':
      // sm: 32px desktop baseline, mais min-h-[44px] en touch via pointer:coarse.
      return 'min-h-[32px] [@media(pointer:coarse)]:min-h-[44px] px-3 py-1.5 text-sm';
    case 'md':
      return 'min-h-[44px] px-4 py-2 text-sm';
    case 'lg':
      return 'min-h-[48px] px-6 py-3 text-base';
  }
});

const isInactive = computed<boolean>(() => props.disabled || props.loading);

const slots = useSlots();

// Runtime warning icon-only sans ariaLabel (defense en profondeur + AC5).
onMounted(() => {
  if (
    props.iconOnly === true &&
    (!props.ariaLabel || props.ariaLabel.trim().length === 0)
  ) {
    // eslint-disable-next-line no-console
    console.warn('[ui/Button] iconOnly=true requires non-empty ariaLabel prop.');
  }
  // Si slot default vide ET pas iconOnly ET pas ariaLabel, le bouton risque d'etre
  // invisible aux lecteurs d'ecran. On signale en developpement (pas de throw).
  // Note : on teste uniquement la presence de la fonction slot, pas son rendu
  // (invoquer slots.default() hors render declenche un warning Vue).
  const hasDefaultSlot = typeof slots.default === 'function';
  if (!hasDefaultSlot && !props.iconOnly && !props.ariaLabel) {
    // eslint-disable-next-line no-console
    console.warn(
      '[ui/Button] button has no visible label and no ariaLabel — screen readers will announce "button" only.',
    );
  }
});

function handleClick(event: MouseEvent): void {
  if (isInactive.value) {
    event.preventDefault();
    event.stopPropagation();
    return;
  }
  emit('click', event);
}
</script>

<template>
  <button
    :type="type"
    :disabled="isInactive"
    :aria-disabled="disabled ? 'true' : undefined"
    :aria-busy="loading ? 'true' : undefined"
    :aria-label="ariaLabel"
    :class="[
      // Base : layout + transitions sobres (Q10 restraint institutionnel, AC6).
      'relative inline-flex items-center justify-center gap-2 rounded font-medium',
      'transition-opacity duration-150',
      'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card',
      'disabled:cursor-not-allowed disabled:opacity-60',
      // prefers-reduced-motion deja gere par transition-opacity (pas de scale/translate).
      variantClasses,
      sizeClasses,
    ]"
    @click="handleClick"
  >
    <!-- Slot iconLeft : texte conserve sa box en loading via visibility. -->
    <span
      v-if="$slots.iconLeft"
      class="inline-flex items-center"
      :class="{ invisible: loading }"
      aria-hidden="true"
    >
      <slot name="iconLeft" />
    </span>

    <!-- Slot default : texte principal, invisible (pas collapse) en loading. -->
    <span :class="{ invisible: loading }">
      <slot />
    </span>

    <!-- Slot iconRight : symetrique iconLeft. -->
    <span
      v-if="$slots.iconRight"
      class="inline-flex items-center"
      :class="{ invisible: loading }"
      aria-hidden="true"
    >
      <slot name="iconRight" />
    </span>

    <!-- Spinner absolute centre en loading (Q3 layout stable). -->
    <!-- STUB: remplace par <Loader2 /> Lucide Story 10.21. Animation rotation
         ralentie en prefers-reduced-motion via <style scoped> ci-dessous. -->
    <span
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center"
      aria-hidden="true"
    >
      <svg
        class="animate-spin h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10" class="opacity-25" />
        <path d="M12 2a10 10 0 0 1 10 10" class="opacity-75" />
      </svg>
    </span>
  </button>
</template>

<style scoped>
/* prefers-reduced-motion : spinner ralenti (pas supprime, reste fonctionnel). */
@media (prefers-reduced-motion: reduce) {
  .animate-spin {
    animation-duration: 2s;
  }
}
</style>
