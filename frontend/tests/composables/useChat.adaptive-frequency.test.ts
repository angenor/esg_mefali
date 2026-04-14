import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks des stores Nuxt ──
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
  useUiStore: () => ({ currentPage: '/dashboard' }),
}))

// Mock useGuidedTour — on capture les increments + startTour
const mockStartTour = vi.fn()
const mockIncrementRefusal = vi.fn()
const mockIncrementAcceptance = vi.fn()
const mockGuidanceRefusalCount = { value: 0 }
const mockGuidanceAcceptanceCount = { value: 0 }

vi.mock('~/composables/useGuidedTour', () => ({
  useGuidedTour: () => ({
    startTour: mockStartTour,
    cancelTour: vi.fn(),
    tourState: { value: 'idle' },
    guidanceRefusalCount: mockGuidanceRefusalCount,
    guidanceAcceptanceCount: mockGuidanceAcceptanceCount,
    incrementGuidanceRefusal: mockIncrementRefusal,
    incrementGuidanceAcceptance: mockIncrementAcceptance,
    resetGuidanceStats: vi.fn(),
    computeEffectiveCountdown: vi.fn((c: number) => c),
  }),
}))

vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api' },
}))

vi.stubGlobal('crypto', {
  randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8),
})

// ── Helper : creer un ReadableStream SSE a partir d'events ──
function createMockSSEStream(
  events: Array<Record<string, unknown>>,
): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  const lines = events.map(e => `data: ${JSON.stringify(e)}`).join('\n') + '\n'
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(lines))
      controller.close()
    },
  })
}

// Reset module-level state entre les tests
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

describe('useChat — frequence adaptative (FR17 / story 6.4)', () => {
  beforeEach(async () => {
    await resetModuleState()
    vi.restoreAllMocks()
    mockStartTour.mockClear()
    mockIncrementRefusal.mockClear()
    mockIncrementAcceptance.mockClear()
    mockGuidanceRefusalCount.value = 0
    mockGuidanceAcceptanceCount.value = 0
  })

  afterEach(async () => {
    await resetModuleState()
  })

  // ── AC2 : FormData inclut guidance_stats (sendMessage) ──
  it('sendMessage appends guidance_stats to FormData with correct JSON shape', async () => {
    mockGuidanceRefusalCount.value = 2
    mockGuidanceAcceptanceCount.value = 1

    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-1', title: 'Test', created_at: '', updated_at: '',
    }

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream([{ type: 'token', content: 'ok' }]),
    })
    vi.stubGlobal('fetch', fetchMock)

    await chat.sendMessage('hello')

    expect(fetchMock).toHaveBeenCalled()
    const formData = fetchMock.mock.calls[0]![1].body as FormData
    const guidanceRaw = formData.get('guidance_stats')
    expect(guidanceRaw).toBeTruthy()
    expect(JSON.parse(guidanceRaw as string)).toEqual({
      refusal_count: 2,
      acceptance_count: 1,
    })
  })

  // ── AC2 : FormData inclut guidance_stats (submitInteractiveAnswer) ──
  it('submitInteractiveAnswer appends guidance_stats to FormData', async () => {
    mockGuidanceRefusalCount.value = 4
    mockGuidanceAcceptanceCount.value = 2

    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-2', title: 'Test', created_at: '', updated_at: '',
    }
    chat.currentInteractiveQuestion.value = {
      id: 'iq-1',
      conversation_id: 'conv-2',
      question_type: 'qcu',
      prompt: '?',
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
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

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: createMockSSEStream([{ type: 'token', content: 'ok' }]),
    })
    vi.stubGlobal('fetch', fetchMock)

    await chat.submitInteractiveAnswer('iq-1', { values: ['yes'] })

    const formData = fetchMock.mock.calls[0]![1].body as FormData
    const guidanceRaw = formData.get('guidance_stats')
    expect(JSON.parse(guidanceRaw as string)).toEqual({
      refusal_count: 4,
      acceptance_count: 2,
    })
  })

  // ── AC5 : « Non merci » sur consent question → incrementGuidanceRefusal ──
  it('"Non merci" option id=no on consent question triggers incrementGuidanceRefusal exactly once', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-3', title: 'Test', created_at: '', updated_at: '',
    }
    chat.currentInteractiveQuestion.value = {
      id: 'iq-consent',
      conversation_id: 'conv-3',
      question_type: 'qcu',
      prompt: 'Veux-tu que je te montre ?',
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
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

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([{ type: 'token', content: 'ok' }]),
      }),
    )

    await chat.submitInteractiveAnswer('iq-consent', { values: ['no'] })

    expect(mockIncrementRefusal).toHaveBeenCalledTimes(1)
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })

  // ── Review 6.4 P5 : direct trigger (sendMessage, sans consent widget) → PAS d'increment ──
  it('guided_tour event after sendMessage (direct trigger, no consent widget) does NOT increment acceptance', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-4', title: 'Test', created_at: '', updated_at: '',
    }

    // startTour reussit (completed=true), mais comme le flag consent n'est pas arme,
    // l'acceptance ne doit PAS etre creditee (declenchement direct explicite).
    mockStartTour.mockResolvedValue(true)

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'ok' },
          {
            type: 'guided_tour',
            tour_id: 'show_esg_results',
            context: { score: 72 },
          },
        ]),
      }),
    )

    await chat.sendMessage('montre-moi')

    expect(mockStartTour).toHaveBeenCalledTimes(1)
    expect(mockStartTour).toHaveBeenCalledWith('show_esg_results', { score: 72 })
    // Pas de consent precedent → pas d'increment acceptance
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })

  // ── Review 6.4 P4+P5 : consent widget → yes → guided_tour + startTour reussi → increment acceptance APRES startTour ──
  it('consent widget yes → guided_tour → increment acceptance ONLY after startTour succeeds', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-4b', title: 'Test', created_at: '', updated_at: '',
    }
    chat.currentInteractiveQuestion.value = {
      id: 'iq-consent',
      conversation_id: 'conv-4b',
      question_type: 'qcu',
      prompt: 'Veux-tu voir ?',
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
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

    const callOrder: string[] = []
    mockIncrementAcceptance.mockImplementation(() => callOrder.push('inc'))
    mockStartTour.mockImplementation(async () => {
      callOrder.push('start')
      return true // tour completed successfully
    })

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'ok' },
          {
            type: 'guided_tour',
            tour_id: 'show_esg_results',
            context: {},
          },
        ]),
      }),
    )

    await chat.submitInteractiveAnswer('iq-consent', { values: ['yes'] })

    expect(mockStartTour).toHaveBeenCalledTimes(1)
    expect(mockIncrementAcceptance).toHaveBeenCalledTimes(1)
    // Increment APRES startTour (review P4)
    expect(callOrder).toEqual(['start', 'inc'])
  })

  // ── Review 6.4 P4 : consent widget → yes → startTour echoue → PAS d'increment ──
  it('consent widget yes → startTour fails (returns false) → NO increment acceptance', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-4c', title: 'Test', created_at: '', updated_at: '',
    }
    chat.currentInteractiveQuestion.value = {
      id: 'iq-consent-fail',
      conversation_id: 'conv-4c',
      question_type: 'qcu',
      prompt: '?',
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
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

    mockStartTour.mockResolvedValue(false) // tour did not complete (invalid tour_id, DOM missing, etc.)

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([
          { type: 'guided_tour', tour_id: 'show_esg_results', context: {} },
        ]),
      }),
    )

    await chat.submitInteractiveAnswer('iq-consent-fail', { values: ['yes'] })

    expect(mockStartTour).toHaveBeenCalled()
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })

  // ── AC5 : tour_id invalide → PAS d'increment acceptance ──
  it('guided_tour event with invalid tour_id does NOT increment acceptance', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-5', title: 'Test', created_at: '', updated_at: '',
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([
          { type: 'guided_tour', tour_id: '', context: {} },
          { type: 'guided_tour', tour_id: 123, context: {} },
          { type: 'guided_tour' }, // aucun tour_id
        ]),
      }),
    )

    await chat.sendMessage('test')

    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
    expect(mockStartTour).not.toHaveBeenCalled()
  })

  // ── AC5 : « no » sur question NON-consentement → PAS d'increment refusal ──
  it('non-consent interactive question resolved with "no" does NOT increment refusal', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-6', title: 'Test', created_at: '', updated_at: '',
    }
    // Question ESG classique avec yes/no mais labels NON canoniques → heuristique rejette
    chat.currentInteractiveQuestion.value = {
      id: 'iq-esg',
      conversation_id: 'conv-6',
      question_type: 'qcu',
      prompt: 'As-tu une politique anti-corruption ?',
      options: [
        { id: 'yes', label: 'Oui' },
        { id: 'no', label: 'Non' },
      ],
      min_selections: 1,
      max_selections: 1,
      requires_justification: false,
      justification_prompt: null,
      module: 'esg_scoring',
      created_at: new Date().toISOString(),
      state: 'pending',
      response_values: null,
      response_justification: null,
      answered_at: null,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([{ type: 'token', content: 'ok' }]),
      }),
    )

    await chat.submitInteractiveAnswer('iq-esg', { values: ['no'] })

    expect(mockIncrementRefusal).not.toHaveBeenCalled()
  })
})
