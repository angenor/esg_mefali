import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'

// Mock des auto-imports Nuxt au niveau global
const mockNavigateTo = vi.fn()
;(globalThis as any).navigateTo = mockNavigateTo
;(globalThis as any).defineNuxtRouteMiddleware = (fn: Function) => fn

describe('middleware chat-redirect.global (Story 2.2 — AC3)', () => {
  let middleware: (to: any) => any

  beforeAll(async () => {
    const mod = await import('~/middleware/chat-redirect.global')
    middleware = mod.default
  })

  beforeEach(() => {
    mockNavigateTo.mockClear()
  })

  it('redirige /chat vers / avec query openChat=1 et replace=true', () => {
    middleware({ path: '/chat' })

    expect(mockNavigateTo).toHaveBeenCalledOnce()
    expect(mockNavigateTo).toHaveBeenCalledWith(
      { path: '/', query: { openChat: '1' } },
      { replace: true },
    )
  })

  it('redirige /chat/ (trailing slash) vers / avec query openChat=1', () => {
    middleware({ path: '/chat/' })

    expect(mockNavigateTo).toHaveBeenCalledOnce()
    expect(mockNavigateTo).toHaveBeenCalledWith(
      { path: '/', query: { openChat: '1' } },
      { replace: true },
    )
  })

  it('ne redirige pas les autres routes', () => {
    const result = middleware({ path: '/esg' })

    expect(mockNavigateTo).not.toHaveBeenCalled()
    expect(result).toBeUndefined()
  })

  it('ne redirige pas /chat/quelque-chose (sous-routes API)', () => {
    const result = middleware({ path: '/chat/conversations' })

    expect(mockNavigateTo).not.toHaveBeenCalled()
    expect(result).toBeUndefined()
  })

  it('ne redirige pas la route racine /', () => {
    const result = middleware({ path: '/' })

    expect(mockNavigateTo).not.toHaveBeenCalled()
    expect(result).toBeUndefined()
  })
})
