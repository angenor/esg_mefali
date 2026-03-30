import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(true)
  const chatPanelOpen = ref(true)
  const theme = ref<'light' | 'dark'>('light')

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function toggleChatPanel() {
    chatPanelOpen.value = !chatPanelOpen.value
  }

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
  }

  return {
    sidebarOpen,
    chatPanelOpen,
    theme,
    toggleSidebar,
    toggleChatPanel,
    setTheme,
  }
})
