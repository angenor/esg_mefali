<script setup lang="ts">
const props = defineProps<{
  documentId: string
  mimeType: string
  filename: string
}>()

const emit = defineEmits<{
  close: []
}>()

const config = useRuntimeConfig()
const authStore = useAuthStore()
const apiBase = config.public.apiBase

const previewUrl = computed(() =>
  `${apiBase}/documents/${props.documentId}/preview`,
)

const isPdf = computed(() => props.mimeType === 'application/pdf')
const isImage = computed(() => props.mimeType.startsWith('image/'))
const canPreview = computed(() => isPdf.value || isImage.value)

const imageUrl = ref<string>('')
const isLoading = ref(true)
const error = ref('')

async function loadPreview() {
  if (!canPreview.value) return

  isLoading.value = true
  error.value = ''

  try {
    const response = await fetch(previewUrl.value, {
      headers: {
        Authorization: `Bearer ${authStore.accessToken}`,
      },
    })

    if (!response.ok) throw new Error('Impossible de charger la previsualisation')

    if (isImage.value) {
      const blob = await response.blob()
      imageUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Erreur inconnue'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadPreview()
})

onUnmounted(() => {
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value)
  }
})
</script>

<template>
  <div class="bg-white dark:bg-dark-card rounded-xl border border-gray-200 dark:border-dark-border overflow-hidden">
    <div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-dark-border">
      <p class="text-sm font-medium text-surface-text dark:text-surface-dark-text truncate">
        {{ filename }}
      </p>
      <button
        class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        @click="emit('close')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <div class="p-4">
      <!-- Loading -->
      <div v-if="isLoading" class="flex justify-center py-12">
        <div class="w-8 h-8 border-3 border-brand-green border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Erreur -->
      <div v-else-if="error" class="text-center py-8 text-red-500 text-sm">
        {{ error }}
      </div>

      <!-- Pas de previsualisation -->
      <div v-else-if="!canPreview" class="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
        Previsualisation non disponible pour ce type de fichier
      </div>

      <!-- PDF -->
      <iframe
        v-else-if="isPdf"
        :src="`${previewUrl}#toolbar=0`"
        class="w-full h-96 rounded-lg border border-gray-200 dark:border-dark-border"
      />

      <!-- Image -->
      <img
        v-else-if="isImage && imageUrl"
        :src="imageUrl"
        :alt="filename"
        class="max-w-full max-h-96 mx-auto rounded-lg"
      >
    </div>
  </div>
</template>
