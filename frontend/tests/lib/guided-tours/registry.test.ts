import { describe, it, expect } from 'vitest'
import { tourRegistry, DEFAULT_ENTRY_COUNTDOWN } from '~/lib/guided-tours/registry'
import type { GuidedTourDefinition } from '~/types/guided-tour'

const EXPECTED_IDS = [
  'show_esg_results',
  'show_carbon_results',
  'show_financing_catalog',
  'show_credit_score',
  'show_action_plan',
  'show_dashboard_overview',
] as const

describe('tourRegistry', () => {
  it('contient exactement 6 parcours', () => {
    expect(Object.keys(tourRegistry)).toHaveLength(6)
  })

  it('contient les 6 ids attendus', () => {
    for (const id of EXPECTED_IDS) {
      expect(tourRegistry[id]).toBeDefined()
    }
  })

  it('chaque id suit la convention show_*', () => {
    for (const key of Object.keys(tourRegistry)) {
      expect(key).toMatch(/^show_[a-z_]+$/)
    }
  })

  it('chaque parcours a un id coherent avec sa cle', () => {
    for (const [key, tour] of Object.entries(tourRegistry)) {
      expect(tour.id).toBe(key)
    }
  })

  it('chaque parcours a au moins un step', () => {
    for (const tour of Object.values(tourRegistry)) {
      expect(tour.steps.length).toBeGreaterThanOrEqual(1)
    }
  })

  it('tous les selectors utilisent [data-guide-target="..."]', () => {
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        expect(step.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
      if (tour.entryStep) {
        expect(tour.entryStep.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
    }
  })

  it('aucun selector ne commence par . ou #', () => {
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        expect(step.selector).not.toMatch(/^[.#]/)
      }
      if (tour.entryStep) {
        expect(tour.entryStep.selector).not.toMatch(/^[.#]/)
      }
    }
  })

  it('les entrySteps utilisent DEFAULT_ENTRY_COUNTDOWN', () => {
    for (const tour of Object.values(tourRegistry)) {
      if (tour.entryStep) {
        expect(tour.entryStep.popover.countdown).toBe(DEFAULT_ENTRY_COUNTDOWN)
      }
    }
  })

  it('les ids sont uniques', () => {
    const ids = Object.values(tourRegistry).map(t => t.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('un 7eme parcours peut etre ajoute sans erreur (extensibilite)', () => {
    const extended: Record<string, GuidedTourDefinition> = {
      ...tourRegistry,
      show_custom_demo: {
        id: 'show_custom_demo',
        steps: [
          {
            selector: '[data-guide-target="custom-element"]',
            popover: { title: 'Demo', description: 'Test extensibilite' },
          },
        ],
      },
    }
    expect(Object.keys(extended)).toHaveLength(7)
    expect(extended.show_custom_demo.id).toBe('show_custom_demo')
  })
})
