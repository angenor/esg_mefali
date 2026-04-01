import { useAuthStore } from '~/stores/auth'
import { useDashboardStore } from '~/stores/dashboard'
import type { DashboardSummary } from '~/types/dashboard'

export function useDashboard() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const store = useDashboardStore()
  const apiBase = config.public.apiBase

  function getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      ...(authStore.accessToken
        ? { Authorization: `Bearer ${authStore.accessToken}` }
        : {}),
    }
  }

  async function fetchSummary(): Promise<DashboardSummary | null> {
    store.setLoading(true)
    store.setError('')
    try {
      const response = await fetch(`${apiBase}/dashboard/summary`, {
        headers: getHeaders(),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erreur lors du chargement du tableau de bord')
      }
      const data: DashboardSummary = await response.json()
      store.setSummary(data)
      return data
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erreur inconnue'
      store.setError(msg)
      return null
    } finally {
      store.setLoading(false)
    }
  }

  return {
    store,
    fetchSummary,
  }
}
