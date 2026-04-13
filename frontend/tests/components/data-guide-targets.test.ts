import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { tourRegistry } from '~/lib/guided-tours/registry'

// Stub des auto-imports Vue/Nuxt
vi.stubGlobal('computed', computed)
vi.stubGlobal('onMounted', onMounted)
vi.stubGlobal('ref', ref)

import AppSidebar from '~/components/layout/AppSidebar.vue'

// Mock des composables utilises par AppSidebar
vi.mock('~/composables/useAuth', () => ({
  useAuth: () => ({ logout: vi.fn() }),
}))
vi.mock('~/composables/useCompanyProfile', () => ({
  useCompanyProfile: () => ({ fetchCompletion: vi.fn() }),
}))

// Stub NuxtLink — single root, fallthrough attrs actif
const NuxtLink = {
  name: 'NuxtLink',
  props: ['to'],
  inheritAttrs: true,
  template: '<a :href="to" :data-to="to"><slot /></a>',
}

/**
 * Extrait toutes les valeurs de data-guide-target du registre
 * (steps + entrySteps), sans doublons.
 */
function extractRegistryTargets(): string[] {
  const targets = new Set<string>()
  for (const tour of Object.values(tourRegistry)) {
    for (const step of tour.steps) {
      const match = step.selector.match(/^\[data-guide-target="([^"]+)"\]$/)
      if (match) targets.add(match[1])
    }
    if (tour.entryStep) {
      const match = tour.entryStep.selector.match(/^\[data-guide-target="([^"]+)"\]$/)
      if (match) targets.add(match[1])
    }
  }
  return [...targets].sort()
}

describe('Coherence registre-DOM : data-guide-target (Story 4.3)', () => {
  // Les 19 valeurs attendues dans le registre
  const EXPECTED_TARGETS = [
    'action-plan-timeline',
    'carbon-benchmark',
    'carbon-donut-chart',
    'carbon-reduction-plan',
    'credit-score-gauge',
    'dashboard-carbon-card',
    'dashboard-credit-card',
    'dashboard-esg-card',
    'dashboard-financing-card',
    'esg-recommendations',
    'esg-score-circle',
    'esg-strengths-badges',
    'financing-fund-list',
    'sidebar-action-plan-link',
    'sidebar-carbon-link',
    'sidebar-credit-link',
    'sidebar-dashboard-link',
    'sidebar-esg-link',
    'sidebar-financing-link',
  ].sort()

  it('le registre contient exactement les 19 selectors attendus', () => {
    const targets = extractRegistryTargets()
    expect(targets).toEqual(EXPECTED_TARGETS)
  })

  it('chaque selector du registre respecte la convention [data-guide-target="xxx"]', () => {
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        expect(step.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
      if (tour.entryStep) {
        expect(tour.entryStep.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
    }
  })

  it('aucun doublon parmi les selectors du registre', () => {
    const allSelectors: string[] = []
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        allSelectors.push(step.selector)
      }
      if (tour.entryStep) {
        allSelectors.push(tour.entryStep.selector)
      }
    }
    expect(new Set(allSelectors).size).toBe(allSelectors.length)
  })

  describe('AppSidebar — 6 attributs data-guide-target sur les liens', () => {
    beforeEach(() => {
      setActivePinia(createPinia())
    })

    const SIDEBAR_TARGETS = [
      'sidebar-dashboard-link',
      'sidebar-action-plan-link',
      'sidebar-esg-link',
      'sidebar-carbon-link',
      'sidebar-financing-link',
      'sidebar-credit-link',
    ]

    const NON_GUIDE_ROUTES = [
      '/applications',
      '/reports',
      '/documents',
      '/profile',
    ]

    function mountSidebar() {
      return mount(AppSidebar, {
        global: { stubs: { NuxtLink } },
      })
    }

    it('les 6 liens cibles portent chacun leur data-guide-target', () => {
      const wrapper = mountSidebar()
      for (const target of SIDEBAR_TARGETS) {
        const el = wrapper.find(`[data-guide-target="${target}"]`)
        expect(el.exists(), `data-guide-target="${target}" absent du DOM`).toBe(true)
      }
    })

    it('les 4 autres liens n\'ont pas de data-guide-target', () => {
      const wrapper = mountSidebar()
      for (const route of NON_GUIDE_ROUTES) {
        const link = wrapper.find(`[data-to="${route}"]`)
        expect(link.exists(), `lien vers ${route} introuvable`).toBe(true)
        expect(
          link.attributes('data-guide-target'),
          `le lien ${route} ne devrait pas avoir de data-guide-target`,
        ).toBeUndefined()
      }
    })

    it('le nombre total de data-guide-target dans la sidebar est exactement 6', () => {
      const wrapper = mountSidebar()
      const elements = wrapper.findAll('[data-guide-target]')
      expect(elements).toHaveLength(6)
    })
  })
})
