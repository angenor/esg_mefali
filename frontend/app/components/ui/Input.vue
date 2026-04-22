<!--
  ui/Input.vue — primitive UI P0 Story 10.16.
  7 types HTML5 (text/email/number/password/url/tel/search) x 3 sizes (sm/md/lg).
  Slots #iconLeft / #iconRight (coherent Button 10.15 Q2).
  Auto-ID useId() Vue 3.5+ si prop id absente (AC5 label for/id association).
  States : default / focus / error / disabled / readonly.
  Dark mode >= 6 dark: (AC7 exception 10.15 MEDIUM-2 seuil primitive simple).
  Tokens @theme exclusifs (AC8 : 0 hex hardcode scan).
  Validation externe : prop `error: string` pilotee par le parent (Zod/VeeValidate
  / backend async) — la primitive reste "dumb" (SRP, Q4 verrouillee).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { InputType, FormSize } from './registry';

type InputMode =
  | 'text'
  | 'numeric'
  | 'decimal'
  | 'tel'
  | 'email'
  | 'url'
  | 'search'
  | 'none';

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
  inputmode?: InputMode;
  name?: string;
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

// Size -> classes Tailwind (AC6 touch target >= 44 px md+, sm pointer:coarse).
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

// State -> classes Tailwind (error override focus ring, AC5 couleur + icone + bord).
const stateClasses = computed<string>(() => {
  if (props.error) {
    return 'border-brand-red focus-visible:ring-brand-red dark:border-brand-red';
  }
  return 'border-gray-300 dark:border-dark-border focus-visible:ring-brand-green';
});

// inputmode auto si non fourni pour type email/tel/search (AC6 UX mobile).
const resolvedInputmode = computed<InputMode | undefined>(() => {
  if (props.inputmode) return props.inputmode;
  switch (props.type) {
    case 'email':
      return 'email';
    case 'tel':
      return 'tel';
    case 'search':
      return 'search';
    case 'url':
      return 'url';
    default:
      return undefined;
  }
});

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  // Laisse string (cohesion v-model standard, piege #11 codemap §5) —
  // consommateur coerce explicitement via v-model.number si besoin.
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
        :inputmode="resolvedInputmode"
        :name="name"
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
          'read-only:bg-gray-50 dark:read-only:bg-dark-card',
          'transition-colors duration-150',
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
      <svg
        class="h-3.5 w-3.5 flex-shrink-0"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <span>{{ error }}</span>
    </p>
  </div>
</template>
