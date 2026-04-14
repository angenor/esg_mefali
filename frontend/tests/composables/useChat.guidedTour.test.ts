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

// Mock useGuidedTour — on capture les appels a startTour
const mockStartTour = vi.fn()
vi.mock('~/composables/useGuidedTour', () => ({
  useGuidedTour: () => ({
    startTour: mockStartTour,
    cancelTour: vi.fn(),
    tourState: { value: 'idle' },
    // Story 6.4 — compteurs adaptatifs (FR17)
    guidanceRefusalCount: { value: 0 },
    guidanceAcceptanceCount: { value: 0 },
    incrementGuidanceRefusal: vi.fn(),
    incrementGuidanceAcceptance: vi.fn(),
    resetGuidanceStats: vi.fn(),
    computeEffectiveCountdown: vi.fn((c: number) => c),
  }),
}))

// Mock useRuntimeConfig
vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api' },
}))

// Mock crypto.randomUUID
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

// ── Helper : creer un ReadableStream simule a partir de lignes SSE ──
function createMockSSEStream(events: Array<Record<string, unknown>>): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  const lines = events.map(e => `data: ${JSON.stringify(e)}`).join('\n') + '\n'
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(lines))
      controller.close()
    },
  })
}

// Reset module-level state
async function resetModuleState() {
  const { useChat } = await import('~/composables/useChat')
  const chat = useChat()
  chat.conversations.value = []
  chat.currentConversation.value = null
  chat.messages.value = []
  chat.isStreaming.value = false
  chat.streamingContent.value = ''
  chat.error.value = ''
  chat.documentProgress.value = null
  chat.reportSuggestion.value = null
  chat.activeToolCall.value = null
  chat.currentInteractiveQuestion.value = null
  chat.interactiveQuestionsByMessage.value = {}
  chat.searchQuery.value = ''
}

describe('useChat — guided_tour SSE event handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    mockStartTour.mockClear()
  })

  afterEach(async () => {
    await resetModuleState()
  })

  it('appelle startTour quand un event guided_tour est recu dans sendMessage', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    // Simuler une conversation active
    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = []

    const sseEvents = [
      { type: 'token', content: 'Je vais vous montrer.' },
      { type: 'guided_tour', tour_id: 'show_esg_results', context: { score: 72 } },
      { type: 'done', message_id: 'msg-final' },
    ]

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    })
    vi.stubGlobal('fetch', mockFetch)

    await chat.sendMessage('Montre-moi les resultats ESG')

    expect(mockStartTour).toHaveBeenCalledOnce()
    expect(mockStartTour).toHaveBeenCalledWith('show_esg_results', { score: 72 })
  })

  it('appelle startTour avec context vide si context absent', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = []

    const sseEvents = [
      { type: 'guided_tour', tour_id: 'show_dashboard_overview' },
      { type: 'done', message_id: 'msg-final' },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    }))

    await chat.sendMessage('Montre-moi le dashboard')

    expect(mockStartTour).toHaveBeenCalledOnce()
    expect(mockStartTour).toHaveBeenCalledWith('show_dashboard_overview', {})
  })

  it('bloque le tour et envoie un addSystemMessage si une question interactive est pending', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = []

    // Simuler une question interactive pending
    chat.currentInteractiveQuestion.value = {
      id: 'iq-pending',
      conversation_id: 'conv-1',
      question_type: 'qcu',
      prompt: 'Quel secteur ?',
      options: [{ id: 'a', label: 'Agri' }],
      min_selections: 1,
      max_selections: 1,
      requires_justification: false,
      justification_prompt: null,
      module: 'chat',
      created_at: new Date().toISOString(),
      state: 'pending',
      response_values: null,
      response_justification: null,
      answered_at: null,
    }

    const sseEvents = [
      { type: 'guided_tour', tour_id: 'show_esg_results', context: {} },
      { type: 'done', message_id: 'msg-x' },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    }))

    await chat.sendMessage('test')

    // startTour NE doit PAS etre appele
    expect(mockStartTour).not.toHaveBeenCalled()
    // Un message systeme doit informer l'utilisateur
    const sysMsg = chat.messages.value.find(m => m.content.includes('Repondez d\'abord'))
    expect(sysMsg).toBeDefined()
  })

  it('rattrape les rejets asynchrones de startTour sans propager', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    mockStartTour.mockRejectedValueOnce(new Error('driverjs load failed'))

    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = []

    const sseEvents = [
      { type: 'guided_tour', tour_id: 'show_esg_results', context: {} },
      { type: 'done', message_id: 'msg-y' },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    }))

    // Aucune exception ne doit remonter
    await expect(chat.sendMessage('test')).resolves.not.toThrow()
    expect(warnSpy).toHaveBeenCalledWith(
      '[useChat] Echec declenchement guided tour',
      expect.any(Error),
    )
    warnSpy.mockRestore()
  })

  it('ignore un event guided_tour sans tour_id', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = []

    const sseEvents = [
      { type: 'guided_tour' }, // pas de tour_id
      { type: 'done', message_id: 'msg-final' },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    }))

    await chat.sendMessage('test')

    expect(mockStartTour).not.toHaveBeenCalled()
  })

  it('appelle startTour dans submitInteractiveAnswer quand un event guided_tour est recu', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()

    chat.currentConversation.value = { id: 'conv-1', title: 'Test', created_at: '', updated_at: '' }
    chat.messages.value = [
      { id: 'msg-1', role: 'assistant', content: 'Question' },
    ]

    // Simuler une question interactive en cours
    chat.currentInteractiveQuestion.value = {
      id: 'iq-1',
      conversation_id: 'conv-1',
      question_type: 'qcu',
      prompt: 'Quel secteur ?',
      options: [{ id: 'opt1', label: 'Agriculture' }],
      min_selections: 1,
      max_selections: 1,
      requires_justification: false,
      justification_prompt: null,
      module: 'chat',
      created_at: new Date().toISOString(),
      state: 'pending',
      response_values: null,
      response_justification: null,
      answered_at: null,
    }

    const sseEvents = [
      { type: 'token', content: 'Merci, je vais vous guider.' },
      { type: 'guided_tour', tour_id: 'show_carbon_results', context: { total_tco2: 47 } },
      { type: 'done', message_id: 'msg-2' },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream(sseEvents),
    }))

    await chat.submitInteractiveAnswer('iq-1', {
      values: ['opt1'],
    })

    expect(mockStartTour).toHaveBeenCalledOnce()
    expect(mockStartTour).toHaveBeenCalledWith('show_carbon_results', { total_tco2: 47 })
  })
})
