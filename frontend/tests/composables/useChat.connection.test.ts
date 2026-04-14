import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import fs from 'fs'
import path from 'path'

// ═════════════════════════════════════════════════════════════════════
// Story 7.3 — Tests resilience SSE et indicateur de reconnexion
// Couvre AC1/AC2 (ref + listeners), AC3 (classification fetch errors),
// AC4 (badge visuel), AC5 (reprise), AC6 (hint ChatInput),
// AC7/AC8 (isolation Driver.js), AC10 (invariant source).
// ═════════════════════════════════════════════════════════════════════

// ── Mocks stores (stateful, mutables par test) ──
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

// useGuidedTour est charge statiquement dans useChat.ts (ligne 15).
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

vi.stubGlobal('crypto', { randomUUID: () => 'mock-uuid-' + Math.random().toString(36).slice(2, 8) })

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

// Helper : reimporter useChat avec un state module-level propre.
// navigatorOnline permet de controler la valeur initiale de isConnected
// (l'IIFE au top-level du module lit navigator.onLine une seule fois).
async function importUseChatFresh(opts: { navigatorOnline?: boolean } = {}) {
  vi.resetModules()
  Object.defineProperty(navigator, 'onLine', {
    configurable: true,
    value: opts.navigatorOnline ?? true,
  })
  const mod = await import('~/composables/useChat')
  return mod.useChat()
}

beforeEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
  mockUiStore.currentPage = '/'
  mockUiStore.guidedTourActive = false
  mockAuthStore.accessToken = 'test-token'
})

afterEach(() => {
  // Remettre navigator.onLine a true pour eviter les effets de bord.
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 1 : Ref isConnected initiale (AC1, AC2)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 1 : isConnected ref initiale + listeners online/offline', () => {
  it('test_isConnected_initial_value_is_true_when_navigator_online_true', async () => {
    const chat = await importUseChatFresh({ navigatorOnline: true })
    expect(chat.isConnected.value).toBe(true)
  })

  it('test_isConnected_initial_value_is_false_when_navigator_offline', async () => {
    const chat = await importUseChatFresh({ navigatorOnline: false })
    expect(chat.isConnected.value).toBe(false)
  })

  it('test_online_event_switches_isConnected_to_true', async () => {
    const chat = await importUseChatFresh({ navigatorOnline: false })
    expect(chat.isConnected.value).toBe(false)
    window.dispatchEvent(new Event('online'))
    expect(chat.isConnected.value).toBe(true)
  })

  it('test_offline_event_switches_isConnected_to_false', async () => {
    const chat = await importUseChatFresh({ navigatorOnline: true })
    expect(chat.isConnected.value).toBe(true)
    window.dispatchEvent(new Event('offline'))
    expect(chat.isConnected.value).toBe(false)
  })

  it('test_connection_listeners_installed_once_across_multiple_useChat_calls', async () => {
    vi.resetModules()
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
    const spy = vi.spyOn(window, 'addEventListener')
    const mod = await import('~/composables/useChat')
    // Appeler useChat() plusieurs fois.
    mod.useChat()
    mod.useChat()
    mod.useChat()
    const onlineCalls = spy.mock.calls.filter(c => c[0] === 'online').length
    const offlineCalls = spy.mock.calls.filter(c => c[0] === 'offline').length
    expect(onlineCalls).toBe(1)
    expect(offlineCalls).toBe(1)
    spy.mockRestore()
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 2 : Classification des erreurs fetch (AC3)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 2 : classification des erreurs fetch', () => {
  async function setupChatWithConversation() {
    const chat = await importUseChatFresh({ navigatorOnline: true })
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    return chat
  }

  it('test_AbortError_does_not_affect_isConnected', async () => {
    const chat = await setupChatWithConversation()
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(
      new DOMException('aborted', 'AbortError'),
    ))
    await chat.sendMessage('hello')
    expect(chat.isConnected.value).toBe(true)
    expect(chat.error.value).toBe('')
  })

  it('test_TypeError_failed_to_fetch_sets_isConnected_false', async () => {
    const chat = await setupChatWithConversation()
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(
      new TypeError('Failed to fetch'),
    ))
    await chat.sendMessage('hello')
    expect(chat.isConnected.value).toBe(false)
    expect(chat.error.value).toContain('Connexion perdue')
  })

  it('test_NetworkError_message_triggers_disconnection', async () => {
    const chat = await setupChatWithConversation()
    // Cas Firefox : Error (non TypeError) avec message NetworkError.
    const err = new Error('NetworkError when attempting to fetch resource.')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(err))
    await chat.sendMessage('hello')
    expect(chat.isConnected.value).toBe(false)
  })

  it('test_HTTP_500_does_not_affect_isConnected', async () => {
    const chat = await setupChatWithConversation()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      body: null,
    }))
    await chat.sendMessage('hello')
    expect(chat.isConnected.value).toBe(true)
    // Erreur technique renvoyee par le throw 'Erreur lors de l\'envoi du message'
    expect(chat.error.value.toLowerCase()).toContain('erreur lors de')
  })

  it('test_reader_error_during_streaming_sets_isConnected_false', async () => {
    const chat = await setupChatWithConversation()
    // Stream qui throw au second read() via une queue strategy personnalisee.
    const brokenStream = new ReadableStream<Uint8Array>({
      start(controller) {
        const encoder = new TextEncoder()
        controller.enqueue(encoder.encode('data: {"type":"token","content":"hi"}\n'))
        // Simuler une coupure reseau apres le premier chunk.
        controller.error(new TypeError('Network error during read'))
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: true,
      body: brokenStream,
    }))
    await chat.sendMessage('hello')
    expect(chat.isConnected.value).toBe(false)
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 3 : Reprise de connexion (AC5)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 3 : reprise de connexion', () => {
  it('test_isConnected_becomes_true_on_first_successful_chunk_read', async () => {
    // Partir en offline : navigator.onLine = false => isConnected init a false.
    const chat = await importUseChatFresh({ navigatorOnline: false })
    expect(chat.isConnected.value).toBe(false)
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: true,
      body: createMockSSEStream([
        { type: 'token', content: 'Bonjour' },
        { type: 'done', message_id: 'msg-ok' },
      ]),
    }))
    await chat.sendMessage('test')
    expect(chat.isConnected.value).toBe(true)
  })

  it('test_online_event_clears_connection_error_message', async () => {
    const chat = await importUseChatFresh({ navigatorOnline: false })
    chat.error.value = 'Connexion perdue. Verifiez votre reseau.'
    window.dispatchEvent(new Event('online'))
    expect(chat.isConnected.value).toBe(true)
    expect(chat.error.value).toBe('')
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 4 : Isolation guidage Driver.js (AC7, AC8)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 4 : isolation guidage Driver.js', () => {
  it('test_driverjs_tour_continues_when_connection_lost', async () => {
    mockUiStore.guidedTourActive = true
    const chat = await importUseChatFresh({ navigatorOnline: true })
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(
      new TypeError('Failed to fetch'),
    ))
    await chat.sendMessage('test')
    expect(chat.isConnected.value).toBe(false)
    // Invariant AC7/AC8 : on ne doit pas avoir appele cancelTour ni touche a tourState.
    expect(mockGuided.cancelTour).not.toHaveBeenCalled()
    expect(mockGuided.tourState.value).toBe('idle')
  })

  it('test_network_error_during_guided_tour_skips_system_message', async () => {
    mockUiStore.guidedTourActive = true
    const chat = await importUseChatFresh({ navigatorOnline: true })
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    const before = chat.messages.value.length
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(
      new TypeError('Failed to fetch'),
    ))
    await chat.sendMessage('test')
    // On a ajoute 1 message utilisateur, mais AUCUN message systeme supplementaire.
    expect(chat.messages.value.length).toBe(before + 1)
    expect(chat.messages.value.every(m => m.role !== 'assistant')).toBe(true)
    // error.value ne doit pas contenir le message "Connexion perdue" (masque pendant guidage).
    expect(chat.error.value).toBe('')
  })

  it('test_network_error_outside_guided_tour_sets_connexion_perdue_error', async () => {
    mockUiStore.guidedTourActive = false
    const chat = await importUseChatFresh({ navigatorOnline: true })
    chat.currentConversation.value = {
      id: 'conv-1',
      title: 'Test',
      current_module: 'chat',
      created_at: '',
      updated_at: '',
    }
    vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(
      new TypeError('Failed to fetch'),
    ))
    await chat.sendMessage('test')
    expect(chat.error.value).toBe('Connexion perdue. Verifiez votre reseau.')
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 5 : Composant ConnectionStatusBadge.vue (AC4)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 5 : ConnectionStatusBadge', () => {
  async function importBadge() {
    const mod = await import('~/components/copilot/ConnectionStatusBadge.vue')
    return mod.default
  }

  it('test_badge_not_rendered_when_connected', async () => {
    const Badge = await importBadge()
    const wrapper = mount(Badge, { props: { isConnected: true } })
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
  })

  it('test_badge_rendered_with_reconnexion_text_when_disconnected', async () => {
    const Badge = await importBadge()
    const wrapper = mount(Badge, { props: { isConnected: false } })
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Reconnexion...')
  })

  it('test_badge_has_dark_mode_classes', async () => {
    const Badge = await importBadge()
    const wrapper = mount(Badge, { props: { isConnected: false } })
    const html = wrapper.html()
    expect(html).toContain('dark:bg-amber-900/20')
    expect(html).toContain('dark:text-amber-300')
    expect(html).toContain('dark:border-amber-800/50')
  })

  it('test_badge_has_aria_live_polite', async () => {
    const Badge = await importBadge()
    const wrapper = mount(Badge, { props: { isConnected: false } })
    const el = wrapper.find('[role="status"]')
    expect(el.attributes('aria-live')).toBe('polite')
    expect(el.attributes('role')).toBe('status')
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 6 : ChatInput hint (AC6)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 6 : ChatInput disable + hint', () => {
  async function importChatInput() {
    const mod = await import('~/components/chat/ChatInput.vue')
    return mod.default
  }

  it('test_chat_input_disabled_when_disconnected', async () => {
    const ChatInput = await importChatInput()
    // isConnected=false => le parent passe :disabled="isStreaming || !isConnected" = true.
    const wrapper = mount(ChatInput, {
      props: { disabled: true, hint: 'Connexion perdue. Les envois reprendront après reconnexion.' },
    })
    const textarea = wrapper.find('textarea')
    expect(textarea.exists()).toBe(true)
    expect(textarea.attributes('disabled')).toBeDefined()
  })

  it('test_chat_input_shows_hint_when_disconnected', async () => {
    const ChatInput = await importChatInput()
    const wrapper = mount(ChatInput, {
      props: { disabled: true, hint: 'Connexion perdue. Les envois reprendront après reconnexion.' },
    })
    const hint = wrapper.find('[data-testid="chat-input-hint"]')
    expect(hint.exists()).toBe(true)
    expect(hint.text()).toContain('Connexion perdue')
    expect(hint.text()).toContain('reprendront après reconnexion')
  })

  it('test_chat_input_hint_hidden_when_connected', async () => {
    const ChatInput = await importChatInput()
    const wrapper = mount(ChatInput, {
      props: { disabled: false, hint: null },
    })
    expect(wrapper.find('[data-testid="chat-input-hint"]').exists()).toBe(false)
  })
})

// ═════════════════════════════════════════════════════════════════════
// Bloc 7 : Invariant d'isolation — useGuidedTour ne reference pas isConnected (AC8)
// ═════════════════════════════════════════════════════════════════════

describe('Story 7.3 — Bloc 7 : invariant useGuidedTour sans isConnected', () => {
  it('test_useGuidedTour_source_does_not_reference_isConnected', () => {
    const filePath = path.resolve(
      process.cwd(),
      'app/composables/useGuidedTour.ts',
    )
    const src = fs.readFileSync(filePath, 'utf8')
    expect(src).not.toMatch(/isConnected/)
  })
})
