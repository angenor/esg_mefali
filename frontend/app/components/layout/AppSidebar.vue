<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
import { useAuth } from '~/composables/useAuth'
import { useCompanyStore } from '~/stores/company'
import { useCompanyProfile } from '~/composables/useCompanyProfile'

const uiStore = useUiStore()
const { logout } = useAuth()
const companyStore = useCompanyStore()
const { fetchCompletion } = useCompanyProfile()

const navItems = [
  { label: 'Tableau de bord', to: '/', icon: 'dashboard' },
  { label: 'Chat IA', to: '/chat', icon: 'chat' },
  { label: 'Evaluation ESG', to: '/esg', icon: 'esg' },
  { label: 'Empreinte Carbone', to: '/carbon', icon: 'carbon' },
  { label: 'Rapports', to: '/reports', icon: 'reports' },
  { label: 'Documents', to: '/documents', icon: 'documents' },
  { label: 'Profil', to: '/profile', icon: 'profile' },
]

const completionPct = computed(() => Math.round(companyStore.overallCompletion))

function completionColor(pct: number): string {
  if (pct >= 80) return 'bg-emerald-500 text-white'
  if (pct >= 50) return 'bg-blue-500 text-white'
  if (pct > 0) return 'bg-amber-500 text-white'
  return 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
}

// Charger la complétion au montage
onMounted(() => {
  fetchCompletion()
})
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
        <svg v-if="item.icon === 'dashboard'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
        <!-- Icone chat -->
        <svg v-else-if="item.icon === 'chat'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
        </svg>
        <!-- Icone ESG -->
        <svg v-else-if="item.icon === 'esg'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <!-- Icone carbone -->
        <svg v-else-if="item.icon === 'carbon'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clip-rule="evenodd" />
        </svg>
        <!-- Icone rapports -->
        <svg v-else-if="item.icon === 'reports'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z" clip-rule="evenodd" />
        </svg>
        <!-- Icone documents -->
        <svg v-else-if="item.icon === 'documents'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
        <!-- Icone profil -->
        <svg v-else-if="item.icon === 'profile'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2H4a1 1 0 010-2V4zm3 1h6v4H7V5zm6 6H7v2h6v-2z" clip-rule="evenodd" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="flex-1">{{ item.label }}</span>
        <!-- Badge complétion profil -->
        <span
          v-if="item.icon === 'profile' && uiStore.sidebarOpen && completionPct >= 0"
          class="text-xs font-medium px-1.5 py-0.5 rounded-full"
          :class="completionColor(completionPct)"
        >
          {{ completionPct }}%
        </span>
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
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="text-xs">Deconnexion</span>
      </button>
    </div>
  </aside>
</template>
