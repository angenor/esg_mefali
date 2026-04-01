import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardSummary } from '~/types/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref<DashboardSummary | null>(null)
  const loading = ref(false)
  const error = ref('')

  function setSummary(data: DashboardSummary) {
    summary.value = data
  }

  function setLoading(val: boolean) {
    loading.value = val
  }

  function setError(msg: string) {
    error.value = msg
  }

  function reset() {
    summary.value = null
    loading.value = false
    error.value = ''
  }

  return { summary, loading, error, setSummary, setLoading, setError, reset }
})
