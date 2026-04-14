import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks driver.js ──
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

// Mock useDriverLoader (controlable par test pour simuler loadDriver rejection AC4)
const mockLoadDriver = vi.fn(() => Promise.resolve(mockDriverModule))
vi.mock('~/composables/useDriverLoader', () => ({
  loadDriver: mockLoadDriver,
}))

// Mock du store ui
const mockUiStore = {
  prefersReducedMotion: false,
  guidedTourActive: false,
  chatWidgetMinimized: false,
  chatWidgetOpen: false,
}
vi.mock('~/stores/ui', () => ({
  useUiStore: () => mockUiStore,
}))

// Mock de useChat (l'appel se fait via import dynamique → vi.mock intercepte)
const mockAddSystemMessage = vi.fn()
vi.mock('~/composables/useChat', () => ({
  useChat: () => ({
    addSystemMessage: mockAddSystemMessage,
  }),
}))

// Mock navigateTo (auto-import Nuxt)
const mockNavigateTo = vi.fn(() => Promise.resolve())
vi.stubGlobal('navigateTo', mockNavigateTo)

// Mock crypto.randomUUID
vi.stubGlobal('crypto', {
  randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8),
})

// ── Registres de test ──

const MOCK_REGISTRY = {
  // Tour mono-page (pas de route) — pour tester waitForElement et skip gracieux
  tour_mono: {
    id: 'tour_mono',
    steps: [
      {
        selector: '[data-guide-target="absent-el"]',
        popover: {
          title: 'Etape 1',
          description: 'Desc 1',
          side: 'bottom' as const,
        },
      },
    ],
  },
  // Tour mono-page multi-steps — pour tester plusieurs skips consecutifs
  tour_mono_multi: {
    id: 'tour_mono_multi',
    steps: [
      {
        selector: '[data-guide-target="absent-1"]',
        popover: { title: 'S1', description: 'D1', side: 'bottom' as const },
      },
      {
        selector: '[data-guide-target="absent-2"]',
        popover: { title: 'S2', description: 'D2', side: 'bottom' as const },
      },
      {
        selector: '[data-guide-target="absent-3"]',
        popover: { title: 'S3', description: 'D3', side: 'bottom' as const },
      },
    ],
  },
  // Tour multi-pages — pour tester soft retry + hard timeout
  tour_multi_page: {
    id: 'tour_multi_page',
    steps: [
      {
        route: '/esg/results',
        selector: '[data-guide-target="page-el"]',
        popover: { title: 'Page', description: 'Desc', side: 'bottom' as const },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-link"]',
      popover: {
        title: 'Entry',
        description: 'Entry desc',
        countdown: 3,
      },
      targetRoute: '/esg/results',
    },
  },
}

vi.mock('~/lib/guided-tours/registry', () => ({
  tourRegistry: MOCK_REGISTRY,
  DEFAULT_ENTRY_COUNTDOWN: 8,
}))

// ── Controle du pathname ──
let currentPathname = '/home'
vi.stubGlobal('location', {
  get pathname() {
    return currentPathname
  },
})

// ── Controle de document.querySelector ──
// Strategie : whitelist de selectors presents, tout le reste → null
let presentSelectors = new Set<string>()

function makeElement(selector: string): Element {
  const el = document.createElement('div')
  el.setAttribute('data-mock-selector', selector)
  return el
}

const realQuerySelector = document.querySelector.bind(document)
vi.spyOn(document, 'querySelector').mockImplementation((selector: string) => {
  if (presentSelectors.has(selector)) return makeElement(selector)
  // Fallback pour les selectors internes a Driver.js (.driver-popover, etc.)
  if (selector.startsWith('.driver-') || selector.startsWith('[data-driver-')) {
    return realQuerySelector(selector)
  }
  return null
})

// Meme strategie pour querySelectorAll (utilise par cleanupDriverResiduals)
// Whitelist les selectors Driver.js pour ne pas masquer la couverture du cleanup (review 7.1 / B6)
const realQuerySelectorAll = document.querySelectorAll.bind(document)
vi.spyOn(document, 'querySelectorAll').mockImplementation((selector: string) => {
  if (selector.startsWith('.driver-') || selector.startsWith('[data-driver-')) {
    return realQuerySelectorAll(selector)
  }
  return [] as unknown as NodeListOf<Element>
})

/**
 * Helper : resout un highlight en simulant la mini-app Vue du popover
 * (onPopoverRender appele → on clique "Suivant" via onCountdownExpired)
 */
function autoResolveHighlight(config: { popover?: { onPopoverRender?: (arg: { wrapper: HTMLElement }) => void } }): void {
  const popover = config?.popover
  if (popover?.onPopoverRender) {
    const wrapper = document.createElement('div')
    document.body.appendChild(wrapper)
    popover.onPopoverRender({ wrapper })
  }
}

describe('useGuidedTour — resilience (story 7.1)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    presentSelectors = new Set()
    currentPathname = '/home'
    mockHighlight.mockReset()
    mockDestroy.mockReset()
    mockSetConfig.mockReset()
    mockDriverFactory.mockClear()
    mockDriverFactory.mockReturnValue(mockDriverInstance)
    mockAddSystemMessage.mockClear()
    mockNavigateTo.mockClear()
    mockLoadDriver.mockReset()
    mockLoadDriver.mockImplementation(() => Promise.resolve(mockDriverModule))
    mockUiStore.chatWidgetMinimized = false
    mockUiStore.guidedTourActive = false
    mockUiStore.chatWidgetOpen = false
  })

  afterEach(async () => {
    vi.useRealTimers()
    vi.resetModules()
  })

  async function importFresh() {
    const mod = await import('~/composables/useGuidedTour')
    return mod.useGuidedTour()
  }

  // ═════════════════════════════════════════════════════════════════
  // Bloc 1 : waitForElement retry + cancelled (AC1, AC5)
  // ═════════════════════════════════════════════════════════════════

  describe('Bloc 1 — waitForElement retry + cancelled', () => {
    it('resolves immediately when element is present on first try', async () => {
      // L'element est present des l'entree → pas de retry, pas de skip message
      presentSelectors.add('[data-guide-target="absent-el"]')

      // Highlight resout immediatement via popoverRender + onCountdownExpired
      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        // Appeler onCountdownExpired pour resoudre le highlight
        setTimeout(() => {
          const popover = config?.popover as { onPopoverRender?: (arg: { wrapper: HTMLElement }) => void }
          if (popover?.onPopoverRender) {
            const wrapper = document.createElement('div')
            popover.onPopoverRender({ wrapper })
          }
          // Simuler clic "suivant"
        }, 10)
      })

      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(20)
      // Force la resolution du highlight (le popover custom doit appeler onNext/onCountdownExpired,
      // mais comme on ne peut pas reellement monter le composant, on se contente de verifier le non-skip)
      await vi.advanceTimersByTimeAsync(2000)

      // Pas de message skip car l'element etait present
      const skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls).toHaveLength(0)

      // Le highlight reste en attente (popover mock non monte) — cleanup via resetModules/useRealTimers dans afterEach.
      void promise
    })

    it('retries 3 times with 500ms interval and emits skip message when absent', async () => {
      // Aucun selector present → 3 retries echouent → skip message
      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      // Entry : nextTick + 500 + 500 + 500 = ~1500ms cumules pour les retries
      // On avance largement au-dela pour que waitForElement retourne null puis que le skip soit emis
      await vi.advanceTimersByTimeAsync(2000)

      // Apres les 3 retries, le skip message a ete emis
      const skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls.length).toBeGreaterThanOrEqual(1)
      await promise
    })

    it('returns null and skips gracefully after 3 failed retries', async () => {
      const { startTour, tourState } = await importFresh()
      const promise = startTour('tour_mono')

      // Advance enough pour que waitForElement termine ses 3 retries et que le continue soit execute
      await vi.advanceTimersByTimeAsync(2500)

      // Le tour a fini (1 step, skip + fin) → tourState revient a 'idle' (ou 'complete'→'idle')
      const result = await promise
      expect(result).toBe(true) // Le tour "reussit" meme si le step a ete skippe (FR31)
      // tourState redevient 'idle' apres le setTimeout(1000) de finalisation
      await vi.advanceTimersByTimeAsync(1100)
      expect(tourState.value).toBe('idle')
    })

    it('resolves immediately when element appears between retry attempts', async () => {
      // AC6 Bloc 1 — insertion DOM entre 2 timers : on simule l'apparition de l'element
      // apres le 1er retry (entre 500ms et 1000ms cumules) et on verifie qu'aucun skip
      // message n'est emis (element pointe normalement).
      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      // Laisser passer le 1er retry (nextTick + ~500ms)
      await vi.advanceTimersByTimeAsync(600)

      // L'element apparait maintenant (avant le retry 2 qui sinon serait l'echec final)
      presentSelectors.add('[data-guide-target="absent-el"]')

      // Avancer pour que le prochain querySelector du retry trouve l'element
      await vi.advanceTimersByTimeAsync(600)

      // Aucun skip message — l'element a ete trouve a temps
      const skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls).toHaveLength(0)

      // Le highlight reste en attente (popover mock non monte) — cleanup via afterEach.
      void promise
    })

    it('returns null immediately when cancelled during retry (parity with waitForElementExtended)', async () => {
      const { startTour, cancelTour } = await importFresh()
      const promise = startTour('tour_mono')

      // Avancer un peu pour que waitForElement soit dans sa boucle retry
      await vi.advanceTimersByTimeAsync(600)

      // Annuler pendant que waitForElement attend
      cancelTour()

      // Avancer largement
      await vi.advanceTimersByTimeAsync(2000)

      // Apres cancel, le skip message NE doit PAS etre emis (cancelled court-circuite)
      const skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls).toHaveLength(0)

      // UI widget restaure
      expect(mockUiStore.chatWidgetMinimized).toBe(false)
      expect(mockUiStore.guidedTourActive).toBe(false)

      await promise
    })
  })

  // ═════════════════════════════════════════════════════════════════
  // Bloc 2 : Skip gracieux mono-page (AC2)
  // ═════════════════════════════════════════════════════════════════

  describe('Bloc 2 — skip gracieux mono-page', () => {
    it('adds exact system message with accents when element is missing', async () => {
      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(2500)
      await promise

      // Message exact avec accents é/à (FR31)
      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        "Je n'ai pas pu pointer cet élément. Passons à la suite.",
      )
    })

    it('does not transition to interrupted when a step is skipped', async () => {
      const { startTour, tourState } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(2500)

      // Pendant le skip, l'etat reste a 'highlighting' (pas d'interruption)
      // Note : apres la fin du tour, l'etat passe a 'complete' puis 'idle', mais jamais 'interrupted'
      await promise
      expect(['idle', 'complete', 'highlighting']).toContain(tourState.value)
      // L'important : l'etat n'est jamais passe par 'interrupted'
      expect(tourState.value).not.toBe('interrupted')
    })

    it('emits one message per skipped step when multiple steps are absent', async () => {
      // Aucun selector present → 3 steps → 3 skip messages
      const { startTour } = await importFresh()
      const promise = startTour('tour_mono_multi')

      // Chaque step attend 1500ms (3 retries x 500ms) avant de skip
      // Total : ~4500ms pour 3 steps
      await vi.advanceTimersByTimeAsync(6000)

      const skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls).toHaveLength(3)

      await promise
    })
  })

  // ═════════════════════════════════════════════════════════════════
  // Bloc 3 : Soft retry + hard timeout page load (AC3)
  // ═════════════════════════════════════════════════════════════════

  describe('Bloc 3 — soft retry + hard timeout page load', () => {
    it('resolves before soft retry window without logging debug or emitting message', async () => {
      // AC6 Bloc 3 — element apparait a ~3s apres navigation : pas de log soft-retry, pas de message timeout, tour continue
      currentPathname = '/home'
      presentSelectors.add('[data-guide-target="sidebar-link"]')

      const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {})

      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        autoResolveHighlight(config)
      })

      const { startTour } = await importFresh()
      const promise = startTour('tour_multi_page')

      // Entry countdown + navigation
      await vi.advanceTimersByTimeAsync(4000)
      currentPathname = '/esg/results'

      // A ~3s post-navigation, l'element apparait (avant les 5s de soft retry)
      await vi.advanceTimersByTimeAsync(3000)
      presentSelectors.add('[data-guide-target="page-el"]')

      // Laisser le polling detecter l'element
      await vi.advanceTimersByTimeAsync(1000)

      // Pas de log soft-retry (on n'a pas depasse 5s)
      const softRetryDebugs = debugSpy.mock.calls.filter((c) =>
        String(c[0]).includes('soft retry page load'),
      )
      expect(softRetryDebugs).toHaveLength(0)

      // Pas de message hard timeout NFR16
      const timeoutMsg = mockAddSystemMessage.mock.calls.find((c) =>
        String(c[0]).includes('La page met trop de temps'),
      )
      expect(timeoutMsg).toBeUndefined()

      // Le highlight du step reste en attente — cleanup via afterEach.
      void promise

      debugSpy.mockRestore()
    })

    it('logs console.debug at soft retry threshold (~5s)', async () => {
      currentPathname = '/home'
      presentSelectors.add('[data-guide-target="sidebar-link"]')
      // Note : '[data-guide-target="page-el"]' reste absent → timeout

      const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {})

      // Highlight du entryStep : resolu immediatement via popoverRender avec onCountdownExpired
      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        // Simuler que l'utilisateur clique ou que le countdown expire
        // en montant le popover (qui declenche onCountdownExpired apres son propre timer)
        autoResolveHighlight(config)
      })

      const { startTour, cancelTour } = await importFresh()
      const promise = startTour('tour_multi_page')

      // Laisser le countdown du entryStep s'ecouler (3s) + navigation
      await vi.advanceTimersByTimeAsync(4000)
      currentPathname = '/esg/results'

      // Apres navigation, waitForElementExtended commence son polling
      // A 5s cumulees, il doit logger console.debug
      await vi.advanceTimersByTimeAsync(6000)

      const debugCalls = debugSpy.mock.calls.filter((c) =>
        String(c[0]).includes('soft retry page load'),
      )
      expect(debugCalls.length).toBeGreaterThanOrEqual(1)

      // Cleanup : annuler et attendre le timeout hard
      cancelTour()
      await vi.advanceTimersByTimeAsync(2000)
      await promise

      debugSpy.mockRestore()
    })

    it('emits NFR16 exact message and interrupts after 10s hard timeout', async () => {
      currentPathname = '/home'
      presentSelectors.add('[data-guide-target="sidebar-link"]')
      // page-el jamais present → hard timeout

      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        autoResolveHighlight(config)
      })

      const { startTour } = await importFresh()
      const promise = startTour('tour_multi_page')

      // Entry countdown ~3s + navigation
      await vi.advanceTimersByTimeAsync(4000)
      currentPathname = '/esg/results'

      // Avancer au-dela des 10s hard timeout
      await vi.advanceTimersByTimeAsync(12000)

      // Message NFR16 exact
      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        'La page met trop de temps à charger. Réessayez plus tard.',
      )

      // startTour retourne false (review 6.4 P4 : pas d'acceptance creditee)
      const result = await promise
      expect(result).toBe(false)

      // UI widget restauree (interruption)
      await vi.advanceTimersByTimeAsync(600)
      expect(mockUiStore.chatWidgetMinimized).toBe(false)
      expect(mockUiStore.guidedTourActive).toBe(false)
    })

    it('sets tourState to interrupted then idle after hard timeout', async () => {
      currentPathname = '/home'
      presentSelectors.add('[data-guide-target="sidebar-link"]')

      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        autoResolveHighlight(config)
      })

      const { startTour, tourState } = await importFresh()
      const promise = startTour('tour_multi_page')

      await vi.advanceTimersByTimeAsync(4000)
      currentPathname = '/esg/results'
      await vi.advanceTimersByTimeAsync(12000)
      await promise

      // Apres interruption, transition automatique vers 'idle' (setTimeout 500ms ligne 230)
      await vi.advanceTimersByTimeAsync(600)
      expect(tourState.value).toBe('idle')
    })
  })

  // ═════════════════════════════════════════════════════════════════
  // Bloc 4 : Catch global Driver.js crash (AC4)
  // ═════════════════════════════════════════════════════════════════

  describe('Bloc 4 — catch global Driver.js crash', () => {
    it('loadDriver rejection triggers empathic message and cleanup', async () => {
      mockLoadDriver.mockImplementation(() => Promise.reject(new Error('driver.js load failed')))

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { startTour, tourState } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(50)

      const result = await promise
      expect(result).toBe(false)

      // Message empathique exact (FR31)
      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        'Le guidage a rencontré un problème. Le chat est toujours disponible.',
      )

      // console.warn appele avec le label + error object
      const crashWarn = warnSpy.mock.calls.find((c) =>
        String(c[0]).includes('tour crashed'),
      )
      expect(crashWarn).toBeDefined()
      expect(crashWarn?.[1]).toBeInstanceOf(Error)

      // Etat final : idle (pas interrupted car catch court-circuite interruptTour)
      expect(tourState.value).toBe('idle')

      // Flags UI restaures
      expect(mockUiStore.chatWidgetMinimized).toBe(false)
      expect(mockUiStore.guidedTourActive).toBe(false)

      warnSpy.mockRestore()
    })

    it('highlight throwing triggers empathic message and cleanup', async () => {
      presentSelectors.add('[data-guide-target="absent-el"]')

      mockHighlight.mockImplementation(() => {
        throw new Error('Driver.js highlight boom')
      })

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(100)
      await promise

      expect(mockAddSystemMessage).toHaveBeenCalledWith(
        'Le guidage a rencontré un problème. Le chat est toujours disponible.',
      )

      expect(
        warnSpy.mock.calls.some((c) => String(c[0]).includes('tour crashed')),
      ).toBe(true)

      warnSpy.mockRestore()
    })

    it('logs the error object (not empty) alongside the label', async () => {
      const specificError = new Error('specific-crash-signature')
      mockLoadDriver.mockImplementation(() => Promise.reject(specificError))

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      await vi.advanceTimersByTimeAsync(50)
      await promise

      const crashCall = warnSpy.mock.calls.find((c) =>
        String(c[0]).includes('tour crashed'),
      )
      expect(crashCall).toBeDefined()
      expect(crashCall?.[1]).toBe(specificError)

      warnSpy.mockRestore()
    })

    it('does NOT emit empathic message when crash follows a user-initiated cancel', async () => {
      // Scenario : cancelTour est appele, cancelled=true, puis une erreur survient
      // pendant le cleanup (double destroy ou autre). Le catch ne doit PAS spammer.
      let triggerCrash = false
      mockLoadDriver.mockImplementation(async () => {
        // Yield une iteration pour permettre a cancelTour de positionner cancelled=true
        await new Promise((r) => setTimeout(r, 10))
        if (triggerCrash) {
          throw new Error('post-cancel crash')
        }
        return mockDriverModule
      })

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { startTour, cancelTour } = await importFresh()
      triggerCrash = true
      const promise = startTour('tour_mono')

      // Annuler AVANT que loadDriver throw
      await vi.advanceTimersByTimeAsync(1)
      cancelTour()

      await vi.advanceTimersByTimeAsync(100)
      await promise

      // Message empathique NE doit PAS etre emis (cancelled etait true au moment du catch)
      const emphaticCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('rencontré un problème'),
      )
      expect(emphaticCalls).toHaveLength(0)

      // Mais le warn "tour crashed" est quand meme emis (traceabilite)
      expect(
        warnSpy.mock.calls.some((c) => String(c[0]).includes('tour crashed')),
      ).toBe(true)

      warnSpy.mockRestore()
    })
  })

  // ═════════════════════════════════════════════════════════════════
  // Bloc 5 : Constantes module-level (AC1, AC3) — comportement observable
  // ═════════════════════════════════════════════════════════════════

  describe('Bloc 5 — constantes module-level observables', () => {
    it('hard timeout observed at ~10s (PAGE_LOAD_HARD_TIMEOUT_MS)', async () => {
      currentPathname = '/home'
      presentSelectors.add('[data-guide-target="sidebar-link"]')

      mockHighlight.mockImplementation((config: Parameters<typeof autoResolveHighlight>[0]) => {
        autoResolveHighlight(config)
      })

      const { startTour } = await importFresh()
      const promise = startTour('tour_multi_page')

      // Entry countdown + navigation + DOM wait
      await vi.advanceTimersByTimeAsync(4000)
      currentPathname = '/esg/results'

      // A 9s cumulees apres navigation, aucun message de hard timeout encore
      await vi.advanceTimersByTimeAsync(8500)
      let timeoutMsg = mockAddSystemMessage.mock.calls.find((c) =>
        String(c[0]).includes('La page met trop de temps'),
      )
      expect(timeoutMsg).toBeUndefined()

      // Au-dela de 10s, le message doit etre emis
      await vi.advanceTimersByTimeAsync(2500)
      timeoutMsg = mockAddSystemMessage.mock.calls.find((c) =>
        String(c[0]).includes('La page met trop de temps'),
      )
      expect(timeoutMsg).toBeDefined()

      await promise
    })

    it('DOM retry observed at 3 x 500ms = ~1500ms (DOM_RETRY_COUNT, DOM_RETRY_INTERVAL_MS)', async () => {
      const { startTour } = await importFresh()
      const promise = startTour('tour_mono')

      // A ~1400ms, waitForElement n'a pas encore epuise ses retries → pas de skip
      await vi.advanceTimersByTimeAsync(1200)
      let skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls).toHaveLength(0)

      // Au-dela de 1500ms, le skip a du etre emis
      await vi.advanceTimersByTimeAsync(1000)
      skipCalls = mockAddSystemMessage.mock.calls.filter((c) =>
        String(c[0]).includes('pointer cet'),
      )
      expect(skipCalls.length).toBeGreaterThanOrEqual(1)

      await promise
    })
  })
})
