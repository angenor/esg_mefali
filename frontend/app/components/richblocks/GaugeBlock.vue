<script setup lang="ts">
import type { GaugeBlockData } from '~/types/richblocks'

const props = defineProps<{
  rawContent: string
}>()

const parseError = ref('')
const gaugeData = ref<GaugeBlockData | null>(null)
const animatedValue = ref(0)

try {
  const parsed = JSON.parse(props.rawContent) as GaugeBlockData
  if (parsed.value == null || !parsed.max || !parsed.label || !parsed.thresholds?.length) {
    parseError.value = 'Données de jauge incomplètes (value, max, label, thresholds requis)'
  } else {
    gaugeData.value = parsed
  }
} catch {
  parseError.value = 'JSON invalide pour la jauge'
}

// Animation du remplissage
onMounted(() => {
  if (!gaugeData.value) return
  const target = gaugeData.value.value
  const duration = 800
  const start = performance.now()

  function animate(now: number) {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    // Easing out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedValue.value = eased * target
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  requestAnimationFrame(animate)
})

const currentColor = computed(() => {
  if (!gaugeData.value) return '#10B981'
  const value = gaugeData.value.value
  const sorted = [...gaugeData.value.thresholds].sort((a, b) => a.limit - b.limit)
  for (const threshold of sorted) {
    if (value <= threshold.limit) return threshold.color
  }
  return sorted[sorted.length - 1]?.color || '#10B981'
})

// Arc SVG
const radius = 60
const strokeWidth = 12
const circumference = Math.PI * radius // Demi-cercle

const dashOffset = computed(() => {
  if (!gaugeData.value) return circumference
  const ratio = animatedValue.value / gaugeData.value.max
  return circumference * (1 - ratio)
})
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="gaugeData" class="my-3 flex justify-center">
    <div class="rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-4 inline-flex flex-col items-center">
      <svg width="150" height="90" viewBox="0 0 150 90">
        <!-- Arc de fond -->
        <path
          :d="`M ${75 - radius} 80 A ${radius} ${radius} 0 0 1 ${75 + radius} 80`"
          fill="none"
          :stroke="'currentColor'"
          class="text-gray-200 dark:text-dark-border"
          :stroke-width="strokeWidth"
          stroke-linecap="round"
        />
        <!-- Arc de valeur -->
        <path
          :d="`M ${75 - radius} 80 A ${radius} ${radius} 0 0 1 ${75 + radius} 80`"
          fill="none"
          :stroke="currentColor"
          :stroke-width="strokeWidth"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          class="transition-all duration-500"
        />
      </svg>
      <!-- Valeur centrale -->
      <div class="text-center -mt-6">
        <span class="text-2xl font-bold text-surface-text dark:text-surface-dark-text">
          {{ Math.round(animatedValue) }}
        </span>
        <span v-if="gaugeData.unit" class="text-sm text-gray-400">{{ gaugeData.unit }}</span>
      </div>
      <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {{ gaugeData.label }}
      </div>
    </div>
  </div>
</template>
