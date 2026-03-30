<script setup lang="ts">
import type { ProgressBlockData } from '~/types/richblocks'

const props = defineProps<{
  rawContent: string
}>()

const parseError = ref('')
const progressData = ref<ProgressBlockData | null>(null)
const animated = ref(false)

try {
  const parsed = JSON.parse(props.rawContent) as ProgressBlockData
  if (!parsed.items?.length) {
    parseError.value = 'Données de progression incomplètes (items requis)'
  } else {
    progressData.value = parsed
  }
} catch {
  parseError.value = 'JSON invalide pour les barres de progression'
}

onMounted(() => {
  // Declencher l'animation apres le montage
  requestAnimationFrame(() => {
    animated.value = true
  })
})

const defaultColors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="progressData" class="my-3 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-4 space-y-3">
    <div
      v-for="(item, idx) in progressData.items"
      :key="idx"
      class="flex items-center gap-3"
    >
      <!-- Label -->
      <span class="text-sm text-surface-text dark:text-surface-dark-text w-28 shrink-0 truncate">
        {{ item.label }}
      </span>
      <!-- Barre -->
      <div class="flex-1 h-3 bg-gray-100 dark:bg-dark-hover rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-700 ease-out"
          :style="{
            width: animated ? `${(item.value / item.max) * 100}%` : '0%',
            backgroundColor: item.color || defaultColors[idx % defaultColors.length],
          }"
        />
      </div>
      <!-- Valeur -->
      <span class="text-sm font-medium text-surface-text dark:text-surface-dark-text w-12 text-right shrink-0">
        {{ item.value }}/{{ item.max }}
      </span>
    </div>
  </div>
</template>
