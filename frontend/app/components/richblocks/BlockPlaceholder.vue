<script setup lang="ts">
defineProps<{
  label?: string
}>()
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg border border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-card p-4">
    <div class="w-5 h-5 border-2 border-brand-green border-t-transparent rounded-full animate-spin" />
    <span class="text-sm text-gray-500 dark:text-gray-400">
      {{ label || 'Génération du graphique...' }}
    </span>
  </div>
</template>
