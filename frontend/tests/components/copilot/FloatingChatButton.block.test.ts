import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FloatingChatButton from '~/components/copilot/FloatingChatButton.vue'
import { useUiStore } from '~/stores/ui'

describe('FloatingChatButton — blocage pendant guidage (Story 5.2)', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  function mountButton() {
    return mount(FloatingChatButton, {
      global: {
        plugins: [pinia],
      },
    })
  }

  it('clic pendant guidedTourActive = true ne toggle pas le widget', async () => {
    const wrapper = mountButton()
    const uiStore = useUiStore()

    uiStore.guidedTourActive = true

    await wrapper.find('button').trigger('click')
    expect(uiStore.chatWidgetOpen).toBe(false)
  })

  it('aria-disabled est present quand guidedTourActive = true', async () => {
    const wrapper = mountButton()
    const uiStore = useUiStore()

    uiStore.guidedTourActive = true
    await wrapper.vm.$nextTick()

    const button = wrapper.find('button')
    expect(button.attributes('aria-disabled')).toBe('true')
  })

  it('cursor-not-allowed et opacity-60 quand guidedTourActive = true', async () => {
    const wrapper = mountButton()
    const uiStore = useUiStore()

    uiStore.guidedTourActive = true
    await wrapper.vm.$nextTick()

    const button = wrapper.find('button')
    expect(button.classes()).toContain('cursor-not-allowed')
    expect(button.classes()).toContain('opacity-60')
  })

  it('clic normal quand guidedTourActive = false toggle le widget', async () => {
    const wrapper = mountButton()
    const uiStore = useUiStore()

    expect(uiStore.guidedTourActive).toBe(false)
    expect(uiStore.chatWidgetOpen).toBe(false)

    await wrapper.find('button').trigger('click')
    expect(uiStore.chatWidgetOpen).toBe(true)
  })

  it('aria-disabled est absent quand guidedTourActive = false', () => {
    const wrapper = mountButton()

    const button = wrapper.find('button')
    expect(button.attributes('aria-disabled')).toBeUndefined()
  })

  it('hover:scale-105 est present quand guidedTourActive = false', () => {
    const wrapper = mountButton()

    const button = wrapper.find('button')
    expect(button.classes()).toContain('hover:scale-105')
    expect(button.classes()).toContain('active:scale-95')
  })
})
