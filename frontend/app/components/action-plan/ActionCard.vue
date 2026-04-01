<script setup lang="ts">
import type { ActionItem } from '~/types/actionPlan'

interface Props {
  item: ActionItem
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update-status', itemId: string, status: string): void
}>()

// Labels de catégorie
const categoryLabels: Record<string, string> = {
  environment: 'Environnement',
  social: 'Social',
  governance: 'Gouvernance',
  financing: 'Financement',
  carbon: 'Carbone',
  intermediary_contact: 'Contact intermédiaire',
}

const priorityLabels: Record<string, { label: string; class: string }> = {
  high: { label: 'Haute', class: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' },
  medium: { label: 'Moyenne', class: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' },
  low: { label: 'Basse', class: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400' },
}

const statusLabels: Record<string, string> = {
  todo: 'À faire',
  in_progress: 'En cours',
  on_hold: 'En pause',
  completed: 'Terminée',
  cancelled: 'Annulée',
}

// Transitions valides
const validTransitions: Record<string, string[]> = {
  todo: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'on_hold', 'cancelled'],
  on_hold: ['in_progress', 'cancelled'],
  completed: [],
  cancelled: [],
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="emit('close')"
    >
      <!-- Overlay -->
      <div class="absolute inset-0 bg-black/50" />

      <!-- Modal -->
      <div
        class="relative bg-white dark:bg-dark-card rounded-xl shadow-xl border border-gray-200 dark:border-dark-border max-w-lg w-full max-h-[90vh] overflow-y-auto"
      >
        <!-- En-tête -->
        <div class="flex items-start justify-between p-5 border-b border-gray-200 dark:border-dark-border">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span v-if="item.category === 'intermediary_contact'" class="text-lg">🏦</span>
              <span
                :class="['text-xs px-2 py-0.5 rounded-full', priorityLabels[item.priority]?.class]"
              >
                {{ priorityLabels[item.priority]?.label }}
              </span>
              <span class="text-xs text-gray-400 dark:text-gray-500">
                {{ categoryLabels[item.category] }}
              </span>
            </div>
            <h3 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text">
              {{ item.title }}
            </h3>
          </div>
          <button
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl"
            @click="emit('close')"
          >
            ✕
          </button>
        </div>

        <!-- Corps -->
        <div class="p-5 space-y-4">
          <!-- Description -->
          <p
            v-if="item.description"
            class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed"
          >
            {{ item.description }}
          </p>

          <!-- Infos -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span class="text-gray-400 dark:text-gray-500 text-xs block">Statut</span>
              <span class="font-medium text-surface-text dark:text-surface-dark-text">
                {{ statusLabels[item.status] }}
              </span>
            </div>
            <div>
              <span class="text-gray-400 dark:text-gray-500 text-xs block">Échéance</span>
              <span class="font-medium text-surface-text dark:text-surface-dark-text">
                {{ formatDate(item.due_date) }}
              </span>
            </div>
            <div v-if="item.estimated_cost_xof">
              <span class="text-gray-400 dark:text-gray-500 text-xs block">Coût estimé</span>
              <span class="font-medium text-surface-text dark:text-surface-dark-text">
                {{ item.estimated_cost_xof.toLocaleString('fr-FR') }} FCFA
              </span>
            </div>
            <div v-if="item.estimated_benefit">
              <span class="text-gray-400 dark:text-gray-500 text-xs block">Bénéfice attendu</span>
              <span class="font-medium text-surface-text dark:text-surface-dark-text">
                {{ item.estimated_benefit }}
              </span>
            </div>
          </div>

          <!-- Progression -->
          <div v-if="item.completion_percentage > 0">
            <span class="text-gray-400 dark:text-gray-500 text-xs block mb-1">Progression</span>
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="h-2 rounded-full bg-primary-500 transition-all"
                  :style="{ width: `${item.completion_percentage}%` }"
                />
              </div>
              <span class="text-sm font-medium text-surface-text dark:text-surface-dark-text">
                {{ item.completion_percentage }}%
              </span>
            </div>
          </div>

          <!-- Coordonnées intermédiaire -->
          <div
            v-if="item.category === 'intermediary_contact' && item.intermediary_name"
            class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800"
          >
            <h4 class="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-2">
              🏦 Coordonnées de l'intermédiaire
            </h4>
            <div class="space-y-1 text-sm text-blue-600 dark:text-blue-300">
              <p class="font-medium">{{ item.intermediary_name }}</p>
              <p v-if="item.intermediary_address">📍 {{ item.intermediary_address }}</p>
              <p v-if="item.intermediary_phone">📞 {{ item.intermediary_phone }}</p>
              <p v-if="item.intermediary_email">✉️ {{ item.intermediary_email }}</p>
            </div>
            <NuxtLink
              v-if="item.related_fund_id"
              :to="`/financing/${item.related_fund_id}`"
              class="inline-block mt-3 text-sm font-medium text-blue-700 dark:text-blue-400 hover:underline"
            >
              Voir la fiche de préparation →
            </NuxtLink>
          </div>

          <!-- Actions de changement de statut -->
          <div v-if="validTransitions[item.status]?.length" class="flex flex-wrap gap-2 pt-2">
            <button
              v-for="nextStatus in validTransitions[item.status]"
              :key="nextStatus"
              class="px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors"
              :class="
                nextStatus === 'completed'
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40'
                  : nextStatus === 'cancelled'
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40'
                    : 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              "
              @click="emit('update-status', item.id, nextStatus)"
            >
              {{ statusLabels[nextStatus] }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
