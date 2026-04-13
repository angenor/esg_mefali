import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUiStore } from '~/stores/ui'

describe('useUiStore — dead code cleanup (Story 2.2 — AC4)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('chatPanelOpen n\'existe plus dans le store', () => {
    const store = useUiStore()
    expect('chatPanelOpen' in store).toBe(false)
  })

  it('toggleChatPanel n\'existe plus dans le store', () => {
    const store = useUiStore()
    expect('toggleChatPanel' in store).toBe(false)
  })

  it('chatWidgetOpen existe toujours (non affecte)', () => {
    const store = useUiStore()
    expect('chatWidgetOpen' in store).toBe(true)
    expect(store.chatWidgetOpen).toBe(false)
  })

  it('toggleChatWidget fonctionne toujours', () => {
    const store = useUiStore()
    expect(store.chatWidgetOpen).toBe(false)
    store.toggleChatWidget()
    expect(store.chatWidgetOpen).toBe(true)
  })

  it('openChatWidget ouvre le widget', () => {
    const store = useUiStore()
    expect(store.chatWidgetOpen).toBe(false)
    store.openChatWidget()
    expect(store.chatWidgetOpen).toBe(true)
  })
})
