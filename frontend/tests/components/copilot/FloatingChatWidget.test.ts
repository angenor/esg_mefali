import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { useUiStore } from '~/stores/ui'

// Mock GSAP
const mockFromTo = vi.fn()
const mockTo = vi.fn((_el: unknown, opts: Record<string, unknown>) => {
  if (typeof opts.onComplete === 'function') {
    ;(opts.onComplete as () => void)()
  }
})

vi.mock('gsap', () => ({
  gsap: {
    fromTo: (...args: unknown[]) => mockFromTo(...args),
    to: (...args: unknown[]) => mockTo(...args),
  },
}))

describe('FloatingChatWidget', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    mockFromTo.mockClear()
    mockTo.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  async function mountWidget() {
    const { default: Component } = await import('~/components/copilot/FloatingChatWidget.vue')
    return mount(Component, {
      global: {
        plugins: [pinia],
      },
    })
  }

  describe('Visibilite (AC #2, #4)', () => {
    it('le widget est cache par defaut (chatWidgetOpen = false)', async () => {
      const wrapper = await mountWidget()
      const widget = wrapper.find('.widget-glass')

      // v-show avec isVisible=false et chatWidgetOpen=false → display: none
      expect(widget.attributes('style')).toContain('display: none')
    })

    it('le widget devient visible quand chatWidgetOpen passe a true', async () => {
      const wrapper = await mountWidget()
      const uiStore = useUiStore()

      uiStore.chatWidgetOpen = true
      await nextTick()
      await nextTick()

      const widget = wrapper.find('.widget-glass')
      expect(widget.exists()).toBe(true)
      // chatWidgetOpen = true donc v-show condition est true
      expect(widget.attributes('style') || '').not.toContain('display: none')
    })
  })

  describe('Structure du widget (AC #2, #3)', () => {
    it('a les dimensions par defaut w-[400px] h-[600px]', async () => {
      const wrapper = await mountWidget()
      const widget = wrapper.find('.widget-glass')

      expect(widget.classes()).toContain('w-[400px]')
      expect(widget.classes()).toContain('h-[600px]')
    })

    it('a le positionnement fixed et z-50', async () => {
      const wrapper = await mountWidget()
      const widget = wrapper.find('.widget-glass')

      expect(widget.classes()).toContain('fixed')
      expect(widget.classes()).toContain('z-50')
      expect(widget.classes()).toContain('bottom-24')
      expect(widget.classes()).toContain('right-6')
    })

    it('a overflow-hidden et rounded-2xl', async () => {
      const wrapper = await mountWidget()
      const widget = wrapper.find('.widget-glass')

      expect(widget.classes()).toContain('overflow-hidden')
      expect(widget.classes()).toContain('rounded-2xl')
    })

    it('affiche le header temporaire avec titre "Assistant IA"', async () => {
      const wrapper = await mountWidget()
      const header = wrapper.find('h2')

      expect(header.text()).toBe('Assistant IA')
    })

    it('affiche le placeholder "Chat arrive en Story 1.5"', async () => {
      const wrapper = await mountWidget()
      const placeholder = wrapper.find('p')

      expect(placeholder.text()).toBe('Chat arrive en Story 1.5')
    })
  })

  describe('Fermeture via bouton X (AC #4)', () => {
    it('appelle closeChatWidget quand on clique sur le bouton X du header', async () => {
      const wrapper = await mountWidget()
      const uiStore = useUiStore()
      uiStore.chatWidgetOpen = true
      await nextTick()

      const closeButton = wrapper.find('button[aria-label="Fermer l\'assistant IA"]')
      expect(closeButton.exists()).toBe(true)

      await closeButton.trigger('click')
      expect(uiStore.chatWidgetOpen).toBe(false)
    })
  })

  describe('Glassmorphism et fallback (AC #3)', () => {
    it('le widget a la classe widget-glass pour le glassmorphism', async () => {
      const wrapper = await mountWidget()
      const widget = wrapper.find('.widget-glass')

      expect(widget.exists()).toBe(true)
    })
  })

  describe('Dark mode (AC #5)', () => {
    it('le header a les classes dark mode', async () => {
      const wrapper = await mountWidget()
      const header = wrapper.find('h2')

      expect(header.classes().join(' ')).toContain('dark:text-surface-dark-text')
    })

    it('le bouton fermer a les classes dark mode', async () => {
      const wrapper = await mountWidget()
      const closeButton = wrapper.find('button[aria-label="Fermer l\'assistant IA"]')

      expect(closeButton.classes().join(' ')).toContain('dark:text-gray-400')
      expect(closeButton.classes().join(' ')).toContain('dark:hover:bg-dark-hover')
    })
  })

  describe('prefers-reduced-motion (AC #6)', () => {
    it('utilise duration: 0 quand prefers-reduced-motion est actif', async () => {
      // Mocker matchMedia pour reduced motion avant import du composant
      const originalMatchMedia = window.matchMedia
      window.matchMedia = vi.fn((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        onchange: null,
        dispatchEvent: vi.fn(),
      })) as unknown as typeof window.matchMedia

      vi.resetModules()
      const { default: Component } = await import('~/components/copilot/FloatingChatWidget.vue')
      const wrapper = mount(Component, {
        global: { plugins: [pinia] },
      })
      const uiStore = useUiStore()

      uiStore.chatWidgetOpen = true
      await nextTick()
      await nextTick()

      expect(mockFromTo).toHaveBeenCalledWith(
        expect.any(Object),
        { scale: 0.8, opacity: 0, y: 20 },
        expect.objectContaining({ duration: 0 }),
      )

      window.matchMedia = originalMatchMedia
    })
  })

  describe('GSAP animations (AC #2, #4, #6)', () => {
    it('appelle gsap.fromTo a l\'ouverture du widget', async () => {
      const wrapper = await mountWidget()
      const uiStore = useUiStore()

      uiStore.chatWidgetOpen = true
      await nextTick()
      await nextTick()

      expect(mockFromTo).toHaveBeenCalledWith(
        expect.any(Object),
        { scale: 0.8, opacity: 0, y: 20 },
        expect.objectContaining({
          scale: 1,
          opacity: 1,
          y: 0,
          duration: 0.25,
          ease: 'power2.out',
        }),
      )
    })

    it('appelle gsap.to a la fermeture du widget', async () => {
      const wrapper = await mountWidget()
      const uiStore = useUiStore()

      // Ouvrir
      uiStore.chatWidgetOpen = true
      await nextTick()
      await nextTick()
      mockFromTo.mockClear()

      // Fermer
      uiStore.chatWidgetOpen = false
      await nextTick()
      await nextTick()

      expect(mockTo).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          scale: 0.8,
          opacity: 0,
          y: 20,
          duration: 0.2,
          ease: 'power2.in',
        }),
      )
    })
  })
})
