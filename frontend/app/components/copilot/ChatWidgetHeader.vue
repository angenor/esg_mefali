<script setup lang="ts">
defineProps<{
  title: string
  showBackButton: boolean
}>()

defineEmits<{
  close: []
  toggleHistory: []
  back: []
}>()
</script>

<template>
  <header class="flex items-center justify-between px-4 py-3 border-b border-gray-200/50 dark:border-dark-border/50">
    <!-- Bouton retour (visible uniquement en mode historique) — min-w pour eviter le decalage du titre (F7) -->
    <button
      v-if="showBackButton"
      type="button"
      class="p-1 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus:ring-2 focus:ring-brand-green min-w-8"
      aria-label="Retour à la conversation"
      @click="$emit('back')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
    </button>
    <div v-else class="min-w-8" aria-hidden="true" />

    <!-- Titre -->
    <h2 class="flex-1 text-sm font-semibold text-surface-text dark:text-surface-dark-text truncate">
      {{ title }}
    </h2>

    <!-- Bouton historique (masque en mode retour) -->
    <button
      v-if="!showBackButton"
      type="button"
      class="p-1 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus:ring-2 focus:ring-brand-green"
      aria-label="Historique des conversations"
      @click="$emit('toggleHistory')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
        <path d="M8 10h8M8 14h4" />
      </svg>
    </button>

    <!-- Bouton fermer -->
    <button
      type="button"
      class="p-1 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus:ring-2 focus:ring-brand-green"
      aria-label="Fermer l'assistant IA"
      @click="$emit('close')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </header>
</template>
