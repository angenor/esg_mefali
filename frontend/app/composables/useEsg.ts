import { ref } from 'vue'
import type {
  ESGAssessment,
  ESGAssessmentList,
  ScoreResponse,
  BenchmarkResponse,
} from '~/types/esg'
import { useAuthStore } from '~/stores/auth'
import { useEsgStore } from '~/stores/esg'

export function useEsg() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const esgStore = useEsgStore()
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

  async function createAssessment(conversationId?: string): Promise<ESGAssessment | null> {
    loading.value = true
    error.value = ''
    try {
      const body = conversationId ? { conversation_id: conversationId } : undefined
      const response = await fetch(`${apiBase}/esg/assessments`, {
        method: 'POST',
        headers: getHeaders(),
        body: body ? JSON.stringify(body) : undefined,
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de la creation')
      }
      const data: ESGAssessment = await response.json()
      return data
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
    esgStore.setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), limit: String(limit) })
      if (status) params.set('status', status)

      const response = await fetch(`${apiBase}/esg/assessments?${params}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Erreur lors du chargement')

      const data: ESGAssessmentList = await response.json()
      esgStore.setAssessments(data.data, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      esgStore.setError(error.value)
    } finally {
      loading.value = false
      esgStore.setLoading(false)
    }
  }

  async function fetchAssessment(id: string): Promise<ESGAssessment | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/esg/assessments/${id}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Evaluation non trouvee')

      const data: ESGAssessment = await response.json()
      esgStore.setCurrentAssessment(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchScore(id: string): Promise<ScoreResponse | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/esg/assessments/${id}/score`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Score non disponible')

      const data: ScoreResponse = await response.json()
      esgStore.setCurrentScore(data)
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
      const response = await fetch(`${apiBase}/esg/benchmarks/${sector}`, {
        headers: getHeaders(),
      })
      if (!response.ok) return null
      return await response.json()
    } catch {
      return null
    }
  }

  return {
    loading,
    error,
    createAssessment,
    fetchAssessments,
    fetchAssessment,
    fetchScore,
    fetchBenchmark,
  }
}
