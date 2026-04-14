import { ref } from 'vue'
import { useFinancingStore } from '~/stores/financing'
import { useAuth, ApiFetchError, SessionExpiredError } from '~/composables/useAuth'
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
  const financingStore = useFinancingStore()
  const { apiFetch, apiFetchBlob, handleAuthFailure } = useAuth()

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

  // --- Matches / Recommandations ---

  async function fetchMatches(): Promise<void> {
    loading.value = true
    financingStore.setLoading(true)
    financingStore.setError(null)
    try {
      const data = await apiFetch<MatchListResponse>('/financing/matches')
      financingStore.setMatches(data.items, data.total)
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return
      }
      // 428 Precondition Required : signal metier « evaluation ESG requise »,
      // pas une erreur technique — conserve le comportement historique.
      if (e instanceof ApiFetchError && e.status === 428) {
        const detail = (e.body as { detail?: { message?: string } })?.detail
        financingStore.setError(detail?.message || 'Evaluation ESG requise')
        return
      }
      const msg = e instanceof Error ? e.message : 'Erreur lors du chargement des recommandations'
      error.value = msg
      financingStore.setError(msg)
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function fetchMatchDetail(fundId: string): Promise<FundMatch | null> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const data = await apiFetch<FundMatch>(`/financing/matches/${fundId}`)
      financingStore.setCurrentMatch(data)
      return data
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return null
      }
      const msg = e instanceof Error ? e.message : 'Erreur lors du chargement du match'
      error.value = msg
      financingStore.setError(msg)
      return null
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  async function updateMatchStatus(matchId: string, status: string): Promise<FundMatchSummary | null> {
    try {
      return await apiFetch<FundMatchSummary>(`/financing/matches/${matchId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
    } catch (e) {
      await handleError(e, 'Erreur de mise a jour')
      return null
    }
  }

  async function updateMatchIntermediary(matchId: string, intermediaryId: string): Promise<FundMatchSummary | null> {
    try {
      return await apiFetch<FundMatchSummary>(`/financing/matches/${matchId}/intermediary`, {
        method: 'PATCH',
        body: JSON.stringify({ intermediary_id: intermediaryId }),
      })
    } catch (e) {
      await handleError(e, 'Erreur de mise a jour')
      return null
    }
  }

  // --- Fonds ---

  async function fetchFunds(params?: Record<string, string>): Promise<void> {
    loading.value = true
    financingStore.setLoading(true)
    try {
      const searchParams = new URLSearchParams(params || {})
      const data = await apiFetch<FundListResponse>(`/financing/funds?${searchParams}`)
      financingStore.setFunds(data.items, data.total)
    } catch (e) {
      await handleError(e, 'Erreur lors du chargement des fonds')
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
      const data = await apiFetch<Fund>(`/financing/funds/${fundId}`)
      financingStore.setCurrentFund(data)
      return data
    } catch (e) {
      await handleError(e, 'Erreur lors du chargement du fonds')
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
      const data = await apiFetch<IntermediaryListResponse>(
        `/financing/intermediaries?${searchParams}`,
      )
      financingStore.setIntermediaries(data.items, data.total)
    } catch (e) {
      await handleError(e, 'Erreur lors du chargement des intermediaires')
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
      const data = await apiFetch<Intermediary>(
        `/financing/intermediaries/${intermediaryId}`,
      )
      financingStore.setCurrentIntermediary(data)
      return data
    } catch (e) {
      await handleError(e, 'Erreur lors du chargement')
      return null
    } finally {
      loading.value = false
      financingStore.setLoading(false)
    }
  }

  // --- Fiche de preparation ---
  async function fetchPreparationSheet(matchId: string): Promise<Blob | null> {
    try {
      return await apiFetchBlob(`/financing/matches/${matchId}/preparation-sheet`)
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return null
      }
      error.value = e instanceof Error ? e.message : 'Erreur lors de la generation de la fiche'
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
