import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  CarbonAssessment,
  CarbonAssessmentSummary,
  CarbonSummary,
} from '~/types/carbon'

export const useCarbonStore = defineStore('carbon', () => {
  const assessments = ref<CarbonAssessmentSummary[]>([])
  const currentAssessment = ref<CarbonAssessment | null>(null)
  const currentSummary = ref<CarbonSummary | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasAssessments = computed(() => assessments.value.length > 0)
  const latestCompleted = computed(() =>
    assessments.value.find(a => a.status === 'completed') ?? null
  )

  function setAssessments(data: CarbonAssessmentSummary[], count: number) {
    assessments.value = data
    total.value = count
  }

  function setCurrentAssessment(data: CarbonAssessment | null) {
    currentAssessment.value = data
  }

  function setCurrentSummary(data: CarbonSummary | null) {
    currentSummary.value = data
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function reset() {
    assessments.value = []
    currentAssessment.value = null
    currentSummary.value = null
    total.value = 0
    loading.value = false
    error.value = null
  }

  return {
    assessments,
    currentAssessment,
    currentSummary,
    total,
    loading,
    error,
    hasAssessments,
    latestCompleted,
    setAssessments,
    setCurrentAssessment,
    setCurrentSummary,
    setLoading,
    setError,
    reset,
  }
})
