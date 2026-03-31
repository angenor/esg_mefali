import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useFinancingStore } from '~/stores/financing'
import type {
  FundListResponse,
  Fund,
  FundMatch,
  MatchListResponse,
  IntermediaryListResponse,
  Intermediary,
  FundMatchSummary,
} from '~/types/financing'

export function useFinancing() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const financingStore = useFinancingStore()
  const apiBase = config.public.apiBase

  const loading = ref(false)
  const error = ref('')

  function getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      ...(authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : {}),
    }
  }

  // --- Matches / Recommandations ---

  async function fetchMatches(): Promise<void> {
    loading.value = true
    financingStore.setLoading(true)
    financingStore.setError(null)
    try {
      const response = await fetch(`${apiBase}/financing/matches`, { headers: getHeaders() })
      if (response.status === 428) {
        const data = await response.json()
        financingStore.setError(data.detail?.message || 'Evaluation ESG requise')
        return
      }
      if (!response.ok) throw new Error('Erreur lors du chargement des recommandations')
      const data: MatchListResponse = await response.json()
      financingStore.setMatches(data.items, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      financingStore.setError(error.value)
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function fetchMatchDetail(fundId: string): Promise<FundMatch | null> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const response = await fetch(`${apiBase}/financing/matches/${fundId}`, { headers: getHeaders() })
      if (!response.ok) throw new Error('Erreur lors du chargement du match')
      const data: FundMatch = await response.json()
      financingStore.setCurrentMatch(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      financingStore.setError(error.value)
      return null
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function updateMatchStatus(matchId: string, status: string): Promise<FundMatchSummary | null> {
    try {
      const response = await fetch(`${apiBase}/financing/matches/${matchId}/status`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Erreur de mise a jour')
      }
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    }
  }

  async function updateMatchIntermediary(matchId: string, intermediaryId: string): Promise<FundMatchSummary | null> {
    try {
      const response = await fetch(`${apiBase}/financing/matches/${matchId}/intermediary`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ intermediary_id: intermediaryId }),
      })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Erreur de mise a jour')
      }
      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    }
  }

  // --- Fonds ---

  async function fetchFunds(params?: Record<string, string>): Promise<void> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const searchParams = new URLSearchParams(params || {})
      const response = await fetch(`${apiBase}/financing/funds?${searchParams}`, { headers: getHeaders() })
      if (!response.ok) throw new Error('Erreur lors du chargement des fonds')
      const data: FundListResponse = await response.json()
      financingStore.setFunds(data.items, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      financingStore.setError(error.value)
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function fetchFundDetail(fundId: string): Promise<Fund | null> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const response = await fetch(`${apiBase}/financing/funds/${fundId}`, { headers: getHeaders() })
      if (!response.ok) throw new Error('Erreur lors du chargement du fonds')
      const data: Fund = await response.json()
      financingStore.setCurrentFund(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      financingStore.setError(error.value)
      return null
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  // --- Intermediaires ---

  async function fetchIntermediaries(params?: Record<string, string>): Promise<void> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const searchParams = new URLSearchParams(params || {})
      const response = await fetch(`${apiBase}/financing/intermediaries?${searchParams}`, { headers: getHeaders() })
      if (!response.ok) throw new Error('Erreur lors du chargement des intermediaires')
      const data: IntermediaryListResponse = await response.json()
      financingStore.setIntermediaries(data.items, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      financingStore.setError(error.value)
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function fetchIntermediaryDetail(intermediaryId: string): Promise<Intermediary | null> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const response = await fetch(`${apiBase}/financing/intermediaries/${intermediaryId}`, { headers: getHeaders() })
      if (!response.ok) throw new Error('Erreur lors du chargement')
      const data: Intermediary = await response.json()
      financingStore.setCurrentIntermediary(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  // --- Fiche de preparation ---

  async function fetchPreparationSheet(matchId: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${apiBase}/financing/matches/${matchId}/preparation-sheet`, {
        headers: { ...(authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : {}) },
      })
      if (!response.ok) throw new Error('Erreur lors de la generation de la fiche')
      return await response.blob()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    }
  }

  return {
    loading,
    error,
    fetchMatches,
    fetchMatchDetail,
    updateMatchStatus,
    updateMatchIntermediary,
    fetchFunds,
    fetchFundDetail,
    fetchIntermediaries,
    fetchIntermediaryDetail,
    fetchPreparationSheet,
  }
}
