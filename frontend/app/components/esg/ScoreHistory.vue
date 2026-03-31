<script setup lang="ts">
import { Line } from 'vue-chartjs'
import type { ESGAssessmentSummary } from '~/types/esg'

const props = defineProps<{
  assessments: ESGAssessmentSummary[]
}>()

const chartData = computed(() => {
  // Trier par date croissante
  const sorted = [...props.assessments]
    .filter(a => a.status === 'completed' && a.overall_score !== null)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())

  const labels = sorted.map(a => {
    const d = new Date(a.created_at)
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: '2-digit' })
  })

  return {
    labels,
    datasets: [
      {
        label: 'Score global',
        data: sorted.map(a => a.overall_score),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointBackgroundColor: '#10B981',
      },
      {
        label: 'Environnement',
        data: sorted.map(a => a.environment_score),
        borderColor: '#34D399',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#34D399',
      },
      {
        label: 'Social',
        data: sorted.map(a => a.social_score),
        borderColor: '#3B82F6',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#3B82F6',
      },
      {
        label: 'Gouvernance',
        data: sorted.map(a => a.governance_score),
        borderColor: '#8B5CF6',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#8B5CF6',
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 16,
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx: { dataset: { label: string }; parsed: { y: number } }) =>
          `${ctx.dataset.label}: ${ctx.parsed.y}/100`,
      },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 100,
      ticks: { stepSize: 20 },
      grid: { color: 'rgba(156, 163, 175, 0.15)' },
    },
    x: {
      grid: { display: false },
    },
  },
}))
</script>

<template>
  <div class="h-64">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
