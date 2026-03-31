<script setup lang="ts">
defineProps<{
  identityCompletion: number
  esgCompletion: number
  overallCompletion: number
}>()

function progressColor(value: number): string {
  if (value >= 80) return 'bg-emerald-500'
  if (value >= 50) return 'bg-blue-500'
  if (value >= 25) return 'bg-amber-500'
  return 'bg-gray-400'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Complétion globale -->
    <div class="text-center">
      <div class="inline-flex items-center justify-center w-24 h-24 rounded-full border-4 transition-colors"
        :class="overallCompletion >= 80
          ? 'border-emerald-500 dark:border-emerald-400'
          : overallCompletion >= 50
            ? 'border-blue-500 dark:border-blue-400'
            : 'border-gray-300 dark:border-gray-600'"
      >
        <span class="text-2xl font-bold text-gray-900 dark:text-surface-dark-text">
          {{ Math.round(overallCompletion) }}%
        </span>
      </div>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Profil global
      </p>
    </div>

    <!-- Barres par catégorie -->
    <div class="space-y-3">
      <!-- Identité & Localisation -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Identité & Localisation
          </span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ Math.round(identityCompletion) }}%
          </span>
        </div>
        <div class="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="progressColor(identityCompletion)"
            :style="{ width: `${identityCompletion}%` }"
          />
        </div>
      </div>

      <!-- ESG -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Critères ESG
          </span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ Math.round(esgCompletion) }}%
          </span>
        </div>
        <div class="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="progressColor(esgCompletion)"
            :style="{ width: `${esgCompletion}%` }"
          />
        </div>
      </div>
    </div>

    <!-- Message d'encouragement -->
    <p class="text-sm text-center text-gray-500 dark:text-gray-400 italic">
      <template v-if="overallCompletion === 100">
        Bravo, votre profil est complet !
      </template>
      <template v-else-if="overallCompletion >= 70">
        Encore quelques champs pour un profil optimal.
      </template>
      <template v-else-if="overallCompletion >= 30">
        Bon debut ! Continuez a remplir votre profil.
      </template>
      <template v-else>
        Completez votre profil pour des conseils plus personnalises.
      </template>
    </p>
  </div>
</template>
