<script setup lang="ts">
import { computed, ref } from 'vue'
import type { InteractiveOption } from '~/types/interactive-question'
import JustificationField from './JustificationField.vue'

interface Props {
  options: InteractiveOption[]
  minSelections?: number
  maxSelections?: number
  disabled?: boolean
  requiresJustification?: boolean
  justificationPrompt?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  minSelections: 1,
  maxSelections: 8,
  disabled: false,
  requiresJustification: false,
  justificationPrompt: null,
})

const emit = defineEmits<{
  (e: 'submit', payload: { values: string[]; justification?: string }): void
}>()

const selected = ref<Set<string>>(new Set())
const justification = ref('')
const submitted = ref(false)

const selectedCount = computed(() => selected.value.size)

const canSelectMore = computed(() => selectedCount.value < props.maxSelections)

const canSubmit = computed(() => {
  if (selectedCount.value < props.minSelections) return false
  if (selectedCount.value > props.maxSelections) return false
  if (props.requiresJustification && justification.value.trim().length === 0) {
    return false
  }
  return !props.disabled && !submitted.value
})

function isChecked(optionId: string): boolean {
  return selected.value.has(optionId)
}

function toggle(optionId: string) {
  if (props.disabled || submitted.value) return
  const next = new Set(selected.value)
  if (next.has(optionId)) {
    next.delete(optionId)
  } else if (canSelectMore.value) {
    next.add(optionId)
  }
  selected.value = next
}

function submit() {
  if (!canSubmit.value) return
  submitted.value = true
  emit('submit', {
    values: Array.from(selected.value),
    justification: props.requiresJustification ? justification.value : undefined,
  })
}
</script>

<template>
  <div role="group" aria-labelledby="multi-choice-label" class="space-y-2">
    <button
      v-for="option in options"
      :key="option.id"
      type="button"
      role="checkbox"
      :aria-checked="isChecked(option.id)"
      :disabled="disabled || submitted || (!isChecked(option.id) && !canSelectMore)"
      :class="[
        'w-full text-left px-4 py-3 rounded-lg border transition-all',
        'focus:outline-none focus:ring-2 focus:ring-brand-blue',
        isChecked(option.id)
          ? 'border-brand-blue bg-brand-blue/10 dark:bg-brand-blue/20'
          : 'border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card hover:bg-gray-50 dark:hover:bg-dark-hover',
        (disabled || submitted) && 'opacity-50 cursor-not-allowed',
        (!isChecked(option.id) && !canSelectMore) && 'opacity-60',
      ]"
      @click="toggle(option.id)"
    >
      <span class="flex items-start gap-3 text-surface-text dark:text-surface-dark-text">
        <span
          :class="[
            'flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5',
            isChecked(option.id)
              ? 'border-brand-blue bg-brand-blue text-white'
              : 'border-gray-300 dark:border-dark-border',
          ]"
        >
          <svg
            v-if="isChecked(option.id)"
            class="w-3 h-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </span>
        <span v-if="option.emoji" class="text-xl flex-shrink-0">{{ option.emoji }}</span>
        <span class="flex-1">
          <span class="block font-medium text-sm">{{ option.label }}</span>
          <span
            v-if="option.description"
            class="block text-xs text-gray-500 dark:text-gray-400 mt-0.5"
          >
            {{ option.description }}
          </span>
        </span>
      </span>
    </button>

    <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
      {{ selectedCount }} / {{ maxSelections }} selectionne(s)
      <span v-if="minSelections > 1"> — minimum {{ minSelections }}</span>
    </p>

    <JustificationField
      v-if="requiresJustification"
      v-model="justification"
      :prompt="justificationPrompt"
      :required="true"
      :disabled="disabled || submitted"
    />

    <button
      type="button"
      :disabled="!canSubmit"
      class="mt-3 w-full sm:w-auto px-4 py-2 rounded-lg bg-brand-blue text-white text-sm font-medium hover:bg-brand-blue/90 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 dark:focus:ring-offset-dark-card"
      @click="submit"
    >
      Valider ma selection
    </button>
  </div>
</template>
