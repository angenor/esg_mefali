import { defineStore } from 'pinia'
import type { Document, DocumentDetail, DocumentStatus } from '~/types/documents'

interface DocumentsState {
  documents: Document[]
  currentDocument: DocumentDetail | null
  total: number
  page: number
  limit: number
  isLoading: boolean
  isUploading: boolean
  uploadProgress: Map<string, DocumentStatus>
  error: string
}

export const useDocumentsStore = defineStore('documents', {
  state: (): DocumentsState => ({
    documents: [],
    currentDocument: null,
    total: 0,
    page: 1,
    limit: 20,
    isLoading: false,
    isUploading: false,
    uploadProgress: new Map(),
    error: '',
  }),

  getters: {
    hasDocuments: (state): boolean => state.documents.length > 0,
    analyzedCount: (state): number =>
      state.documents.filter(d => d.status === 'analyzed').length,
  },

  actions: {
    setDocuments(documents: Document[], total: number, page: number, limit: number) {
      this.documents = documents
      this.total = total
      this.page = page
      this.limit = limit
    },

    setCurrentDocument(doc: DocumentDetail | null) {
      this.currentDocument = doc
    },

    removeDocument(id: string) {
      this.documents = this.documents.filter(d => d.id !== id)
      if (this.currentDocument?.id === id) {
        this.currentDocument = null
      }
      this.total = Math.max(0, this.total - 1)
    },

    updateDocumentStatus(id: string, status: DocumentStatus) {
      this.documents = this.documents.map(d =>
        d.id === id ? { ...d, status } : d,
      )
      this.uploadProgress.set(id, status)
    },

    setError(error: string) {
      this.error = error
    },

    clearError() {
      this.error = ''
    },
  },
})
