import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(true)
  const chatPanelOpen = ref(true)
  const conversationDrawerOpen = ref(false)
  const chatWidgetOpen = ref(false)
  const chatWidgetWidth = ref(400)
  const chatWidgetHeight = ref(600)
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

  function toggleConversationDrawer() {
    conversationDrawerOpen.value = !conversationDrawerOpen.value
  }

  function toggleChatWidget() {
    chatWidgetOpen.value = !chatWidgetOpen.value
  }

  function closeChatWidget() {
    chatWidgetOpen.value = false
  }

  const WIDGET_STORAGE_KEY = 'esg_mefali_widget_size'

  function initWidgetSize() {
    if (import.meta.client) {
      try {
        const saved = localStorage.getItem(WIDGET_STORAGE_KEY)
        if (saved) {
          const parsed = JSON.parse(saved)
          if (
            typeof parsed === 'object' && parsed !== null
            && typeof parsed.width === 'number' && typeof parsed.height === 'number'
          ) {
            chatWidgetWidth.value = parsed.width
            chatWidgetHeight.value = parsed.height
          }
        }
      } catch {
        // Donnees invalides — garder les defauts
      }
    }
  }

  function setChatWidgetSize(width: number, height: number) {
    chatWidgetWidth.value = width
    chatWidgetHeight.value = height
    if (import.meta.client) {
      localStorage.setItem(WIDGET_STORAGE_KEY, JSON.stringify({ width, height }))
    }
  }

  function resetChatWidgetSize() {
    chatWidgetWidth.value = 400
    chatWidgetHeight.value = 600
    if (import.meta.client) {
      localStorage.removeItem(WIDGET_STORAGE_KEY)
    }
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
    conversationDrawerOpen,
    chatWidgetOpen,
    chatWidgetWidth,
    chatWidgetHeight,
    theme,
    initTheme,
    initWidgetSize,
    setChatWidgetSize,
    resetChatWidgetSize,
    toggleSidebar,
    toggleChatPanel,
    toggleConversationDrawer,
    toggleChatWidget,
    closeChatWidget,
    toggleTheme,
    setTheme,
  }
})
