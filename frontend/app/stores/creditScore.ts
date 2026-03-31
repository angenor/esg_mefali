import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CreditScoreData {
  id: string
  version: number
  combined_score: number
  solvability_score: number
  green_impact_score: number
  confidence_level: number
  confidence_label: string
  generated_at: string
  valid_until: string
  is_expired?: boolean
}

export interface ScoreBreakdown extends CreditScoreData {
  score_breakdown: {
    solvability: {
      total: number
      factors: Record<string, {
        score: number
        weight: number
        details: string
        intermediary_interactions?: {
          contacted: number
          appointments: number
          submitted: number
          intermediary_names: string[]
        }
        application_statuses?: {
          interested: number
          submitted_via_intermediary: number
          accepted: number
        }
      }>
    }
    green_impact: {
      total: number
      factors: Record<string, {
        score: number
        weight: number
        details: string
        application_statuses?: {
          interested: number
          submitted_via_intermediary: number
          accepted: number
        }
      }>
    }
  }
  data_sources: {
    sources: Array<{
      name: string
      available: boolean
      completeness: number
      last_updated?: string
    }>
    overall_coverage: number
  }
  recommendations: Array<{
    action: string
    impact: string
    category: string
  }>
}

export interface ScoreHistoryItem {
  id: string
  version: number
  combined_score: number
  solvability_score: number
  green_impact_score: number
  confidence_level: number
  confidence_label: string
  generated_at: string
}

export const useCreditScoreStore = defineStore('creditScore', () => {
  const score = ref<CreditScoreData | null>(null)
  const breakdown = ref<ScoreBreakdown | null>(null)
  const history = ref<ScoreHistoryItem[]>([])
  const historyTotal = ref(0)
  const loading = ref(false)
  const generating = ref(false)
  const error = ref<string | null>(null)

  const hasScore = computed(() => score.value !== null)
  const isExpired = computed(() => score.value?.is_expired ?? false)
  const hasHistory = computed(() => history.value.length > 1)

  function setScore(data: CreditScoreData | null) {
    score.value = data
  }

  function setBreakdown(data: ScoreBreakdown | null) {
    breakdown.value = data
  }

  function setHistory(items: ScoreHistoryItem[], total: number) {
    history.value = items
    historyTotal.value = total
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setGenerating(value: boolean) {
    generating.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function reset() {
    score.value = null
    breakdown.value = null
    history.value = []
    historyTotal.value = 0
    loading.value = false
    generating.value = false
    error.value = null
  }

  return {
    score,
    breakdown,
    history,
    historyTotal,
    loading,
    generating,
    error,
    hasScore,
    isExpired,
    hasHistory,
    setScore,
    setBreakdown,
    setHistory,
    setLoading,
    setGenerating,
    setError,
    reset,
  }
})
