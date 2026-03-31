import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useCreditScoreStore } from '~/stores/creditScore'
import type { CreditScoreData, ScoreBreakdown, ScoreHistoryItem } from '~/stores/creditScore'

export function useCreditScore() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const store = useCreditScoreStore()
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

  async function generateScore(): Promise<CreditScoreData | null> {
    loading.value = true
    error.value = ''
    store.setGenerating(true)
    try {
      const response = await fetch(`${apiBase}/credit/generate`, {
        method: 'POST',
        headers: getHeaders(),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors de la generation du score')
      }
      const result: CreditScoreData = await response.json()
      store.setScore(result)
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      store.setError(error.value)
      return null
    } finally {
      loading.value = false
      store.setGenerating(false)
    }
  }

  async function fetchScore(): Promise<CreditScoreData | null> {
    loading.value = true
    error.value = ''
    store.setLoading(true)
    try {
      const response = await fetch(`${apiBase}/credit/score`, {
        headers: getHeaders(),
      })
      if (response.status === 404) {
        store.setScore(null)
        return null
      }
      if (!response.ok) throw new Error('Erreur lors du chargement du score')

      const data: CreditScoreData = await response.json()
      store.setScore(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      store.setError(error.value)
      return null
    } finally {
      loading.value = false
      store.setLoading(false)
    }
  }

  async function fetchBreakdown(): Promise<ScoreBreakdown | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/credit/score/breakdown`, {
        headers: getHeaders(),
      })
      if (response.status === 404) return null
      if (!response.ok) throw new Error('Erreur lors du chargement du detail')

      const data: ScoreBreakdown = await response.json()
      store.setBreakdown(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchHistory(limit = 10, offset = 0): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      })
      const response = await fetch(`${apiBase}/credit/score/history?${params}`, {
        headers: getHeaders(),
      })
      if (!response.ok) throw new Error('Erreur lors du chargement de l\'historique')

      const data: { scores: ScoreHistoryItem[]; total: number } = await response.json()
      store.setHistory(data.scores, data.total)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
    } finally {
      loading.value = false
    }
  }

  async function downloadCertificate(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/credit/score/certificate`, {
        headers: {
          ...(authStore.accessToken
            ? { Authorization: `Bearer ${authStore.accessToken}` }
            : {}),
        },
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Erreur lors du telechargement')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `attestation_credit_vert_v${store.score?.version ?? 1}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    generateScore,
    fetchScore,
    fetchBreakdown,
    fetchHistory,
    downloadCertificate,
  }
}
