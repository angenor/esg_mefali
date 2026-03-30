<script setup lang="ts">
import { Bar, Line, Pie, Doughnut, Radar, PolarArea } from 'vue-chartjs'
import type { ChartBlockData } from '~/types/richblocks'

const props = defineProps<{
  rawContent: string
}>()

const showFullscreen = ref(false)
const chartCanvas = ref<InstanceType<typeof Bar | typeof Line | typeof Pie | typeof Doughnut | typeof Radar | typeof PolarArea> | null>(null)
const parseError = ref('')
const chartData = ref<ChartBlockData | null>(null)

const chartComponents: Record<string, unknown> = {
  bar: Bar,
  line: Line,
  pie: Pie,
  doughnut: Doughnut,
  radar: Radar,
  polarArea: PolarArea,
}

// Parser le JSON du bloc
try {
  const parsed = JSON.parse(props.rawContent) as ChartBlockData
  if (!parsed.type || !parsed.data?.labels || !parsed.data?.datasets) {
    parseError.value = 'Données de graphique incomplètes (type, data.labels, data.datasets requis)'
  } else if (!chartComponents[parsed.type]) {
    parseError.value = `Type de graphique non supporté : ${parsed.type}`
  } else {
    chartData.value = parsed
  }
} catch {
  parseError.value = 'JSON invalide pour le graphique'
}

const chartComponent = computed(() => {
  if (!chartData.value) return null
  return chartComponents[chartData.value.type]
})

const chartOptions = computed(() => {
  const defaults: Record<string, unknown> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: document.documentElement.classList.contains('dark') ? '#F9FAFB' : '#111827',
        },
      },
    },
  }
  return { ...defaults, ...(chartData.value?.options || {}) }
})

function downloadChart() {
  const ref = chartCanvas.value as { $el?: HTMLElement; chart?: { canvas?: HTMLCanvasElement } } | null
  const canvas = ref?.$el?.querySelector?.('canvas')
    || ref?.chart?.canvas
  if (!canvas) return

  const link = document.createElement('a')
  link.download = `graphique-${chartData.value?.type || 'chart'}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="chartData" class="my-3">
    <div class="rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-4">
      <div class="h-62.5 md:h-75">
        <component
          :is="chartComponent"
          ref="chartCanvas"
          :data="chartData.data"
          :options="chartOptions"
        />
      </div>
      <!-- Actions -->
      <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-dark-border">
        <button
          class="text-xs text-gray-500 dark:text-gray-400 hover:text-brand-blue dark:hover:text-brand-blue flex items-center gap-1 transition-colors"
          @click="showFullscreen = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15 13.586V12a1 1 0 011-1z" />
          </svg>
          Agrandir
        </button>
        <button
          class="text-xs text-gray-500 dark:text-gray-400 hover:text-brand-green dark:hover:text-brand-green flex items-center gap-1 transition-colors"
          @click="downloadChart"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
          Télécharger
        </button>
      </div>
    </div>

    <!-- Modale plein écran -->
    <FullscreenModal :visible="showFullscreen" @close="showFullscreen = false">
      <div class="h-[70vh]">
        <component
          :is="chartComponent"
          :data="chartData.data"
          :options="chartOptions"
        />
      </div>
    </FullscreenModal>
  </div>
</template>
