import { ref } from 'vue'
import type {
  CarbonAssessment,
  CarbonAssessmentList,
  CarbonSummary,
  BenchmarkResponse,
  AddEntriesRequest,
  AddEntriesResponse,
} from '~/types/carbon'
import { useAuthStore } from '~/stores/auth'
import { useCarbonStore } from '~/stores/carbon'

export function useCarbon() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const carbonStore = useCarbonStore()
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

  async function createAssessment(year: number, conversationId?: string): Promise<CarbonAssessment | null> {
    loading.value = true
    error.value = ''
    try {
      const body: Record<string, unknown> = { year }
      if (conversationId) body.conversation_id = conversationId

      const response = await fetch(`${apiBase}/carbon/assessments`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de la creation')
      }
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAssessments(status?: string, page = 1, limit = 10): Promise<void> {
    loading.value = true
    error.value = ''
    carbonStore.setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) })
      if (status) params.set('status', status)

      const response = await fetch(`${apiBase}/carbon/assessments?${params}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Erreur lors du chargement')

      const data: CarbonAssessmentList = await response.json()
      carbonStore.setAssessments(data.items, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      carbonStore.setError(error.value)
    } finally {
      loading.value = false
      carbonStore.setLoading(false)
    }
  }

  async function fetchAssessment(id: string): Promise<CarbonAssessment | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/carbon/assessments/${id}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Bilan non trouve')

      const data: CarbonAssessment = await response.json()
      carbonStore.setCurrentAssessment(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(id: string): Promise<CarbonSummary | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/carbon/assessments/${id}/summary`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Resume non disponible')

      const data: CarbonSummary = await response.json()
      carbonStore.setCurrentSummary(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchBenchmark(sector: string): Promise<BenchmarkResponse | null> {
    try {
      const response = await fetch(`${apiBase}/carbon/benchmarks/${sector}`, {
        headers: getHeaders(),
      })
      if (!response.ok) return null
      return await response.json()
    } catch {
      return null
    }
  }

  async function addEntries(assessmentId: string, request: AddEntriesRequest): Promise<AddEntriesResponse | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/carbon/assessments/${assessmentId}/entries`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(request),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de l\'ajout')
      }
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
    createAssessment,
    fetchAssessments,
    fetchAssessment,
    fetchSummary,
    fetchBenchmark,
    addEntries,
  }
}
