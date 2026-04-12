// @vitest-environment node
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick, effectScope } from 'vue'

// ── Helper pour créer un mock MediaQueryList ──

interface MockMediaQueryList {
  matches: boolean
  media: string
  addEventListener: ReturnType<typeof vi.fn>
  removeEventListener: ReturnType<typeof vi.fn>
  dispatchEvent: ReturnType<typeof vi.fn>
  onchange: null
  addListener: ReturnType<typeof vi.fn>
  removeListener: ReturnType<typeof vi.fn>
  _triggerChange: (matches: boolean) => void
}

function createMockMatchMedia(matches: boolean): { mql: MockMediaQueryList; matchMediaFn: ReturnType<typeof vi.fn> } {
  let changeHandler: ((e: { matches: boolean }) => void) | null = null

  const mql: MockMediaQueryList = {
    matches,
    media: '(min-width: 1024px)',
    addEventListener: vi.fn((event: string, handler: (e: { matches: boolean }) => void) => {
      if (event === 'change') {
        changeHandler = handler
      }
    }),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    _triggerChange(newMatches: boolean) {
      mql.matches = newMatches
      if (changeHandler) {
        changeHandler({ matches: newMatches })
      }
    },
  }

  const matchMediaFn = vi.fn(() => mql)

  return { mql, matchMediaFn }
}

// ── Helper : installer un window minimal avec matchMedia ──

function stubWindowWithMatchMedia(matchMediaFn: ReturnType<typeof vi.fn>) {
  vi.stubGlobal('window', { matchMedia: matchMediaFn })
}

describe('useDeviceDetection', () => {
  beforeEach(() => {
    // Réinitialiser le cache des modules pour chaque test (import dynamique frais)
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  describe('Détection desktop (AC #1)', () => {
    it('retourne isDesktop=true et isMobile=false pour un écran >= 1024px', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(true)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      const result = scope.run(() => useDeviceDetection())!

      expect(result.isDesktop.value).toBe(true)
      expect(result.isMobile.value).toBe(false)
      expect(matchMediaFn).toHaveBeenCalledWith('(min-width: 1024px)')

      scope.stop()
    })
  })

  describe('Détection mobile (AC #2)', () => {
    it('retourne isDesktop=false et isMobile=true pour un écran < 1024px', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(false)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      const result = scope.run(() => useDeviceDetection())!

      expect(result.isDesktop.value).toBe(false)
      expect(result.isMobile.value).toBe(true)

      scope.stop()
    })
  })

  describe('Changement réactif en temps réel (AC #3)', () => {
    it('met à jour isDesktop quand la media query change (desktop → mobile)', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(true)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      const { isDesktop, isMobile } = scope.run(() => useDeviceDetection())!

      expect(isDesktop.value).toBe(true)

      // Simuler le redimensionnement en dessous de 1024px
      mql._triggerChange(false)
      await nextTick()

      expect(isDesktop.value).toBe(false)
      expect(isMobile.value).toBe(true)

      scope.stop()
    })

    it('met à jour isDesktop quand la media query change (mobile → desktop)', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(false)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      const { isDesktop, isMobile } = scope.run(() => useDeviceDetection())!

      expect(isDesktop.value).toBe(false)

      // Simuler le redimensionnement au-dessus de 1024px
      mql._triggerChange(true)
      await nextTick()

      expect(isDesktop.value).toBe(true)
      expect(isMobile.value).toBe(false)

      scope.stop()
    })

    it('enregistre un listener change sur la MediaQueryList', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(true)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      scope.run(() => useDeviceDetection())

      expect(mql.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))

      scope.stop()
    })
  })

  describe('Cleanup du listener', () => {
    it('appelle removeEventListener lors du cleanup (onScopeDispose)', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(true)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      scope.run(() => useDeviceDetection())

      // Vérifier que le listener est enregistré
      expect(mql.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))

      // Déclencher le cleanup en arrêtant le scope
      scope.stop()

      expect(mql.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function))
    })
  })

  describe('Guard SSR (pas de window)', () => {
    it('retourne isDesktop=true par défaut quand window n\'existe pas', async () => {
      // Ne pas stubber window → typeof window === 'undefined' en Node
      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const { isDesktop, isMobile } = useDeviceDetection()

      expect(isDesktop.value).toBe(true)
      expect(isMobile.value).toBe(false)
    })

    it('ne tente pas d\'accéder à matchMedia quand window n\'existe pas', async () => {
      // Placer un spy sur globalThis pour détecter tout accès
      const matchMediaSpy = vi.fn()
      vi.stubGlobal('matchMedia', matchMediaSpy)
      // Ne PAS stubber window → le guard typeof window !== 'undefined' est false

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      useDeviceDetection()

      expect(matchMediaSpy).not.toHaveBeenCalled()
    })
  })

  describe('isMobile est dérivé de isDesktop', () => {
    it('isMobile est toujours l\'inverse de isDesktop', async () => {
      const { mql, matchMediaFn } = createMockMatchMedia(true)
      stubWindowWithMatchMedia(matchMediaFn)

      const { useDeviceDetection } = await import('~/composables/useDeviceDetection')
      const scope = effectScope()
      const { isDesktop, isMobile } = scope.run(() => useDeviceDetection())!

      // Desktop
      expect(isDesktop.value).toBe(true)
      expect(isMobile.value).toBe(false)

      // Passer en mobile
      mql._triggerChange(false)
      await nextTick()
      expect(isDesktop.value).toBe(false)
      expect(isMobile.value).toBe(true)

      // Revenir en desktop
      mql._triggerChange(true)
      await nextTick()
      expect(isDesktop.value).toBe(true)
      expect(isMobile.value).toBe(false)

      scope.stop()
    })
  })
})
