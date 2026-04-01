<script setup lang="ts">
import type { ActionItem, ActionItemCategory } from '~/types/actionPlan'

interface Props {
  items: ActionItem[]
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'select', item: ActionItem): void
}>()

// Couleurs par catégorie
const categoryColors: Record<ActionItemCategory, string> = {
  environment: 'bg-green-500',
  social: 'bg-purple-500',
  governance: 'bg-blue-500',
  financing: 'bg-amber-500',
  carbon: 'bg-teal-500',
  intermediary_contact: 'bg-indigo-500',
}

const categoryBorderColors: Record<ActionItemCategory, string> = {
  environment: 'border-green-500',
  social: 'border-purple-500',
  governance: 'border-blue-500',
  financing: 'border-amber-500',
  carbon: 'border-teal-500',
  intermediary_contact: 'border-indigo-500',
}

// Icônes par statut
function statusIcon(status: string): string {
  switch (status) {
    case 'completed': return '✓'
    case 'in_progress': return '▶'
    case 'on_hold': return '⏸'
    case 'cancelled': return '✕'
    default: return '○'
  }
}

function statusClass(status: string): string {
  switch (status) {
    case 'completed': return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
    case 'in_progress': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
    case 'on_hold': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400'
    case 'cancelled': return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
    default: return 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Sans échéance'
  return new Date(dateStr).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="relative">
    <!-- Ligne verticale -->
    <div
      class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-dark-border"
    />

    <!-- Items -->
    <div
      v-for="item in items"
      :key="item.id"
      class="relative flex gap-4 pb-6 cursor-pointer group"
      @click="emit('select', item)"
    >
      <!-- Point sur la timeline -->
      <div
        :class="[
          'relative z-10 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2',
          categoryBorderColors[item.category],
          statusClass(item.status),
        ]"
      >
        <span v-if="item.category === 'intermediary_contact'">🏦</span>
        <span v-else>{{ statusIcon(item.status) }}</span>
      </div>

      <!-- Carte -->
      <div
        :class="[
          'flex-1 bg-white dark:bg-dark-card rounded-lg border border-gray-200 dark:border-dark-border p-4',
          'group-hover:shadow-md transition-shadow',
          'border-l-4',
          categoryBorderColors[item.category],
        ]"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text truncate">
              {{ item.title }}
            </h4>
            <p
              v-if="item.description"
              class="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2"
            >
              {{ item.description }}
            </p>
          </div>
          <span :class="['text-xs px-2 py-0.5 rounded-full whitespace-nowrap', statusClass(item.status)]">
            {{ statusIcon(item.status) }} {{ item.status.replace('_', ' ') }}
          </span>
        </div>

        <!-- Métadonnées -->
        <div class="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-400 dark:text-gray-500">
          <span>📅 {{ formatDate(item.due_date) }}</span>
          <span v-if="item.estimated_cost_xof">💰 {{ item.estimated_cost_xof.toLocaleString('fr-FR') }} FCFA</span>
          <span v-if="item.intermediary_name">🏦 {{ item.intermediary_name }}</span>
        </div>

        <!-- Barre de progression -->
        <div v-if="item.completion_percentage > 0" class="mt-2">
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              :class="['h-1.5 rounded-full', categoryColors[item.category]]"
              :style="{ width: `${item.completion_percentage}%` }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- État vide -->
    <div v-if="items.length === 0" class="text-center py-8 text-gray-400 dark:text-gray-600">
      <p class="text-lg mb-2">📋</p>
      <p class="text-sm">Aucune action dans cette catégorie</p>
    </div>
  </div>
</template>
