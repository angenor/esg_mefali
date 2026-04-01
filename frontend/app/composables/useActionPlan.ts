import { ref, onUnmounted } from 'vue'
import type { ActionPlan, ActionItem, ActionItemsListResponse, Reminder, ReminderType } from '~/types/actionPlan'
import { useAuthStore } from '~/stores/auth'
import { useActionPlanStore } from '~/stores/actionPlan'

export function useActionPlan() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const actionPlanStore = useActionPlanStore()
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

  /**
   * Générer un nouveau plan d'action via l'IA.
   * POST /api/action-plan/generate
   */
  async function generatePlan(timeframe: number): Promise<ActionPlan | null> {
    loading.value = true
    error.value = ''
    actionPlanStore.setLoading(true)
    actionPlanStore.setError(null)

    try {
      const response = await fetch(`${apiBase}/action-plan/generate`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ timeframe }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        const message = data.detail || `Erreur ${response.status} lors de la génération du plan`
        throw new Error(message)
      }

      const plan: ActionPlan = await response.json()
      actionPlanStore.setPlan(plan)
      return plan
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Erreur inconnue'
      error.value = message
      actionPlanStore.setError(message)
      return null
    } finally {
      loading.value = false
      actionPlanStore.setLoading(false)
    }
  }

  /**
   * Récupérer le plan d'action actif de l'utilisateur.
   * GET /api/action-plan/
   */
  async function fetchPlan(): Promise<ActionPlan | null> {
    loading.value = true
    error.value = ''
    actionPlanStore.setLoading(true)
    actionPlanStore.setError(null)

    try {
      const response = await fetch(`${apiBase}/action-plan/`, {
        headers: getHeaders(),
      })

      if (response.status === 404) {
        actionPlanStore.setPlan(null)
        return null
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erreur lors du chargement du plan')
      }

      const plan: ActionPlan = await response.json()
      actionPlanStore.setPlan(plan)
      return plan
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Erreur inconnue'
      error.value = message
      actionPlanStore.setError(message)
      return null
    } finally {
      loading.value = false
      actionPlanStore.setLoading(false)
    }
  }

  /**
   * Récupérer les actions d'un plan avec filtres optionnels.
   * GET /api/action-plan/{planId}/items
   */
  async function fetchItems(
    planId: string,
    options: {
      category?: string
      status?: string
      page?: number
      limit?: number
    } = {}
  ): Promise<ActionItemsListResponse | null> {
    loading.value = true
    error.value = ''
    actionPlanStore.setLoading(true)

    try {
      const params = new URLSearchParams()
      if (options.category) params.set('category', options.category)
      if (options.status) params.set('status', options.status)
      if (options.page) params.set('page', String(options.page))
      if (options.limit) params.set('limit', String(options.limit))

      const url = `${apiBase}/action-plan/${planId}/items${params.toString() ? `?${params}` : ''}`
      const response = await fetch(url, { headers: getHeaders() })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Erreur lors du chargement des actions')
      }

      const data: ActionItemsListResponse = await response.json()
      actionPlanStore.setItems(data.items, data.total)

      // Construire le progress au format store
      if (data.progress) {
        actionPlanStore.setProgress(data.progress as any)
      }

      return data
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Erreur inconnue'
      error.value = message
      actionPlanStore.setError(message)
      return null
    } finally {
      loading.value = false
      actionPlanStore.setLoading(false)
    }
  }

  /**
   * Mettre à jour une action (statut, progression, date).
   * PATCH /api/action-plan/items/{itemId}
   */
  async function updateItem(
    itemId: string,
    updates: {
      status?: string
      completion_percentage?: number
      due_date?: string
    }
  ): Promise<ActionItem | null> {
    loading.value = true
    error.value = ''

    try {
      const response = await fetch(`${apiBase}/action-plan/items/${itemId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(updates),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        const message = data.detail || `Erreur ${response.status} lors de la mise à jour`
        throw new Error(message)
      }

      const updatedItem: ActionItem = await response.json()
      actionPlanStore.updateItem(updatedItem)
      return updatedItem
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Erreur inconnue'
      error.value = message
      actionPlanStore.setError(message)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Créer un rappel.
   * POST /api/action-plan/reminders/
   */
  async function createReminder(data: {
    action_item_id: string | null
    type: ReminderType
    message: string
    scheduled_at: string
  }): Promise<Reminder | null> {
    loading.value = true
    error.value = ''

    try {
      const response = await fetch(`${apiBase}/action-plan/reminders/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const respData = await response.json().catch(() => ({}))
        throw new Error(respData.detail || 'Erreur lors de la création du rappel')
      }

      return await response.json()
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Erreur inconnue'
      error.value = message
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Récupérer les rappels à venir.
   * GET /api/action-plan/reminders/upcoming
   */
  async function fetchUpcomingReminders(limit: number = 10): Promise<Reminder[]> {
    try {
      const response = await fetch(`${apiBase}/action-plan/reminders/upcoming?limit=${limit}`, {
        headers: getHeaders(),
      })

      if (!response.ok) return []

      const data = await response.json()
      return data.items || []
    } catch {
      return []
    }
  }

  // Polling des rappels échus (toutes les 60s)
  let reminderPollingInterval: ReturnType<typeof setInterval> | null = null

  function startReminderPolling(onDueReminder: (reminder: Reminder) => void) {
    if (reminderPollingInterval) return

    reminderPollingInterval = setInterval(async () => {
      const reminders = await fetchUpcomingReminders(5)
      const now = new Date()
      for (const reminder of reminders) {
        if (new Date(reminder.scheduled_at) <= now) {
          onDueReminder(reminder)
        }
      }
    }, 60_000)
  }

  function stopReminderPolling() {
    if (reminderPollingInterval) {
      clearInterval(reminderPollingInterval)
      reminderPollingInterval = null
    }
  }

  return {
    loading,
    error,
    generatePlan,
    fetchPlan,
    fetchItems,
    updateItem,
    createReminder,
    fetchUpcomingReminders,
    startReminderPolling,
    stopReminderPolling,
  }
}
