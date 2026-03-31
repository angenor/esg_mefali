<script setup lang="ts">
import { useCarbon } from '~/composables/useCarbon'
import { useCarbonStore } from '~/stores/carbon'

definePageMeta({
  layout: 'default',
})

const carbonStore = useCarbonStore()
const { fetchAssessments, loading, error } = useCarbon()

onMounted(() => {
  fetchAssessments()
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    in_progress: 'En cours',
    completed: 'Termine',
  }
  return labels[status] ?? status
}

function statusColor(status: string): string {
  const colors: Record<string, string> = {
    in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  }
  return colors[status] ?? 'bg-gray-100 text-gray-600'
}

const categoryLabels: Record<string, string> = {
  energy: 'Energie',
  transport: 'Transport',
  waste: 'Dechets',
  industrial: 'Proc. ind.',
  agriculture: 'Agriculture',
}

const categoryColors: Record<string, string> = {
  energy: 'bg-amber-500',
  transport: 'bg-blue-500',
  waste: 'bg-emerald-500',
  industrial: 'bg-violet-500',
  agriculture: 'bg-pink-500',
}
</script>

<template>
  <div class="flex flex-col h-full bg-surface-bg dark:bg-surface-dark-bg">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-dark-border">
      <div>
        <h1 class="text-xl font-bold text-surface-text dark:text-surface-dark-text">
          Empreinte Carbone
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Calculez et suivez l'empreinte carbone de votre entreprise
        </p>
      </div>
      <NuxtLink
        to="/chat"
        class="inline-flex items-center gap-2 px-4 py-2 bg-brand-green text-white rounded-lg hover:bg-emerald-600 transition-colors text-sm font-medium"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        Nouveau bilan
      </NuxtLink>
    </div>

    <div class="flex-1 overflow-y-auto p-6">
      <!-- Chargement -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-green" />
      </div>

      <!-- Erreur -->
      <div
        v-else-if="error"
        class="text-center py-12 text-red-500 dark:text-red-400"
      >
        {{ error }}
      </div>

      <!-- Aucun bilan -->
      <div
        v-else-if="!carbonStore.hasAssessments"
        class="flex flex-col items-center justify-center py-16 text-center"
      >
        <div class="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-emerald-600 dark:text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clip-rule="evenodd" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text mb-2">
          Aucun bilan carbone
        </h3>
        <p class="text-gray-500 dark:text-gray-400 max-w-md mb-6">
          Demarrez votre premier bilan carbone dans le chat. Notre assistant vous guidera a travers les categories d'emissions pour calculer votre empreinte.
        </p>
        <NuxtLink
          to="/chat"
          class="inline-flex items-center gap-2 px-6 py-3 bg-brand-green text-white rounded-lg hover:bg-emerald-600 transition-colors font-medium"
        >
          Demarrer dans le chat
        </NuxtLink>
      </div>

      <!-- Liste des bilans -->
      <div v-else class="space-y-4">
        <div
          v-for="assessment in carbonStore.assessments"
          :key="assessment.id"
          class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <!-- Emissions cercle -->
              <div
                class="w-14 h-14 rounded-full flex items-center justify-center"
                :class="assessment.total_emissions_tco2e !== null
                  ? 'bg-emerald-50 dark:bg-emerald-900/20'
                  : 'bg-gray-100 dark:bg-gray-700'"
              >
                <span
                  class="text-lg font-bold"
                  :class="assessment.total_emissions_tco2e !== null
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-gray-400'"
                >
                  {{ assessment.total_emissions_tco2e !== null ? assessment.total_emissions_tco2e.toFixed(1) : '—' }}
                </span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-surface-text dark:text-surface-dark-text">
                    Bilan {{ assessment.year }}
                  </span>
                  <span
                    class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="statusColor(assessment.status)"
                  >
                    {{ statusLabel(assessment.status) }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {{ formatDate(assessment.created_at) }}
                  <span v-if="assessment.total_emissions_tco2e !== null">
                    &middot; {{ assessment.total_emissions_tco2e.toFixed(2) }} tCO2e
                  </span>
                </p>
              </div>
            </div>
            <NuxtLink
              v-if="assessment.status === 'completed'"
              :to="`/carbon/results?id=${assessment.id}`"
              class="inline-flex items-center gap-1 text-sm text-brand-green hover:underline"
            >
              Voir les resultats
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </NuxtLink>
            <NuxtLink
              v-else
              to="/chat"
              class="inline-flex items-center gap-1 text-sm text-amber-600 dark:text-amber-400 hover:underline"
            >
              Continuer
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </NuxtLink>
          </div>

          <!-- Mini barres de categories si completed -->
          <div
            v-if="assessment.status === 'completed' && assessment.completed_categories.length"
            class="flex gap-3 mt-4 pt-3 border-t border-gray-100 dark:border-dark-border/50"
          >
            <div
              v-for="cat in assessment.completed_categories"
              :key="cat"
              class="flex items-center gap-1.5"
            >
              <span
                class="w-2 h-2 rounded-full"
                :class="categoryColors[cat] ?? 'bg-gray-400'"
              />
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ categoryLabels[cat] ?? cat }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
