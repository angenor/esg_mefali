<script setup lang="ts">
defineProps<{
  error: {
    statusCode: number
    statusMessage?: string
    message: string
  }
}>()

const handleError = () => clearError({ redirect: '/' })
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-bg dark:bg-surface-dark-bg px-4">
    <div class="text-center">
      <p class="text-8xl font-bold text-brand-green mb-4">
        {{ error.statusCode }}
      </p>
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-surface-dark-text mb-2">
        {{ error.statusCode === 404 ? 'Page introuvable' : 'Une erreur est survenue' }}
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
        {{
          error.statusCode === 404
            ? "La page que vous recherchez n'existe pas ou a été déplacée."
            : error.statusMessage || "Quelque chose s'est mal passé."
        }}
      </p>
      <button
        type="button"
        class="px-6 py-3 bg-brand-green text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors"
        @click="handleError"
      >
        Retour à l'accueil
      </button>
    </div>
  </div>
</template>
