<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
import { useAuth } from '~/composables/useAuth'

const uiStore = useUiStore()
const { logout } = useAuth()

const navItems = [
  { label: 'Tableau de bord', to: '/', icon: 'dashboard' },
  { label: 'Chat IA', to: '/chat', icon: 'chat' },
]
</script>

<template>
  <aside
    class="bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border flex flex-col h-full transition-all duration-300"
    :class="uiStore.sidebarOpen ? 'w-56' : 'w-16'"
  >
    <!-- Logo -->
    <div class="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-dark-border">
      <span v-if="uiStore.sidebarOpen" class="text-lg font-bold text-brand-green">
        ESG Mefali
      </span>
      <span v-else class="text-lg font-bold text-brand-green mx-auto">
        E
      </span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4">
      <NuxtLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-hover hover:text-brand-green transition-colors"
        active-class="bg-emerald-50 dark:bg-emerald-900/20 text-brand-green font-medium border-r-2 border-brand-green"
      >
        <!-- Icone dashboard -->
        <svg v-if="item.icon === 'dashboard'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
        <!-- Icone chat -->
        <svg v-else-if="item.icon === 'chat'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
        </svg>
        <span v-if="uiStore.sidebarOpen">{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <!-- Bouton replier -->
    <div class="border-t border-gray-200 dark:border-dark-border p-3">
      <button
        class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-hover rounded-lg transition-colors"
        @click="uiStore.toggleSidebar"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4 h-4 transition-transform"
          :class="uiStore.sidebarOpen ? '' : 'rotate-180'"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="text-xs">Replier</span>
      </button>
    </div>

    <!-- Deconnexion -->
    <div class="border-t border-gray-200 dark:border-dark-border p-3">
      <button
        class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-brand-red hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
        @click="logout"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="text-xs">Deconnexion</span>
      </button>
    </div>
  </aside>
</template>
