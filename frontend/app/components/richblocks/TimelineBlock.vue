<script setup lang="ts">
import type { TimelineBlockData } from '~/types/richblocks'
import { normalizeTimeline } from '~/utils/normalizeTimeline'

const props = defineProps<{
  rawContent: string
}>()

const parseError = ref('')
const timelineData = ref<TimelineBlockData | null>(null)

try {
  const parsed = JSON.parse(props.rawContent)
  const normalized = normalizeTimeline(parsed)
  if (!normalized) {
    parseError.value = 'Données de frise chronologique incomplètes (events, phases, items ou steps requis)'
  } else {
    timelineData.value = normalized
  }
} catch {
  parseError.value = 'JSON invalide pour la frise chronologique'
}

const statusColors: Record<string, { dot: string; line: string }> = {
  done: { dot: 'bg-brand-green', line: 'bg-brand-green' },
  in_progress: { dot: 'bg-brand-blue', line: 'bg-brand-blue' },
  todo: { dot: 'bg-gray-300 dark:bg-gray-600', line: 'bg-gray-200 dark:bg-dark-border' },
}

const statusLabels: Record<string, string> = {
  done: 'Terminé',
  in_progress: 'En cours',
  todo: 'À faire',
}
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="timelineData" class="my-3 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-4">
    <div class="relative">
      <div
        v-for="(event, idx) in timelineData.events"
        :key="idx"
        class="flex gap-4 pb-6 last:pb-0"
      >
        <!-- Ligne verticale + point -->
        <div class="flex flex-col items-center">
          <div
            class="w-3 h-3 rounded-full shrink-0 ring-2 ring-white dark:ring-dark-card"
            :class="statusColors[event.status]?.dot ?? 'bg-gray-300 dark:bg-gray-600'"
          />
          <div
            v-if="idx < timelineData.events.length - 1"
            class="w-0.5 flex-1 mt-1"
            :class="statusColors[event.status]?.line ?? 'bg-gray-200 dark:bg-dark-border'"
          />
        </div>

        <!-- Contenu -->
        <div class="-mt-0.5 pb-1">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-gray-400">{{ event.date }}</span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
              :class="{
                'bg-brand-green/10 text-brand-green': event.status === 'done',
                'bg-brand-blue/10 text-brand-blue': event.status === 'in_progress',
                'bg-gray-100 text-gray-500 dark:bg-dark-hover dark:text-gray-400': event.status === 'todo',
              }"
            >
              {{ statusLabels[event.status] || event.status }}
            </span>
          </div>
          <h4 class="text-sm font-medium text-surface-text dark:text-surface-dark-text mt-0.5">
            {{ event.title }}
          </h4>
          <p v-if="event.description" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ event.description }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
