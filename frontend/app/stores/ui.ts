import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(true)
  const chatPanelOpen = ref(true)
  const theme = ref<'light' | 'dark'>('light')

  function initTheme() {
    if (import.meta.client) {
      const saved = localStorage.getItem('esg-theme')
      if (saved === 'dark' || saved === 'light') {
        theme.value = saved
      } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        theme.value = 'dark'
      }
      applyTheme()
    }
  }

  function applyTheme() {
    if (import.meta.client) {
      document.documentElement.classList.toggle('dark', theme.value === 'dark')
    }
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    if (import.meta.client) {
      localStorage.setItem('esg-theme', theme.value)
    }
    applyTheme()
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function toggleChatPanel() {
    chatPanelOpen.value = !chatPanelOpen.value
  }

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
    if (import.meta.client) {
      localStorage.setItem('esg-theme', newTheme)
    }
    applyTheme()
  }

  return {
    sidebarOpen,
    chatPanelOpen,
    theme,
    initTheme,
    toggleSidebar,
    toggleChatPanel,
    toggleTheme,
    setTheme,
  }
})
