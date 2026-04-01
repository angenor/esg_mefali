<script setup lang="ts">
import type { ProgressByCategory, ActionItemCategory } from '~/types/actionPlan'

interface Props {
  globalPercentage: number
  byCategory: Record<string, ProgressByCategory>
}

defineProps<Props>()

const categoryLabels: Record<string, { label: string; color: string; bgColor: string }> = {
  environment: { label: 'Environnement', color: 'bg-green-500', bgColor: 'bg-green-100 dark:bg-green-900/30' },
  social: { label: 'Social', color: 'bg-purple-500', bgColor: 'bg-purple-100 dark:bg-purple-900/30' },
  governance: { label: 'Gouvernance', color: 'bg-blue-500', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  financing: { label: 'Financement', color: 'bg-amber-500', bgColor: 'bg-amber-100 dark:bg-amber-900/30' },
  carbon: { label: 'Carbone', color: 'bg-teal-500', bgColor: 'bg-teal-100 dark:bg-teal-900/30' },
  intermediary_contact: { label: 'Contacts intermédiaires', color: 'bg-indigo-500', bgColor: 'bg-indigo-100 dark:bg-indigo-900/30' },
}
</script>

<template>
  <div class="bg-white dark:bg-dark-card rounded-xl border border-gray-200 dark:border-dark-border p-5">
    <!-- Barre de progression globale -->
    <div class="mb-5">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-surface-text dark:text-surface-dark-text">
          Progression globale
        </span>
        <span class="text-sm font-bold text-primary-600 dark:text-primary-400">
          {{ globalPercentage }}%
        </span>
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          class="h-3 rounded-full bg-primary-500 transition-all duration-500"
          :style="{ width: `${globalPercentage}%` }"
        />
      </div>
    </div>

    <!-- Barres par catégorie -->
    <div class="space-y-3">
      <div
        v-for="(catInfo, key) in categoryLabels"
        :key="key"
        class="flex items-center gap-3"
      >
        <span class="text-xs text-gray-500 dark:text-gray-400 w-32 truncate">
          {{ catInfo.label }}
        </span>
        <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            :class="['h-2 rounded-full transition-all duration-500', catInfo.color]"
            :style="{ width: `${byCategory[key]?.percentage ?? 0}%` }"
          />
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500 w-16 text-right">
          {{ byCategory[key]?.completed ?? 0 }}/{{ byCategory[key]?.total ?? 0 }}
        </span>
      </div>
    </div>
  </div>
</template>
