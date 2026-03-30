<script setup lang="ts">
const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
}>()

const content = ref('')
const MAX_LENGTH = 5000

const isValid = computed(() => {
  const trimmed = content.value.trim()
  return trimmed.length >= 1 && trimmed.length <= MAX_LENGTH
})

const charCount = computed(() => content.value.length)

function handleSubmit() {
  if (!isValid.value || props.disabled) return
  emit('send', content.value.trim())
  content.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}
</script>

<template>
  <div class="border-t border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-3">
    <div class="flex gap-2 items-end">
      <textarea
        v-model="content"
        :disabled="disabled"
        :maxlength="MAX_LENGTH"
        rows="1"
        class="flex-1 resize-none rounded-xl border border-gray-300 dark:border-dark-border dark:bg-dark-input dark:text-surface-dark-text px-3 py-2 text-sm focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        placeholder="Ecrivez votre message..."
        @keydown="handleKeydown"
      />
      <button
        :disabled="!isValid || disabled"
        class="shrink-0 w-9 h-9 rounded-full bg-brand-green text-white flex items-center justify-center hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        @click="handleSubmit"
      >
        <!-- Spinner pendant le streaming -->
        <div
          v-if="disabled"
          class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
        />
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
        </svg>
      </button>
    </div>
    <div v-if="charCount > MAX_LENGTH * 0.8" class="text-xs text-gray-400 mt-1 text-right">
      {{ charCount }}/{{ MAX_LENGTH }}
    </div>
  </div>
</template>
