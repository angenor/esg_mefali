<script setup lang="ts">
import { useReports } from '~/composables/useReports'
import type { ReportStatus } from '~/types/report'

const props = defineProps<{
  assessmentId: string
}>()

const { generateReport, pollStatus, downloadReport, loading, error } = useReports()

const status = ref<ReportStatus | null>(null)
const reportId = ref<string | null>(null)
const polling = ref(false)

const buttonLabel = computed(() => {
  if (loading.value && !polling.value) return 'Lancement...'
  if (polling.value || status.value === 'generating') return 'Generation en cours...'
  if (status.value === 'completed') return 'Telecharger le rapport PDF'
  if (status.value === 'failed') return 'Echec — Reessayer'
  return 'Generer le rapport PDF'
})

const buttonDisabled = computed(() => {
  return loading.value || polling.value || status.value === 'generating'
})

async function handleClick() {
  if (status.value === 'completed' && reportId.value) {
    downloadReport(reportId.value)
    return
  }

  error.value = ''
  const result = await generateReport(props.assessmentId)
  if (!result) return

  reportId.value = result.id
  status.value = result.status

  if (result.status === 'generating') {
    await startPolling()
  }
}

async function startPolling() {
  polling.value = true
  const maxAttempts = 60
  let attempts = 0

  while (attempts < maxAttempts && polling.value) {
    await new Promise(resolve => setTimeout(resolve, 2000))
    attempts++

    if (!reportId.value) break

    const statusResult = await pollStatus(reportId.value)
    if (!statusResult) continue

    status.value = statusResult.status

    if (statusResult.status === 'completed' || statusResult.status === 'failed') {
      polling.value = false
      break
    }
  }

  if (attempts >= maxAttempts) {
    polling.value = false
    status.value = 'failed'
    error.value = 'Delai de generation depasse. Veuillez reessayer.'
  }
}

onUnmounted(() => {
  polling.value = false
})
</script>

<template>
  <div class="inline-flex flex-col items-start gap-2">
    <button
      :disabled="buttonDisabled"
      class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200"
      :class="{
        'bg-brand-green text-white hover:bg-emerald-600 shadow-sm': !status || status === 'failed',
        'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-wait': buttonDisabled && status !== 'completed',
        'bg-blue-600 text-white hover:bg-blue-700 shadow-sm': status === 'completed',
      }"
      @click="handleClick"
    >
      <!-- Icone PDF -->
      <svg
        v-if="!polling && status !== 'generating'"
        xmlns="http://www.w3.org/2000/svg"
        class="w-4 h-4"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586L7.707 10.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z"
          clip-rule="evenodd"
        />
      </svg>

      <!-- Spinner -->
      <div
        v-if="polling || status === 'generating'"
        class="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-white"
      />

      {{ buttonLabel }}
    </button>

    <!-- Message d'erreur -->
    <p v-if="error" class="text-xs text-red-500 dark:text-red-400">
      {{ error }}
    </p>

    <!-- Indicateur de progression -->
    <p
      v-if="polling"
      class="text-xs text-gray-500 dark:text-gray-400"
    >
      Le rapport est en cours de generation. Cela peut prendre quelques secondes...
    </p>
  </div>
</template>
