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

// Mock useGuidedTour — on capture les appels a startTour + increments adaptatifs
const mockStartTour = vi.fn()
const mockIncrementRefusal = vi.fn()
const mockIncrementAcceptance = vi.fn()
vi.mock('~/composables/useGuidedTour', () => ({
  useGuidedTour: () => ({
    startTour: mockStartTour,
    cancelTour: vi.fn(),
    tourState: { value: 'idle' },
    // Story 6.4 — compteurs adaptatifs (FR17)
    guidanceRefusalCount: { value: 0 },
    guidanceAcceptanceCount: { value: 0 },
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

describe('useChat — consentement widget + declenchement guided_tour (story 6.3)', () => {
  beforeEach(async () => {
    // Reset AVANT chaque test aussi : `useChat` est un singleton module-level,
    // un etat laisse par un fichier de test voisin pourrait fuir ici.
    await resetModuleState()
    vi.restoreAllMocks()
    mockStartTour.mockClear()
    mockIncrementRefusal.mockClear()
    mockIncrementAcceptance.mockClear()
  })

  afterEach(async () => {
    await resetModuleState()
  })

  // ── T-AC2 : consentement accepte → trigger_guided_tour fire ──
  it('T-AC2 — cycle complet : interactive_question pending → answered → guided_tour declenche startTour', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      created_at: '',
      updated_at: '',
    }
    chat.messages.value = [
      { id: 'msg-ask', role: 'assistant', content: 'Evaluation terminee !' },
    ]

    // Phase 1 : tour LLM qui pose la question de consentement
    const sseEventsQuestion = [
      { type: 'token', content: 'Evaluation terminee ! ' },
      {
        type: 'interactive_question',
        id: 'iq-consent',
        conversation_id: 'conv-1',
        question_type: 'qcu',
        prompt: 'Veux-tu que je te montre tes resultats ?',
        options: [
          { id: 'yes', label: 'Oui, montre-moi', emoji: '👀' },
          { id: 'no', label: 'Non merci', emoji: '🙏' },
        ],
        min_selections: 1,
        max_selections: 1,
      },
      { type: 'done', message_id: 'msg-ask' },
    ]

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseEventsQuestion),
      }),
    )

    await chat.sendMessage('je veux voir')

    // Apres Phase 1 : question `pending`, aucun tour declenche
    expect(chat.currentInteractiveQuestion.value?.state).toBe('pending')
    expect(chat.currentInteractiveQuestion.value?.id).toBe('iq-consent')
    expect(mockStartTour).not.toHaveBeenCalled()

    // Phase 2 : utilisateur clique « Oui, montre-moi » → submitInteractiveAnswer
    // Le backend repond avec un guided_tour event au tour suivant
    const sseEventsTour = [
      { type: 'token', content: 'Parfait !' },
      {
        type: 'guided_tour',
        tour_id: 'show_esg_results',
        context: { pillar_top: 'Social' },
      },
      { type: 'done', message_id: 'msg-tour' },
    ]

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseEventsTour),
      }),
    )

    await chat.submitInteractiveAnswer('iq-consent', { values: ['yes'] })

    // Apres Phase 2 : question liberee (state passe a 'answered' localement,
    // puis currentInteractiveQuestion est remise a null), startTour appele
    expect(chat.currentInteractiveQuestion.value).toBeNull()
    expect(mockStartTour).toHaveBeenCalledOnce()
    expect(mockStartTour).toHaveBeenCalledWith('show_esg_results', {
      pillar_top: 'Social',
    })

    // Aucun message systeme de blocage n'a ete injecte
    const blocked = chat.messages.value.find(m =>
      m.content.includes("Repondez d'abord"),
    )
    expect(blocked).toBeUndefined()
  })

  // ── T-AC6 : verrou widget pending pendant un sendMessage ──
  it('T-AC6 — guided_tour arrivant tant qu\'une question est pending → startTour bloque + message systeme injecte', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-2',
      title: 'Test',
      created_at: '',
      updated_at: '',
    }
    chat.messages.value = []

    // Pre-condition : une question est deja pending (tour precedent l'avait posee)
    chat.currentInteractiveQuestion.value = {
      id: 'iq-pending',
      conversation_id: 'conv-2',
      question_type: 'qcu',
      prompt: 'Choix ?',
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

    // Le backend tente de declencher un tour alors que l'utilisateur
    // n'a pas encore repondu — garde cote frontend doit bloquer.
    const sseEvents = [
      {
        type: 'guided_tour',
        tour_id: 'show_carbon_results',
        context: {},
      },
      { type: 'done', message_id: 'msg-blocked' },
    ]

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseEvents),
      }),
    )

    await chat.sendMessage('autre chose')

    // La garde `pending` doit bloquer startTour
    expect(mockStartTour).not.toHaveBeenCalled()

    // Un message systeme « Repondez d'abord... » doit avoir ete ajoute
    // avec EXACTEMENT la chaine de useChat.ts:690
    const sysMsg = chat.messages.value.find(m =>
      m.content.includes("Repondez d'abord a la question en attente."),
    )
    expect(sysMsg).toBeDefined()
  })

  // ── T-AC3 (complementaire) : consentement refuse → pas de startTour ──
  it('T-AC3 — reponse « no » via submitInteractiveAnswer + aucun guided_tour dans la reponse → startTour non appele', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-3',
      title: 'Test',
      created_at: '',
      updated_at: '',
    }
    chat.messages.value = [
      { id: 'msg-ask', role: 'assistant', content: 'Proposition' },
    ]
    chat.currentInteractiveQuestion.value = {
      id: 'iq-refus',
      conversation_id: 'conv-3',
      question_type: 'qcu',
      prompt: 'Voir ?',
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

    // Le backend repond en texte libre, SANS event guided_tour
    const sseEvents = [
      { type: 'token', content: "Tres bien, on continue la conversation." },
      { type: 'done', message_id: 'msg-refus' },
    ]

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseEvents),
      }),
    )

    await chat.submitInteractiveAnswer('iq-refus', { values: ['no'] })

    expect(mockStartTour).not.toHaveBeenCalled()
    expect(chat.currentInteractiveQuestion.value).toBeNull()
    // Review 6.4 P18 — refus consent → increment refusal compteur (post-SSE round-trip)
    expect(mockIncrementRefusal).toHaveBeenCalledTimes(1)
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })

  // ── Review 6.4 P19 — edge case : submitInteractiveAnswer sans currentInteractiveQuestion ──
  it('submitInteractiveAnswer without currentInteractiveQuestion does NOT increment counters', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-null',
      title: 'Test',
      created_at: '',
      updated_at: '',
    }
    chat.currentInteractiveQuestion.value = null // aucune question active

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream([{ type: 'token', content: 'ok' }]),
      }),
    )

    await chat.submitInteractiveAnswer('iq-ghost', { values: ['no'] })

    expect(mockIncrementRefusal).not.toHaveBeenCalled()
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })

  // ── Review 6.4 P19 — edge case : question consent a 3 options → heuristique rejette ──
  it('3-option question is NOT detected as guidance consent (heuristic requires exactly 2 options)', async () => {
    const { useChat } = await import('~/composables/useChat')
    const chat = useChat()
    chat.currentConversation.value = {
      id: 'conv-3opt',
      title: 'Test',
      created_at: '',
      updated_at: '',
    }
    chat.currentInteractiveQuestion.value = {
      id: 'iq-3opt',
      conversation_id: 'conv-3opt',
      question_type: 'qcu',
      prompt: 'Que veux-tu voir ?',
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
        { id: 'maybe', label: 'Plus tard' },
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

    await chat.submitInteractiveAnswer('iq-3opt', { values: ['no'] })

    // 3 options → pas une question consent → ni refus ni acceptance
    expect(mockIncrementRefusal).not.toHaveBeenCalled()
    expect(mockIncrementAcceptance).not.toHaveBeenCalled()
  })
})
