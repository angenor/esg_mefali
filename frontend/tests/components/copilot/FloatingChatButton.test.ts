import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FloatingChatButton from '~/components/copilot/FloatingChatButton.vue'
import { useUiStore } from '~/stores/ui'

describe('FloatingChatButton', () => {
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

  describe('Rendu initial (AC #1)', () => {
    it('affiche un bouton avec aria-label "Ouvrir l\'assistant IA" quand le widget est ferme', () => {
      const wrapper = mountButton()
      const button = wrapper.find('button')

      expect(button.exists()).toBe(true)
      expect(button.attributes('aria-label')).toBe('Ouvrir l\u2019assistant IA')
      expect(button.attributes('aria-expanded')).toBe('false')
    })

    it('affiche l\'icone chat (pas l\'icone X) quand le widget est ferme', () => {
      const wrapper = mountButton()
      const svgs = wrapper.findAll('svg')

      // Une seule SVG visible (icone chat)
      expect(svgs.length).toBe(1)
    })

    it('a les classes de positionnement fixed bottom-right z-50', () => {
      const wrapper = mountButton()
      const button = wrapper.find('button')

      expect(button.classes()).toContain('fixed')
      expect(button.classes()).toContain('bottom-6')
      expect(button.classes()).toContain('right-6')
      expect(button.classes()).toContain('z-50')
    })

    it('a la couleur bg-brand-green', () => {
      const wrapper = mountButton()
      const button = wrapper.find('button')

      expect(button.classes()).toContain('bg-brand-green')
      expect(button.classes()).toContain('text-white')
    })
  })

  describe('Toggle du widget (AC #2, #4)', () => {
    it('toggle chatWidgetOpen dans le store au clic', async () => {
      const wrapper = mountButton()
      const uiStore = useUiStore()

      expect(uiStore.chatWidgetOpen).toBe(false)

      await wrapper.find('button').trigger('click')
      expect(uiStore.chatWidgetOpen).toBe(true)

      await wrapper.find('button').trigger('click')
      expect(uiStore.chatWidgetOpen).toBe(false)
    })
  })

  describe('Etat visuel actif (AC #1)', () => {
    it('change aria-label quand le widget est ouvert', async () => {
      const wrapper = mountButton()
      const uiStore = useUiStore()

      uiStore.chatWidgetOpen = true
      await wrapper.vm.$nextTick()

      const button = wrapper.find('button')
      expect(button.attributes('aria-label')).toBe('Fermer l\u2019assistant IA')
    })

    it('affiche l\'icone X quand le widget est ouvert', async () => {
      const wrapper = mountButton()
      const uiStore = useUiStore()

      uiStore.chatWidgetOpen = true
      await wrapper.vm.$nextTick()

      // L'icone X utilise stroke (pas fill)
      const svg = wrapper.find('svg')
      expect(svg.attributes('stroke')).toBe('currentColor')
    })
  })

  describe('Dark mode (AC #5)', () => {
    it('inclut les classes shadow dark mode', () => {
      const wrapper = mountButton()
      const button = wrapper.find('button')
      const classes = button.classes().join(' ')

      expect(classes).toContain('shadow-lg')
      expect(classes).toContain('dark:shadow-dark-border/20')
    })
  })
})
