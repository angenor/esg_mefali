<!--
  ui/Textarea.vue — primitive UI P0 Story 10.16.
  Native <textarea> x 3 sizes (sm/md/lg).
  Compteur 400 chars stricts (AC4) avec 3 seuils :
    < 350 : gris (text-gray-500 dark:text-gray-400)
    >= 350 && < 400 : orange (text-brand-orange, 3,85:1 sur blanc — auxiliaire acceptable §6)
    >= 400 : rouge (text-brand-red, 4,83:1 AA) + role="status" aria-live="polite".
  Triple defense frappe bloquee (spec 018) :
    1) attribut HTML native maxlength (bloque saisie clavier standard)
    2) handler @input tronque a maxlength cote JS (capture paste + programmatique)
    3) validator backend (ligne de defense finale, hors composant).
  Pas de slots icones (UX : zone multi-ligne, icone inline confusante).
  Dark mode >= 6 dark: (AC7). Tokens @theme exclusifs (AC8).
  Validation externe prop `error` (Q4 verrouillee).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { FormSize } from './registry';
import { TEXTAREA_DEFAULT_MAX_LENGTH } from './registry';

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
  name?: string;
};

const props = withDefaults(defineProps<TextareaProps>(), {
  size: 'md',
  rows: 4,
  maxlength: TEXTAREA_DEFAULT_MAX_LENGTH,
  showCounter: true,
  required: false,
  disabled: false,
  readonly: false,
});

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

const autoId = useId();
const inputId = computed<string>(() => props.id ?? `ui-textarea-${autoId}`);
const errorId = computed<string>(() => `${inputId.value}-error`);
const hintId = computed<string>(() => `${inputId.value}-hint`);
const counterId = computed<string>(() => `${inputId.value}-counter`);

const describedBy = computed<string | undefined>(() => {
  const ids: string[] = [];
  if (props.hint) ids.push(hintId.value);
  if (props.error) ids.push(errorId.value);
  if (props.showCounter) ids.push(counterId.value);
  return ids.length ? ids.join(' ') : undefined;
});

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

const stateClasses = computed<string>(() => {
  if (props.error) {
    return 'border-brand-red focus-visible:ring-brand-red dark:border-brand-red';
  }
  return 'border-gray-300 dark:border-dark-border focus-visible:ring-brand-green';
});

// Seuils compteur (AC4) : 50 chars avant la limite => orange auxiliaire.
const ORANGE_THRESHOLD_OFFSET = 50;

const currentLength = computed<number>(
  () => String(props.modelValue ?? '').length,
);

const isAtLimit = computed<boolean>(() => currentLength.value >= props.maxlength);

const counterClasses = computed<string>(() => {
  const len = currentLength.value;
  if (len >= props.maxlength) return 'text-brand-red font-medium';
  if (len >= props.maxlength - ORANGE_THRESHOLD_OFFSET) return 'text-brand-orange';
  return 'text-gray-500 dark:text-gray-400';
});

function handleInput(event: Event): void {
  const target = event.target as HTMLTextAreaElement;
  // Defense en profondeur JS : tronque a maxlength meme si paste ou programmatique bypass.
  const truncated = target.value.slice(0, props.maxlength);
  if (truncated !== target.value) {
    // Re-sync DOM pour eviter desynchronisation v-model / DOM (piege #16 codemap).
    target.value = truncated;
  }
  emit('update:modelValue', truncated);
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

    <textarea
      :id="inputId"
      :value="modelValue"
      :rows="rows"
      :maxlength="maxlength"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
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
        'resize-y',
        sizeClasses,
        stateClasses,
      ]"
      @input="handleInput"
    />

    <div class="flex justify-between items-start gap-2">
      <p
        v-if="error"
        :id="errorId"
        role="alert"
        class="flex items-center gap-1 text-xs text-brand-red"
      >
        <!-- STUB AlertCircle Lucide 10.21. -->
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
      <p
        v-else-if="hint"
        :id="hintId"
        class="text-xs text-gray-500 dark:text-gray-400"
      >
        {{ hint }}
      </p>
      <span v-else aria-hidden="true"></span>

      <p
        v-if="showCounter"
        :id="counterId"
        :class="['text-xs tabular-nums flex-shrink-0', counterClasses]"
        :role="isAtLimit ? 'status' : undefined"
        :aria-live="isAtLimit ? 'polite' : undefined"
      >
        {{ currentLength }}/{{ maxlength }}
      </p>
    </div>
  </div>
</template>
