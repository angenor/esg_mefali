import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks minimaux (on ne teste pas Driver.js, seulement le state adaptatif) ──
vi.mock('driver.js', () => ({
  driver: vi.fn(() => ({
    highlight: vi.fn(),
    destroy: vi.fn(),
    setConfig: vi.fn(),
  })),
}))

vi.mock('~/composables/useDriverLoader', () => ({
  loadDriver: vi.fn(() => Promise.resolve({ driver: vi.fn() })),
}))

vi.mock('~/stores/ui', () => ({
  useUiStore: () => ({
    prefersReducedMotion: false,
    guidedTourActive: false,
    chatWidgetMinimized: false,
    chatWidgetOpen: false,
  }),
}))

vi.mock('~/composables/useChat', () => ({
  useChat: () => ({ addSystemMessage: vi.fn() }),
}))

vi.stubGlobal('navigateTo', vi.fn(() => Promise.resolve()))

// ── Mock localStorage (vitest jsdom fournit un vrai localStorage,
//    mais on veut un mock controllable par test) ──
function createMockLocalStorage() {
  const store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => (key in store ? store[key] : null)),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      for (const k of Object.keys(store)) delete store[k]
    }),
    _store: store,
  }
}

describe('useGuidedTour — frequence adaptative (FR17 / story 6.4)', () => {
  let mockStorage: ReturnType<typeof createMockLocalStorage>

  beforeEach(() => {
    mockStorage = createMockLocalStorage()
    vi.stubGlobal('localStorage', mockStorage)
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  // ── AC1 : initialisation ──
  it('initial values are 0 when localStorage empty', async () => {
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    const tour = useGuidedTour()
    expect(tour.guidanceRefusalCount.value).toBe(0)
    expect(tour.guidanceAcceptanceCount.value).toBe(0)
  })

  it('initial values are restored from localStorage', async () => {
    mockStorage.setItem(
      'esg_mefali_guidance_stats',
      JSON.stringify({ refusal_count: 3, acceptance_count: 2 }),
    )
    mockStorage.setItem.mockClear()
    // Forcer re-import pour relire le state module-level
    vi.resetModules()
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    const tour = useGuidedTour()
    expect(tour.guidanceRefusalCount.value).toBe(3)
    expect(tour.guidanceAcceptanceCount.value).toBe(2)
  })

  it('corrupted localStorage falls back to 0', async () => {
    mockStorage.setItem('esg_mefali_guidance_stats', 'not-json')
    vi.resetModules()
    const { useGuidedTour: useGT1 } = await import('~/composables/useGuidedTour')
    expect(useGT1().guidanceRefusalCount.value).toBe(0)
    expect(useGT1().guidanceAcceptanceCount.value).toBe(0)

    // Cas : type non-numerique
    mockStorage.setItem(
      'esg_mefali_guidance_stats',
      JSON.stringify({ refusal_count: '3', acceptance_count: 'abc' }),
    )
    vi.resetModules()
    const { useGuidedTour: useGT2 } = await import('~/composables/useGuidedTour')
    expect(useGT2().guidanceRefusalCount.value).toBe(0)
    expect(useGT2().guidanceAcceptanceCount.value).toBe(0)

    // Cas : valeurs negatives
    mockStorage.setItem(
      'esg_mefali_guidance_stats',
      JSON.stringify({ refusal_count: -1, acceptance_count: 2 }),
    )
    vi.resetModules()
    const { useGuidedTour: useGT3 } = await import('~/composables/useGuidedTour')
    expect(useGT3().guidanceRefusalCount.value).toBe(0)
    expect(useGT3().guidanceAcceptanceCount.value).toBe(0)
  })

  // ── AC1 : increments + persistance ──
  it('incrementGuidanceRefusal increments and persists', async () => {
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    const tour = useGuidedTour()
    tour.incrementGuidanceRefusal()
    expect(tour.guidanceRefusalCount.value).toBe(1)
    expect(mockStorage.setItem).toHaveBeenCalledWith(
      'esg_mefali_guidance_stats',
      expect.stringContaining('"refusal_count":1'),
    )
    tour.incrementGuidanceRefusal()
    expect(tour.guidanceRefusalCount.value).toBe(2)
  })

  it('incrementGuidanceAcceptance increments acceptance AND resets refusal to 0', async () => {
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    const tour = useGuidedTour()
    // Pre-condition : 3 refus accumules
    tour.incrementGuidanceRefusal()
    tour.incrementGuidanceRefusal()
    tour.incrementGuidanceRefusal()
    expect(tour.guidanceRefusalCount.value).toBe(3)

    tour.incrementGuidanceAcceptance()
    expect(tour.guidanceAcceptanceCount.value).toBe(1)
    expect(tour.guidanceRefusalCount.value).toBe(0) // reset cycle

    // Verifier qu'une seule ecriture atomique est faite (pas 2)
    const lastCall = mockStorage.setItem.mock.calls.at(-1)
    expect(lastCall?.[1]).toContain('"refusal_count":0')
    expect(lastCall?.[1]).toContain('"acceptance_count":1')
  })

  it('resetGuidanceStats writes zeros to localStorage', async () => {
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    const tour = useGuidedTour()
    tour.incrementGuidanceRefusal()
    tour.incrementGuidanceAcceptance()
    tour.resetGuidanceStats()
    expect(tour.guidanceRefusalCount.value).toBe(0)
    expect(tour.guidanceAcceptanceCount.value).toBe(0)
    const lastCall = mockStorage.setItem.mock.calls.at(-1)
    expect(lastCall?.[1]).toBe(
      JSON.stringify({ refusal_count: 0, acceptance_count: 0 }),
    )
  })

  // ── AC4 : countdown reduit ──
  it.each([
    [0, 8, 8],
    [3, 8, 5],
    [5, 8, 3],
    [10, 8, 3],
    [100, 8, 3],
  ])(
    'effective countdown: N=%i, default=%i → %i (plancher 3s)',
    async (n, defaultCountdown, expected) => {
      const { useGuidedTour } = await import('~/composables/useGuidedTour')
      const tour = useGuidedTour()
      // Simuler N acceptations accumulees
      for (let i = 0; i < n; i++) tour.incrementGuidanceAcceptance()
      expect(tour.computeEffectiveCountdown(defaultCountdown)).toBe(expected)
    },
  )
})
