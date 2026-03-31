<script setup lang="ts">
import type { Document } from '~/types/documents'
import { useDocuments } from '~/composables/useDocuments'

definePageMeta({
  layout: 'default',
})

const { store, fetchDocuments, uploadDocuments, fetchDocumentDetail, deleteDocument, reanalyze } = useDocuments()

const selectedDocument = ref<Document | null>(null)
const showPreview = ref(false)

onMounted(() => {
  fetchDocuments()
})

async function handleUpload(files: File[]) {
  await uploadDocuments(files)
}

async function handleSelect(doc: Document) {
  selectedDocument.value = doc
  showPreview.value = false
  await fetchDocumentDetail(doc.id)
}

async function handleDelete(id: string) {
  await deleteDocument(id)
}

async function handleReanalyze(id: string) {
  await reanalyze(id)
  // Rafraichir le detail
  await fetchDocumentDetail(id)
}

function handleCloseDetail() {
  selectedDocument.value = null
  store.setCurrentDocument(null)
}

function togglePreview() {
  showPreview.value = !showPreview.value
}
</script>

<template>
  <div class="flex flex-col h-full bg-surface-bg dark:bg-surface-dark-bg">
    <!-- Header -->
    <div class="border-b border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card px-6 py-4">
      <h1 class="text-lg font-bold text-surface-text dark:text-surface-dark-text">
        Documents
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Uploadez et analysez vos documents d'entreprise
      </p>
    </div>

    <div class="flex-1 overflow-hidden flex">
      <!-- Panneau gauche : Upload + Liste -->
      <div
        class="flex-1 overflow-y-auto p-6 space-y-6"
        :class="store.currentDocument ? 'w-1/2' : 'w-full'"
      >
        <!-- Zone d'upload -->
        <DocumentUpload
          :is-uploading="store.isUploading"
          @upload="handleUpload"
        />

        <!-- Erreur -->
        <div v-if="store.error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2">
          {{ store.error }}
        </div>

        <!-- Liste des documents -->
        <DocumentList
          :documents="store.documents"
          :is-loading="store.isLoading"
          @select="handleSelect"
          @delete="handleDelete"
        />

        <!-- Pagination -->
        <div v-if="store.total > store.limit" class="flex justify-center gap-2">
          <button
            :disabled="store.page <= 1"
            class="px-3 py-1.5 text-sm border border-gray-300 dark:border-dark-border rounded-lg disabled:opacity-50 text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover"
            @click="fetchDocuments({ page: store.page - 1 })"
          >
            Precedent
          </button>
          <span class="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400">
            {{ store.page }} / {{ Math.ceil(store.total / store.limit) }}
          </span>
          <button
            :disabled="store.page >= Math.ceil(store.total / store.limit)"
            class="px-3 py-1.5 text-sm border border-gray-300 dark:border-dark-border rounded-lg disabled:opacity-50 text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover"
            @click="fetchDocuments({ page: store.page + 1 })"
          >
            Suivant
          </button>
        </div>
      </div>

      <!-- Panneau droit : Detail du document -->
      <div
        v-if="store.currentDocument"
        class="w-1/2 border-l border-gray-200 dark:border-dark-border overflow-y-auto p-6 space-y-4"
      >
        <!-- Bouton previsualisation -->
        <div
          v-if="store.currentDocument.mime_type === 'application/pdf' || store.currentDocument.mime_type.startsWith('image/')"
          class="flex justify-end"
        >
          <button
            class="text-xs px-3 py-1 border border-gray-300 dark:border-dark-border rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-hover"
            @click="togglePreview"
          >
            {{ showPreview ? 'Masquer' : 'Previsualiser' }}
          </button>
        </div>

        <!-- Previsualisation -->
        <DocumentPreview
          v-if="showPreview"
          :document-id="store.currentDocument.id"
          :mime-type="store.currentDocument.mime_type"
          :filename="store.currentDocument.original_filename"
          @close="showPreview = false"
        />

        <!-- Detail -->
        <DocumentDetail
          :document="store.currentDocument"
          @close="handleCloseDetail"
          @reanalyze="handleReanalyze"
        />
      </div>
    </div>
  </div>
</template>
