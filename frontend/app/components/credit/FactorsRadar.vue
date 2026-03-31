<script setup lang="ts">
import { Radar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps<{
  factors: Record<string, { score: number; weight: number; details: string }>
  axis: 'solvability' | 'green_impact'
}>()

const LABELS: Record<string, Record<string, string>> = {
  solvability: {
    activity_regularity: 'Regularite',
    information_coherence: 'Coherence',
    governance: 'Gouvernance',
    financial_transparency: 'Transparence',
    engagement_seriousness: 'Engagement',
  },
  green_impact: {
    esg_global_score: 'Score ESG',
    esg_trend: 'Tendance ESG',
    carbon_engagement: 'Carbone',
    green_projects: 'Projets verts',
  },
}

const isDark = computed(() =>
  typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
)

const chartData = computed(() => {
  const labelMap = LABELS[props.axis] ?? {}
  const labels = Object.keys(labelMap).map(k => labelMap[k])
  const data = Object.keys(labelMap).map(k => props.factors[k]?.score ?? 0)

  const borderColor = props.axis === 'solvability' ? '#3B82F6' : '#10B981'
  const bgColor = props.axis === 'solvability' ? 'rgba(59,130,246,0.2)' : 'rgba(16,185,129,0.2)'

  return {
    labels,
    datasets: [
      {
        label: props.axis === 'solvability' ? 'Solvabilite' : 'Impact Vert',
        data,
        borderColor,
        backgroundColor: bgColor,
        pointBackgroundColor: borderColor,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      beginAtZero: true,
      max: 100,
      ticks: {
        stepSize: 20,
        color: isDark.value ? '#9CA3AF' : '#6B7280',
        backdropColor: 'transparent',
      },
      pointLabels: {
        color: isDark.value ? '#D1D5DB' : '#374151',
        font: { size: 11 },
      },
      grid: {
        color: isDark.value ? '#374151' : '#E5E7EB',
      },
    },
  },
  plugins: {
    legend: { display: false },
  },
}))
</script>

<template>
  <div class="h-64">
    <Radar :data="chartData" :options="chartOptions" />
  </div>
</template>
