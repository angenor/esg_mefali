import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ═════════════════════════════════════════════════════════════════════
// Story 9.1 — Rate limiting FR-013 : handler 429 cote frontend
// Couvre AC5 : sur reponse 429, afficher "Trop de messages, reessayez dans
// X secondes" et retirer le message utilisateur de l'historique local.
// ═════════════════════════════════════════════════════════════════════

const mockAuthStore = { accessToken: 'test-token' as string | null }
vi.mock('~/stores/auth', () => ({
  useAuthStore: () => mockAuthStore,
}))

const mockCompanyStore = {
  addProfileUpdate: vi.fn(),
  updateProfileField: vi.fn(),
  setCompletion: vi.fn(),
}
vi.mock('~/stores/company', () => ({
  useCompanyStore: () => mockCompanyStore,
}))

const mockUiStore = {
  currentPage: '/',
  guidedTourActive: false,
}
vi.mock('~/stores/ui', () => ({
  useUiStore: () => mockUiStore,
}))

const mockGuided = {
  guidanceRefusalCount: { value: 0 },
  guidanceAcceptanceCount: { value: 0 },
  startTour: vi.fn(() => Promise.resolve(true)),
  incrementGuidanceRefusal: vi.fn(),
  incrementGuidanceAcceptance: vi.fn(),
  cancelTour: vi.fn(),
  tourState: { value: 'idle' as const },
}
vi.mock('~/composables/useGuidedTour', () => ({
  useGuidedTour: () => mockGuided,
  notifyRetractComplete: vi.fn(),
}))

vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api' },
}))

vi.stubGlobal('crypto', {
  randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8),
})

async function importUseChatFresh() {
  vi.resetModules()
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
  const mod = await import('~/composables/useChat')
  return mod.useChat()
}

function makeRateLimitedResponse(retryAfter: string | null): Response {
  const headers = new Headers()
  headers.set('content-type', 'application/json')
  if (retryAfter !== null) headers.set('Retry-After', retryAfter)
  return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
    status: 429,
    headers,
  })
}

beforeEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
  mockAuthStore.accessToken = 'test-token'
})

afterEach(() => {
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
})

describe('Story 9.1 — rate limiting 429 dans sendMessage()', () => {
  async function setupChat() {
    const chat = await importUseChatFresh()
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    return chat
  }

  it('AC5 — affiche "reessayez dans 42 secondes" quand Retry-After=42', async () => {
    const chat = await setupChat()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(makeRateLimitedResponse('42')),
    )

    await chat.sendMessage('ping')

    expect(chat.error.value).toContain('42')
    expect(chat.error.value.toLowerCase()).toContain('seconde')
    expect(chat.isStreaming.value).toBe(false)
  })

  it('AC5 — fallback sans Retry-After affiche "patientez quelques instants"', async () => {
    const chat = await setupChat()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(makeRateLimitedResponse(null)),
    )

    await chat.sendMessage('ping')

    expect(chat.error.value.toLowerCase()).toContain('trop de messages')
    expect(chat.error.value.toLowerCase()).toContain('instants')
  })

  it('AC5 — idempotence : le message utilisateur refuse est retire de la liste', async () => {
    const chat = await setupChat()
    const before = chat.messages.value.length
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(makeRateLimitedResponse('10')),
    )

    await chat.sendMessage('ping')

    // Aucun message user ne doit persister apres un 429.
    expect(chat.messages.value.length).toBe(before)
  })

  it('AC5 — Retry-After non numerique est ignore (fallback generique)', async () => {
    const chat = await setupChat()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(makeRateLimitedResponse('Mon Apr 17 2026')),
    )

    await chat.sendMessage('ping')

    expect(chat.error.value.toLowerCase()).toContain('trop de messages')
    // Ne doit pas interpoler la date littéralement dans le message utilisateur.
    expect(chat.error.value).not.toContain('Mon Apr 17 2026')
  })
})
