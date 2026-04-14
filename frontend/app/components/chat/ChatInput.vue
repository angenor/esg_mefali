<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
  hint?: string | null
}>()

const emit = defineEmits<{
  send: [content: string]
  sendWithFile: [content: string, file: File]
}>()

const content = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const MAX_LENGTH = 5000

const ACCEPTED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
].join(',')

const isValid = computed(() => {
  const trimmed = content.value.trim()
  return (trimmed.length >= 1 && trimmed.length <= MAX_LENGTH) || selectedFile.value !== null
})

const charCount = computed(() => content.value.length)

function handleSubmit() {
  if (!isValid.value || props.disabled) return

  if (selectedFile.value) {
    emit('sendWithFile', content.value.trim(), selectedFile.value)
    selectedFile.value = null
  } else {
    emit('send', content.value.trim())
  }
  content.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    if (file.size > 10 * 1024 * 1024) {
      return
    }
    selectedFile.value = file
  }
  if (fileInput.value) fileInput.value.value = ''
}

function removeFile() {
  selectedFile.value = null
}
</script>

<template>
  <div class="border-t border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-3">
    <!-- Fichier selectionne -->
    <div v-if="selectedFile" class="flex items-center gap-2 mb-2 px-1">
      <div class="flex items-center gap-2 bg-gray-100 dark:bg-dark-hover rounded-lg px-3 py-1.5 text-xs text-surface-text dark:text-surface-dark-text">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-brand-green shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
        </svg>
        <span class="truncate max-w-48">{{ selectedFile.name }}</span>
        <button
          class="text-gray-400 hover:text-red-500 shrink-0"
          @click="removeFile"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <!-- FR33/NFR17 — hint affiche quand la connexion reseau est perdue -->
    <p
      v-if="hint"
      class="text-xs text-amber-700 dark:text-amber-400 mb-2 px-1"
      data-testid="chat-input-hint"
    >
      {{ hint }}
    </p>

    <div class="flex gap-2 items-end">
      <!-- Bouton trombone -->
      <button
        :disabled="disabled"
        class="shrink-0 w-9 h-9 rounded-full text-gray-400 dark:text-gray-500 hover:text-brand-green hover:bg-gray-100 dark:hover:bg-dark-hover flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Joindre un fichier"
        @click="openFilePicker"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z" clip-rule="evenodd" />
        </svg>
      </button>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        :accept="ACCEPTED_TYPES"
        @change="handleFileSelect"
      >

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
