<script setup lang="ts">
import type { ActionItem, ActionItemCategory, ProgressByCategory } from '~/types/actionPlan'
import { useActionPlan } from '~/composables/useActionPlan'
import { useActionPlanStore } from '~/stores/actionPlan'

definePageMeta({ layout: 'default' })

const actionPlanStore = useActionPlanStore()
const { fetchPlan, fetchItems, updateItem, generatePlan, loading, error } = useActionPlan()

// État local
const selectedCategory = ref('')
const selectedItem = ref<ActionItem | null>(null)
const showActionCard = ref(false)
const generating = ref(false)
const selectedTimeframe = ref(12)

// Catégories pour le filtre
const categoryOptions = computed(() => {
  const progress = actionPlanStore.progress
  const categories: Array<{ value: string; label: string; icon: string; count: number }> = [
    { value: 'environment', label: 'Environnement', icon: '🌿', count: 0 },
    { value: 'social', label: 'Social', icon: '👥', count: 0 },
    { value: 'governance', label: 'Gouvernance', icon: '⚖️', count: 0 },
    { value: 'financing', label: 'Financement', icon: '💰', count: 0 },
    { value: 'carbon', label: 'Carbone', icon: '🌍', count: 0 },
    { value: 'intermediary_contact', label: 'Contacts intermédiaires', icon: '🏦', count: 0 },
  ]

  if (progress) {
    for (const cat of categories) {
      const catProgress = progress[cat.value]
      if (catProgress && typeof catProgress === 'object' && 'total' in catProgress) {
        cat.count = catProgress.total
      }
    }
  }

  return categories
})

// Progression par catégorie pour le ProgressBar
const progressByCategory = computed<Record<string, ProgressByCategory>>(() => {
  const result: Record<string, ProgressByCategory> = {}
  const progress = actionPlanStore.progress
  if (!progress) return result

  for (const [key, value] of Object.entries(progress)) {
    if (key !== 'global_percentage' && typeof value === 'object' && 'total' in value) {
      result[key] = value as ProgressByCategory
    }
  }
  return result
})

const globalPercentage = computed(() => {
  const progress = actionPlanStore.progress
  if (!progress) return actionPlanStore.completionPercentage
  return typeof progress.global_percentage === 'number' ? progress.global_percentage : 0
})

// Timeframe labels
const timeframeLabels: Record<number, string> = {
  6: '6 mois',
  12: '12 mois',
  24: '24 mois',
}

// Charger les données au montage
async function loadData() {
  const plan = await fetchPlan()
  if (plan) {
    await fetchItems(plan.id, {
      category: selectedCategory.value || undefined,
    })
  }
}

// Filtrer par catégorie
async function onCategorySelect(category: string) {
  selectedCategory.value = category
  const plan = actionPlanStore.plan
  if (plan) {
    await fetchItems(plan.id, {
      category: category || undefined,
    })
  }
}

// Sélectionner une action
function onSelectItem(item: ActionItem) {
  selectedItem.value = item
  showActionCard.value = true
}

// Mettre à jour le statut d'une action
async function onUpdateStatus(itemId: string, status: string) {
  const result = await updateItem(itemId, { status })
  if (result) {
    showActionCard.value = false
    selectedItem.value = null
    // Recharger les items pour rafraîchir les compteurs
    const plan = actionPlanStore.plan
    if (plan) {
      await fetchItems(plan.id, {
        category: selectedCategory.value || undefined,
      })
    }
  }
}

// Générer un nouveau plan
async function onGenerate() {
  generating.value = true
  const plan = await generatePlan(selectedTimeframe.value)
  generating.value = false
  if (plan) {
    await fetchItems(plan.id)
  }
}

onMounted(loadData)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6">
    <!-- En-tête -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-surface-text dark:text-surface-dark-text">
          Plan d'action
        </h1>
        <p
          v-if="actionPlanStore.plan"
          class="text-sm text-gray-500 dark:text-gray-400 mt-1"
        >
          {{ actionPlanStore.plan.title }} — {{ timeframeLabels[actionPlanStore.plan.timeframe] || actionPlanStore.plan.timeframe + ' mois' }}
        </p>
      </div>

      <!-- Bouton régénérer -->
      <div class="flex items-center gap-2">
        <select
          v-model="selectedTimeframe"
          class="text-sm px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text"
        >
          <option :value="6">6 mois</option>
          <option :value="12">12 mois</option>
          <option :value="24">24 mois</option>
        </select>
        <button
          class="px-4 py-2 bg-primary-500 text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="generating"
          @click="onGenerate"
        >
          {{ generating ? 'Génération...' : actionPlanStore.hasPlan ? 'Régénérer' : 'Générer un plan' }}
        </button>
      </div>
    </div>

    <!-- Erreur -->
    <div
      v-if="error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-sm text-red-700 dark:text-red-400"
    >
      {{ error }}
    </div>

    <!-- État vide (pas de plan) -->
    <div
      v-if="!actionPlanStore.hasPlan && !loading"
      class="text-center py-16 bg-white dark:bg-dark-card rounded-xl border border-gray-200 dark:border-dark-border"
    >
      <p class="text-4xl mb-4">📋</p>
      <h2 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text mb-2">
        Aucun plan d'action
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
        Générez votre plan d'action personnalisé pour obtenir des recommandations concrètes
        en matière d'ESG, de financement vert et de contacts avec les intermédiaires financiers.
      </p>
      <button
        class="px-6 py-2.5 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
        :disabled="generating"
        @click="onGenerate"
      >
        {{ generating ? 'Génération en cours...' : 'Générer mon plan d\'action' }}
      </button>
    </div>

    <!-- Contenu du plan -->
    <template v-if="actionPlanStore.hasPlan">
      <!-- Progression -->
      <ProgressBar
        :global-percentage="globalPercentage"
        :by-category="progressByCategory"
      />

      <!-- Filtre par catégorie -->
      <CategoryFilter
        :categories="categoryOptions"
        :selected="selectedCategory"
        @select="onCategorySelect"
      />

      <!-- Chargement -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>

      <!-- Timeline -->
      <Timeline
        v-else
        :items="actionPlanStore.items"
        data-guide-target="action-plan-timeline"
        @select="onSelectItem"
      />
    </template>

    <!-- Modal détail action -->
    <ActionCard
      v-if="selectedItem"
      :item="selectedItem"
      :show="showActionCard"
      @close="showActionCard = false; selectedItem = null"
      @update-status="onUpdateStatus"
    />
  </div>
</template>
