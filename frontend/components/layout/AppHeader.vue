<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
import { useAuthStore } from '~/stores/auth'

const uiStore = useUiStore()
const authStore = useAuthStore()
</script>

<template>
  <header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4">
    <!-- Gauche : bouton menu mobile + titre -->
    <div class="flex items-center gap-3">
      <button
        class="lg:hidden text-gray-500 hover:text-gray-700"
        @click="uiStore.toggleSidebar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
        </svg>
      </button>
      <h2 class="text-sm font-medium text-surface-text hidden sm:block">
        Tableau de bord
      </h2>
    </div>

    <!-- Droite : utilisateur + toggle chat -->
    <div class="flex items-center gap-3">
      <!-- Bouton ouvrir/fermer chat panel -->
      <button
        class="p-2 text-gray-500 hover:text-brand-green hover:bg-emerald-50 rounded-lg transition-colors"
        :title="uiStore.chatPanelOpen ? 'Fermer le chat' : 'Ouvrir le chat'"
        @click="uiStore.toggleChatPanel"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
        </svg>
      </button>

      <!-- Info utilisateur -->
      <div v-if="authStore.user" class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-brand-green flex items-center justify-center text-white text-xs font-bold">
          {{ authStore.user.full_name.charAt(0).toUpperCase() }}
        </div>
        <span class="text-sm text-gray-600 hidden md:block">
          {{ authStore.user.full_name }}
        </span>
      </div>
    </div>
  </header>
</template>
