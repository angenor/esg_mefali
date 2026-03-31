<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { ScoreHistoryItem } from '~/stores/creditScore'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  history: ScoreHistoryItem[]
}>()

const isDark = computed(() =>
  typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
)

const chartData = computed(() => {
  // Trier par version croissante
  const sorted = [...props.history].sort((a, b) => a.version - b.version)

  const labels = sorted.map(
    (s) => `v${s.version} (${new Date(s.generated_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })})`
  )

  return {
    labels,
    datasets: [
      {
        label: 'Score combine',
        data: sorted.map((s) => s.combined_score),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Solvabilite',
        data: sorted.map((s) => s.solvability_score),
        borderColor: '#3B82F6',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
      {
        label: 'Impact vert',
        data: sorted.map((s) => s.green_impact_score),
        borderColor: '#8B5CF6',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
    ],
  }
})

const chartOptions = computed(() => {
  const gridColor = isDark.value ? 'rgba(75, 85, 99, 0.3)' : 'rgba(156, 163, 175, 0.15)'
  const tickColor = isDark.value ? '#D1D5DB' : '#9CA3AF'
  const legendColor = isDark.value ? '#D1D5DB' : '#9CA3AF'

  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: {
          color: gridColor,
        },
        ticks: {
          color: tickColor,
          callback: (value: number) => `${value}`,
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: tickColor,
          maxRotation: 45,
        },
      },
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: legendColor,
          usePointStyle: true,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#F9FAFB',
        bodyColor: '#D1D5DB',
        borderColor: 'rgba(75, 85, 99, 0.3)',
        borderWidth: 1,
        callbacks: {
          label: (ctx: { dataset: { label?: string }; parsed: { y: number } }) =>
            `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}/100`,
        },
      },
    },
  }
})
</script>

<template>
  <div class="h-64">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
