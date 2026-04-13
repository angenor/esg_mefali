<script setup lang="ts">
import { watch } from 'vue'
import { useUiStore } from '~/stores/ui'
import { useDeviceDetection } from '~/composables/useDeviceDetection'

const uiStore = useUiStore()
const { isDesktop } = useDeviceDetection()
const route = useRoute()
const router = useRouter()

// D1 : reset le widget flottant quand on passe en mobile
watch(isDesktop, (desktop) => {
  if (!desktop) uiStore.closeChatWidget()
})

// Ouvrir le widget quand on arrive via la redirection /chat
if (import.meta.client) {
  watch(() => route.query.openChat, (val) => {
    if (val === '1') {
      uiStore.openChatWidget()
      const { openChat: _, ...rest } = route.query
      router.replace({ query: rest })
    }
  }, { immediate: true })
}
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

  </div>

  <!-- Widget flottant copilot (desktop uniquement) -->
  <template v-if="isDesktop">
    <FloatingChatButton />
    <FloatingChatWidget />
  </template>
</template>
