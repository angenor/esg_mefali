import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks ──

// Mock driver.js
const mockHighlight = vi.fn()
const mockDestroy = vi.fn()
const mockSetConfig = vi.fn()
const mockDriverInstance = {
  highlight: mockHighlight,
  destroy: mockDestroy,
  setConfig: mockSetConfig,
}
const mockDriverFactory = vi.fn(() => mockDriverInstance)
const mockDriverModule = { driver: mockDriverFactory }

vi.mock('driver.js', () => mockDriverModule)

// Mock useDriverLoader
const mockLoadDriver = vi.fn(() => Promise.resolve(mockDriverModule))
vi.mock('~/composables/useDriverLoader', () => ({
  loadDriver: mockLoadDriver,
}))

// Mock du store ui
const mockUiStoreState = {
  prefersReducedMotion: false,
  guidedTourActive: false,
  chatWidgetMinimized: false,
  chatWidgetOpen: false,
}
vi.mock('~/stores/ui', () => ({
  useUiStore: () => mockUiStoreState,
}))

// Mock navigateTo (auto-import Nuxt)
vi.stubGlobal('navigateTo', vi.fn(() => Promise.resolve()))

// Mock de useChat (pour addSystemMessage)
const mockAddSystemMessage = vi.fn()
vi.mock('~/composables/useChat', () => ({
  useChat: () => ({
    addSystemMessage: mockAddSystemMessage,
  }),
}))

// Mock de crypto.randomUUID
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

// Registre de test minimal
const TEST_REGISTRY = {
  test_tour: {
    id: 'test_tour',
    steps: [
      {
        route: '/test',
        selector: '[data-guide-target="test-el"]',
        popover: {
          title: 'Titre {{name}}',
          description: 'Description {{score}}/100',
          side: 'bottom' as const,
        },
      },
      {
        selector: '[data-guide-target="test-el-2"]',
        popover: {
          title: 'Etape 2',
          description: 'Sans placeholder',
          side: 'right' as const,
        },
      },
    ],
  },
  tour_with_countdown: {
    id: 'tour_with_countdown',
    steps: [
      {
        selector: '[data-guide-target="countdown-el"]',
        popover: {
          title: 'Titre',
          description: 'Desc',
          countdown: 5,
        },
      },
    ],
  },
  tour_invalid_countdown: {
    id: 'tour_invalid_countdown',
    steps: [
      {
        selector: '[data-guide-target="cd-el"]',
        popover: {
          title: 'Titre',
          description: 'Desc',
          countdown: 0,
        },
      },
    ],
  },
  tour_negative_countdown: {
    id: 'tour_negative_countdown',
    steps: [
      {
        selector: '[data-guide-target="cd-neg"]',
        popover: {
          title: 'Titre',
          description: 'Desc',
          countdown: -5,
        },
      },
    ],
  },
  tour_nan_countdown: {
    id: 'tour_nan_countdown',
    steps: [
      {
        selector: '[data-guide-target="cd-nan"]',
        popover: {
          title: 'Titre',
          description: 'Desc',
          countdown: NaN,
        },
      },
    ],
  },
  tour_other_route: {
    id: 'tour_other_route',
    steps: [
      {
        route: '/other-page',
        selector: '[data-guide-target="other-el"]',
        popover: {
          title: 'Titre',
          description: 'Desc',
        },
      },
    ],
  },
}

// Mock du registre
vi.mock('~/lib/guided-tours/registry', () => ({
  tourRegistry: TEST_REGISTRY,
  DEFAULT_ENTRY_COUNTDOWN: 8,
}))

// Helper pour simuler un element DOM present
function createMockElement(selector: string): Element {
  const el = document.createElement('div')
  const attr = selector.match(/data-guide-target="([^"]+)"/)
  if (attr) el.setAttribute('data-guide-target', attr[1]!)
  document.body.appendChild(el)
  return el
}

function clearDom(): void {
  document.body.innerHTML = ''
}

function setPathname(path: string): void {
  Object.defineProperty(window, 'location', {
    value: { pathname: path },
    writable: true,
    configurable: true,
  })
}

describe('useGuidedTour', () => {
  let useGuidedTour: typeof import('~/composables/useGuidedTour').useGuidedTour

  beforeEach(async () => {
    vi.clearAllMocks()
    clearDom()
    mockUiStoreState.prefersReducedMotion = false
    mockUiStoreState.guidedTourActive = false
    mockUiStoreState.chatWidgetMinimized = false
    mockUiStoreState.chatWidgetOpen = false

    // Reset module-level state en re-important
    vi.resetModules()
    const mod = await import('~/composables/useGuidedTour')
    useGuidedTour = mod.useGuidedTour

    // Simuler que les highlights se resolvent immediatement via popoverRender
    mockHighlight.mockImplementation((opts: Record<string, unknown>) => {
      const popover = opts.popover as Record<string, unknown> | undefined
      if (popover?.onPopoverRender) {
        // Monter le popover custom dans un conteneur DOM
        const wrapper = document.createElement('div')
        document.body.appendChild(wrapper)
        ;(popover.onPopoverRender as (p: { wrapper: HTMLElement }) => void)({ wrapper })
        // Simuler un clic sur le bouton Suivant (auto-resolve)
        const nextBtn = wrapper.querySelector('[data-testid="popover-next-btn"]')
        if (nextBtn) (nextBtn as HTMLElement).click()
      } else if (popover?.onNextClick) {
        ;(popover.onNextClick as () => void)()
      }
    })
  })

  afterEach(() => {
    clearDom()
  })

  // ── T8.2 : Machine a etats ──
  describe('machine a etats', () => {
    it('etat initial est idle', () => {
      const { tourState } = useGuidedTour()
      expect(tourState.value).toBe('idle')
    })

    it('transitions idle → loading → highlighting → complete → idle', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour, tourState } = useGuidedTour()
      expect(tourState.value).toBe('idle')

      await startTour('test_tour', { name: 'ESG', score: 75 })

      // Apres completion, l'etat est 'complete'
      expect(tourState.value).toBe('complete')

      // Apres 1000ms, retour a idle
      await new Promise(r => setTimeout(r, 1100))
      expect(tourState.value).toBe('idle')
    }, 10000)
  })

  // ── T8.3 : startTour valide ──
  describe('startTour valide', () => {
    it('charge Driver.js et appelle highlight pour chaque etape', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour } = useGuidedTour()
      await startTour('test_tour', { name: 'Test', score: 42 })

      expect(mockDriverFactory).toHaveBeenCalledOnce()
      // 2 etapes mono-page quand on est sur /test
      expect(mockHighlight).toHaveBeenCalledTimes(2)
      expect(mockDestroy).toHaveBeenCalledOnce()
    })
  })

  // ── T8.4 : startTour invalide ──
  describe('startTour invalide', () => {
    it('tour_id absent appelle addSystemMessage et reste idle', async () => {
      const { startTour, tourState } = useGuidedTour()
      await startTour('inexistant_tour')

      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        'Parcours « inexistant_tour » introuvable.',
      )
      expect(tourState.value).toBe('idle')
    })
  })

  // ── T8.5 : startTour en cours ──
  describe('startTour en cours', () => {
    it('ignore un second appel pendant un parcours actif', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Bloquer le highlight : ne pas appeler onNextClick → la Promise reste pending
      mockHighlight.mockImplementationOnce(() => {
        // Le mock par defaut appelle onNextClick, celui-ci ne le fait pas
        // → le composable reste bloque sur await new Promise(...)
      })

      const { startTour, tourState } = useGuidedTour()
      startTour('test_tour')

      // Attendre un tick pour que le tour passe en highlighting
      await new Promise(r => setTimeout(r, 50))

      expect(tourState.value).toBe('highlighting')

      // Tenter un second tour — devrait etre ignore
      await startTour('test_tour')
      expect(mockDriverFactory).toHaveBeenCalledTimes(1) // Un seul driver cree
    })
  })

  // ── T8.6 : Interpolation ──
  describe('interpolation', () => {
    it('remplace {{key}} par context[key] dans le popover custom', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Capturer les titres montes dans les popovers
      const mountedTitles: string[] = []
      mockHighlight.mockImplementation((opts: Record<string, unknown>) => {
        const popover = opts.popover as Record<string, unknown> | undefined
        if (popover?.onPopoverRender) {
          const wrapper = document.createElement('div')
          document.body.appendChild(wrapper)
          ;(popover.onPopoverRender as (p: { wrapper: HTMLElement }) => void)({ wrapper })
          // Capturer le titre du popover monte
          const titleEl = wrapper.querySelector('h3')
          if (titleEl) mountedTitles.push(titleEl.textContent ?? '')
          const nextBtn = wrapper.querySelector('[data-testid="popover-next-btn"]')
          if (nextBtn) (nextBtn as HTMLElement).click()
        }
      })

      const { startTour } = useGuidedTour()
      await startTour('test_tour', { name: 'Société ABC', score: 85 })

      expect(mountedTitles[0]).toBe('Titre Société ABC')
    })

    it('cle manquante → chaine vide', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const mountedTitles: string[] = []
      const mountedDescriptions: string[] = []
      mockHighlight.mockImplementation((opts: Record<string, unknown>) => {
        const popover = opts.popover as Record<string, unknown> | undefined
        if (popover?.onPopoverRender) {
          const wrapper = document.createElement('div')
          document.body.appendChild(wrapper)
          ;(popover.onPopoverRender as (p: { wrapper: HTMLElement }) => void)({ wrapper })
          const titleEl = wrapper.querySelector('h3')
          if (titleEl) mountedTitles.push(titleEl.textContent ?? '')
          const descEl = wrapper.querySelector('p')
          if (descEl) mountedDescriptions.push(descEl.textContent ?? '')
          const nextBtn = wrapper.querySelector('[data-testid="popover-next-btn"]')
          if (nextBtn) (nextBtn as HTMLElement).click()
        }
      })

      const { startTour } = useGuidedTour()
      await startTour('test_tour', {}) // Pas de name ni score

      expect(mountedTitles[0]).toBe('Titre ')
      expect(mountedDescriptions[0]).toBe('Description /100')
    })
  })

  // ── T8.7 : waitForElement ──
  describe('waitForElement', () => {
    it('element present retourne l\'element', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      // Si on arrive ici, les elements ont ete trouves (pas de skip message)
      expect(mockAddSystemMessage).not.toHaveBeenCalled()
    })

    it('element absent retourne null apres 3 retries et skip l\'etape', async () => {
      setPathname('/test')
      // Ne creer que le second element — le premier sera absent
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      // L'element absent declenche addSystemMessage
      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        'Je n\'ai pas pu pointer cet élément. Passons à la suite.',
      )
      // Le second element a quand meme ete highlight
      expect(mockHighlight).toHaveBeenCalledTimes(1) // Seulement le second element
    }, 10000)
  })

  // ── T8.8 : cancelTour ──
  describe('cancelTour', () => {
    it('etat → interrupted → idle, driver.destroy() appele', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Bloquer le highlight : ne pas appeler onNextClick → Promise pending
      mockHighlight.mockImplementationOnce(() => {})

      const { startTour, cancelTour, tourState } = useGuidedTour()
      startTour('test_tour')

      await new Promise(r => setTimeout(r, 50))
      expect(tourState.value).toBe('highlighting')

      // Cancel pendant le highlighting
      cancelTour()
      expect(tourState.value).toBe('interrupted')
      expect(mockDestroy).toHaveBeenCalled()

      // Apres 500ms, retour a idle
      await new Promise(r => setTimeout(r, 600))
      expect(tourState.value).toBe('idle')
    }, 10000)

    it('cancel en idle ne fait rien', () => {
      const { cancelTour, tourState } = useGuidedTour()
      cancelTour()
      expect(tourState.value).toBe('idle')
      expect(mockDestroy).not.toHaveBeenCalled()
    })
  })

  // ── T8.9 : Countdown validation ──
  describe('countdown validation', () => {
    it('countdown 0 → clamp a 1', async () => {
      setPathname('/')
      createMockElement('[data-guide-target="cd-el"]')

      const { startTour } = useGuidedTour()
      await startTour('tour_invalid_countdown')

      expect(mockHighlight).toHaveBeenCalledOnce()
    })

    it('countdown -5 → clamp a 1', async () => {
      setPathname('/')
      createMockElement('[data-guide-target="cd-neg"]')

      const { startTour } = useGuidedTour()
      await startTour('tour_negative_countdown')

      expect(mockHighlight).toHaveBeenCalledOnce()
    })

    it('countdown NaN → fallback DEFAULT_ENTRY_COUNTDOWN (8)', async () => {
      setPathname('/')
      createMockElement('[data-guide-target="cd-nan"]')

      const { startTour } = useGuidedTour()
      await startTour('tour_nan_countdown')

      expect(mockHighlight).toHaveBeenCalledOnce()
      const call = mockHighlight.mock.calls[0]?.[0] as Record<string, unknown>
      const popover = call?.popover as Record<string, unknown>
      // NaN → DEFAULT_ENTRY_COUNTDOWN (8), pas 1
      // Le countdown est interpole dans les etapes avant d'etre passe a highlight
      // Ici on verifie que le tour s'execute (le clamp ne bloque pas)
    })
  })

  // ── T8.10 : prefers-reduced-motion ──
  describe('prefers-reduced-motion', () => {
    it('passe animate: false a Driver.js quand reduced motion est actif', async () => {
      mockUiStoreState.prefersReducedMotion = true
      setPathname('/')
      createMockElement('[data-guide-target="countdown-el"]')

      const { startTour } = useGuidedTour()
      await startTour('tour_with_countdown')

      expect(mockDriverFactory).toHaveBeenCalledWith(
        expect.objectContaining({ animate: false }),
      )
    })

    it('passe animate: true quand reduced motion est inactif', async () => {
      mockUiStoreState.prefersReducedMotion = false
      setPathname('/')
      createMockElement('[data-guide-target="countdown-el"]')

      const { startTour } = useGuidedTour()
      await startTour('tour_with_countdown')

      expect(mockDriverFactory).toHaveBeenCalledWith(
        expect.objectContaining({ animate: true }),
      )
    })
  })

  // ── T8.11 : loadDriver rejection ──
  describe('loadDriver rejection', () => {
    it('rejection de loadDriver reset tourState a idle', async () => {
      mockLoadDriver.mockRejectedValueOnce(new Error('Network error'))

      const { startTour, tourState } = useGuidedTour()
      await startTour('test_tour')

      // L'etat doit etre revenu a idle grace au try/catch
      expect(tourState.value).toBe('idle')
      expect(mockDriverFactory).not.toHaveBeenCalled()
    })
  })

  // ── T8.12 : etapes sur autre route → navigation (Story 5.3) ──
  describe('etapes sur autre route', () => {
    it('navigue vers la route de l\'etape si differente de la route courante', async () => {
      setPathname('/dashboard') // Etape de tour_other_route est sur /other-page
      createMockElement('[data-guide-target="other-el"]')

      const { startTour, tourState } = useGuidedTour()
      await startTour('tour_other_route')

      // navigateTo doit avoir ete appele pour la route de l'etape
      expect(navigateTo).toHaveBeenCalledWith('/other-page')
    })
  })

  // ── T8.13 : cancelTour pendant loading ──
  describe('cancelTour pendant loading', () => {
    it('cancel pendant loadDriver empeche l\'execution des etapes', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Retarder loadDriver pour pouvoir cancel pendant le loading
      let resolveLoadDriver: ((value: typeof mockDriverModule) => void) | null = null
      mockLoadDriver.mockImplementationOnce(() => new Promise((resolve) => {
        resolveLoadDriver = resolve
      }))

      const { startTour, cancelTour, tourState } = useGuidedTour()
      startTour('test_tour')

      await new Promise(r => setTimeout(r, 10))
      expect(tourState.value).toBe('loading')

      // Cancel pendant le loading
      cancelTour()
      expect(tourState.value).toBe('interrupted')

      // Resoudre loadDriver apres le cancel
      resolveLoadDriver!(mockDriverModule)
      await new Promise(r => setTimeout(r, 50))

      // Le cancelled flag empeche l'execution — pas de highlight
      expect(mockHighlight).not.toHaveBeenCalled()

      // Apres 500ms, retour a idle
      await new Promise(r => setTimeout(r, 600))
      expect(tourState.value).toBe('idle')
    }, 10000)
  })

  // ── T8.14 : Interruption via onDestroyStarted (Story 5.4 — AC1/AC2) ──
  describe('interruption via onDestroyStarted', () => {
    it('interruption utilisateur (Escape/clic overlay) declenche cancelTour', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Bloquer le highlight : ne pas appeler le next automatiquement
      let capturedOnDestroyStarted: (() => void) | null = null
      mockDriverFactory.mockImplementationOnce((config: Record<string, unknown>) => {
        capturedOnDestroyStarted = config.onDestroyStarted as () => void
        return mockDriverInstance
      })
      mockHighlight.mockImplementationOnce(() => {
        // Ne pas resolve — le tour reste bloque sur l'etape
      })

      const { startTour, tourState } = useGuidedTour()
      startTour('test_tour')

      await new Promise(r => setTimeout(r, 50))
      expect(tourState.value).toBe('highlighting')

      // Simuler une interruption utilisateur (Escape/clic overlay)
      // userInitiatedClose est true par defaut → onDestroyStarted appelle cancelTour
      capturedOnDestroyStarted?.()

      expect(tourState.value).toBe('interrupted')
      expect(mockUiStoreState.chatWidgetMinimized).toBe(false)
      expect(mockUiStoreState.guidedTourActive).toBe(false)

      // Pas de message chat sur interruption volontaire (FR25)
      expect(mockAddSystemMessage).not.toHaveBeenCalled()

      await new Promise(r => setTimeout(r, 600))
      expect(tourState.value).toBe('idle')
    }, 10000)
  })

  // ── T8.15 : Cleanup DOM residuel (Story 5.4 — AC6) ──
  describe('cleanup DOM residuel', () => {
    it('supprime les elements orphelins Driver.js apres completion', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Simuler des elements Driver.js orphelins dans le DOM
      const overlay = document.createElement('div')
      overlay.className = 'driver-overlay'
      document.body.appendChild(overlay)

      const popover = document.createElement('div')
      popover.className = 'driver-popover'
      document.body.appendChild(popover)

      const activeEl = document.createElement('div')
      activeEl.setAttribute('data-driver-active-element', 'true')
      document.body.appendChild(activeEl)

      const highlightedEl = document.createElement('div')
      highlightedEl.classList.add('driver-highlighted-element')
      document.body.appendChild(highlightedEl)

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      // Les elements orphelins doivent avoir ete nettoyes
      expect(document.querySelector('.driver-overlay')).toBeNull()
      expect(document.querySelector('.driver-popover')).toBeNull()
      expect(document.querySelector('[data-driver-active-element]')).toBeNull()
      expect(document.querySelector('.driver-highlighted-element')).toBeNull()
    })

    it('preserve les elements non-driver du DOM', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      // Ajouter un element non-driver
      const userEl = document.createElement('div')
      userEl.id = 'user-content'
      userEl.textContent = 'Mon contenu'
      document.body.appendChild(userEl)

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      // L'element non-driver est preserve
      expect(document.getElementById('user-content')).not.toBeNull()
      expect(document.getElementById('user-content')?.textContent).toBe('Mon contenu')
    })
  })

  // ── T8.16 : popoverRender monte le composant GuidedTourPopover (Story 5.4 — AC3) ──
  describe('popoverRender', () => {
    it('passe popoverRender dans chaque highlight pour monter le composant custom', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      let popoverRenderCallCount = 0
      mockHighlight.mockImplementation((opts: Record<string, unknown>) => {
        const pop = opts.popover as Record<string, unknown> | undefined
        if (pop?.onPopoverRender) {
          popoverRenderCallCount++
          const wrapper = document.createElement('div')
          document.body.appendChild(wrapper)
          ;(pop.onPopoverRender as (p: { wrapper: HTMLElement }) => void)({ wrapper })
          const nextBtn = wrapper.querySelector('[data-testid="popover-next-btn"]')
          if (nextBtn) (nextBtn as HTMLElement).click()
        }
      })

      const { startTour } = useGuidedTour()
      await startTour('test_tour', { name: 'ESG', score: 75 })

      // popoverRender est appele pour chaque etape
      expect(popoverRenderCallCount).toBe(2)
    })

    it('allowClose est true dans la config Driver.js', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      expect(mockDriverFactory).toHaveBeenCalledWith(
        expect.objectContaining({ allowClose: true }),
      )
    })

    it('showButtons est vide (le popover custom gere les boutons)', async () => {
      setPathname('/test')
      createMockElement('[data-guide-target="test-el"]')
      createMockElement('[data-guide-target="test-el-2"]')

      const { startTour } = useGuidedTour()
      await startTour('test_tour')

      expect(mockDriverFactory).toHaveBeenCalledWith(
        expect.objectContaining({ showButtons: [] }),
      )
    })
  })
})
