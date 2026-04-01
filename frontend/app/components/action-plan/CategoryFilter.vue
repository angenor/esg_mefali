<script setup lang="ts">
import type { ActionItemCategory } from '~/types/actionPlan'

interface CategoryOption {
  value: string
  label: string
  icon: string
  count: number
}

interface Props {
  categories: CategoryOption[]
  selected: string
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'select', category: string): void
}>()
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <!-- Bouton "Tous" -->
    <button
      :class="[
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border',
        selected === ''
          ? 'bg-primary-500 text-white border-primary-500'
          : 'bg-white dark:bg-dark-card border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-hover',
      ]"
      @click="emit('select', '')"
    >
      Tous
    </button>

    <!-- Boutons par catégorie -->
    <button
      v-for="cat in categories"
      :key="cat.value"
      :class="[
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border flex items-center gap-1.5',
        selected === cat.value
          ? 'bg-primary-500 text-white border-primary-500'
          : 'bg-white dark:bg-dark-card border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-hover',
      ]"
      @click="emit('select', cat.value)"
    >
      <span>{{ cat.icon }}</span>
      <span>{{ cat.label }}</span>
      <span
        v-if="cat.count > 0"
        :class="[
          'text-xs px-1.5 py-0.5 rounded-full',
          selected === cat.value
            ? 'bg-white/20 text-white'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
        ]"
      >
        {{ cat.count }}
      </span>
    </button>
  </div>
</template>
