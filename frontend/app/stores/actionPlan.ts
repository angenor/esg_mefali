import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ActionPlan,
  ActionItem,
  ActionItemCategory,
  ActionItemStatus,
  ProgressByCategory,
} from '~/types/actionPlan'

// Type de la progression retournée par l'API
export type PlanProgress = {
  global_percentage: number
  [key: string]: ProgressByCategory | number
}

export const useActionPlanStore = defineStore('actionPlan', () => {
  // --- État ---
  const plan = ref<ActionPlan | null>(null)
  const items = ref<ActionItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const progress = ref<PlanProgress | null>(null)

  // --- Calculés ---
  const hasPlan = computed(() => plan.value !== null)

  const completionPercentage = computed(() => {
    if (!plan.value || plan.value.total_actions === 0) return 0
    return Math.round((plan.value.completed_actions / plan.value.total_actions) * 100)
  })

  const pendingItems = computed(() =>
    items.value.filter(i => i.status === 'todo' || i.status === 'in_progress')
  )

  const completedItems = computed(() =>
    items.value.filter(i => i.status === 'completed')
  )

  const highPriorityItems = computed(() =>
    items.value.filter(i => i.priority === 'high' && i.status !== 'completed' && i.status !== 'cancelled')
  )

  // --- Setters ---

  function setPlan(data: ActionPlan | null): void {
    plan.value = data
  }

  function setItems(data: ActionItem[], count: number): void {
    items.value = data
    total.value = count
  }

  function setProgress(data: PlanProgress | null): void {
    progress.value = data
  }

  function setLoading(value: boolean): void {
    loading.value = value
  }

  function setError(message: string | null): void {
    error.value = message
  }

  function updateItem(updatedItem: ActionItem): void {
    const idx = items.value.findIndex(i => i.id === updatedItem.id)
    if (idx !== -1) {
      items.value = [
        ...items.value.slice(0, idx),
        updatedItem,
        ...items.value.slice(idx + 1),
      ]
    }
    // Mettre à jour aussi dans plan.items si disponible
    if (plan.value && plan.value.items) {
      const planIdx = plan.value.items.findIndex(i => i.id === updatedItem.id)
      if (planIdx !== -1) {
        plan.value = {
          ...plan.value,
          items: [
            ...plan.value.items.slice(0, planIdx),
            updatedItem,
            ...plan.value.items.slice(planIdx + 1),
          ],
        }
      }
    }
  }

  function reset(): void {
    plan.value = null
    items.value = []
    total.value = 0
    loading.value = false
    error.value = null
    progress.value = null
  }

  return {
    // État
    plan,
    items,
    total,
    loading,
    error,
    progress,
    // Calculés
    hasPlan,
    completionPercentage,
    pendingItems,
    completedItems,
    highPriorityItems,
    // Méthodes
    setPlan,
    setItems,
    setProgress,
    setLoading,
    setError,
    updateItem,
    reset,
  }
})
