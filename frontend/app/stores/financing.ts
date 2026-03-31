import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  FundMatchSummary,
  FundMatch,
  FundSummary,
  Fund,
  IntermediarySummary,
  Intermediary,
} from '~/types/financing'

export const useFinancingStore = defineStore('financing', () => {
  // Matches / recommandations
  const matches = ref<FundMatchSummary[]>([])
  const currentMatch = ref<FundMatch | null>(null)
  const matchesTotal = ref(0)

  // Fonds
  const funds = ref<FundSummary[]>([])
  const currentFund = ref<Fund | null>(null)
  const fundsTotal = ref(0)

  // Intermediaires
  const intermediaries = ref<IntermediarySummary[]>([])
  const currentIntermediary = ref<Intermediary | null>(null)
  const intermediariesTotal = ref(0)

  // UI state
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeTab = ref<'recommendations' | 'funds' | 'intermediaries'>('recommendations')

  // Computed
  const hasMatches = computed(() => matches.value.length > 0)
  const hasFunds = computed(() => funds.value.length > 0)
  const hasIntermediaries = computed(() => intermediaries.value.length > 0)

  function setMatches(data: FundMatchSummary[], total: number) {
    matches.value = data
    matchesTotal.value = total
  }

  function setCurrentMatch(data: FundMatch | null) {
    currentMatch.value = data
  }

  function setFunds(data: FundSummary[], total: number) {
    funds.value = data
    fundsTotal.value = total
  }

  function setCurrentFund(data: Fund | null) {
    currentFund.value = data
  }

  function setIntermediaries(data: IntermediarySummary[], total: number) {
    intermediaries.value = data
    intermediariesTotal.value = total
  }

  function setCurrentIntermediary(data: Intermediary | null) {
    currentIntermediary.value = data
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function setActiveTab(tab: 'recommendations' | 'funds' | 'intermediaries') {
    activeTab.value = tab
  }

  function reset() {
    matches.value = []
    currentMatch.value = null
    matchesTotal.value = 0
    funds.value = []
    currentFund.value = null
    fundsTotal.value = 0
    intermediaries.value = []
    currentIntermediary.value = null
    intermediariesTotal.value = 0
    loading.value = false
    error.value = null
    activeTab.value = 'recommendations'
  }

  return {
    matches, currentMatch, matchesTotal,
    funds, currentFund, fundsTotal,
    intermediaries, currentIntermediary, intermediariesTotal,
    loading, error, activeTab,
    hasMatches, hasFunds, hasIntermediaries,
    setMatches, setCurrentMatch,
    setFunds, setCurrentFund,
    setIntermediaries, setCurrentIntermediary,
    setLoading, setError, setActiveTab, reset,
  }
})
