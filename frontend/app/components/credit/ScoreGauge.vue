<script setup lang="ts">
const props = defineProps<{
  score: number
  label?: string
  size?: 'sm' | 'md' | 'lg'
}>()

const size = computed(() => props.size ?? 'lg')

const dimensions = computed(() => {
  const sizes = { sm: 120, md: 160, lg: 220 }
  return sizes[size.value]
})

const strokeWidth = computed(() => size.value === 'lg' ? 12 : 8)

const radius = computed(() => (dimensions.value - strokeWidth.value) / 2)
const circumference = computed(() => Math.PI * radius.value)
const offset = computed(() => circumference.value - (props.score / 100) * circumference.value)

const scoreColor = computed(() => {
  if (props.score >= 80) return '#10B981'
  if (props.score >= 60) return '#3B82F6'
  if (props.score >= 40) return '#F59E0B'
  return '#EF4444'
})

const fontSize = computed(() => {
  const sizes = { sm: 'text-xl', md: 'text-2xl', lg: 'text-4xl' }
  return sizes[size.value]
})
</script>

<template>
  <div class="flex flex-col items-center">
    <svg
      :width="dimensions"
      :height="dimensions / 2 + strokeWidth + 10"
      :viewBox="`0 0 ${dimensions} ${dimensions / 2 + strokeWidth + 10}`"
    >
      <!-- Fond -->
      <path
        :d="`M ${strokeWidth / 2} ${dimensions / 2 + 5} A ${radius} ${radius} 0 0 1 ${dimensions - strokeWidth / 2} ${dimensions / 2 + 5}`"
        fill="none"
        stroke="currentColor"
        class="text-gray-200 dark:text-gray-700"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
      />
      <!-- Valeur -->
      <path
        :d="`M ${strokeWidth / 2} ${dimensions / 2 + 5} A ${radius} ${radius} 0 0 1 ${dimensions - strokeWidth / 2} ${dimensions / 2 + 5}`"
        fill="none"
        :stroke="scoreColor"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        class="transition-all duration-1000 ease-out"
      />
    </svg>
    <div class="text-center -mt-8">
      <span :class="[fontSize, 'font-bold']" :style="{ color: scoreColor }">
        {{ score.toFixed(1) }}
      </span>
      <span class="text-sm text-gray-500 dark:text-gray-400">/100</span>
    </div>
    <p v-if="label" class="mt-2 text-sm font-medium text-gray-600 dark:text-gray-400">
      {{ label }}
    </p>
  </div>
</template>
