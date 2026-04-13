<script setup lang="ts">
import { useCreditScore } from '~/composables/useCreditScore'
import { useCreditScoreStore } from '~/stores/creditScore'

definePageMeta({ layout: 'default' })

const store = useCreditScoreStore()
const { fetchScore, fetchBreakdown, fetchHistory, generateScore, downloadCertificate, loading, error } = useCreditScore()

const generating = computed(() => store.generating)

// Labels francais pour les niveaux de confiance
const confidenceLabels: Record<string, string> = {
  very_low: 'Tres faible',
  low: 'Faible',
  medium: 'Moyen',
  good: 'Bon',
  excellent: 'Excellent',
}

function confidenceColor(label: string): string {
  if (label === 'excellent' || label === 'good') return 'text-emerald-600 dark:text-emerald-400'
  if (label === 'medium') return 'text-blue-600 dark:text-blue-400'
  return 'text-amber-600 dark:text-amber-400'
}

async function handleGenerate() {
  const result = await generateScore()
  if (result) {
    await Promise.all([fetchBreakdown(), fetchHistory()])
  }
}

// Charger les donnees au montage
onMounted(async () => {
  await fetchScore()
  if (store.hasScore) {
    await Promise.all([fetchBreakdown(), fetchHistory()])
  }
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="border-b border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">Score de Credit Vert</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Score hybride combinant solvabilite et impact vert
          </p>
        </div>
        <button
          class="px-4 py-2 bg-brand-green text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          :disabled="generating"
          @click="handleGenerate"
        >
          <span v-if="generating" class="flex items-center gap-2">
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generation...
          </span>
          <span v-else>{{ store.hasScore ? 'Regenerer le score' : 'Generer mon score' }}</span>
        </button>
      </div>
    </div>

    <!-- Contenu -->
    <div class="flex-1 overflow-y-auto p-6">
      <!-- Loading -->
      <div v-if="store.loading && !store.hasScore" class="flex items-center justify-center py-20">
        <svg class="animate-spin h-8 w-8 text-brand-green" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Erreur -->
      <div v-else-if="error" class="max-w-2xl mx-auto py-10">
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <p class="text-red-600 dark:text-red-400">{{ error }}</p>
          <button
            class="mt-4 px-4 py-2 text-sm bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700"
            @click="fetchScore()"
          >
            Reessayer
          </button>
        </div>
      </div>

      <!-- Etat vide -->
      <div v-else-if="!store.hasScore" class="max-w-xl mx-auto py-16 text-center">
        <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-8">
          <svg class="mx-auto w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <h2 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Pas encore de score
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
            Generez votre premier score de credit vert pour decouvrir votre profil
            de solvabilite et d'impact environnemental.
          </p>
          <button
            class="px-6 py-2.5 bg-brand-green text-white rounded-lg hover:bg-emerald-600 transition-colors font-medium"
            :disabled="generating"
            @click="handleGenerate"
          >
            Generer mon score
          </button>
        </div>
      </div>

      <!-- Resultats -->
      <div v-else class="max-w-4xl mx-auto space-y-6">
        <!-- Score expire -->
        <div v-if="store.isExpired" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-center gap-3">
          <span class="text-amber-500 text-xl">⚠️</span>
          <div class="flex-1">
            <p class="text-sm font-medium text-amber-800 dark:text-amber-300">Score expire</p>
            <p class="text-xs text-amber-600 dark:text-amber-400">Regenerez votre score pour obtenir une evaluation a jour.</p>
          </div>
          <button
            class="px-3 py-1.5 text-xs bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-200 rounded-lg hover:bg-amber-200"
            @click="handleGenerate"
          >
            Regenerer
          </button>
        </div>

        <!-- Score global -->
        <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6" data-guide-target="credit-score-gauge">
          <div class="text-center">
            <ScoreGauge :score="store.score!.combined_score" label="Score Credit Vert Combine" />
          </div>

          <!-- Confiance -->
          <div class="mt-4 text-center">
            <span class="text-sm text-gray-500 dark:text-gray-400">
              Confiance :
            </span>
            <span
              class="text-sm font-semibold"
              :class="confidenceColor(store.score!.confidence_label)"
            >
              {{ confidenceLabels[store.score!.confidence_label] ?? store.score!.confidence_label }}
              ({{ Math.round(store.score!.confidence_level * 100) }}%)
            </span>
          </div>

          <!-- Version et validite -->
          <div class="mt-3 flex items-center justify-center gap-4 text-xs text-gray-400 dark:text-gray-500">
            <span>Version {{ store.score!.version }}</span>
            <span>|</span>
            <span>Genere le {{ new Date(store.score!.generated_at).toLocaleDateString('fr-FR') }}</span>
            <span>|</span>
            <span>Valide jusqu'au {{ new Date(store.score!.valid_until).toLocaleDateString('fr-FR') }}</span>
          </div>
        </div>

        <!-- Sous-scores -->
        <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Sous-scores</h2>
          <SubScoreGauges
            :solvability-score="store.score!.solvability_score"
            :green-impact-score="store.score!.green_impact_score"
          />
        </div>

        <!-- Radars -->
        <div v-if="store.breakdown" class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Facteurs de solvabilite</h3>
            <FactorsRadar
              :factors="store.breakdown.score_breakdown.solvability.factors"
              axis="solvability"
            />
          </div>
          <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Facteurs d'impact vert</h3>
            <FactorsRadar
              :factors="store.breakdown.score_breakdown.green_impact.factors"
              axis="green_impact"
            />
          </div>
        </div>

        <!-- Couverture des sources -->
        <div v-if="store.breakdown" class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Couverture des sources</h2>
          <DataCoverage
            :sources="store.breakdown.data_sources.sources"
            :overall-coverage="store.breakdown.data_sources.overall_coverage"
          />
        </div>

        <!-- Recommandations -->
        <div v-if="store.breakdown && store.breakdown.recommendations.length > 0" class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Recommandations</h2>
          <Recommendations :recommendations="store.breakdown.recommendations" />
        </div>

        <!-- Historique -->
        <div v-if="store.hasHistory" class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-4">
            Evolution du score
            <span class="text-xs font-normal text-gray-400 dark:text-gray-500 ml-2">
              {{ store.historyTotal }} version(s)
            </span>
          </h2>
          <ScoreHistory :history="store.history" />
        </div>
        <div v-else-if="store.hasScore" class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Historique des scores</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Un seul score disponible. Regenerez votre score pour suivre son evolution.
          </p>
        </div>

        <!-- Bouton attestation -->
        <div v-if="store.hasScore && !store.isExpired" class="bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl p-6 text-center">
          <CertificateButton
            :loading="loading"
            @download="downloadCertificate"
          />
        </div>
      </div>
    </div>
  </div>
</template>
