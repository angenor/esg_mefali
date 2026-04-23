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
import EsgIcon from './EsgIcon.vue';
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

// H-4 : emit discrimine selon type=number (Number) vs autres (string).
const emit = defineEmits<{ 'update:modelValue': [value: string | number] }>();

// Auto-ID pour label association si prop id non fournie (AC5).
const autoId = useId();
const inputId = computed<string>(() => props.id ?? `ui-input-${autoId}`);
const errorId = computed<string>(() => `${inputId.value}-error`);
const hintId = computed<string>(() => `${inputId.value}-hint`);

// H-1 : aria-describedby combine hint + error si les 2 presents (AC5 post-review).
// Les 2 paragraphes sont rendus simultanement (v-if hint tout le temps, error en plus).
const describedBy = computed<string | undefined>(() => {
  const ids = [
    props.hint ? hintId.value : null,
    props.error ? errorId.value : null,
  ].filter((id): id is string => id !== null);
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

// M-4 : defense en profondeur maxlength (parite avec Textarea triple defense).
// Exclut type=number : valeur DOM type=number n'est pas une chaine humaine a trunquer.
function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement;

  // H-4 : coercion Number si type=number (contrat modelValue number respecte).
  if (props.type === 'number') {
    const raw = target.value;
    if (raw === '') {
      emit('update:modelValue', '');
      return;
    }
    const num = Number(raw);
    emit('update:modelValue', Number.isNaN(num) ? '' : num);
    return;
  }

  // M-4 : troncature JS defense en profondeur si maxlength defini (types text).
  const max = props.maxlength;
  let value = target.value;
  if (typeof max === 'number' && value.length > max) {
    value = value.slice(0, max);
    // Re-sync DOM (pattern Textarea H-2).
    const { selectionStart, selectionEnd } = target;
    target.value = value;
    if (selectionStart !== null && selectionEnd !== null) {
      target.setSelectionRange(
        Math.min(selectionStart, value.length),
        Math.min(selectionEnd, value.length),
      );
    }
  }
  emit('update:modelValue', value);
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
          // M-5 : offset distinct du bg input en dark (neutral-900 != dark-input #1F2937).
          'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-neutral-900',
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

    <!-- H-1 : hint rendu meme quand error present (aria-describedby combine les 2). -->
    <p
      v-if="hint"
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
      <!-- AlertCircle Lucide 10.21 migration (piege #48 shim class preserved). -->
      <EsgIcon name="alert-circle" class="h-3.5 w-3.5 flex-shrink-0" decorative />
      <span>{{ error }}</span>
    </p>
  </div>
</template>
