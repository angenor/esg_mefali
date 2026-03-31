import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ESGAssessment,
  ESGAssessmentSummary,
  ScoreResponse,
} from '~/types/esg'

export const useEsgStore = defineStore('esg', () => {
  const assessments = ref<ESGAssessmentSummary[]>([])
  const currentAssessment = ref<ESGAssessment | null>(null)
  const currentScore = ref<ScoreResponse | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasAssessments = computed(() => assessments.value.length > 0)
  const latestCompleted = computed(() =>
    assessments.value.find(a => a.status === 'completed') ?? null
  )

  function setAssessments(data: ESGAssessmentSummary[], count: number) {
    assessments.value = data
    total.value = count
  }

  function setCurrentAssessment(data: ESGAssessment | null) {
    currentAssessment.value = data
  }

  function setCurrentScore(data: ScoreResponse | null) {
    currentScore.value = data
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
    currentScore.value = null
    total.value = 0
    loading.value = false
    error.value = null
  }

  return {
    assessments,
    currentAssessment,
    currentScore,
    total,
    loading,
    error,
    hasAssessments,
    latestCompleted,
    setAssessments,
    setCurrentAssessment,
    setCurrentScore,
    setLoading,
    setError,
    reset,
  }
})
