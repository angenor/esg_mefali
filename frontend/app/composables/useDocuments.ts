import { useDocumentsStore } from '~/stores/documents'
import { useAuthStore } from '~/stores/auth'
import type {
  Document,
  DocumentDetail,
  DocumentListResponse,
  DocumentUploadResponse,
  ReanalyzeResponse,
} from '~/types/documents'

export function useDocuments() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const store = useDocumentsStore()
  const apiBase = config.public.apiBase

  function getHeaders(): Record<string, string> {
    return {
      ...(authStore.accessToken
        ? { Authorization: `Bearer ${authStore.accessToken}` }
        : {}),
    }
  }

  async function fetchDocuments(params?: {
    document_type?: string
    status?: string
    page?: number
    limit?: number
  }): Promise<void> {
    store.isLoading = true
    store.clearError()
    try {
      const query = new URLSearchParams()
      if (params?.document_type) query.set('document_type', params.document_type)
      if (params?.status) query.set('status', params.status)
      if (params?.page) query.set('page', String(params.page))
      if (params?.limit) query.set('limit', String(params.limit))

      const url = `${apiBase}/documents/${query.toString() ? `?${query}` : ''}`
      const response = await fetch(url, {
        headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      })

      if (!response.ok) throw new Error('Erreur lors du chargement des documents')

      const data: DocumentListResponse = await response.json()
      store.setDocuments(data.documents, data.total, data.page, data.limit)
    } catch (e) {
      store.setError(e instanceof Error ? e.message : 'Erreur inconnue')
    } finally {
      store.isLoading = false
    }
  }

  async function uploadDocuments(files: File[]): Promise<Document[]> {
    store.isUploading = true
    store.clearError()
    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }

      const response = await fetch(`${apiBase}/documents/upload`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Erreur lors de l\'upload')
      }

      const data: DocumentUploadResponse = await response.json()

      // Rafraichir la liste
      await fetchDocuments()

      return data.documents
    } catch (e) {
      store.setError(e instanceof Error ? e.message : 'Erreur inconnue')
      return []
    } finally {
      store.isUploading = false
    }
  }

  async function fetchDocumentDetail(id: string): Promise<DocumentDetail | null> {
    store.isLoading = true
    store.clearError()
    try {
      const response = await fetch(`${apiBase}/documents/${id}`, {
        headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      })

      if (!response.ok) throw new Error('Document non trouvé')

      const data: DocumentDetail = await response.json()
      store.setCurrentDocument(data)
      return data
    } catch (e) {
      store.setError(e instanceof Error ? e.message : 'Erreur inconnue')
      return null
    } finally {
      store.isLoading = false
    }
  }

  async function deleteDocument(id: string): Promise<boolean> {
    store.clearError()
    try {
      const response = await fetch(`${apiBase}/documents/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })

      if (!response.ok) throw new Error('Erreur lors de la suppression')

      store.removeDocument(id)
      return true
    } catch (e) {
      store.setError(e instanceof Error ? e.message : 'Erreur inconnue')
      return false
    }
  }

  async function reanalyze(id: string): Promise<boolean> {
    store.clearError()
    try {
      const response = await fetch(`${apiBase}/documents/${id}/reanalyze`, {
        method: 'POST',
        headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      })

      if (!response.ok) throw new Error('Erreur lors de la relance')

      const data: ReanalyzeResponse = await response.json()
      store.updateDocumentStatus(id, data.status)
      return true
    } catch (e) {
      store.setError(e instanceof Error ? e.message : 'Erreur inconnue')
      return false
    }
  }

  return {
    store,
    fetchDocuments,
    uploadDocuments,
    fetchDocumentDetail,
    deleteDocument,
    reanalyze,
  }
}
