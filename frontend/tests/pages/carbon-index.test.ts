import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useUiStore } from '~/stores/ui'

// Stub des auto-imports Vue/Nuxt
vi.stubGlobal('onMounted', onMounted)
vi.stubGlobal('computed', computed)
vi.stubGlobal('ref', ref)
vi.stubGlobal('definePageMeta', vi.fn())

import CarbonIndex from '~/pages/carbon/index.vue'

// Mock des composables
vi.mock('~/composables/useCarbon', () => ({
  useCarbon: () => ({
    fetchAssessments: vi.fn(),
    loading: ref(false),
    error: ref(null),
  }),
}))

// Stub NuxtLink
const NuxtLink = defineComponent({
  name: 'NuxtLink',
  props: ['to'],
  template: '<a :href="to"><slot /></a>',
})

describe('pages/carbon/index.vue — liens /chat remplaces (Story 2.2 — AC1)', () => {
  let uiStore: ReturnType<typeof useUiStore>

  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    uiStore = useUiStore()
  })

  function mountPage() {
    return mount(CarbonIndex, {
      global: {
        stubs: { NuxtLink },
      },
    })
  }

  it('ne contient aucun NuxtLink vers /chat dans le template', () => {
    const wrapper = mountPage()
    expect(wrapper.html()).not.toContain('href="/chat"')
  })

  it('le bouton "Nouveau bilan" ouvre le widget au clic', async () => {
    const wrapper = mountPage()
    const buttons = wrapper.findAll('button')
    const newBtn = buttons.find(b => b.text().includes('Nouveau bilan'))

    expect(newBtn).toBeDefined()
    expect(uiStore.chatWidgetOpen).toBe(false)

    await newBtn!.trigger('click')
    expect(uiStore.chatWidgetOpen).toBe(true)
  })

  it('le bouton "Demarrer dans le chat" ouvre le widget au clic (etat vide)', async () => {
    const { useCarbonStore } = await import('~/stores/carbon')
    const carbonStore = useCarbonStore()
    ;(carbonStore as any).assessments = []

    const wrapper = mountPage()
    const buttons = wrapper.findAll('button')
    const startBtn = buttons.find(b => b.text().includes('Demarrer dans le chat'))

    expect(startBtn).toBeDefined()
    expect(uiStore.chatWidgetOpen).toBe(false)

    await startBtn!.trigger('click')
    expect(uiStore.chatWidgetOpen).toBe(true)
  })
})
