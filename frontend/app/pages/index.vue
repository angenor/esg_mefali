<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-surface-text dark:text-surface-dark-text mb-4">
      Tableau de bord
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      Bienvenue, {{ authStore.user?.full_name ?? 'utilisateur' }} !
    </p>
    <p class="text-gray-500 dark:text-gray-500 mt-2">
      {{ authStore.user?.company_name }}
    </p>

    <!-- Placeholder : les modules ESG seront ajoutes ici -->
    <div class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="bg-white dark:bg-dark-card rounded-xl shadow p-6 border border-gray-100 dark:border-dark-border">
        <h2 class="font-semibold text-surface-text dark:text-surface-dark-text">Analyse ESG</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Bientot disponible</p>
      </div>
      <div class="bg-white dark:bg-dark-card rounded-xl shadow p-6 border border-gray-100 dark:border-dark-border">
        <h2 class="font-semibold text-surface-text dark:text-surface-dark-text">Financement vert</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Bientot disponible</p>
      </div>
      <div class="bg-white dark:bg-dark-card rounded-xl shadow p-6 border border-gray-100 dark:border-dark-border">
        <h2 class="font-semibold text-surface-text dark:text-surface-dark-text">Empreinte carbone</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Bientot disponible</p>
      </div>
    </div>
  </div>
</template>
