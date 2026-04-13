import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import GuidedTourPopover from '~/components/copilot/GuidedTourPopover.vue'

describe('GuidedTourPopover', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ── Rendu de base ──
  describe('rendu titre et description', () => {
    it('affiche le titre et la description', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Bienvenue sur le tableau de bord',
          description: 'Voici votre score ESG actuel.',
          currentStep: 1,
          totalSteps: 5,
        },
      })

      expect(wrapper.text()).toContain('Bienvenue sur le tableau de bord')
      expect(wrapper.text()).toContain('Voici votre score ESG actuel.')
    })

    it('affiche l\'indicateur de progression', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          currentStep: 3,
          totalSteps: 7,
        },
      })

      expect(wrapper.text()).toContain('Étape 3/7')
    })
  })

  // ── Boutons et emits ──
  describe('boutons et emits', () => {
    it('emit close quand le bouton X est clique', async () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const closeBtn = wrapper.find('[data-testid="popover-close-btn"]')
      expect(closeBtn.exists()).toBe(true)
      await closeBtn.trigger('click')
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('emit next quand le bouton Suivant est clique', async () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const nextBtn = wrapper.find('[data-testid="popover-next-btn"]')
      expect(nextBtn.exists()).toBe(true)
      await nextBtn.trigger('click')
      expect(wrapper.emitted('next')).toHaveLength(1)
    })
  })

  // ── Countdown integre ──
  describe('countdown integre', () => {
    it('affiche le badge countdown quand countdown est defini', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          countdown: 5,
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const badge = wrapper.find('[data-testid="countdown-badge"]')
      expect(badge.exists()).toBe(true)
      expect(badge.text()).toContain('5s')
    })

    it('n\'affiche pas le badge countdown quand countdown est undefined', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const badge = wrapper.find('[data-testid="countdown-badge"]')
      expect(badge.exists()).toBe(false)
    })

    it('decremente le countdown chaque seconde', async () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          countdown: 3,
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const badge = wrapper.find('[data-testid="countdown-badge"]')
      expect(badge.text()).toContain('3s')

      vi.advanceTimersByTime(1000)
      await nextTick()
      expect(wrapper.find('[data-testid="countdown-badge"]').text()).toContain('2s')

      vi.advanceTimersByTime(1000)
      await nextTick()
      expect(wrapper.find('[data-testid="countdown-badge"]').text()).toContain('1s')
    })

    it('emit countdownExpired quand le timer atteint 0', async () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          countdown: 2,
          currentStep: 1,
          totalSteps: 3,
        },
      })

      vi.advanceTimersByTime(2000)
      await nextTick()

      expect(wrapper.emitted('countdownExpired')).toHaveLength(1)
    })
  })

  // ── Dark mode classes ──
  describe('dark mode', () => {
    it('contient les classes dark mode sur le conteneur principal', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const html = wrapper.html()
      expect(html).toContain('dark:bg-dark-card')
      expect(html).toContain('dark:text-surface-dark-text')
      expect(html).toContain('dark:border-dark-border')
    })
  })

  // ── Accessibilite ──
  describe('accessibilite', () => {
    it('a role="dialog" sur le conteneur', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Titre test',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const dialog = wrapper.find('[role="dialog"]')
      expect(dialog.exists()).toBe(true)
    })

    it('a un aria-label sur le conteneur', () => {
      const wrapper = mount(GuidedTourPopover, {
        props: {
          title: 'Mon titre',
          description: 'Desc',
          currentStep: 1,
          totalSteps: 3,
        },
      })

      const dialog = wrapper.find('[role="dialog"]')
      expect(dialog.attributes('aria-label')).toBe('Mon titre')
    })
  })
})
