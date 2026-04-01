<script setup lang="ts">
// Liste des prochaines actions du plan d'action
import type { NextAction } from '~/types/dashboard'

interface Props {
  actions: NextAction[]
}

const props = defineProps<Props>()

// Icône par catégorie
function categoryIcon(category: string): string {
  const icons: Record<string, string> = {
    environment: '🌿',
    social: '👥',
    governance: '📋',
    financing: '💰',
    carbon: '💨',
    intermediary_contact: '🏦',
  }
  return icons[category] ?? '📌'
}

// Couleur du badge de statut
function statusColor(status: string): string {
  switch (status) {
    case 'in_progress': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
    case 'todo': return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
    default: return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  }
}

// Libellé de statut en français
function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    todo: 'À faire',
    in_progress: 'En cours',
    on_hold: 'En attente',
    completed: 'Terminé',
    cancelled: 'Annulé',
  }
  return labels[status] ?? status
}

// Formater la date d'échéance
function formatDueDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

// Vérifier si une action est en retard
function isOverdue(dateStr: string | null): boolean {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- Liste des actions -->
    <template v-if="actions.length > 0">
      <div
        v-for="action in actions"
        :key="action.id"
        class="bg-white dark:bg-dark-card rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-4 flex gap-3"
      >
        <!-- Icône catégorie -->
        <span class="text-2xl flex-shrink-0 mt-0.5">{{ categoryIcon(action.category) }}</span>

        <div class="flex-1 min-w-0">
          <!-- Titre + statut -->
          <div class="flex items-start justify-between gap-2">
            <p class="text-sm font-medium text-surface-text dark:text-surface-dark-text leading-snug">
              {{ action.title }}
            </p>
            <span
              :class="['text-xs px-2 py-0.5 rounded-full flex-shrink-0 font-medium', statusColor(action.status)]"
            >
              {{ statusLabel(action.status) }}
            </span>
          </div>

          <!-- Date d'échéance -->
          <p
            v-if="action.due_date"
            :class="[
              'text-xs mt-1',
              isOverdue(action.due_date)
                ? 'text-red-500 dark:text-red-400 font-medium'
                : 'text-gray-500 dark:text-gray-500',
            ]"
          >
            {{ isOverdue(action.due_date) ? '⚠️ ' : '📅 ' }}{{ formatDueDate(action.due_date) }}
          </p>

          <!-- Informations intermédiaire (catégorie intermediary_contact) -->
          <template v-if="action.category === 'intermediary_contact' && action.intermediary_name">
            <div class="mt-2 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-500">
              <span>🏦</span>
              <div>
                <p class="font-medium text-gray-700 dark:text-gray-300">{{ action.intermediary_name }}</p>
                <p v-if="action.intermediary_address" class="mt-0.5">{{ action.intermediary_address }}</p>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- État vide -->
    <div
      v-else
      class="bg-white dark:bg-dark-card rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-6 text-center"
    >
      <span class="text-3xl">🎯</span>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-500">
        Aucune action en cours pour le moment.
      </p>
      <NuxtLink
        to="/action-plan"
        class="mt-2 inline-block text-xs text-green-600 dark:text-green-400 hover:underline"
      >
        Créer un plan d'action →
      </NuxtLink>
    </div>
  </div>
</template>
