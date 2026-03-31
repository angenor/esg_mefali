import { ref } from 'vue'
import type {
  ReportGenerateResponse,
  ReportStatusResponse,
  ReportListResponse,
} from '~/types/report'
import { useAuthStore } from '~/stores/auth'

export function useReports() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const apiBase = config.public.apiBase

  const loading = ref(false)
  const error = ref('')

  function getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      ...(authStore.accessToken
        ? { Authorization: `Bearer ${authStore.accessToken}` }
        : {}),
    }
  }

  async function generateReport(assessmentId: string): Promise<ReportGenerateResponse | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/reports/esg/${assessmentId}/generate`, {
        method: 'POST',
        headers: getHeaders(),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de la generation du rapport')
      }
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function pollStatus(reportId: string): Promise<ReportStatusResponse | null> {
    try {
      const response = await fetch(`${apiBase}/reports/${reportId}/status`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Erreur lors de la verification du statut')
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    }
  }

  function downloadReport(reportId: string): void {
    const token = authStore.accessToken
    const url = `${apiBase}/reports/${reportId}/download`
    const link = document.createElement('a')
    link.href = `${url}?token=${encodeURIComponent(token || '')}`
    link.click()
  }

  async function listReports(
    page = 1,
    limit = 20,
    assessmentId?: string,
  ): Promise<ReportListResponse | null> {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams({
        page: String(page),
        limit: String(limit),
      })
      if (assessmentId) params.set('assessment_id', assessmentId)

      const response = await fetch(`${apiBase}/reports/?${params}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Erreur lors du chargement des rapports')
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    generateReport,
    pollStatus,
    downloadReport,
    listReports,
  }
}
