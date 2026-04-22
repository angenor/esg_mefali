<!--
  ui/Select.vue — primitive UI P0 Story 10.16.
  Native <select> stylise Tailwind x 3 sizes (sm/md/lg).
  Q3 verrouillee : natif MVP (override Epic AC5 Reka UI SelectRoot, trace
  DEF-10.16-1 deferred-work.md). Reka UI Combobox riche = Story 10.19.
  Rationale : a11y ChromeVox/VoiceOver native battle-tested, 0 dep ajoutee,
  touch target iOS picker wheel + Android bottom sheet natifs.
  Props options: Array<{ value: string; label: string; disabled?: boolean }>
  + multiple pour select-multiple natif.
  ChevronDown stub SVG absolute droite (masque fleche native cross-browser).
  Dark mode >= 6 dark: (AC7). Tokens @theme exclusifs (AC8).
-->
<script setup lang="ts">
import { computed, useId } from 'vue';
import type { FormSize } from './registry';

export type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type SelectProps = {
  modelValue: string | string[];
  label: string;
  options: SelectOption[];
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  size?: FormSize;
  multiple?: boolean;
  name?: string;
};

const props = withDefaults(defineProps<SelectProps>(), {
  size: 'md',
  required: false,
  disabled: false,
  multiple: false,
});

const emit = defineEmits<{ 'update:modelValue': [value: string | string[]] }>();

const autoId = useId();
const inputId = computed<string>(() => props.id ?? `ui-select-${autoId}`);
const errorId = computed<string>(() => `${inputId.value}-error`);
const hintId = computed<string>(() => `${inputId.value}-hint`);

const describedBy = computed<string | undefined>(() => {
  const ids: string[] = [];
  if (props.hint) ids.push(hintId.value);
  if (props.error) ids.push(errorId.value);
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

function handleChange(event: Event): void {
  const target = event.target as HTMLSelectElement;
  if (props.multiple) {
    const values = Array.from(target.selectedOptions).map((o) => o.value);
    emit('update:modelValue', values);
  } else {
    // Piege #13 codemap : value toujours string cote DOM natif.
    emit('update:modelValue', target.value);
  }
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
      <select
        :id="inputId"
        :value="modelValue"
        :multiple="multiple"
        :required="required"
        :disabled="disabled"
        :name="name"
        :aria-required="required ? 'true' : undefined"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        :class="[
          'block w-full rounded border bg-white dark:bg-dark-input',
          'text-surface-text dark:text-surface-dark-text',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'focus-visible:ring-offset-surface-bg dark:focus-visible:ring-offset-dark-card',
          'disabled:bg-gray-50 dark:disabled:bg-dark-card',
          'disabled:text-gray-500 dark:disabled:text-gray-600',
          'disabled:cursor-not-allowed',
          'transition-colors duration-150',
          'appearance-none',
          multiple ? '' : 'pr-10',
          sizeClasses,
          stateClasses,
        ]"
        @change="handleChange"
      >
        <option v-if="placeholder && !multiple" value="" disabled>
          {{ placeholder }}
        </option>
        <option
          v-for="opt in options"
          :key="opt.value"
          :value="opt.value"
          :disabled="opt.disabled"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- STUB ChevronDown Lucide 10.21. Masque par multiple (no caret). -->
      <span
        v-if="!multiple"
        class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400 dark:text-gray-500"
        aria-hidden="true"
      >
        <svg
          class="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
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
  </div>
</template>
