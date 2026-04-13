import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref, defineComponent } from 'vue'
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

  it('masque le widget flottant sur mobile', () => {
    mockIsDesktop.value = false
    const wrapper = mountLayout()
    expect(wrapper.find('[data-testid="floating-chat-button"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="floating-chat-widget"]').exists()).toBe(false)
  })
})
