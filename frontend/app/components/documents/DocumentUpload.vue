<script setup lang="ts">
const emit = defineEmits<{
  upload: [files: File[]]
}>()

const props = defineProps<{
  isUploading?: boolean
}>()

const isDragOver = ref(false)
const fileInput = ref<HTMLInputElement>()

const ACCEPTED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]
const MAX_SIZE = 10 * 1024 * 1024
const MAX_FILES = 5

const error = ref('')

function validateFiles(files: File[]): boolean {
  error.value = ''

  if (files.length > MAX_FILES) {
    error.value = `Maximum ${MAX_FILES} fichiers par upload`
    return false
  }

  for (const file of files) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      error.value = `Type non accepte : ${file.name}. Types autorises : PDF, PNG, JPG, DOCX, XLSX`
      return false
    }
    if (file.size > MAX_SIZE) {
      error.value = `${file.name} depasse la taille maximale (10 MB)`
      return false
    }
  }

  return true
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length > 0 && validateFiles(files)) {
    emit('upload', files)
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length > 0 && validateFiles(files)) {
    emit('upload', files)
  }
  // Reset input
  if (fileInput.value) fileInput.value.value = ''
}

function openFilePicker() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer"
    :class="[
      isDragOver
        ? 'border-brand-green bg-emerald-50 dark:bg-emerald-900/20'
        : 'border-gray-300 dark:border-dark-border hover:border-brand-green',
      isUploading ? 'opacity-50 pointer-events-none' : '',
    ]"
    @dragover.prevent="isDragOver = true"
    @dragleave="isDragOver = false"
    @drop.prevent="handleDrop"
    @click="openFilePicker"
  >
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      :accept="ACCEPTED_TYPES.join(',')"
      multiple
      @change="handleFileSelect"
    >

    <!-- Icone upload -->
    <div class="flex justify-center mb-3">
      <div
        v-if="isUploading"
        class="w-10 h-10 border-3 border-brand-green border-t-transparent rounded-full animate-spin"
      />
      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        class="w-10 h-10 text-gray-400 dark:text-gray-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    </div>

    <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
      {{ isUploading ? 'Upload en cours...' : 'Glissez vos fichiers ici ou cliquez pour parcourir' }}
    </p>
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
      PDF, PNG, JPG, DOCX, XLSX — Max 10 MB — {{ MAX_FILES }} fichiers max
    </p>

    <!-- Erreur -->
    <p v-if="error" class="text-xs text-red-500 mt-2">
      {{ error }}
    </p>
  </div>
</template>
