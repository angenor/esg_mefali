<script setup lang="ts">
// Fil d'activité récente du dashboard
import type { ActivityEvent } from '~/types/dashboard'

interface Props {
  events: ActivityEvent[]
}

const props = defineProps<Props>()

// Icône par type d'événement
function eventIcon(type: string): string {
  const icons: Record<string, string> = {
    esg_completed: '📊',
    carbon_completed: '💨',
    badge_unlocked: '🏅',
    action_status_change: '✅',
    application_status_change: '📝',
  }
  return icons[type] ?? '🔔'
}

// Couleur de fond de l'icône par type
function eventBgColor(type: string): string {
  switch (type) {
    case 'esg_completed': return 'bg-blue-100 dark:bg-blue-900/30'
    case 'carbon_completed': return 'bg-green-100 dark:bg-green-900/30'
    case 'badge_unlocked': return 'bg-yellow-100 dark:bg-yellow-900/30'
    case 'action_status_change': return 'bg-purple-100 dark:bg-purple-900/30'
    case 'application_status_change': return 'bg-orange-100 dark:bg-orange-900/30'
    default: return 'bg-gray-100 dark:bg-gray-700'
  }
}

// Calcul du temps relatif (il y a X min/h/j)
function relativeTime(timestamp: string): string {
  const now = new Date()
  const ts = new Date(timestamp)
  const diffMs = now.getTime() - ts.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffH = Math.floor(diffMin / 60)
  const diffD = Math.floor(diffH / 24)

  if (diffSec < 60) return "à l'instant"
  if (diffMin < 60) return `il y a ${diffMin} min`
  if (diffH < 24) return `il y a ${diffH} h`
  if (diffD < 30) return `il y a ${diffD} j`
  return ts.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <!-- Liste des événements -->
    <template v-if="events.length > 0">
      <div
        v-for="(event, index) in events"
        :key="index"
        class="flex items-start gap-3 bg-white dark:bg-dark-card rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-3"
      >
        <!-- Icône type événement -->
        <div
          :class="['w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-base', eventBgColor(event.type)]"
        >
          {{ eventIcon(event.type) }}
        </div>

        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-surface-text dark:text-surface-dark-text leading-snug">
            {{ event.title }}
          </p>
          <p v-if="event.description" class="text-xs text-gray-500 dark:text-gray-500 mt-0.5 truncate">
            {{ event.description }}
          </p>
        </div>

        <!-- Horodatage relatif -->
        <span class="text-xs text-gray-400 dark:text-gray-600 flex-shrink-0 mt-0.5">
          {{ relativeTime(event.timestamp) }}
        </span>
      </div>
    </template>

    <!-- État vide -->
    <div
      v-else
      class="bg-white dark:bg-dark-card rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-6 text-center"
    >
      <span class="text-3xl">📭</span>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-500">
        Aucune activité récente.
      </p>
      <p class="text-xs text-gray-400 dark:text-gray-600 mt-1">
        Vos actions et évaluations apparaîtront ici.
      </p>
    </div>
  </div>
</template>
