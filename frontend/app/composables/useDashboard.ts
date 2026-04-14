import { useDashboardStore } from '~/stores/dashboard'
import { useAuth, SessionExpiredError } from '~/composables/useAuth'
import type { DashboardSummary } from '~/types/dashboard'

export function useDashboard() {
  const store = useDashboardStore()
  const { apiFetch, handleAuthFailure } = useAuth()

  async function fetchSummary(): Promise<DashboardSummary | null> {
    store.setLoading(true)
    store.setError('')
    try {
      const data = await apiFetch<DashboardSummary>('/dashboard/summary')
      store.setSummary(data)
      return data
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return null
      }
      const msg = e instanceof Error ? e.message : 'Erreur lors du chargement du tableau de bord'
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
