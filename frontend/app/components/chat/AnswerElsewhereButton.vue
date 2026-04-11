<script setup lang="ts">
interface Props {
  questionId: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  (e: 'abandoned'): void
}>()

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

async function abandon() {
  if (props.disabled) return
  try {
    const authStore = useAuthStore()
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (authStore.accessToken) {
      headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    const response = await fetch(
      `${apiBase}/chat/interactive-questions/${props.questionId}/abandon`,
      {
        method: 'POST',
        headers,
        body: '{}',
      },
    )
    if (response.ok) {
      emit('abandoned')
    }
  } catch {
    // Best effort : si l'API echoue, on emet quand meme pour debloquer le user
    emit('abandoned')
  }
}
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    class="mt-2 text-xs text-gray-500 dark:text-gray-400 hover:text-brand-blue dark:hover:text-brand-blue underline disabled:opacity-50"
    @click="abandon"
  >
    Repondre autrement
  </button>
</template>
