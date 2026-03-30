<script setup lang="ts">
import { useUiStore } from '~/stores/ui'

const uiStore = useUiStore()
</script>

<template>
  <div class="flex h-screen bg-surface-bg overflow-hidden">
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
</template>
