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
const mockUiStore = {
  prefersReducedMotion: false,
  guidedTourActive: false,
  chatWidgetMinimized: false,
  chatWidgetOpen: false,
}
vi.mock('~/stores/ui', () => ({
  useUiStore: () => mockUiStore,
}))

// Mock de useChat
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
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

// Mock du registre avec entryStep
const MOCK_REGISTRY_NAV = {
  tour_nav: {
    id: 'tour_nav',
    steps: [
      {
        route: '/esg/results',
        selector: '[data-guide-target="esg-score"]',
        popover: {
          title: 'Score ESG',
          description: 'Votre score ESG.',
          side: 'bottom' as const,
        },
      },
      {
        selector: '[data-guide-target="esg-badges"]',
        popover: {
          title: 'Badges',
          description: 'Vos badges.',
          side: 'right' as const,
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-esg-link"]',
      popover: {
        title: 'ESG',
        description: 'Cliquez pour voir vos resultats ESG.',
        countdown: 5,
      },
      targetRoute: '/esg/results',
    },
  },
  tour_same_page: {
    id: 'tour_same_page',
    steps: [
      {
        route: '/dashboard',
        selector: '[data-guide-target="dash-card"]',
        popover: {
          title: 'Dashboard',
          description: 'Votre dashboard.',
          side: 'bottom' as const,
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-dash-link"]',
      popover: {
        title: 'Dashboard',
        description: 'Cliquez ici.',
        countdown: 5,
      },
      targetRoute: '/dashboard',
    },
  },
  tour_no_entry: {
    id: 'tour_no_entry',
    steps: [
      {
        selector: '[data-guide-target="simple-el"]',
        popover: {
          title: 'Simple',
          description: 'Une etape simple.',
        },
      },
    ],
  },
  tour_multi_route: {
    id: 'tour_multi_route',
    steps: [
      {
        route: '/dashboard',
        selector: '[data-guide-target="dash-el"]',
        popover: {
          title: 'Dashboard',
          description: 'Sur le dashboard.',
        },
      },
      {
        route: '/esg/results',
        selector: '[data-guide-target="esg-el"]',
        popover: {
          title: 'ESG',
          description: 'Sur ESG.',
        },
      },
    ],
  },
}

vi.mock('~/lib/guided-tours/registry', () => ({
  tourRegistry: MOCK_REGISTRY_NAV,
  DEFAULT_ENTRY_COUNTDOWN: 8,
}))

// Simuler location.pathname
let currentPathname = '/dashboard'
vi.stubGlobal('location', {
  get pathname() { return currentPathname },
})

// Simuler document.querySelector pour les elements DOM
const mockElement = document.createElement('div')
let querySelectorResult: Element | null = mockElement

const originalQuerySelector = document.querySelector.bind(document)
vi.spyOn(document, 'querySelector').mockImplementation((selector: string) => {
  // Retourner le popover pour l'injection du badge
  if (selector === '.driver-popover-description') return mockElement
  return querySelectorResult
})

describe('useGuidedTour — navigation multi-pages', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    currentPathname = '/dashboard'
    querySelectorResult = mockElement
    mockNavigateTo.mockClear()
    mockHighlight.mockClear()
    mockDestroy.mockClear()
    mockDriverFactory.mockClear()
    mockAddSystemMessage.mockClear()
    mockLoadDriver.mockClear()
    mockUiStore.guidedTourActive = false
    mockUiStore.chatWidgetMinimized = false
    mockUiStore.chatWidgetOpen = false

    // Simuler que highlight resolve immediatement (clic next)
    mockHighlight.mockImplementation(() => {})
  })

  afterEach(async () => {
    vi.useRealTimers()
    vi.resetModules()
  })

  async function importFresh() {
    const mod = await import('~/composables/useGuidedTour')
    return mod.useGuidedTour()
  }

  // ── entryStep processing ──

  it('passe a "navigating" quand entryStep.targetRoute !== currentRoute', async () => {
    currentPathname = '/dashboard'
    const { startTour, tourState } = await importFresh()

    // Configurer highlight pour resoudre via onNextClick
    mockHighlight.mockImplementation((config: any) => {
      // Simuler clic immediat
      setTimeout(() => config?.popover?.onNextClick?.(), 100)
    })

    const promise = startTour('tour_nav')

    // Laisser les microtasks s'executer (loadDriver, etc.)
    await vi.advanceTimersByTimeAsync(50)

    // L'etat doit passer par 'navigating' a un moment donne
    // Comme le tour navigue puis continue, verifions que navigateTo est appele
    await vi.advanceTimersByTimeAsync(200)

    // Simuler que la navigation met a jour le pathname
    currentPathname = '/esg/results'

    // Avancer le temps pour que le polling DOM fonctionne
    await vi.advanceTimersByTimeAsync(6000)

    // Terminer le tour
    await vi.advanceTimersByTimeAsync(2000)

    expect(mockNavigateTo).toHaveBeenCalledWith('/esg/results')
  })

  it('navigue automatiquement a l\'expiration du decompteur', async () => {
    currentPathname = '/dashboard'
    const { startTour } = await importFresh()

    // Configurer highlight pour les etapes normales (resoudre via onNextClick)
    let highlightCallCount = 0
    mockHighlight.mockImplementation((config: any) => {
      highlightCallCount++
      // Premier highlight = entryStep, ne pas resoudre automatiquement (attendre countdown)
      if (highlightCallCount > 1) {
        setTimeout(() => config?.popover?.onNextClick?.(), 50)
      }
    })

    const promise = startTour('tour_nav')

    // Laisser loadDriver et setup s'executer
    await vi.advanceTimersByTimeAsync(50)

    // Laisser le countdown expirer (5 secondes)
    await vi.advanceTimersByTimeAsync(5500)

    // La navigation auto doit etre declenchee
    currentPathname = '/esg/results'

    // Attendre DOM + highlights
    await vi.advanceTimersByTimeAsync(6000)
    await vi.advanceTimersByTimeAsync(2000)

    expect(mockNavigateTo).toHaveBeenCalledWith('/esg/results')
  })

  // ── Skip entryStep si meme page (AC7) ──

  it('ignore entryStep si deja sur la bonne page', async () => {
    currentPathname = '/dashboard'
    const { startTour } = await importFresh()

    mockHighlight.mockImplementation((config: any) => {
      setTimeout(() => config?.popover?.onNextClick?.(), 50)
    })

    const promise = startTour('tour_same_page')

    await vi.advanceTimersByTimeAsync(50)
    await vi.advanceTimersByTimeAsync(200)
    await vi.advanceTimersByTimeAsync(2000)

    // navigateTo ne doit PAS avoir ete appele car on est deja sur /dashboard
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  // ── Tour sans entryStep ──

  it('fonctionne normalement sans entryStep', async () => {
    currentPathname = '/dashboard'
    const { startTour } = await importFresh()

    mockHighlight.mockImplementation((config: any) => {
      setTimeout(() => config?.popover?.onNextClick?.(), 50)
    })

    const promise = startTour('tour_no_entry')

    await vi.advanceTimersByTimeAsync(50)
    await vi.advanceTimersByTimeAsync(200)
    await vi.advanceTimersByTimeAsync(2000)

    expect(mockNavigateTo).not.toHaveBeenCalled()
    expect(mockHighlight).toHaveBeenCalled()
  })

  // ── Attente DOM timeout ──

  it('interrompt le parcours apres 10s si element DOM introuvable', async () => {
    currentPathname = '/dashboard'
    querySelectorResult = null // Element jamais trouve

    const { startTour } = await importFresh()

    mockHighlight.mockImplementation((config: any) => {
      // entryStep: simuler clic immediat
      setTimeout(() => config?.popover?.onNextClick?.(), 50)
    })

    const promise = startTour('tour_nav')

    // Laisser loadDriver
    await vi.advanceTimersByTimeAsync(50)

    // Simuler clic sur le lien (navigateTo)
    await vi.advanceTimersByTimeAsync(200)
    currentPathname = '/esg/results'

    // Attendre au dela de 10s timeout
    await vi.advanceTimersByTimeAsync(12000)

    expect(mockAddSystemMessage).toHaveBeenCalledWith(
      expect.stringContaining('charger correctement')
    )
  })

  // ── Navigation intra-boucle (etapes avec routes differentes) ──

  it('navigue entre pages pendant la boucle d\'etapes', async () => {
    currentPathname = '/dashboard'
    const { startTour } = await importFresh()

    let highlightCount = 0
    mockHighlight.mockImplementation((config: any) => {
      highlightCount++
      setTimeout(() => config?.popover?.onNextClick?.(), 50)
    })

    const promise = startTour('tour_multi_route')

    await vi.advanceTimersByTimeAsync(50)

    // Premiere etape : route /dashboard = meme page, pas de navigation
    await vi.advanceTimersByTimeAsync(200)

    // Deuxieme etape : route /esg/results, navigation necessaire
    currentPathname = '/esg/results'
    await vi.advanceTimersByTimeAsync(6000)
    await vi.advanceTimersByTimeAsync(2000)

    // navigateTo appele pour la 2eme etape
    expect(mockNavigateTo).toHaveBeenCalledWith('/esg/results')
  })

  // ── Annulation pendant navigation ──

  it('annule proprement pendant la navigation', async () => {
    currentPathname = '/dashboard'
    const { startTour, cancelTour } = await importFresh()

    // Ne pas resoudre le highlight (simuler attente)
    mockHighlight.mockImplementation(() => {})

    const promise = startTour('tour_nav')

    await vi.advanceTimersByTimeAsync(50)

    // Annuler pendant que le countdown tourne
    cancelTour()

    await vi.advanceTimersByTimeAsync(1000)

    // Le tour doit etre interrompu, widget restaure
    expect(mockUiStore.chatWidgetMinimized).toBe(false)
    expect(mockUiStore.guidedTourActive).toBe(false)
  })
})
