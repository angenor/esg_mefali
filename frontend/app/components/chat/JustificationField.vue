<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string
  prompt?: string | null
  required?: boolean
  disabled?: boolean
  maxLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  prompt: null,
  required: false,
  disabled: false,
  maxLength: 400,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const charCount = computed(() => props.modelValue.length)
const remaining = computed(() => props.maxLength - charCount.value)
const isInvalid = computed(() => props.required && props.modelValue.trim().length === 0)

function onInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  // Defense en profondeur : tronquer cote client
  const value = target.value.slice(0, props.maxLength)
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="mt-3">
    <label
      v-if="prompt"
      :for="`justif-${prompt}`"
      class="block text-sm font-medium text-surface-text dark:text-surface-dark-text mb-1"
    >
      {{ prompt }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <textarea
      :id="`justif-${prompt || 'field'}`"
      :value="modelValue"
      :disabled="disabled"
      :maxlength="maxLength"
      :aria-invalid="isInvalid"
      :aria-describedby="`justif-counter-${prompt || 'field'}`"
      rows="3"
      class="w-full rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text px-3 py-2 text-sm focus:ring-2 focus:ring-brand-blue focus:border-brand-blue disabled:opacity-50"
      placeholder="Ta reponse..."
      @input="onInput"
    />
    <div
      :id="`justif-counter-${prompt || 'field'}`"
      class="flex items-center justify-between text-xs mt-1"
    >
      <span
        v-if="isInvalid"
        class="text-red-500 dark:text-red-400"
      >
        Ce champ est obligatoire.
      </span>
      <span v-else class="text-gray-500 dark:text-gray-400">
        Justification optionnelle
      </span>
      <span
        :class="[
          'tabular-nums',
          remaining < 50 ? 'text-orange-500' : 'text-gray-500 dark:text-gray-400',
        ]"
      >
        {{ charCount }} / {{ maxLength }}
      </span>
    </div>
  </div>
</template>
