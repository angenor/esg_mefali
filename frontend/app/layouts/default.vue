<script setup lang="ts">
import { useUiStore } from '~/stores/ui'
import { useDeviceDetection } from '~/composables/useDeviceDetection'

const uiStore = useUiStore()
const { isDesktop } = useDeviceDetection()
</script>

<template>
  <div class="flex h-screen bg-surface-bg dark:bg-surface-dark-bg overflow-hidden">
    <!-- Sidebar navigation -->
    <AppSidebar class="hidden lg:flex" />

    <!-- Contenu principal -->
    <div class="flex-1 flex flex-col min-w-0">
      <AppHeader />
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>

    <!-- Panneau chat IA -->
    <ChatPanel />
  </div>

  <!-- Widget flottant copilot (desktop uniquement) -->
  <template v-if="isDesktop">
    <FloatingChatButton />
    <FloatingChatWidget />
  </template>
</template>
