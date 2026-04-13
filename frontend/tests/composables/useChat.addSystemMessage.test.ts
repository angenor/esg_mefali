import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks des composables Nuxt et stores ──
vi.mock('~/stores/auth', () => ({
  useAuthStore: () => ({ accessToken: 'test-token' }),
}))

vi.mock('~/stores/company', () => ({
  useCompanyStore: () => ({
    addProfileUpdate: vi.fn(),
    updateProfileField: vi.fn(),
    setCompletion: vi.fn(),
  }),
}))

vi.mock('~/stores/ui', () => ({
  useUiStore: () => ({ currentPage: '/' }),
}))

// Mock useRuntimeConfig (auto-import Nuxt)
vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api' },
}))

// Mock crypto.randomUUID
let uuidCounter = 0
vi.stubGlobal('crypto', {
  randomUUID: () => `sys-msg-uuid-${++uuidCounter}`,
})

describe('useChat — addSystemMessage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    uuidCounter = 0
  })

  afterEach(async () => {
    // Reset module-level state
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.messages.value = []
  })

  it('ajoute un message assistant local dans messages', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    expect(chat.messages.value).toHaveLength(0)

    chat.addSystemMessage('Bienvenue dans le parcours guidé !')

    expect(chat.messages.value).toHaveLength(1)
    const msg = chat.messages.value[0]!
    expect(msg.role).toBe('assistant')
    expect(msg.content).toBe('Bienvenue dans le parcours guidé !')
    expect(msg.id).toMatch(/^sys-msg-uuid-/)
    expect(msg.created_at).toBeDefined()
  })

  it('n\'a pas de conversation_id (message local, pas persiste)', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.addSystemMessage('Message local')

    const msg = chat.messages.value[0]!
    expect(msg).not.toHaveProperty('conversation_id')
  })

  it('preserve les messages existants (immutabilite)', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    // Ajouter un message existant
    chat.messages.value = [{
      id: 'existing-1',
      role: 'user',
      content: 'Bonjour',
      created_at: '2026-01-01T00:00:00.000Z',
    }]

    const oldRef = chat.messages.value

    chat.addSystemMessage('Reponse systeme')

    // Nouvelle reference (immutabilite)
    expect(chat.messages.value).not.toBe(oldRef)
    expect(chat.messages.value).toHaveLength(2)
    expect(chat.messages.value[0]!.id).toBe('existing-1')
    expect(chat.messages.value[1]!.content).toBe('Reponse systeme')
  })

  it('n\'envoie rien au backend (pas de fetch)', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.addSystemMessage('Message local uniquement')

    expect(fetchSpy).not.toHaveBeenCalled()
    fetchSpy.mockRestore()
  })

  it('est expose dans le return de useChat()', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    expect(chat.addSystemMessage).toBeDefined()
    expect(typeof chat.addSystemMessage).toBe('function')
  })
})
