import { ref } from 'vue'
import type {
  CarbonAssessment,
  CarbonAssessmentList,
  CarbonSummary,
  BenchmarkResponse,
  AddEntriesRequest,
  AddEntriesResponse,
} from '~/types/carbon'
import { useCarbonStore } from '~/stores/carbon'
import { useAuth, SessionExpiredError } from '~/composables/useAuth'

export function useCarbon() {
  const carbonStore = useCarbonStore()
  const { apiFetch, handleAuthFailure } = useAuth()

  const loading = ref(false)
  const error = ref('')

  // Skip error.value sur SessionExpiredError pour eviter un flash d'erreur
  // juste avant la redirection vers /login (UX NFR9).
  async function handleError(e: unknown, fallback: string): Promise<void> {
    if (e instanceof SessionExpiredError) {
      await handleAuthFailure()
      return
    }
    error.value = e instanceof Error ? e.message : fallback
  }

  async function createAssessment(year: number, conversationId?: string): Promise<CarbonAssessment | null> {
    loading.value = true
    error.value = ''
    try {
      const body: Record<string, unknown> = { year }
      if (conversationId) body.conversation_id = conversationId
      return await apiFetch<CarbonAssessment>('/carbon/assessments', {
        method: 'POST',
        body: JSON.stringify(body),
      })
    } catch (e) {
      await handleError(e, 'Erreur lors de la creation')
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
      const data = await apiFetch<CarbonAssessmentList>(`/carbon/assessments?${params}`)
      carbonStore.setAssessments(data.items, data.total)
    } catch (e) {
      await handleError(e, 'Erreur lors du chargement')
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
      const data = await apiFetch<CarbonAssessment>(`/carbon/assessments/${id}`)
      carbonStore.setCurrentAssessment(data)
      return data
    } catch (e) {
      await handleError(e, 'Bilan non trouve')
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(id: string): Promise<CarbonSummary | null> {
    loading.value = true
    error.value = ''
    try {
      const data = await apiFetch<CarbonSummary>(`/carbon/assessments/${id}/summary`)
      carbonStore.setCurrentSummary(data)
      return data
    } catch (e) {
      await handleError(e, 'Resume non disponible')
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchBenchmark(sector: string): Promise<BenchmarkResponse | null> {
    try {
      return await apiFetch<BenchmarkResponse>(`/carbon/benchmarks/${sector}`)
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
      }
      return null
    }
  }

  async function addEntries(assessmentId: string, request: AddEntriesRequest): Promise<AddEntriesResponse | null> {
    loading.value = true
    error.value = ''
    try {
      return await apiFetch<AddEntriesResponse>(`/carbon/assessments/${assessmentId}/entries`, {
        method: 'POST',
        body: JSON.stringify(request),
      })
    } catch (e) {
      await handleError(e, "Erreur lors de l'ajout")
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
