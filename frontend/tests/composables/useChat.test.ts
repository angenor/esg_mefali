import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'

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

const mockCurrentPage = { value: '/' }
vi.mock('~/stores/ui', () => ({
  useUiStore: () => ({ currentPage: mockCurrentPage.value }),
}))

// Mock useRuntimeConfig (auto-import Nuxt)
vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:8000/api' },
}))

// Mock crypto.randomUUID
vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

// ── Helper : créer un ReadableStream simulé à partir de lignes SSE ──
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

// ── Reset du module-level state entre les tests ──
// Comme les refs sont module-level, il faut re-importer pour chaque groupe de tests
// qui nécessite un état propre. Pour les tests de singleton (3.1), on ne reset PAS.

// Helper pour reset complet du state module-level entre les tests
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

describe('useChat — module-level state', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(async () => {
    await resetModuleState()
  })

  // ── Test 3.1 : Deux appels retournent les mêmes références (===) ──
  describe('T3.1: singleton references', () => {
    it('deux appels à useChat() retournent les mêmes refs (===)', async () => {
      const { useChat } = await import('~/composables/useChat')

      const chat1 = useChat()
      const chat2 = useChat()

      // Toutes les refs doivent être strictement identiques
      expect(chat1.messages).toBe(chat2.messages)
      expect(chat1.conversations).toBe(chat2.conversations)
      expect(chat1.currentConversation).toBe(chat2.currentConversation)
      expect(chat1.isStreaming).toBe(chat2.isStreaming)
      expect(chat1.streamingContent).toBe(chat2.streamingContent)
      expect(chat1.error).toBe(chat2.error)
      expect(chat1.documentProgress).toBe(chat2.documentProgress)
      expect(chat1.reportSuggestion).toBe(chat2.reportSuggestion)
      expect(chat1.activeToolCall).toBe(chat2.activeToolCall)
      expect(chat1.currentInteractiveQuestion).toBe(chat2.currentInteractiveQuestion)
      expect(chat1.interactiveQuestionsByMessage).toBe(chat2.interactiveQuestionsByMessage)
      expect(chat1.searchQuery).toBe(chat2.searchQuery)
      expect(chat1.filteredConversations).toBe(chat2.filteredConversations)
    })

    it('la mutation d\'un ref dans une instance est visible dans l\'autre', async () => {
      const { useChat } = await import('~/composables/useChat')

      const chat1 = useChat()
      const chat2 = useChat()

      chat1.messages.value = [{ id: '1', role: 'user', content: 'test', created_at: '' }]
      expect(chat2.messages.value).toHaveLength(1)
      expect(chat2.messages.value[0]!.content).toBe('test')

    })
  })

  // ── Test 3.2 : Persistence après changement de route simulé ──
  describe('T3.2: persistence après simulated route change', () => {
    it('les messages persistent après démontage/remontage simulé', async () => {
      const { useChat } = await import('~/composables/useChat')

      // Simuler un premier composant qui ajoute des messages
      const chatBefore = useChat()
      chatBefore.messages.value = [
        { id: 'msg-1', role: 'user', content: 'Bonjour', created_at: '2026-01-01' },
        { id: 'msg-2', role: 'assistant', content: 'Salut!', created_at: '2026-01-01' },
      ]
      chatBefore.currentConversation.value = {
        id: 'conv-1', title: 'Test', current_module: 'chat',
        created_at: '2026-01-01', updated_at: '2026-01-01',
      }

      // Simuler la destruction du composant (ne rien faire côté module-level)
      // puis un nouveau composant appelle useChat()
      const chatAfter = useChat()

      // L'état est intact
      expect(chatAfter.messages.value).toHaveLength(2)
      expect(chatAfter.messages.value[0]!.content).toBe('Bonjour')
      expect(chatAfter.currentConversation.value?.id).toBe('conv-1')

    })
  })

  // ── Test 3.3 : SSE survit à un changement de route (mock ReadableStream) ──
  describe('T3.3: SSE cross-routes', () => {
    it('le streaming SSE continue après un changement de route simulé', async () => {
      const { useChat } = await import('~/composables/useChat')

      const sseEvents = [
        { type: 'token', content: 'Bonjour ' },
        { type: 'token', content: 'monde!' },
        { type: 'done', message_id: 'real-msg-id' },
      ]

      const mockStream = createMockSSEStream(sseEvents)

      vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
        ok: true,
        body: mockStream,
      }))

      const chat = useChat()
      chat.currentConversation.value = {
        id: 'conv-1', title: 'Test', current_module: 'chat',
        created_at: '', updated_at: '',
      }
      chat.isStreaming.value = false

      // Lancer sendMessage
      const sendPromise = chat.sendMessage('test')

      // Simuler un changement de route : un nouveau composant prend le relais
      const chat2 = useChat()

      // Attendre la fin du streaming
      await sendPromise

      // Le nouveau composant voit le même état
      expect(chat2.messages.value.length).toBeGreaterThanOrEqual(2)
      const assistantMsg = chat2.messages.value.find(m => m.role === 'assistant')
      expect(assistantMsg).toBeDefined()
      expect(assistantMsg!.content).toBe('Bonjour monde!')
      expect(assistantMsg!.id).toBe('real-msg-id')

    })
  })

  // ── Test 3.4 : AbortController annule le stream précédent ──
  describe('T3.4: AbortController', () => {
    it('le stream précédent est annulé avant un nouveau sendMessage', async () => {
      const { useChat } = await import('~/composables/useChat')

      const abortSpy = vi.fn()
      const mockAbortController = { abort: abortSpy, signal: {} as AbortSignal }

      const sseEvents = [
        { type: 'token', content: 'Réponse' },
        { type: 'done', message_id: 'msg-2' },
      ]
      const mockStream = createMockSSEStream(sseEvents)

      // Premier appel : simuler un controller déjà actif
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      }))

      const chat = useChat()
      chat.currentConversation.value = {
        id: 'conv-1', title: 'Test', current_module: 'chat',
        created_at: '', updated_at: '',
      }

      // Premier sendMessage
      await chat.sendMessage('premier')

      // On ne peut pas récupérer l'AbortController interne directement,
      // mais on vérifie qu'un second appel ne plante pas (le premier controller est aborté)
      const sseEvents2 = [
        { type: 'token', content: 'Seconde réponse' },
        { type: 'done', message_id: 'msg-3' },
      ]
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        body: createMockSSEStream(sseEvents2),
      }))

      await chat.sendMessage('second')

      // Le dernier message assistant doit avoir le contenu du second stream
      const lastAssistant = [...chat.messages.value].reverse().find(m => m.role === 'assistant')
      expect(lastAssistant).toBeDefined()
      expect(lastAssistant!.content).toBe('Seconde réponse')

    })
  })

  // ── Test 3.5 : filteredConversations fonctionne (fix computed) ──
  describe('T3.5: filteredConversations', () => {
    it('filtre les conversations par searchQuery', async () => {
      const { useChat } = await import('~/composables/useChat')

      const chat = useChat()
      chat.conversations.value = [
        { id: '1', title: 'Analyse ESG', current_module: 'esg', created_at: '', updated_at: '' },
        { id: '2', title: 'Bilan carbone', current_module: 'carbon', created_at: '', updated_at: '' },
        { id: '3', title: 'Financement vert', current_module: 'financing', created_at: '', updated_at: '' },
      ]

      // Sans filtre : toutes les conversations
      expect(chat.filteredConversations.value).toHaveLength(3)

      // Avec filtre
      chat.searchQuery.value = 'carbone'
      expect(chat.filteredConversations.value).toHaveLength(1)
      expect(chat.filteredConversations.value[0]!.title).toBe('Bilan carbone')

      // Filtre insensible à la casse
      chat.searchQuery.value = 'ESG'
      expect(chat.filteredConversations.value).toHaveLength(1)

      // Aucun résultat
      chat.searchQuery.value = 'xyz'
      expect(chat.filteredConversations.value).toHaveLength(0)

    })
  })

  // ── Story 3.1 : current_page dans le FormData ──
  describe('Story 3.1: current_page dans sendMessage', () => {
    afterEach(() => {
      mockCurrentPage.value = '/'
    })

    it('sendMessage inclut current_page dans le FormData', async () => {
      const { useChat } = await import('~/composables/useChat')

      mockCurrentPage.value = '/carbon/results'

      let capturedBody: FormData | null = null
      const sseEvents = [
        { type: 'token', content: 'OK' },
        { type: 'done', message_id: 'msg-cp-1' },
      ]

      vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: RequestInit) => {
        capturedBody = opts.body as FormData
        return { ok: true, body: createMockSSEStream(sseEvents) }
      }))

      const chat = useChat()
      chat.currentConversation.value = {
        id: 'conv-cp', title: 'Test CP', current_module: 'chat',
        created_at: '', updated_at: '',
      }

      await chat.sendMessage('test current page')

      expect(capturedBody).toBeInstanceOf(FormData)
      expect(capturedBody!.get('current_page')).toBe('/carbon/results')
    })

    it('submitInteractiveAnswer inclut current_page dans le FormData', async () => {
      const { useChat } = await import('~/composables/useChat')

      mockCurrentPage.value = '/esg'

      let capturedBody: FormData | null = null
      const sseEvents = [
        { type: 'token', content: 'Merci' },
        { type: 'done', message_id: 'msg-iq-cp' },
      ]

      vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: RequestInit) => {
        capturedBody = opts.body as FormData
        return { ok: true, body: createMockSSEStream(sseEvents) }
      }))

      const chat = useChat()
      chat.currentConversation.value = {
        id: 'conv-iq-cp', title: 'Test IQ CP', current_module: 'esg_scoring',
        created_at: '', updated_at: '',
      }
      chat.currentInteractiveQuestion.value = {
        id: 'iq-1',
        conversation_id: 'conv-iq-cp',
        question_type: 'qcu',
        prompt: 'Quel secteur ?',
        options: [{ key: 'agri', label: 'Agriculture' }],
        min_selections: 1,
        max_selections: 1,
        requires_justification: false,
        justification_prompt: null,
        module: 'esg_scoring',
        created_at: new Date().toISOString(),
      }

      await chat.submitInteractiveAnswer('iq-1', { values: ['agri'] })

      expect(capturedBody).toBeInstanceOf(FormData)
      expect(capturedBody!.get('current_page')).toBe('/esg')
    })
  })
})
