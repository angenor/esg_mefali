import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUiStore } from '~/stores/ui'

describe('useUiStore — widget resize (Story 1.6)', () => {
  let pinia: ReturnType<typeof createPinia>
  const STORAGE_KEY = 'esg_mefali_widget_size'

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('valeurs par defaut', () => {
    it('chatWidgetWidth vaut 400 par defaut', () => {
      const store = useUiStore()
      expect(store.chatWidgetWidth).toBe(400)
    })

    it('chatWidgetHeight vaut 600 par defaut', () => {
      const store = useUiStore()
      expect(store.chatWidgetHeight).toBe(600)
    })
  })

  describe('setChatWidgetSize', () => {
    it('met a jour les dimensions du widget', () => {
      const store = useUiStore()
      store.setChatWidgetSize(500, 700)
      expect(store.chatWidgetWidth).toBe(500)
      expect(store.chatWidgetHeight).toBe(700)
    })

    it('persiste les dimensions dans localStorage', () => {
      const store = useUiStore()
      store.setChatWidgetSize(500, 700)
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY)!)
      expect(saved).toEqual({ width: 500, height: 700 })
    })
  })

  describe('resetChatWidgetSize', () => {
    it('remet les dimensions par defaut (400x600)', () => {
      const store = useUiStore()
      store.setChatWidgetSize(500, 700)
      store.resetChatWidgetSize()
      expect(store.chatWidgetWidth).toBe(400)
      expect(store.chatWidgetHeight).toBe(600)
    })

    it('supprime la cle localStorage', () => {
      const store = useUiStore()
      store.setChatWidgetSize(500, 700)
      store.resetChatWidgetSize()
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
    })
  })

  describe('chargement initial depuis localStorage', () => {
    it('charge la taille sauvegardee au demarrage via initWidgetSize', () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ width: 550, height: 750 }))
      const store = useUiStore()
      store.initWidgetSize()
      expect(store.chatWidgetWidth).toBe(550)
      expect(store.chatWidgetHeight).toBe(750)
    })

    it('garde les defauts si localStorage est vide', () => {
      const store = useUiStore()
      store.initWidgetSize()
      expect(store.chatWidgetWidth).toBe(400)
      expect(store.chatWidgetHeight).toBe(600)
    })

    it('garde les defauts si localStorage contient des donnees invalides', () => {
      localStorage.setItem(STORAGE_KEY, 'invalid-json')
      const store = useUiStore()
      store.initWidgetSize()
      expect(store.chatWidgetWidth).toBe(400)
      expect(store.chatWidgetHeight).toBe(600)
    })

    it('garde les defauts si localStorage contient un objet incomplet', () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ width: 500 }))
      const store = useUiStore()
      store.initWidgetSize()
      expect(store.chatWidgetWidth).toBe(400)
      expect(store.chatWidgetHeight).toBe(600)
    })
  })
})
