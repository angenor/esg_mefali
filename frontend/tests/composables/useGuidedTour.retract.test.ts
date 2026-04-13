import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks ──

const mockHighlight = vi.fn()
const mockDestroy = vi.fn()
const mockSetConfig = vi.fn()

let capturedOnDestroyStarted: (() => void) | null = null
const mockDriverFactory = vi.fn((config: Record<string, unknown>) => {
  capturedOnDestroyStarted = (config.onDestroyStarted as () => void) ?? null
  return {
    highlight: mockHighlight,
    destroy: (...args: unknown[]) => {
      capturedOnDestroyStarted?.()
      mockDestroy(...args)
    },
    setConfig: mockSetConfig,
  }
})
const mockDriverModule = { driver: mockDriverFactory }

vi.mock('driver.js', () => mockDriverModule)

const mockLoadDriver = vi.fn(() => Promise.resolve(mockDriverModule))
vi.mock('~/composables/useDriverLoader', () => ({
  loadDriver: mockLoadDriver,
}))

// Mock du store ui avec les champs Story 5.2
const mockStoreState = {
  prefersReducedMotion: false,
  chatWidgetOpen: true,
  chatWidgetMinimized: false,
  guidedTourActive: false,
}

vi.mock('~/stores/ui', () => ({
  useUiStore: () => mockStoreState,
}))

const mockAddSystemMessage = vi.fn()
vi.mock('~/composables/useChat', () => ({
  useChat: () => ({
    addSystemMessage: mockAddSystemMessage,
  }),
}))

vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

const TEST_REGISTRY = {
  retract_tour: {
    id: 'retract_tour',
    steps: [
      {
        selector: '[data-guide-target="retract-el"]',
        popover: {
          title: 'Etape 1',
          description: 'Description',
          side: 'bottom' as const,
        },
      },
    ],
  },
}

vi.mock('~/lib/guided-tours/registry', () => ({
  tourRegistry: TEST_REGISTRY,
  DEFAULT_ENTRY_COUNTDOWN: 8,
}))

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

describe('useGuidedTour — retraction widget (Story 5.2)', () => {
  let useGuidedTour: typeof import('~/composables/useGuidedTour').useGuidedTour
  let notifyRetractComplete: typeof import('~/composables/useGuidedTour').notifyRetractComplete

  beforeEach(async () => {
    vi.clearAllMocks()
    clearDom()
    setPathname('/')

    // Reset store state
    mockStoreState.prefersReducedMotion = false
    mockStoreState.chatWidgetOpen = true
    mockStoreState.chatWidgetMinimized = false
    mockStoreState.guidedTourActive = false

    vi.resetModules()
    const mod = await import('~/composables/useGuidedTour')
    useGuidedTour = mod.useGuidedTour
    notifyRetractComplete = mod.notifyRetractComplete

    mockHighlight.mockImplementation((opts: Record<string, unknown>) => {
      const popover = opts.popover as Record<string, unknown> | undefined
      if (popover?.onNextClick) {
        ;(popover.onNextClick as () => void)()
      }
    })
  })

  afterEach(() => {
    clearDom()
  })

  it('startTour positionne guidedTourActive = true et chatWidgetMinimized = true', async () => {
    createMockElement('[data-guide-target="retract-el"]')

    const { startTour } = useGuidedTour()

    // Lancer startTour mais il va attendre la retraction
    const tourPromise = startTour('retract_tour')

    // Les flags doivent etre positionnes immediatement (avant await retractPromise)
    // On doit notifier que la retraction est terminee pour debloquer
    await new Promise(r => setTimeout(r, 10))
    expect(mockStoreState.guidedTourActive).toBe(true)
    expect(mockStoreState.chatWidgetMinimized).toBe(true)

    // Notifier que la retraction GSAP est terminee
    notifyRetractComplete()

    await tourPromise

    // Apres completion, les flags sont remis a false
    expect(mockStoreState.chatWidgetMinimized).toBe(false)
    expect(mockStoreState.guidedTourActive).toBe(false)
  })

  it('fin de parcours remet chatWidgetMinimized et guidedTourActive a false', async () => {
    createMockElement('[data-guide-target="retract-el"]')
    mockStoreState.chatWidgetOpen = false // Widget ferme — pas d'attente

    const { startTour } = useGuidedTour()
    await startTour('retract_tour')

    expect(mockStoreState.chatWidgetMinimized).toBe(false)
    expect(mockStoreState.guidedTourActive).toBe(false)
  })

  it('cancelTour remet les deux flags a false', async () => {
    createMockElement('[data-guide-target="retract-el"]')

    // Bloquer le highlight pour pouvoir annuler pendant qu'il attend
    let resolveHighlight: (() => void) | null = null
    mockHighlight.mockImplementationOnce(() => {
      // Ne pas appeler onNextClick — le highlight reste bloque
      // On stocke le resolver pour pouvoir debloquer apres cancel
    })

    const { startTour, cancelTour, tourState } = useGuidedTour()

    // Lancer le tour
    const tourPromise = startTour('retract_tour')

    // Debloquer la retraction (le widget est "open")
    await new Promise(r => setTimeout(r, 10))
    notifyRetractComplete()

    // Attendre que le tour passe en highlighting (highlight bloque)
    await new Promise(r => setTimeout(r, 50))
    expect(tourState.value).toBe('highlighting')

    // Annuler
    cancelTour()

    expect(mockStoreState.chatWidgetMinimized).toBe(false)
    expect(mockStoreState.guidedTourActive).toBe(false)
    expect(tourState.value).toBe('interrupted')
  })

  it('widget deja ferme : pas d\'attente de retraction', async () => {
    createMockElement('[data-guide-target="retract-el"]')
    mockStoreState.chatWidgetOpen = false

    const { startTour } = useGuidedTour()

    // Doit se terminer sans appel a notifyRetractComplete
    await startTour('retract_tour')

    // Le tour a fonctionne normalement
    expect(mockHighlight).toHaveBeenCalledOnce()
    expect(mockDestroy).toHaveBeenCalledOnce()
  })

  it('notifyRetractComplete est une no-op quand aucune retraction en attente', () => {
    // Pas de startTour en cours — l'appel ne doit pas throw
    expect(() => notifyRetractComplete()).not.toThrow()
  })
})
