<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
import { useAuthStore } from '~/stores/auth'

const uiStore = useUiStore()
const authStore = useAuthStore()
</script>

<template>
  <header class="h-14 bg-white dark:bg-dark-card border-b border-gray-200 dark:border-dark-border flex items-center justify-between px-4">
    <!-- Gauche : bouton menu mobile + titre -->
    <div class="flex items-center gap-3">
      <button
        class="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
        @click="uiStore.toggleSidebar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
        </svg>
      </button>
      <h2 class="text-sm font-medium text-surface-text dark:text-surface-dark-text hidden sm:block">
        Tableau de bord
      </h2>
    </div>

    <!-- Droite : toggle theme + toggle chat + utilisateur -->
    <div class="flex items-center gap-3">
      <!-- Toggle dark mode -->
      <button
        class="p-2 text-gray-500 dark:text-gray-400 hover:text-brand-purple hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
        :title="uiStore.theme === 'dark' ? 'Mode clair' : 'Mode sombre'"
        @click="uiStore.toggleTheme"
      >
        <!-- Soleil (mode clair) -->
        <svg v-if="uiStore.theme === 'dark'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
        </svg>
        <!-- Lune (mode sombre) -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      </button>

      <!-- Bouton ouvrir/fermer chat panel -->
      <button
        class="p-2 text-gray-500 dark:text-gray-400 hover:text-brand-green hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg transition-colors"
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
        <span class="text-sm text-gray-600 dark:text-gray-400 hidden md:block">
          {{ authStore.user.full_name }}
        </span>
      </div>
    </div>
  </header>
</template>
