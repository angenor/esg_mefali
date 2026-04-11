<script setup lang="ts">
import { computed, ref } from 'vue'
import type { InteractiveOption } from '~/types/interactive-question'
import JustificationField from './JustificationField.vue'

interface Props {
  options: InteractiveOption[]
  disabled?: boolean
  requiresJustification?: boolean
  justificationPrompt?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  requiresJustification: false,
  justificationPrompt: null,
})

const emit = defineEmits<{
  (e: 'submit', payload: { values: string[]; justification?: string }): void
}>()

const selected = ref<string | null>(null)
const justification = ref('')
const submitted = ref(false)

const canSubmit = computed(() => {
  if (selected.value === null) return false
  if (props.requiresJustification && justification.value.trim().length === 0) {
    return false
  }
  return !props.disabled && !submitted.value
})

function onSelect(optionId: string) {
  if (props.disabled || submitted.value) return
  selected.value = optionId
  // Pour QCU sans justification : submit immediat
  if (!props.requiresJustification) {
    submit()
  }
}

function submit() {
  if (!canSubmit.value) return
  submitted.value = true
  emit('submit', {
    values: [selected.value!],
    justification: props.requiresJustification ? justification.value : undefined,
  })
}
</script>

<template>
  <div
    role="radiogroup"
    aria-labelledby="single-choice-label"
    class="space-y-2"
  >
    <button
      v-for="option in options"
      :key="option.id"
      type="button"
      role="radio"
      :aria-checked="selected === option.id"
      :disabled="disabled || submitted"
      :class="[
        'w-full text-left px-4 py-3 rounded-lg border transition-all',
        'focus:outline-none focus:ring-2 focus:ring-brand-blue',
        selected === option.id
          ? 'border-brand-blue bg-brand-blue/10 dark:bg-brand-blue/20 text-surface-text dark:text-surface-dark-text'
          : 'border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover',
        (disabled || submitted) && 'opacity-50 cursor-not-allowed',
      ]"
      @click="onSelect(option.id)"
    >
      <span class="flex items-start gap-3">
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

    <JustificationField
      v-if="requiresJustification"
      v-model="justification"
      :prompt="justificationPrompt"
      :required="true"
      :disabled="disabled || submitted"
    />

    <button
      v-if="requiresJustification"
      type="button"
      :disabled="!canSubmit"
      class="mt-3 w-full sm:w-auto px-4 py-2 rounded-lg bg-brand-blue text-white text-sm font-medium hover:bg-brand-blue/90 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 dark:focus:ring-offset-dark-card"
      @click="submit"
    >
      Valider ma reponse
    </button>
  </div>
</template>
