import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock de driver.js
const mockDriverModule = {
  driver: vi.fn(() => ({
    highlight: vi.fn(),
    drive: vi.fn(),
    destroy: vi.fn(),
  })),
}

vi.mock('driver.js', () => mockDriverModule)

describe('useDriverLoader', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllGlobals()
  })

  describe('loadDriver', () => {
    it('retourne le module driver.js', async () => {
      const { loadDriver } = await import('~/composables/useDriverLoader')
      const mod = await loadDriver()
      expect(mod).toBeDefined()
      expect(mod.driver).toBeDefined()
    })

    it('met en cache le module apres le premier appel', async () => {
      const { loadDriver } = await import('~/composables/useDriverLoader')
      const mod1 = await loadDriver()
      const mod2 = await loadDriver()
      expect(mod1).toBe(mod2) // meme reference
    })
  })

  describe('prefetchDriverJs', () => {
    it('appelle requestIdleCallback', async () => {
      const mockRIC = vi.fn((cb: () => void) => { cb(); return 0 })
      vi.stubGlobal('requestIdleCallback', mockRIC)

      const { prefetchDriverJs } = await import('~/composables/useDriverLoader')
      prefetchDriverJs()
      expect(mockRIC).toHaveBeenCalledOnce()

      vi.unstubAllGlobals()
    })

    it('utilise setTimeout comme fallback si requestIdleCallback absent', async () => {
      vi.stubGlobal('requestIdleCallback', undefined)
      const spy = vi.spyOn(globalThis, 'setTimeout')

      const { prefetchDriverJs } = await import('~/composables/useDriverLoader')
      prefetchDriverJs()
      expect(spy).toHaveBeenCalledWith(expect.any(Function), 200)

      vi.unstubAllGlobals()
      spy.mockRestore()
    })

    it('ne re-importe pas si deja en cache via loadDriver', async () => {
      const mockRIC = vi.fn((cb: () => void) => { cb(); return 0 })
      vi.stubGlobal('requestIdleCallback', mockRIC)

      const { loadDriver, prefetchDriverJs } = await import('~/composables/useDriverLoader')
      await loadDriver() // charge le module en cache
      prefetchDriverJs() // ne devrait pas re-appeler requestIdleCallback
      expect(mockRIC).not.toHaveBeenCalled()

      vi.unstubAllGlobals()
    })

    it('prefetch remplit le cache reutilise par loadDriver', async () => {
      const mockRIC = vi.fn((cb: () => void) => { cb(); return 0 })
      vi.stubGlobal('requestIdleCallback', mockRIC)

      const { prefetchDriverJs, loadDriver } = await import('~/composables/useDriverLoader')
      prefetchDriverJs()

      // Attendre que la promesse du prefetch se resolve
      await vi.dynamicImportSettled?.() ?? new Promise(r => setTimeout(r, 0))

      const mod = await loadDriver()
      expect(mod).toBeDefined()
      expect(mod.driver).toBeDefined()
      // requestIdleCallback appele une seule fois (par prefetch), pas de second import par loadDriver
      expect(mockRIC).toHaveBeenCalledOnce()

      vi.unstubAllGlobals()
    })
  })
})
