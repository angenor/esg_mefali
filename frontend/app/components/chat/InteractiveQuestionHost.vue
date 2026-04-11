<script setup lang="ts">
import { computed } from 'vue'
import type {
  InteractiveQuestion,
  InteractiveQuestionAnswer,
} from '~/types/interactive-question'
import SingleChoiceWidget from './SingleChoiceWidget.vue'
import MultipleChoiceWidget from './MultipleChoiceWidget.vue'
import AnswerElsewhereButton from './AnswerElsewhereButton.vue'

interface Props {
  question: InteractiveQuestion
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'answer', payload: InteractiveQuestionAnswer): void
  (e: 'abandoned'): void
}>()

const isQcu = computed(() =>
  props.question.question_type === 'qcu' ||
  props.question.question_type === 'qcu_justification',
)
const isQcm = computed(() =>
  props.question.question_type === 'qcm' ||
  props.question.question_type === 'qcm_justification',
)
const isPending = computed(() => props.question.state === 'pending')
const isExpired = computed(() => props.question.state === 'expired')
const isAnswered = computed(() => props.question.state === 'answered')
const isAbandoned = computed(() => props.question.state === 'abandoned')

function onSubmit(payload: InteractiveQuestionAnswer) {
  emit('answer', payload)
}
</script>

<template>
  <div
    class="my-3 p-4 rounded-xl border border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-card"
    :class="{ 'opacity-60': isExpired || isAbandoned }"
  >
    <p class="text-sm font-medium text-surface-text dark:text-surface-dark-text mb-3">
      {{ question.prompt }}
    </p>

    <SingleChoiceWidget
      v-if="isQcu"
      :options="question.options"
      :disabled="!isPending"
      :requires-justification="question.requires_justification"
      :justification-prompt="question.justification_prompt"
      @submit="onSubmit"
    />

    <MultipleChoiceWidget
      v-else-if="isQcm"
      :options="question.options"
      :min-selections="question.min_selections"
      :max-selections="question.max_selections"
      :disabled="!isPending"
      :requires-justification="question.requires_justification"
      :justification-prompt="question.justification_prompt"
      @submit="onSubmit"
    />

    <AnswerElsewhereButton
      v-if="isPending"
      :question-id="question.id"
      @abandoned="emit('abandoned')"
    />

    <p
      v-else-if="isExpired"
      class="text-xs italic text-gray-500 dark:text-gray-400 mt-2"
    >
      Cette question n'est plus active.
    </p>

    <p
      v-else-if="isAnswered && question.response_values?.length"
      class="text-xs text-gray-600 dark:text-gray-300 mt-2"
    >
      Reponse :
      {{ question.options.filter(o => question.response_values?.includes(o.id)).map(o => o.label).join(', ') }}
      <span v-if="question.response_justification" class="block italic mt-1">
        « {{ question.response_justification }} »
      </span>
    </p>

    <p
      v-else-if="isAbandoned"
      class="text-xs italic text-gray-500 dark:text-gray-400 mt-2"
    >
      Question contournee — vous avez repondu librement.
    </p>
  </div>
</template>
