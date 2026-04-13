import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUiStore } from '~/stores/ui'

describe('useUiStore — chatWidgetMinimized et guidedTourActive (Story 5.2)', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('chatWidgetMinimized est initialise a false', () => {
    const store = useUiStore()
    expect(store.chatWidgetMinimized).toBe(false)
  })

  it('guidedTourActive est initialise a false', () => {
    const store = useUiStore()
    expect(store.guidedTourActive).toBe(false)
  })

  it('chatWidgetMinimized est reactif et modifiable', () => {
    const store = useUiStore()
    store.chatWidgetMinimized = true
    expect(store.chatWidgetMinimized).toBe(true)
    store.chatWidgetMinimized = false
    expect(store.chatWidgetMinimized).toBe(false)
  })

  it('guidedTourActive est reactif et modifiable', () => {
    const store = useUiStore()
    store.guidedTourActive = true
    expect(store.guidedTourActive).toBe(true)
    store.guidedTourActive = false
    expect(store.guidedTourActive).toBe(false)
  })

  it('chatWidgetMinimized est expose dans le store', () => {
    const store = useUiStore()
    expect('chatWidgetMinimized' in store).toBe(true)
  })

  it('guidedTourActive est expose dans le store', () => {
    const store = useUiStore()
    expect('guidedTourActive' in store).toBe(true)
  })
})
