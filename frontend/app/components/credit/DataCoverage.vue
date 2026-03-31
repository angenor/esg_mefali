<script setup lang="ts">
defineProps<{
  sources: Array<{
    name: string
    available: boolean
    completeness: number
    last_updated?: string
  }>
  overallCoverage: number
}>()

function barColor(completeness: number): string {
  if (completeness >= 0.8) return 'bg-emerald-500'
  if (completeness >= 0.5) return 'bg-blue-500'
  if (completeness > 0) return 'bg-amber-500'
  return 'bg-gray-300 dark:bg-gray-600'
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between mb-4">
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
        Couverture globale
      </span>
      <span class="text-sm font-bold" :class="overallCoverage >= 0.7 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'">
        {{ Math.round(overallCoverage * 100) }}%
      </span>
    </div>

    <div v-for="source in sources" :key="source.name" class="space-y-1">
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-600 dark:text-gray-400">{{ source.name }}</span>
        <span class="text-xs font-medium" :class="source.available ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400 dark:text-gray-500'">
          {{ source.available ? `${Math.round(source.completeness * 100)}%` : 'Non disponible' }}
        </span>
      </div>
      <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="barColor(source.completeness)"
          :style="{ width: `${source.completeness * 100}%` }"
        />
      </div>
    </div>
  </div>
</template>
