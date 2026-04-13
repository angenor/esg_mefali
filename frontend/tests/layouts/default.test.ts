import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref, defineComponent, watch, nextTick } from 'vue'

// Stub des auto-imports Nuxt (useRoute, useRouter, watch)
const mockRoute = ref({ query: {}, path: '/' })
vi.stubGlobal('useRoute', () => mockRoute.value)
vi.stubGlobal('useRouter', () => ({
  replace: vi.fn(),
}))
vi.stubGlobal('watch', watch)

import DefaultLayout from '~/layouts/default.vue'

// Stubs pour les composants auto-importes Nuxt
const AppSidebar = defineComponent({ name: 'AppSidebar', template: '<div data-testid="app-sidebar" />' })
const AppHeader = defineComponent({ name: 'AppHeader', template: '<div data-testid="app-header" />' })
const FloatingChatButton = defineComponent({ name: 'FloatingChatButton', template: '<div data-testid="floating-chat-button" />' })
const FloatingChatWidget = defineComponent({ name: 'FloatingChatWidget', template: '<div data-testid="floating-chat-widget" />' })

// Mock useDeviceDetection
const mockIsDesktop = ref(true)
vi.mock('~/composables/useDeviceDetection', () => ({
  useDeviceDetection: () => ({ isDesktop: mockIsDesktop }),
}))

describe('Layout default.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockIsDesktop.value = true
    mockRoute.value = { query: {}, path: '/' }
  })

  function mountLayout() {
    return mount(DefaultLayout, {
      global: {
        stubs: {
          AppSidebar,
          AppHeader,
          FloatingChatButton,
          FloatingChatWidget,
        },
      },
      slots: {
        default: '<div data-testid="slot-content">contenu</div>',
      },
    })
  }

  it('monte FloatingChatButton et FloatingChatWidget sur desktop', () => {
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="floating-chat-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="floating-chat-widget"]').exists()).toBe(true)
  })

  it('ne monte PAS ChatPanel (composant supprime)', () => {
    const wrapper = mountLayout()
    // ChatPanel ne doit pas exister dans le template
    expect(wrapper.html()).not.toContain('ChatPanel')
    expect(wrapper.html()).not.toContain('chat-panel')
  })

  it('monte AppSidebar et AppHeader', () => {
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="app-sidebar"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="app-header"]').exists()).toBe(true)
  })

  it('rend le slot de contenu principal', () => {
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="slot-content"]').exists()).toBe(true)
  })

  it('ouvre le widget quand openChat=1 est dans le query', async () => {
    const { useUiStore } = await import('~/stores/ui')
    const uiStore = useUiStore()
    const mockReplace = vi.fn()
    vi.stubGlobal('useRouter', () => ({ replace: mockReplace }))

    mockRoute.value = { query: { openChat: '1' }, path: '/' }
    mountLayout()

    // Le watcher immediate devrait avoir declenche l'ouverture
    expect(uiStore.chatWidgetOpen).toBe(true)
    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
  })

  it('ne reagit pas si openChat est absent du query', async () => {
    const { useUiStore } = await import('~/stores/ui')
    const uiStore = useUiStore()

    mockRoute.value = { query: {}, path: '/' }
    mountLayout()

    expect(uiStore.chatWidgetOpen).toBe(false)
  })

  it('met a jour uiStore.currentPage au mount (Story 3.1)', async () => {
    const { useUiStore } = await import('~/stores/ui')
    const uiStore = useUiStore()

    mockRoute.value = { query: {}, path: '/dashboard' }
    mountLayout()

    // Le watcher immediate devrait avoir mis a jour currentPage
    expect(uiStore.currentPage).toBe('/dashboard')
  })

  it('met a jour uiStore.currentPage quand la route change (Story 3.1)', async () => {
    const { useUiStore } = await import('~/stores/ui')
    const uiStore = useUiStore()

    // Monter avec une route initiale
    mockRoute.value = { query: {}, path: '/dashboard' }
    mountLayout()
    expect(uiStore.currentPage).toBe('/dashboard')

    // Simuler un changement de route — on modifie path sur le meme objet reactif
    mockRoute.value.path = '/carbon/results'
    await nextTick()

    expect(uiStore.currentPage).toBe('/carbon/results')
  })

  it('masque le widget flottant sur mobile', () => {
    mockIsDesktop.value = false
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="floating-chat-button"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="floating-chat-widget"]').exists()).toBe(false)
  })
})
