import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

describe('ChatWidgetHeader', () => {
  let ChatWidgetHeader: ReturnType<typeof import('vue')['defineComponent']>

  beforeEach(async () => {
    vi.resetModules()
    const mod = await import('~/components/copilot/ChatWidgetHeader.vue')
    ChatWidgetHeader = mod.default
  })

  function mountHeader(props: Record<string, unknown> = {}) {
    return mount(ChatWidgetHeader, {
      props: {
        title: 'Assistant IA',
        showBackButton: false,
        ...props,
      },
    })
  }

  describe('Rendu du titre (AC #1)', () => {
    it('affiche le titre par defaut "Assistant IA"', () => {
      const wrapper = mountHeader()
      expect(wrapper.text()).toContain('Assistant IA')
    })

    it('affiche un titre personnalise via prop', () => {
      const wrapper = mountHeader({ title: 'Ma conversation ESG' })
      expect(wrapper.text()).toContain('Ma conversation ESG')
    })

    it('le titre a la classe truncate pour les textes longs', () => {
      const wrapper = mountHeader({ title: 'Un titre tres long qui devrait etre tronque' })
      const titleEl = wrapper.find('h2')
      expect(titleEl.classes()).toContain('truncate')
    })
  })

  describe('Bouton fermer (AC #1)', () => {
    it('emet close au clic sur le bouton fermer', async () => {
      const wrapper = mountHeader()
      const closeBtn = wrapper.find('button[aria-label="Fermer l\'assistant IA"]')
      expect(closeBtn.exists()).toBe(true)

      await closeBtn.trigger('click')
      expect(wrapper.emitted('close')).toHaveLength(1)
    })
  })

  describe('Bouton historique (AC #1)', () => {
    it('emet toggleHistory au clic sur le bouton historique', async () => {
      const wrapper = mountHeader()
      const historyBtn = wrapper.find('button[aria-label="Historique des conversations"]')
      expect(historyBtn.exists()).toBe(true)

      await historyBtn.trigger('click')
      expect(wrapper.emitted('toggleHistory')).toHaveLength(1)
    })
  })

  describe('Mode retour avec showBackButton (AC #2)', () => {
    it('affiche la fleche retour quand showBackButton=true', () => {
      const wrapper = mountHeader({ showBackButton: true })
      const backBtn = wrapper.find('button[aria-label="Retour à la conversation"]')
      expect(backBtn.exists()).toBe(true)
    })

    it('masque le bouton historique quand showBackButton=true', () => {
      const wrapper = mountHeader({ showBackButton: true })
      const historyBtn = wrapper.find('button[aria-label="Historique des conversations"]')
      expect(historyBtn.exists()).toBe(false)
    })

    it('emet back au clic sur la fleche retour', async () => {
      const wrapper = mountHeader({ showBackButton: true })
      const backBtn = wrapper.find('button[aria-label="Retour à la conversation"]')

      await backBtn.trigger('click')
      expect(wrapper.emitted('back')).toHaveLength(1)
    })
  })

  describe('Aria labels (AC #1)', () => {
    it('le bouton fermer a aria-label="Fermer l\'assistant IA"', () => {
      const wrapper = mountHeader()
      const closeBtn = wrapper.find('button[aria-label="Fermer l\'assistant IA"]')
      expect(closeBtn.exists()).toBe(true)
    })

    it('le bouton historique a aria-label="Historique des conversations"', () => {
      const wrapper = mountHeader()
      const historyBtn = wrapper.find('button[aria-label="Historique des conversations"]')
      expect(historyBtn.exists()).toBe(true)
    })

    it('le bouton retour a aria-label="Retour à la conversation"', () => {
      const wrapper = mountHeader({ showBackButton: true })
      const backBtn = wrapper.find('button[aria-label="Retour à la conversation"]')
      expect(backBtn.exists()).toBe(true)
    })
  })

  describe('Dark mode (AC #6)', () => {
    it('le titre a les classes dark mode', () => {
      const wrapper = mountHeader()
      const title = wrapper.find('h2')
      expect(title.classes().join(' ')).toContain('dark:text-surface-dark-text')
    })

    it('le header a la bordure dark mode', () => {
      const wrapper = mountHeader()
      const header = wrapper.find('header')
      expect(header.classes().join(' ')).toContain('dark:border-dark-border/50')
    })

    it('les boutons ont les classes hover dark mode', () => {
      const wrapper = mountHeader()
      const closeBtn = wrapper.find('button[aria-label="Fermer l\'assistant IA"]')
      expect(closeBtn.classes().join(' ')).toContain('dark:hover:bg-dark-hover')
    })
  })
})
