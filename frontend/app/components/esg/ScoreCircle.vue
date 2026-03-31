<script setup lang="ts">
const props = defineProps<{
  score: number
  max?: number
  size?: number
  label?: string
}>()

const max = computed(() => props.max ?? 100)
const size = computed(() => props.size ?? 120)
const radius = computed(() => (size.value - 12) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const progress = computed(() => {
  const pct = Math.min(props.score / max.value, 1)
  return circumference.value * (1 - pct)
})

const color = computed(() => {
  if (props.score < 40) return '#EF4444'
  if (props.score < 70) return '#F59E0B'
  return '#10B981'
})

const bgColor = computed(() => {
  if (props.score < 40) return 'rgba(239, 68, 68, 0.1)'
  if (props.score < 70) return 'rgba(245, 158, 11, 0.1)'
  return 'rgba(16, 185, 129, 0.1)'
})
</script>

<template>
  <div class="flex flex-col items-center gap-2">
    <svg :width="size" :height="size" class="transform -rotate-90">
      <!-- Cercle de fond -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="currentColor"
        stroke-width="8"
        class="text-gray-200 dark:text-gray-700"
      />
      <!-- Cercle de progression -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="color"
        stroke-width="8"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="progress"
        class="transition-all duration-700 ease-out"
      />
    </svg>
    <!-- Score au centre -->
    <div
      class="absolute flex flex-col items-center justify-center"
      :style="{ width: `${size}px`, height: `${size}px` }"
    >
      <span class="text-2xl font-bold text-surface-text dark:text-surface-dark-text">
        {{ Math.round(score) }}
      </span>
      <span class="text-xs text-gray-500 dark:text-gray-400">/{{ max }}</span>
    </div>
    <span
      v-if="label"
      class="text-sm font-medium text-gray-600 dark:text-gray-400"
    >
      {{ label }}
    </span>
  </div>
</template>
